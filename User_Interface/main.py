import json
from datetime import datetime, date

from fastapi import Request as Http_Request
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    Response,
    HTMLResponse,
    RedirectResponse,
    PlainTextResponse,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from jinja2 import Environment, FileSystemLoader


from typing import Annotated, Optional, List

from pydantic import BaseModel

from opentldr import KnowledgeGraph, Workflow, log
from opentldr.Domain import ReferenceNode, ReferenceEdge, User, Request, Tldr, TldrEntry
from opentldr.Domain import inferDateFormat

app = FastAPI()

app.mount("/resources", StaticFiles(directory="resources"), name="resources")

# app.config["PREFERRED_URL_SCHEME"] = "https"

# If you plan to host a Web-based UI on a different port and it needs to make REST
# calls into this API, you will want to specifically allow it. This is required
# because by default, cross-site calls are blocked as are security cookies.
#
# READ THIS: https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
#

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://opentldr.ncsu-las.priv:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Utilities to format data for the responses


def to_json_list(list_of_domain_obs: list, kg: KnowledgeGraph) -> str:
    """
    Utility to convert list of domain objects to string containing a json list of json objects.
    This is used over default conversion to better handle connection embedding.
    If NeoModel worked with Pydantic, we would not have this issue.
    """
    if list_of_domain_obs is None:
        log.warn("Creating empty JSON list.")
        return "[]"
    else:
        out: list[str] = []
        for obj in list_of_domain_obs:
            # Strip out Neo4j ids in favor of opentldr uids
            # if hasattr(obj, 'element_id_property'):
            #    delattr(obj,'element_id_property')
            out.append(obj.to_json(kg))
        return "[ " + ", ".join(out) + "]"


def response_as_json(data: str):
    return Response(content=data, media_type="application/json")


# API Methods

# ----------------------
# Reference Data
# ----------------------


@app.get("/reference")
async def get_all_reference_data():
    with KnowledgeGraph() as kg:
        n: list[ReferenceNode] = kg.get_all_reference_nodes()
        e: list[ReferenceEdge] = kg.get_all_reference_edges()
        return response_as_json(
            '{ "nodes" : '
            + to_json_list(n, kg)
            + ', "edges" : '
            + to_json_list(e, kg)
            + "}"
        )


@app.get("/reference/nodes")
async def get_all_reference_nodes():
    with KnowledgeGraph() as kg:
        return response_as_json(to_json_list(kg.get_all_reference_nodes(), kg))


@app.get("/reference/nodes/{uid}")
async def get_reference_node_by_uid(uid: Optional[str]):
    with KnowledgeGraph() as kg:
        node = kg.get_reference_node_by_uid(uid)
        if node is None:
            raise HTTPException(
                status_code=404, detail="Reference node ({id}) not found".format(id=uid)
            )
        return response_as_json(node.to_json(kg))


class Payload_Reference_Node(BaseModel):
    """
    Pydantic class for automatically parsing http request objects from json.
    """

    type: str
    text: str
    hypothesized: bool = False


@app.post("/reference/nodes")
async def add_user(new_reference_node: Payload_Reference_Node):
    node: ReferenceNode = None
    with KnowledgeGraph() as kg:
        node = kg.add_reference_node(
            new_reference_node.text,
            new_reference_node.type,
            new_reference_node.hypothesized,
        )
        return response_as_json(node.to_json(kg))


@app.get("/reference/edges")
async def get_all_reference_edges():
    with KnowledgeGraph() as kg:
        return response_as_json(to_json_list(kg.get_all_reference_edges(), kg))


@app.get("/reference/edges/{uid}")
async def get_reference_edge_by_uid(uid: Optional[str]):
    with KnowledgeGraph() as kg:
        edge = kg.get_reference_edge_by_uid(uid)
        if edge is None:
            raise HTTPException(
                status_code=404, detail="Reference edge ({id}) not found".format(id=uid)
            )

        return response_as_json(edge.to_json(kg))


class Payload_Reference_Edge(BaseModel):
    """
    Pydantic class for automatically parsing http request objects from json.
    """

    from_uid: str
    to_uid: str
    type: str
    text: str
    hypothesized: bool = False


