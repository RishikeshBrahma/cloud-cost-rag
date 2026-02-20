import streamlit as st
import requests

# Page Configuration
st.set_page_config(
    page_title="FinOps Knowledge Assistant",
    page_icon="☁️",
    layout="centered"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("☁️ FinOps Knowledge Assistant")
st.info("Ask about FOCUS 1.0 standards and how AWS/Azure costs map to them.")

# --- Sidebar: Knowledge Graph Stats ---
st.sidebar.header("📊 Graph Insights")
if st.sidebar.button("Refresh Graph Stats"):
    try:
        # Calls the /stats endpoint from our FastAPI backend
        response = requests.get("http://localhost:8000/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            for label, count in stats.items():
                st.sidebar.metric(label=f"Node: {label}", value=count)
        else:
            st.sidebar.error("Backend returned an error.")
    except Exception:
        st.sidebar.error("Backend Offline! Start main.py first.")

# --- Chat Interface Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if prompt := st.chat_input("Ex: What is the difference between BilledCost and EffectiveCost?"):
    # 1. Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the FastAPI Backend
    with st.chat_message("assistant"):
        with st.spinner("🤖 Consulting Knowledge Graph..."):
            try:
                # Matches the /query endpoint in backend/main.py
                api_response = requests.post(
                    "http://localhost:8000/query",
                    json={"question": prompt},
                    timeout=60  # Give the LLM time to think
                )
                
                if api_response.status_code == 200:
                    answer = api_response.json().get("answer", "No answer received.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Error {api_response.status_code}: {api_response.text}"
                    st.error(error_msg)
                    
            except requests.exceptions.ConnectionError:
                st.error("🚨 Connection Failed! Make sure your FastAPI server is running at http://localhost:8000")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")