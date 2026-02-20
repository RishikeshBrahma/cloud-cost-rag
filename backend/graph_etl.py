import os
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

class RAGPipeline:
    def __init__(self, uri, auth):
        
        self.driver = GraphDatabase.driver(uri, auth=auth)
        
        
        print("Loading embedding model (this takes a few seconds)...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded!")
        
        
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def close(self):
        self.driver.close()

    def generate_and_store_embeddings(self):
        """Part C: Generates embeddings for node descriptions and stores them in Neo4j"""
        print("Generating embeddings for Knowledge Graph...")
        
        
        fetch_query = "MATCH (c:FOCUSColumn) WHERE c.description IS NOT NULL RETURN c.name AS name, c.description AS desc"
        records, _, _ = self.driver.execute_query(fetch_query, database_="neo4j")
        
        
        update_query = """
        MATCH (c:FOCUSColumn {name: $name})
        CALL db.create.setNodeVectorProperty(c, 'embedding', $embedding)
        """
        
        count = 0
        for record in records:
            name = record["name"]
            desc = record["desc"]
            
            embedding = self.embedding_model.encode(desc).tolist() 
            self.driver.execute_query(update_query, name=name, embedding=embedding, database_="neo4j")
            count += 1
            
        print(f"Successfully embedded and stored {count} nodes!")

    def hybrid_search(self, user_question):
        """Part D: Combines Vector Similarity with Graph Traversal"""
        
        # Convert user question to a vector
        question_embedding = self.embedding_model.encode(user_question).tolist()
        
        # Hybrid Cypher Query: Find similar columns, then traverse to find connected vendor columns
        hybrid_query = """
        CALL db.index.vector.queryNodes('focus_embeddings', 3, $question_embedding)
        YIELD node AS focusCol, score
        OPTIONAL MATCH (vendorCol)-[:MAPS_TO]->(focusCol)
        RETURN focusCol.name AS FocusColumn, 
               focusCol.description AS Description, 
               score AS SemanticSimilarity,
               collect(vendorCol.name) AS VendorEquivalents
        """
        
        results, _, _ = self.driver.execute_query(hybrid_query, question_embedding=question_embedding, database_="neo4j")
        
        # Assemble Context
        context = "Knowledge Graph Context:\n"
        for row in results:
            context += f"- Standard Column: {row['FocusColumn']} (Similarity: {row['SemanticSimilarity']:.2f})\n"
            context += f"  Description: {row['Description']}\n"
            context += f"  Vendor Equivalents: {row['VendorEquivalents']}\n"
            
        return context

    def ask_llm(self, user_question):
        """Part D: Passes the Graph context and the user question to OpenAI"""
        
        context = self.hybrid_search(user_question)
        
        system_prompt = f"""You are a Cloud FinOps Expert. Answer the user's question using ONLY the context provided below. 
        If the answer is not in the context, say "I don't have enough information in the Knowledge Graph."
        
        {context}
        """
        
        print("\n--- Sending Context to LLM ---")
        print(context)
        
        # Generate Answer using the Chat Completions API
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        
        return response.choices[0].message.content

if __name__ == "__main__":
    rag = RAGPipeline(URI, AUTH)
    
    test_question = "What is the amortized cost of a charge and how is it mapped?"
    print(f"\nUser Question: {test_question}")
    
    answer = rag.ask_llm(test_question)
    print(f"\nLLM Answer:\n{answer}")
    
    rag.close()