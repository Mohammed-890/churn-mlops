"""Train once on the training split; evaluate once on the untouched test split."""
import argparse
import hashlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, roc_auc_score, average_precision_score,
                            precision_score, recall_score, f1_score, confusion_matrix, brier_score_loss)
from src.schema import FEATURES, NUMERIC, CATEGORICAL

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
THRESHOLD = 0.5

def load_data(path):
    frame = pd.read_csv(path)
    required = FEATURES + ['Churn', 'customerID']
    if not set(required).issubset(frame.columns):
        raise ValueError('Dataset is missing required columns')
    if frame.customerID.duplicated().any():
        raise ValueError('Duplicate customers could leak across splits')
    if not frame.Churn.isin(['Yes', 'No']).all():
        raise ValueError('Invalid or missing target')
    frame['TotalCharges'] = pd.to_numeric(frame.TotalCharges, errors='coerce')
    if frame[NUMERIC[:2] + CATEGORICAL].isna().any().any():
        raise ValueError('Unexpected missing required feature')
    return frame[FEATURES], (frame.Churn == 'Yes').astype(int)

def make_pipeline():
    numeric = Pipeline([('impute', SimpleImputer(strategy='median')),
                        ('scale', StandardScaler())])
    categorical = OneHotEncoder(handle_unknown='ignore')
    transform = ColumnTransformer([('numeric', numeric, NUMERIC),
                                   ('categorical', categorical, CATEGORICAL)])
    return Pipeline([('features', transform),
                     ('classifier', LogisticRegression(C=1.0, max_iter=1500, random_state=SEED))])

def train(data_path=ROOT/'data/telco.csv', output=ROOT/'artifacts'):
    X, y = load_data(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED)
    model = make_pipeline()
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    predicted = (probabilities >= THRESHOLD).astype(int)
    sha = hashlib.sha256(Path(data_path).read_bytes()).hexdigest()
    version = 'lr-v1-' + hashlib.sha256((joblib.hash(model) + str(THRESHOLD)).encode()).hexdigest()[:12]
    metrics = dict(roc_auc=float(roc_auc_score(y_test, probabilities)),
        average_precision=float(average_precision_score(y_test, probabilities)),
        accuracy=float(accuracy_score(y_test, predicted)),
        precision=float(precision_score(y_test, predicted)),
        recall=float(recall_score(y_test, predicted)),
        f1=float(f1_score(y_test, predicted)),
        brier_score=float(brier_score_loss(y_test, probabilities)),
        confusion_matrix=confusion_matrix(y_test, predicted).tolist(),
        majority_baseline_accuracy=float((y_test == 0).mean()),
        random_ranking_average_precision=float(y_test.mean()))
    names = model.named_steps['features'].get_feature_names_out()
    coefficients = model.named_steps['classifier'].coef_[0]
    global_weights = sorted([dict(feature=n, coefficient=float(c)) for n,c in zip(names,coefficients)],
                            key=lambda v: abs(v['coefficient']), reverse=True)
    metadata = dict(model_version=version, sklearn_version=sklearn.__version__,
        dataset_sha256=sha, seed=SEED, threshold=THRESHOLD,
        train_rows=len(X_train), test_rows=len(X_test), features=FEATURES,
        metrics=metrics, global_coefficients=global_weights,
        source='https://github.com/IBM/telco-customer-churn-on-icp4d',
        disclaimer='IBM fictional sample; probabilities are estimates, not calibrated guarantees.')
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    joblib.dump(dict(model=model, metadata=metadata), output/'model.joblib')
    (output/'metrics.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return metadata

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=ROOT/'data/telco.csv')
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts')
    args = parser.parse_args()
    result = train(args.data, args.output)
    print(json.dumps(result['metrics'], indent=2))
