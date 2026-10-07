# Understand ChurnOps and explain it confidently

## 1. The project in one sentence

“ChurnOps predicts whether a telecom customer may leave, exposes that model through a tested API, and packages the service for repeatable deployment to AWS ECS.”

Churn means a customer stops using a service. A company might use a churn score to prioritise customers for a conversation. This project estimates a sample dataset's churn label; it does not send offers or make decisions about real people.

A useful way to explain the scope is: “I have a working local system, passing GitHub CI including Docker checks, and validated cloud infrastructure configuration. I will describe a live AWS deployment only after I deploy and verify it.”

## 2. What the user sees

The browser has a customer profile form and a result panel. You enter contract length, charges, tenure and service details. Pressing Predict sends JSON to the Python API. The API validates it, runs the saved model, and returns a probability, a review flag, the threshold and the model version.

The compare button sends a second request with only Contract changed to Two year. Both requests use the same actual model. If the score changes, that shows how the model responds to an input change. It does **not** prove changing the contract would prevent churn. Customers on long contracts may also differ in ways this dataset does not capture. This distinction is correlation versus causation.

## 3. Where the data comes from

The CSV comes from IBM's public Telco Customer Churn sample repository. It contains 7,043 fictional customer records. Each row has account information and a target named Churn, with Yes or No values.

The included file is frozen. `scripts/verify_data.py` checks its SHA-256 hash, a fingerprint of the complete file. A different byte changes that fingerprint, so CI fails if the dataset changes unexpectedly. The provenance file records its source and fingerprint.

The model uses eight inputs:

| Feature | Meaning |
|---|---|
| tenure | Months with the company, within the sample's 0–72 month range |
| MonthlyCharges | Current monthly bill amount |
| TotalCharges | Total billed amount; sometimes missing for new customers |
| Contract | Month-to-month, one year or two years |
| InternetService | DSL, fiber optic or no internet |
| PaymentMethod | How the bill is paid |
| PaperlessBilling | Whether paperless billing is enabled |
| TechSupport | Whether support is present, absent or not applicable |

The project excludes customerID because it is an identifier with little generalisable meaning. It excludes Churn from the inputs because Churn is the answer we are trying to predict. Feeding the answer into the model would create data leakage and unrealistic scores. Demographic fields are excluded to keep this demo focused on account features; exclusion alone does not prove fairness.

## 4. How training works

Run `python -m src.train` to execute these steps:

1. Read the CSV and check required columns, target values and duplicate customers.
2. Convert TotalCharges to numbers. Blank entries become missing values.
3. Create X, the eight input columns, and y, the label: Yes becomes 1 and No becomes 0.
4. Split into 80% training data and 20% test data with seed 42. Stratification maintains approximately the same churn ratio in both sets.
5. Fit preprocessing and logistic regression on the training data only.
6. Predict probabilities for the untouched test set and compute the report.
7. Save the fitted preprocessing and model together, plus a separate JSON report.

The split has 5,634 training records and 1,409 test records. A fixed seed makes reruns comparable. It does not guarantee identical results across every operating system or future dependency version.

The test set is the exam, not the study material. If you use test results repeatedly to choose model settings, you start learning from the exam. The current implementation has one preset model and a fixed threshold. When experimenting, create a validation split or use cross-validation within the training set, then evaluate the final choice once on a new holdout.

### Preprocessing

Numbers and categories need different handling.

For numeric columns, the pipeline fills missing values using each training column's median, then standardises values by subtracting its training mean and dividing by its training standard deviation. This makes numbers with different scales easier for a regularised linear model to handle.

For category columns, one-hot encoding creates indicator columns. For example, Contract becomes separate columns for its three choices. This avoids telling the model that an arbitrary text code such as “3” is mathematically three times “1”.

`ColumnTransformer` applies the right operation to each set of columns. `Pipeline` connects those operations to the classifier. The saved object includes the fitted transformations, so training and API inference use the same process. The median and scaler statistics come only from the training split. That is how we avoid preprocessing leakage.

The encoder tolerates unfamiliar categories internally. The public API uses a stricter list of allowed values to catch typos and unsupported profiles. A future legitimate category needs a reviewed schema and data/model update.

## 5. Why logistic regression

