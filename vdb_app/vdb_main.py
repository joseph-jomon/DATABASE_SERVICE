# vdb_app/vdb_main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter
from fastapi_lifespan import Lifespan
from vdb_app.routers import vdb_ingest
from vdb_app.services.vdb_es_client import get_vdb_index_manager, VDBIndexManager
from vdb_app.vdb_config import vdb_settings

mappings = {
    "properties": {
        "Image": {"type": "text", "analyzer": "german"},
        "Combined_Text": {"type": "text", "analyzer": "german"},
        "Immobilie": {"type": "text", "analyzer": "german"},
        "Headline": {"type": "text", "analyzer": "german"},
        "Lage": {"type": "text", "analyzer": "german"},
        "id": {"type": "text"},
        "EMBEDDINGS_TEXT": {
            "type": "dense_vector",
            "dims": 512,
            "index": True,
            "similarity": "cosine"
        },
        "EMBEDDINGS_IMAGE": {
            "type": "dense_vector",
            "dims": 512,
            "index": True,
            "similarity": "cosine"
        }
    }
}

def app_lifespan(app: FastAPI):
    @Lifespan
    async def lifespan():
        # Perform startup tasks for default index if required
        index_manager: VDBIndexManager = get_vdb_index_manager()
        response = index_manager.create_index(index=vdb_settings.ELASTICSEARCH_INDEX, mappings=mappings)
        if not response.get('acknowledged'):
            raise RuntimeError("Failed to create default index")
        
        yield
        # Perform any shutdown tasks if necessary
    return lifespan

app = FastAPI(lifespan=app_lifespan)

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
