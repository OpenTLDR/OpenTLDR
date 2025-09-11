#
# This code is intended to be run on either:
#   (a) The Live OpenTLDR server - where runs daily and uses today's date to load new content
#   (b) To simulate a live server running the sample data over 4 simulated days over 1/1/2000 - 1/8/2000
#
# MOST OpenTLDR users will not need to use this file, and will find Workflow.ipynb a better fit for them.

import os
from datetime import datetime, timedelta

from opentldr import Workflow
from datetime import date

from dotenv import load_dotenv
load_dotenv(".env")

#
# Setup parameters and data source for workflow run
#
type = "gpt4all"

def build_llm_config() -> dict:
        '''
        builds a simple llm config that inserts model info.
        '''
        match (type.lower()):
            case "ollama":
                return {
                    'type': 'Ollama',
                    'device':'',
                    'model':'mistral:latest'
                }
            case "gpt4all":
                return {
                    'type': 'GPT4ALL',
                    'device':'cpu',
                    'model':'../LLM_Models/mistral-7b-openorca.gguf2.Q4_0.gguf'
                }
            case _ :
                return {
                    'type': 'GPT4ALL',
                    'device':'gpu',
                    'model':'../LLM_Models/mistral-7b-openorca.gguf2.Q4_0.gguf'
                }

# path (a) - run it each day
real_today= date.today()
backdate_days = 5

for today in [(real_today-timedelta(days=i)).strftime('%Y-%m-%d') for i in range(backdate_days,0,-1)]:

    print("Today is {d}".format(d=today))

    # from .env or os environment

    use_s3 = False

    bucket:str = os.getenv("S3_BUCKET")
    if bucket is None:
        print("No S3 Bucket set in environment.")
        use_s3=False

    access:str = os.getenv("S3_ACCESS_KEY_ID")
    if access is None:
        print("No S3 Access Key set in environment.")    
        use_s3=False

    secret:str = os.getenv("S3_SECRET_KEY")
    if secret is None:
        print("No S3 Secret Key set in environment.")     
        use_s3=False

    def data_repo_config(today:str, dir:str) -> dict:
        if use_s3:
            return {
                "repo_type": "s3",
                "bucket": bucket,
                "aws_access_key_id": access,
                "aws_secret_access_key": secret,
                "prefix": "live/{d}/{dir}".format(d=today, dir=dir)
                }
        else:
            return {'repo_type': 'files',
                    'path': '../Data/Live/{d}/{dir}'.format(d=today, dir=dir)}


    #
    #   Setup OpenTLDR Workflow
    #

    workflow = {
        
        # Where a read-only version of the notebook AFTER execution is stored
        "Output": "./READ_ONLY_OUTPUT",
        
        # Parameters passed into all notebooks in workflow
        "Common": {
            "logging_level":10,
            "verbose": True,
        },

        # Order and parameters of notebooks to execute in workflow
        "Notebooks": [

            # Setup the KG
            [ "Stage_1_Initialize/Clear_Live_Content.ipynb", {}],

                    # Load Content and Requests
            [ "Stage_2_Ingest/Load_Content.ipynb", {
                "active_data_repo_config": data_repo_config(today,"content"),
            }],

            # Generate stand-alone untailored summaries ONLY NEEDED for multi-doc comparisons in digger
            [ "Stage_5_Summarize/Presummarize.ipynb",{
                "llm_config" : build_llm_config(),
            }],

            # Perform Analytics to link entities in Requests and Content nodes
            [ "Stage_3_Connect/Entity_Cosin_Similarity.ipynb",{
                "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "connect_threshold": 0.6,
                "hypothesize_threshold": 0.9
            }],

            # Compute recommendations based on relevance of content to request
            [ "Stage_4_Recommend/Shortest_Path_Scoring.ipynb", {
                "recommendation_threshold": 0.6
            }],

            # Generate a summary of the content that is tailored with respect to the request and useful reference knowledge
            [ "Stage_5_Summarize/Tailored_Abstractive_Summary.ipynb", {
                "llm_config" : build_llm_config(),
                "llm_prompt": "You are a helpful assistant responding to the request: {request} \n\n and were given these facts: {knowledge} \n\n Concisely summarize the following article: {content}"
            }],

            # Produce a TLDR Report for each request
            [ "Stage_6_Produce/Build_TLDR.ipynb", {}]

        ]}

    wf:Workflow = Workflow(workflow)
    wf.run()
