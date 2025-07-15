import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import vision
from google.api_core.client_options import ClientOptions
from PIL import Image
import io

# Set your Google Cloud API Key
API_KEY = "AIzaSyBdKgU7oxnyDqoYx9x6qaWyPkIZzLAyS1c"
client_options = ClientOptions(api_key=API_KEY)
client = vision.ImageAnnotatorClient(client_options=client_options)

st.set_page_config(page_title="Picklist OCR App", layout="wide")
st.title("📦 Picklist OCR App")
st.caption("Capture or upload a picklist photo. Detect handwritten qty & ✓/✗, then download Excel.")

# Upload or capture image
option = st.radio("📸 Capture or 📂 Upload Pick List", ("Capture picklist using mobile camera", "Upload picklist photo"))

if option == "Capture picklist using mobile camera":
    img_file = st.camera_input("Take a photo of the picklist")
else:
    img_file = st.file_uploader("Or upload picklist photo", type=["jpg", "jpeg", "png"])

if img_file is not None:
    st.image(img_file, caption="Selected Picklist", use_container_width=True)
    
    image = Image.open(img_file)

    # ✅ Convert to RGB if image has transparency or is palette-based
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    content = img_byte_arr.getvalue()

    vision_img = vision.Image(content=content)
    response = client.document_text_detection(image=vision_img)
    texts = response.text_annotations

    if not texts:
        st.error("No text detected. Please try a clearer image.")
    else:
        st.success("Text detected successfully!")
        detected_text = texts[0].description
        st.text_area("Detected Text", detected_text, height=300)

        # Dummy logic to convert text into DataFrame (customize as needed)
        data = []
        lines = detected_text.split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                item = " ".join(parts[:-1])
                qty = parts[-1]
                data.append({"Item": item, "Quantity": qty})

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        # Download Excel
        excel_bytes = io.BytesIO()
        df.to_excel(excel_bytes, index=False)
        st.download_button(
            "📥 Download Excel", 
            data=excel_bytes.getvalue(), 
            file_name="picklist.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
