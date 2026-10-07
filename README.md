# ChurnOps — an ML prediction service with an ECS deployment design

A working customer churn demo, a tested Python API, reproducible training, Docker packaging, GitHub Actions workflows and Terraform infrastructure. Inspired by the public ECS project direction at CoderCo; independently implemented, not a copy of its paid course.

**Start here:** this is a locally tested portfolio implementation. AWS resources have not been created, and the GitHub workflows have not run on a GitHub repository yet. The detailed verification report distinguishes tested components from prepared deployment code.

## Run it on your Mac

1. Download and extract the repository ZIP, or clone it with `git clone https://github.com/Mohammed-890/churn-mlops.git`.
2. Open Terminal, type `cd ` (including the space), drag that folder into Terminal, and press Enter.
3. Run `bash start.sh`. Requires Python 3.12, the version used for testing. The first run needs internet access to install packages.
4. Open **http://127.0.0.1:8000** after the terminal says the application has started. Leave Terminal running.
5. Click **Predict churn risk**, then **Compare two-year contract**. Visit **http://127.0.0.1:8000/docs** to inspect the API.

Stop with Ctrl+C. If port 8000 is occupied, stop the earlier app or run `python -m uvicorn src.api:app --port 8001` with the virtual environment activated and use that address.

## What is included

| File or folder | Purpose |
|---|---|
| `src/train.py` | Data loading, train/test split, preprocessing, model training and evaluation |
| `src/schema.py` | The eight input features and request validation |
| `src/api.py` | Web demo, prediction endpoint, health/readiness checks and request logs |
| `web/index.html` | Responsive browser interface; calls the real API |
| `data/` | IBM fictional dataset, checksum, provenance and upstream license |
| `artifacts/` | Trained model and measured evaluation report |
| `tests/` | API, validation, leakage prevention and failure tests |
| `Dockerfile` | Non-root Python service container |
| `.github/workflows/` | CI checks and manually triggered AWS deployment |
| `infra/` | ECS Fargate, ECR, networking, ALB, logs, alarms and deployment identity |
| `docs/EXPLAINED.md` | Full beginner-friendly project explanation and interview answers |
| `docs/AWS_DEPLOYMENT.md` | Bootstrap, deployment, rollback and teardown instructions |
| `docs/VERIFICATION.md` | Actual executed checks and outstanding validation |

## Measured result

Split: 5,634 training customers and 1,409 held-out test customers. Logistic regression, fixed 0.50 review threshold, random seed 42.

| Metric | Test result |
|---|---:|
| ROC-AUC | 0.8371 |
| Average precision | 0.6365 |
| Accuracy | 79.13% |
| Precision | 62.90% |
| Recall | 52.14% |
| F1 | 0.5702 |
| Majority baseline accuracy | 73.46% |

AUC is not accuracy. These results describe this fictional sample's random holdout, not guaranteed performance on real customers. The project does not demonstrate actual customer retention, savings, or business impact.

## Developer commands

From the project folder after activating `.venv`:

```bash
python -m pip install -r requirements-dev.txt
python scripts/verify_data.py
python -m src.train
python -m pytest -q
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Example request from another Terminal:

```bash
curl -H 'Content-Type: application/json' \
  -d @examples/customer.json http://127.0.0.1:8000/predict
```

Docker (Docker Desktop must be running):

```bash
docker build --platform linux/amd64 -t churnops:local .
docker run --rm -p 8000:8000 churnops:local
```

The `--platform` option makes the image match the x86_64 ECS task on an Apple Silicon Mac. Local emulation can be slower. CI builds on x86_64 Ubuntu.

## Scope and next improvements

This is a tabular machine learning and cloud engineering project, not generative AI. Its stronger portfolio contribution is the working system around the model. There is no Kubernetes, database, authentication, retraining scheduler or drift detector hidden in the implementation.

The cloud configuration is a short-lived demonstration: one task, public HTTP ALB, public task IP for outbound access, restricted inbound task traffic. Before using real customer records or running a persistent public service, add HTTPS, authentication, rate limiting, budgets, a controlled data pipeline and stronger availability. See the deployment guide for exact limits and costs to review.

Data source: https://github.com/IBM/telco-customer-churn-on-icp4d
Technical references: scikit-learn common pitfalls; AWS ECS circuit breaker documentation; GitHub AWS OIDC documentation. Links are in the explanation guide.