Despite its name, logistic regression is used here for classification: predicting Yes or No. It starts with a weighted sum of the transformed inputs:

`z = intercept + weight_1 × feature_1 + weight_2 × feature_2 + ...`

It then applies a sigmoid:

`p = 1 / (1 + exp(-z))`

That converts the score into a number between 0 and 1. `predict_proba` returns estimates for both classes; this code uses the probability of class 1, churn.

It is a sensible first model because it trains quickly, is small enough to serve cheaply and offers understandable coefficients. This project uses regularisation, which discourages unnecessarily large weights. More complexity is not automatically better. A later comparison against gradient boosting should be measured on validation data and assessed for accuracy, explainability, latency and operational cost.

The JSON report includes global coefficients. A positive coefficient increases the model's log-odds when that feature increases, holding the other encoded features fixed. A negative coefficient decreases them. Numeric coefficients refer to standardised values. With all category indicators retained, correlated inputs and regularisation, coefficients should not be read as independent causal effects or precise customer-specific explanations. The UI deliberately avoids invented reasons for an individual prediction.

The probabilities have not been separately calibrated on validation data. A score of 70% is a model estimate, not a demonstrated guarantee that seven of ten equivalent future customers would leave.

## 6. Understand the results

Accuracy: 79.13% of test labels were predicted correctly at threshold 0.50. A model that always says No already gets 73.46%, because most customers do not churn. That is why accuracy alone is insufficient.

Precision: 62.90% of flagged customers actually churned in the test set. Higher precision means fewer unnecessary review calls.

Recall: 52.14% of customers who churned were flagged. This model misses roughly 48% at the current threshold. Higher recall would catch more churners, often at the cost of flagging more non-churners.

F1: 0.5702, a combined precision/recall measure. It is helpful when both matter, but it does not directly measure business profit.

ROC-AUC: 0.8371. It measures how well the model ranks a random churner above a random non-churner across thresholds. An AUC of 0.837 is not “83.7% accuracy”.

Average precision: 0.6365. It summarises the precision/recall ranking tradeoff. The churn prevalence baseline is approximately 0.2654. Average precision is useful when the positive class is less common.

Brier score: 0.1403. It is the average squared difference between estimated probabilities and actual 0/1 outcomes. Lower is better. It is a probability-quality measure, not proof of calibration by itself.

The confusion matrix gives the concrete counts:

| | Predicted stay | Predicted churn |
|---|---:|---:|
| Actually stayed | 920 | 115 |
| Actually churned | 179 | 195 |

The 115 false positives could lead to unnecessary conversations; the 179 false negatives represent missed opportunities. To choose a better threshold for a real business, estimate the cost of each mistake, set review capacity and tune on validation data. Changing the threshold does not retrain the model; it changes when a probability becomes a review flag.

These are static sample results. A random split is weaker evidence for future performance than a time-based evaluation on newly arriving customers. There are no deployment outcome labels yet, so no live performance or retention claims can be made.

## 7. What an API is and how ours works

An API is a predictable interface another program can call. Here it is an HTTP web service built with FastAPI.

| Endpoint | Purpose |
|---|---|
| GET / | Browser demo |
| GET /docs | Interactive generated API documentation |
| GET /health | Is the process alive? |
| GET /ready | Did the model load and complete startup inference? |
| GET /model | Model version, inputs and evaluation report |
| POST /predict | Validate one customer and return a prediction |

Pydantic checks the request: required fields, allowed categories, ranges, extra fields and consistency between internet service and support. Invalid requests return HTTP 422. A missing model makes readiness and predictions return HTTP 503, while liveness stays 200. This separation stops a broken prediction service from appearing healthy merely because its process runs.

At startup, the service loads one trusted model file and performs a sample prediction to catch incompatibility. It reuses the loaded model for subsequent requests, avoiding repeated disk loads and training. To use a newly trained model, restart the process or deploy a new container. The running server does not hot-reload the model file.

Request logs include a generated request ID, endpoint path, response status and elapsed time. They do not include customer payloads. Each response carries the request ID so a failure can be traced. Unexpected prediction failures return a generic error instead of exposing a Python traceback to the client.

## 8. Docker: package the working environment

“It works on my laptop” is not enough if deployment has different libraries. The Dockerfile installs pinned runtime dependencies, copies the API, web files, examples and trusted model, and defines how the service starts.

