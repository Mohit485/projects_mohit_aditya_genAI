import streamlit as st
import requests 
import base64
from PIL import Image
import io

# Page Setup
st.set_page_config(
    page_title= "VisualMind",
    layout= "wide"
)

#Session State Setup

#st.session_state is a dictionary that PERSISTS across reruns — it's the only "memory" Streamlit has.
if "gallery" not in st.session_state:
    st.session_state.gallery = []
    # gallery = list of dicts, each with: image (base64), prompt, style

if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = ""
#Sidebar - Settings bar 
with st.sidebar:
    st.title(" Settings")
    api_url= st.text_input(
        "Kaggle API URL",
        placeholder= "https://xxxx.ngrok-free.app",
        help= " Paste the URL from the Kaggle Notebook"
    )

    st.divider()

    st.subheader("Style Preset")
    style= st.selectbox(   #st.selectbox= drop down menu
        "Choose Style (Art)", 
        ["Realistic", "Anime", "Oil Painting", "Watercolor", "Cyberpunk", "Sketch"]
    )

    st.subheader("Generation Settings")
    steps= st.slider(
        "Quality Steps",
        min_value= 10,
        max_value= 50,
        value= 20,
        help= "more quality steps, better quality" 
    )

    batch_size= st.slider(
        "Images to Generate",
        min_value= 1,
        max_value= 2,
        value= 1
    )

    st.divider()

    st.caption(f" Gallery: {len(st.session_state.gallery)} image(s) saved.")

    if st.button("Clear Gallery ", use_container_width= True):
        st.session_state.gallery= [] #empty gallery
        st.rerun()


# main area

st.title("AI Creative Studio")

st.caption("Powered by SDXL 1.0 + BLIP · Running on Kaggle GPU")

# create tabs
tab1, tab2,tab3,tab4= st.tabs(
    ["Text to Image Generation",
     "Style Transfer",
     " Image Analysis",
     "Gallery"]
)
#check API URL
def check_APIurl():
    if not api_url:
        st.warning("Please enter the API URL in the Sidebar")
        return False
    return True


