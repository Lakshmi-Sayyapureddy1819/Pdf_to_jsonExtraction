import streamlit as st
import os
import tempfile
import re
import json
import json5   # install via `pip install json5`
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


# ---- Utility: Clean Gemini output into parseable JSON ----
def clean_json_response(text: str) -> str:
    """Remove markdown fences and common JSON-breaking issues."""
    # Remove markdown fences like ```json ... ```
    cleaned = re.sub(r"^```(json)?", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE)

    # Remove trailing commas inside objects/arrays
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Ensure property names are quoted
    cleaned = re.sub(r"([{,]\s*)([A-Za-z0-9_]+)\s*:", r'\1"\2":', cleaned)

    return cleaned.strip()


# ---- Function: Analyze PDF with Gemini ----
def analyze_pdf_with_gemini(api_key, pdf_bytes, prompt: str) -> str:
    client = genai.Client(api_key=api_key)

    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_file_path = tmp_file.name

    # Upload to Gemini
    uploaded = client.files.upload(
        file=tmp_file_path,
        config=dict(mime_type="application/pdf")
    )

    # Ask Gemini
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[uploaded, prompt]
    )

    return response.text


# ---- Streamlit UI ----
st.title("📄 PDF Structure Extraction with Gemini API")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

prompt = st.text_area(
    "Custom extraction prompt (or use default):",
    value=(
        "Extract the PDF as structured JSON with pages, sections, sub-sections, "
        "paragraphs, tables, and charts. Output ONLY valid JSON. "
        "Do not include markdown or code fences."
    )
)

if uploaded_file:
    with st.spinner("Uploading and analyzing PDF..."):
        pdf_bytes = uploaded_file.read()
        try:
            result_text = analyze_pdf_with_gemini(API_KEY, pdf_bytes, prompt)
            cleaned_json = clean_json_response(result_text)

            try:
                # First try strict JSON
                parsed = json.loads(cleaned_json)
                st.success("✅ Extraction complete (strict JSON)!")
                st.json(parsed)

            except json.JSONDecodeError:
                try:
                    # Fall back to json5 for lenient parsing
                    parsed = json5.loads(cleaned_json)
                    st.warning("⚠️ Extracted using relaxed JSON5 parsing.")
                    st.json(parsed)
                except Exception as e:
                    st.error(f"⚠️ Still invalid JSON: {e}")
                    st.text_area("Raw Gemini Output", result_text, height=400)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
