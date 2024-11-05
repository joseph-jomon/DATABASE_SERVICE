In the `/var/lib/docker/volumes` directory, each named volume has a unique folder. Based on your description, the `database_service_es_data` folder is likely the one storing your Elasticsearch data.

To confirm and delete the data in this directory:

1. **Check the `database_service_es_data` Folder**:
   - Navigate to the path:
     ```bash
     cd /var/lib/docker/volumes/database_service_es_data/_data
     ```
   - Inside `_data`, you should see Elasticsearch data files, such as folders named `nodes` and possibly others related to Elasticsearch indices.

2. **Delete the Data in the Folder**:
   - To clear the Elasticsearch data, run:
     ```bash
     sudo rm -rf /var/lib/docker/volumes/database_service_es_data/_data/*
     ```
   - This action removes the existing data, allowing Elasticsearch to start with a clean slate.

3. **Restart the Elasticsearch Container**:
   - After deleting the data, restart the container to allow Elasticsearch to initialize without legacy data:
     ```bash
     docker-compose up
     ```

By deleting this folder’s contents, you resolve any legacy data conflicts, enabling Elasticsearch to start without needing any in-container modifications.