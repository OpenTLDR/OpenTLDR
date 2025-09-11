import logging
import os
from openai import OpenAI

from typing import Optional, List

class SummarizeWithChatGPT(Summarizer)

    def __init__(self,api_key:str, model_name: str="gpt-4", llm_temp:float=0.01, logging_level=logging.WARN):
        """
        Setups up an LLM instance using commercial ChatGPT.
        """
    
        self.log = logging.getLogger("OpenTLDR")
        self.log.setLevel(logging_level)
        self.llm=model_name
        self.temp=llm_temp

        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        self.api_key = api_key
        self.client = OpenAI()


 
    def _get_response(self, model_name, request:str) -> str:
        completion = self.client.chat.completions.create(
            model=model_name,
            temperature=self.temp,
            messages=[
                {
                    "role": "user",
                    "content": request,
                },
            ],
        )
        return completion.choices[0].message.content


    def summarize (self, text:str) -> str:
        """
        Use LLM to run an Abstractive Summary of the provided text.
        """
        out:str = self._get_response(self.llm, text)
        return out
