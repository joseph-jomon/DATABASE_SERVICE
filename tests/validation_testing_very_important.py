from pydantic import BaseModel, ValidationError
import pdb
# Do not use names starting with an underscore

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
'''class ES_Response_Body(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: List[float]
    EMBEDDINGS_IMAGE: List[float]'''


# Define the model for each hit
class ES_Hit(BaseModel):
    _index: str # try with just index , do not use names starting with an underscore it will create uncaught error be very careful
    _id: str # This is wrong starts with _
    _score: float # This is wrong starts with _
    _source: VDBDocument # this is wrong starts with -
'''
class ES_Hit(BaseModel):
    index: str = Field(..., alias="_index")  # Using alias for _index
    id: str = Field(..., alias="_id")        # Using alias for _id
    score: float = Field(..., alias="_score")
    source: VDBDocument = Field(..., alias="_source")
'''


# Define the model for the complete response structure
class SearchResponse(BaseModel):
    hits: list[ES_Hit]

full_doc_dict = {
        "_index": "my_index",
        "_id": "123",
        "_score": 1.23,
        "_source": {
            "Image": "image_url",
            "Combined_Text": "This is combined text.",
            "Immobilie": "Property info",
            "Headline": "Headline text",
            "Lage": "Location info",
            "id": "doc_id_123",
            "EMBEDDINGS_TEXT": [0.1, 0.2, 0.3],
            "EMBEDDINGS_IMAGE": [0.4, 0.5, 0.6]
        }
}
class customdoc(BaseModel):
    index: str
    thedoc: VDBDocument


the_doc = {
            "Image": "image_url",
            "Combined_Text": "This is combined text.",
            "Immobilie": "Property info",
            "Headline": "Headline text",
            "Lage": "Location info",
            "id": "doc_id_123",
            "EMBEDDINGS_TEXT": [0.1, 0.2, 0.3],
            "EMBEDDINGS_IMAGE": [0.4, 0.5, 0.6]
        }
custom_doc_dict = {
    "_index": "my_index",
    "thedoc": the_doc
}
#validation setp

validated_response = customdoc(**custom_doc_dict)
#pdb.set_trace()
print(customdoc(**custom_doc_dict))
validation_step= customdoc.model_validate(validated_response)
pdb.set_trace()
try:
    customdoc.model_validate(validated_response)
except ValidationError as exc:
    print(repr(exc.error()[0]['type']))