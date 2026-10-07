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

## Outstanding / not executed

- Full terraform validate could not complete. The provider plugin failed to start because this execution environment disallows its Unix socket: `listen unix ... socket: operation not permitted`. No checksum verification was disabled. Run CI or local terraform init/validate before any cloud apply.
- Docker build/run was not executed here because no Docker executable/daemon was available. The CI and deploy workflows include build and HTTP smoke checks.
- GitHub CI and OIDC deployment have not been run in a repository.
- No AWS plan against an authenticated account, resource creation, load balancer routing, IAM permission exercise, alarm notification or cloud rollback test has been performed.
- No live accuracy, drift, throughput, availability or business retention results have been measured.

## Non-failing dependency warning

The tested FastAPI/Starlette TestClient emits a deprecation warning about its httpx transport, suggesting a future move to httpx2. All 12 tests pass with the pinned httpx version. This is recorded rather than silenced.

## Next validation sequence

Run on your Mac; then run GitHub CI (including Terraform validation and Docker tests). Review AWS account/region/costs, deploy the bootstrap image and infrastructure, test public routing and logs, and only then exercise OIDC delivery and rollback. Update this report with actual observations.

## Setup continuation — 2026-10-07

- Rechecked the dataset checksum and reproduced all reported holdout metrics in a separate Python 3.12.14 environment using the pinned development requirements.
- All 12 tests passed again (one previously documented Starlette/httpx deprecation warning).
- Retraining wrote to a separate temporary directory; the committed model and the user's existing Python 3.14 environment were preserved.
- Expanded Git and Docker exclusions for local environments, caches, environment files, common credential/key files, Terraform state/plans/variable values and macOS metadata.
- Inspected all 38 tracked files for common AWS/GitHub token and private-key patterns; no matches were found. This is a targeted check, not a guarantee that every possible secret format is detectable.
- GitHub upload and CI results remain pending authentication.
