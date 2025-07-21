import streamlit as st
import requests
import base64
from PIL import Image
import pickle
import os

# Streamlit page config
st.set_page_config(page_title="Plant Identifier & Health Check", layout="centered")



# Input your Plant.id API Key here
API_KEY = "3HywOgP38ubLI7GBr4Kmy0ZSADLccuftFIJRpaOjSOq5goz6Fs"  # <-- Replace this with your actual API key
IDENTIFY_API_URL = "https://api.plant.id/v2/identify"
HEALTH_API_URL = "https://api.plant.id/v2/health_assessment"

st.set_page_config(page_title="Plant Health & ID", layout="centered")
st.title("🌱 Plant Health & Identification")
st.write("Upload a plant image to get both identification and health assessment.")

# Persistent vector database file
DATA_DIR = "Data"
VECTOR_DB_FILE = os.path.join(DATA_DIR, "vector_db.pkl")

# Ensure Data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Load or initialize vector_db
def load_vector_db():
    if os.path.exists(VECTOR_DB_FILE):
        with open(VECTOR_DB_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_vector_db(db):
    with open(VECTOR_DB_FILE, "wb") as f:
        pickle.dump(db, f)

# Simple in-memory vector database
vector_db = {}

# Use Streamlit session state for vector_db reference
if "vector_db" not in st.session_state:
    st.session_state.vector_db = load_vector_db()

vector_db = st.session_state.vector_db

# Encode image to base64
def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

def call_plant_api(image_bytes, endpoint, mode):
    image_data = encode_image(image_bytes)
    payload = {
        "api_key": API_KEY,
        "images": [image_data],
        "modifiers": ["crops_fast"],
        "plant_language": "en",
        "plant_details": ["common_names", "url", "wiki_description"],
    }
    if mode == "health":
        payload["modifiers"].append("health")
        payload["disease_details"] = ["cause", "description", "treatment"]

    response = requests.post(endpoint, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"API Error {response.status_code}: {response.text}")
        return None

# Upload section
uploaded_file = st.file_uploader("Upload an image of your plant", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="📷 Uploaded Image", use_column_width=True)

    col1, col2 = st.columns(2)
    analyze_id = col1.button("🔍 Identify Plant")
    analyze_health = col2.button("🩺 Health Assessment")

    # Use base64 image string as unique key for vector_db
    image_bytes = uploaded_file.read()
    image_key = encode_image(image_bytes)

    if analyze_id:
        with st.spinner("Identifying plant... please wait."):
            result = call_plant_api(image_bytes, IDENTIFY_API_URL, mode="identify")

        if result:
            # Store identification result in vector_db
            if image_key not in vector_db:
                vector_db[image_key] = {}
            vector_db[image_key]['identification'] = result
            save_vector_db(vector_db)  # Save after update

            st.subheader("🪴 Identified Plant:")
            plant_name = "Unknown"
            if "suggestions" in result and result["suggestions"]:
                suggestion = result["suggestions"][0]
                plant_name = suggestion.get("plant_name", "Unknown")
                probability = suggestion.get("probability", 0)
                common_names = ", ".join(suggestion.get("plant_details", {}).get("common_names", []))
                st.markdown(f"**Scientific Name:** *{plant_name}*")
                st.markdown(f"**Common Names:** {common_names if common_names else 'N/A'}")
                st.markdown(f"**Confidence:** {round(probability * 100, 2)}%")
                wiki = suggestion.get("plant_details", {}).get("wiki_description", {}).get("value", "")
                if wiki:
                    st.markdown(f"**Info:** {wiki}")
            else:
                st.markdown(f"**Scientific Name:** *{plant_name}*")
                st.markdown("No plant identification details found.")

    if analyze_health:
        with st.spinner("Assessing health... please wait."):
            result = call_plant_api(image_bytes, HEALTH_API_URL, mode="health")

        if result:
            # Store health assessment result in vector_db
            if image_key not in vector_db:
                vector_db[image_key] = {}
            vector_db[image_key]['health_assessment'] = result
            save_vector_db(vector_db)  # Save after update

            # 🏷️ Plant Identification
            st.subheader("🪴 Identified Plant:")
            plant_name = "Unknown"
            if "suggestions" in result and result["suggestions"]:
                suggestion = result["suggestions"][0]
                plant_name = suggestion.get("plant_name", "Unknown")
                probability = suggestion.get("probability", 0)
                common_names = ", ".join(suggestion.get("plant_details", {}).get("common_names", []))
                st.markdown(f"**Scientific Name:** *{plant_name}*")
                st.markdown(f"**Common Names:** {common_names if common_names else 'N/A'}")
                st.markdown(f"**Confidence:** {round(probability * 100, 2)}%")
                wiki = suggestion.get("plant_details", {}).get("wiki_description", {}).get("value", "")
                if wiki:
                    st.markdown(f"**Info:** {wiki}")
            else:
                st.markdown(f"**Scientific Name:** *{plant_name}*")
                st.markdown("No plant identification details found.")

            # 🧪 Health Assessment
            health = result.get("health_assessment", {})
            diseases = health.get("diseases", [])

            st.subheader("🩺 Health Assessment:")

            if not diseases:
                st.success("✅ No diseases detected. Your plant appears healthy!")
            else:
                for disease in diseases:
                    name = disease.get("name", "Unknown")
                    confidence = disease.get("probability", 0)
                    st.warning(f"**⚠️ Disease:** {name} ({round(confidence * 100, 2)}% confidence)")
                    st.markdown(f"- **Cause:** {disease.get('cause', 'N/A')}")
                    st.markdown(f"- **Description:** {disease.get('description', 'N/A')}")
                    st.markdown(f"- **Treatment:** {disease.get('treatment', 'N/A')}")
                    st.markdown("---")

    # Optionally, display stored results for the current image
    if image_key in vector_db:
        st.markdown("### 🗄️ Stored Results for This Image")
        if 'identification' in vector_db[image_key]:
            st.markdown("- **Identification:** Saved")
        if 'health_assessment' in vector_db[image_key]:
            st.markdown("- **Health Assessment:** Saved")