An image is the packaged template. A container is a running instance of that image. The container listens on port 8000. It runs as a non-root user, reducing its privileges. A health check calls /ready. The cloud task also has a read-only root filesystem. The dataset and training scripts are not used to train during API requests.

The image uses Python 3.12, matching the tested Python major/minor version. Runtime and transitive package versions are pinned to the tested environment. The base image tag is not pinned by digest and package file hashes are not locked, so full bit-for-bit build reproducibility is not claimed. For a production release, pin a reviewed base digest and lock package hashes.

Joblib uses Python object serialisation. Loading an untrusted file can execute code. The service has no model-upload endpoint and should only load artifacts from your own reviewed build.

## 9. GitHub Actions: repeat the checks

Continuous integration, CI, runs when code is pushed or a pull request is opened. It checks the dataset checksum, retrains, runs tests, validates Terraform, builds Docker and sends requests to a running container. These checks are written into the repository; they have not yet executed on GitHub.

Continuous delivery is prepared separately. The deploy workflow is manually triggered from main and uses a GitHub production environment. It repeats the model tests, obtains a short-lived AWS identity, builds and tests a container, pushes it to ECR, registers a new ECS task revision and updates the service.

The image tag includes the source commit and workflow run. Deployment uses the ECR content digest, so the task identifies the actual image bytes rather than a movable tag. The model has its own version fingerprint derived from the fitted object and threshold; the JSON report also records the data hash, seed and sklearn version.

OIDC means GitHub presents a verified identity token to AWS and receives temporary credentials. No long-lived AWS access keys need to be placed in GitHub. The trust policy limits this to the named repository's production environment. That environment must restrict deployment to main and preferably require a reviewer. Without those environment protections, a workflow on another branch might request the same environment identity.

After waiting for ECS stability, the workflow verifies that the active task revision is the newly requested one. This prevents an automatic rollback from being mistaken for a successful deployment merely because the previous version became stable again.

## 10. AWS components and their purpose

ECR stores Docker images. ECS manages containers. Fargate runs them without you managing EC2 servers. The task definition describes the image, CPU, memory, port and logging. The service keeps the desired number of tasks running.

The Application Load Balancer, ALB, receives browser/API requests and forwards them to healthy tasks. Its readiness check calls /ready. Security groups allow public traffic to the ALB on port 80 and allow traffic to a task on port 8000 only from the ALB security group.

The VPC is the network boundary. There are two public subnets so the ALB can use two availability zones. The demo task has a public IP for outbound image downloads and logs, avoiding a paid NAT gateway. That does not make its API port open to the whole internet: the task's inbound security group is restricted. Outbound internet access is broad in this demo.

CloudWatch collects container output and exposes service metrics. Terraform creates CPU and unhealthy-target alarms, with an optional SNS email subscription. You must confirm the subscription email. These alarms monitor infrastructure; they do not measure model accuracy or drift.

The ECS deployment circuit breaker can fail an unhealthy rollout and revert to an earlier completed deployment. The first deployment has no previous completed version to fall back to. One task is economical for a demonstration but is not high availability. There are no autoscaling policies in this implementation.

The demo ALB is HTTP, with no authentication or rate limiting. Use fictional input only. For a real service add an ACM certificate and HTTPS listener, authentication, request limits, an agreed privacy model, private-subnet networking if appropriate and an availability design.

## 11. Terraform: infrastructure as code

Terraform describes the desired cloud resources in text. `terraform plan` shows proposed changes; `terraform apply` creates or updates them. The state file maps that configuration to actual AWS resources. State must be protected and never committed to Git.

The setup deliberately splits responsibilities: Terraform owns infrastructure, while GitHub delivery owns service task-definition revisions. Terraform ignores task_definition changes on the ECS service so a later infrastructure apply does not undo a successful app deployment. This also means changing the bootstrap image variable is not the normal way to update the running service. To change task CPU/memory/log settings, apply the infrastructure change and explicitly deploy the resulting task revision using the runbook.

Remote state is not preconfigured because no AWS account or bucket exists yet. The deployment guide provides a recommended S3 backend setup; the initial demo can use local state with careful retention. `destroy` needs the matching state and account, and deletes the project resources.

## 12. Tests and failure handling

