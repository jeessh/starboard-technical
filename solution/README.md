# Solution

## Setup

```bash
cd solution/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
export OPENAI_API_KEY="sk-..."
python extract.py
```

Output JSON files are written to `candidate-package/example-outputs/`.  
A token usage report is printed to stdout when complete.

## Files

| File | Purpose |
|---|---|
| `extract.py` | Main extraction agent |
| `NOTES.md` | Design decisions and assumptions |
| `requirements.txt` | Python dependencies |
