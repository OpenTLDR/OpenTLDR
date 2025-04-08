class Networkplot{

    constructor(svg_id){
        this.svg_id = svg_id;
        this.svg = d3.select(this.svg_id).append("svg").attr("height","100%").attr("width","100%");

        this.netplot_width = +this.svg.node().getBoundingClientRect().width;
        this.netplot_height = +this.svg.node().getBoundingClientRect().height;
    }

    loadData(netdata){
        //this.tempData();
        this.graph=netdata;
    }

    clear(){
        this.svg.remove();
        this.svg = d3.select(this.svg_id).append("svg").attr("height","100%").attr("width","100%");
    }

    draw(){
        this.clear()
        this.draw_network();
    }

    draw_network(){
        this.simulation = d3.forceSimulation(this.graph.nodes)
            .force("link", d3.forceLink(this.graph.links).id(d => d.id).distance(50))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(this.netplot_width / 2, this.netplot_height / 2));

        net_simulation=this.simulation;

        this.link = this.svg.append("g")
            .selectAll("line")
            .data(this.graph.links)
            .enter().append("line")
            .attr("class", "link");

        this.node = this.svg.append("g")
            .selectAll("circle")
            .data(this.graph.nodes)
            .enter().append("circle")
            .attr("class", d => d.type)
            .attr("r", 8)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        this.label = this.svg.append("g")
            .selectAll("text")
            .data(this.graph.nodes)
            .enter().append("text")
            .attr("dy", -15)
            .attr("dx", -5)
            .attr("class", "nodeText")
            .text(d => d.text);

        this.simulation.on("tick", () => {
            this.link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            this.node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            this.label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });
    }
}

net_simulation=null;

function dragstarted(event, d) {
    event.sourceEvent.stopPropagation();
    if (!event.active)
        net_simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active)
        net_simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
