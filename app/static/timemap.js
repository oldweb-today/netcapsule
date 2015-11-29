


function Sparkline(target, data, options)
{    
    // set up a date parsing function for future use
    var parseDate = d3.time.format.utc("%Y-%m-%dT%H:%M:%SZ").parse;
    var dateOnly = d3.time.format.utc("%Y-%m-%d");
    var userDate = d3.time.format.utc("%Y-%m-%d %H:%M:%S").parse;
    
    var width = options.width;
    var height = options.height;
    
    var timeScale = d3.time.scale()
    var linScale = d3.scale.linear()
    //var linScale = d3.scale.log().base(Math.E);
    
    var timeAxis = d3.svg.axis().scale(timeScale);
    
    if (data) {  
        data = data.mementos.list.map(function(d) { return parseDate(d.datetime); });

        data = d3.nest()
        .key(function(d) { 
            return d3.time.day.utc(d).getTime()
        })
        .rollup(function(vals) { 
            return {"total":  vals.length}
        })
        .entries(data);

        data = data.map(function(d) { 
            return {"date": new Date(+d.key),
                    "total": d.values.total,
                   }
        });

        timeScale.domain(d3.extent(data, function(d) { return d.date; }));

        linScale.domain([0, d3.max(data, function(d) { return d.total; })]);
    } else {
        timeScale.domain([new Date(1996, 1, 1), new Date()]);
        linScale.domain([0, 1]);
    }
    
    var timeAxisTrans;
    var graphTrans;
    
    var xfunc;
    var yfunc;
    var widthFunc;
    var heightFunc;
    
    var x_offset = 40;
    var y_offset = 20;
    var y_margin = 15;
    var graphWidth = width - x_offset;
    var graphHeight = height - y_offset;
    
    options.thickness = options.thickness || 4;
    var halfThick = options.thickness / 2;
    
    if (options.swapXY) {
        timeScale.range([height - y_margin, y_margin]);
        linScale.range([0, graphWidth]);
        timeAxis.orient("left");
        
        yVal = function(d) { return timeScale(d.date) - halfThick; };
        heightVal = options.thickness;
        xVal = x_offset;
        widthVal = function(d) { return linScale(d.total); };
        
        timeAxisTrans = "translate(" + x_offset + ",0)";
        
    } else {
        timeScale.range([0, width]);
        linScale.range([graphHeight, 0]);
        timeAxis.orient("bottom");
        
        xVal = function(d) { return timeScale(d.date) - halfThick; };
        widthVal = options.thickness;
        yVal = function(d) { return linScale(d.total); };
        heightVal =  function(d) { return graphHeight - linScale(d.total); };
        
        timeAxisTrans = "translate(0," + graphHeight + ")";
    }
    
    d3.select(target).select("svg").remove();
    
    var svg = d3.select(target)
    .append("svg") 
    .attr("width", width)
    .attr("height", height);
    
    var tooltipId = options.tooltipId || "spark-mouseover-tooltip";
    var tooltip = d3.select("#" + tooltipId);
    
    if (tooltip.empty()) {
        tooltip = d3.select(target).append("div")
        .attr("id", tooltipId)
        .attr("class", "tooltip")
        .style("opacity", 0);
    }

    options["class"] = options["class"] || "";

    var spark = svg.append("g").attr("class", options["class"]);
    
    spark.append("g")
    .attr("class", "axis")
    .attr("transform", timeAxisTrans)
    .call(timeAxis);
    
    var bgrect = svg.append("svg:rect")
    .attr("class", "pane")
    .attr("width", width)
    .attr("height", height);
    
    if (data) {
        spark.append("g")
        .attr("class", "plot")
        //.attr("transform", graphTrans)
        .selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", xVal)
        .attr("width", widthVal)
        .attr("y", yVal)
        .attr("height", heightVal);
    }
    
    //TODO make x-axis time friendly
    function update_selected_marker(date) {
        if (options.onchange) {
            options.onchange(date);
        }
        dragging = true;
        selected.attr("transform", "translate(0, " + timeScale(date) + ")");
        selected.classed("hidden", false);
    }
    
    var highlight = spark.append("rect")
    .attr("class", "highlight hidden")
    .attr("x", x_offset)
    .attr("y", 0)
    .attr("width", graphWidth)
    .attr("height", 1);
    
    this.add_marker = function(name, marker_class, text, x_extra) {
        var marker = spark.append("g")
        .attr("id", name)
        .attr("class", marker_class);

        marker.append("rect")
        .attr("x", x_offset)
        .attr("y", 0)
        .attr("width", graphWidth)
        .attr("height", 2);

        x_extra = x_extra || 8;

        marker.append("text")
        .attr("x", x_offset + x_extra)
        .attr("y", -4)
        .text(text);

        return marker;
    }
    
    var selected = this.add_marker("select-dt", "spark-selected hidden", "Requested", graphWidth - 70);

    var dragging = false;
    
    tooltip.style("left", width + "px");

    bgrect.on("mousemove", function(d) {
        var mouse = d3.mouse(this);
        var date = timeScale.invert(mouse[1]);
        highlight.attr("transform", "translate(0, " + timeScale(date) + ")");
        highlight.classed("hidden", false);

        tooltip.html(dateOnly(date))
        .style("top", (mouse[1] - 11) + "px")
        .style("opacity", 1.0);

        if (dragging) {
            update_selected_marker(date);
        }
    });

    bgrect.on("mousedown", function(d) {
        var date = timeScale.invert(d3.mouse(this)[1]);
        update_selected_marker(date);
    }).on("mouseup", function(d) {
        dragging = false;
        if (options.onmouseup) {
            options.onmouseup(d);
        }
    });
    
    bgrect.on("mouseout", function(d) {
        highlight.classed("hidden", true);
        
        tooltip.style("opacity", 0.0);
    });

    this.move_marker = function(name, date) {
        var marker = d3.select("#" + name);
        marker.attr("transform", "translate(0, " + timeScale(date) + ")");
        marker.classed("hidden", false);
    }
    
    this.move_selected = function(datestr) {
        var date = userDate(datestr);
        if (date) {
            update_selected_marker(date);
        }
    }
}