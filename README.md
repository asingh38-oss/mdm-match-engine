# MDM Match and Merge Engine
Honeywell x UNC Charlotte Capstone Project

This is a matching engine that finds duplicate customer records in Honeywell's MDM system. It handles multilingual company names, address variations, typos, and abbreviations by running records through a preprocessing pipeline and then a multi-level matching engine powered by LLMs.

## What It Does

Takes customer records (company name + address) from an MDM table, compares pairs, and outputs a confidence score from 0 to 100 along with a plain english explanation of why it matched or didn't.

| score | classification |
|-------|----------------|
| > 85  | high confidence match |
| 60–85 | potential match |
| < 60  | non-match |

## How It Works

Records go through preprocessing first to get cleaned up and translated, then get encoded as embeddings so we can efficiently find similar pairs without comparing every record against every other record. Those candidate pairs then get passed through the full 5-level matching engine.

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
  level 3 → company name verification agent ✅
  level 4 → address deep analysis agent ✅
  level 5 → final score computation ✅
      │
      ▼
confidence score + classification + reasoning
```

## Results on Test Dataset

Ran against 20 synthetic records covering multilingual entries, typos, abbreviations, and multiple offices. Found 12 candidate pairs:

| classification | count |
|----------------|-------|
| High Confidence Match | 3 |
| Potential Match | 5 |
| Non-Match | 4 |

Notable results: Müller GmbH & Co. KG vs Muller GmbH Co KG → 89.0 (High Confidence), Lockheed Martin HQ vs Arlington office → correctly classified as Non-Match (different addresses). Full results in `docs/findings.md`.

## Project Structure

```
mdm-match-engine/
├── src/
│   ├── preprocessing/
│   │   ├── cleaner.py              # text normalization, cleanup
│   │   ├── language.py             # language detection + translation
│   │   ├── abbreviations.py        # LLM-based abbreviation expansion
│   │   ├── embeddings.py           # embedding generation + FAISS indexing
│   │   └── pipeline.py             # chains all preprocessing steps together
│   ├── matching/
│   │   ├── level1_exact.py         # exact/fuzzy match check
│   │   ├── level2_geo.py           # geo distance check via Google Maps
│   │   ├── level3_name.py          # LLM company name verification
│   │   ├── level4_address.py       # LLM address deep analysis
│   │   ├── level5_scoring.py       # final score computation
│   │   └── orchestrator.py         # runs all 5 levels in sequence
│   └── utils/
│       ├── config.py               # API keys, thresholds, constants
│       ├── loader.py               # CSV loader
│       └── logger.py               # logging setup
├── data/
│   ├── raw/                        # MDM exports — gitignored, never commit
│   └── test/
│       └── sample_records.csv      # 20 synthetic test records
├── docs/
│   ├── architecture.md             # technical design doc
│   ├── findings.md                 # results and known issues
│   └── threshold_calibration.md    # threshold tuning notes
├── tests/unit/
│   ├── test_cleaner.py             # 17 tests for text normalization
│   ├── test_loader.py              # 6 tests for CSV loader
│   ├── test_scoring.py             # 7 tests for level 5 scoring
│   └── test_orchestrator.py        # 6 tests for full pipeline (mocked)
├── run.py                          # main entry point
├── CONTRIBUTING.md                 # task assignments doc
├── .env.example                    # template for API keys
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

Takes a few minutes — preprocessing makes one API call per record for abbreviation expansion, and the matching engine makes additional calls per candidate pair.

## Running Tests

```bash
python -m pytest tests/unit/ -v
```

36 tests, all passing.

## API Keys Needed

| service | what it's for | where to get it |
|--------|---------|-----------------|
| OpenAI | abbreviation expansion, name/address agents | platform.openai.com |
| Google Maps Geocoding | geo distance checks (level 2) | console.cloud.google.com |

## Team

| name | role |
|------|------|
| Aditya Singh | Set up the repo, CI, and dev environment. Debugged and integrated teammate contributions throughout all 3 weeks |
| Maddy | |
| Samir | |
| Darell | |

## Timeline

Week 1 — preprocessing pipeline, embeddings, candidate pair generation ✅

Week 2 — multi-agent matching engine (levels 2–4) ✅

Week 3 — scoring, classification, reasoning output, final integration ✅

## Known Limitations

The geo distance check (level 2) currently returns REQUEST_DENIED due to Google Cloud billing configuration — it defaults to a neutral score and the engine still works, but scores would be 10-17 points higher with geo fully enabled. The Toyota Japanese transliteration case also doesn't match correctly due to the lossy phonetic rendering — both issues are documented with fixes in `docs/findings.md`.