#tab 1 - text to image generation
with tab1:
    st.header("Generate Images from Text")

    # Quick example buttons — no st.rerun(), just session state
    st.caption(" Quick examples:")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(" Sunset scene", use_container_width=True):
            st.session_state.quick_prompt = (
                "a beautiful sunset over snow-capped mountains, "
                "golden hour lighting, dramatic sky, reflections on a lake"
            )
    with col2:
        if st.button(" Cyberpunk city", use_container_width=True):
            st.session_state.quick_prompt = (
                "a futuristic cyberpunk city at night, neon signs, "
                "rain on streets, crowds of people, towering skyscrapers"
            )
    with col3:
        if st.button(" Fantasy forest", use_container_width=True):
            st.session_state.quick_prompt = (
                "a magical enchanted forest at dusk, glowing flowers, "
                "fireflies, ancient trees, misty atmosphere"
            )
    
    prompt = st.text_area(
        "Your prompt",
        value=st.session_state.quick_prompt,
        placeholder="Example: a majestic dragon flying over a medieval castle at sunset",
        height=100
    )

    st.divider()

    if st.button(" Generate Image", type="primary", use_container_width=True):
        
        # Check 1: API URL
        if not api_url:
            st.warning("Enter your Kaggle API URL in the sidebar first.")
        
        # Check 2: Prompt
        elif not prompt.strip():
            st.warning("Please type a prompt before generating.")
        
        # All good — make the request
        else:
            with st.spinner(f"Generating {batch_size} image(s)... this takes ~15 to 30 seconds"):
                try:
                    response = requests.post(
                        f"{api_url}/generate",
                        data={
                            "prompt": prompt,
                            "style": style,
                            "steps": steps,
                            "batch": batch_size,
                        },
                        timeout=180
                    )

                    if response.status_code == 200:
                        result = response.json()
                        images_b64 = result["images"]
                        prompt_used = result["prompt_used"]

                        st.success(f" Done! Prompt used: _{prompt_used}_")
                        st.caption(f"Full prompt sent to SDXL: _{prompt_used}_")
                        img_cols = st.columns(len(images_b64))
                        for idx, img_b64 in enumerate(images_b64):
                            img_bytes = base64.b64decode(img_b64)
                            pil_img = Image.open(io.BytesIO(img_bytes))
                            with img_cols[idx]:
                                st.image(pil_img, caption=f"Image {idx+1}", use_container_width=True)
                                if st.button(f"💾 Save #{idx+1}", key=f"save_{idx}"):
                                    st.session_state.gallery.append({
                                        "image": img_b64,
                                        "prompt": prompt,
                                        "style": style,
                                        "tab": "Text to Image"
                                    })
                                    st.success("Saved!")
                    else:
                        st.error(f"API error {response.status_code}: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error(" Cannot connect. Check your ngrok URL.")
                except requests.exceptions.Timeout:
                    st.error(" Timed out after 180s. Try again.")
                except Exception as e:
                    st.error(f" Error: {e}")

# Tab - 2 - Image to image
with tab2:
    st.header("Style Transfer")
    st.write("Upload a photo, describe a style, SDXL will repaint it at 1024×1024")
    col_left, col_right= st.columns(2)
    with col_left:
        uploaded_file= st.file_uploader(
            "Upload your image",
            type= ["jpg", "jpeg", "png"],
            help="Will be resized to 1024×1024 — SDXL's native resolution"
        )
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Original Image", use_container_width= True )

        style_prompt= st.text_area(
            "Describe the art style",
            placeholder= "Transform into a Van Gogh oil painting with swirling brushstrokes and bold colors",
            height= 80,
            key= "i2i_prompt" # key is needed or st will merge both text area of tab 1 and tab2 into one widget
        )
        strength= st.slider(
            "Style Strength",
            min_value= 0.1,
            max_value= 0.95,
            value= 0.7,
            step= 0.05,
            help= "0.1 = barely changes original. 0.95 = dramatic transformation."
        )
        if strength < 0.4:
            st.caption("🔵 Subtle — light style touch, structure preserved")
        elif strength < 0.7:
            st.caption("🟡 Moderate — clear style change, composition preserved")
        else:
            st.caption("🔴 Strong — heavy transformation, may look very different")

        transfer_clicked= st.button("Generate", type= "primary", use_container_width=True)
    if transfer_clicked:
        if not check_APIurl:
            pass
        elif uploaded_file is None:
            st.warning("Please upload an image first")
        elif not style_prompt.strip():
            st.warning("Please Describe the style you want")
        else:
            with st.spinner("Generating.....(~25 seconds)"):
                try:
                    response= requests.post(
                        f"{api_url}/img2img",
                        files= {
                            "file": ("image.png", uploaded_file.getvalue(), "image/png")
                        },
                        # files= sends the image as a multipart upload
                        # Format: {"field_name": (filename, bytes, content_type)}
                        # uploaded_file.getvalue() reads all bytes from the upload)
                        data= {
                            "prompt": style_prompt,
                            "strength": strength
                        },
                        timeout= 300
                    )
                    if response.status_code== 200:
                        result= response.json()
                        if "error" in result:
                            st.error(f"Server error: {result['error']}")
                        else:
                            img_bytes = base64.b64decode(result["image"])
                            result_img = Image.open(io.BytesIO(img_bytes))

                            with col_right:
                                st.subheader("Result")
                                st.image(result_img, use_container_width= True)
                                if st.button("Save to Gallery", key= "save_i2i"):
                                    st.session_state.gallery.append({
                                        "image": result["image"],
                                        "prompt": style_prompt,
                                        "style": f"Style Transfer · strength {strength}",
                                        "tab": "Style Transfer"
                                    })
                                    st.success("Saved!")
                    else:
                        st.error(f"API error {response.status_code}: {response.text}")           
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect. Check ngrok URL.")
                except requests.exceptions.Timeout:
                    st.error("❌ Timed out. Try again.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

#BLIP Captioning
with tab3:
    st.header("Image Analysis")
    st.write("Upload an image  — BLIP will describe it, then we suggest creative prompts.")
    col_img, col_results= st.columns(2)
    with col_img:
        analysis_file= st.file_uploader(
            "Upload image to analyze",
            type= ["jpg", "jpeg", "png"],
            key=" analysis_uploader"
        )
        if analysis_file is not None:
            st.image(analysis_file, use_container_width= True)
        analyze_clicked=st.button("Analyze Image", type= "primary", use_container_width=True)
    if analyze_clicked:
        if not check_APIurl():
            pass
        elif analysis_file is None:
            st.warning("Please upload an image first")
        else:
            with st.spinner("Analyzing....."):
                try:
                    response= requests.post(
                        f"{api_url}/caption",
                        files={
                            "file": ("image.png", analysis_file.getvalue(), "image/png")
                        },
                        timeout= 60
                    )
                    if response.status_code== 200:
                        result= response.json()
                        if "error" in result:
                            st.error(f"Server error: {result['error']}")
                        else:
                            caption= result["caption"]

                            with col_results:
                                st.subheader("BLIP Caption")
                                st.info(f'"{caption}"')
                                st.subheader("Creative Prompt Suggestions")
                                st.write("Click any to load it into Tab 1:")
                                # Build style variations from the caption
                                # Pure Python string formatting — no extra AI needed
                                suggestions = {
                                    " Oil painting version": (
                                        f"{caption}, oil painting, thick brush strokes, "
                                        "impressionist, museum quality, masterpiece"
                                    ),
                                    " Anime version": (
                                        f"{caption}, anime style, vibrant colors, "
                                        "Studio Ghibli, detailed illustration"
                                    ),
                                    " Cyberpunk version": (
                                        f"{caption}, cyberpunk aesthetic, neon lights, "
                                        "futuristic, blade runner style"
                                    ),
                                    " Pencil sketch version": (
                                        f"{caption}, detailed pencil sketch, fine line art, "
                                        "black and white, high contrast"
                                    ),
                                }
                                for label, suggestion_text in suggestions.items():
                                    if st.button(label, key=f"sug_{label}", use_container_width=True):
                                        st.session_state.quick_prompt = suggestion_text
                                        # Store in session state
                                        # When user goes to Tab 1, the text area
                                        # will be pre-filled with this prompt
                                        st.success("Loaded! Switch to 'Text to Image' tab.")
                                        st.code(suggestion_text)
                                        # Show the full prompt so they can also copy manually
                    else:
                        st.error(f"API Error {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect.")
                except requests.exceptions.Timeout:
                    st.error("❌ Timed out.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# Tab 4 - Gallery
with tab4:
    st.header("Saved Gallery")
    if not st.session_state.gallery:
        st.info("No images saved yet, Generate some and click 'Save to gallery'")
    else:
        total= len(st.session_state.gallery)
        st.write(f"{total} image(s) in your gallery")
        st.caption("Gallery resets when you close or refresh the browser tab.")


        # Display in a 3-column grid
        for row_start in range(0, total, 3):
            # range(0, 7, 3) = [0, 3, 6]
            # Processes 3 images at a time — one row per loop

            row_items = st.session_state.gallery[row_start : row_start + 3]
            # List slicing — gets exactly 3 items (or fewer for the last row)

            cols = st.columns(3)
            # Create 3 columns — unused ones are invisible, no harm

            for col_idx, item in enumerate(row_items):
                with cols[col_idx]:
                    img_bytes = base64.b64decode(item["image"])
                    pil_img = Image.open(io.BytesIO(img_bytes))

                    st.image(pil_img, use_container_width=True)
                    st.caption(f"**{item['tab']}**")
                    st.caption(f"Style: {item['style']}")

                    # Truncate long prompts to keep the gallery clean
                    display_prompt = item["prompt"]
                    if len(display_prompt) > 60:
                        display_prompt = display_prompt[:60] + "..."
                    st.caption(f"_{display_prompt}_")


