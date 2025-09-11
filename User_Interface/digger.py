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

logging.getLogger("Digger").setLevel(logging.INFO)  # More output

from sentence_transformers import SentenceTransformer, util

from dotenv import load_dotenv

# Get absolute path to other OpenTLDR classes
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Import path for Summarizer class
summ_dir = os.path.join(parent_dir, "Stage_5_Summarize")
sys.path.append(summ_dir)
import Summarizer


load_dotenv()
load_dotenv("{d}/.env".format(d=os.getcwd()))
load_dotenv("{d}/../.env".format(d=os.getcwd()))


def _getenv(variable: str, default: str):
    """
    _getenv(variable, default) attempts to resolve the value of the environment variable specified.
    If it cannot find the variable in the OS or .env (from dotenv package) it will fail over to the
    provided default value while giving a warning to the logging system.
    """
    value: str = os.getenv(variable)
    if value == None:
        log.warning(
            "No environment variable '"
            + variable
            + "' so defaulting to '"
            + default
            + "'."
        )
        return default
    return value


class RankedContent(BaseModel):
    request_uid: str
    content_uid: str
    recommendation_uid: str
    title: str
    source: str
    date: str
    age: int
    relevance: float
    cited: bool


# FROM NOTEBOOK CONNECT

sentence_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(sentence_embedding_model)


def cosin_similarity(string_1: str, string_2: str):
    if string_1 == string_2:
        return 1.0

    # compute the embeddings for each string
    embedding_1 = model.encode(string_1, convert_to_tensor=True)
    embedding_2 = model.encode(string_2, convert_to_tensor=True)

    # compute the cosin similarity of the two embeddings
    similarity = util.cos_sim(embedding_1, embedding_2).cpu().numpy()[0][0]

    return round(similarity, 4)


# FROM NOTEBOOK RECOMMEND

decay_rate = 0.2  ## 1


def distance_decay(
    kg: KnowledgeGraph, distance_scores:dict, node_id: str, score: float
):
    # print ("\nRecursing on node {id} with score of {score}.".format(id=node_id, score=score))
    node = kg.get_by_uid(node_id)
    # print ("\tNode is: {}".format(node.to_text()))

    # Avoid looking along paths that circumvent reference data
    nodetype = str(type(node))
    for avoid in [
        "Source",
        "User",
        "Recommendation",
        "Summary",
        "Feedback",
        "User",
        "TldrEntry",
        "Tldr",
        "Source",
        "EvalKey",
    ]:
        if avoid in nodetype:
            # print("\tAvoiding path through a {type} node.".format(type=nodetype))
            return

    prev_score = distance_scores.get(str(node_id), -999)
    if prev_score >= score:
        # print ("\tPreviously at node {id} with score of {prev} vs now with {current}.".format(id=node_id, prev=prev_score, current=score))
        return
    else:
        # print ("\tAssigning node {id} a score of {current}.".format(id=node_id,current=score))
        distance_scores[str(node_id)] = score

    # include Content nodes only once
    if nodetype == "Content":
        return

    # Since this is the lowest so far, we have to also check its neighbors
    neighbor_records, meta = kg.neo4j_query(
        "MATCH (h)<-[]->(n) WHERE h.uid='{uid}' RETURN n.uid".format(uid=node_id)
    )
    for n_record in neighbor_records:
        other_id = n_record.data()["n.uid"]

        # recurse on nodes that are not too far already
        other_score = score - decay_rate
        if other_score > 0.0:
            distance_decay(kg, distance_scores, other_id, round(other_score, 2))

    return


def normalize(score: float) -> float:
    out = score + (3 * decay_rate)
    if out < 0.0:
        return 0.0
    else:
        return out


def average_content(kg: KnowledgeGraph, distance_scores: dict):
    avg_scores = dict()
    all_content = kg.get_all_content()
    for article in all_content:
        acc = normalize(distance_scores.get(str(article.uid), 0.0))
        count = 1
        if acc > 0.0:
            for e in kg.get_entities_by_content(article):
                acc += normalize(distance_scores.get(str(e.uid), 0.0))
                count += 1
        else:
            acc = 0.0
        avg_scores[str(article.uid)] = round(acc / count, 3)
    return avg_scores


def score_new(kg: KnowledgeGraph, request: Request, content: Content) -> float:
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

    count = 1
    acc = 0.0
    decay_rate = 0.2

    try:
        q = kg.neomodel_query(
            shortest_path_cypher.format(start_id=request.uid, end_id=content_uid)
        )
        path = q[0][0][0]
        acc = 1.0 - ((len(path.nodes) - 5) * decay_rate)
    except Exception:
        return 0.0  # no path found 

    if acc <= 0.0:
        return 0.0

    for e in kg.get_entities_by_request(request):
        count += 1
        try:
            q = kg.neomodel_query(
                shortest_path_cypher.format(start_id=e.uid, end_id=content_uid)
            )
            path = q[0][0][0]
            acc += 1.0 - ((len(path.nodes) - 4) * decay_rate)
        except Exception as e:
            acc = 0.0  # no addition if no path found

    out = round(acc / count, 3)

    if out > 1.0:
        return 1.0

    return out


# FROM NOTEBOOK SUMMARIZE

llm: Summarizer = Summarizer.getSummarizer(None, logging_level=logging.ERROR)


