# ☁️ FinOps Knowledge Assistant

A professional-grade **Graph-RAG** (Retrieval-Augmented Generation) system built to help cloud teams understand **FOCUS 1.0** (FinOps Open Cost & Usage Specification) standards and how their AWS/Azure costs map to them.

---

## 🚀 Key Features
- **Knowledge Graph:** Uses **Neo4j** to store complex relationships between cloud resources, services, and billing accounts.
- **Hybrid Search:** Combines **Vector Similarity** (semantic meaning) with **Graph Traversal** (structured relationships) for highly accurate answers.
- **LLM Powered:** Uses **Google Gemini 3 Flash** to generate natural language explanations grounded in your specific graph data.
- **Interactive UI:** A clean **Streamlit** dashboard for chatting and monitoring graph statistics.

---

## 🛠️ Tech Stack
- **Database:** Neo4j AuraDB (Cloud)
- **Backend:** FastAPI (Python)
- **Frontend:** Streamlit
- **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM:** Google Gemini API

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
2. Environment Variables
Create a .env file in the root directory and add your credentials:

Code snippet
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
GEMINI_API_KEY=your-gemini-api-key
3. Install Dependencies
Bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
🏃 Running the Application
To run the full system, you need to start the backend and frontend in two separate terminals:

Terminal 1: Backend (FastAPI)
Bash
python -m uvicorn backend.main:app --reload
The API will be available at http://localhost:8000

Terminal 2: Frontend (Streamlit)
Bash
python -m streamlit run frontend/app.py
The UI will open automatically at http://localhost:8501

📊 Knowledge Graph Schema
The system uses a property graph model:

(CostRecord): Individual billing line items.

(Service): AWS/Azure services (e.g., S3, EC2).

(Resource): Specific cloud resources.

(FOCUSColumn): The standardized FinOps definitions.

Relationships: INCURRED_BY, USES_SERVICE, MAPS_TO.

🤝 Acknowledgements
Built as part of the AAIDC FinOps Project.

Based on the FOCUS 1.0 specification.
