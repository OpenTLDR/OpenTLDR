
class Scatterplot {
    
    constructor(svg_id){
        this.svg_id = svg_id;
        this.svg = d3.select(this.svg_id).append("svg").attr("height","100%").attr("width","100%");

        this.margin = {top: 10, right: 40, bottom: 20, left: 10};
        this.area_width = +this.svg.node().getBoundingClientRect().width ;
        this.area_height = +this.svg.node().getBoundingClientRect().height;
        this.width = this.area_width - this.margin.left - this.margin.right;
        this.height = this.area_height - this.margin.top - this.margin.bottom;
        this.y_offset = this.area_height - this.margin.bottom;
        this.x_offset = this.area_width  - this.margin.right +10;
        this.selected=[]
    }

    genData(){
        this.data = Array.from({ length: 1000 }, () => ({
            x: Math.random() * 100,
            y: Math.random(),
            uid: "THISISATEST"
        }));
    }

    loadData(data){
        this.data=Array()
        for (const point of data){
            this.data.push({
                x: point.age,
                y: point.relevance,
                u: point.content_uid
            })
        }
    }

    draw(){
        this.svg.remove();
        this.svg = d3.select(this.svg_id).append("svg").attr("height","100%").attr("width","100%");

        this.build_axis();
        this.draw_points();
        this.selection();
    }

    build_axis(){
        // Create scales
        this.xScale = d3.scaleLinear()
            .domain([d3.max(this.data, d => d.x), d3.min(this.data, d => d.x)])
            .range([this.margin.left, this.width+this.margin.left])
            .nice();
        this.yScale = d3.scaleLinear()
            .domain([1.0, 0.0])
            .range([this.margin.bottom, this.height])
            .nice();
        this.xAxis = d3.axisBottom(this.xScale);
        this.yAxis = d3.axisRight(this.yScale);

        // Axis
        this.x_axis= this.svg.append("g")
            .attr("class", "x axis")
            .attr("transform", `translate(0,${this.y_offset})`)
            .call(this.xAxis)
            .append("text")
            .attr("class", "axis-label")
            .attr("x", (this.area_width)/ 2)
            .attr("y", this.y_offset-15)
            .style("text-anchor", "middle")
            .text("Content Age (days)");

        this.y_axis= this.svg.append("g")
            .attr("class", "y axis")
            .attr("transform", `translate(${this.x_offset},0)`) 
            .call(this.yAxis)
            .append("text")
            .attr("class", "axis-label")
            .attr("x", this.area_width)
            .attr("y", this.area_height/2)
            .style("text-anchor", "middle")
            .text("Relevance");
    }

    draw_points(){      
        this.points = this.svg.selectAll("circle")
            .data(this.data)
            .enter().append("circle")
            .attr("cx", d => this.xScale(d.x + ((Math.random()*0.5)-0.25)))
            .attr("cy", d => this.yScale(d.y))
            .attr("id", d => d.u)
            .attr("r", 8)
            .attr("fill", "lightgrey")
            .attr('fill-opacity', 0.5)
            .attr("class","unselected");

    }

    selection(){
        // Selection box
        this.isSelecting = false;
        this.startPoint = null;

        this.selectionBox = this.svg.append("rect")
            .attr("class", "selection-box")
            .style("display", "none");

        // Mouse Down
        this.svg.on("mousedown", event => {
            this.isSelecting = true;
            this.startPoint = d3.pointer(event);
            this.selectionBox
                .attr("x", this.startPoint[0])
                .attr("y", this.startPoint[1])
                .attr("width", 0)
                .attr("height", 0)
                .style("display", null);
        });

        // Mouse Move
        this.svg.on("mousemove", event => {
            if (!this.isSelecting) return;
            this.currentPoint = d3.pointer(event);
            const x = Math.min(this.startPoint[0], this.currentPoint[0]);
            const y = Math.min(this.startPoint[1], this.currentPoint[1]);
            const width = Math.abs(this.startPoint[0] - this.currentPoint[0]);
            const height = Math.abs(this.startPoint[1] - this.currentPoint[1]);
            this.selectionBox
                .attr("x", x)
                .attr("y", y)
                .attr("width", width)
                .attr("height", height);
        });

        // Mouse Up
        this.svg.on("mouseup", event => {
            if (!this.isSelecting) return;
            this.isSelecting = false;
            this.endPoint = d3.pointer(event);
            const xMin = Math.min(this.startPoint[0], this.endPoint[0]);
            const yMin = Math.min(this.startPoint[1], this.endPoint[1]);
            const xMax = Math.max(this.startPoint[0], this.endPoint[0]);
            const yMax = Math.max(this.startPoint[1], this.endPoint[1]);

            console.log("BBox (["+xMin+"-"+xMax+"],["+yMin+"-"+yMax+"])");


            for (const point of this.points){
                const p=d3.select(point);  
                //console.log("p: "+typeof(p)+"-> "+JSON.stringify(p))
                //console.log("pt "+typeof(pt)+"-> "+JSON.stringify(point))

                const cx = this.xScale(point["__data__"].x);
                const cy = this.yScale(point["__data__"].y);
                //console.log("("+cx+","+cy+")");
                if(cx >= xMin && cx <= xMax && cy >= yMin && cy <= yMax){
                    p.attr("class","selected");
                    selected_content_nodes[point.id]=true;
                    console.log("selected: "+point.id);
                } else {
                    p.attr("class","unselected");
                    selected_content_nodes[point.id]=false;
                    console.log("not selected: "+point.id);
                }
            }

 //           this.points.classed("selected", d => {
 //               const cx = this.xScale(d.x);
 //               const cy = this.yScale(d.y);
 //               return cx >= xMin && cx <= xMax && cy >= yMin && cy <= yMax;
 //           });

            this.selectionBox.style("display", "none");
            update_groupsummary();
            update_selected_table();
        });
    }

}
