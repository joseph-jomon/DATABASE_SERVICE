# vdb_app/vdb_config.py

class VDBSettings:
    ELASTICSEARCH_HOST: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "immo"  # Default index name
    TIMEOUT: int = 90

vdb_settings = VDBSettings()
