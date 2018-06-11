

var jsondata = '{"nodes": [{"id": "eb3b15cfce031f9f7494882cccaa04bf", "product": "1,1-dimethylcyclopentane", "name": "market for 1,1-dimethylcyclopentane", "location": "GLO"}, {"id": "304d42eabdcfe000e76034a265f7aa6a", "product": "solvent, organic", "name": "1,1-dimethylcyclopentane to generic market for solvent, organic", "location": "GLO"}], "edges": [{"source": "eb3b15cfce031f9f7494882cccaa04bf", "target": "304d42eabdcfe000e76034a265f7aa6a", "label": "1,1-dimethylcyclopentane"}]}'
console.log ("Hello World");

var heading = document.getElementById("heading");
// document.getElementById("data").innerHTML = "no data yet";

// SETUP GRAPH
// https://github.com/dagrejs/graphlib/wiki/API-Reference
// HOW TO SET EDGES AND NODES MANUALLY USING GRAPHLIB:
// digraph.setNode("kspacey",    { label: "Kevin Spacey",  width: 144, height: 100 });
// digraph.setEdge("kspacey",   "swilliams");
// var graph = new dagre.graphlib.Graph({ multigraph: true });

// Set an object for the graph label
// graph.setGraph({});


// Create and configure the renderer
// var render = dagreD3.render();


function windowSize() {
    w = window,
    d = document,
    e = d.documentElement,
    g = d.getElementsByTagName('body')[0],
    x = w.innerWidth || e.clientWidth || g.clientWidth;
    y = w.innerHeight|| e.clientHeight|| g.clientHeight;
    return [x,y];
};



// zoom for the graph-

var svg = d3.select("body")
 .append("svg")
 .attr("viewBox", "0 0 600 400")
 .attr("height", "100%")
 .attr("width", "100%")
 .call(d3.zoom().on("zoom", function () {
    svg.attr("transform", d3.event.transform)
 }))
 .append("g")

// var container = svg.append("g")
//    .attr("id", "container")
//    .attr("transform", "translate(0,0)scale(1,1)");
//
// var bbox, viewBox, vx, vy, vw, vh, defaultView;
//
//
// bbox = container.node().getBBox();
//  vx = bbox.x;
//  vy = bbox.y;
//  vw = bbox.width;
//  vh = bbox.height;
//
//  defaultView = "" + vx + " " + vy + " " + vw + " " + vh;
//
//  svg
//    .attr("viewBox", defaultView)
//    .attr("preserveAspectRatio", "xMidYMid meet")
//        .call(zoom);
//
//function getTransform(node, xScale) {
//  bbox = node.node().getBBox();
//  var bx = bbox.x;
//  var by = bbox.y;
//  var bw = bbox.width;
//  var bh = bbox.height;
//  var tx = -bx*xScale + vx + vw/2 - bw*xScale/2;
//  var ty = -by*xScale + vy + vh/2 - bh*xScale/2;
//  return {translate: [tx, ty], scale: xScale}
//}

 //.classed("svg-container", true) //container class to make it responsive
 //.attr("preserveAspectRatio", "none")
 //.attr("preserveAspectRatio", "xMinYMin meet")

 //.classed("svg-content-responsive", true);



var render = dagreD3.render();

function update_graph(json_data) {
    console.log("Updating Graph")
	data = JSON.parse(json_data)

	heading.innerHTML = data.title;

	// reset graph
	var graph = new dagre.graphlib.Graph({ multigraph: true });
	graph.setGraph({});

	  // nodes --> graph
	  data.nodes.forEach(function(n) {

	    graph.setNode(n['id'], {
	      label: chunkString(n['name'], 40),
	      product: n['product'],
	      location: n['location'],
	      id: n['id'],
	      database: n['database'],
	    });
	  });

	  // edges --> graph
	  data.edges.forEach(function(e) {
	  	// document.writeln(e['source']);
	    graph.setEdge(e['source'], e['target'], {label: chunkString(e['label'], 40)});
	  });

	  // Render the graph into svg g
	  svg.call(render, graph);


	  // Interacting with the graph (MUST HAPPEN AFTER RENDERING!)
	  var nodes = svg.selectAll("g .node")
	      .on("click", handleMouseClick)
	      console.log ("click!");

	// Interaction with Python/Qt

	function handleMouseClick(node){

		if (window.event.ctrlKey){
            console.log ('ctrl')

            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.bridge = channel.objects.bridge;
                window.bridge.node_clicked_expand(graph.node(node).database + ";" + graph.node(node).id)
                window.bridge.graph_ready.connect(update_graph);
            });

		} else if (window.event.shiftKey){
            console.log ('shift')

            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.bridge = channel.objects.bridge;
                window.bridge.node_clicked_expand_upstream(graph.node(node).database + ";" + graph.node(node).id)
                window.bridge.graph_ready.connect(update_graph);
            });

		} else  {
            console.log ('no ctrl')
            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.bridge = channel.objects.bridge;
                window.bridge.node_clicked(graph.node(node).database + ";" + graph.node(node).id)
            window.bridge.graph_ready.connect(update_graph);
            });
	}

};
};


// break strings into multiple lines after certain length if necessary
function chunkString(str, length) {
    return str.match(new RegExp('.{1,' + length + '}', 'g')).join("\n");
}


new QWebChannel(qt.webChannelTransport, function (channel) {
    window.bridge = channel.objects.bridge;
    window.bridge.graph_ready.connect(update_graph);
});

// var svg = d3.select("body").select("svg");
// https://stackoverflow.com/questions/16265123/resize-svg-when-window-is-resized-in-d3-js
//var svg = d3.select("body")
  // .append("div")

  // .append("svg")
   //responsive SVG needs these 2 attributes and no width and height attr
   // .attr("preserveAspectRatio", "none")
   // .attr("preserveAspectRatio", "xMinYMin meet")
   // .attr("viewBox", "0 0 600 400")
   //.attr('viewBox','0 0 '+windowSize()[0]+' '+windowSize()[1])
   //class to make it responsive
   //.classed("svg-content-responsive", true);

      <!--var nodeEnter = node.enter().append("g")-->
          <!--.attr("class", "node")-->
          <!--.attr("transform", function(d) {-->
              <!--return "translate(" + source.y0 + "," + source.x0 + ")";-->
          <!--})-->
          <!--.on("click", click)-->
          <!--.on("mouseover", function(d) {-->
              <!--// The class is used to remove the additional text later-->
      <!--var info = g.append('text')-->
                 <!--.classed('info', true)-->
                 <!--.attr('x', 20)-->
                 <!--.attr('y', 10)-->
                 <!--.text('More info');-->
          <!--})-->
          <!--.on("mouseout", function() {-->
              <!--// Remove the info text on mouse out.-->
          <!--d3.select(this).select('text.info').remove();-->
      <!--});-->