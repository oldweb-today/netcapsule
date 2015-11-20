

function load_timemap(timemapBase, url)
{
}


function init_spark(target, data, options)
{
    // set up a date parsing function for future use
    var parseDate = d3.time.format.utc("%Y-%m-%dT%H:%M:%SZ").parse;
    
    var dateOnly = d3.time.format.utc("%Y-%m-%d");
    
    var width = options.width;
    var height = options.height;
    
    var timeScale = d3.time.scale()
    var linScale = d3.scale.linear()
    
    var timeAxis = d3.svg.axis().scale(timeScale);
    
    data = data.mementos.list.map(function(d) { return parseDate(d.datetime); });

    data = d3.nest()
    .key(function(d) { 
        return d3.time.month.utc(d).getTime()
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
    
    var timeAxisTrans;
    var graphTrans;
    
    var xfunc;
    var yfunc;
    var widthFunc;
    var heightFunc;
    
    var x_offset = 35;
    var y_offset = 20;
    var graphWidth = width - x_offset;
    var graphHeight = height - y_offset;
    
    options.thickness = options.thickness || 4;
    
    if (options.swap) {
        timeScale.range([height, 0]);
        linScale.range([0, graphWidth]);
        timeAxis.orient("left");
        
        yVal = function(d) { return timeScale(d.date) - 3; };
        heightVal = options.thickness;
        xVal = x_offset;
        widthVal = function(d) { return linScale(d.total); };
        
        timeAxisTrans = "translate(" + x_offset + ",0)";
        
    } else {
        timeScale.range([0, width]);
        linScale.range([graphHeight, 0]);
        timeAxis.orient("bottom");
        
        xVal = function(d) { return timeScale(d.date) - 3; };
        widthVal = options.thickness;
        yVal = function(d) { return linScale(d.total); };
        heightVal =  function(d) { return graphHeight - linScale(d.total); };
        
        timeAxisTrans = "translate(0," + graphHeight + ")";
    }
    
    var svg = d3.select(target)
    .append("svg") 
    .attr("width", width)
    .attr("height", height);
    
    var tooltip = d3.select(target).append("div")
    .attr("class", "tooltip")
    .style("opacity", 0);

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
    
    var res = spark.append("g")
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
    
    
    if (options.swap) {
        var highlight = spark.append("rect")
        .attr("class", "highlight hidden")
        .attr("x", x_offset)
        .attr("y", 0)
        .attr("width", graphWidth)
        .attr("height", 2);
        
        bgrect.on("mousemove", function(d) {
            var y = timeScale.invert(d3.mouse(this)[1]);
            highlight.attr("transform", "translate(0, " + timeScale(y) + ")");
            highlight.classed("hidden", false);
            
            tooltip.html(dateOnly(y))
            .style("left", (width + 5) + "px")
            .style("top", (d3.event.pageY - 30) + "px")
            .style("opacity", 1.0);
        });
    }
    
    bgrect.on("mouseout", function(d) {
        highlight.classed("hidden", true);
        
        tooltip.style("opacity", 0.0);
    });
}