from opentldr import KnowledgeGraph
from opentldr.Domain import Request, Content, Recommendation, ReferenceNode, Entity
from datetime import datetime, date
from pydantic import BaseModel
from random import random

import os
import re
import sys
import subprocess
import logging
logging.getLogger("Digger").setLevel(logging.INFO)   # More output

import spacy
from langchain.chains.summarize import load_summarize_chain
from langchain_community.llms import GPT4All
from langchain.chains import LLMChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.mapreduce import MapReduceChain
from langchain_core.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from sentence_transformers import SentenceTransformer, util

from dotenv import load_dotenv
load_dotenv()
load_dotenv("{d}/.env".format(d=os.getcwd()))
load_dotenv("{d}/../.env".format(d=os.getcwd()))

def _getenv(variable:str , default:str):
        '''
        _getenv(variable, default) attempts to resolve the value of the environment variable specified.
        If it cannot find the variable in the OS or .env (from dotenv package) it will fail over to the
        provided default value while giving a warning to the logging system.
        '''
        value:str = os.getenv(variable)
        if value == None:
            log.warning("No environment variable '"+variable+"' so defaulting to '"+default+"'.")
            return default
        return value

# When run an LLM locally, you need to download the model to your local machine
llm_model_path = _getenv("LLM_MODEL", "../LLM_Models/mistral-7b-openorca.gguf2.Q4_0.gguf")
llm_device = _getenv("LLM_DEVICE", 'cpu')
spacy_model= _getenv("SPACY_MODEL", "en_core_web_lg")

class RankedContent(BaseModel):
    request_uid:str
    content_uid:str
    recommendation_uid:str
    title:str
    source:str
    date:str
    age:int
    relevance:float
    cited:bool

# FROM NOTEBOOK MOCKUI


# if you have a GPU and your imstalled the spacy[cuda] package, it will use the GPU
spacy.prefer_gpu()

# SpaCy uses a language model that needs to be downloaded, this checks if that has been done
# and if it has not, it will download the model (and some dependencies) which can take a bit.
if not spacy.util.is_package(spacy_model):
        print("Downloading spaCy NLP Model...")
        #equivelent to running -> !{sys.executable} -m spacy download {spacy_model}
        subprocess.check_call([sys.executable, "-m", "spacy", "download", spacy_model])
else:
        print("spaCy model ({model}) is already downloaded.".format(model=spacy_model))

nlp = spacy.load(spacy_model)


def named_entity_recognition(text:str):
        doc = nlp(text)
        #spacy.displacy.render(doc, style='ent')
        return doc.ents


def add_entities(kg:KnowledgeGraph, request_node:Request):
    existing_entities=kg.get_entities_by_request(request_node)
    #unique=[ e.text for e in existing_entities ]
    # remove existing entities and rebuild in case they changed
    for e in existing_entities:
         kg.delete_entity(e)


    # Iterate Keywords
    for keyword_node in kg.get_all_reference_nodes():
        if keyword_node.type == "KEYWORD":
            if re.search(keyword_node.text, request_node.text, re.IGNORECASE):
                entity_node=kg.add_entity(node=request_node,text=keyword_node.text, type="KEYWORD")
                print(" - Added entity '{text}' of type {type}".format(text=entity_node.text, type=entity_node.type))
            #    unique.append(entity_node.text)


    # perform NER on the entities in the request
    for entity in named_entity_recognition(request_node.text):
        if entity.label_ not in ['DATE','TIME','MONEY','ORDINAL','PERCENT','QUANTITY']:
#            if entity.text not in unique:
            entity_node = kg.add_entity(node=request_node, text=entity.text, type=entity.label_)
            print(" - Added entity '{text}' of type {type}".format(text=entity_node.text, type=entity_node.type))
#            unique.append(entity_node.text)


# FROM NOTEBOOK CONNECT

sentence_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(sentence_embedding_model)

def cosin_similarity(string_1:str, string_2:str):
        if string_1 == string_2:
                return 1.0

        #compute the embeddings for each string
        embedding_1= model.encode(string_1, convert_to_tensor=True)
        embedding_2 = model.encode(string_2, convert_to_tensor=True)
        
        #compute the cosin similarity of the two embeddings
        similarity = util.cos_sim(embedding_1, embedding_2).cpu().numpy()[0][0]

        return round(similarity,4)

