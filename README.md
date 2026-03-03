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

### Hugging Face Token Setup

To use private models or access Hugging Face resources:

1. Get your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

2. Copy `env_sample` to `.env`:

```bash
cp env_sample .env
```

3. Add your token to `.env`:

```plaintext
HF_TOKEN="your_huggingface_token_here"
```

The server will automatically load this token when initialized.

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
- **HTML**: HTML and HTM files - parsed with BeautifulSoup, script/style tags removed
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
- `beautifulsoup4`: HTML parsing
- `markdown`: Markdown processing

## Configuration

Python version is locked to 3.11 via `.python-version` file. Modify if needed.

Embedding model: `all-MiniLM-L6-v2` (configurable in rag_indexer.py)

## Notes

- The knowledge base is self-contained in the `db/` folder
- Indexing tracks file modification times to support resumable operations
- ChromaDB uses persistent SQLite storage

## Integration with AI Tools

### VS Code with Cline or MCP Extensions

1. Install the MCP extension or Cline extension in VS Code
2. Add configuration to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "mcp_rag": {
      "command": "pipenv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/mcp-rag"
    }
  }
}
```

3. In VS Code, use the MCP commands to search your knowledge base:
   - Open Command Palette (Ctrl+Shift+P)
   - Search for "MCP: Call Tool"
   - Select "search_engine_knowledge"

### Cursor Editor

1. Create a `.cursor/mcp-config.json` in your project:

```json
{
  "mcpServers": {
    "mcp_rag": {
      "command": "pipenv",
      "args": ["run", "python", "server.py"],
      "cwd": "/path/to/mcp-rag"
    }
  }
}
```

2. In Cursor, use `@mcp-rag` to reference the RAG server in prompts:

```
@mcp-rag search for architecture patterns in C++
```

### Anthropic Claude (Claude Desktop)

1. Add to your Claude desktop config (`~/.claude/config.json` or via CLI):

```json
{
  "mcpServers": {
    "mcp_rag": {
      "command": "pipenv",
      "args": ["run", "python", "server.py"],
      "cwd": "/absolute/path/to/mcp-rag"
    }
  }
}
```

2. In your Claude conversation, use the tool directly:

```
Use the search_engine_knowledge tool to find information about memory alignment in C++
```

### Example Workflows

#### Indexing Documentation

```bash
# Terminal in project
pipenv run python server.py

# In Cursor/Claude prompt
@mcp-rag Index all documentation from my project
# Pass: {"file_path": "/absolute/path/to/docs", "force_reindex": false}
```

#### Searching Knowledge Base

```
# In any MCP-enabled editor
Query: "How should I structure game loops?"
Domain: "C++"

# Returns relevant chunks from indexed documentation
```

#### Multiple Tool Calls

```
# First, index new files
Call: index_knowledge_file
Args: {"file_path": "/docs/new_architecture.md"}

# Then search the updated knowledge base
Call: search_engine_knowledge
Args: {"query": "class hierarchy design", "domain": "C++"}
```

### Running as Background Service

For continuous access without restarting:

```bash
# Windows PowerShell
Start-Process -NoNewWindow -FilePath "pipenv" -ArgumentList "run python server.py"

# macOS/Linux
nohup pipenv run python server.py &
```

Get the process ID and keep it running for multiple editor instances.

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
