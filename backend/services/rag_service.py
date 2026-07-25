# =============================================================================
# backend/services/rag_service.py
#
# Service to ingest documents, chunk them, embed, and store in ChromaDB.
# =============================================================================

import os
import logging
from typing import List, Dict, Any

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

log = logging.getLogger(__name__)

class RAGService:
    def __init__(self, persist_directory: str = "artifacts/chroma_db"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize Embeddings
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize ChromaDB Vector Store
        self.vector_store = Chroma(
            collection_name="knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
    def _get_loader(self, file_path: str):
        """Returns the appropriate LangChain document loader based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".txt":
            return TextLoader(file_path)
        elif ext == ".csv":
            return CSVLoader(file_path)
        elif ext == ".docx":
            return Docx2txtLoader(file_path)
        elif ext == ".md":
            # Using TextLoader for simple markdown if unstructured is not installed
            return TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def ingest_document(self, file_path: str, metadata: Dict[str, Any] = None) -> int:
        """
        Loads a document, chunks it, and stores the vectors in ChromaDB.
        Returns the number of chunks added.
        """
        log.info(f"Ingesting document into RAG: {file_path}")
        
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # Inject custom metadata (like session_id or user_id)
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
                
        # Chunk the documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        
        chunks = text_splitter.split_documents(documents)
        
        if not chunks:
            log.warning("No text extracted from document.")
            return 0
            
        # Store in ChromaDB
        self.vector_store.add_documents(chunks)
        log.info(f"Successfully added {len(chunks)} chunks to ChromaDB.")
        
        return len(chunks)

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieves the top k most relevant document chunks for a given query.
        """
        log.info(f"Retrieving RAG context for query: {query}")
        # Return documents sorted by relevance score
        results = self.vector_store.similarity_search(query, k=k)
        return results
