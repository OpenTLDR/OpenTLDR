import logging
import os

from langchain.chains.summarize import load_summarize_chain
from langchain.llms import GPT4All
from langchain import PromptTemplate, LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.mapreduce import MapReduceChain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

class SummarizeWithGPT4All:

    def __init__(self, model_path: str, device: str = "gpu", logging_level=logging.WARN):
        """
        Setups up an LLM instance using a local GPT4ALL Model.
        model_path is the path and model name to load (e.g., "./LLM_Models/mistral-7b-openorca.gguf2.Q4_o.gguf")
        """
    
        self.log = logging.getLogger("OpenTLDR")
        self.log.setLevel(logging_level)

        if not os.path.isfile(model_path):
            error =  "No LLM Model File was found at {path}".format(path=model_path)
            self.log.error(error)
            raise ValueError(error)
        
        self.llm=GPT4All(model=model_path, backend='gptj', device=device, verbose=False)
        self.sum_chain = load_summarize_chain(self.llm, chain_type="refine")


    def summarize (self, text:str) -> str:
        """
        Use LLM to run an Abstractive Summary of the provided text.
        """
        
        # put the content into a format that works for prompts
        out:str =""

        if len(text) > 2000:
            logging.warning("Text too long, using first 2000 characters.")
            text=text[0:2000]

        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_text(text)
        docs = [Document(page_content=t) for t in texts[:3]]
        
        if len(docs) > 0:
            out= self.sum_chain.invoke(docs)['output_text'].strip()

        return out
