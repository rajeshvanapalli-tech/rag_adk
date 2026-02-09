import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from .llm import get_llm, BaseLLM

class UniversalEmbeddingFunction(EmbeddingFunction):
    def __init__(self, llm: BaseLLM, task_type: str = "retrieval_document"):
        self.llm = llm
        self.task_type = task_type

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            embeddings.append(self.llm.get_embedding(text, task_type=self.task_type))
        return embeddings

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.llm = get_llm()
        self.embedding_fn_doc = UniversalEmbeddingFunction(self.llm, "retrieval_document")
        self.embedding_fn_query = UniversalEmbeddingFunction(self.llm, "retrieval_query")

    @property
    def provider(self):
        return os.getenv("MODEL_PROVIDER", "google").lower()

    @property
    def collection(self):
        return self.client.get_or_create_collection(
            name=f"rag_docs_{self.provider}",
            embedding_function=self.embedding_fn_doc
        )

    @property
    def history_collection(self):
        return self.client.get_or_create_collection(
            name=f"chat_history_{self.provider}",
            embedding_function=self.embedding_fn_doc
        )

    def add_documents(self, documents: list[str], metadatas: list[dict], ids: list[str]):
        """Adds documents to the vector store."""
        if not documents:
            return
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, n_results: int = 7, filter_metadata: dict = None) -> list[str]:
        """Searches for relevant documents."""
        # We manually embed the query using the query-specific embedding function
        query_embeddings = self.embedding_fn_query([query])
        
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=filter_metadata
        )
        if results['documents']:
            return results['documents'][0]
        return []

    def search_as_tool(self, query: str, category: str = None) -> str:
        """
        Optimized Search: Fetches top 2 most relevant chunks for precise answers.
        """
        # Search with k=5 to find good candidates
        docs = self.search(query, n_results=5, filter_metadata={"category": category} if category else None)
        
        if not docs:
            return "No relevant information found in the knowledge base."
            
        # Return only top 2 chunks to keep context focused and short
        return "\n\n---\n\n".join(docs[:2])


    def add_chat_history(self, user_id: str, role: str, content: str, timestamp: float, conversation_id: str = None):
        """Adds a chat message to history."""
        import uuid
        metadata = {"user_id": user_id, "role": role, "timestamp": timestamp}
        if conversation_id:
            metadata["conversation_id"] = conversation_id
            
        self.history_collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def search_chat_history(self, user_id: str, query: str, n_results: int = 5, conversation_id: str = None) -> list[str]:
        """Searches past chat history for similar queries/responses."""
        where_clause = {"user_id": user_id}
        
        query_embeddings = self.embedding_fn_query([query])
        
        results = self.history_collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where_clause
        )
        if results['documents']:
            return results['documents'][0]
        return []

    def get_conversation_history(self, conversation_id: str) -> list[dict]:
        """Retrieves full history for a conversation, sorted by timestamp."""
        result = self.history_collection.get(
            where={"conversation_id": conversation_id}
        )
        
        messages = []
        if result['documents']:
            for i in range(len(result['documents'])):
                msg = {
                    "text": result['documents'][i],
                    "role": result['metadatas'][i].get("role"),
                    "timestamp": result['metadatas'][i].get("timestamp", 0),
                    "user_id": result['metadatas'][i].get("user_id")
                }
                messages.append(msg)
        
        return sorted(messages, key=lambda x: x["timestamp"])

    def delete_conversation_history(self, conversation_id: str):
        """Deletes all history for a specific conversation."""
        try:
             self.history_collection.delete(
                 where={"conversation_id": conversation_id}
             )
        except Exception as e:
            print(f"Error deleting history for {conversation_id}: {e}")

    def delete_documents_by_source(self, source_filename: str):
        """Deletes all document chunks from a specific source file."""
        try:
            self.collection.delete(
                where={"source": source_filename}
            )
            print(f"Deleted documents from source: {source_filename}")
        except Exception as e:
            print(f"Error deleting documents for {source_filename}: {e}")

    def clear_all_documents(self):
        """Deletes all documents from the rag_docs collection."""
        try:
            # We can't actually 'clear' a collection in Chroma easily without deleting/recreating
            # or deleting every ID. Deleting and recreating is cleaner.
            self.client.delete_collection("rag_docs")
            self.client.get_or_create_collection(
                name="rag_docs",
                embedding_function=self.embedding_fn_doc
            )
            print("Cleared all rag_docs documents.")
        except Exception as e:
            print(f"Error clearing rag_docs: {e}")

    def reset_database(self):
        """Resets the vector store by deleting collections."""
        try:
             self.client.delete_collection("rag_docs")
             self.client.delete_collection("chat_history")
             print("Vector collections deleted.")
        except Exception as e:
             print(f"Error deleting collections: {e}")
