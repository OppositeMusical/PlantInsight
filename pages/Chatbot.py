import streamlit as st
import base64
import requests
import pickle
import os

# Load persistent vector_db from file
VECTOR_DB_FILE = os.path.join(os.path.dirname(__file__), "..", "Data", "vector_db.pkl")
if os.path.exists(VECTOR_DB_FILE):
    with open(VECTOR_DB_FILE, "rb") as f:
        vector_db = pickle.load(f)
else:
    vector_db = {}

st.title("🌱 PlantInsight")

if not vector_db:
    st.info("No plant data available. Please analyze images on the main page first.")
else:
    # Select image from database
    image_keys = list(vector_db.keys())
    selected_key = st.selectbox("Select an image to discuss:", image_keys)

    if selected_key:
        st.markdown("### 📷 Selected Image")
        st.image(base64.b64decode(selected_key), caption="Selected Plant Image", use_column_width=True)

        # Show identification and health assessment data
        data = vector_db[selected_key]
        if 'identification' in data:
            st.markdown("#### 🪴 Identification Data")
            st.json(data['identification'])
        if 'health_assessment' in data:
            st.markdown("#### 🩺 Health Assessment Data")
            st.json(data['health_assessment'])

        # Chatbot UI (ChatGPT-like)
        st.markdown("### 💬 Chat with Plant LLM (Ollama)")

        # Initialize chat history for each image separately
        chat_key = f"chat_history_{selected_key}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        # Display chat history
        for speaker, msg in st.session_state[chat_key]:
            if speaker == "user":
                st.markdown(
                    f"""
                    <div style='background:var(--primary-color,#262730);color:var(--text-color,#fafafa);padding:8px;border-radius:6px;margin-bottom:4px;border:1px solid #444;'>
                        <b>You:</b> {msg}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style='background:var(--secondary-background-color,#1a1a1a);color:var(--text-color,#fafafa);padding:8px;border-radius:6px;margin-bottom:4px;border:1px solid #444;'>
                        <b>Bot:</b> {msg}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # LLM selection UI
        llm_models = ["llama3"]  # Add more models if available in Ollama
        selected_llm = st.selectbox("Select LLM model:", llm_models, index=0)

        # Chat input area
        user_input = st.text_area("Type your message:", key=f"user_input_{selected_key}")

        # Send button
        if st.button("Send", key=f"send_{selected_key}") and user_input.strip():
            # Build context from previous turns and plant data
            context = f"Identification: {data.get('identification', {})}\nHealth: {data.get('health_assessment', {})}"
            history = "\n".join([f"{'User' if s == 'user' else 'Bot'}: {m}" for s, m in st.session_state[chat_key]])
            prompt = f"{context}\n\nConversation so far:\n{history}\nUser: {user_input}\nBot:"

            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": selected_llm,
                "prompt": prompt,
                "stream": False
            }
            try:
                response = requests.post(ollama_url, json=payload)
                if response.status_code == 200:
                    llm_output = response.json().get("response", "")
                else:
                    llm_output = f"Ollama API error: {response.status_code}"
            except Exception as e:
                llm_output = f"Error connecting to Ollama: {e}"

            st.session_state[chat_key].append(("user", user_input))
            st.session_state[chat_key].append(("bot", llm_output))
            st.rerun()