import sys
import subprocess
from typing import List, Tuple

import spacy
spacy.prefer_gpu()

from opentldr.Domain import Entity, Request, Content

class NerWithSpacy():

    verbose:bool = True
    exclude_type_filter = [ 'DATE', 'TIME', 'MONEY', 'CARDINAL', 'ORDINAL', 'PERCENT', 'QUANTITY', 'WORK_OF_ART' ]
    skip_words:list[str] = []
    # NOTE SpaCy's rendering doesn't work in Python3.12 at this time.
    render:bool = False
    nlp = None

    def __init__(self, model_name:str="en_core_web_lg", verbose:bool = True, skip_words:list[str]=[]) -> None:
        self.verbose=verbose
        self.skip_words=skip_words
        self._load_model(model_name)


    def _load_model(self, spacy_model_name:str="en_core_web_lg"):
        if not spacy.util.is_package(spacy_model_name):
            print("Downloading spaCy NLP Model...")
            # equivelent to running -> !{sys.executable} -m spacy download {spacy_model}
            subprocess.check_call([sys.executable, "-m", "spacy", "download", spacy_model_name])
        else:
            if self.verbose:
                print("spaCy model ({model}) is already downloaded.".format(model=spacy_model_name))

        self.nlp=spacy.load(spacy_model_name)
        print (type(self.nlp))
        return self.nlp


    def process(self, text:str) -> List[Tuple[str, str]]:
        if self.nlp is None:
            self.load_model()
        
        doc = self.nlp(text)
        if self.render:
            spacy.displacy.render(doc,style='ent')
        
        out = []
        unique = []
        for spacy_ent in doc.ents:
            if spacy_ent.label_ not in self.exclude_type_filter:
                if spacy_ent.text not in unique:
                    out.append((spacy_ent.label_,spacy_ent.text))
                    unique.append(spacy_ent.text)
        
        return out