@app.post("/reference/edges")
async def add_reference_edge(new_reference_edge: Payload_Reference_Edge):
    edge: ReferenceEdge = None
    with KnowledgeGraph() as kg:
        from_node = kg.get_reference_ndoe_by_uid(new_reference_edge.from_uid)
        if from_node is None:
            raise HTTPException(
                status_code=404,
                detail="Reference node ({id}) not found".format(
                    id=new_reference_edge.from_uid
                ),
            )

        to_node = kg.get_reference_ndoe_by_uid(new_reference_edge.to_uid)
        if to_node is None:
            raise HTTPException(
                status_code=404,
                detail="Reference node ({id}) not found".format(
                    id=new_reference_edge.to_uid
                ),
            )

        edge = kg.add_reference_edge(
            from_node,
            to_node,
            new_reference_edge.text,
            new_reference_edge.type,
            new_reference_edge.hypothesized,
        )
        return response_as_json(edge.to_json(kg))


# ----------------------
# Users
# ----------------------


@app.get("/users")
async def get_all_users():
    with KnowledgeGraph() as kg:
        data = to_json_list(kg.get_all_users(), kg)
    return response_as_json(data)


@app.get("/users/{user_uid}")
async def get_user_by_uid(user_uid: Optional[str]):
    with KnowledgeGraph() as kg:
        user = kg.get_user_by_uid(user_uid)
        if user is None:
            user = kg.get_user_by_name(user_uid)
        if user is None:
            raise HTTPException(
                status_code=404, detail="User ({id}) not found".format(id=user_uid)
            )
        return response_as_json(user.to_json(kg))


class Payload_User(BaseModel):
    """
    Pydantic class for automatically parsing http request objects from json.
    """

    user_name: str
    user_email: str


@app.post("/users/")
async def add_user(new_user: Payload_User):
    user: User = None
    with KnowledgeGraph() as kg:
        user = kg.get_user_by_name(new_user.user_name)
        if user is None:
            user = kg.add_user(new_user.user_name, new_user.user_email)

        return response_as_json(user.to_json(kg))


# ----------------------
# Requests
# ----------------------


@app.get("/requests")
async def get_all_requests():
    with KnowledgeGraph() as kg:
        data = to_json_list(kg.get_all_requests(), kg)
    return response_as_json(data)


@app.get("/requests/{uid}")
async def get_request_by_uid(uid: str):
    with KnowledgeGraph() as kg:
        r: Request = kg.get_request_by_uid(uid)
        if r is None:
            raise HTTPException(
                status_code=404, detail="Request ({id}) not found".format(id=uid)
            )

        return response_as_json(r.to_json(kg))


@app.delete("/requests/{uid}")
async def delete_request_by_uid(uid: str):
    with KnowledgeGraph() as kg:
        r: Request = kg.get_request_by_uid(uid)
        if r is None:
            raise HTTPException(
                status_code=404, detail="Request ({id}) not found".format(id=uid)
            )

        kg.delete_request_by_uid(uid)
        return {"message": "Request deleted successfully"}


class Payload_UserRequest(BaseModel):
    """
    Pydantic class for automatically parsing http request objects from json.
    """

    user_name: str
    user_email: str
    request_title: str
    request_text: str


@app.post("/requests/")
async def add_request(new_request: Payload_UserRequest):
    user: User = None

    if not new_request.user_name or not new_request.user_email:
        raise HTTPException(
            status_code=403, detail="User information required for new Request"
        )
    if not new_request.request_title or not new_request.request_text:
        raise HTTPException(
            status_code=403, detail="Request title and text required for new Request"
        )

    with KnowledgeGraph() as kg:
        # ensure that this user is in KG
        user = kg.get_user_by_name(new_request.user_name)
        if user is None:
            user = kg.add_user(new_request.user_name, new_request.user_email)

        # create a new request
        r: Request = kg.add_request(
            new_request.request_title, new_request.request_text, user
        )

        ingest_workflow = {
            # Where a read-only version of the notebook AFTER execution is stored
            "Output": "./READ_ONLY_OUTPUT",
            # Parameters passed into all notebooks in workflow
            "Common": {
                "logging_level": 10,
                "verbose": False,
            },
            "Notebooks": [
                [
                    "../Stage_2_Ingest/Load_Requests.ipynb",
                    {"data_repo_config": None, "list_of_uids": [r.uid]},
                ],
                # Perform Analytics to link entities in Requests and Content nodes
                [
                    "../Stage_3_Connect/Entity_Cosin_Similarity.ipynb",
                    {
                        "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "connect_threshold": 0.6,
                        "hypothesize_threshold": 0.9,
                    },
                ],
                # Compute recommendations based on relevance of content to request
                [
                    "../Stage_4_Recommend/Shortest_Path_Scoring.ipynb",
                    {
                        "recommendation_threshold": 0.6,
                        "delete_existing_recommendations": False,
                        "list_of_uids": [r.uid],
                    },
                ],
                # Generate a summary of the content that is tailored with respect to the request and useful reference knowledge
                [
                    "../Stage_5_Summarize/Tailored_Abstractive_Summary.ipynb",
                    {
                        "llm_config": {
                            "type": "GPT4ALL",
                            "device": "cpu",
                            "model": "../LLM_Models/mistral-7b-openorca.gguf2.Q4_0.gguf",
                        },
                        "llm_prompt": "You are a helpful assistant responding to the request: {request} \n\n and were given these facts: {knowledge} \n\n Concisely summarize the following article: {content}",
                        "list_of_uids": [r.uid],
                    },
                ],
                # Produce a TLDR Report for each request
                ["../Stage_6_Produce/Build_TLDR.ipynb", {"list_of_uids": [r.uid]}],
            ],
        }
        wf = Workflow(ingest_workflow)
        wf.run()

        return response_as_json(r.to_json(kg))


