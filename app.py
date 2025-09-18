import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.title("PDF Structure Extraction with Gemini API")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
prompt = st.text_area(
    "Custom extraction prompt (or use default):",
    value="Extract the PDF as structured JSON with pages, sections, sub-sections, paragraphs, tables, and charts. Output only valid JSON."
)

def analyze_pdf_with_gemini(api_key, pdf_bytes, prompt):
    client = genai.Client(api_key=api_key)

    # Save PDF bytes into a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name

    # Upload the temp file
    uploaded = client.files.upload(
        file=tmp_file_path,
        config=dict(mime_type="application/pdf")
    )

    # Ask Gemini to process it
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[uploaded, prompt]
    )

    return response.text


if uploaded_file:
    with st.spinner("Uploading and analyzing PDF..."):
        pdf_bytes = uploaded_file.read()
        try:
            result = analyze_pdf_with_gemini(API_KEY, pdf_bytes, prompt)
            st.success("Extraction complete!")
            st.json(result)
        except Exception as e:
            st.error(f"Error: {str(e)}")
