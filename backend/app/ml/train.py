
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.data import load_dataset, prepare_features


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = PROJECT_ROOT / "database" / "attrition.csv"
MODEL_DIR = PROJECT_ROOT / "artifacts"
MODEL_PATH = MODEL_DIR / "attrition_model.joblib"
REPORT_PATH = MODEL_DIR / "attrition_evaluation.json"

RANDOM_STATE = 42


def train_model(dataset_path: str | Path = DEFAULT_DATASET) -> dict:
    """Train, evaluate, and save an attrition classifier."""

    df = load_dataset(dataset_path)
    X, y = prepare_features(df)

    if len(df) < 10:
        raise ValueError(
            "At least 10 labelled rows are required for a training split."
        )

    class_counts = y.value_counts()
    if class_counts.min() < 2:
        raise ValueError(
            "Each attrition class must have at least two examples."
        )

    numeric_features = [
        "Age",
        "MonthlyIncome",
        "YearsAtCompany",
        "JobSatisfaction",
        "WorkLifeBalance",
    ]
    categorical_features = [
        "Department",
        "JobRole",
        "OverTime",
    ]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=RANDOM_STATE,
            stratify=y,
        )
    except ValueError as exc:
        raise ValueError(
            "Unable to create a stratified train/test split. "
            "Provide enough labelled examples in both attrition classes."
        ) from exc

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    report = {
        "model": "LogisticRegression",
        "dataset_rows": int(len(df)),
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "random_state": RANDOM_STATE,
        "target_mapping": {"No": 0, "Yes": 1},
        "metrics": {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(
                precision_score(y_test, predictions, zero_division=0)
            ),
            "recall": float(
                recall_score(y_test, predictions, zero_division=0)
            ),
            "f1_score": float(
                f1_score(y_test, predictions, zero_division=0)
            ),
        },
        "confusion_matrix": confusion_matrix(
            y_test, predictions, labels=[0, 1]
        ).tolist(),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=["No attrition", "Attrition"],
            output_dict=True,
            zero_division=0,
        ),
        "warning": (
            "Metrics describe only this holdout split. "
            "They do not establish real-world performance."
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Save only after training and evaluation have completed.
    joblib.dump(model, MODEL_PATH)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report


if __name__ == "__main__":
    try:
        evaluation = train_model()
        print(json.dumps(evaluation, indent=2))
        print(f"\nModel saved to: {MODEL_PATH}")
        print(f"Evaluation report saved to: {REPORT_PATH}")
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Training stopped: {exc}") from exc