# ----------------------
# TLDRs
# ----------------------


def produce_tldr_entry(kg: KnowledgeGraph, entry: TldrEntry) -> dict:
    e: dict = dict()
    e["uid"] = entry.uid
    e["link"] = entry.link
    e["title"] = entry.title
    e["content_type"] = entry.type
    e["score"] = entry.score
    e["score_text"] = entry.score_to_text()
    e["summary"] = entry.summary
    return e


def produce_tldr(kg: KnowledgeGraph, tldr: Tldr) -> dict:
    out: dict = dict()
    out["date"] = tldr.date.strftime("%m/%d/%Y")
    out["uid"] = tldr.uid

    request: Request = tldr.response_to.single()
    out["request_uid"] = request.uid
    out["request_title"] = request.title

    user: User = tldr.response_to.single().requested_by.single()
    out["user"] = user.name
    out["email"] = user.email

    unsorted = []
    for e in tldr.contains:
        new_entry = produce_tldr_entry(kg, e)
        unsorted.append(new_entry)

    entries = []
    for e in sorted(unsorted, key=lambda entry: entry["score"], reverse=True):
        e["order"] = len(entries)
        entries.append(e)

    out["entries"] = entries
    return out


@app.get("/tldrs")
async def get_all_tldrs():
    out: list[dict] = []
    with KnowledgeGraph() as kg:
        tldrs: list[Tldr] = []
        tldrs = kg.get_all_tldrs()
        for tldr in tldrs:
            out.append(produce_tldr(kg, tldr))
        return response_as_json(json.dumps(out))


@app.get("/tldrs/{request_uid}/{date}")
async def get_tldrs_for_request_uid_and_date(request_uid: str, date: Optional[str]):
    out: list[dict] = []
    with KnowledgeGraph() as kg:
        tldrs: list[Tldr] = []

        if date is not None:
            d: date = inferDateFormat(date).date()
            tldr = kg.get_tldr_by_uid_and_date(request_uid, d)
            if tldr is None:
                raise HTTPException(
                    status_code=404,
                    detail="TLDR for Request ({id}) and Date ({date}) not found".format(
                        id=request_uid, date=d
                    ),
                )
            tldrs.append(tldr)
        else:
            tldrs = kg.get_tldr_by_request_uid(request_uid)

        for tldr in tldrs:
            out.append(produce_tldr(kg, tldr))
        return response_as_json(json.dumps(out))


@app.get("/tldrs/{uid}")
async def get_tldr_by_uid(uid: str):
    with KnowledgeGraph() as kg:
        tldr = kg.get_tldr_by_uid(uid)

        if tldr is None:
            raise HTTPException(
                status_code=404, detail="TLDR ({id}) not found".format(id=uid)
            )
        return response_as_json(json.dumps(produce_tldr(kg, tldr)))


# ----------------------
# Home Page
# ----------------------
# This is the default URL for testing that your API is running.


def produce_request_line(kg: KnowledgeGraph, request: Request) -> dict:
    out: dict = dict()

    out["uid"] = request.uid
    out["title"] = request.title
    out["text"] = request.text

    user: User = request.requested_by.single()
    out["user"] = user.name
    out["email"] = user.email

    tldrs = kg.get_tldr_by_request_uid(request.uid)
    tldr_list_out = []
    for tldr in tldrs:
        tldr_out = dict()
        tldr_out["uid"] = tldr.uid
        tldr_out["date"] = tldr.date
        tldr_list_out.append(tldr_out)
    out["tldrs"] = tldr_list_out

    return out


