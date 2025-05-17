import pandas as pd
import os
import gzip
import re
import xml.etree.ElementTree as ET
import spacy
import json
from typing import List, Optional
from bs4 import BeautifulSoup  # Missing import
import numpy as np          # Missing import

nlp = spacy.blank('en')
nlp.add_pipe('sentencizer')

def load_list(filename):
    """
    Loads a gzipped JSON Lines (jsonl) file and returns a list of dictionaries.

    Parameters:
        filename (str): The filename of the gzipped jsonl file.

    Returns:
        list: A list of dictionaries read from the file.
    """
    result = []
    with gzip.open(filename, 'rt', encoding='utf-8') as f:
        for line in f:
            result.append(json.loads(line))
    return pd.DataFrame(result)

# Keywords to search for in headings (allowing fuzzy matching with up to one error)
keyword1 = ["scope of the invention","Description of the Related Art", "TECHNICAL SCOPE","Description of Related Art","REVEALING THE INVENTION","background of the invention", "background of the disclosure", "field of the invention", "technical field","summary","industrial applicability","field of the disclosure","background",  "prior art", "state of the art"]
keyword2=["background","The present invention regards","herein described subject matter", "It is well known" "technology described herein", "field of the disclosure", "field of the invention", "subject of the invention", "belongs to the field", "invention is","invention relates to", "present invention refers to"]

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
    3) If still nothing, searches for keyword_fallback in <p> tags and takes
       paragraphs until max_words.
    Removes the matched heading keywords, normalizes whitespace, then segments
    into sentences and accumulates full sentences up to max_words.
    Returns the concatenated string.
    """
    soup = BeautifulSoup(html_text, 'html.parser')

    # Lowercased keyword lists for matching
    kws_h = [kw.lower() for kw in keyword_headings]
    kws_p = [kw.lower() for kw in keyword_paragraphs]
    kws_f = [kw.lower() for kw in keyword_fallback]

    def clean_text(elem):
        return elem.get_text(separator=' ', strip=True)

    # 1) Heading-based extraction
    collected = []
    # consider both <heading> and standard heading tags
    headings = soup.find_all(lambda tag: tag.name == 'heading' or re.fullmatch(r'h[1-6]', tag.name))
    for h in headings:
        txt = h.get_text().lower()
        if any(kw in txt for kw in kws_h):
            block_texts = []
            for sib in h.find_next_siblings():
                # stop at next heading
                if sib.name == 'heading' or re.fullmatch(r'h[1-6]', sib.name):
                    break
                block_texts.append(clean_text(sib))
            if block_texts:
                collected.append(' '.join(block_texts))

    # 2) Paragraph-based fallback
    if not collected:
        paragraphs = soup.find_all('p')
        for idx, p in enumerate(paragraphs):
            txt = clean_text(p).lower()
            if any(kw in txt for kw in kws_p):
                collected.append(clean_text(p))
                if idx + 1 < len(paragraphs):
                    collected.append(clean_text(paragraphs[idx+1]))
        # 3) Fallback keywords
        if not collected:
            for idx, p in enumerate(paragraphs):
                txt = clean_text(p).lower()
                if any(kw in txt for kw in kws_f):
                    j = idx
                    while j < len(paragraphs) and sum(len(c.split()) for c in collected) < max_words:
                        collected.append(clean_text(paragraphs[j]))
                        j += 1
                    break

    # Combine and remove heading keywords
    combined = ' '.join(collected)
    for kw in kws_h:
        combined = re.sub(re.escape(kw), '', combined, flags=re.IGNORECASE)
        
        combined = re.sub(r'\(.*?\)', '', combined)  # remove all parenthesis content
        # Remove numeric references like (1), [0004]
        combined = re.sub(r'\(\d+\)', '', combined)
        combined = re.sub(r'\[\d+\]', '', combined)
        combined = re.sub(r'\[\s*[^\d\]]+\]', '', combined)
    combined = re.sub(r'\s+', ' ', combined).strip()

    # Sentence segmentation and word limit
    doc = nlp(combined)
    output_sents = []
    total_words = 0
    for sent in doc.sents:
        wc = len([t for t in sent if not t.is_space])
        if total_words + wc > max_words:
            break
        output_sents.append(sent.text.strip())
        total_words += wc

    return output_sents



def process_texts(texts, keyword1, keyword2, min_sentence_length=5):
    """
    Processes a list of texts, each with an associated id.
    
    Args:
        texts (list of tuples): Each tuple is (text_id, text).
        keyword1 (list): Keywords for heading-based extraction.
        keyword2 (list): Fallback keywords for paragraph-based extraction.
        min_sentence_length (int): Minimum number of words a sentence must have.
        
    Returns:
        list of tuples: Each tuple is (text_id, sentence) for each extracted sentence.
    """
    results = []
    for item in texts:
        sentences = extract_text_simple(item["original_text"], keyword1,keyword1, keyword2)
        if len(sentences)==0:
            sentences=[""]
        for sentence in sentences:
            results.append({"id":item["id"], "sentence":sentence})

    return results


def merge_sentence(processed_texts):
    """
    Merges sentences by text_id from the processed texts.
    
    Args:
        processed_texts (list of tuples): Each tuple is (text_id, sentence).
        
    Returns:
        list of dict: Each dictionary has the text_id as key and the merged sentences as value.
    """
    merged = {}
    for item in processed_texts:
        text_id=item["id"]
        sentence=item["sentence"]
        if text_id not in merged:
            merged[text_id] = sentence
        else:
            merged[text_id] += "\n" + sentence
    # Convert to list of dictionaries as required.
    return [{"id":text_id,"text":sentences, "status":""} for text_id, sentences in merged.items()]

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
        sentence = entry['sentence']
        count = len(sentence.split())
        word_counts.append(count)
    word_counts = np.array(word_counts)
    
    # Compute statistics
    stats = {
        'Nbr of entries': nbr,
        'mean': word_counts.mean(),
        'square_mean': np.mean(word_counts**2),
        'min': word_counts.min(),
        'max': word_counts.max()
    }
    return stats

def compute_sentence_stats(df):
    """
    Computes statistics on the number of sentences per text_id.

    Parameters:
        df (pandas.DataFrame): DataFrame with columns 'text_id' and 'sentence'
    
    Returns:
        stats (dict): Dictionary containing the following keys:
                      - 'mean': average number of sentences per text_id
                      - 'min': minimum number of sentences in any text_id
                      - 'max': maximum number of sentences in any text_id
                      - 'square_mean': mean of the squared sentence counts per text_id
    """
    # Group by text_id and count the sentences per group
    sentence_counts = df.groupby('id')['sentence'].count()
    
    # Compute the required statistics
    mean_sentences = sentence_counts.mean()
    min_sentences = sentence_counts.min()
    max_sentences = sentence_counts.max()
    square_mean_sentences = np.mean(sentence_counts**2)
    
    # Prepare the results in a dictionary
    stats = {
        'mean': mean_sentences,
        'min': min_sentences,
        'max': max_sentences,
        'square_mean': square_mean_sentences
    }

    return stats

def merge_by_id(list1, list2):
    # Create a lookup dictionary from list2 using 'id' as the key
    lookup = {item['id']: item['original_text'] for item in list2}
    lookup1 = {item['id']: item['pubnbr'] for item in list2}
    lookup2 = {item['id']: item['pubdate'] for item in list2}

    # Merge with corresponding entry in list1
    merged = []
    for item in list1:
        merged_item = {
            'id': item['id'],
            'text': item['text'],
            'pubdate': lookup2.get(item['id']) ,
            'pubnbr':lookup1.get(item['id']) ,
            'original_text': lookup.get(item['id'])  # Use .get() to avoid KeyError
        }
        merged.append(merged_item)
    
    return merged