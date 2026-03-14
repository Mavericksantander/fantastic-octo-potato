import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import agents as agent_routes
from .routes import authorization as auth_routes
from .routes import external_onboarding as onboarding_routes
from .routes import heartbeat as heartbeat_routes
from .routes import metrics as metrics_routes
from .routes import reputation as reputation_routes
from .routes import search as search_routes
from .routes import tasks as task_routes

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ApexVeritasOS Governance API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_routes.router)
app.include_router(task_routes.router)
app.include_router(reputation_routes.router)
app.include_router(auth_routes.router)
app.include_router(onboarding_routes.router)
app.include_router(heartbeat_routes.router)
app.include_router(metrics_routes.router)
app.include_router(search_routes.router)


@app.on_event("startup")
def on_startup():
    init_db()
    logging.info("AVOS database schemas initialized")