@app.get("/", response_class=HTMLResponse)
async def root(http_request: Http_Request):
    # With a proxy running for authentication, the user information is passed into the request
    # in this case it comes in as the "remote_user" attribute.

    # Security Note: This code is not hardened for production. For example:
    # - The DEFAULT behavior is to just not filter by user
    # - Most of the REST calls do NOT check user, so this is cosmetic

    user_email: str = None
    if "remote_user" in http_request.headers:
        user_email = http_request.headers["remote_user"]
        print("Found remote_user: {email}".format(email=user_email))

    with KnowledgeGraph() as kg:
        out: list[dict] = []
        requests: list[Request] = kg.get_all_requests()

        for request in requests:
            if user_email is not None:
                user: User = request.requested_by.single()
                if (
                    user.email == user_email
                    or user.email == "digger@opentldr.org"
                    or user.name == "public"
                ):
                    out.append(produce_request_line(kg, request))
            else:
                out.append(produce_request_line(kg, request))

    # This returns the main.html template in the templates directory
    return templates.TemplateResponse(
        request=http_request,
        name="main.html",
        context={"data": out, "auth": user_email},
    )


# ----------------------
# HTML Report
# ----------------------


@app.get("/reports/{request_uid}/{date}", response_class=HTMLResponse)
async def tldr_list_report(
    http_request: Http_Request, request_uid: str, date: Optional[str]
):
    with KnowledgeGraph() as kg:
        d = None
        if date is not None:
            d = inferDateFormat(date).date()
        else:
            d = date.now()

        tldr: Tldr = kg.get_tldr_by_uid_and_date(request_uid, d)
        if tldr is None:
            raise HTTPException(
                status_code=404,
                detail="TLDR Report for Request ({id}) and Date ({date}) not found".format(
                    id=request_uid, date=d
                ),
            )
        tldr_json = produce_tldr(kg, tldr)

        # This returns the tldr.html template in the templates directory
        return templates.TemplateResponse(
            request=http_request, name="tldr.html", context={"tldr": tldr_json}
        )


@app.get("/reports/{uid}", response_class=HTMLResponse)
async def tldr_report(http_request: Http_Request, uid: str):
    with KnowledgeGraph() as kg:
        tldr: Tldr = kg.get_tldr_by_uid(uid)
        if tldr is None:
            raise HTTPException(
                status_code=404,
                detail="TLDR Report for UID ({id}) not found".format(id=uid),
            )
        tldr_json = produce_tldr(kg, tldr)

    # This returns the tldr.html template in the templates directory
    return templates.TemplateResponse(
        request=http_request, name="tldr.html", context={"tldr": tldr_json}
    )


# ----------------------
# Feedback
# ----------------------


@app.get("/forward/{tldr_entry_uid}", response_class=HTMLResponse)
async def get_forwarding_to_content_link(tldr_entry_uid: str):
    with KnowledgeGraph() as kg:
        tldr_entry = kg.get_tldr_entry_by_uid(tldr_entry_uid)
        if tldr_entry is None:
            raise HTTPException(
                status_code=404,
                detail="TLDR Entry for ({id}) not found".format(id=tldr_entry_uid),
            )

        feedback = kg.add_feedback_click(tldr_entry, datetime.now().date())
        return RedirectResponse(tldr_entry.link)


class Payload_Feedback(BaseModel):
    """
    Pydantic class for automatically parsing http request objects from json.
    """

    feedback_entry_id: str
    feedback_rating: float


@app.post("/feedback/", response_class=PlainTextResponse)
async def set_feedback_rating(feedback: Payload_Feedback):
    print(feedback)
    entry_id = feedback.feedback_entry_id
    rating = feedback.feedback_rating

    if rating is None or rating > 1.0 or rating < 0.0:
        return "Error, not a valid rating."

    if entry_id is None:
        return "Error, no TLDR Entry uid provided."

    entry: TldrEntry = None
    with KnowledgeGraph() as kg:
        entry = kg.get_tldr_entry_by_uid(entry_id)
        if entry is None:
            # this is likely an outdated TLDR entry so lets flag it and stop
            return "Error, no TLDR Entry for uid ({uid}) for feedback.".format(
                uid=feedback.feedback_entry_id
            )

        feedback = kg.add_feedback_rating(entry, feedback.feedback_rating)
        return "Success"


