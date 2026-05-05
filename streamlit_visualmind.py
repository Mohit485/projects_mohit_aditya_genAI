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

st.caption("Stable Diffusion + BLIP running on kaggle GPU")

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

# TAB -1 Text to Image
with tab1:
    st.header("Generate Images from Text ")

    prompt= st.text_area(
        "Your Prompt",
        placeholder= " Example: a majestic dragon flying over a medieval castle at sunset",
        height= 100 
    ) 
    st.divider()

    #generate button
    generate_but= st.button(
        "Generate Image",
        type="primary",
        use_container_width= True
    )

    if generate_but:
        if not check_APIurl():
            pass
    elif not prompt.strip():
        st.warning("Please enter a prompt before Generating!")

    else:
        with st.spinner(f"Generating {batch_size} image(s) with {steps} steps... (~15 sec)"):
            try:
                response= requests.post(f"{api_url}/Generate",
                data= {
                    "prompt": prompt,
                    "style": style,
                    "steps": steps,
                    "batch": batch_size

                },
                # data={} = sends as HTML form data
                timeout= 180
                )
                if response.status_code== 200:
                    result= response.json()   # .json() = parse the response body as JSON into a Python dict
                    images_b64=result["images"]  # A list of base64 strings, one per generated image
                    prompt_used= result["prompt_used"] # The full prompt including style text — good to show the user
                    st.success(f"Generated {len(images_b64)} images")
                    st.caption(f"prompt sent to model:{prompt_used}")
                    

                    #display images side by side when batch = 2
                    img_cols= st.columns(len(images_b64))



                    for idx, img_b64 in enumerate(images_b64):
                        image_bytes= base64.b64decode(img_b64)
                        pil_img= Image.open(io.BytesIO(image_bytes))

                        with img_cols[idx]:
                            st.image(pil_img, caption=f"Image{idx+1}", use_container_width= True)
                            if st.button(f"save {idx+1} to gallery", key=f"save_t2i_idx"):
                                st.session_state.gallery.apppend({
                                    "image": img_b64,
                                    "prompt": prompt,
                                    "style": style,
                                    "tab": "Text to Image"
                                })
                                st.success("Saved to Gallery")

                else: 
                    st.error(f"API returned error {response.status_code}")
                    st.code(response.text)

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Double-check your ngrok URL in the sidebar.")
            except requests.exceptions.Timeout:
                st.error("Request timed out. The model might still be warming up — try again in 30 seconds.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")