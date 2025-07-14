import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
import io
import cv2
import numpy as np
import pandas as pd
import json

# --- App Title ---
st.set_page_config(page_title="📦 Picklist OCR App", layout="centered")
st.title("📦 Picklist OCR App")
st.write("Capture or upload a picklist photo. Detect handwritten qty & ✓/✗, then download Excel.")

# --- Load Google Vision API Credentials from Streamlit Secrets ---
creds_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
credentials = service_account.Credentials.from_service_account_info(creds_dict)
client = vision.ImageAnnotatorClient(credentials=credentials)

# --- User Input ---
st.header("📸 Capture or 📂 Upload Pick List")
uploaded_image = st.camera_input("Capture picklist using mobile camera")
uploaded_file = st.file_uploader("Or upload picklist photo", type=["jpg", "jpeg", "png"])

image = None
if uploaded_image:
    image = Image.open(uploaded_image)
elif uploaded_file:
    image = Image.open(uploaded_file)

if image:
    st.image(image, caption="Selected Picklist", use_container_width=True)

    # --- Ensure RGB Mode ---
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    # --- Save to BytesIO safely ---
    img_bytes = io.BytesIO()
    try:
        # Fallback to PNG if format unknown or save fails
        save_format = image.format if image.format in ["JPEG", "PNG"] else "PNG"
        image.save(img_bytes, format=save_format)
    except Exception as e:
        st.warning(f"Retrying save as PNG due to error: {e}")
        image.save(img_bytes, format="PNG")
    content = img_bytes.getvalue()

    # --- Google Vision OCR ---
    st.write("🔍 Processing image with Google Vision OCR...")
    vision_img = vision.Image(content=content)
    response = client.document_text_detection(image=vision_img)
    full_text = response.full_text_annotation.text if response.full_text_annotation.text else ""
    st.text_area("📝 Detected Text", full_text, height=200)

    # --- Tick/Cross Detection (OpenCV) ---
    st.write("✅ Detecting ✓ / ✗ marks...")
    image_np = np.array(image)
    try:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    except Exception as e:
        st.error(f"OpenCV error: {e}")
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    marks = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 100 < area < 1000:  # Adjust these values for your tick/cross size
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) > 2:
                marks.append("✓")
            else:
                marks.append("✗")

    st.write("Detected marks:", marks)

    # --- Dummy DataFrame for Demo ---
    df = pd.DataFrame({
        "Item No": ["1001", "1002", "1003"],
        "Qty Ordered": [10, 5, 8],
        "Qty Picked": [10 if "✓" in marks else 0 for _ in range(3)]
    })

    st.dataframe(df)

    # --- Download Excel ---
    excel_bytes = io.BytesIO()
    df.to_excel(excel_bytes, index=False)
    st.download_button(
        label="📥 Download Excel",
        data=excel_bytes.getvalue(),
        file_name="picklist_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("📸 Capture or 📂 Upload a picklist photo to get started.")
