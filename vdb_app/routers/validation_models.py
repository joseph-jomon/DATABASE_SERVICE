# vdb_app/routers/validation_models.py

from pydantic import BaseModel
from typing import List, Dict, Any

class IngestDataItemImage(BaseModel):
    id: str  # The unique identifier for the item
    image_embedding: List[float]  # The vector embedding for image data
    index_name: str  # The name of the Elasticsearch index for storage

class IngestDataItemText(BaseModel):
    id: str  # The unique identifier for the item
    text_embedding: List[float]  # The vector embedding for text data
    index_name: str  # The name of the Elasticsearch index for storage

class IngestDataBatchImage(BaseModel):
    items: List[IngestDataItemImage]  # A list of items to be ingested as a batch

class IngestDataBatchText(BaseModel):
    items: List[IngestDataItemText]  # A list of items to be ingested as a batch

class SearchRequest(BaseModel):
    search_vector: List[float]  # The vector embedding for the search query

class SearchResponse(BaseModel):
    hits: List[Dict[str, Any]]  # List of search hits from the Elasticsearch response
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
class VectorDataItem(BaseModel):
    id: str
    company_name: str
    image_embedding: List[float]  # Adjust dimensions if required
    tracking_path: str # Added the new field

class VectorDataBatch(BaseModel):
    items: List[VectorDataItem]
