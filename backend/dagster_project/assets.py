import pandas as pd
import os
import json
from typing import List, Optional, Tuple
from dagster import (
    asset, multi_asset, AssetExecutionContext,
    Output, MetadataValue, MaterializeResult,
    AutomationCondition)
from dagster import asset_check, AssetCheckResult, AssetCheckSeverity, Config, ConfigurableResource, AssetSpec
import funcutils as fu
from codecarbon import EmissionsTracker

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from elasticsearch import Elasticsearch, helpers
# from resources import SBERT, qdrant, es # Removed direct import, will access via context
from qdrant_client.models import VectorParams, Distance
from collections import defaultdict 
import uuid
import checkfunc


class MyAssetConfig(Config):
    filename_texts: str = "/opt/project_data/raw_data.dat.gz"
    filename_prompts_targets: str = "/opt/project_data/sdg_targets.dat"
    filename_prompts_goals: str = "/opt/project_data/sdg_goals.dat"
    main_table: str = "main_table"
    ref_table:str="ref_table"
    feedback_table:str="fb_table"
    test_table:str="test_table"
    batch_size: int = 100
    search_results_file: str = "/opt/project_data/search_results.csv" # Added output file path
    threshold: float =0.7
    es_sample_size: int = 5 # New: Number of documents to sample for overview
    clear_vector: str="no"

@asset(description="Raw file provided byb epadb in TIP")
def raw_file_asset(config: MyAssetConfig):
    file_name = config.filename_texts
    # Load file
    try:
        metadata,data = fu.load_list(file_name)
    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise the exception to fail the asset
    metadata = {
        "num_rows": MetadataValue.int(len(data)),
        "file_name": MetadataValue.text(file_name),
        "Extraction method": MetadataValue.text(metadata["extract_method"]),
    }
    yield MaterializeResult(asset_key="raw_file_asset",metadata=metadata)
    return Output(value=data)


@asset
def goals_asset(config: MyAssetConfig):
    file_name = config.filename_prompts_goals
   
    try:
        df = fu.read_dataframe(file_name)
        
        metadata1 = {
                "num_rows": MetadataValue.int(len(df)),
                "file_name": MetadataValue.text(file_name)
            }
        yield Output(value=df, metadata=metadata1)
       
    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise to fail the multi-asset

@asset
def targets_asset(config: MyAssetConfig):
    file_name = config.filename_prompts_targets
   
    try:
        df = fu.read_dataframe(file_name)
        
        metadata1 = {
                "num_rows": MetadataValue.int(len(df)),
                "file_name": MetadataValue.text(file_name)
            }
        return Output(value=df, metadata=metadata1)
       
    except Exception as e:
        print(f"Error loading File: {e}")
        raise  # Re-raise to fail the multi-asset    


@asset_check(asset=raw_file_asset)
def text_column_not_empty(raw_file_asset: list[dict]) -> AssetCheckResult:
    # Convert list of dictionaries to DataFrame for easier processing,
    # especially for `isnull().any()` and `isnull().sum()`
    df = pd.DataFrame(raw_file_asset)

    if "original_text" not in df.columns:
        return AssetCheckResult(passed=False, metadata={"missing_column": "original_text"})

    if df["original_text"].isnull().any():
        return AssetCheckResult(passed=False, metadata={"empty_values": df["original_text"].isnull().sum()})

    return AssetCheckResult(passed=True)


@asset(deps=[raw_file_asset],automation_condition=AutomationCondition.eager())
def extracted_data_asset(raw_file_asset, config: MyAssetConfig) -> Output[List[dict]]:  # Changed return type hint
    try:
        tracker = EmissionsTracker()
        tracker.start()
        extracted = fu.process_texts(raw_file_asset, fu.keyword1, fu.keyword2)
        merged=fu.merge_sentence(extracted)
        result=fu.merge_by_id(merged,raw_file_asset)
    finally:
        _ = tracker.stop()
    stats = fu.analyze_text_data(merged)
    # Attach metadata: number of lines
    metadata = {
        "stats": MetadataValue.md(json.dumps(stats)),
    }

    return Output(value=result, metadata=metadata)  # Ensure you return the processed data