# ----------------------
# Timeline
# ----------------------


def produce_request_timeline(
    kg: KnowledgeGraph, request: Request, tldrs: list[Tldr]
) -> dict:
    out: dict = dict()

    #    out["title"] = {
    #            "text": {
    #            "headline": request.title,
    #            "text": request.text
    #        }
    #    }

    events_list = [
        {"start_date": {"year": 2022}, "group": "very high"},
        {"start_date": {"year": 2022}, "group": "high"},
        {"start_date": {"year": 2022}, "group": "medium"},
        {"start_date": {"year": 2022}, "group": "low"},
        {"start_date": {"year": 2022}, "group": "very low"},
    ]
    for tldr in tldrs:
        d = tldr.date
        for entry in tldr.contains:
            events_list.append(
                {
                    "media": {
                        "url": "/resources/news.png",
                        "link": entry.link,
                    },
                    "start_date": {"year": d.year, "month": d.month, "day": d.day},
                    "text": {"headline": entry.title, "text": entry.summary},
                    "unique_id": entry.uid,
                    "group": entry.score_to_text(),
                }
            )

    out["events"] = events_list
    return out


@app.get("/timeline/{uid}", response_class=HTMLResponse)
async def timeline(http_request: Http_Request, uid: str):
    with KnowledgeGraph() as kg:
        request: Request = kg.get_request_by_uid(uid)
        tldrs: list[Tldr] = kg.get_tldr_by_request_uid(uid)

        if request is None:
            raise HTTPException(
                status_code=404,
                detail="Request for UID ({id}) not found".format(id=uid),
            )

        timeline_json = produce_request_timeline(kg, request, tldrs)

    # This returns the timeline.html template in the templates directory
    return templates.TemplateResponse(
        request=http_request,
        name="timeline.html",
        context={"timeline_json": timeline_json, "request_title": request.title},
    )


# DIGGER

from typing import Optional

# mimics a Request object but with Pydantic syntex...


class DiggerRequest(BaseModel):
    uid: str = ""
    metadata: Optional[str] = ""
    title: str = ""
    text: str = ""
    user: str = "digger"
    email: str = "digger@opentldr.org"


@app.get("/digger", response_class=HTMLResponse)
async def digger_new(http_request: Http_Request):
    # default request data
    default_request_json = DiggerRequest().json()

    return templates.TemplateResponse(
        request=http_request,
        name="digger.html",
        context={"request_json": default_request_json},
    )


@app.get("/digger/{uid}", response_class=HTMLResponse)
async def digger_existing(http_request: Http_Request, uid: str):
    with KnowledgeGraph() as kg:
        request_node = kg.get_request_by_uid(uid)

        if request_node is None:
            raise HTTPException(
                status_code=404, detail="Request node ({id}) not found".format(id=uid)
            )

        request_json = DiggerRequest.model_validate_json(request_node.to_json(kg))

        return templates.TemplateResponse(
            request=http_request,
            name="digger.html",
            context={"request_json": request_json.json()},
        )


@app.post("/digger/update_request")
async def digger_update_request(dr: DiggerRequest):
    if not dr.user or not dr.email:
        raise HTTPException(
            status_code=403, detail="User information required for new Request"
        )

    if not dr.title or not dr.text:
        raise HTTPException(
            status_code=403, detail="Request title and text required for new Request"
        )

    r: Request = None

    with KnowledgeGraph() as kg:
        if dr.uid == "":
            # ensure that this user is in KG
            user = kg.get_user_by_name(dr.user)
            if user is None:
                user = kg.add_user(dr.user, dr.email)

            r: Request = kg.add_request(dr.title, dr.text, user)
            dr = DiggerRequest.model_validate_json(r.to_json(kg))
        else:
            r: Request = kg.get_request_by_uid(dr.uid)
            if r is None:
                raise HTTPException(
                    status_code=403, detail="Invalid Request UID updated"
                )
            r.title = dr.title
            r.text = dr.text
            r.save()
            dr = DiggerRequest.model_validate_json(r.to_json(kg))

        # Remove all existing entities and re-run the ingestion and connection notebooks
        # Otherwise we will get multiple edges to entities each time we update a request
        existing_entities=kg.get_entities_by_request(r)
        for e in existing_entities:
            kg.delete_entity(e)

        update_request_workflow = {
            # Where a read-only version of the notebook AFTER execution is stored
            "Output": "./READ_ONLY_OUTPUT",
            # Parameters passed into all notebooks in workflow
            "Common": {
                "logging_level": 10,
                "verbose": False,
            },
            "Notebooks": [
                [
                    "../Stage_2_Ingest/Load_Requests.ipynb",
                    {
                        "data_repo_config": None, 
                        "list_of_uids": [r.uid]
                    },
                ],
                # Perform Analytics to link entities in Requests and Content nodes
                [
                    "../Stage_3_Connect/Entity_Cosin_Similarity.ipynb",
                    {
                        "sentence_embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "connect_threshold": 0.6,
                        "hypothesize_threshold": 0.9,
                    },
                ],
            ],
        }
        wf = Workflow(update_request_workflow)
        wf.run()

        # digger.nlp_entities(kg, r)
        # digger.connect_request(kg,r)

        return response_as_json(dr.json())


