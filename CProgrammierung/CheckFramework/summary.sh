#!/bin/bash

# Bash script to generate graph

graph=$(cat <<GRAPHEND
graph match { 
	node[style=filled shape=point label= ""];
	size="40.0,40.0";
	fontsize=10.0;
	overlap=false ;
	spline=true; 
	nodesep=4.0;

"Teststudent3"
"Teststudent2"
"Teststudent1"

	"Teststudent3" -- "Teststudent2" [penwidth=2.25 color="red" label="1" fontsize=7.0];
	"Teststudent1" -- "Teststudent3" [penwidth=0.971455347833 color="#ffff00" label="1" fontsize=7.0];
	"Teststudent1" -- "Teststudent2" [penwidth=0.971455347833 color="#ffff00" label="1" fontsize=7.0];
}
GRAPHEND
)
echo $graph > .temp.dot 
neato -Tps -osummary.ps .temp.dot 
rm -f .temp.dot
