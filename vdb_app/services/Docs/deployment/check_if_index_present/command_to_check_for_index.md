The `0` folder inside `nodes` signifies the **node ID** in a single-node Elasticsearch setup. This directory should contain subdirectories and files representing the data Elasticsearch has indexed. Here’s what to look for:

1. **Inspect the `0` Folder**:
   - Navigate into the `0` folder to see if it contains further subdirectories. Typical paths are `indices`, which stores actual index data.
     ```bash
     sudo ls /var/lib/docker/volumes/database_service_es_data/_data/nodes/0
     ```
   - If data has been indexed, you should see directories such as `indices`, `translog`, or `snapshot_cache`.

2. **Verify Index Data in `indices` Folder**:
   - If you see an `indices` folder within `0`, it’s where Elasticsearch stores index-specific data. List the contents of the `indices` directory to see individual index directories:
     ```bash
     sudo ls /var/lib/docker/volumes/database_service_es_data/_data/nodes/0/indices
     ```
   - Each directory here corresponds to an index. If no `indices` folder or if it’s empty, Elasticsearch likely hasn’t stored any data yet.

3. **Confirm with Elasticsearch API**:
   - From within the container or your host machine (if accessible), confirm indexed data with:
     ```bash
     curl http://localhost:9200/_cat/indices?v
     ```
   - This command lists all indices and provides a quick overview of the database contents.

Seeing a populated `indices` directory or the index information in the API confirms that Elasticsearch is actively storing data in your Docker volume. If you’d like to proceed with test indexing or need further assistance with the setup, let me know!