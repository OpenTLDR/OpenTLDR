import feedparser

from datetime import datetime, timedelta, timezone
import pytz

import json
import uuid

import logging

import os
from dotenv import load_dotenv
load_dotenv()

from opentldr.Domain import Source, Content

class RssFeed():

    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    
    feed_store=None
    feed = None
    archive = None
    title:str = "no title set"
    description:str ="no description found"

    def __init__(self, name:str, user_agent=None) -> None:
        self.log = logging.getLogger("OpenTLDR Collector")
        self.name = name
        self.filter:bool=False
        self.filter_latest_time:datetime = datetime.now(timezone.utc)
        self.filter_earliest_time:datetime = (self.filter_latest_time - timedelta(days=1000))
        if user_agent is not None:
            self.user_agent = user_agent

    def set_log_level(self, level) -> None:
        self.log.setLevel(level)


    def set_filter(self, today:datetime=None, earliest:datetime=None, days:int=1):
        self.filter=True
        
        if today is None:
            self.filter_latest_time = datetime.now(timezone.utc)
        else:
            self.filter_latest_time = pytz.UTC.localize(today)

        if earliest is None:
            self.filter_earliest_time = pytz.UTC.localize(self.filter_latest_time - timedelta(days=days))
        else:
            self.filter_earliest_time = pytz.UTC.localize(earliest)


    def process_item(self, entry:dict, url:str, type:str) -> dict:
        content:dict = {}
        entry_date =  pytz.UTC.localize(datetime(*(entry.published_parsed[0:6])))
        
        if not hasattr(entry,'title'):
            entry['title'] = "unknown"

        if not hasattr(entry,'author'):
            entry['author'] = "unknown"

        if not hasattr(entry,'link'):
            entry['link'] = "no link provided"

        if not hasattr(entry,'summary'):
            entry['summary'] = "no summary provided"

        if not hasattr(entry,'description'):
            entry['description'] = entry['summary']

        # build content object
        content:dict = {
            "title": entry.title,
            "date": entry_date.strftime("%Y-%m-%d"),
            "type": type,
            "author": entry.author,
            "source": self.name,
            "url": entry.link,
            "text": entry.description,
            "metadata":{
                "source_id": entry.id,
                "source_rss_feed": self.url,
                "source_rss_title": self.title,
                "media": [],
            },
        }

        # Media Thumbnails
        if hasattr(entry,'media_thumbnail'):
            self.log.debug("Entry has {} media_thumbnails.".format(len(entry.media_thumbnail)))
            for e in entry.media_thumbnail:
                content['metadata']['media'].append(e["url"])
                # Note: enclosure has attrivutes url, width, height

        # Enclosures are how rss links to media and are optional
        if hasattr(entry,'enclosure'):
            self.log.debug("Entry has {} enclosures.".format(len(entry.enclosure)))
            for e in entry.enclosure:
                content['metadata']['media'].append(e["url"])
                # Note: enclosure has attrivutes url, length, and type

        return content
      
    def resolve_date(self,string:str) -> datetime:
        out = pytz.UTC.localize(datetime.now())

        try:
            out = datetime.strptime(string.published, "%a, %d %b %Y %H:%M:%S %z")
            return out
        except:
            pass

        try:
            out = datetime.strptime(string.published, datetime.isoformat)
            return out
        except:
            pass

        # Give up and return the current datetime
        return out


    def fetch_feed(self, url:str, type="unknown") -> list:
        self.url = url   
        feedparser.USER_AGENT = self.user_agent
        self.feed = feedparser.parse(self.url)
        
        if self.feed is None:
            self.log.error("No feed loaded.")
            return []

        header = self.feed.feed

        if hasattr(header,"title"):
            self.title = header.title

        # Sometimes RSS dates are screwy - let's try to fix them.
        if hasattr(header,'published_parsed'):
            self.published:datetime = pytz.UTC.localize(datetime(*(header.published_parsed[0:6])))
        else:
            if hasattr(header,'published'):
                self.published:datetime = pytz.UTC.localize(self.resolve_date(header.published))
            else:
                self.published:datetime = pytz.UTC.localize(datetime.now())

        if hasattr(header,"decription"):
            self.description = header.description

        if self.feed.bozo != 0:
            self.log.error("RSS Feed {title} had parse error (line {line}): {error}".format(
                title=self.title,
                line=self.feed.bozo_exception.getLineNumber(),
                error=self.feed.bozo_exception
            )) 
            return []
                
        self.log.info("Title: {} \t Published: {}".format(
                self.title,self.published.strftime('%Y-%m-%d %H:%M:%S'))
                                                                                                                                                                   )
        if self.archive is not None:
            if not os.path.exists(self.archive):
                os.makedirs(self.archive)  

            feed_store_path=os.path.join(self.archive,"{}_{}.rss_json".format(self.name, self.published.strftime('%Y%m%d%H%M%S')))
            
            with open(feed_store_path,'w') as fs:
                json.dump(self.feed, fs, indent=4, ensure_ascii=True)
            self.log.info("Stored RSS Feed with {} entries as {}".format(len(self.feed.entries),feed_store_path))  
    
            #print(json.dumps(self.feed, indent=4))
        
        out = []
        for entry in self.feed.entries:
   
            try:
                # Sometimes RSS dates are screwy - let's try to fix them.
                # worst option
                entry_date = datetime.today()

                # not bad
                if hasattr(header,'published'):
                    entry_date = self.resolve_date(header.published)
                
                # pretty good option
                if hasattr(entry,'published_parsed'):
                    entry_date = datetime(*(entry.published_parsed[0:3]))
                
                # best option
                if hasattr(entry,'updated_parsed'):
                    entry_date = datetime(*(entry.updated_parsed[0:3]))               
                
                entry_date = pytz.UTC.localize(entry_date)

                if entry_date >= self.filter_earliest_time and entry_date <= self.filter_latest_time:
                    self.log.debug("Adding Entry '{}'".format(entry.title))
                    out.append(self.process_item(entry, url, type))
                else:
                    self.log.debug("Skipping Entry (date filtered {}):'{}'".format(entry_date.strftime('%Y-%m-%d'),entry.title))
                
            except Exception as e:
                self.log.error("Error Parsing Entry: {} \n {} ".format(e, json.dumps(entry)))
        
        return out



