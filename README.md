# MCP RAG Server

A Model Context Protocol (MCP) server that implements Retrieval-Augmented Generation (RAG) capabilities with local embeddings and persistent knowledge storage using ChromaDB.

## Features

- Local knowledge base indexing with ChromaDB
- Support for multiple file formats: PDF, images (with OCR), Markdown, C++/C#, JSON, and plain text
- Incremental indexing with change detection to avoid reprocessing unchanged files
- Semantic search with sentence-transformers embeddings
- MCP-compatible tools for knowledge search and file indexing
- Persistent storage in local SQLite database

## Requirements

- Python 3.11 or higher
- Tesseract OCR (optional, for image text extraction)
- Pipenv for dependency management

## Installation

### Windows

```powershell
$env:PIPENV_VENV_IN_PROJECT = 1
pyenv install 3.11.9
pipenv install
```

### macOS / Linux

```bash
export PIPENV_VENV_IN_PROJECT=1
pyenv install 3.11.9
pipenv install
```

If you don't have pyenv installed, you can install Python 3.11 directly from your package manager or [python.org](https://www.python.org/downloads/).

## Project Structure

```
mcp-rag/
├── server.py              # MCP server implementation
├── rag_indexer.py         # RAG indexing and search logic
├── Pipfile                # Dependency definitions
├── .python-version        # Python version specification
├── db/                    # ChromaDB persistent storage
├── docs/                  # Documents folder for indexing
└── README.md              # This file
```

## Usage

Start the server using pipenv:

```bash
pipenv run python server.py
```

The server exposes two main tools:

### 1. search_engine_knowledge

Queries the knowledge base for information.

**Parameters:**

- `query` (string, required): Search query (e.g., "How is memory alignment handled?")
- `domain` (string, required): Domain scope (e.g., "Vulkan", "DOD", "C++")

**Example:**

```json
{
  "query": "How is memory alignment handled?",
  "domain": "C++"
}
```

### 2. index_knowledge_file

Indexes new files into the knowledge base.

**Parameters:**

- `file_path` (string, optional): Absolute path to file or directory. Defaults to `docs/` folder if omitted.
- `force_reindex` (boolean, optional): Force re-indexing even if file hasn't changed.

**Example:**

```json
{
  "file_path": "/path/to/docs",
  "force_reindex": false
}
```

## Supported File Types

- **PDF**: Text extracted via pypdf
- **Images**: PNG, JPG, JPEG, BMP - text extracted with OCR (Tesseract)
- **Code**: C++, C#, Python, JSON files
- **Documents**: Markdown, plain text files

## Database

ChromaDB stores:

- Document chunks with embeddings
- Metadata (source file path, modification time)
- Indexing state for incremental processing

Location: `db/` directory

## Dependencies

See `Pipfile` for complete list:

- `mcp`: Model Context Protocol framework
- `chromadb`: Vector database
- `sentence-transformers`: Local embeddings
- `pypdf`: PDF text extraction
- `pillow`: Image handling
- `pytesseract`: OCR integration
- `markdown`: Markdown processing

## Configuration

Python version is locked to 3.11 via `.python-version` file. Modify if needed.

Embedding model: `all-MiniLM-L6-v2` (configurable in rag_indexer.py)

## Notes

- The knowledge base is self-contained in the `db/` folder
- Indexing tracks file modification times to support resumable operations
- ChromaDB uses persistent SQLite storage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Created by [Marcio Vale](https://github.com/marciocamello)

- Frontend Developer at Smartdigit
- GamePlay Design student with Unreal Engine, Blender, and ZBrush
- Over 15 years of experience in software development
- Location: Portugal

For more information, visit:

- GitHub: [github.com/marciocamello](https://github.com/marciocamello)
- Portfolio: [vovozera.com](http://vovozera.com/)
- ArtStation: [marcioavelinodovale](https://www.artstation.com/marcioavelinodovale)
