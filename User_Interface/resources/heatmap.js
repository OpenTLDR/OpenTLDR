class Heatmap {
    
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

        const cellSize = 40;
        this.cell_width = cellSize * itemsX.length + margin.left + margin.right;
        this.cell_height = cellSize * itemsY.length + margin.top + margin.bottom;
    }

    genData(){
        this.data_x = ['A', 'B', 'C', 'D', 'E'];
        this.data_y  = ['1', '2', '3', '4', '5'];
        this.data_values = []
        
        for (x in this.data_x){
            for (y in this.data_y){
                this.data_values.push({ x: x, y: y, score: Math.random(), url:"NA"})
            }
        }
    }

    loadData(data){
        this.data_x = ['A', 'B', 'C', 'D', 'E'];
        this.data_y  = ['1', '2', '3', '4', '5'];
        this.data_values = []
        
        for (x in this.data_x){
            for (y in this.data_y){
                this.data_values.push({ x: x, y: y, score: Math.random(), url:"loaded"})
            }
        }
    }

    draw(){

        this.cell_spacing = 1
        this.cell_width = this.width / this.data_x.length
        this.cell_height = this.height / this.data_y.length

        this.svg.remove();
        //this.svg = d3.select(this.svg_id).append("svg").attr("height","100%").attr("width","100%");

        this.svg = d3.select(this.svg_id)
            .append("svg")
            .attr("width", this.width)
            .attr("height", this.height)
            .append("g")
            .attr("transform", `translate(${margin.left}, ${margin.top})`);

        this.build_axis();
        this.draw_cells();
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

        this.x_axis = svg.append("g")
            .selectAll(".xLabel")
            .data(this.data_x)
            .enter()
            .append("text")
            .attr("x", (d, i) => i * cellSize + cellSize / 2)
            .attr("y", -5)
            .style("text-anchor", "middle")
            .text(d => d);
    
        this.y_axis = svg.append("g")
            .selectAll(".yLabel")
            .data(this.data_y)
            .enter()
            .append("text")
            .attr("y", (d, i) => i * cellSize + cellSize / 2)
            .attr("x", -5)
            .style("text-anchor", "end")
            .text(d => d);
    }

    draw_cells(){
        
        // Color scale based on score
        this.colorScale = d3.scaleLinear()
            .domain([-1.0, 0.0, 1.0])
            .range(["#ff0000", "#ffffff", "#00ff00"]); // red to white to green

        const tooltip = d3.select("#tooltip");

        // Draw the heatmap cells
        svg.selectAll(".cell")
            .data(this.data_values)
            .enter()
            .append("rect")
            .attr("class", "cell")
            .attr("x", d => this.data_x.indexOf(d.x) * this.cell_width)
            .attr("y", d => this.data_y.indexOf(d.y) * this.cell_height)
            .attr("width", this.cell_width - this.cell_spacing)
            .attr("height", this.cell_height - this.cell_spacing)
            .attr("fill", d => colorScale(d.score))
            .on("mouseover", function(event, d) {
                d3.select("#tooltip-img").attr("src", d.url);
                tooltip.style("display", "block");
            })
            .on("mousemove", function(event) {
                tooltip.style("top", (event.pageY + 10) + "px")
                    .style("left", (event.pageX + 10) + "px");
            })
            .on("mouseout", function() {
                tooltip.style("display", "none");
            });


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
