import logging
import os
import ollama

from typing import Optional, List
from Summarizer import Summarizer


class SummarizeWithOllama(Summarizer):

    def __init__(self, model_name: str, llm_temp:float=0.01, logging_level=logging.WARN):
        """
        Setups up an LLM instance using a local Ollama Model.
        """
    
        self.log = logging.getLogger("OpenTLDR")
        self.log.setLevel(logging_level)

        available_models = self._get_models()
        if model_name not in available_models:
            error =  "LLM Model {name} is not currently loaded in Ollama, attempting to pull...".format(name=model_name)
            self.log.warning(error)
            ollama.pull(model_name)
            
            available_models = self._get_models()
            if model_name not in available_models:
                error =  "Unable to load LLM Model in Ollama for {name}.".format(name=model_name)
                self.log.error(error)
                raise ValueError(error)
       
        self.llm=model_name
        self.temp=llm_temp

    def _get_models(self) -> List[str]:
        response:ollama.ListResponse = ollama.list()
        out = []
        for model in response.models:
            out.append(str(model.model))

        return out

    def _get_response(self, model_name, prompt:str) -> str:
        options= { "temperture":self.temp }
        response = ollama.generate(model = self.llm, prompt = prompt, stream=False, options=options)
        return response['response'].strip()

    def summarize (self, text:str) -> str:
        """
        Use LLM to run an Abstractive Summary of the provided text.
        """
        out:str = self._get_response(self.llm, text)
        return out
