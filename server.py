import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
from mcp.types import Tool, TextContent
from rag_indexer import RAGIndexer

# Initialize Server and Indexer
server = Server("mcp_rag")
indexer = RAGIndexer()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools from this server."""
    return [
        Tool(
            name="search_engine_knowledge",
            description="Queries the local ChromaDB for architecture rules, C++, Vulkan, SDL3, OpenGL, Jolt Physics, or DOD patterns.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'How is memory alignment handled?')"
                    },
                    "domain": {
                        "type": "string",
                        "description": "The specific domain to search within (e.g., 'Vulkan', 'DOD', 'C++')"
                    }
                },
                "required": ["query", "domain"]
            }
        ),
        Tool(
            name="index_knowledge_file",
            description="Ingests new files (PDF, Image, .cpp, .h, or .md) into the local ChromaDB. If no path is provided, it automatically indexes all files in the tools/mcp_rag/docs directory, resuming only those that have changed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Optional: Absolute path to the file or directory to index. If omitted, defaults to tools/mcp_rag/docs."
                    },
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Optional: If True, forces the file to be re-indexed even if it hasn't been modified."
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution requests."""
    if name == "search_engine_knowledge":
        query = arguments.get("query", "")
        domain = arguments.get("domain", "")
        full_query = f"{domain} {query}".strip()
        
        results = indexer.search(full_query, n_results=5)
        
        if results and results.get('documents') and len(results['documents']) > 0 and results['documents'][0]:
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            
            response_text = "Search Results:\n\n"
            for i, doc in enumerate(docs):
                source = metadatas[i].get("source", "Unknown Source")
                response_text += f"--- Source: {source} ---\n{doc}\n\n"
            return [TextContent(type="text", text=response_text)]
        else:
            return [TextContent(type="text", text="No relevant information found.")]
            
    elif name == "index_knowledge_file":
        file_path = arguments.get("file_path", "")
        force = arguments.get("force_reindex", False)
        
        # If omitted or directory, run directory indexing
        if not file_path or os.path.isdir(file_path):
            result = indexer.index_directory(dir_path=file_path, force=force)
        else:
            result = indexer.index_file(file_path, force=force)
            
        return [TextContent(type="text", text=result)]
        
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Starts the standard input/output MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp_rag",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
