import os
import json
import logging
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

# Importers for specific file types
from pypdf import PdfReader
from PIL import Image
import pytesseract

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(__file__)
DB_DIR = os.path.join(BASE_DIR, "db")
DEFAULT_DOCS_DIR = os.path.join(BASE_DIR, "docs")
INDEX_STATE_FILE = os.path.join(DB_DIR, "index_state.json")

class RAGIndexer:
    def __init__(self, collection_name="mcp_knowledge"):
        self.chroma_client = chromadb.PersistentClient(path=DB_DIR)
        
        # Use sentence-transformers for local embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        self.index_state = self._load_index_state()

    def _load_index_state(self):
        """Loads the incremental indexing state."""
        if os.path.exists(INDEX_STATE_FILE):
            try:
                with open(INDEX_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load index state: {e}")
        return {}

    def _save_index_state(self):
        """Saves the incremental indexing state to disk."""
        os.makedirs(DB_DIR, exist_ok=True)
        try:
            with open(INDEX_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.index_state, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save index state: {e}")

    def _extract_text_from_pdf(self, file_path):
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            logging.error(f"Error reading PDF {file_path}: {e}")
        return text
        
    def _extract_text_from_image(self, file_path):
        text = ""
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            if not text.strip():
                logging.warning(f"OCR found no text in image {file_path}. Is Tesseract installed?")
        except Exception as e:
            logging.error(f"Error reading image {file_path} via OCR: {e}")
        return text

    def extract_text_from_file(self, file_path):
        """Dispatches extracting logic based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".bmp"]:
            return self._extract_text_from_image(file_path)
        elif ext in [".md", ".txt", ".cpp", ".h", ".cs", ".py", ".json"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except UnicodeDecodeError:
                # Fallback to general read
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                logging.error(f"Error reading text file {file_path}: {e}")
                return ""
        else:
            logging.warning(f"Unsupported file type for extraction: {ext}")
            return ""

    def chunk_text(self, text, chunk_size=1000, overlap=100):
        chunks = []
        for i in range(0, len(text), max(1, chunk_size - overlap)):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def index_file(self, file_path, force=False):
        """
        Indexes a single file. Skips if the file modifications time hasn't changed,
        allowing the process to incrementally resume if it crashes.
        """
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."
            
        file_mtime = os.path.getmtime(file_path)
        file_key = os.path.abspath(file_path)
        
        # Check if the file has already been indexed and hasn't changed
        if not force and file_key in self.index_state:
            last_mtime = self.index_state[file_key].get("mtime", 0)
            if file_mtime <= last_mtime:
                msg = f"Skipped {os.path.basename(file_path)} (already indexed with same mtime)."
                logging.info(msg)
                return msg

        text = self.extract_text_from_file(file_path)
        if not text.strip():
            msg = f"Failed to extract text from {os.path.basename(file_path)} or file is empty."
            logging.warning(msg)
            return msg
        
        chunks = self.chunk_text(text)
        if not chunks:
            return f"No valid chunks generated for {file_path}."

        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_path, "mtime": file_mtime} for _ in range(len(chunks))]

        try:
            self.collection.upsert(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            # Update State
            self.index_state[file_key] = {
                "mtime": file_mtime,
                "timestamp": datetime.now().isoformat(),
                "chunks": len(chunks)
            }
            self._save_index_state()
            
            msg = f"Successfully indexed {len(chunks)} chunks from {os.path.basename(file_path)}."
            logging.info(msg)
            return msg
            
        except Exception as e:
            return f"Error indexing {file_path}: {e}"

    def index_directory(self, dir_path=None, force=False):
        """
        Walks a directory and indexes files incrementally.
        Defaults to the self-contained 'docs/' folder if dir_path is entirely omitted.
        """
        if not dir_path:
            dir_path = DEFAULT_DOCS_DIR
            
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            return f"Directory {dir_path} did not exist and was created. It is currently empty."

        results = []
        indexed_count = 0
        skipped_count = 0

        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                result = self.index_file(file_path, force=force)
                results.append(result)
                
                if "Skipped" in result:
                    skipped_count += 1
                elif "Successfully indexed" in result:
                    indexed_count += 1

        summary = f"\nDirectory Indexing Complete: {dir_path}\nTotal Files Processed: {len(files)}\nIndexed: {indexed_count} | Skipped (Cached): {skipped_count}"
        logging.info(summary)
        return "\n".join(results) + summary

    def search(self, query, n_results=5):
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logging.error(f"Error during search: {e}")
            return None
