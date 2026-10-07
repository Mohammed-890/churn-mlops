import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.train import load_data, make_pipeline, ROOT, SEED
from src.schema import FEATURES
from sklearn.model_selection import train_test_split

@pytest.fixture
def customer():
    return json.loads((ROOT/'examples/customer.json').read_text())

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_prediction_and_metadata(client, customer):
    assert client.get('/ready').status_code == 200
    response = client.post('/predict', json=customer)
    assert response.status_code == 200
    data=response.json()
    assert 0 <= data['churn_probability'] <= 1
    assert data['flagged'] == (data['churn_probability'] >= data['threshold'])
    assert data['model_version'] == client.get('/model').json()['model_version']
    assert response.headers['X-Request-ID']

@pytest.mark.parametrize('field,value', [('tenure',-1),('Contract','invalid'),('MonthlyCharges',151),('Churn','Yes')])
def test_invalid_input_rejected(client, customer, field, value):
    customer[field]=value
    assert client.post('/predict',json=customer).status_code==422

def test_missing_total_charges(client,customer):
    customer['TotalCharges']=None
    assert client.post('/predict',json=customer).status_code==200

def test_service_consistency(client,customer):
    customer['InternetService']='No'
    assert client.post('/predict',json=customer).status_code==422

def test_missing_model_is_not_ready(monkeypatch,customer):
    monkeypatch.setenv('MODEL_PATH','/nonexistent/model.joblib')
    with TestClient(app) as c:
        assert c.get('/health').status_code==200
        assert c.get('/ready').status_code==503
        assert c.post('/predict',json=customer).status_code==503

def test_no_target_id_or_demographics_used():
    X,y=load_data(ROOT/'data/telco.csv')
    assert list(X.columns)==FEATURES
    assert not {'Churn','customerID','gender','SeniorCitizen'} & set(X.columns)
    assert len(X)==7043

def test_preprocessing_fits_training_only_and_handles_unknown_category():
    X,y=load_data(ROOT/'data/telco.csv')
    train,test,_,_=train_test_split(X,y,test_size=.2,stratify=y,random_state=SEED)
    pipeline=make_pipeline()
    transform=pipeline.named_steps['features']
    transform.fit(train)
    imputer=transform.named_transformers_['numeric'].named_steps['impute']
    assert np.allclose(imputer.statistics_,train[['tenure','MonthlyCharges','TotalCharges']].median())
    probe=test.iloc[:1].copy(); probe['Contract']='future contract'
    encoded=transform.transform(probe)
    assert encoded.shape[0]==1

def test_web_and_openapi(client):
    assert 'ChurnOps' in client.get('/').text
    assert '/predict' in client.get('/openapi.json').json()['paths']
