"""Company research: fetch website text for Gemini context (MVP, no scraping beyond basics)."""
from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (cover-letter-personalizer-mvp)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}
TIMEOUT = 20
MAX_CHARS = 8000


def fetch_website_text(url: str, max_chars: int = MAX_CHARS) -> str:
    """Download a company page and return cleaned visible text."""
    if not url:
        return ""
    try:
        resp = requests.get(url.strip(), headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:  # MVP: research failure is non-fatal, surfaced to prompt
        return f"[Recherche web impossible pour {url} : {exc}]"

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()

    chunks: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if len(text) >= 40:  # skip menus / short labels
            chunks.append(text)

    if not chunks:  # fallback: whole body text
        body = soup.get_text(separator=" ", strip=True)
        chunks = [body] if body else []

    raw = "\n".join(chunks)
    raw = re.sub(r"\s+", " ", raw).strip()
    if len(raw) > max_chars:
        raw = raw[:max_chars].rsplit(" ", 1)[0] + " [...]"
    return raw or "[Aucun contenu textuel exploitable trouvé sur le site.]"


def build_research_context(
    company_name: str,
    position: str,
    website_text: str = "",
    website_url: str = "",
    linkedin_url: str = "",
) -> str:
    lines = [
        f"Entreprise : {company_name}",
        f"Poste visé : {position}",
    ]
    if website_url:
        lines.append(f"Site web : {website_url}")
    if linkedin_url:
        lines.append(
            f"LinkedIn : {linkedin_url} (indicatif uniquement, non exploré dans le MVP)"
        )
    lines.append("")
    lines.append("Extraits du site de l'entreprise :")
    lines.append(website_text or "[Aucune recherche web fournie.]")
    return "\n".join(lines)
