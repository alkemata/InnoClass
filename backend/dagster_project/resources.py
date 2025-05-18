from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

class SBERT(ConfigurableResource):
    model: str = "all-MiniLM-L6-v2"

    def get_transformer():
        return SentenceTransformer(model)

class qdrant(ConfigurableResource):
    url: str = "http://qdrant:6333"

#   Qdrant client resource
    def qdrant_client_resource(_init_context) -> QdrantClient:
        return QdrantClient(url=url, prefer_grpc=True)   