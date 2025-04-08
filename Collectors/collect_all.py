import os
import logging
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from opentldr import Workflow

write_path = os.getenv("LIVE_DATA_REPO_PATH")

if write_path is None:
    write_path = "../Data/Live"

print ("Writing Data to: {}".format(write_path))

today = datetime.now().strftime('%Y-%m-%d')
print ("Today is {}".format(today))

workflow = {
    "Output": "./READ_ONLY_OUTPUT_COLLECTORS_ALL",

    "Common": {
        "live_data_repo_path": write_path,
        "media_cache_path": os.path.join(write_path,"MediaCache"),
        "logging_level": logging.INFO,
        "days_history": 100,
        "date": today,
        "organize_by_source": True
    },

   "Notebooks": [

        # RSS Feeds from BBC.uk (RSS fields/thumbnails and target HTML page)
        ["collect_bbc.ipynb", {
            "download_media": False,
        }],

        # Scrape NPR's text-only website    
        ["collect_npr.ipynb", {
            "download_media": False,
        }],

        # RSS Feeds from US Dept of State (text from RSS Description Field)
        ["collect_state.ipynb", {
            "download_media": False,
        }],

        # RSS Feeds from NY Times (text from RSS Description Field only)
        ["collect_nytimes.ipynb", {
            "download_media": False,
        }],
 
        # RSS Feeds from Arxiv.org (Technical Documents as PDF and HTML)
        ["collect_arxiv.ipynb",{
            "download_media": False,
            "arxiv_file_format": "pdf",
        }],
    ]}

wf:Workflow = Workflow(workflow)
wf.run()