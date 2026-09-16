"""Gemini generation via the official google-genai SDK."""
from __future__ import annotations

import json
import re
from pathlib import Path


def load_prompt_template(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def build_prompt(
    template: str,
    *,
    company_name: str,
    position: str,
    research_context: str,
    job_description: str,
    target_words: int = 100,
    target_chars: int = 600,
) -> str:
    return template.format(
        company_name=company_name,
        position=position,
        research_context=research_context or "[Aucune information de recherche.]",
        job_description=job_description or "[Non fournie.]",
        target_words=target_words,
        target_chars=target_chars,
    )


def _extract_json(text: str) -> dict:
    """Parse model output, tolerating ```json fences or surrounding text."""
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini did not return valid JSON: {exc}\nRaw output:\n{text}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Gemini JSON is not an object. Raw output:\n{text}")
    return data


def generate_paragraphs(
    *,
    api_key: str,
    model: str,
    prompt: str,
) -> dict[str, str]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc

    text = (getattr(response, "text", "") or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    data = _extract_json(text)
    return {
        "company_paragraph_1": str(data.get("company_paragraph_1", "")).strip(),
        "company_paragraph_2": str(data.get("company_paragraph_2", "")).strip(),
    }
