#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/verify_data.py
python -m src.train
printf '\nOpen http://127.0.0.1:8000 in your browser once startup finishes.\nPress Ctrl+C to stop.\n'
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --no-access-log
