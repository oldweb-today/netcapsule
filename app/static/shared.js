// Dropdowns
$(function() {

    // Shared
    $(".menu-selector-close").click(function(e) {
        hide_menu();
    });

    $(document).click(function(e){
        hide_menu();
    });

    $(".selector-menu").click(function(e){
        e.stopPropagation();
    });

    $(".drop-skip").click(function(e){
        e.stopPropagation();
    });

    function hide_menu()
    {
        $(".selector-menu").hide();
        $(".dropdown").removeClass("dropdown-shown");
    }


    // Browser
    $("#browser-dropdown").click(function(e) {
        if (!$(".selector-menu").is(":visible")) {
            show_browser_menu();
        } else {
            hide_menu();
        }
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
        
        coll = $(this).attr("data-path");
        //$("#about-link").text("about " + browserTH.text());
        $("#about-link").attr("href", $(this).attr("data-about-url"));
        $(".about-browser").show();
    });

    function show_browser_menu()
    {
        $("#browser-selector").show();
        $("#browser-dropdown").addClass("dropdown-shown");

        var pos = $("#browser-dropdown").offset();
        pos.top += $("#browser-dropdown").outerHeight();
        $("#browser-selector").offset(pos);
    }

    // Datetime
    $("#datetime-dropdown").click(function(e) {
        if (!$(".selector-menu").is(":visible")) {
            show_datetime_menu();
        } else {
            hide_menu();
        }
        e.stopPropagation();
    });

    function show_datetime_menu()
    {
        $("#datetime-selector").show();
        $("#datetime-dropdown").addClass("dropdown-shown");

        var pos = $("#datetime-dropdown").offset();
        pos.top += $("#datetime-dropdown").outerHeight();
        $("#datetime-selector").offset(pos);
    }
    
    if (coll) {
        var browser = $("#browser-selector td[data-path='" + coll + "']");
        browser.addClass("selected");
        $("#about-link").attr("href", browser.attr("data-about-url"));
        $(".about-browser").show();
    }
});