
# PhishGuard Pro (Backend)

FastAPI + TensorFlow phishing detector with Gmail scanning and SQLite storage.

## Setup (Local)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Place datasets:
```
backend/data/enron_spam_data.csv
backend/data/spam_assassin.csv
```

Train:
```bash
python train.py --epochs 5
```

Run API:
```bash
python -m uvicorn app.main:app --reload
```

Docs: http://127.0.0.1:8000/docs

### Apple Silicon note
If you see optimizer warnings or slow training:
```bash
pip uninstall -y tensorflow
pip install tensorflow-macos==2.15.0 tensorflow-metal==1.1.0
```

## Gmail Scan

1. Create OAuth **Desktop App** in Google Cloud, download `credentials.json` into `backend/`.
2. Start API, then trigger:
```bash
curl -X POST http://127.0.0.1:8000/emails/scan -H "Content-Type: application/json" -d '{"max_messages":20,"query":"in:inbox newer_than:30d"}'
```
First run opens a browser for consent. Token is saved as `token.json`.
