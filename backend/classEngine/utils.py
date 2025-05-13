# --- Helper Functions ---

# cleaninf for sdgbert
def clean_text(text):
    """Basic text cleaning: lowercase, remove punctuation, extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Keep basic punctuation that might be relevant for meaning in some models
    # text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip() # Remove extra whitespace
    return text


# function to read compressed jsonl (the file with text data .dat.gz)
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

# function used tor ead goals and targets files
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