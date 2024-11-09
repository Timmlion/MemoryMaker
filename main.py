# Standard library imports
import os
import json
import sqlite3
import logging
import re
import uuid

# Third-party imports
import numpy as np
import faiss
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import openai

# Local imports
from langfuse import Langfuse
from langfuse.decorators import observe
from langfuse.openai import openai as langfuse_openai
from prompts import get_prompt
from database import (
    initialize_db,
    add_to_db,
    get_entry_by_faiss_index,
    get_graph_info,
    get_all_keywords
)

app = Flask(__name__)
faiss_index = None


def main():
    """
    Initialize the application by setting up the database and FAISS index.
    """
    global faiss_index
    load_dotenv()
    initialize_db()
    
    # Retrieve the OpenAI API key from environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key is not set in the environment variables.")

    # Set the OpenAI API key
    openai.api_key = api_key

    # Define the dimension of embeddings (OpenAI's embedding size)
    dimension = 1536
    faiss_index = faiss.IndexFlatL2(dimension)

    # Rebuild the FAISS index from existing embeddings in the database
    rebuild_faiss_index()

def setup_logger():
    """
    Set up the logger to log messages to a file with timestamps.
    """
    logging.basicConfig(
        level=logging.INFO,  # Log messages with level INFO and above
        format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
        datefmt='%Y-%m-%d %H:%M:%S',  # Timestamp format
        handlers=[
            logging.FileHandler("app.log"),  # Log to 'app.log' file
            logging.StreamHandler()  # Also output logs to the console
        ]
    )

def rebuild_faiss_index(db_path="memories.db"):
    """
    Rebuild the FAISS index from the embeddings stored in the SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    global faiss_index
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch all content entries from the database, ordered by their FAISS index
    cursor.execute('SELECT content FROM memories ORDER BY faiss_index')
    rows = cursor.fetchall()
    conn.close()

    embeddings = []
    for row in rows:
        content = row[0]
        # Generate embedding for each content entry
        embedding = get_embedding(content)
        embeddings.append(embedding)
    
    if embeddings:
        # Convert embeddings list to NumPy array of type float32
        embeddings_np = np.array(embeddings).astype('float32')
        # Add embeddings to the FAISS index
        faiss_index.add(embeddings_np)

def get_entry_by_faiss_index(faiss_idx, db_path="memories.db"):
    """
    Retrieve an entry from the database using the FAISS index.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT title, content, keywords FROM memories WHERE faiss_index = ?',
        (str(faiss_idx),)
    )
    result = cursor.fetchone()
    conn.close()
    return result 

def search_similar_entries(query_text, k=5, db_path="memories.db"):
    """
    Search for entries similar to the query_text using the FAISS index.

    Args:
        query_text (str): The text to search for similar entries.
        k (int): The number of similar entries to retrieve.
        db_path (str): The path to the SQLite database file.

    Returns:
        list: A list of dictionaries containing similar entries.
    """
    # Generate the embedding for the query text
    query_embedding = get_embedding(query_text)
    query_embedding_np = np.array([query_embedding]).astype('float32')

    # Search for the k nearest neighbors in the FAISS index
    distances, indices = faiss_index.search(query_embedding_np, k)

    results = []
    for faiss_idx in indices[0]:
        if faiss_idx == -1:
            continue  # Skip if no result found at this position
        # Retrieve the entry corresponding to the FAISS index
        entry = get_entry_by_faiss_index(faiss_idx, db_path)
        if entry:
            # Map the tuple to a dictionary for JSON format
            result_dict = {
                "title": entry[0],
                "content": entry[1],
                "keywords": entry[2]
            }
            results.append(result_dict)
    
    return results

def add_to_faiss_and_db(title, content, keywords, db_path="memories.db"):
    """
    Add a new entry to the FAISS index and the SQLite database.

    Args:
        title (str): The title of the content.
        content (str): The content to be added.
        keywords (list): A list of keywords associated with the content.
        db_path (str): The path to the SQLite database file.
    """
    # Embed the content using OpenAI's embedding API
    content_embedding = get_embedding(content)
    content_embedding_np = np.array([content_embedding]).astype('float32')

    # Get the next index position in FAISS
    faiss_index_position = faiss_index.ntotal
    # Add the embedding to the FAISS index
    faiss_index.add(content_embedding_np)

    # Store the new entry in the SQLite database
    add_to_db(title, content, keywords, faiss_index_position, db_path)

@observe()
def send_question_to_openai(system_prompt, user_prompt, message_history=None):
    """
    Send a question to OpenAI's API and return the response.

    Args:
        system_prompt (str): The system prompt guiding the assistant's behavior.
        user_prompt (str): The user's input or query.
        message_history (list, optional): A list of message dictionaries representing the conversation history.

    Returns:
        str: The assistant's response generated by OpenAI.
    """
    if message_history is None:
        # Start a new conversation with the system prompt and user prompt
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    else:
        # Continue the conversation using the provided message history
        messages = message_history.copy()
        # Ensure the system prompt is included at the beginning
        if not any(msg['role'] == 'system' for msg in messages):
            messages.insert(0, {"role": "system", "content": system_prompt})
        # Append the new user message
        messages.append({"role": "user", "content": user_prompt})

    try:
        # Send the messages to OpenAI's API to get a response
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        # Extract and return the assistant's reply
        assistant_reply = response.choices[0].message.content
        return assistant_reply
    except Exception as e:
        logging.error(f"An error occurred while communicating with OpenAI: {e}")
        return None

