
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import require_roles
from app.models.user import User
from app.schemas.prediction import (
    AttritionPredictionRequest,
    AttritionPredictionResponse,
)

router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Attrition Predictions"],
)

MODEL_PATH = (
    Path(__file__).resolve().parents[4]
    / "artifacts"
    / "attrition_model.joblib"
)

DISCLAIMER = (
    "Prototype prediction based on a public benchmark dataset. "
    "This estimate is not a validated assessment of an individual. "
    "Do not use it alone for employment, promotion, or termination decisions."
)


@lru_cache(maxsize=1)
def load_model():
    """Load the trained model once per application process."""
    return joblib.load(MODEL_PATH)


@router.post(
    "/attrition",
    response_model=AttritionPredictionResponse,
    status_code=status.HTTP_200_OK,
)
def predict_attrition(
    request: AttritionPredictionRequest,
    current_user: User = Depends(require_roles("ADMIN", "HR")),
):
    """Estimate attrition probability for an employee profile."""
    if not MODEL_PATH.is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Attrition model is unavailable. Train the model first.",
        )

    try:
        model = load_model()

        features = pd.DataFrame(
            [request.model_dump()],
            columns=[
                "Age",
                "Department",
                "JobRole",
                "MonthlyIncome",
                "YearsAtCompany",
                "JobSatisfaction",
                "WorkLifeBalance",
                "OverTime",
            ],
        )

        probabilities = model.predict_proba(features)[0]
        classes = list(model.classes_)

        if 1 not in classes:
            raise ValueError("The trained model has no attrition-positive class.")

        attrition_probability = float(probabilities[classes.index(1)])
        prediction = "Yes" if attrition_probability >= 0.5 else "No"

        # Preliminary demo thresholds, not validated business policy.
        if attrition_probability < 0.30:
            risk_level = "LOW"
        elif attrition_probability < 0.60:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"

        return AttritionPredictionResponse(
            prediction=prediction,
            attrition_probability=round(attrition_probability, 4),
            risk_level=risk_level,
            model="LogisticRegression",
            disclaimer=DISCLAIMER,
        )

    except HTTPException:
        raise
    except Exception as exc:
        # Keep internal model and filesystem details out of API responses.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate a prediction. Check model availability.",
        ) from exc
