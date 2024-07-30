#
# This code is intended to be run on either:
#   (a) The Live OpenTLDR server - where runs daily and uses today's date to load new content
#   (b) To simulate a live server running the sample data over 4 simulated days over 1/1/2000 - 1/8/2000
#
# MOST OpenTLDR users will not need to use this file, and will find Workflow.ipynb a better fit for them.

import os
from opentldr import Workflow
from datetime import date

from dotenv import load_dotenv
load_dotenv(".env")

#
# Setup parameters and data source for workflow run
#

# path (a) - run it each day
today= str(date.today())

# path (b) - uncomment to force use of sim date given in sample_data/sim_time folder
#today = "2000-01-08"

print("Today is {d}".format(d=today))

# from .env or os environment

use_s3 = True

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

def date_repo_config(dir:str) -> dict:
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
                'path': './sample_data/sim_live/{d}/{dir}'.format(d=today, dir=dir)}


#
#   Setup OpenTLDR Workflow
#

workflow = {
    "Output": "./READ_ONLY_OUTPUT/{d}".format(d=today),
    "Notebooks": [
        ["Step_0_Initialize.ipynb",{
            "message": "Successfully passed in parameters from Workflow.ipynb!",
            "ref_date_repo_config": date_repo_config("reference"),
            "clean_policy": "live",
            }],
        ["Step_1_Ingest.ipynb", {
            "active_date_repo_config": date_repo_config("content"),
            }],
        ["Step_1a_MockUI.ipynb",{
            "request_date_repo_config": date_repo_config("request"),
            }],
        ["Step_2_Connect.ipynb",{
            "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "threshold_similarity_connect": 0.5,
            "threshold_similarity_hypothesize": 0.8,
            }],
        ["Step_3_Recommend.ipynb",{
            "recommendation_threshold": 0.54,
        }],
        ["Step_4_Summarize.ipynb",{
            "llm_model_path": "./models/mistral-7b-openorca.gguf2.Q4_0.gguf",
            "llm_prompt": "Given these facts: {knowledge} and the request: {request}. Concisely summarize this article: {content}",
            }],
        ["Step_5_Produce.ipynb",{
            "today":today,
        }],
        ["Step_6_Evaluate.ipynb",{
            "eval_data_repo_config": date_repo_config("evalkey"),
            "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            }],
    ]}

wf:Workflow = Workflow(workflow)
wf.run()
