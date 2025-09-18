import os
from google import genai

def analyze_pdf_with_gemini(api_key, pdf_bytes, prompt):
    client = genai.Client(api_key=api_key)
    uploaded = client.files.upload(
        file=pdf_bytes,
        config=dict(mime_type="application/pdf")
    )
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=[uploaded, prompt]
    )
    return response.text