The tests exercise valid predictions, invalid values, unknown/extra fields, missing optional charges, contradictory service details, readiness when the model is missing, exclusion of target/identifier/demographic columns and fitting preprocessing on the training split only. The UI and OpenAPI endpoints are also checked.

The missing-model test is a real local failure simulation: point MODEL_PATH to a nonexistent file, start the application, and assert it stays alive but refuses predictions. It is not a simulated successful AWS rollback. Cloud failover/rollback needs an actual controlled deployment exercise later.

The separate task-rendering test checks that a describe-task response is cleaned into registerable input while preserving CPU, execution role and container settings. This protects the deployment workflow from accidental configuration loss.

## 13. Interview practice

**Why this project?** “I wanted to go beyond a notebook and show how a model is served, tested, versioned and prepared for cloud deployment.”

**Why no neural network?** “This is a small structured dataset. I started with an interpretable linear baseline and focused on reliable evaluation and serving. I would compare more complex models using validation data before adding operational complexity.”

**How did you prevent leakage?** “I excluded the target and customer ID, split before fitting preprocessing, and fitted imputation, scaling and encoding inside a pipeline on training data only.”

**What is the weakest result?** “Recall is about 52% at a 50% threshold. It misses many churners. A real threshold should be chosen using validation data, contact capacity and mistake costs.”

**What happens if the model cannot load?** “Startup inference fails, readiness returns 503 and predictions are unavailable. Liveness still reports that the process runs. That supports load-balancer routing and deployment health checks.”

**How would you detect drift?** “It is not implemented yet. I would compare live feature distributions to a reference window, monitor unknown/missing values, and evaluate performance when delayed churn labels arrive. Feature drift does not automatically mean accuracy fell.”

**What would you improve next?** “Validation-based model comparison and threshold selection, probability calibration, dependency hash locking, HTTPS/authentication, and a real AWS deployment and rollback exercise.”

**Did you deploy this to AWS?** Before deployment: “I prepared and validated the Terraform configuration, and GitHub CI passed the Docker build and API smoke tests. I have not deployed to AWS; its runtime behaviour remains to be tested.” After deployment: describe only actual resources, logs, test requests and rollback evidence you observed.

**Did you build it unaided?** “I used AI assistance for implementation and explanations, then reviewed and ran the project. I can explain the data split, pipeline, serving flow and infrastructure decisions.” Make that statement only after you have actually reviewed and run it yourself.

## 14. A 90-second project explanation

“ChurnOps is a customer churn prediction service. I used IBM's fictional telecom dataset and eight account features. The model is logistic regression with median imputation, numeric scaling and one-hot encoding in a single sklearn pipeline. I split the data before fitting transformations to avoid leakage. On 1,409 held-out customers it achieved 0.837 ROC-AUC, and recall was 52% at the fixed review threshold, so I documented the tradeoff instead of relying on accuracy alone.

“The model is served by FastAPI with input validation, liveness and readiness checks, model version metadata and request logs. The browser demo calls that API and lets you compare a hypothetical contract change, which I label as a model response rather than a causal claim.

“I packaged the service with Docker and wrote GitHub Actions checks. I also prepared Terraform for ECS Fargate, ECR, a load balancer and CloudWatch alarms, plus an OIDC-based deployment workflow. The Python tests, Terraform validation, Docker build and container API checks passed in GitHub Actions. AWS deployment remains a separate, untested stage.”

## 15. Your learning order

Start the app and make two predictions. Read the eight input fields in schema.py. Trace the predict function in api.py. Read train.py from loading through saving. Use the confusion matrix to explain precision and recall without notes. Then read the Dockerfile, the CI workflow and the deployment workflow. Finally read the Terraform resources and AWS runbook.

A good understanding check is to change the example customer's Contract to Two year, predict again and explain why the changed score is not a causal finding. Then point MODEL_PATH at a missing path and explain why /health and /ready give different answers.

## References

- IBM dataset: https://github.com/IBM/telco-customer-churn-on-icp4d
- Leakage and consistent preprocessing: https://scikit-learn.org/stable/common_pitfalls.html
- Logistic regression: https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
- ECS circuit breaker: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html
- GitHub AWS OIDC: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- CoderCo's public project direction: https://coderco.io/academy
