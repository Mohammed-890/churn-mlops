from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

NUMERIC = ['tenure', 'MonthlyCharges', 'TotalCharges']
CATEGORICAL = ['Contract', 'InternetService', 'PaymentMethod', 'PaperlessBilling', 'TechSupport']
FEATURES = NUMERIC + CATEGORICAL

class Customer(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    tenure: int = Field(ge=0, le=72)
    MonthlyCharges: float = Field(ge=0, le=150)
    TotalCharges: float | None = Field(default=None, ge=0, le=12000)
    Contract: Literal['Month-to-month', 'One year', 'Two year']
    InternetService: Literal['DSL', 'Fiber optic', 'No']
    PaymentMethod: Literal['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)']
    PaperlessBilling: Literal['Yes', 'No']
    TechSupport: Literal['Yes', 'No', 'No internet service']

    @model_validator(mode='after')
    def consistent_service(self):
        if (self.InternetService == 'No') != (self.TechSupport == 'No internet service'):
            raise ValueError('TechSupport must match whether internet service exists')
        return self
