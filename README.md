# MDM Match and Merge Engine
Honeywell x UNC Charlotte Capstone Project

This is a matching engine that finds duplicate customer records in Honeywell's MDM system. It handles multilingual company names, address variations, typos, and abbreviations by running records through a preprocessing pipeline and then a multi-level matching engine powered by LLMs.

## What It Does

Takes customer records (company name + address) from an MDM table, compares pairs, and spits out a confidence score from 0 to 100 along with a plain english explanation of why it matched or didn't.

| score | classification |
|-------|----------------|
| > 85  | high confidence match |
| 60–85 | potential match |
| < 60  | non-match |

## How It Works

Records go through preprocessing first to get cleaned up and translated, then get encoded as embeddings so we can efficiently find similar pairs without comparing every record against every other record. Those candidate pairs then get passed through the matching engine.

```
raw MDM records
      │
      ▼
pre-processing
  - language detection + translation
  - text cleanup (lowercase, punctuation, articles)
  - abbreviation expansion via LLM
      │
      ▼
embedding generation
  - encode each record, index with FAISS
  - find candidate pairs above similarity threshold
      │
      ▼
matching engine
  level 1 → exact/fuzzy match check ✅
  level 2 → geo distance check ✅
  level 3 → company name verification agent (in progress)
  level 4 → address deep analysis agent (in progress)
  level 5 → final score computation (week 3)
      │
      ▼
confidence score + classification + reasoning
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
│   │   ├── level1_exact.py     # exact match check ✅
│   │   ├── level2_geo.py       # geo distance check ✅
│   │   ├── level3_name.py      # company name verification agent (in progress)
│   │   ├── level4_address.py   # address deep analysis agent (in progress)
│   │   ├── level5_scoring.py   # final score computation (week 3)
│   │   └── orchestrator.py     # runs the full pipeline
│   └── utils/
│       ├── config.py           # API keys, thresholds, constants
│       ├── loader.py           # CSV loader
│       └── logger.py           # logging setup
├── data/
│   ├── raw/                    # original MDM exports (gitignored)
│   └── test/                   # test datasets
├── tests/unit/
├── docs/architecture.md
├── run.py
├── .env.example
└── requirements.txt
```

## Setup

Clone the repo and cd into it, then create and activate a virtual environment.

```bash
git clone https://github.com/asingh38-oss/mdm-match-engine.git
cd mdm-match-engine
python -m venv venv
source venv/bin/activate       # mac/linux
venv\Scripts\activate          # windows
```

If you're on Windows and get a script execution error when activating, run this first:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Install dependencies, copy the env file, and fill in your API keys.

```bash
pip install -r requirements.txt
cp .env.example .env
```

If `faiss-cpu` fails on Windows run `pip install faiss-cpu==1.13.2` manually. If `sentence-transformers` errors out run `pip install sentence-transformers` separately.

Then run it:
```bash
python run.py
```

Takes about 1-2 minutes on the test dataset since abbreviation expansion makes one API call per record.

## API Keys Needed

| service | what it's for | where to get it |
|--------|---------|-----------------|
| OpenAI | abbreviation expansion, name/address agents | platform.openai.com |
| Google Maps Geocoding | geo distance checks (level 2) | console.cloud.google.com |

## Team

| name | role |
|------|------|
| Aditya Singh | |
| Maddy | |
| Samir | |
| Darell | |

## Timeline

Week 1 — preprocessing pipeline, embeddings, candidate pair generation ✅

Week 2 — multi-agent matching engine (levels 2–4) in progress

Week 3 — scoring, classification, reasoning output, final integration

## Notes

Raw MDM data goes in `data/raw/` and is gitignored so don't commit any customer data. Test data only in `data/test/`. Never commit your `.env`. Short company names like "GE Company" can trip up the language detector since there aren't enough characters to detect reliably — known issue, fixing this week.