def get_embedding(text, model="text-embedding-3-small"):
    """
    Get the embedding of a text using OpenAI's embedding API.

    Args:
        text (str): The text to be embedded.
        model (str): The name of the embedding model to use.

    Returns:
        list: A list representing the embedding vector.
    """
    # Replace newlines to avoid issues with the API
    text = text.replace("\n", " ")
    # Generate and return the embedding
    return openai.embeddings.create(input=[text], model=model).data[0].embedding

def process_input(prompt):
    """
    Process user input by searching for similar entries, analyzing the input,
    updating the database and FAISS index if necessary, and generating a response.
    """
    logging.info("Processing input")
    keywords = get_all_keywords()
    # Analyze the user's input
    logging.info("Starting user input analysis")
    analysis = send_question_to_openai(get_prompt("analyzer") + "<keywords>" + str(keywords) + "</keywords>", prompt)
    logging.info("Analysis completed. Result: " + str(analysis))

    memory_added = False

    if analysis:
        try:
            analysis_data = json.loads(analysis)
            keywords = analysis_data.get("keywords", [])
            content = analysis_data.get("content")
            title = analysis_data.get("title")
            
            if content:
                logging.info("Adding information to DB")
                add_to_faiss_and_db(title, content, keywords)
                memory_added = True

        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from analysis.")

    # Search for similar information
    logging.info("Searching for similar entries")
    similar_entries = search_similar_entries(prompt)
    logging.info(f"Found {len(similar_entries)} similar entries")

    if similar_entries:
        logging.info("Gathering similar entries")
        combined_content = ' '.join(item['content'] for item in similar_entries)
        system_prompt = f"{get_prompt('assistant')}<context>{combined_content}</context>"
        assistant_response = send_question_to_openai(system_prompt, prompt)
    else:
        # If no similar entries are found, proceed with the user's prompt
        assistant_response = send_question_to_openai(get_prompt("assistant"), prompt)

    return assistant_response, memory_added

def sanitize_id(s):
    """
    Sanitize a string to be used as an ID by:
    - Converting to lowercase.
    - Replacing non-alphanumeric characters with underscores.
    - Removing leading digits.
    - Ensuring the ID is not empty.
    """
    try:
        s = s.lower().strip()
        s = re.sub(r'\W+', '_', s)  # Replace non-word characters with '_'
        s = re.sub(r'^_+', '', s)   # Remove leading underscores
        s = re.sub(r'^(\d)', r'_\1', s)  # Prefix leading digits with '_'
        if not s:
            s = 'id_' + str(uuid.uuid4()).replace('-', '')  # Generate a random ID if empty
        return s
    except Exception as e:
        app.logger.error(f"Error sanitizing ID for string '{s}': {e}", exc_info=True)
        # Return a fallback ID
        return 'id_' + str(uuid.uuid4()).replace('-', '')


# Route to serve the main page
@app.route('/')
def index():
    """
    Render the main chat interface.
    """
    return render_template('index.html')

# Route to handle chat messages
@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle incoming chat messages and return the assistant's response.
    """
    data = request.get_json()
    prompt = data.get("prompt")
    if prompt:
        logging.info("User input: " + prompt)
        response, memory_added = process_input(prompt)
        logging.info("Chat output: " + response)
        return jsonify({"response": response, "graph_updated": memory_added})
    return jsonify({"response": "Invalid input"}), 400


@app.route('/graph-data', methods=['GET'])
def graph_data():
    logging.info("Graph retrieval started")
    rows = get_graph_info()
    logging.info("Db returned: " + str(len(rows)) + " rows, for graph")
    try:
        nodes = []
        edges = []
        keyword_set = set()

        for row in rows:
            title = row[0]
            keywords_str = row[1]

            # Ensure title is not empty
            if title and title.strip():
                note_label = title.strip()
            else:
                note_label = 'untitled'

            # Normalize and sanitize the note title for ID
            note_id = f"note_{sanitize_id(note_label)}"
            app.logger.info(f"Creating note node with ID: {note_id}, Label: {note_label}")

            # Add note node
            nodes.append({
                'data': {'id': note_id, 'label': note_label, 'type': 'note'}
            })

            # Check if keywords_str is not None or empty
            if keywords_str:
                # Split the comma-separated string into a list and normalize keywords
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(',') if keyword.strip()]
                app.logger.info(f"Title: {title}, Parsed Keywords: {keywords}")
            else:
                keywords = []
                app.logger.info(f"Title: {title} has no keywords.")

            # Add keyword nodes and edges
            for keyword in keywords:
                keyword_normalized = keyword.lower()
                keyword_id = f"keyword_{sanitize_id(keyword_normalized)}"
                keyword_label = keyword.title()
                app.logger.info(f"Creating keyword node with ID: {keyword_id}, Label: {keyword_label}")

                if keyword_normalized not in keyword_set:
                    nodes.append({
                        'data': {'id': keyword_id, 'label': keyword_label, 'type': 'keyword'}
                    })
                    keyword_set.add(keyword_normalized)

                edge_id = f"edge_{note_id}_{keyword_id}"
                edges.append({
                    'data': {'id': edge_id, 'source': note_id, 'target': keyword_id}
                })
                app.logger.info(f"Creating edge with ID: {edge_id}, Source: {note_id}, Target: {keyword_id}")

        app.logger.info(f"Total nodes: {len(nodes)}, Total edges: {len(edges)}")
        return jsonify(nodes + edges)
    except Exception as e:
        app.logger.error(f"An error occurred in /graph-data: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while fetching graph data'}), 500
       
        
if __name__ == '__main__':
    setup_logger()
    main()
    app.run(host='0.0.0.0', port=5000, debug=True)