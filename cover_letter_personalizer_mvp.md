# AI Cover Letter Personalizer — MVP Specification

## Objective

Build a small Python CLI that personalizes an existing cover letter for a specific company and position using Gemini through a **Google AI Studio API key**.

The system must preserve the candidate's fixed content and rewrite only designated adaptable paragraphs.

## Input

The CLI accepts:

- `company_name` — required
- `position` — required
- `website_url` — optional
- `linkedin_url` — optional
- `job_description` — optional
- `template_path` — path to the cover-letter template

Example:

```bash
python main.py \
  --company "Invivoo" \
  --position "AI Engineer" \
  --website "https://www.invivoo.com" \
  --template "templates/ai_engineer_fr.docx"
```

## Template

The cover-letter template contains explicit placeholders:

```text
[COMPANY_PARAGRAPH_1]

[COMPANY_PARAGRAPH_2]
```

Everything else in the template must remain unchanged.

## Workflow

```text
Company + Position + URLs + Job Description
                    ↓
             Company Research
                    ↓
              Gemini Prompt
                    ↓
       Two Personalized Paragraphs
                    ↓
          Template Replacement
                    ↓
                DOCX Output
```

### 1. Research

Fetch useful information from the company website when available. Extract relevant facts about:

- Company activities
- AI/Data/technology work
- Products or services
- Information relevant to the target position

The job description should be included directly in the Gemini context.

LinkedIn is optional and must not be required for the MVP.

### 2. Gemini Generation

Use the official `google-genai` Python SDK and a Google AI Studio API key stored in `.env`.

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

Gemini must:

- Rewrite only the two company paragraphs.
- Write natural, professional French.
- Connect company activities to the candidate's AI/ML background.
- Use only information provided by the research/job description.
- Never invent company facts or candidate experience.
- Avoid generic corporate praise.
- Keep approximately the same length as the original paragraphs.

Return structured JSON:

```json
{
  "company_paragraph_1": "...",
  "company_paragraph_2": "..."
}
```

### 3. Validation

Before rendering:

- Both generated paragraphs must exist and be non-empty.
- No template placeholders may remain.
- Generated text should not be excessively longer than the original.
- If generation fails, return a clear error instead of producing a broken letter.

### 4. Output

Use `python-docx` to replace the placeholders in the existing `.docx` template.

Save to:

```text
output/{company}_{position}_Hazem_Ben_Alaya.docx
```

## Project Structure

```text
cover-letter-ai/
├── main.py
├── config.py
├── .env
├── requirements.txt
├── prompts/
│   └── personalization.txt
├── services/
│   ├── gemini.py
│   ├── research.py
│   └── document.py
├── templates/
│   └── ai_engineer_fr.docx
└── output/
```

## MVP Dependencies

```text
google-genai
python-dotenv
python-docx
requests
beautifulsoup4
```

## Out of Scope

The MVP does **not** require:

- LangChain/LangGraph
- RAG or vector databases
- Autonomous agents
- LinkedIn scraping
- Database/authentication
- Web UI
- Automatic job-board scraping

The goal is a reliable command-line workflow: **provide company information → personalize two paragraphs → generate a ready-to-send DOCX.**
