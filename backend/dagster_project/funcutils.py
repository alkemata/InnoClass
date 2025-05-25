import pandas as pd
import os
import gzip
import re
import xml.etree.ElementTree as ET
import spacy
import json
import pickle
from typing import List, Optional
from bs4 import BeautifulSoup  # Missing import
import numpy as np          # Missing import
from dagster import MetadataValue
import seaborn
import matplotlib.pyplot as plt
import base64
from io import BytesIO

nlp = spacy.blank('en')
nlp.add_pipe('sentencizer')

def load_list(filename):
    """
    Loads a gzipped JSON Lines (jsonl) file, separating the first line as metadata
    and the rest as a list of dictionaries.

    Parameters:
        filename (str): The filename of the gzipped jsonl file.

    Returns:
        tuple: A tuple containing:
            - dict: The metadata dictionary from the first line.
            - list: A list of dictionaries (data records) read from the file.
    """
    metadata = {}
    data_records = []
    
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        # Read the first line as metadata
        first_line = f.readline()
        if first_line:
            try:
                metadata = json.loads(first_line)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not decode first line as metadata: {e}")
                pass     
        # Read the rest of the lines as data records
        for line in f:
            try:
                data_records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Could not decode line as JSON, skipping: {line.strip()} - {e}")
                continue # Skip malformed lines

    return metadata, data_records

# Keywords to search for in headings (allowing fuzzy matching with up to one error)
keyword1 = ["scope of the invention","Description of the Related Art", "TECHNICAL SCOPE","Description of Related Art","REVEALING THE INVENTION","background of the invention", "background of the disclosure", "field of the invention", "field of invention", "technical field","summary","industrial applicability","Field of art","background","introduction","background art"]
keyword2=["background","The present invention regards","herein described subject matter", "It is well known" "technology described herein", "field of the disclosure", "field of the invention", "subject of the invention", "belongs to the field", "invention is","invention relates to", "present invention refers to","aspect of the invention","technical field"]

def clean_sentences(s):
    if s.endswith('.'):
        # Remove all content in parentheses or brackets, including the symbols
        s = re.sub(r'\([^)]*\)', '', s)  # remove ( ... )
        s = re.sub(r'\[[^\]]*\]', '', s)  # remove [ ... ]

        # Remove HTML tags
        s = re.sub(r'<[^>]+>', '', s)

        # Collapse multiple spaces and strip again
        s = re.sub(r'\s+', ' ', s).strip()
    return s


def remove_keywords(text,keywords):
    pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
    return re.sub(pattern, '', text,flags=re.IGNORECASE)

import re
from bs4 import BeautifulSoup, Tag
from typing import List
import spacy

# Load the English spaCy model (make sure you have it installed: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spacy model 'en_core_web_sm'...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def remove_keywords(text: str, keywords: List[str]) -> str:
    """
    Removes specified keywords from text using whole word, case-insensitive matching.
    """
    if not isinstance(text, str): return ""
    if not keywords or not any(keywords): # Handle empty or all-empty keywords list
        return text
    
    # Filter out non-string or empty keywords and escape them
    valid_keywords = [re.escape(str(kw)) for kw in keywords if kw and isinstance(kw, str)]
    if not valid_keywords:
        return text
        
    pattern = r'\b(?:' + '|'.join(valid_keywords) + r')\b'
    return re.sub(pattern, '', text, flags=re.IGNORECASE)

