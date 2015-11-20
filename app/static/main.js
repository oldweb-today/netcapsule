window.INCLUDE_URI = "/static/novnc/";

var cmd_host = undefined;
var vnc_host = undefined;

var connected = false;
var ping_id = undefined;
var ping_interval = undefined;

// Load supporting scripts
Util.load_scripts(["webutil.js", "base64.js", "websock.js", "des.js",
                   "keysymdef.js", "keyboard.js", "input.js", "display.js",
                   "inflator.js", "rfb.js", "keysym.js"]);

$(function() {
    function init_container() {
        var params = {"url": url, "ts": curr_ts, "browser": coll, "state": "ping"};
        
        var fail_count = 0;

        function send_request() {
            var init_url = "/init_browser?" + $.param(params);

            $.getJSON(init_url, handle_response)
            .fail(function() {
                fail_count++;
                
                if (fail_count <= 3) {
                    browserMsg.text("Retry Browser Init...");
                    setTimeout(send_request, 5000);
                } else {
                    browserMsg.text("Failed to init browser... Please try again later");
                }
            });
        }

        function handle_response(data) {
            params.id = data.id;

            if (data.cmd_host && data.vnc_host) {
                cmd_host = data.cmd_host;
                vnc_host = data.vnc_host;

                $("#currLabel").html("Loading <b>" + url + "</b>");
                window.setTimeout(do_init, 1000);

            } else if (data.queue != undefined) {
                var msg = "Waiting for empty slot... ";
                if (data.queue == 0) {
                    msg += "<b>You are next!</b>";
                } else {
                    msg += "At most <b>" + data.queue + " user(s)</b> ahead of you";
                }
                $("#currLabel").html(msg);

                window.setTimeout(send_request, 3000);
            }
        }

        send_request();
    }

    function do_init() {
        var res = do_vnc();
        if (!res) {
            window.setTimeout(do_init, 1000);
        }
    }

    $("#update").click(function() {
        var ts = $("#ts").val();

        var cmd_url = "http://" + cmd_host + "/set?ts=" + ts;

        $.getJSON(cmd_url, function(data) {
            if (data && data.success) {
                curr_ts = ts;
                console.log("Updated Date to " + ts);
                $(".rel_message").show();
                update_replay_state();
            }
        });
    });

    function lose_focus() {
        if (!rfb) return;
        rfb.get_keyboard().set_focused(false);
        rfb.get_mouse().set_focused(false);
    }

    function grab_focus() {
        if (!rfb) return;
        rfb.get_keyboard().set_focused(true);
        rfb.get_mouse().set_focused(true);
    }

    $("#noVNC_screen").blur(lose_focus);
    $("#noVNC_screen").mouseleave(lose_focus);

    $("#noVNC_screen").mouseenter(grab_focus);
    
    $("#new_date").click(lose_focus);
    $("#new_time").click(lose_focus);

    init_container();


    function update_replay_state() {
        var full_url = "/" + coll + "/" + curr_ts + "/" + url;

        window.history.replaceState({}, "", full_url);
    }


    function ping() {
        $.getJSON("http://" + cmd_host + "/ping?ts=" + curr_ts, function(data) {
            /*
if (data.urls && data.min_sec && data.max_sec) {
var min_date = new Date(data.min_sec * 1000).toLocaleString();
var max_date = new Date(data.max_sec * 1000).toLocaleString();
$("#currLabel").html("Loaded <b>" + data.urls + " urls </b> spanning " + min_date + " - " + max_date);
$(".rel_message").hide();
}
*/
            if (data.referrer && data.referrer_secs) {
                var date_time = new Date(data.referrer_secs * 1000).toISOString().slice(0, -5).split("T");
                //$("#currLabel").html("Loaded <b>" + data.referrer + "</b> from <b>" + url_date + "</b>");
                $(".rel_message").hide();
                $("#curr-date").html(date_time[0]);
                $("#curr-time").html(date_time[1]);
                url = data.referrer;
                ping_interval = 10000;
            }

            
            if (data.hosts && data.hosts.length > 0) {
                $("#hosts").html("Archived content courtesy of <b>" + data.hosts.join(", ") + "</b>");
            }
            //if (sec) {
            //    $("#currLabel").html("Current Page: <b>" + url + "</b> from <b>" + new Date(sec * 1000).toGMTString() + "</b>");
            //}

            update_replay_state();
        }).complete(function() {
            ping_id = window.setTimeout(ping, ping_interval);
        });
    }

    var rfb;
    var resizeTimeout;


    function UIresize() {
        if (WebUtil.getQueryVar('resize', false)) {
            var innerW = window.innerWidth;
            var innerH = window.innerHeight;
            var controlbarH = $D('noVNC_status_bar').offsetHeight;
            var padding = 5;
            if (innerW !== undefined && innerH !== undefined)
                rfb.setDesktopSize(innerW, innerH - controlbarH - padding);
        }
    }
    function FBUComplete(rfb, fbu) {
        UIresize();
        rfb.set_onFBUComplete(function() { });
    }

    function onVNCCopyCut(rfb, text)
    {
        //$("#clipcontent").text(text);
    }

    function do_vnc() {
        try {
            rfb = new RFB({'target':       $D('noVNC_canvas'),
                           'encrypt':      WebUtil.getQueryVar('encrypt',
                                                               (window.location.protocol === "https:")),
                           'repeaterID':   WebUtil.getQueryVar('repeaterID', ''),
                           'true_color':   WebUtil.getQueryVar('true_color', true),
                           'local_cursor': WebUtil.getQueryVar('cursor', true),
                           'shared':       WebUtil.getQueryVar('shared', true),
                           'view_only':    WebUtil.getQueryVar('view_only', false),
                           'onUpdateState':  updateState,
                           'onClipboard': onVNCCopyCut,
                           'onFBUComplete': FBUComplete});
        } catch (exc) {
            //updateState(null, 'fatal', null, 'Unable to create RFB client -- ' + exc);
            console.warn(exc);
            return false; // don't continue trying to connect
        }

        var hostport = vnc_host.split(":");
        var host = hostport[0];
        var port = hostport[1];
        var password = "secret";
        var path = "websockify";

        try {
            rfb.connect(host, port, password, path);
            connected = true;
        } catch (exc) {
            console.warn(exc);
            return false;
        }

        return true;
    }

    function updateState(rfb, state, oldstate, msg) {
        if (state == "failed" || state == "fatal") {
            // if not connected yet, attempt to connect until succeed
            if (!connected) {
                window.setTimeout(do_vnc, 1000);
            }
        } else if (state == "disconnected") {
            if (connected) {
                connected = false;
                $("#noVNC_canvas").hide();
                $("#browserMsg").show();

                if (ping_id) {
                    window.clearInterval(ping_id);
                }

                init_container();
            }
        } else if (state == "normal") {
            $("#noVNC_canvas").show();
            $("#browserMsg").hide();
            
            ping_interval = 1000;

            // start ping at regular intervals
            ping_id = window.setTimeout(ping, ping_interval);
        }

        //        var s, sb, cad, level;
        //        s = $D('noVNC_status');
        //        sb = $D('noVNC_status_bar');
        //        cad = $D('sendCtrlAltDelButton');
        //        switch (state) {
        //            case 'failed':       level = "error";  break;
        //            case 'fatal':        level = "error";  break;
        //            case 'normal':       level = "normal"; break;
        //            case 'disconnected': level = "normal"; break;
        //            case 'loaded':       level = "normal"; break;
        //            default:             level = "warn";   break;
        //        }
        //
        //        if (state === "normal") {
        //            cad.disabled = false;
        //        } else {
        //            cad.disabled = true;
        //            xvpInit(0);
        //        }
        //
        //        if (typeof(msg) !== 'undefined') {
        //            sb.setAttribute("class", "noVNC_status_" + level);
        //            s.innerHTML = msg;
        //        }
        console.log(msg);
    }

    window.onresize = function () {
        // When the window has been resized, wait until the size remains
        // the same for 0.5 seconds before sending the request for changing
        // the resolution of the session
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function(){
            UIresize();
        }, 500);
    };
});




