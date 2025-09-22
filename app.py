import streamlit as st
import os
import tempfile
import re
import json
import json5   # pip install json5
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


def extract_json_block(text: str) -> str:
    """Extract the largest JSON-like block from text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def safe_parse_json(text: str):
    """
    Try to parse Gemini output into JSON.
    Cleans up common issues like extra braces, dangling commas, unquoted keys.
    """
    # First isolate possible JSON block
    cleaned = extract_json_block(text)
    cleaned = clean_json_response(cleaned)

    # Fix double closing braces like "}}"
    cleaned = re.sub(r"\}\s*\}", "}", cleaned)

    # Fix trailing commas again
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Remove unexpected characters before first '{'
    if "{" in cleaned:
        cleaned = cleaned[cleaned.index("{"):]

    # Try JSON strict first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try JSON5 (lenient)
    try:
        return json5.loads(cleaned)
    except Exception:
        pass

    # Last resort: truncate until last complete brace
    last_curly = cleaned.rfind("}")
    if last_curly != -1:
        try:
            return json.loads(cleaned[: last_curly + 1])
        except Exception:
            pass

    raise ValueError("Could not repair JSON")


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
        "You are a JSON API. Extract the PDF into structured JSON with keys: "
        "pages, sections, sub_sections, paragraphs, tables, charts. "
        "Respond with ONLY valid JSON. "
        "Do not include explanations, markdown, or code fences. "
        "Start with '{' and end with '}'."
    )
)

if uploaded_file:
    with st.spinner("Uploading and analyzing PDF..."):
        pdf_bytes = uploaded_file.read()
        try:
            result_text = analyze_pdf_with_gemini(API_KEY, pdf_bytes, prompt)

            try:
                parsed = safe_parse_json(result_text)
                st.success("✅ Extraction complete!")
                st.json(parsed)

            except Exception as e:
                st.error(f"⚠️ Still invalid JSON after repair: {e}")
                st.text_area("Raw Gemini Output", result_text, height=400)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