def connect_entities(kg:KnowledgeGraph, request_node:Request):

    # The cosin similarity overwhich we connect a new entity to existing reference data nodes
    threshold_similarity_connect = 0.56

    # The cosin similarity over which we hypothesize new reference data based on entities
    threshold_similarity_hypothesize = 0.8

    # Query KG for Entities from Articles that have not been connected with a REFERS_TO edge.
    #unreferred_entities = kg.cypher_query("MATCH (a:Entity) WHERE NOT (a)-[:REFERS_TO]->() RETURN (a)","a")
    #print ("Query found {count} Entity nodes that did not have REFER_TO edges.".format(count=len(unreferred_entities)))
    unreferred_entities = kg.cypher_query("""
            MATCH (r:Request) WHERE r.uid=$request_uid
            MATCH (e:Entity)
            MATCH (e)-[y:MENTIONED_IN]->(r)
            WHERE NOT (e)-[:REFERS_TO]->() 
            RETURN e """,
            "e", params={"request_uid": request_node.uid})
    
    # Query KG for Reference Nodes that might be appropriate to add a REFERS_TO edge.
    reference_node_list = kg.get_all_reference_nodes();
    print ("Query found {count} Reference nodes those entities might match.".format(count=len(reference_node_list)))

    count=0
    if len(unreferred_entities) > 0 and len(reference_node_list) > 0:
        for entity in unreferred_entities:

            # For each entity find the most semantically similar Reference Node
            max_score=0.0
            max_record:ReferenceNode=None
            for ref_node in reference_node_list:
                if entity.type == ref_node.type:
                    this_score=cosin_similarity(entity.text,ref_node.text)
                    if this_score > max_score or max_record==None:
                        max_score = this_score
                        max_record = ref_node
            
            # If the most similar is above the threshold, add a REFERS_TO edge.
            if max_score > threshold_similarity_connect:
                print ("Linking:\t{entity}\t-[REFERS_TO ({score})]->\t{reference}".format(
                    score=max_score,entity=entity.text,reference=max_record.text))
                
                kg.add_refers_to_edge(entity=entity, reference=max_record, confidence=max_score)
                count+=1
            #else:
                #print ("Skipping:\t{entity}".format(entity=entity.text))

    print ("Discovered {count} new REFER_TO edges.".format(count=count))
  






# FROM NOTEBOOK RECOMMEND

decay_rate=0.2 ## 1

def distance_decay(kg:KnowledgeGraph,distance_scores:float, node_id:str, score:float):
    #print ("\nRecursing on node {id} with score of {score}.".format(id=node_id, score=score))
    node=kg.get_by_uid(node_id)
    #print ("\tNode is: {}".format(node.to_text()))
    
    # Avoid looking along paths that circumvent reference data
    nodetype=str(type(node))
    for avoid in ["Source", "User", "Recommendation", "Summary", "Feedback", "User", "TldrEntry", "Tldr", "Source", "EvalKey"]:
        if avoid in nodetype:
            # print("\tAvoiding path through a {type} node.".format(type=nodetype))
            return

    prev_score = distance_scores.get(str(node_id),-999)
    if prev_score >= score:
        #print ("\tPreviously at node {id} with score of {prev} vs now with {current}.".format(id=node_id, prev=prev_score, current=score))
        return
    else:
        #print ("\tAssigning node {id} a score of {current}.".format(id=node_id,current=score))
        distance_scores[str(node_id)]= score

    # include Content nodes only once
    if nodetype=="Content":
        return

    # Since this is the lowest so far, we have to also check its neighbors    
    neighbor_records, meta = kg.neo4j_query("MATCH (h)<-[]->(n) WHERE h.uid='{uid}' RETURN n.uid".format(uid=node_id))
    for n_record in neighbor_records:
        other_id = n_record.data()["n.uid"]

        # recurse on nodes that are not too far already
        other_score = score - decay_rate
        if other_score > 0.0:
              distance_decay(kg,distance_scores,other_id, round(other_score,2))

    return

def normalize(score:float) -> float:
    out= (score + (3*decay_rate))
    if out < 0.0:
        return 0.0
    else:
        return out

def average_content(kg:KnowledgeGraph, distance_scores:dict):
    avg_scores=dict()
    all_content = kg.get_all_content()
    for article in all_content:
        acc=normalize(distance_scores.get(str(article.uid),0.0));
        count=1
        if acc > 0.0:
            for e in kg.get_entities_by_content(article):
                acc+=normalize(distance_scores.get(str(e.uid),0.0))
                count+=1
        else:
            acc=0.0
        avg_scores[str(article.uid)]=round(acc/count,3)
    return avg_scores


