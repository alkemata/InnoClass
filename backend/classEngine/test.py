import json
import re
import string
from tqdm import tqdm  # Optional: for progress bars
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, helpers
import os
import pickle
import pandas

# --- Configuration ---
FILE1_PATH = './data/sg_test1.dat'
FILE2_PATH = '.data/toto.dat'
TEXT_KEY1 = 'prompt'  # The key in your JSON dictionaries holding the text
TEXT_KEY2 = 'extracted_text'
print("connecting to elasticsearch")
ELASTICSEARCH_HOSTS = "https://elasticsearch:9200"
ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
print("username: "+ELASTICSEARCH_USER)
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
print("password : "+ELASTICSEARCH_PASSWORD)
INDEX_NAME = "hybrid_search_index"
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2' # Or any other SBERT model

# --- Initialize Elasticsearch Client ---
try:
    es_client = Elasticsearch(
        ELASTICSEARCH_HOSTS,
            basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
            verify_certs=False, # Use with caution
        #request_timeout=60
    )
    # Test connection
    if not es_client.ping():
        raise ValueError("Connection to Elasticsearch failed!")
    print("Successfully connected to Elasticsearch.")
except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")
    exit()

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

def read_jsonl(filepath):
    """Reads a JSONL file and yields dictionaries line by line."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    yield json.loads(line.strip())
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line in {filepath}: {line.strip()}")
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        yield None # Indicate error

def read_dataframe(filepath):
    """
    Reads a pandas DataFrame from a pickle file and converts it to a list of dictionaries.

    Args:
        filepath (str): The path to the pickle file.

    Returns:
        list of dict: A list of dictionaries representing the DataFrame, or None if an error occurs.
    """
    try:
        with open(filepath, 'rb') as f:
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
            print(f"Warning: Missing or invalid text key '{TEXT_KEY}' in record: {record}")
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

def perform_hybrid_search(query_text, k=5, num_candidates=50):
    """Performs hybrid search using KNN and BM25 with RRF."""
    print(f"\n--- Searching for text similar to: '{query_text[:100]}...' ---")

    # 1. Clean and embed the query text
    cleaned_query = clean_text(query_text)
    query_embedding = model.encode(cleaned_query)

    # 2. Define KNN search part
    knn_query = {
        "field": "embedding",
        "query_vector": query_embedding.tolist(),
        "k": k,
        "num_candidates": num_candidates # Higher value increases accuracy but uses more resources
    }

    # 3. Define Keyword search part (BM25)
    keyword_query = {
        "match": {
            "cleaned_text": {
                "query": cleaned_query
                # Add options like "fuzziness": "AUTO" if needed
            }
        }
    }

    # 4. Combine using Reciprocal Rank Fusion (RRF) - Requires ES 8.x+
    # Adjust rank constants (rrf_window_size, rrf_rank_constant) as needed
    search_body = {
        "query": keyword_query, # Standard query part
        "knn": knn_query,       # KNN query part
        "rank": {
            "rrf": {
                "window_size": num_candidates + k, # Should be >= knn.k + query.size
                "rank_constant": 20 # Controls influence of lower-ranked results
            }
        },
        "size": k, # Number of final results to return
        "_source": ["original_data", "cleaned_text"] # Specify fields to retrieve
    }

    # --- Alternative: Simple Boolean Combination (Less sophisticated scoring) ---
    # Uncomment this block and comment out the RRF block above if using older ES or prefer bool logic
    # search_body = {
    #     "query": {
    #         "bool": {
    #             "should": [ # Combine scores from both clauses
    #                 {"match": {"cleaned_text": {"query": cleaned_query, "boost": 0.2}}}, # Keyword match (adjust boost)
    #             ]
    #         }
    #     },
    #     "knn": { # KNN query adds to the score based on vector similarity
    #          "field": "embedding",
    #          "query_vector": query_embedding.tolist(),
    #          "k": k,
    #          "num_candidates": num_candidates,
    #          "boost": 0.8 # Adjust boost relative to keyword match
    #     },
    #     "size": k,
    #     "_source": ["original_data", "cleaned_text"]
    # }
    # print("Using Boolean Combination for Hybrid Search.")

    # 5. Execute Search
    try:
        response = es_client.search(
            index=INDEX_NAME,
            body=search_body
        )
        return response['hits']['hits']
    except Exception as e:
        print(f"Error during search: {e}")
        # Try to provide more specific error info if possible
        if hasattr(e, 'info') and 'error' in e.info:
            print(f"Elasticsearch error details: {json.dumps(e.info['error'], indent=2)}")
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

        if not query_text_original or not isinstance(query_text_original, str):
             print(f"Warning: Skipping record due to missing/invalid text in {FILE1_PATH}: {record}")
             continue

        query_count += 1
        results = perform_hybrid_search(query_text_original, k=5, num_candidates=50) # Find top 5 results

        print(f"Found {len(results)} results:")
        search_results_all[query_text_original] = [] # Store results if needed
        for hit in results:
            print(f"  Score: {hit['_score']:.4f}")
            # Extract original text safely
            original_data = hit['_source'].get('original_data', {})
            hit_text = original_data.get(TEXT_KEY, "N/A")
            print(f"  Original Text: {hit_text[:200]}...") # Display snippet
            print(f"  Cleaned Text: {hit['_source'].get('cleaned_text', 'N/A')[:200]}...")
            print("-" * 10)
            search_results_all[query_text_original].append({
                'score': hit['_score'],
                'original_data': original_data
            })

    print(f"\n--- Search finished. Processed {query_count} queries from {FILE1_PATH}. ---")
    # You can now work with the `search_results_all` dictionary if needed
    # e.g., save it to a file
    # with open("search_results.json", "w", encoding="utf-8") as f_out:
    #     json.dump(search_results_all, f_out, indent=2, ensure_ascii=False)