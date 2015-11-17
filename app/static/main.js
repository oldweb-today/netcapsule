window.INCLUDE_URI = "/static/novnc/";

var cmd_host = undefined;
var vnc_host = undefined;

$(function() {
    function init_container() {
        var params = {"url": url, "ts": curr_ts, "browser": coll, "state": "ping"};

        function send_request() {
            var init_url = "/init_browser?" + $.param(params);

            $.getJSON(init_url, handle_response);
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

    init_container();
});


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
            var url_date = new Date(data.referrer_secs * 1000).toLocaleString();
            $("#currLabel").html("Loaded <b>" + data.referrer + "</b> from <b>" + url_date + "</b>");
            $(".rel_message").hide();
            url = data.referrer;
        }

        if (data.hosts && data.hosts.length > 0) {
            $("#hosts").html("Archived content courtesy of <b>" + data.hosts.join(", ") + "</b>");
        }
        //if (sec) {
        //    $("#currLabel").html("Current Page: <b>" + url + "</b> from <b>" + new Date(sec * 1000).toGMTString() + "</b>");
        //}

        update_replay_state();
    });
}

/*jslint white: false */
/*global window, $, Util, RFB, */
"use strict";

// Load supporting scripts
Util.load_scripts(["webutil.js", "base64.js", "websock.js", "des.js",
                   "keysymdef.js", "keyboard.js", "input.js", "display.js",
                   "inflator.js", "rfb.js", "keysym.js"]);

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
                       //'onXvpInit':    xvpInit,
                       //'onPasswordRequired':  passwordRequired,
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
    } catch (exc) {
        console.warn(exc);
        return false;
    }

    return true;
}

function updateState(rfb, state, oldstate, msg) {
    if (state == "failed" || state == "fatal") {
        window.setTimeout(do_vnc, 1000);
    } else if (state == "normal") {
        $("#noVNC_canvas").show();
        $("#browserMsg").hide();
        
        // first ping
        window.setTimeout(ping, 1000);
        // start ping at regular intervals
        window.setInterval(ping, 10000);
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



$(function() {
    $("#browser-dropdown").click(function(e) {
        if (!$("#browser-selector").is(":visible")) {
            show_menu();
            var pos = $("#browser-dropdown").offset();
            pos.top += $("#browser-dropdown").outerHeight() + 1;
            $("#browser-selector").offset(pos);
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
    }
        
    $("#browser-selector td[data-path='" + coll + "']").addClass("selected");
});