def group_summary(
    summaries: str, info_request: str = "Tell me what these articles have in common."
) -> str:
    llm_prompt = """
        Given the following news articles respond to this request: "{request}"
        Also with respect to the request, identify what the articles have in common and then highlight the main differences between the articles.
        News articles below are preceded by an article title and separated from the other news articles using '========'. \n
        Summarize the following news articles:\n {multicontent}
    """
    # Assemble a prompt to summarize the article
    summary_prompt: str = llm_prompt.format(
        multicontent=summaries, request=info_request
    ).strip()
    if len(summary_prompt) > 2000:
        summary_prompt = summary_prompt[0:2000]
    return llm.summarize(summary_prompt)


# an attempt at starting a customized prompt for summary
def summarizeWithFocus(content_body, focus_text, info_request) -> str:
    llm_prompt: str = """
        Given the following statements as background facts to use: {knowledge}
        Write a concise summary of the following news article: {content}
        Focus the concise summary to respond appropriately to this specific request: {request}
        """
    # Assemble a prompt to summarize the article
    summary_prompt: str = llm_prompt.format(
        knowledge=focus_text, content=content_body, request=info_request
    ).strip()
    if len(summary_prompt) > 2000:
        summary_prompt = summary_prompt[0:2000]
    return llm.summarize(summary_prompt)


def run_group_summary(kg: KnowledgeGraph, request: Request, uids: list[str]) -> str:
    len_original = 0
    len_summaries = 0
    multisum = ""
    multidoc_summary = "Sorry - No Group Summary Created."

    for uid in uids:
        print("summarizing group with {}".format(uid))
        content = kg.get_content_by_uid(uid)
        len_original += len(content.text)

        if content.metadata is not None:
            summary = content.metadata["summary"]
            len_summaries += len(summary)

            if len(summary) > 0:
                multisum += "\n\n========\n\n\nnews- {}:\n".format(content.title)
                multisum += "{}\n".format(summary)

            # in the case there is only one, just sent that summary instead
            if len(uids) == 1:
                return summary
        else:
            print("skipping - no metadata summary found")

    if len(multisum) > 0:
        multidoc_summary = group_summary(multisum, request.text)
        print(
            "\nSummary reduced {reduction}% of content:\t{text}".format(
                reduction=round(
                    ((len_original - len(multidoc_summary)) / len_original) * 100, 1
                ),
                text=multidoc_summary,
            )
        )

    return multidoc_summary


# END NOTEBOOKS


def get_ranked_content(request_uid: str, kg: KnowledgeGraph) -> list[RankedContent]:
    out = []
    print("Started Ranking Content")
    request = kg.get_request_by_uid(request_uid)

    for content in kg.get_all_content():
        score = score_new(kg, request, content)  ## new
        rc = RankedContent(
            request_uid=request_uid,
            content_uid=content.uid,
            recommendation_uid="TODO",
            title=content.title,
            source=content.is_from.single().name,
            date=content.date.strftime("%Y-%m-%d"),
            age=(date.today() - content.date).days,
            relevance=score,
            cited=False,
        )
        out.append(rc)

        print("added: {t} with score of {s}".format(t=rc.title, s=score))
    return out


# produces a text string from a node or edge, if supported
def explain(something):
    if hasattr(something, "to_text") and callable(something.to_text):
        return something.to_text()
    return ""


def get_tailored_summary(kg: KnowledgeGraph, request: Request, content: Content) -> str:
    path_text = ""
    path = kg.shortest_path(request, content)

    if path is not None:
        for hop in path:
            path_text += explain(hop) + " "

    out = summarizeWithFocus(content.text, str(path_text), request.text)
    return out


def get_relevant_subgraph(
    kg: KnowledgeGraph, request_uid: str, content_uid: str
) -> dict:
    request = kg.get_request_by_uid(request_uid)
    content = kg.get_content_by_uid(content_uid)

    print("Request: {}".format(request.to_text()))
    print("Content: {}".format(content.to_text()))

    re_list: list[Entity] = kg.get_entities_by_request(request)
    print("{} Entities".format(len(re_list)))

    nodes = dict()
    edges = []

    # nodes built as dict first to enforce uniqueness of node entries
    nodes[request_uid] = {"type": "Request", "text": request.title}
    nodes[content_uid] = {"type": "Content", "text": content.title}

    for e in re_list:
        nodes[e.uid] = {"type": "Entity", "text": e.text}
        edges.append({"source": request_uid, "target": e.uid, "text": "-"})

        try:
            q = kg.neomodel_query(
                """
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
                """.format(start_id=e.uid, end_id=content_uid)
            )

            if q is None or len(q[0]) == 0:
                print("No path found for entity: {}".format(e.to_text()))
                continue

            path = q[0][0][0]
            previous = e.uid

            for n in path.nodes:
                n_type = type(n).__name__
                n_text = "-"
                match n_type:
                    case "Request":
                        n_text = n.title
                    case "Entity":
                        n_text = "" + n.type + ":" + n.text
                    case "TextChunk":
                        n_text = "TextChunk[{}]: {}".format(n.index, n.text)
                    case "Content":
                        n_text = n.title
                    case "ReferenceNode":
                        n_text = "" + n.type + ":" + n.text
                    case _:
                        n_text = "-"

                nodes[n.uid] = {"type": n_type, "text": n_text}
                edges.append({"source": previous, "target": n.uid, "text": "-"})
                previous = n.uid
                print("node type: {} with text: {}".format(n_type, n_text))

        except Exception as error:
            print(
                "Error: Building subgraph from paths: {}".format(
                    error.with_traceback(None)
                )
            )

    # rebuild nodes as list with ids inside objects
    node_list = []
    for n in nodes:
        node_list.append({"id": n, "type": nodes[n]["type"], "text": nodes[n]["text"]})

    return {
        "start": request_uid,
        "end": content_uid,
        "nodes": node_list,
        "links": edges,
    }
