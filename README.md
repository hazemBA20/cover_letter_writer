# AI Cover Letter Personalizer — MVP

Small Python CLI that personalizes a cover-letter `.docx` template for a specific company and position using Gemini (Google AI Studio API key). Only the two designated company paragraphs are rewritten; everything else in the template stays unchanged.

## Prerequisites

- Python 3.12
- `uv` (venv + package installer)
- A Google AI Studio API key (Gemini)

## Setup

```powershell
# 1. Create the virtual environment
uv venv

# 2. Install dependencies
uv pip install -r requirements.txt

# 3. Configure the API key
Copy-Item ".env.example" -Destination ".env"
# then edit .env and set your key:
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.5-flash
```

Run everything with the venv interpreter:

```powershell
.venv\Scripts\python.exe main.py --help
```

## Template requirements

The `.docx` template **must** contain exactly these two placeholders, each on its own paragraph:

```text
[COMPANY_PARAGRAPH_1]

[COMPANY_PARAGRAPH_2]
```

All other content is treated as fixed and is preserved as-is.

> Current state: `templates/` contains `Lettre_de_motivation_Hazem_Ben_Alaya_AI.docx`, which does **not** contain the placeholders (company-specific paragraphs hardcode xHeron). The CLI will reject it until the two placeholders are added — see "Troubleshooting".

## Usage

```powershell
# Preview the Gemini prompt without calling the API (no key needed)
.venv\Scripts\python.exe main.py `
  --company "Invivoo" `
  --position "AI Engineer" `
  --template "templates/ai_engineer_fr.docx" `
  --dry-run

# Full run (needs GEMINI_API_KEY in .env)
.venv\Scripts\python.exe main.py `
  --company "Invivoo" `
  --position "AI Engineer" `
  --website "https://www.invivoo.com" `
  --template "templates/ai_engineer_fr.docx"

# With job description (inline or from file) + LinkedIn (informational only)
.venv\Scripts\python.exe main.py `
  --company "Invivoo" `
  --position "AI Engineer" `
  --website "https://www.invivoo.com" `
  --linkedin "https://www.linkedin.com/company/invivoo" `
  --job-description-file "job.txt" `
  --template "templates/ai_engineer_fr.docx"

# Custom output path and model override
.venv\Scripts\python.exe main.py `
  --company "Invivoo" `
  --position "AI Engineer" `
  --template "templates/ai_engineer_fr.docx" `
  --output "output/custom.docx" `
  --model "gemini-2.5-flash"
```

### CLI options

| Option | Required | Description |
|---|---|---|
| `--company` | yes | Company name |
| `--position` | yes | Target position |
| `--template` | yes | Path to the `.docx` template |
| `--website` | no | Company website URL (fetched for Gemini context) |
| `--linkedin` | no | LinkedIn URL (informational only, not scraped in MVP) |
| `--job-description` | no | Job description text |
| `--job-description-file` | no | Path to a text file with the job description |
| `--output` | no | Output path. Default: `output/{company}_{position}_Hazem_Ben_Alaya.docx` |
| `--prompt` | no | Prompt template path (default: `prompts/personalization.txt`) |
| `--model` | no | Override `GEMINI_MODEL` from `.env` |
| `--dry-run` | no | Build the prompt and print it without calling Gemini |

### Workflow

```text
Company + Position + URLs + Job Description
                    ↓
             Company Research (website text extraction)
                    ↓
              Gemini Prompt (prompts/personalization.txt)
                    ↓
       Two Personalized Paragraphs (JSON)
                    ↓
          Validation → Template Replacement
                    ↓
                DOCX Output
```

### Validation (before rendering)

- Both paragraphs exist and are non-empty (min 80 chars, max 1800 chars each).
- No `[COMPANY_PARAGRAPH_*]` placeholder remains.
- Generation or rendering failure → clear error, no broken letter is written.

## Project structure

```text
.
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── prompts/
│   └── personalization.txt
├── services/
│   ├── gemini.py
│   ├── research.py
│   └── document.py
├── templates/
│   └── Lettre_de_motivation_Hazem_Ben_Alaya_AI.docx
└── output/
```

## Troubleshooting

| Error | Cause / fix |
|---|---|
| `template not found` | Check the `--template` path (relative to project root). |
| `template must be a .docx file` | Only `.docx` is supported (not `.doc` / `.pdf`). |
| `template must contain [COMPANY_PARAGRAPH_1] and [COMPANY_PARAGRAPH_2]` | Open the template in Word, put each placeholder on its own paragraph, save, retry. |
| `GEMINI_API_KEY is missing` | Create `.env` from `.env.example` and set a real key. |
| `Gemini API call failed` | Invalid/expired key, no network, or wrong `--model` name. |
| `Validation failed ... too long/short` | Rerun — Gemini returned an out-of-range paragraph; nothing was written. |
| `Job description file not found` | Check the `--job-description-file` path. |

## Out of scope (MVP)

LangChain/LangGraph, RAG/vector DBs, agents, LinkedIn scraping, DB/auth, web UI, job-board scraping.
