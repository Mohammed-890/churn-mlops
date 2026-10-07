.PHONY: setup train test run verify docker
setup:
	python -m pip install -r requirements-dev.txt
verify:
	python scripts/verify_data.py
train: verify
	python -m src.train
test:
	python -m pytest -q
run:
	python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
docker:
	docker build -t churnops:local .
