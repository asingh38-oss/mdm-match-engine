# MDM Match and Merge Engine
**Honeywell x UNC Charlotte — Undergraduate Capstone Project**

An enterprise-grade customer record matching engine built to identify duplicate entries in Honeywell's Master Data Management (MDM) system. Handles multilingual data, address normalization, company name variations, typos, and abbreviations — with LLM-assisted reasoning at the core.

---

## What This Does

Takes customer records (company name + address) from an MDM table, compares candidate pairs, and outputs a confidence score (0–100) with a classification:

| Score | Classification |
|-------|----------------|
| > 85  | ✅ High Confidence Match |
| 60–85 | ⚠️ Potential Match |
| < 60  | ❌ Non-Match |

Every decision comes with a human-readable explanation of *why* the engine classified it the way it did.

---

## Pipeline Overview

```
Raw MDM Records
      │
      ▼
[Pre-Processing]
  - Language detection
  - Translation (non-English → English)
  - Cleanup: lowercase, trim, strip punctuation
  - Abbreviation expansion (LLM)
      │
      ▼
[Embedding Generation]
  - Encode each record as: "company: {name} || address: {addr} || city: {city} || country: {country}"
  - Store in vector index (FAISS)
  - Pull candidate pairs via similarity threshold
      │
      ▼
[5-Level Matching Engine]
  Level 1 → Exact Match Check
  Level 2 → Geo Distance Check (via API)
  Level 3 → Company Name Verification Agent (LLM)
  Level 4 → Address Deep Analysis Agent (LLM)
  Level 5 → Final Score Computation
      │
      ▼
[Classification + Reasoning Output]
```

---

## Project Structure

```
mdm-match-engine/
├── src/
│   ├── preprocessing/
│   │   ├── cleaner.py          # Text normalization, cleanup
│   │   ├── language.py         # Language detection + translation
│   │   ├── abbreviations.py    # LLM-based abbreviation expansion
│   │   └── embeddings.py       # Embedding generation + FAISS indexing
│   ├── matching/
│   │   ├── level1_exact.py     # Exact match check
│   │   ├── level2_geo.py       # Geo distance check
│   │   ├── level3_name.py      # Company name verification agent
│   │   ├── level4_address.py   # Address deep analysis agent
│   │   ├── level5_scoring.py   # Final score computation
│   │   └── orchestrator.py     # Runs the full pipeline
│   └── utils/
│       ├── config.py           # API keys, thresholds, constants
│       └── logger.py           # Logging setup
├── data/
│   ├── raw/                    # Original MDM exports (gitignored)
│   ├── processed/              # Cleaned/normalized records
│   └── test/                   # Curated test datasets
├── tests/
│   ├── unit/
│   └── integration/
├── notebooks/                  # Exploration + analysis notebooks
├── docs/
│   └── architecture.md         # Design doc (see Week 1 deliverable)
├── .env.example                # Template for API keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/<your-org>/mdm-match-engine.git
cd mdm-match-engine
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your environment variables
```bash
cp .env.example .env
# then fill in your API keys in .env
```

### 5. Run the pre-processing pipeline (Week 1)
```bash
python -m src.preprocessing.cleaner --input data/test/sample_records.csv
```

---

## API Keys Needed

| Service | Purpose | Where to get it |
|--------|---------|-----------------|
| OpenAI (or Anthropic) | Translation, abbreviation expansion, name/address agents | platform.openai.com |
| Google Maps Geocoding API | Geo distance checks (Level 2) | console.cloud.google.com |
| (Optional) DeepL API | Alternate translation option | deepl.com/pro-api |

---

## Team

| Name | Role |
|------|------|
| [Name] | |
| [Name] | |
| [Name] | |
| [Name] | |

---

## Timeline

- **Week 1** — Pre-processing pipeline + embedding generation + exact match ✅ *(in progress)*
- **Week 2** — Multi-agent matching engine (Levels 2–4)
- **Week 3** — Scoring, classification, reasoning output, final integration

---

## Notes

- All raw MDM data goes in `data/raw/` and is gitignored — don't commit any customer data
- Use `data/test/` for sanitized/synthetic test records only
- Keep API keys in `.env` — never commit them