class Uid(BaseModel):
    uid: str
    request_uid: str


import digger


@app.get("/digger/get_ranked_content/{uid}", response_model=List[digger.RankedContent])
async def digger_get_ranked_content(http_request: Http_Request, uid: str):
    with KnowledgeGraph() as kg:
        all_content: List = digger.get_ranked_content(uid, kg)
        return all_content


@app.post("/digger/get_group_summary", response_model=str)
async def digger_get_group_summary(luids: List[Uid]):
    out = ""
    uids = []
    request_uid = ""
    for u in luids:
        uids.append(u.uid)
        request_uid = u.request_uid

    with KnowledgeGraph() as kg:
        request = kg.get_request_by_uid(request_uid)
        print("group summarize wrt: {}".format(request.text))
        out = digger.run_group_summary(kg, request, uids)

    return out


class SummaryRequest(BaseModel):
    request_uid: str
    content_uid: str


@app.post("/digger/get_tailored_summary", response_model=str)
async def digger_get_tailored_summary(sr: SummaryRequest):
    out = ""

    with KnowledgeGraph() as kg:
        r = kg.get_request_by_uid(sr.request_uid)
        c = kg.get_content_by_uid(sr.content_uid)
        out = digger.get_tailored_summary(kg, r, c)

    return out


class DiggerSubgraphNode(BaseModel):
    id: str
    type: str
    text: str


class DiggerSubgraphEdge(BaseModel):
    source: str
    target: str
    text: str


class DiggerSubGraph(BaseModel):
    start: str = ""
    end: str = ""
    nodes: list[DiggerSubgraphNode]
    links: list[DiggerSubgraphEdge]


@app.post("/digger/get_subgraph", response_model=DiggerSubGraph)
async def digger_get_subgraph(sr: SummaryRequest):
    out = ""

    with KnowledgeGraph() as kg:
        sg = digger.get_relevant_subgraph(kg, sr.request_uid, sr.content_uid)
        out = DiggerSubGraph.model_validate_json(json.dumps(sg))
        print("subgraph: {}".format(out))
    return out


@app.get("/digger/forward/{content_uid}", response_class=HTMLResponse)
async def digger_forward_to_content_link(content_uid: str):
    with KnowledgeGraph() as kg:
        c = kg.get_content_by_uid(content_uid)
        if c is None:
            raise HTTPException(
                status_code=404,
                detail="Content for ({id}) not found".format(id=content_uid),
            )

        return RedirectResponse(c.url)


class TldrCitation(BaseModel):
    request_uid: str
    content_uid: str
    score: float
    summary: str


@app.post("/digger/cite", response_model=str)
async def digger_cite(cite: TldrCitation):
    out = ""
    with KnowledgeGraph() as kg:
        r = kg.get_request_by_uid(cite.request_uid)
        c = kg.get_content_by_uid(cite.content_uid)

        rec = kg.add_recommendation(request=r, content=c, score=cite.score)
        sum = kg.add_summary(text=cite.summary, content=c, recommendation=rec)

        tldr = kg.get_tldr(r, date.today())

        if tldr is None:
            tldrlist = kg.get_tldr_by_request_uid(cite.request_uid)
            if len(tldrlist) > 0:
                tldr = tldrlist[0]

        if tldr is None:
            tldr = kg.add_tldr(r, date.today())

        tldr_entry = kg.add_entry_to_tldr(
            tldr=tldr, score=cite.score, recommendation=rec, summary=sum, content=c
        )

    return "success"