$(function() {
    $("#browser-dropdown").click(function(e) {
        if (!$("#browser-selector").is(":visible")) {
            show_menu();
        } else {
            hide_menu();
        }
        e.stopPropagation();
    });

    $("#browser-close").click(function(e) {
        hide_menu();
    });

    $(document).click(function(e){
        hide_menu();
    });

    $("#browser-selector").click(function(e){
        e.stopPropagation();
    });

    $("#browser-selector td:not(:empty)").click(function(e) {
        $("#browser-selector td").removeClass("selected");
        $(this).addClass("selected");

        var tr = $(this).parent();
        var browserTH;
        do {
            browserTH = tr.find("th");
            tr = tr.prev();
        } while (tr && !browserTH.length);


        var platform = $("#browser-selector thead").find("th").eq($(this).index());

        $("#browser-text").text(browserTH.text() + " on " + platform.text());
        $("#browser-icon").attr("src", $(this).find("img").attr("src"));
        $("#browser-label").text($(this).find("label").text());

        hide_menu();

        var path = $(this).attr("data-path");
        var full_url = window.location.origin + "/" + path + "/" + curr_ts + "/" + url;
        window.location.href = full_url;
    });

    function hide_menu()
    {
        $("#browser-selector").hide();
        $("#browser-dropdown").removeClass("browser-drop-shown");
    }

    function show_menu()
    {
        $("#browser-selector").show();
        $("#browser-dropdown").addClass("browser-drop-shown");

        var pos = $("#browser-dropdown").offset();
        pos.top += $("#browser-dropdown").outerHeight();
        $("#browser-selector").offset(pos);
    }

    $("#browser-selector td[data-path='" + coll + "']").addClass("selected");
});

