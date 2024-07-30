CREATE (x:ReferenceNode { type:"PERSON", text: "Alice AllSorts"} );
CREATE (x:ReferenceNode { type:"PERSON", text: "Bob Bobbert"} );
CREATE (x:ReferenceNode { type:"PERSON", text: "Charlie Chuckles"} );
CREATE (x:ReferenceNode { type:"PERSON", text: "David Deadwood"} );
CREATE (x:ReferenceNode { type:"PERSON", text: "Hapster Wheel"} );

CREATE (x:ReferenceNode { type:"ORG", text: "Groceries and Stuff"} );
CREATE (x:ReferenceNode { type:"ORG", text: "First Bank"} );
CREATE (x:ReferenceNode { type:"ORG", text: "Deadwood Arcade"} );
CREATE (x:ReferenceNode { type:"ORG", text: "New News Today Daily"} );

CREATE (x:ReferenceNode { type:"FAC", text: "1st Avenue"} );
CREATE (x:ReferenceNode { type:"FAC", text: "2nd Street"} );
CREATE (x:ReferenceNode { type:"FAC", text: "3rd Blvd"} );
CREATE (x:ReferenceNode { type:"FAC", text: "4th Court"} );

MATCH (a:ReferenceNode {text:"Alice AllSorts"}) MATCH (b:ReferenceNode {text: "First Bank"}) MATCH(p:ReferenceNode {text: "1st Avenue"}) CREATE (a)-[x:REFERENCE_EDGE {type:"WorksFor", text:"Alice is a manager at the First Bank."}]->(b) CREATE (b)-[y:REFERENCE_EDGE {type:"LocatedAt", text:"The First Bank has a branch office on 1st Ave."}]->(p);
MATCH (a:ReferenceNode {text:"Bob Bobbert"}) MATCH (b:ReferenceNode {text: "Deadwood Arcade"}) MATCH(p:ReferenceNode {text: "3rd Blvd"}) CREATE (a)-[x:REFERENCE_EDGE {type:"WorksFor", text:"Bobbert refills the token machine at the Deadwood Arcade."}]->(b) CREATE (b)-[y:REFERENCE_EDGE {type:"LocatedAt", text:"The Deadwood Arcade is located on Third Blvd"}]->(p);
MATCH (a:ReferenceNode {text:"Charlie Chuckles"}) MATCH (b:ReferenceNode {text: "New News Today Daily"}) MATCH(p:ReferenceNode {text: "3rd Blvd"}) CREATE (a)-[x:REFERENCE_EDGE {type:"WorksFor", text:"Charlie is a reporter at New News Today Daily."}]->(b) CREATE (b)-[y:REFERENCE_EDGE {type:"LocatedAt", text:"NNTD has an office on 3rd."}]->(p);
MATCH (a:ReferenceNode {text:"David Deadwood"}) MATCH (b:ReferenceNode {text: "Groceries and Stuff"}) MATCH(p:ReferenceNode {text: "2nd Street"}) CREATE (a)-[x:REFERENCE_EDGE {type:"WorksFor", text:"David works at G&S."}]->(b) CREATE (b)-[y:REFERENCE_EDGE {type:"LocatedAt", text:"Groceries and Stuff (G&S) is on 2nd Street."}]->(p);
MATCH (a:ReferenceNode {text:"Hapster Wheel"}) MATCH (b:ReferenceNode {text: "New News Today Daily"}) CREATE (a)-[x:REFERENCE_EDGE {type:"WorksFor", text:"Hipster N. Wheel is an award winning journalist for the New News Today Daily."}]->(b);