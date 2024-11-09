import sqlite3

def initialize_db(db_path="memories.db"):
    """
    Initialize the SQLite database and create the memories table if it doesn't exist.
    """

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT UNIQUE,
                        content TEXT,
                        keywords TEXT,
                        faiss_index INTEGER
                     )''')
    conn.commit()
    conn.close()   

def add_to_db(title, content, keywords, faiss_index, db_path="memories.db"):
    """
    Add a new memory to the database.
    """

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO memories (title, content, keywords, faiss_index)
                          VALUES (?, ?, ?, ?)''', (title, content, ','.join(keywords), faiss_index))
        conn.commit()
        print(f"Added to database: {title}")
    except Exception as e:
        print(f"Error inserting into database: {e}")
    finally:
        conn.close()


def get_entry_by_faiss_index(faiss_index, db_path="memories.db"):
    """
    Retrieve a memory from the database by its FAISS index.
    """
        # Embed the content
    content_embedding = get_embedding(content)  # Use OpenAI embedding API
    content_embedding_np = np.array([content_embedding]).astype('float32')  # Convert to NumPy array

    # Add embedding to Faiss
    faiss_index_position = index.ntotal  # The next index position in Faiss
    index.add(content_embedding_np)

    # Store in SQLite
    add_to_db(title, content, keywords, faiss_index_position, db_path)

def get_graph_info(db_path="memories.db"):
    """
    Retrieve all notes and their associated keywords from the database.

    Args:
        db_path (str): The path to the SQLite database file.

    Returns:
        list: A list of tuples containing titles and keywords.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT title, keywords FROM memories')
    rows = cursor.fetchall()
    conn.close()
    return rows  # This will be a list of tuples (title, keywords)

def get_all_keywords(db_path="memories.db"):
    """
    Retrieve all unique keywords stored in the database.

    Args:
        db_path (str): The path to the SQLite database file.

    Returns:
        set: A set of all unique keywords.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT keywords FROM memories')
    rows = cursor.fetchall()
    conn.close()

    keywords_set = set()
    for row in rows:
        keywords_str = row[0]
        if keywords_str:
            # Split the comma-separated string into a list of keywords
            keywords = [keyword.strip() for keyword in keywords_str.split(',')]
            # Add the keywords to the set
            keywords_set.update(keywords)
    return keywords_set