// TimeUtils
function TimeUtils()
{
    this.date_pad = "10000101";
    this.time_pad = "000000";

    this.set_from_ts = function(ts) {
        ts = ts.substr(0, 14);
        ts += this.date_pad.substr(ts.length);
        ts += this.time_pad.substr(ts.length - this.date_pad.length);

        this.set_date(ts.substr(0, this.date_pad.length));
        this.set_time(ts.substr(this.date_pad.length));
    };

    this.set_date = function(value) {
        $("#new-date").attr("data-date", value);

        var formatted = value.substr(0, 4) + "-" + value.substr(4, 2) + "-" + value.substr(6);
        $("#new-date").val(formatted);
    };

    this.set_time = function(value) {
        $("#new-time").attr("data-time", value);

        var formatted = value.substr(0, 2) + ":" + value.substr(2, 2) + ":" + value.substr(4);
        $("#new-time").val(formatted);
    };
    
    this.validate_date = function() {
        var value = $("#new-date").val();
        value = value.replace(/[^\d]/g, '');
        value = value.substr(0, 8);
        value += this.date_pad.substring(value.length);
        this.set_date(value);
    };
    
    this.validate_time = function() {
        var value = $("#new-time").val();
        value = value.replace(/[^\d]/g, '');
        value = value.substr(0, 6);
        value += this.time_pad.substring(value.length);
        this.set_time(value);
    };
}

$(function() {
    var timeutil = new TimeUtils();
    
    timeutil.set_from_ts(curr_ts);
    
    $("#new-date").blur(function() {
        timeutil.validate_date();
    });
    
    $("#new-time").blur(function() {
        timeutil.validate_time();
    });
});
    
    






$(function() {
    var jsonUrl = "http://" + window.location.hostname + ":1208/timemap/json/" + url;
    $.getJSON(jsonUrl, function(data) {
        init_spark("#spark", data, {width: 150, height: 500, thickness: 6, swap: true});
    }).fail(function(e) {
        console.log(e);
    });
});