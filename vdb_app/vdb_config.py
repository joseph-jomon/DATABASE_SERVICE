# vdb_app/vdb_config.py

class VDBSettings:
    ELASTICSEARCH_HOST: str = "elasticsearch" # see how_to_name_host.md
    ELASTICSEARCH_INDEX: str = "immo"  # Default index name
    TIMEOUT: int = 90

vdb_settings = VDBSettings()
