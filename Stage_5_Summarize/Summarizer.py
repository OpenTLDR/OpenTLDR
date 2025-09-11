import os
import logging
import json
import dotenv

class Summarizer:

    def summarize (self, text:str) -> str:
        """
        Abstract method to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this!")


def getSummarizer(llm_config=None, logging_level=logging.WARN) -> Summarizer | None:
    dotenv.load_dotenv()  # Load environment variables from .env file

    if llm_config is None:
        llm_config = json.loads(os.getenv("LLM_CONFIG", '{"type": "Ollama", "device":"local", "model":"mistral:latest"}' ))

    llm:Summarizer | None = None

    match (llm_config['type'].lower()):
        case "gpt4all": 
            from SummarizeWithGPT4All import SummarizeWithGPT4All
            llm = SummarizeWithGPT4All(llm_config['model'],device=llm_config['device'], logging_level=logging_level)
        case "ollama":
            from SummarizeWithOllama import SummarizeWithOllama
            llm = SummarizeWithOllama(model_name=llm_config['model'], logging_level=logging_level)
        case "chatgpt":
            from SummarizeWithChatGPT import SummarizeWithChatGPT
            api_key:str = llm_config.get("OPENAI_API_KEY", None)
            if "api_key" in llm_config:
                api_key = llm_config['api_key']
            llm = SummarizeWithChatGPT(api_key, model_name=llm_config['model'], logging_level=logging_level)
        case _:
            raise ValueError("No LLM type support for {}.".format(llm_config['type']))
        
    return llm