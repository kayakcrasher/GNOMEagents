from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import add_lead, get_leads, initialize_database
from app.leads import Lead, LeadCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="GNOME Agents",
    description="Small helpers. Big business.",
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "name": "GNOME Agents",
        "agent": "Leadkeeper",
        "version": "0.2.0",
        "status": "awake",
    }


@app.get("/health")
def health():
    return {"status": "green"}


@app.post("/leads", response_model=Lead, status_code=201)
def create_lead(lead: LeadCreate):
    return add_lead(lead)


@app.get("/leads", response_model=list[Lead])
def list_leads():
    return get_leads()


from app.leadkeeper import process_lead
from app.leads import LeadkeeperResult


@app.post(
    "/leadkeeper/process",
    response_model=LeadkeeperResult,
)
def leadkeeper_process(
    lead: LeadCreate,
    collection_id: str = "default",
):
    """Process a lead using GNOMEdata knowledge."""

    return process_lead(
        lead,
        collection_id=collection_id,
    )
