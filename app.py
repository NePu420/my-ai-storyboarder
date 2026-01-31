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

# --- AUTHENTICATION (SECRETS) ---
if "OPENAI_API_KEY" in st.secrets:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = st.sidebar.text_input("Google Gemini API Key", type="password")

# --- MAIN INPUT ---
script_input = st.text_area("Paste your YouTube Script here:", height=200)

# --- THE MASTER PROMPT (UPDATED WITH YOUR RULES) ---
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

EXAMPLE:
Input: "I woke up at 5am and the city was still asleep"
Output Prompt: "Cinematic close-up of a young man opening his eyes in a dim bedroom, soft blue pre-dawn light through curtains, alarm clock showing 5:00 AM glowing red, dust particles in air, quiet atmosphere, side angle 50mm lens, cold blue and grey palette, shallow depth of field, film still, ultra detailed, 8k"

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

# --- FUNCTION: GENERATE SCENES (OPENAI) ---
def get_scenes(script, api_key):
    if not api_key:
        st.error("OpenAI API Key is missing!")
        return None
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
        return None

# --- APP LOGIC ---
if st.button("🚀 Analyze Script & Generate Scenes"):
    if not script_input:
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
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader(f"Scene {scene['scene_number']}")
            st.caption(f"⏱ {scene['timestamp']}")
            
            # Show the script line if available, otherwise description
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
