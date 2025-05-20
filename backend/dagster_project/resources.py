from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from dagster import ConfigurableResource, EnvVar

class SBERT(ConfigurableResource):
    model: str = "all-MiniLM-L6-v2"

    def get_transformer():
        return SentenceTransformer(model)

class qdrant(ConfigurableResource):
    url: str = "http://qdrant:6333"

#   Qdrant client resource
    def qdrant_client_resource(_init_context) -> QdrantClient:
        return QdrantClient(url=url, prefer_grpc=True)   

class es(ConfigurableResource):
    url:str="http://elasticsearch:9200"
    ELASTICSEARCH_USER:str = EnvVar("ELASTICSEARCH_USER")
    ELASTICSEARCH_PASSWORD:str = EnvVar("ELASTICSEARCH_PASSWORD")

    def es_resource(_init_context):
        return Elasticsearch(
                url,
                    basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
                    verify_certs=False, # Use with caution
                    request_timeout=60
            )