# MDM Match and Merge Engine
Honeywell x UNC Charlotte Capstone Project

Matching engine that finds duplicate customer records in Honeywell's MDM system. Handles multilingual company names, address variations, typos, and abbreviations using embeddings and LLM agents.

## What It Does

Takes customer records (company name + address) from an MDM table, compares pairs, and outputs a confidence score from 0 to 100.

| score | classification |
|-------|----------------|
| > 85  | high confidence match |
| 60–85 | potential match |
| < 60  | non-match |

Each result also comes with a plain english explanation of why it matched or didn't.

## How the Pipeline Works

```
raw MDM records
      │
      ▼
pre-processing
  - language detection
  - translation (non-english → english)
  - cleanup: lowercase, trim, strip punctuation
  - abbreviation expansion via LLM
      │
      ▼
embedding generation
  - encode each record as: "company: {name} || address: {addr} || city: {city} || country: {country}"
  - index with FAISS
  - pull candidate pairs above similarity threshold (avoids brute force n^2)
      │
      ▼
5-level matching engine
  level 1 → exact/fuzzy match check
  level 2 → geo distance check (week 2)
  level 3 → company name verification agent (week 2)
  level 4 → address deep analysis agent (week 2)
  level 5 → final score computation (week 3)
      │
      ▼
classification + reasoning output
```

## Project Structure

```
mdm-match-engine/
├── src/
│   ├── preprocessing/
│   │   ├── cleaner.py          # text normalization, cleanup
│   │   ├── language.py         # language detection + translation
│   │   ├── abbreviations.py    # LLM-based abbreviation expansion
│   │   ├── embeddings.py       # embedding generation + FAISS indexing
│   │   └── pipeline.py         # chains all preprocessing steps together
│   ├── matching/
│   │   ├── level1_exact.py     # exact match check
│   │   ├── level2_geo.py       # geo distance check (week 2)
│   │   ├── level3_name.py      # company name verification agent (week 2)
│   │   ├── level4_address.py   # address deep analysis agent (week 2)
│   │   ├── level5_scoring.py   # final score computation (week 3)
│   │   └── orchestrator.py     # runs the full pipeline (week 3)
│   └── utils/
│       ├── config.py           # API keys, thresholds, constants
│       ├── loader.py           # CSV loader
│       └── logger.py           # logging setup
├── data/
│   ├── raw/                    # original MDM exports (gitignored)
│   ├── processed/              # cleaned/normalized records
│   └── test/                   # test datasets
├── tests/
│   └── unit/
├── docs/
│   └── architecture.md
├── run.py
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

Clone the repo and cd into it.

```bash
git clone https://github.com/asingh38-oss/mdm-match-engine.git
cd mdm-match-engine
```

Create a virtual environment and activate it.

```bash
python -m venv venv
source venv/bin/activate       # mac/linux
venv\Scripts\activate          # windows
```

If you're on Windows and get a script execution error run this first:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Install dependencies.

```bash
pip install -r requirements.txt
```

If `faiss-cpu` fails on Windows run `pip install faiss-cpu==1.13.2` manually. If `sentence-transformers` errors out run `pip install sentence-transformers` separately.

Copy the example env file and fill in your API keys.

```bash
cp .env.example .env
```

Run it.

```bash
python run.py
```

Takes about 1-2 minutes on the test dataset since abbreviation expansion makes one API call per record.

## API Keys Needed

| service | what it's used for | where to get it |
|--------|---------|-----------------|
| OpenAI | abbreviation expansion, name/address agents | platform.openai.com |
| Google Maps Geocoding | geo distance checks (level 2, week 2) | console.cloud.google.com |

## Team

| name | role |
|------|------|
| Aditya Singh | |
| Maddy | |
| Samir | |
| Darell | |

## Timeline

Week 1 — preprocessing pipeline, embeddings, candidate pair generation ✅

Week 2 — multi-agent matching engine (levels 2–4)

Week 3 — scoring, classification, reasoning output, final integration

## Notes

Raw MDM data goes in `data/raw/` and is gitignored so don't commit any customer data. Test data only goes in `data/test/`. Never commit your `.env` file. Short company names like "GE Company" can confuse the language detector since it doesn't have enough characters to work with — known issue, fixing in week 2.