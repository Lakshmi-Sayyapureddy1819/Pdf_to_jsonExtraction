import streamlit as st
import pdfplumber
import os
from dotenv import load_dotenv

from utils import analyze_pdf_with_gemini

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

st.title("PDF Structure Extraction with Gemini API")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
prompt = st.text_area(
    "Custom extraction prompt (or use default):",
    value="Extract the PDF as structured JSON with pages, sections, sub-sections, paragraphs, tables, and charts. Output only valid JSON."
)

if uploaded_file:
    with st.spinner("Uploading and analyzing PDF..."):
        pdf_bytes = uploaded_file.read()
        try:
            # Send to Gemini API for processing
            result = analyze_pdf_with_gemini(API_KEY, pdf_bytes, prompt)
            st.success("Extraction complete!")
            st.json(result)
        except Exception as e:
            st.error(f"Error: {str(e)}")
