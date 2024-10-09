# vdb_app/routers/validation_models.py

from pydantic import BaseModel
from typing import List, Dict, Any

class IngestDataItem(BaseModel):
    id: str  # The unique identifier for the item
    text_embedding: List[float]  # The vector embedding for text data
    image_embedding: List[float]  # The vector embedding for image data
    index_name: str  # The name of the Elasticsearch index for storage

class IngestDataBatch(BaseModel):
    items: List[IngestDataItem]  # A list of items to be ingested as a batch

class SearchRequest(BaseModel):
    search_vector: List[float]  # The vector embedding for the search query

class SearchResponse(BaseModel):
    hits: List[Dict[str, Any]]  # List of search hits from the Elasticsearch response
