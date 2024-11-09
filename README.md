# MemoryMaker

MemoryMaker is a simple implementation of a Retrieval-Augmented Generation (RAG) application that enables users to add and retrieve information using vector embeddings. By leveraging OpenAI’s embedding models and FAISS for similarity search, MemoryMaker offers an efficient way to store "memories" and retrieve them based on similarity to input queries.

**Note:** This application is designed primarily for storing and retrieving saved information. While it includes a chat interface, it does not maintain chat history for context-aware conversations.


<img width="1428" alt="image" src="https://github.com/user-attachments/assets/baa937b1-653a-4063-917a-32532d0bced3">


---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Accessing the Web Interface](#accessing-the-web-interface)
- [How It Works](#how-it-works)
- [Technologies Used](#technologies-used)
- [Dependencies](#dependencies)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Features
- **Add Memories**: Input information that is stored with vector embeddings for later retrieval.
- **Retrieve Information**: Search and retrieve stored information based on similarity to input queries.
- **Data Visualization**: A graphical interface using Cytoscape.js displays stored memories and their relationships.
- **Simple Chat Interface**: Interact with the application via a chat interface (note: chat history is not maintained).

---

## Installation

### Prerequisites
- Python 3.7 or higher
- Docker and VS Code (Optional): For a consistent development environment using the Dev Container setup.

### Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/memorymaker.git
   cd memorymaker
   ```

2. **Using Dev Container (Optional but Recommended)**
   This project includes a `.devcontainer.json` configuration for a consistent development environment using VS Code and Docker.

   - **Install Required Tools**:
     - Docker Desktop
     - Visual Studio Code
     - Remote - Containers Extension

   - **Open the Project in Dev Container**:
     - Open the project folder in VS Code.
     - When prompted, reopen the project in a Dev Container.
     - VS Code will build the container defined in `.devcontainer/devcontainer.json`.

3. **Set Up Environment Variables**
   Create a `.env` file in the project root directory and add the following:

   ```plaintext
   OPENAI_API_KEY=your_openai_api_key  
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key  
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key  
   LANGFUSE_HOST=your_langfuse_host  
   ```

   Replace `your_openai_api_key`, `your_langfuse_public_key`, `your_langfuse_secret_key`, and `your_langfuse_host` with your actual credentials.

   **Note:** Obtain an API key from OpenAI and Langfuse credentials if you plan to use observability features.

4. **Install Dependencies**
   If not using the Dev Container, you can install dependencies manually:

   - **Create a Virtual Environment (Optional but Recommended)**
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows use `venv\Scripts\activate`
     ```

   - **Install Python Dependencies**
     ```bash
     pip install -r requirements.txt
     ```

---

## Usage

### Running the Application
Run the following command to start the Flask application:

```bash
python main.py
```

### Accessing the Web Interface
Once the application is running, open your web browser and navigate to:

```plaintext
http://localhost:5000
```

---

## How It Works

### 1. Adding Memories
- Users input information through the chat interface.
- The application analyzes the input, extracts keywords, and creates vector embeddings using OpenAI’s embedding models.
- The information is stored in a SQLite database along with its embedding.
- FAISS is used to index and search embeddings for efficient similarity queries.

### 2. Retrieving Information
- When a user inputs a query, the application generates an embedding of the query.
- FAISS searches for similar embeddings in the database.
- Relevant memories are retrieved and displayed to the user.

### 3. Visualization
- The application visualizes memories and their relationships using a graph displayed with Cytoscape.js.
- Nodes represent memories and keywords, while edges represent relationships.

---

## Technologies Used
- **Python**: Core programming language.
- **Flask**: Web framework for handling HTTP requests and rendering templates.
- **OpenAI API**: For generating embeddings and processing natural language.
- **FAISS**: Facebook’s library for efficient similarity search.
- **SQLite**: Lightweight database for storing memories and embeddings.
- **Cytoscape.js**: JavaScript library for graph visualizations.
- **Langfuse**: For observability and monitoring of LLM interactions.
- **HTML/CSS/JavaScript**: Front-end technologies for the user interface.

---

## Dependencies
All Python dependencies are listed in the `requirements.txt` file. They can be installed using:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `numpy`
- `faiss-cpu`
- `flask`
- `openai`
- `langfuse`
- `python-dotenv`

---

## License
This project is provided for educational and portfolio purposes. It is free to use and modify for personal use. Commercial use is not permitted without explicit permission.

---

## Acknowledgments
- **OpenAI**: For providing the APIs for embeddings and language processing.
- **Facebook AI Research**: For FAISS, the similarity search library.
- **Cytoscape.js**: For the graph visualization library.
- **Langfuse**: For tools aiding in observability of LLM interactions.

This project demonstrates a simple implementation of a Retrieval-Augmented Generation (RAG) system, showcasing the integration of vector embeddings and similarity search for efficient information storage and retrieval.
