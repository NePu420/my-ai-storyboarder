import streamlit as st
import json
import os
from openai import OpenAI
from google import genai
from google.genai import types

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Storyboarder", layout="wide")

st.title("🎬 AI Video Storyboarder")
st.markdown("### Turn YouTube Scripts into Cinematic Scenes")

# --- SIDEBAR: API KEYS ---
with st.sidebar:
    st.header("🔑 API Keys")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    gemini_api_key = st.text_input("Google Gemini API Key", type="password")
    st.info("Paste your keys here. They are not saved permanently.")

# --- MAIN INPUT ---
script_input = st.text_area("Paste your YouTube Script here:", height=200)

# --- THE MASTER PROMPT ---
SYSTEM_PROMPT = """
You are a professional film director. 
TASK: Break the script into scenes (2-4 seconds each).
OUTPUT: Return valid JSON ONLY.
Structure:
{
  "scenes": [
    {
      "scene_number": 1,
      "timestamp": "00:00-00:04",
      "visual_description": "Brief description of the visual",
      "image_prompt": "Cinematic [shot type] of [subject], [lighting], [mood], [style], 8k, ultra realistic"
    }
  ]
}
"""

# --- FUNCTION: GENERATE SCENES (OPENAI) ---
def get_scenes(script, api_key):
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": script}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating scenes: {e}")
        return None

# --- FUNCTION: GENERATE IMAGE (GEMINI) ---
def generate_image_gemini(prompt, api_key):
    client = genai.Client(api_key=api_key)
    try:
        # Using Imagen 3 model
        response = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
            )
        )
        # Return the first generated image
        return response.generated_images[0].image
    except Exception as e:
        st.warning(f"Image gen failed: {e}")
        return None

# --- APP LOGIC ---
if st.button("🚀 Analyze Script & Generate Scenes"):
    if not openai_api_key or not gemini_api_key:
        st.error("Please enter both API keys in the sidebar!")
    elif not script_input:
        st.error("Please enter a script!")
    else:
        with st.spinner("Director is planning the shots (OpenAI)..."):
            scene_data = get_scenes(script_input, openai_api_key)
        
        if scene_data:
            st.session_state['scene_data'] = scene_data
            st.success(f"Generated {len(scene_data['scenes'])} scenes!")

# --- DISPLAY & IMAGE GENERATION ---
if 'scene_data' in st.session_state:
    scenes = st.session_state['scene_data']['scenes']
    
    st.divider()
    
    for scene in scenes:
        # Create a 2-column layout for each scene
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader(f"Scene {scene['scene_number']}")
            st.caption(f"⏱ {scene['timestamp']}")
            st.markdown(f"**Visual:** {scene['visual_description']}")
            
            # Button to generate image for this specific scene
            if st.button(f"🎨 Generate Image {scene['scene_number']}", key=f"btn_{scene['scene_number']}"):
                with st.spinner("Painting..."):
                    img = generate_image_gemini(scene['image_prompt'], gemini_api_key)
                    if img:
                        # Convert to PIL Image to display
                        from PIL import Image
                        import io
                        # Gemini returns bytes, Streamlit needs PIL or bytes
                        # The SDK usually returns a specific object, we need to handle bytes
                        image_bytes = img.image_bytes
                        st.image(image_bytes, caption=scene['image_prompt'])
        
        with col2:
            st.text_area("Prompt (Editable)", scene['image_prompt'], height=150, key=f"txt_{scene['scene_number']}")

        st.divider()