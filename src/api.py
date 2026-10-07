import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from src.schema import Customer, FEATURES

ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger('churn')
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app):
    app.state.bundle = None
    try:
        # Only load trusted project artifacts: joblib can execute code on load.
        path = Path(os.getenv('MODEL_PATH', str(ROOT/'artifacts/model.joblib')))
        app.state.bundle = joblib.load(path)
        # Force an inference during startup to detect incompatible/corrupt models.
        example = json.loads((ROOT/'examples/customer.json').read_text())
        app.state.bundle['model'].predict_proba(pd.DataFrame([example])[FEATURES])
    except Exception:
        app.state.bundle = None
        logger.exception('Model startup failed')
    yield

app = FastAPI(title='ChurnOps', version='1.0.0', lifespan=lifespan)

@app.middleware('http')
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    logger.info(json.dumps(dict(request_id=request_id, path=request.url.path,
         status=response.status_code, latency_ms=round((time.perf_counter()-started)*1000,2))))
    return response

@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logger.exception('Unexpected inference error')
    return JSONResponse(status_code=500, content={'detail':'Internal prediction error'})

@app.get('/', include_in_schema=False)
def home():
    return FileResponse(ROOT/'web/index.html')

@app.get('/health')
def health():
    return {'status':'alive'}

def bundle(request):
    if request.app.state.bundle is None:
        raise HTTPException(503, 'Model unavailable')
    return request.app.state.bundle

@app.get('/ready')
def ready(request: Request):
    data = bundle(request)
    return {'status':'ready', 'model_version':data['metadata']['model_version']}

@app.get('/model')
def model_info(request: Request):
    return bundle(request)['metadata']

@app.post('/predict')
def predict(customer: Customer, request: Request):
    data = bundle(request)
    row = pd.DataFrame([customer.model_dump()])[FEATURES]
    row['TotalCharges'] = pd.to_numeric(row.TotalCharges, errors='coerce')
    probability = float(data['model'].predict_proba(row)[0,1])
    threshold = data['metadata']['threshold']
    return {'churn_probability':probability, 'flagged':probability >= threshold,
            'threshold':threshold, 'model_version':data['metadata']['model_version']}
