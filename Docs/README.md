

## Initialize and Import an OpenTLDR Knowledge Graph
The KnowledgeGraph() contructor should be called without parameters so that it defaults to using .env and environment variables.
The order of is:

1 Set in KnowledgeGraph() constructor

- You can set each variable and it will create the driver
- You can setup a neo4j driver instance and pass that in
- **We advise NOT using this method** , as your notebook's code will overrule the automation configurations

2 Set as Environment variable
- This is how several automated processes operate, but this is not intended for most users

3 Set in the .env file (in project directory)
- **This is the recommended place for you to set system-specific things!**
- This file is not part of the GitHub repository you cloned, instead you or a setup script must create it (usually this
is done by copying the DefaultDotEnv file to .env (e.g., cp ./DefaultDotEnv ./.env))

4 Defaults that are hard coded will work with the provided neo4j container setup, but probably not much else:

| Variable | Value | Description |
|---|---|---|
| NEO4J_CONNECTION | 'bolt://localhost:7687' | URL for bolt protocol on default port of localhost only |
| NEO4J_USERNAME | neo4jUser | user and password are not used for default localhost only container |
| NEO4J_PASSWORD | neo4jPassword | user and password are not used for default localhost only container |
| NEO4J_DATABASE | neo4j | community edition of neo4j ONLY allows one database |