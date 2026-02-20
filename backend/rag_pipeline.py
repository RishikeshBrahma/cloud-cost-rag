import os
import time
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv

# Load credentials
load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

class RAGPipeline:
    def __init__(self, uri, auth):
        
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.driver.verify_connectivity()
        
        
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        
        self.model_id = "gemini-3-flash-preview" 
        print(f"RAG Pipeline online using: {self.model_id}")

    def close(self):
        
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed.")

    def hybrid_search(self, user_question):
        """Vector Search + Graph Context Retrieval"""
        question_embedding = self.embedding_model.encode(user_question).tolist()
        
        query = """
        CALL db.index.vector.queryNodes('focus_embeddings', 3, $question_embedding)
        YIELD node AS focusCol, score
        OPTIONAL MATCH (vendorCol)-[:MAPS_TO]->(focusCol)
        RETURN focusCol.name AS FocusName, 
               focusCol.description AS Description, 
               score AS Similarity,
               collect(vendorCol.name) AS Vendors
        """
        results, _, _ = self.driver.execute_query(query, question_embedding=question_embedding)
        
        context = "CLOUD DATA CONTEXT:\n"
        for r in results:
            context += f"- {r['FocusName']}: {r['Description']} (Mapped to: {r['Vendors']})\n"
        return context

    def ask_llm(self, user_question):
        """Generation with a retry loop for 429 Quota errors"""
        context = self.hybrid_search(user_question)
        
        system_instruction = (
            "You are a Cloud FinOps expert. Answer the question using ONLY "
            f"the context provided below.\n\nCONTEXT:\n{context}"
        )
        
        
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=user_question,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1
                    )
                )
                return response.text
            except errors.ClientError as e:
                if "429" in str(e) and attempt < 2:
                    print(f"API Busy (429). Retrying in {10 * (attempt + 1)}s...")
                    time.sleep(10 * (attempt + 1))
                else:
                    return f"Pipeline Error: {str(e)}"

if __name__ == "__main__":
    rag = RAGPipeline(URI, AUTH)
    try:
        query = "Explain BilledCost vs EffectiveCost in AWS/Azure."
        print(f"\nQUERY: {query}")
        print(f"\nAI ANSWER:\n{rag.ask_llm(query)}")
    finally:
        rag.close() 