def score_new(kg:KnowledgeGraph, request:Request, content:Content) -> float:
    shortest_path_cypher = """
            MATCH path=shortestPath((s)-[*..10]-(e))
            WHERE s.uid='{start_id}'
            AND e.uid='{end_id}'                         
            AND NONE(n IN nodes(path) WHERE 'Recommendation' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Tldr' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Recommendation' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Summary' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Feedback' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Source' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Request' IN LABELS(n) AND n.uid<>"{start_id}")             
            AND NONE(n IN nodes(path) WHERE 'Content' IN LABELS(n) AND n.uid<>"{end_id}")             
            AND NONE(n IN nodes(path) WHERE 'User' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'EvalKey' IN LABELS(n))
            AND NONE(n IN nodes(path) WHERE 'Similarity' IN LABELS(n))
            RETURN path
            """
    
    content_uid = content.uid

    count=1
    acc=0.0
    decay_rate=0.2

    try:
        q = kg.neomodel_query(shortest_path_cypher.format(start_id=request.uid, end_id=content_uid))
        path=q[0][0][0]
        acc = 1.0-((len(path.nodes)-5)*decay_rate)
    except:
        pass # no path remains 0.0

    if acc <= 0.0:
        return 0.0;

    for e in kg.get_entities_by_request(request):
        count+=1
        try:
            q = kg.neomodel_query(shortest_path_cypher.format(start_id=e.uid, end_id=content_uid))
            path=q[0][0][0]
            acc+= 1.0-((len(path.nodes)-4)*decay_rate)
        except:
            pass # no addition if no path found

    out = round(acc/count,3)
    
    if out > 1.0:
        return 1.0
    
    return out


# FROM NOTEBOOK SUMMARIZE



if not os.path.exists(llm_model_path):
    raise ValueError ("No LLM Model File was found at {path}".format(path=llm_model_path))

llm=GPT4All(model=llm_model_path, backend='gptj', device=llm_device, verbose=False)
print("LLM using device: {device}".format(device=llm.device))

focused_chain = load_summarize_chain(llm, chain_type="refine")

def group_summary(summaries:str,info_request:str="Tell me what these articles have in common.") -> str:
    llm_prompt = '''
        Given the following news articles respond to this request: "{request}"
        Also with respect to the request, identify what the articles have in common and then highlight the main differences between the articles.
        News articles below are preceded by an article title and separated from the other news articles using '========'. \n
        Summarize the following news articles:\n {multicontent}
    '''
    out=""
    
    # Assemble a prompt to summarize the article
    all_text = llm_prompt.format(multicontent=summaries, request=info_request).strip()

    if len(all_text) > 2000:
        all_text=all_text[0:2000]

    print("Prompt: ",all_text.strip())
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(all_text)
    docs = [Document(page_content=t) for t in texts[:3]]

    # run the summarization chain on the combined prompt
    if len(docs) > 0:
        out= focused_chain.invoke(docs)
    return out['output_text'].strip()
    
sum_chain = load_summarize_chain(llm, chain_type="refine")

def summarize(content_text):
    # put the content into a format that works for prompts
    out=""
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(content_text)
    docs = [Document(page_content=t) for t in texts[:3]]
    if len(docs) > 0:
        out= sum_chain.invoke(docs)
    return out['output_text'].strip()

focused_chain = load_summarize_chain(llm, chain_type="refine")

# an attempt at starting a customized prompt for summary
def summarizeWithFocus(content_body,focus_text,info_request):
    llm_prompt = '''
        Given the following statements as background facts to use: {knowledge}
        Write a concise summary of the following news article: {content}
        Focus the concise summary to respond appropriately to this specific request: {request}
        '''
    out=""

    # Assemble a prompt to summarize the article
    all_text = llm_prompt.format(knowledge=focus_text, content=content_body, request=info_request).strip()

    if len(all_text) > 2000:
        all_text=all_text[0:2000]

    print("Prompt: ",all_text.strip())
    text_splitter = CharacterTextSplitter()
    texts = text_splitter.split_text(all_text)
    docs = [Document(page_content=t) for t in texts[:3]]

    # run the summarization chain on the combined prompt
    if len(docs) > 0:
        out= focused_chain.invoke(docs)
    return out['output_text'].strip()


def run_group_summary(kg:KnowledgeGraph, request:Request, uids:list[str]) -> str:
    len_original=0
    len_summaries=0
    multisum=""
    multidoc_summary="Sorry - No Group Summary Created."

    for uid in uids:
        print("summarizing group with {}".format(uid))
        content=kg.get_content_by_uid(uid)
        len_original += len(content.text)

        if content.metadata is not None:
            summary=content.metadata["summary"]
            len_summaries += len(summary)

            if len(summary) > 0:
                multisum+="\n\n========\n\n\nnews- {}:\n".format(content.title)
                multisum+="{}\n".format(summary)

            # in the case there is only one, just sent that summary instead
            if len(uids) ==1:
                 return summary
        else:
            print("skipping - no metadata summary found")

    if len(multisum) > 0:
        multidoc_summary= group_summary(multisum,request.text)
        print("\nSummary reduced {reduction}% of content:\t{text}".format(reduction=round(((len_original-len(multidoc_summary))/len_original)*100,1),text=multidoc_summary))

    return multidoc_summary


