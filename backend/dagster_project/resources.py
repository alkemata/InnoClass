from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from dagster import ConfigurableResource, EnvVar
from elasticsearch import Elasticsearch, helpers

class SBERT(ConfigurableResource):
    model_name: str = "allenai-specter"

    def get_transformer(self):
        return SentenceTransformer(self.model_name)

class qdrant(ConfigurableResource):
    url: str = "http://qdrant:6334"

#   Qdrant client resource
    def get_client(self) -> QdrantClient:
        return QdrantClient(url=self.url, prefer_grpc=True)   

class es(ConfigurableResource):
    url:str="http://elasticsearch:9200"
    ELASTICSEARCH_USER:str  = EnvVar("ELASTICSEARCH_USER")
    ELASTICSEARCH_PASSWORD:str = EnvVar("ELASTICSEARCH_PASSWORD")

    def get_client(self):
        return Elasticsearch(
                self.url,
                    basic_auth=(self.ELASTICSEARCH_USER, self.ELASTICSEARCH_PASSWORD),
                    verify_certs=False, # Use with caution
                    request_timeout=60
            )