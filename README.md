# Licensing Analyst API (Project Talon)

A lightweight FastAPI service that exposes `assemble_deal_profile()` for use in GPT-based ROI analysis of biopharma licensing deals.

## 🔧 Setup

```bash
# 1. Create and activate virtual environment (optional)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the API
uvicorn app.main:app --reload
```

Then visit: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📦 Project Structure

```
licensing_analyst_api/
├── app/
│   ├── main.py
│   ├── gpt_connector.py
│   ├── sec_parser.py
│   ├── test_cases/
│   │   ├── test_case_001.json
│   │   ├── test_case_002.json
│   │   └── test_case_003.json
│   └── utils/
├── actions.yaml
├── requirements.txt
└── README.md
```

## 🚀 CustomGPT Setup

1. Upload `actions.yaml` as your GPT Action schema.
2. Point your GPT to the live endpoint URL (or local if testing).
3. Use the provided prompt format to generate structured reports.