# END NOTEBOOKS 

def nlp_entities(kg:KnowledgeGraph, request:Request):
    if request.uid is not None:
        add_entities(kg, request)
    else:
         print 

def connect_request(kg:KnowledgeGraph, request:Request):
    if request.uid is not None:
         connect_entities(kg, request)


def get_ranked_content(request_uid:str, kg:KnowledgeGraph) -> list[RankedContent]:
    out=[]
    ##content_scores=dict()

    print("Started Ranking Content")

    request=kg.get_request_by_uid(request_uid)

    ##if request is not None:
    ##    distance_scores=dict()
    ##    distance_decay(kg,distance_scores,request.uid,1.3)
    ##   content_scores=average_content(kg,distance_scores)

    for content in kg.get_all_content():
        score= score_new(kg,request,content) ## new

    ##    score = 0.00001
    ##    if request is not None:
    ##        if content.uid in content_scores:
    ##            score = content_scores[content.uid]
        
        rc=RankedContent(
            request_uid=request_uid,
            content_uid=content.uid,
            recommendation_uid="TODO",
            title=content.title,
            source=content.is_from.single().name,
            date=content.date.strftime('%Y-%m-%d'),
            age=(date.today()-content.date).days,
            relevance=score,
            cited=False
            )
        out.append(rc)

        print("added: {t} with score of {s}".format(t=rc.title,s=score))
    return out

# produces a text string from a node or edge, if supported
def explain(something):
    if hasattr(something, 'to_text') and callable(something.to_text):
        return something.to_text()
    return ""

def get_tailored_summary(kg:KnowledgeGraph,request:Request,content:Content) -> str:
    path_text=""
    path=kg.shortest_path(request,content)

    if path is not None:
        for hop in path:
            path_text+=explain(hop)+" "

    out= summarizeWithFocus(content.text,str(path_text),request.text)
    return out


def get_relevant_subgraph(kg:KnowledgeGraph, request_uid:str, content_uid:str) -> dict:
    request= kg.get_request_by_uid(request_uid)
    content= kg.get_content_by_uid(content_uid)

    print ("Request: {}".format(request.to_text()))
    print ("Content: {}".format(content.to_text()))

    re_list:list[Entity]= kg.get_entities_by_request(request)
    print ("{} Entities".format(len(re_list)))

    unique=dict()
    nodes=dict()
    edges=[]

    # nodes built as dict first to enforce uniqueness of node entries
    nodes[request_uid]={
            "type": "Request",
            "text": request.title
        }
    nodes[content_uid]={
        "type": "Content",
        "text": content.title
    }

    for e in re_list:
        nodes[e.uid]={
            "type": "Entity",
            "text": e.text
        }
        edges.append({
            "source": request_uid,
            "target": e.uid,
            "text":"-"
        })
     
        try:
            q = kg.neomodel_query("""
                MATCH path=shortestPath((s)-[*..10]-(e))
                WHERE s.uid='{start_id}'
                AND e.uid='{end_id}'                         
                AND NONE(n IN nodes(path) WHERE 'Recommendation' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Tldr' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Recommendation' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Summary' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Feedback' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Source' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Content' IN LABELS(n) AND n.uid<>"{end_id}")             
                AND NONE(n IN nodes(path) WHERE 'User' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'EvalKey' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Section' IN LABELS(n))
                AND NONE(n IN nodes(path) WHERE 'Similarity' IN LABELS(n))
                RETURN path
                """.format(start_id=e.uid, end_id=content_uid))
            path=q[0][0][0]
            previous= e.uid

            for n in path.nodes:
                n_type=type(n).__name__
                n_text="-"
                match n_type:
                    case "Request":
                        n_text=n.title
                    case "Entity":
                        n_text=""+n.type+":"+n.text
                    case "TextChunk":
                        n_text="TextChunk[{}]: {}".format(n.index,n.text)
                    case "Content":
                        n_text=n.title
                    case "ReferenceNode":
                        n_text=""+n.type+":"+n.text
                    case _:
                        n_text="-"
                                
                nodes[n.uid]={
                    "type":n_type,
                    "text":n_text
                }
                edges.append({
                    "source": previous,
                    "target": n.uid,
                    "text": "-"
                })
                previous=n.uid
                print ("node type: {} with text: {}".format(n_type,n_text))

        except Exception as error:
           print("Error: Building subgraph from paths: {}".format(error.with_traceback()))

    # rebuild nodes as list with ids inside objects
    node_list=[]
    for n in nodes:
        node_list.append({
            "id": n,
            "type": nodes[n]["type"],
            "text": nodes[n]["text"]
        })

    return {
        "start": request_uid,
        "end": content_uid,
        "nodes": node_list,
        "links": edges
    }