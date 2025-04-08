import json
import requests
from tqdm import tqdm
import re
from urllib.parse import urlparse

from datetime import datetime, timezone

import logging

import os
from dotenv import load_dotenv
load_dotenv()

#from opentldr.Domain import Source, Content

# To ensure consistency regardless of run-time
def non_random_hash(text:str):
  hash=0
  for ch in text:
    hash = ( hash*281  ^ ord(ch)*997) & 0xFFFFFFFF
  return str(hex(hash)[2:].upper().zfill(8))

class RepoWriter():

    def __init__(self, write_path:str=None) -> None:
        self.log = logging.getLogger("OpenTLDR Collector")
        self.write_path = write_path
        self.today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        log_level=os.getenv("COLLECTOR_LOG_LEVEL")
        if log_level is not None:
            self.log.setLevel(log_level)

        if self.write_path is None:
            self.write_path=os.getenv("COLLECTOR_WRITE_PATH")
            if self.write_path is None:
                self.write_path="../Data/Live"
        

    def set_log_level(self, level) -> None:
        self.log.setLevel(level)


    def write_content(self, content:dict) -> setattr:
        uid = non_random_hash(str(content["url"]))
        
        content["metadata"]["repo_uid"]=uid
        filename = "{uid}.json".format(uid=uid)
        directory = os.path.join(self.write_path, content['date'], 'content')

        if not os.path.exists(directory):
            os.makedirs(directory)

        fullpath = os.path.join(directory,filename)

        # If hash(url) exists, then skip this
        if os.path.exists(fullpath):
            self.log.info("Skipping duplicate: {}".format(fullpath))
            return None

        with open(fullpath,'w', encoding='utf-8') as writer:
            stuff = { "Content": [
                content
            ] }
            writer.write(json.dumps(stuff, indent=4))

        self.log.info("Wrote: {}".format(filename))

        return uid
    

    def http_copy(self, source_url:str, destination_fullpath:str) -> None:
        response = requests.get(source_url, stream=True)
        with open(destination_fullpath,"wb") as f:
            for data in tqdm(response.iter_content()):
                f.write(data)


    def url_to_filename(self, url:str) -> str:
        parsed_url = urlparse(url)
        path = parsed_url.path
        extension = os.path.splitext(path)[1]
        filename = re.sub(r'[<>:"/\\|.?*]','_', parsed_url.netloc+parsed_url.path)
        if not extension:
            extension=".unk"
        filename= filename[:255 - len(extension)]
        return filename+extension