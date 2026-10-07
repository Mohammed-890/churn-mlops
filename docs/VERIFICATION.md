# Verification report — 2026-10-07

## Passed locally

- Training on the frozen 7,043-row IBM dataset; 5,634 train and 1,409 test records.
- Dataset SHA-256 verified against the recorded fingerprint.
- Model evaluation: ROC-AUC 0.837124, average precision 0.636479, accuracy 0.791341, precision 0.629032, recall 0.521390, F1 0.570175.
- 12 pytest tests passed in a fresh Python 3.12 virtual environment installed from project requirements. Includes missing-model failure behaviour and task definition rendering.
- A real Uvicorn process accepted HTTP requests: /ready returned 200 and model version lr-v1-44b015f799fa; example /predict returned churn probability 0.7391927294.
- Headless Chrome exercised the actual form, prediction button and contract comparison. Example changed from 73.9% to 39.6% when only the contract became Two year. This is a hypothetical model response, not a measured causal effect.
- Desktop 1440px and mobile 390px browser checks passed, including no mobile horizontal overflow and no JavaScript page errors. Screenshots are included in docs/.
- Python source compiled successfully; startup shell scripts passed bash syntax checks.
- Both GitHub workflow YAML files parsed successfully. This checks syntax, not actual GitHub execution.
- Terraform 1.9.8 formatting check passed; provider initialization downloaded the signed AWS 5.100.0 release and generated the included official dependency lock file.

## Passed in GitHub Actions

[Run 37617722779](https://github.com/Mohammed-890/churn-mlops/actions/runs/37617722779) passed on commit `94cc5580d1e7f39ba8d93b8fb11f95b76d94a23b` on 2026-10-07:

- Installed the pinned development requirements on Python 3.12 / Ubuntu.
- Verified the dataset checksum and retrained the model; the reported metrics matched the local results.
- All 12 tests passed with the known deprecation warning.
- Terraform 1.9.8 formatting, provider initialization and configuration validation passed.
- Built the Docker image, started the container, and received successful readiness and prediction responses.
- Example churn probability: `0.7391927294054842`; CI model version: `lr-v1-9ee484f3e882`. Artifact identifiers can differ across platforms even when metrics and predictions agree.

Terraform initialization and validation also passed on the Mac during this continuation. The official signed AWS 5.100.0 package was verified and its Mac checksum added to the lock file; no checksum validation was bypassed. This resolves the earlier environment-specific validation limitation.

## Outstanding / not executed

- Docker was tested on GitHub's Ubuntu runner, not on this Mac, where Docker is not installed.
- The manual AWS/OIDC deployment workflow has not been run.
- No AWS plan against an authenticated account, resource creation, load balancer routing, IAM permission exercise, alarm notification or cloud rollback test has been performed.
- No live accuracy, drift, throughput, availability or business retention results have been measured.

## Non-failing dependency warning

The tested FastAPI/Starlette TestClient emits a deprecation warning about its httpx transport, suggesting a future move to httpx2. All 12 tests pass with the pinned httpx version. This is recorded rather than silenced.

## Next validation sequence

Local Python checks and GitHub CI are complete. A future AWS stage requires separate approval and a chosen account, region and budget. Only after that stage should public routing, logs, OIDC delivery and rollback be described as tested. No cloud deployment was authorized or performed during this setup.

## Setup continuation — 2026-10-07

- Rechecked the dataset checksum and reproduced all reported holdout metrics in a separate Python 3.12.14 environment using the pinned development requirements.
- All 12 tests passed again (one previously documented Starlette/httpx deprecation warning).
- Retraining wrote to a separate temporary directory; the committed model and the user's existing Python 3.14 environment were preserved.
- Expanded Git and Docker exclusions for local environments, caches, environment files, common credential/key files, Terraform state/plans/variable values and macOS metadata.
- Inspected all 38 tracked files for common AWS/GitHub token and private-key patterns; no matches were found. This is a targeted check, not a guarantee that every possible secret format is detectable.
- Authenticated as Mohammed-890 and uploaded the existing history. GitHub CI passed on its first run; no CI implementation fixes were required.
