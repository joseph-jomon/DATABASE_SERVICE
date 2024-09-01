# vdb_app/vdb_main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers import vdb_ingest
from services.vdb_es_client import init_es_client, close_es_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Elasticsearch client, initializing database connection
    init_es_client()

    yield  # The application runs here

    # Cleanup the Elasticsearch client
    close_es_client()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware if needed
origins = [
    "http://localhost",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vdb_ingest.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
