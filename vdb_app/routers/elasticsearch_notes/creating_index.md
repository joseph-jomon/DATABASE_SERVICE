Yes, this change might be related to recent updates or changes in how Elasticsearch handles mappings in the **index creation API**. Previously, Elasticsearch may have accepted `mappings` directly as the body without requiring it to be wrapped under the `"mappings"` key explicitly. However, with more recent versions of Elasticsearch (from version 7.x onwards), the expected format has become stricter, requiring that the `properties` field is always wrapped inside the `mappings` key.

### Why It Worked Before:
- In older versions of Elasticsearch, it was more lenient and may have allowed sending the `properties` directly in the `body` without explicitly including the `"mappings"` key.

### What Changed:
- In recent versions, Elasticsearch has tightened the requirements for the index creation API. It now **expects a properly structured `mappings` key** in the body for all index creation requests. This ensures clarity in distinguishing between index settings and field mappings.
- **Index mappings in Elasticsearch** now **require** a top-level `mappings` key for better structure, which separates settings and mappings clearly.

### Updated Code to Follow the New Format:
Here’s how you should structure your mappings now:

```python
# Define the mappings for the index
mappings = {
    "mappings": {   # Add this top-level mappings key
        "properties": {
            "Image": {"type": "text", "analyzer": "german"},
            "Combined_Text": {"type": "text", "analyzer": "german"},
            "Immobilie": {"type": "text", "analyzer": "german"},
            "Headline": {"type": "text", "analyzer": "german"},
            "Lage": {"type": "text", "analyzer": "german"},
            "id": {"type": "keyword"},  # Consider 'keyword' for IDs, not 'text'
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
}

response = es_client.indices.create(index="immo", body=mappings)  # Use 'body' not 'mappings'
```

### Key Changes:
1. **Top-level `mappings` key**: The `properties` block must be wrapped inside the `mappings` key.
2. **Correct `body` parameter**: The Elasticsearch client’s `indices.create` method expects the `mappings` as part of the `body` parameter, not directly as a `mappings` argument. Use `body=mappings`.

### Conclusion:
Elasticsearch's API has likely become stricter, and while your older code worked fine in the past, newer versions require a stricter format. You now need to include the top-level `mappings` key in your request to ensure compatibility with modern Elasticsearch versions.