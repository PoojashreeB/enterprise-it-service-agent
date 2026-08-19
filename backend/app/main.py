from fastapi import FastAPI
from pydantic import BaseModel

from app.graph.workflow import build_service_desk_graph

app = FastAPI(
    title="Enterprise IT Service Desk Agent",
    version="1.0"
)

graph = build_service_desk_graph()


class ServiceDeskRequest(BaseModel):
    message: str


@app.get("/")
def health():
    return {
        "status": "running",
        "application": "Enterprise IT Service Desk Agent"
    }


@app.post("/service-desk")
def service_desk(request: ServiceDeskRequest):

    state = {
        "user_query": request.message
    }

    result = graph.invoke(state)

    return result