@asset(deps=["extracted_data_asset"],required_resource_keys={"es_resource","model","qdrant_resource"},automation_condition=AutomationCondition.eager())
def index_texts(context: AssetExecutionContext, config: MyAssetConfig, extracted_data_asset: List[dict]) -> None:  # Added extracted_data_asset
    """
    Stream a large text file line-by-line, embed each batch with SBERT,
    and upsert into a Qdrant collection.
    """
    INDEX2="test2"
    batch_size: int = config.batch_size
    sbert_model: SentenceTransformer = context.resources.model.get_transformer() # Get resources from context
    actual_embedding_dimension = sbert_model.get_sentence_embedding_dimension()
    context.log.info(f"Model reports embedding dimension: {actual_embedding_dimension}")

    qdrant_client: QdrantClient = context.resources.qdrant_resource.get_client()
    es_client: Elasticsearch = context.resources.es_resource.get_client()
    if not qdrant_client.collection_exists(INDEX2):
        qdrant_client.create_collection(
            collection_name=INDEX2,
            vectors_config=VectorParams(size=sbert_model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
        )

    texts = [item['text'] for item in extracted_data_asset]  # Extract texts
    ids = [item['id'] for item in extracted_data_asset]  # Extract ids
    for item in texts:
        print(item)
    embeddings = sbert_model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
    points = [
        models.PointStruct(id=str(uuid.uuid4()),vector=emb.tolist(), payload={"epo_id": str(docs_id)})
        for emb, docs_id in zip(embeddings, ids)
    ]
    qdrant_client.upsert(collection_name=INDEX2, points=points)
    context.log.info(f"Indexed {len(ids)} texts into Qdrant.")

@asset(deps=["index_texts"],required_resource_keys={"qdrant_resource"})
def clear_qdrant_collection_content(context: AssetExecutionContext, config: MyAssetConfig):
    """
    Asset to check the content of a specific Qdrant collection.
    """
    INDEX2="test2"
    clearok=config.clear_vector
    if clearok=="no":
        context.log.error("Clearing index for vector database not accepted")
        raise
    qdrant_client: QdrantClient = context.resources.qdrant_resource.get_client()
    qdrant_client.delete_collection(collection_name=INDEX2)

    

# Assuming MyAssetConfig is defined elsewhere, or create a separate one for health checks
# class QdrantHealthConfig(Config):
#     pass # No specific config needed for basic health check

@asset(required_resource_keys={"qdrant_resource"})
def check_qdrant_health(context: AssetExecutionContext):
    """
    Checks the health and status of the Qdrant database and reports results in Markdown metadata.
    """
    qdrant_client: QdrantClient = context.resources.qdrant_resource.get_client()

    markdown_content = []

    try:
        # 1. Basic Health Check

        # 2. Get Telemetry (provides more detailed information including memory and disk usage)
        telemetry_info = qdrant_client.get_telemetry()
        markdown_content.append("## Qdrant Telemetry Information\n")
        context.log.info("Qdrant Telemetry Information:")

        if telemetry_info and telemetry_info.collections:
            markdown_content.append("### Collections Information\n")
            for collection in telemetry_info.collections:
                markdown_content.append(f"#### Collection: `{collection.id}`\n")
                markdown_content.append(f"- Points Count: `{collection.points_count}`\n")
                markdown_content.append(f"- Vectors Count: `{collection.vectors_count}`\n")
                markdown_content.append(f"- Disk Size: `{collection.disk_size} bytes`\n")
                markdown_content.append(f"- RAM Size: `{collection.ram_size} bytes`\n")
                markdown_content.append("\n") # Add a newline for separation
                context.log.info(f"    Collection Name: {collection.id}")
                context.log.info(f"      Points Count: {collection.points_count}")
                context.log.info(f"      Vectors Count: {collection.vectors_count}")
                context.log.info(f"      Disk Size (bytes): {collection.disk_size}")
                context.log.info(f"      RAM Size (bytes): {collection.ram_size}")


        if telemetry_info and telemetry_info.app:
            markdown_content.append("### Application Information\n")
            markdown_content.append(f"- Qdrant Version: `{telemetry_info.app.version}`\n")
            markdown_content.append(f"- Qdrant Uptime: `{telemetry_info.app.uptime} seconds`\n")
            context.log.info("  Application Information:")
            context.log.info(f"    Qdrant Version: {telemetry_info.app.version}")
            context.log.info(f"    Qdrant Uptime (seconds): {telemetry_info.app.uptime}")

        # 3. System-level checks (if Qdrant is running on the same machine as Dagster)
        markdown_content.append("## System Resource Usage (Dagster host)\n")
        markdown_content.append(f"- CPU Usage: `{psutil.cpu_percent()}%`\n")
        markdown_content.append(f"- Memory Usage: `{psutil.virtual_memory().percent}%`\n")
        markdown_content.append(f"- Disk Usage (`/`): `{psutil.disk_usage('/').percent}%`\n")
        context.log.info("System Resource Usage (where Dagster is running):")
        context.log.info(f"  CPU Usage: {psutil.cpu_percent()}%")
        context.log.info(f"  Memory Usage: {psutil.virtual_memory().percent}%")
        context.log.info(f"  Disk Usage: {psutil.disk_usage('/').percent}%")


    except Exception as e:
        error_message = f"Error checking Qdrant health or telemetry: {e}"
        markdown_content.append(f"## Error\n\n```\n{error_message}\n```\n")
        context.log.error(error_message)
        raise # Re-raise to indicate asset failure

    # Set the Markdown metadata
    context.add_output_metadata(
        metadata={"Qdrant Health Report": MetadataValue.md("".join(markdown_content))}
    )



# 4. Asset: Run threshold search for queries and persist scores
# ------------------
@asset(deps=["es_patent_light","index_texts", "targets_asset", "goals_asset"],required_resource_keys={"es_resource","model","qdrant_resource"},automation_condition=AutomationCondition.eager())
def search_and_store(context: AssetExecutionContext, config: MyAssetConfig, goals_asset) -> None:
    """
    Encode a list of queries, run range searches in Qdrant,
    and save to ES
    """
    INDEX_NAME=config.main_table
    INDEX2="test2"
    queries = goals_asset
    threshold: float = config.threshold
    sbert_model: SentenceTransformer = context.resources.model.get_transformer() # Get resources from context
    qdrant_client: QdrantClient = context.resources.qdrant_resource.get_client()
    es_client: Elasticsearch = context.resources.es_resource.get_client()

    # Encode queries
    prompts_list = [item['Goal Title'] for item in queries]
    q_embs = sbert_model.encode(prompts_list, convert_to_numpy=True)
    document_sdg_mapping = defaultdict(set) # Using a set to store unique query_ids for each document
    document_details = {} # To store other relevant details like epo_id
    
    for q_idx, q_emb in enumerate(q_embs,start=1):
        hits = qdrant_client.search(
            collection_name=INDEX2,
            query_vector=q_emb.tolist(),
            score_threshold=config.threshold,
            limit=2000,
        )
        context.log.info(str(len(hits)))
        for hit in hits:
            # Add the query_index to the set for the corresponding hit_id
            document_sdg_mapping[hit.id].add("SDG"+str(q_idx)) # Store as string if SDG field is keyword
            
            # Store other details. Assuming epo_id is consistent for a given hit.id
            if hit.id not in document_details:
                document_details[hit.id] = {
                    "epo_id": hit.payload.get("epo_id"),
                    # You might want to store other relevant details here if they are in the payload
                }

# Prepare data for Elasticsearch bulk update
    actions = []
    for doc_id, query_indices_set in document_sdg_mapping.items():
        print(doc_id)
        # Convert the set of query_indices to a list
        sdg_list = list(query_indices_set)
         # Get the epo_id and any other details for this document
        details = document_details.get(doc_id, {})
        epo_id = details.get("epo_id")
        es_doc_id = epo_id # Make sure epo_id is always present and unique

        if es_doc_id: # Only proceed if you have a valid ID to update
            action = {
                "_op_type": "update",
                "_index": INDEX_NAME, 
                "_id": es_doc_id,
                "doc": {
                    "sdg": sdg_list,
                },
                "doc_as_upsert": True # Creates the document if it doesn't exist, otherwise updates
            }
            actions.append(action)

    # Now, use Elasticsearch's bulk API to update the documents
    # This is much more efficient than updating documents one by one.
    try:
        helpers.bulk(es_client, actions)
        context.log.info(f"Prepared {len(actions)} Elasticsearch bulk update actions.")
    except Exception as e:
        context.log.info(f"Error during Elasticsearch bulk update: {e}")

@asset(required_resource_keys={"es_resource"},description="Creation of the Main table of patents")
def es_maintable_created(context: AssetExecutionContext, config: MyAssetConfig) -> MaterializeResult:
    es_client: Elasticsearch = context.resources.es_resource.get_client()
    INDEX_NAME=config.main_table
    context.log.info(f"Deleting existing index: {INDEX_NAME}")
    es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])
    properties_definition = {
            "original_text": {
                "type": "text",
                "analyzer": "standard"
            }, 
            "pubnbr": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "standard"
            },
            "sdg": {"type": "keyword"},
            "target": {"type": "keyword"}
            }
    context.log.info(f"Creating index: {INDEX_NAME} with mapping...")
    try:
        es_client.indices.create(
            index=INDEX_NAME,
            body=   { "mappings": {  # <--- This is the key you need
        "properties": properties_definition
    }}
        )
        yield MaterializeResult(asset_key="es_maintable_created")
        
    except Exception as e:
        print(f"Error creating index: {e}")
        raise    

