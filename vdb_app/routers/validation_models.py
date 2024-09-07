from pydantic import BaseModel
from typing import List

class VDBDocument(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: list[float]
    EMBEDDINGS_IMAGE: list[float]

class VDBSearchDocument(BaseModel):
    search_vector: list[float]

# Define the model for the _source part of the response
class ES_Response_Body(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: List[float]
    EMBEDDINGS_IMAGE: List[float]

# Define the model for each hit
class Hit(BaseModel):
    _index: str
    _id: str
    _score: float
    _source: ES_Response_Body

# Define the model for the complete response structure
class SearchResponse(BaseModel):
    hits: List[Hit]
