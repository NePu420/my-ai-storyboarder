import streamlit as st
import json
import os
from google import genai
from google.genai import types

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AI Video Storyboarder", layout="wide")

st.title("🎬 AI Video Storyboarder (Gemini 1.5 Flash)")
st.markdown("### Turn YouTube Scripts into Cinematic Scenes")

# --- AUTHENTICATION (SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# --- MAIN INPUT ---
script_input = st.text_area("Paste your YouTube Script here:", height=200)

# --- THE MASTER PROMPT ---
SYSTEM_PROMPT = """
ROLE:
You are a professional film director, cinematographer, and storyboard artist.
Your job is to convert a YouTube script into cinematic visual scenes and generate hyper-detailed image generation prompts for each scene.

TASK:
1. Break the script into scenes of 2–4 seconds each.
2. Each scene should represent one clear visual moment.
3. For every scene, generate a rich, cinematic, production-level image prompt that can be directly used in AI image generators.

THINK LIKE A FILMMAKER:
- Decide what the viewer actually sees
- Add camera language (shot type, angle, lens)
- Add lighting, environment, emotion, and color palette
- Never summarize. Always visualize.

IMAGE PROMPT WRITING RULES:
Each Image Prompt MUST include:
1. Subject (Who/what is in frame)
2. Environment (Location, props, background details)
3. Action (What is happening)
4. Camera (Shot type: wide/close-up, Angle: low/high, Lens: 35mm/85mm)
5. Lighting (Golden hour, neon, rim light, volumetric, shadows)
6. Mood (Emotional tone)
7. Color Palette (Specific colors)
8. Style (Photorealistic, cinematic, film still, 8k)

PROMPT STRUCTURE (MANDATORY):
"Cinematic [shot type] of [subject + action], in [environment], [lighting details], [mood], [camera angle + lens], [color palette], ultra realistic, film still, high detail textures, depth of field, volumetric light, professional cinematography, 8k"

OUTPUT FORMAT (JSON ONLY):
Return results in a valid JSON object. Do not use Markdown. Use this exact structure:
{
  "scenes": [
    {
      "scene_number": 1,
      "timestamp": "00:00-00:04",
      "script_line": "The exact line from the script",
      "visual_description": "Director's notes on the visual (non-prompt)",
      "image_prompt": "Cinematic [shot type]..."
    }
  ]
}
"""

# --- FUNCTION: GENERATE SCENES (GEMINI TEXT) ---
def get_scenes_gemini(script, api_key):
    if not api_key:
        st.error("Gemini API Key is missing!")
        return None
    
    client = genai.Client(api_key=api_key)
    try:
        # UPDATED: Switched to gemini-1.5-flash (Standard Free Tier)
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=[SYSTEM_PROMPT, f"SCRIPT:\n{script}"],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error generating scenes: {e}")
        return None

# --- FUNCTION: GENERATE IMAGE (GEMINI IMAGE) ---
def generate_image_gemini(prompt, api_key):
    if not api_key:
        st.error("Gemini API Key is missing!")
        return None
    
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
        return response.generated_images[0].image
    except Exception as e:
        st.warning(f"Image gen failed: {e}")
        st.info("Note: If Image Gen fails, your API key might not have access to Imagen 3 yet. You may need to enable billing on Google Cloud.")
        return None

# --- APP LOGIC ---
if st.button("🚀 Analyze Script & Generate Scenes"):
    if not script_input:
        st.error("Please enter a script!")
    else:
        with st.spinner("Director (Gemini 1.5) is planning the shots..."):
            scene_data = get_scenes_gemini(script_input, gemini_api_key)
        
        if scene_data:
            st.session_state['scene_data'] = scene_data
            st.success(f"Generated {len(scene_data['scenes'])} scenes!")

# --- DISPLAY & IMAGE GENERATION ---
if 'scene_data' in st.session_state:
    scenes = st.session_state['scene_data']['scenes']
    
    st.divider()
    
    for scene in scenes:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader(f"Scene {scene['scene_number']}")
            st.caption(f"⏱ {scene['timestamp']}")
            
            # Show script line
            script_text = scene.get('script_line', scene.get('visual_description', ''))
            st.markdown(f"**Script:** _{script_text}_")
            
            btn_key = f"btn_{scene['scene_number']}"
            if st.button(f"🎨 Generate Image {scene['scene_number']}", key=btn_key):
                with st.spinner("Painting..."):
                    img = generate_image_gemini(scene['image_prompt'], gemini_api_key)
                    if img:
                        image_bytes = img.image_bytes
                        st.image(image_bytes, caption=scene['image_prompt'])
        
        with col2:
            st.text_area("Prompt (Editable)", scene['image_prompt'], height=200, key=f"txt_{scene['scene_number']}")

        st.divider()