@asset(deps=["raw_file_asset","es_maintable_created"],required_resource_keys={"es_resource"},automation_condition=AutomationCondition.eager())
def es_patent_light(context: AssetExecutionContext,raw_file_asset, config: MyAssetConfig):

    es_client: Elasticsearch = context.resources.es_resource.get_client()
    INDEX_NAME=config.main_table
#   if es_client.indices.exists(index=INDEX_NAME):
#       context.log.info(f"Deleting existing index: {INDEX_NAME}")
#       es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])

    docs_to_index = []
    for text in raw_file_asset:
        doc = {
            "_index": INDEX_NAME,
            "_id": text["id"],
            "pubnbr": text["pubnbr"],
            "original_text": text["original_text"],
            "title": text["title"],
            "sdg":[""],
            "target":[""]
            }
        docs_to_index.append(doc)

    context.log.info(f"Bulk indexing {len(docs_to_index)} documents...")
    try:
        helpers.bulk(es_client, docs_to_index)
    except Exception as e:
        context.log.info(f"Error during bulk indexing: {e}")
        raise


@asset(deps=[es_patent_light],required_resource_keys={"es_resource"})
def es_health_check_and_overview(context: AssetExecutionContext, config: MyAssetConfig):
    """
    Checks the health and status of the Elasticsearch index and provides an overview
    of its content and metrics.
    """
    es_client: Elasticsearch = context.resources.es_resource.get_client()
    index_name = config.main_table

    context.log.info(f"Performing health check and overview for Elasticsearch index: {index_name}")

    # 1. Check if the index exists
    if not es_client.indices.exists(index=index_name):
        raise Exception(f"Elasticsearch index '{index_name}' does not exist after indexing.")
    context.log.info(f"Elasticsearch index '{index_name}' exists.")

    # 2. Get cluster health status
    try:
        cluster_health = es_client.cluster.health(index=index_name)
        status = cluster_health.get('status', 'unknown')
        active_shards = cluster_health.get('active_shards', 0)
        unassigned_shards = cluster_health.get('unassigned_shards', 0)

        health_md = f"""
        ### Elasticsearch Cluster Health for Index '{index_name}'
        - **Status:** `{status}`
        - **Active Shards:** `{active_shards}`
        - **Unassigned Shards:** `{unassigned_shards}`
        """
        if status not in ['green', 'yellow']:
            context.log.warning(f"Elasticsearch index '{index_name}' health is {status}. Investigate any issues.")
            # Depending on severity, you might want to raise an error here
            # raise Exception(f"Elasticsearch index health is {status}. Expected 'green' or 'yellow'.")
        context.log.info(f"Elasticsearch index '{index_name}' health: {status}")

    except Exception as e:
        context.log.error(f"Error getting cluster health for index '{index_name}': {e}")
        health_md = f"Error retrieving cluster health: {e}"
        status = "error" # Indicate an error in status

    # 3. Get index statistics (size on disk, document count)
    index_stats_md = ""
    try:
        stats = es_client.indices.stats(index=index_name)
        index_docs_count = stats['indices'][index_name]['total']['docs']['count']
        store_size_bytes = stats['indices'][index_name]['total']['store']['size_in_bytes']
        store_size_mb = f"{(store_size_bytes / (1024 * 1024)):.2f} MB" if store_size_bytes else "0 MB"
        results = checkfunc.count_non_empty_sdg_target(es_client, index_name)
        index_stats_md = f"""
        ### Elasticsearch Index Statistics for '{index_name}'
        - **Document Count:** `{index_docs_count}`
        - **Storage Size:** `{store_size_mb}`,
        - **SDG Classification Nbr** `{results['sdg_non_empty']}`,
        - **Target Classification Nbr** `{results['target_non_empty']}`,
        """
        context.log.info(f"Elasticsearch index '{index_name}' contains {index_docs_count} documents, size: {store_size_mb}")
    
    except Exception as e:
        context.log.error(f"Error getting index statistics for '{index_name}': {e}")
        index_stats_md = f"Error retrieving index statistics: {e}"


    # 4. Get a sample of documents to show content
    sample_docs_md = ""
    try:
        sample_size = config.es_sample_size
        search_body = {
            "size": sample_size,
            "query": {
                "match_all": {}
            }
        }
        sample_results = es_client.search(index=index_name, body=search_body)
        hits = sample_results['hits']['hits']

        if hits:
            sample_docs_md = f"### Sample Documents from '{index_name}' (First {len(hits)}):\n"
            for i, hit in enumerate(hits):
                source = hit['_source']
                sample_docs_md += f"#### Document {i+1} (ID: {hit['_id']})\n"
                sample_docs_md += "```json\n"
                sample_docs_md += json.dumps(source, indent=2, ensure_ascii=False)
                sample_docs_md += "\n```\n"
        else:
            sample_docs_md = f"### No documents found in index '{index_name}' to sample."

    except Exception as e:
        context.log.error(f"Error sampling documents from '{index_name}': {e}")
        sample_docs_md = f"Error retrieving sample documents: {e}"

    # Combine all markdown outputs
    full_md_output = f"""
    # Elasticsearch Index Overview: {index_name}

    {health_md}
    {index_stats_md}
    {sample_docs_md}
    """

    return Output(
        value=index_name, # Return the index name or a success indicator
        metadata={
            "es_index_name": MetadataValue.text(index_name),
            "es_health_status": MetadataValue.text(status),
            "es_overview": MetadataValue.md(full_md_output)
        }
    )
