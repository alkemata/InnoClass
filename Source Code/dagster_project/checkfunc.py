from elasticsearch import Elasticsearch
from typing import Dict, Any

def count_non_empty_sdg_target(es_client: Elasticsearch, index_name: str) -> Dict[str, int]:

    count_results = {"sdg_non_empty": 0, "target_non_empty": 0}

    try:
        # Construct the queries to count documents where "sdg" and "target" are not empty
        query_sdg = {
            "query": {
                "script": {
                    "script": "params.field != ''",
                    "params": {
                        "field": ""
                    }
                }
            }
        }

        query_target = {
            "query": {
                "script": {
                    "script": "params.field != ''",
                    "params": {
                        "field": ""
                    }
                }
            }
        }

        # Count documents where the 'sdg' field is not empty
        query_sdg["query"]["script"]["params"]["field"] = "sdg"
        sdg_count_response = es_client.count(index=index_name, body=query_sdg)
        count_results["sdg_non_empty"] = sdg_count_response.get("count", 0)

        # Count documents where the 'target' field is not empty
        query_target["query"]["script"]["params"]["field"] = "target"
        target_count_response = es_client.count(index=index_name, body=query_target)
        count_results["target_non_empty"] = target_count_response.get("count", 0)


    except Exception as e:
        print(f"Error counting non-empty fields: {e}")
        return {"sdg_non_empty": 0, "target_non_empty": 0}

    return count_results

if __name__ == '__main__':
    #  Replace with your actual Elasticsearch connection details and index name
    es_client = Elasticsearch(
        cloud_id="YOUR_CLOUD_ID",  #  Replace with your Cloud ID
        api_key=("YOUR_API_KEY_ID", "YOUR_API_KEY_SECRET"),  # Replace with your API Key
    )
    index_name = "your_index_name"  # Replace with your index name

    # Example usage:
    results = count_non_empty_sdg_target(es_client, index_name)
    print(f"Non-empty SDG count: {results['sdg_non_empty']}")
    print(f"Non-empty Target count: {results['target_non_empty']}")
