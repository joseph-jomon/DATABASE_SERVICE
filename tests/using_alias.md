Yes, Pydantic by default doesn't support fields that start with an underscore (`_`). This is because Python uses a single leading underscore to indicate a "weak private" variable and may cause conflicts with internal Pydantic mechanisms.

### Solution to Handle Fields with Underscore:

If you need to handle JSON or dictionary keys that start with an underscore (e.g., `_index`, `_id`), you can use the `alias` feature in Pydantic. This allows you to map the field in the JSON/dictionary to a valid Python attribute name.

Here's how you can modify your model to handle fields like `_index` and `_source` correctly:

### Example:

```python
from pydantic import BaseModel, Field
from typing import List

class VDBDocument(BaseModel):
    Image: str
    Combined_Text: str
    Immobilie: str
    Headline: str
    Lage: str
    id: str
    EMBEDDINGS_TEXT: List[float]
    EMBEDDINGS_IMAGE: List[float]

class Hit(BaseModel):
    index: str = Field(..., alias="_index")  # Using alias for _index
    id: str = Field(..., alias="_id")        # Using alias for _id
    score: float = Field(..., alias="_score")
    source: VDBDocument = Field(..., alias="_source")

class SearchResponse(BaseModel):
    hits: List[Hit]

# Now you can parse the data with the original dictionary keys intact
```

### What’s Happening:

- The `alias` parameter in `Field` allows you to define how the JSON or dictionary keys are mapped to the model attributes.
- For instance, the `index` field will expect the `_index` key in the incoming dictionary, but in Python, you will access it as `hit.index`.

### Usage:

When you use this model with your original data, it will now correctly handle the fields that start with an underscore.

### Example with Data:

```python
hits_list = [
    {
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
]

# Parsing the data
validated_response = SearchResponse(hits=hits_list)
print(validated_response)
```

### Accessing the Fields:

You can access the fields without the underscore in your Python code:

```python
print(validated_response.hits[0].index)  # Will print "my_index"
print(validated_response.hits[0].id)     # Will print "123"
```

This way, you don't have to modify your incoming JSON/dict keys but can work with them in a Pythonic manner within your code.