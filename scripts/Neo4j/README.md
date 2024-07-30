# Setup for Community Neo4j Server for OpenTLDR KnowledgeGraph
Neo4j is a graph database server. In OpenTLDR, we use Neo4j to store the Knowledge Graph by default.
The files in this folder are intended to help you configure and start an instance of the Community Version of Neo4j as a Docker container.
## Step 1: Ensure that you have some version of Docker installed

## Step 2: Use Docker Compose to start the Neo4j container

### Starting the Container

### Stopping the Container

### Accessing the services on the Container

The community version of Neo4j does not require a user id or password (simply press connect) and also only supports a single database (named neo4j).

if you are using an enterprise hosted version of Neo4j then you may be required to authenticate yourself. If this is the case, you will also have to authenticate access made by OpenTLDR, which can be performed by setting the following variables in your environment or local .env file:

NEO4J_CONNECTION='neo4j://localhost:7687'
NEO4J_USERNAME=neo4jUser
NEO4J_PASSWORD=neo4jPassword
NEO4J_DB=neo4j

#### Web Browser Interface

Neo4j comes with a handy web-based GUI that will be setup by default on port 7474. The docker compose file provided here only opens this port for the localhost (as a security percaution).
You can access this page using the link: http://localhost:7474

#### Database API (Bolt)



## Step 3: Using the default color scheme for graphs
To help ensure that images of graphs produced for OpenTLDR maintain a more consistent appearence, we have included a configuration file (a .grass file) that Neo4j uses to determine how to draw the graphs that it produces. This color scheme was designed to be consistent with the various presentations and screen shots used in this repository. While use of this file is entirely optional, the intent is to help make images more immediately understandable between researchers familiar with OpenTLDR.
- Open Neo4j interface in a Web Browser window
- Verify that the "Database Information" is displayed in the top left of the screen (i.e. you cannot be zoomed into a single command output window)
- Drag and drop the file "neo4j_styles.grass" into the window, a modal drop icon will appear
- 
