import os
import whisper
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
import json
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import base64

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Load Whisper
whisper_model = whisper.load_model("small")

# Load or initialize saved recipes
def load_saved_recipes():
    if os.path.exists("saved_recipes.json"):
        with open("saved_recipes.json", "r") as file:
            return json.load(file)
    return []

def save_recipe(recipe):
    saved_recipes = load_saved_recipes()
    saved_recipes.append(recipe)
    with open("saved_recipes.json", "w") as file:
        json.dump(saved_recipes, file)

# Set background image
def set_background_image(image_path):
    with open(image_path, "rb") as f:
        img_data = f.read()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{base64.b64encode(img_data).decode()});
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Streamlit UI
st.set_page_config(page_title="Voice & Text-Based Recipe Generator 🍳", layout="wide")

# Set background image (replace 'background.jpg' with your image file)
set_background_image("background.jpg")

# Main title and description
st.title("Voice & Text-Based Recipe Generator 🍳")
st.subheader("Enter, speak, or upload your ingredients, and get a delicious recipe!")

# Sidebar for dietary preferences
st.sidebar.header("Dietary Preferences")
dietary_preference = st.sidebar.selectbox(
    "Select Dietary Preference",
    ["None", "Vegetarian", "Vegan", "Gluten-Free", "Low-Carb", "Keto"]
)

# User input: Text, Audio Upload, or Voice Recording
st.markdown("### 📝 Enter Ingredients (Text) or Use Audio 🎙️")

# Text input
text_ingredients = st.text_area("Enter ingredients manually (comma-separated):")

# Audio upload
audio_file = st.file_uploader("Upload audio (MP3/WAV)", type=["wav", "mp3"])

# Voice recording
st.markdown("### 🎤 Or Record Your Voice")
voice_recording = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹️ Stop Recording", key="recorder")

# Process audio if uploaded or recorded
transcribed_text = ""
if audio_file or voice_recording:
    with st.spinner("Transcribing your ingredients..."):
        try:
            if audio_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_file.read())
                    tmp_file_path = tmp_file.name
            else:
                tmp_file_path = "recorded_audio.wav"
                with open(tmp_file_path, "wb") as f:
                    f.write(voice_recording["bytes"])

            # Transcribe with Whisper
            transcribed_text = whisper_model.transcribe(tmp_file_path)["text"]
            st.markdown("### 📝 Transcribed Ingredients")
            st.write(transcribed_text)
        except Exception as e:
            st.error(f"Error transcribing audio: {e}")

# Use text input if provided, otherwise use transcribed text
final_ingredients = text_ingredients if text_ingredients else transcribed_text

# Generate recipe if ingredients are available
if final_ingredients:
    with st.spinner("Generating recipe..."):
        try:
            prompt = f"""
            Act as a professional chef. Generate a detailed recipe based on the following ingredients:

            Ingredients: {final_ingredients}

            Dietary Preference: {dietary_preference if dietary_preference != "None" else "None"}

            Provide the recipe in the following format:
            1. Recipe Name
            2. Ingredients (with quantities)
            3. Step-by-Step Instructions
            4. Serving Suggestions
            5. Tips or Variations
            """
            
            response = model.generate_content(prompt)
            recipe = response.text

            # Display recipe
            st.write("---")
            st.markdown("### 🍴 Generated Recipe")
            st.markdown(recipe)

            # Save recipe option
            if st.button("💾 Save Recipe"):
                save_recipe(recipe)
                st.success("Recipe saved successfully!")
        except Exception as e:
            st.error(f"Error generating recipe: {e}")

# View saved recipes
st.write("---")
st.markdown("### 📚 Saved Recipes")
saved_recipes = load_saved_recipes()
if saved_recipes:
    for i, recipe in enumerate(saved_recipes, 1):
        st.markdown(f"#### Recipe {i}")
        st.markdown(recipe)
        st.write("---")
else:
    st.write("No recipes saved yet.")