def extract_text_simple(
    html_text: str,
    keyword_headings: List[str],
    keyword_paragraphs: List[str],
    keyword_fallback: List[str],
    max_words: int = 600
) -> str:
    """
    Extracts up to max_words words of text from HTML:
    1) Finds <heading> or <h1>-<h6> tags whose text contains any keyword_headings;
        collects text of all following sibling elements until the next heading.
    2) If no such headings, finds <p> tags containing any keyword_paragraphs,
        and takes that paragraph + the next one.
    3) If still nothing, extracts the first sentences of the text until near 500 words
       or max_words (whichever is met first).

    Removes the matched heading keywords, normalizes whitespace, then segments
    into sentences and accumulates full sentences up to max_words.
    Returns the concatenated string.
    """
    soup = BeautifulSoup(html_text, 'html.parser')

    # Lowercased keyword lists for matching
    kws_h = [kw.lower() for kw in keyword_headings]
    kws_p = [kw.lower() for kw in keyword_paragraphs]
    kws_f = [kw.lower() for kw in keyword_fallback]
    collecting_mode = False

    def clean_text(elem):
        return elem.get_text(separator=' ', strip=True)

    # 1) Heading-based extraction
    collected = []
    # consider both <heading> and standard heading tags
    headings = soup.find_all(lambda tag: tag.name == 'heading' or re.fullmatch(r'h[1-6]', tag.name))
    mode="headings"
    for h in headings:
        txt = h.get_text().lower()
        if any(kw in txt for kw in kws_h):
            for sib in h.find_next_siblings():
                collected.append(clean_text(sib))
            break # Stop after finding the first matching heading

    # 2) Paragraph-based fallback
    if not collected:
        mode="paragraphs"
        paragraphs = soup.find_all('p')
        for idx, p in enumerate(paragraphs):
            txt = clean_text(p).lower()
        
            if collecting_mode:
                # If we are already in collecting mode, just append the paragraph
                collected.append(clean_text(p))
            elif any(kw in txt for kw in kws_p):
                # If a keyword is found and we are not yet in collecting mode
                collecting_mode = True  # Set the flag to True
                collected.append(clean_text(p)) # Collect the current paragraph
                # All subsequent paragraphs will now be collected in the next iterations

    # 3) Final Fallback: First sentences of the text (now using word count)
    if not collected or (len(' '.join(collected).split())<100):
        mode="fallback"
        # Get all text from the body, then segment into sentences
        full_text = soup.body.get_text(separator=' ', strip=True) if soup.body else html_text
        doc = nlp(full_text)
        current_word_count_initial = 0
        target_word_count_initial = 500 # Aim for around 500 words for the initial fallback
        for sent in doc.sents:
            cleaned_sent = sent.text.strip()
            # Calculate word count for the current sentence
            sent_word_count = len([token for token in nlp(cleaned_sent) if not token.is_space and not token.is_punct]) # Exclude punctuation
            
            # Ensure sentences have more than 15 characters (this constraint remains)
            if len(cleaned_sent) > 15:
                # Check if adding this sentence exceeds the target word count
                if current_word_count_initial + sent_word_count > target_word_count_initial and current_word_count_initial > 0:
                    # Allow some overshoot but try not to go wildly over
                    if current_word_count_initial + sent_word_count <= target_word_count_initial + 100: # Allow up to 100 words overshoot
                        collected.append(cleaned_sent)
                        current_word_count_initial += sent_word_count
                    else:
                        break
                                    
                collected.append(cleaned_sent)
                current_word_count_initial += sent_word_count
            

    # Combine collected text and remove heading keywords (only if collected via heading)
    combined_text = ' '.join(collected)
    # Check if any heading keyword exists in the lowercased combined text to decide if removal is needed
    if mode=="headings":
        if collected and any(kw in combined_text.lower() for kw in kws_h): 
               for kw in kws_h:
                    combined_text = re.sub(re.escape(kw), '', combined_text, flags=re.IGNORECASE)

   # --- Block-level cleaning ---
    # These are applied unconditionally to the combined_text block,
    # as the user's clean_sentences might not trigger if combined_text doesn't end with '.'
    combined_text = re.sub(r'\([^)]*\)', '', combined_text)  # remove (...)
    combined_text = re.sub(r'\[[^\]]*\]', '', combined_text)  # remove [...]
    combined_text = re.sub(r'<[^>]+>', '', combined_text)    # remove <...> HTML tags (extra safeguard)

    # Specific numeric/reference patterns (if these are distinct from general parenthesis removal)
    combined_text = re.sub(r'\(\s*\d+\s*\)', '', combined_text) # e.g. (1), ( 2 )
    combined_text = re.sub(r'\[\s*\d+\s*\]', '', combined_text) # e.g. [1], [ 2 ]
    # Removes e.g. [References], [Table A], but not brackets with only digits or only spaces
    combined_text = re.sub(r'\[\s*[^\]\d\s][^\]]*?\]', '', combined_text) 
    combined_text = re.sub(r'\s+', ' ', combined_text).strip() # Normalize whitespace

    total_words_output = 0
    target_word_count_final = 500 # Aim for around 500 words for the final output

    words = combined_text.split()  # Split the text into a list of words
    if len(words) > target_word_count_final:
        truncated_words = words[:target_word_count_final]
        return " ".join(truncated_words)
    else:
        return combined_text


def process_texts(texts, keyword1, keyword2, min_sentence_length=5): # min_sentence_length is now mostly handled in extract_text_simple
    results = []
    nb1=0
    for item in texts:
        print(nb1)
        nb1=nb1+1
        # Note: extract_text_simple now returns a list of strings (sentences)
        result = extract_text_simple(item["original_text"][1:10000], keyword1, keyword2, keyword2)
        item["cleaned_text"]=result
        results.append(item)
    return results

def analyze_text_data(data):
    """    
    Analyzes a list of dictionaries containing text data.
    
    Parameters:
            data (list): A list where each element is a dictionary with an 'id', a 
                        'sentence' and 'status'.
                        
    Returns:
            stats (dict): A dictionary containing the mean, square-mean, min, and max word counts.
            plot_widget (ipywidgets.Output): An ipywidget containing a histogram of the word counts.
    """
    word_counts = []
    nbr=0
    for entry in data:
        # Adjust the keys if your structure is different.
        nbr+=1
        sentence = entry['cleaned_text']
        count = len(sentence.split())
        word_counts.append(count)
    word_counts = np.array(word_counts)
    
    # Compute statistics
    stats = {
        'Nbr of entries': nbr,
        'mean': word_counts.mean().item(),
        'square_mean': np.mean(word_counts**2).item(),
        'min': word_counts.min().item(),
        'max': word_counts.max().item()
    }
    return stats

# function used tor ead goals and targets files
def read_dataframe(filepath):
 
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

def make_plot(data,x_title):
    plt.clf()
    distrib_plot = seaborn.distplot(data, binwidth=20, x=x_title, y="count")
    fig = distrib_plot.get_figure()
    buffer = BytesIO()
    fig.savefig(buffer)
    image_data = base64.b64encode(buffer.getvalue())

    return MetadataValue.md(f"![img](data:image/png;base64,{image_data.decode()})")