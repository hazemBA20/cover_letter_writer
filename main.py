"""AI Cover Letter Personalizer — MVP CLI.

Example:
    python main.py --company "Invivoo" --position "AI Engineer" \\
        --website "https://www.invivoo.com" --template "templates/ai_engineer_fr.docx"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from config import load_settings, project_root
from services import document, gemini, research


def sanitize_filename(value: str) -> str:
    value = value.strip().replace(" ", "_")
    value = re.sub(r"[^A-Za-z0-9àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇ_\-]+", "", value)
    return value or "output"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Personalize a cover letter template for a company/position (MVP)."
    )
    parser.add_argument("--company", required=True, help="Company name (required).")
    parser.add_argument("--position", required=True, help="Target position (required).")
    parser.add_argument("--website", default="", help="Company website URL (optional).")
    parser.add_argument("--linkedin", default="", help="LinkedIn URL (optional, MVP: not scraped).")
    parser.add_argument("--job-description", default="", help="Job description text (optional).")
    parser.add_argument(
        "--job-description-file",
        default="",
        help="Path to a text file containing the job description (optional).",
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Path to the .docx cover-letter template.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output .docx path. Default: output/{company}_{position}_Hazem_Ben_Alaya.docx",
    )
    parser.add_argument(
        "--prompt",
        default=str(project_root() / "prompts" / "personalization.txt"),
        help="Path to the personalization prompt template.",
    )
    parser.add_argument("--model", default="", help="Override GEMINI_MODEL from .env.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run research + prompt building without calling Gemini.",
    )
    return parser.parse_args(argv)


def load_job_description(text: str, file_path: str) -> str:
    if file_path:
        path = Path(file_path)
        if not path.is_file():
            raise RuntimeError(f"Job description file not found: {file_path}")
        return path.read_text(encoding="utf-8").strip()
    return (text or "").strip()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    template_path = Path(args.template)
    if not template_path.is_file():
        print(f"ERROR: template not found: {template_path}", file=sys.stderr)
        return 2
    if template_path.suffix.lower() != ".docx":
        print("ERROR: template must be a .docx file.", file=sys.stderr)
        return 2
    if not document.template_has_placeholders(template_path):
        print(
            "ERROR: template must contain [COMPANY_PARAGRAPH_1] and "
            "[COMPANY_PARAGRAPH_2].",
            file=sys.stderr,
        )
        return 2

    try:
        job_description = load_job_description(args.job_description, args.job_description_file)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # 1. Research
    print("1/4 Research: fetching company website..." if args.website else "1/4 Research: no website, using provided context only.")
    website_text = research.fetch_website_text(args.website) if args.website else ""
    if website_text:
        print(f"    → {len(website_text)} chars of website text collected.")
    research_context = research.build_research_context(
        company_name=args.company,
        position=args.position,
        website_text=website_text,
        website_url=args.website,
        linkedin_url=args.linkedin,
    )

    # 2. Prompt
    try:
        prompt_template = gemini.load_prompt_template(args.prompt)
    except OSError as exc:
        print(f"ERROR: cannot read prompt file: {exc}", file=sys.stderr)
        return 2
    prompt = gemini.build_prompt(
        prompt_template,
        company_name=args.company,
        position=args.position,
        research_context=research_context,
        job_description=job_description,
    )

    if args.dry_run:
        print("--- DRY RUN: prompt that would be sent to Gemini ---")
        print(prompt)
        print("--- END DRY RUN (no Gemini call, no DOCX written) ---")
        return 0

    # Settings (API key) only needed for real generation.
    try:
        settings = load_settings(args.model)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # 3. Gemini generation
    print(f"2/4 Gemini: generating paragraphs with {settings.model} ...")
    try:
        paragraphs = gemini.generate_paragraphs(
            api_key=settings.api_key, model=settings.model, prompt=prompt
        )
    except RuntimeError as exc:
        print(f"ERROR: generation failed, no letter produced. {exc}", file=sys.stderr)
        return 1

    # 4. Validation
    print("3/4 Validation: checking generated paragraphs...")
    try:
        document.validate_paragraphs(paragraphs)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # 5. Output
    if args.output:
        output_path = Path(args.output)
    else:
        filename = (
            f"{sanitize_filename(args.company)}_{sanitize_filename(args.position)}"
            f"_Hazem_Ben_Alaya.docx"
        )
        output_path = project_root() / "output" / filename

    print("4/4 Rendering DOCX...")
    try:
        document.replace_placeholders(template_path, output_path, paragraphs)
    except RuntimeError as exc:
        print(f"ERROR: rendering failed. {exc}", file=sys.stderr)
        return 1

    print(f"OK → {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
