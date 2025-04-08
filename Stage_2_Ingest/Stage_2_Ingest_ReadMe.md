# Stage 2 Ingest
During the Ingest stage, Active Data is loaded into the system.

![diagram](./Stage_2_Ingest_Content.png) 

For the sake of repeatable experiments, we consider loading Requests from a mocked up User and UI to be treated like Active Data.

![diagram](./Stage_2_Ingest_Requests.png)

## Notebook Capabilities

In both cases, the process is nearly identical:
* Use an OpenTLDR Data_Repo to load data. A Data_Repo abstracts the source of the data to load and allows the data source to be specified as a parameter passed into notebooks. The intent is to avoid hardcoding data paths in the notebooks directly, so they can be better reused by other researchers.
* For each Content or Request node that is imported from the Data_Repo, we want to identify Entities and add appropriate nodes for each. Entities are things (e.g., Keywords or Names) mentioned in the text that later stages will attempt to connect to Reference Data.

## Expected Results

The results of this stage should be:
- A set of Content and/or Request nodes with new Source/User nodes as needed.
- Each Content|Request node connected with "MENTIONED_IN" edges to new appropriate Entity nodes.