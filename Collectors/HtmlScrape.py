import os
import urllib

from bs4 import BeautifulSoup
import requests


def fetch_html(url:str) -> str:
    if url is None:
        return None
    
    request=requests.get(url)
    return request.content

def process_text(in_html:str) -> str:
    soup = BeautifulSoup(in_html,"html.parser")
    text = soup.find_all(string=True)

    output = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head', 
        'input',
        'script',
    ]

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)

    return output

def extract_text_from_element(type:str, param:dict, in_html:str) -> str:
    soup = BeautifulSoup(in_html,"html.parser")
    text= soup.find_all(type, dict, string=True)

    output = ''
    blacklist = [
        '[document]',
        'noscript',
        'header',
        'html',
        'meta',
        'head', 
        'input',
        'script',
    ]

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)

    return output

def url_to_filename(url:str) -> str:
    return os.path.join("", urllib.quote(url, ''))