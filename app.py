"""Simple Streamlit UI for the AI Cover Letter Personalizer (MVP).

Run:
    .venv\\Scripts\\python.exe -m streamlit run app.py
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import streamlit as st

from config import load_settings, project_root
from services import document, gemini, research

st.set_page_config(page_title="Cover Letter Personalizer", layout="centered")
st.title("AI Cover Letter Personalizer")


def sanitize_filename(value: str) -> str:
    value = value.strip().replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇ_\-]+", "", value)
    return value or "output"


def resolve_template(uploaded, fallback_path: str) -> Path | None:
    """Save an uploaded template to temp, else use the fallback path."""
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix != ".docx":
            st.error("The uploaded template must be a .docx file.")
            return None
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        tmp.write(uploaded.getbuffer())
        tmp.close()
        return Path(tmp.name)
    if fallback_path.strip():
        return Path(fallback_path.strip())
    return None


with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input(
        "Gemini API key (optional if set in .env)",
        type="password",
        help="Overrides GEMINI_API_KEY from .env when filled.",
    )
    model_input = st.text_input("Model", value=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

with st.form("generate"):
    company = st.text_input("Company *", placeholder="Invivoo")
    position = st.text_input("Position *", placeholder="AI Engineer")
    website = st.text_input("Company website", placeholder="https://www.invivoo.com")
    linkedin = st.text_input("LinkedIn URL (optional, not scraped in MVP)")
    job_description = st.text_area("Job description (optional)", height=150)
    uploaded_template = st.file_uploader("Template (.docx with placeholders)", type=["docx"])
    template_path_input = st.text_input(
        "…or template path",
        value="templates/ai_engineer_fr.docx",
        help="Used when no file is uploaded above.",
    )
    show_prompt = st.checkbox("Show Gemini prompt before generating", value=False)
    submitted = st.form_submit_button("Generate", type="primary")

if submitted:
    if not company.strip() or not position.strip():
        st.error("Company and position are required.")
        st.stop()

    template_path = resolve_template(uploaded_template, template_path_input)
    if template_path is None:
        st.error("Provide a template: upload a file or set a template path.")
        st.stop()
    if not template_path.is_file():
        st.error(f"Template not found: {template_path}")
        st.stop()
    if not document.template_has_placeholders(template_path):
        st.error("Template must contain [COMPANY_PARAGRAPH_1] and [COMPANY_PARAGRAPH_2].")
        st.stop()

    try:
        if api_key_input.strip():
            os.environ["GEMINI_API_KEY"] = api_key_input.strip()
        settings = load_settings()
        model = model_input.strip() or settings.model
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    with st.spinner("Researching company website..."):
        website_text = research.fetch_website_text(website) if website.strip() else ""
    research_context = research.build_research_context(
        company_name=company.strip(),
        position=position.strip(),
        website_text=website_text,
        website_url=website.strip(),
        linkedin_url=linkedin.strip(),
    )
    if website_text:
        st.caption(f"Collected {len(website_text)} chars of website text.")

    try:
        prompt_template = gemini.load_prompt_template(project_root() / "prompts" / "personalization.txt")
    except OSError as exc:
        st.error(f"Cannot read prompt file: {exc}")
        st.stop()
    prompt = gemini.build_prompt(
        prompt_template,
        company_name=company.strip(),
        position=position.strip(),
        research_context=research_context,
        job_description=job_description.strip(),
    )
    if show_prompt:
        with st.expander("Gemini prompt", expanded=False):
            st.code(prompt)

    try:
        with st.spinner(f"Generating paragraphs with {model}..."):
            paragraphs = gemini.generate_paragraphs(
                api_key=settings.api_key, model=model, prompt=prompt
            )
        document.validate_paragraphs(paragraphs)
    except RuntimeError as exc:
        st.error(f"Generation failed, no letter produced. {exc}")
        st.stop()

    st.subheader("Generated paragraphs")
    st.text_area("Paragraph 1", paragraphs["company_paragraph_1"], height=150)
    st.text_area("Paragraph 2", paragraphs["company_paragraph_2"], height=150)

    filename = (
        f"{sanitize_filename(company)}_{sanitize_filename(position)}_Hazem_Ben_Alaya.docx"
    )
    output_path = project_root() / "output" / filename
    try:
        document.replace_placeholders(template_path, output_path, paragraphs)
    except RuntimeError as exc:
        st.error(f"Rendering failed. {exc}")
        st.stop()

    st.success(f"Saved → {output_path}")
    st.download_button(
        "Download DOCX",
        data=output_path.read_bytes(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
