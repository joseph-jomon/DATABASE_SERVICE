from pydantic import BaseModel, ValidationError, Field
import pdb


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
    index: str = Field(..., alias="_index")  # Using alias for _index
    id: str = Field(..., alias="_id")        # Using alias for _id
    score: float = Field(..., alias="_score")
    source: VDBDocument = Field(..., alias="_source")


# Define the model for the complete response structure
class SearchResponse(BaseModel):
    hits: list[ES_Hit]


#validation setp

'''validated_response = customdoc(**custom_doc_dict)
#pdb.set_trace()
print(customdoc(**custom_doc_dict))
validation_step= customdoc.model_validate(validated_response)
pdb.set_trace()
try:
    customdoc.model_validate(validated_response)
except ValidationError as exc:
    print(repr(exc.error()[0]['type']))'''