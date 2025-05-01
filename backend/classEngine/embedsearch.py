import json
import re
import string
from tqdm import tqdm  # Optional: for progress bars
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, helpers
import os
import pickle
import pandas as pd
import numpy as np
import gzip
import traceback
import time

def load_config(filepath):
    """Loads configuration from a JSON file."""
    try:
        with open(filepath, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Config file not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Invalid JSON in: {filepath}")
        return {}

config=load_config("./data/searchconfig.json")

# --- Configuration ---
FILE1_PATH = config["filename_sdg"]
FILE2_PATH = config["filename_texts"]
TEXT_KEY1 = config['Prompt']  # The key in your JSON dictionaries holding the text
TEXT_KEY2 = config['extracted_text']
print("connecting to elasticsearch")
ELASTICSEARCH_HOSTS = "http://elasticsearch:9200"
ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
SBERT_MODEL_NAME='AI-Growth-Lab/PatentSBERTa'
#SBERT_MODEL_NAME="multi-qa-mpnet-base-dot-v1"
INDEX_NAME = "hybrid_search_index"
#SBERT_MODEL_NAME = 'all-MiniLM-L6-v2' # Or any other SBERT model

time.sleep(10)
# --- Initialize Elasticsearch Clienlst ---
try:
    es_client = Elasticsearch(
        ELASTICSEARCH_HOSTS,
            basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
            verify_certs=False, # Use with caution
            request_timeout=60
    )
    # Test connection
    if es_client.ping():
        print("Successfully connected to Elasticsearch.")

except Exception as e:
    print(f"retry - Error connecting to Elasticsearch: {e}")
    #traceback.print_exc()
    exit()
    
try:
    info = es_client.info()
    version = info['version']['number']
    print(f"Elasticsearch version: {version}")
except Exception as e:
    print(f"Error retrieving version: {e}")

health = es_client.cluster.health()
print("Health:"+str(health))
# --- Load SBERT Model ---
try:
    print(f"Loading SBERT model: {SBERT_MODEL_NAME}...")
    model = SentenceTransformer(SBERT_MODEL_NAME)
    EMBEDDING_DIM = model.get_sentence_embedding_dimension()
    print(f"Model loaded successfully. Embedding dimension: {EMBEDDING_DIM}")
except Exception as e:
    print(f"Error loading SBERT model: {e}")
    exit()

# --- Helper Functions ---

def clean_text(text):
    """Basic text cleaning: lowercase, remove punctuation, extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Keep basic punctuation that might be relevant for meaning in some models
    # text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip() # Remove extra whitespace
    return text

def read_jsonl(filename):
    """
    Loads a gzipped JSON Lines (jsonl) file and returns a list of dictionaries.

    Parameters:
        filename (str): The filename of the gzipped jsonl file.

    Returns:
        list: A list of dictionaries read from the file.
    """
    result = []
    with gzip.open("./data/"+filename, 'rt', encoding='utf-8') as f:
        for line in f:
            result.append(json.loads(line))
    return result

def read_dataframe(filepath):
    """
    Reads a pandas DataFrame from a pickle file and converts it to a list of dictionaries.

    Args:
        filepath (str): The path to the pickle file.

    Returns:
        list of dict: A list of dictionaries representing the DataFrame, or None if an error occurs.
    """
    try:
        with open("./data/"+filepath, 'rb') as f:
            df = pickle.load(f)
        print("sdgs read")
        if isinstance(df, pd.DataFrame):
            return df.to_dict(orient='records')
        else:
            print(f"Error: Pickle file does not contain a pandas DataFrame.")
            return None

    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except pickle.UnpicklingError:
        print(f"Error: Could not unpickle the file at {filepath}. It might be corrupted or not a pickle file.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def generate_embeddings(texts, batch_size=32):
    """Generates embeddings for a list of texts using the loaded SBERT model."""
    return model.encode(texts, batch_size=batch_size, show_progress_bar=True)

# --- Elasticsearch Index Setup ---

def setup_elasticsearch_index():
    """Creates or recreates the Elasticsearch index with appropriate mapping."""
    if es_client.indices.exists(index=INDEX_NAME):
        print(f"Deleting existing index: {INDEX_NAME}")
        es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])

    index_mapping = {
        "properties": {
            "cleaned_text": { # For keyword search (BM25)
                "type": "text",
                "analyzer": "standard" # Use a suitable analyzer
            },
            "embedding": { # For vector search (kNN)
                "type": "dense_vector",
                "dims": EMBEDDING_DIM,
                "index": "true",  # Required for kNN search
                "similarity": "cosine" # Or "l2_norm" (Euclidean), "dot_product"
            },
            "original_data": { # Store the original dictionary
                 "type": "object",
                 "enabled": False # Optional: disable indexing if you only want to retrieve it
            }
            # Add other fields from your JSON if you want to index/search them
        }
    }

    print(f"Creating index: {INDEX_NAME} with mapping...")
    try:
        es_client.indices.create(
            index=INDEX_NAME,
            mappings=index_mapping,
            # Settings for approx-knn might be needed depending on ES version/needs
            # settings={ "index.knn": True, "index.knn.space_type": "cosinesimil"}
        )
        print("Index created successfully.")
    except Exception as e:
        print(f"Error creating index: {e}")
        exit()

# --- Indexing Data (File 2) ---

def index_data_from_file2():
    """Reads file2, cleans text, generates embeddings, and indexes into Elasticsearch."""
    print(f"\n--- Indexing data from {FILE2_PATH} ---")
    docs_to_index = []
    batch_texts = []
    batch_original_data = []
    batch_size = 100 # Process N records at a time for embedding

    for record in read_jsonl(FILE2_PATH):
        if record is None: continue # Skip if error reading line
        original_text = record.get(TEXT_KEY2)
        if not original_text or not isinstance(original_text, str):
            print(f"Warning: Missing or invalid text key '{TEXT_KEY2}' in record: {record}")
            continue

        cleaned = clean_text(original_text)
        batch_texts.append(cleaned)
        batch_original_data.append(record) # Store the whole original dict

        if len(batch_texts) >= batch_size:
            print(f"Generating embeddings for batch of {len(batch_texts)}...")
            embeddings = generate_embeddings(batch_texts)
            for i, text in enumerate(batch_texts):
                doc = {
                    "_index": INDEX_NAME,
                    "_source": {
                        "cleaned_text": text,
                        "embedding": embeddings[i].tolist(), # Convert numpy array to list
                        "original_data": batch_original_data[i]
                    }
                }
                docs_to_index.append(doc)
            # Clear batches
            batch_texts = []
            batch_original_data = []

            # Bulk index periodically to avoid memory issues
            if len(docs_to_index) >= 500: # Index every 500 docs
                 print(f"Bulk indexing {len(docs_to_index)} documents...")
                 try:
                     helpers.bulk(es_client, docs_to_index)
                     print("Bulk indexing successful.")
                 except Exception as e:
                     print(f"Error during bulk indexing: {e}")
                 docs_to_index = [] # Clear indexed docs list

    # Process any remaining records in the last batch
    if batch_texts:
        print(f"Generating embeddings for final batch of {len(batch_texts)}...")
        embeddings = generate_embeddings(batch_texts)
        for i, text in enumerate(batch_texts):
            doc = {
                "_index": INDEX_NAME,
                "_source": {
                    "cleaned_text": text,
                    "embedding": embeddings[i].tolist(),
                    "original_data": batch_original_data[i]
                }
            }
            docs_to_index.append(doc)

    # Final bulk index
    if docs_to_index:
        print(f"Bulk indexing remaining {len(docs_to_index)} documents...")
        try:
            helpers.bulk(es_client, docs_to_index)
            print("Final bulk indexing successful.")
        except Exception as e:
            print(f"Error during final bulk indexing: {e}")

    # Refresh index to make changes searchable
    print("Refreshing index...")
    es_client.indices.refresh(index=INDEX_NAME)
    print("Indexing complete.")


# --- Hybrid Search (File 1) ---

def perform_hybrid_search(query_text, k=5, num_candidates=100):
    """
    Performs a hybrid search combining kNN (vector) and BM25 (standard) using
    Reciprocal Rank Fusion (RRF) in Elasticsearch 8.9+.
    """

    # 1. Clean and embed the query text
    cleaned_query = clean_text(query_text)
    query_embedding = model.encode(cleaned_query)
    if np.isnan(query_embedding).any():
        print("Warning: NaN values detected in embeddings.")
    else:
        print("Embeddings generated successfully.")

    knn_retriever = {
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": num_candidates,
            "num_candidates": num_candidates
        }
    }
    bm25_retriever = {
        "standard": {
            "query": {
                "match": {
                    "cleaned_text": {
                        "query": cleaned_query
                    }
                }
            }
        }
    }

    # 5. Execute the search
    try:
        response = es_client.search(
            index=INDEX_NAME,
            retriever={
                "rrf": {
                    "retrievers": [knn_retriever, bm25_retriever],
                    "rank_window_size": num_candidates,
                    "rank_constant": 20
                }
            },
            size=k,
            _source=["original_data", "cleaned_text"]
        )
    except Exception as e:
        print(f"Error during search: {e}")
        if hasattr(e, "info") and "error" in e.info:
            print(json.dumps(e.info["error"], indent=2))
        return []

# --- Main Execution ---
if __name__ == "__main__":
    # 1. Setup Index
    setup_elasticsearch_index()

    # 2. Index data from file2
    index_data_from_file2()

    # 3. Read file1 and search for each item
    print(f"\n--- Starting search process using {FILE1_PATH} as queries ---")
    search_results_all = {}
    query_count = 0
    for record in read_dataframe(FILE1_PATH):
        if record is None: continue
        query_text_original = record.get(TEXT_KEY1)
        id_prompt=record.get("Target ID")

        if not query_text_original or not isinstance(query_text_original, str):
             print(f"Warning: Skipping record due to missing/invalid text in {FILE1_PATH}: {record}")
             continue

        query_count += 1
        results = perform_hybrid_search(query_text_original, k=10, num_candidates=50) # Find top 5 results

        print(f"Found {len(results)} results:")
        search_results_all[id_prompt] = [] # Store results if needed
        for hit in results:
            #print(f"  Score: {hit['_score']:.4f}")
            # Extract original text safely
            original_data = hit['_source'].get('original_data', {})
            hit_text = original_data.get(TEXT_KEY2, "N/A")
            #print(f"  Original Text: {hit_text[:200]}...") # Display snippet
            #print(f"  Cleaned Text: {hit['_source'].get('cleaned_text', 'N/A')[:200]}...")
            #print("-" * 10)
            search_results_all[id_prompt].append({
                'score': hit['_score'],
                'original_data': original_data
            })

    print(f"\n--- Search finished. Processed {query_count} queries from {FILE1_PATH}. ---")
    # You can now work with the `search_results_all` dictionary if needed
    # e.g., save it to a file
    with open("./data/search_results.json", "w", encoding="utf-8") as f_out:
         json.dump(search_results_all, f_out, indent=2, ensure_ascii=False)