Ah, I see the confusion now. In FastAPI, if a dependency function requires a parameter like `index_name` and it’s annotated as a query parameter in that function, FastAPI will still treat it as a required parameter for the route endpoint. This parameter will automatically show up in the documentation even if it’s only defined within the dependency function.

Here's how this works and why:

### Why `index_name` Appears in the Documentation Without Explicit Definition in the Route Function

When a dependency function has parameters (e.g., `index_name`), FastAPI inspects those parameters and includes them in the endpoint's requirements if they aren't satisfied by other means. FastAPI sees `index_name` as a query parameter for the route because:
  
1. **Dependency Resolution**: FastAPI processes dependency injection recursively. When it sees `index_name` in the `get_vdb_document_manager` function, it recognizes that this parameter must come from the query parameters unless otherwise specified.
   
2. **Automatic Parameter Inference**: FastAPI will add `index_name` to the route’s OpenAPI schema, effectively making it required for any route that relies on `get_vdb_document_manager`. This behavior ensures that dependencies have the necessary parameters, and it updates the documentation to reflect this, enhancing clarity for API consumers.

### Example of How FastAPI Infers `index_name`

Consider the following setup:

```python
from fastapi import Depends, Request

async def get_vdb_document_manager(request: Request, index_name: str) -> VDBDocumentManager:
    return VDBDocumentManager(client=request.app.state.es_client.client, index_doc=index_name)

@router.post("/ingest/")
async def ingest_data_batch(
    batch: IngestDataBatch,
    doc_manager: Annotated[VDBDocumentManager, Depends(get_vdb_document_manager)]
):
    # Your ingestion logic here
    pass
```

In this example:
- `index_name` appears in the documentation because `get_vdb_document_manager` expects it.
- Even though `index_name` is not directly in the route function, FastAPI’s dependency injection system lists it as a required parameter due to its presence in `get_vdb_document_manager`.

### When You Might Want to Define Parameters Directly

Defining `index_name` directly in the route function can sometimes improve readability, especially if you want it explicitly listed in the function signature for documentation or clarity. But if it’s redundant, keeping it in the dependency function is fine, as FastAPI will handle it automatically, as you observed.