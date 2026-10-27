
from pathlib import Path

import pandas as pd


TARGET_COLUMN = "Attrition"

# These columns are expected in the initial training dataset.
REQUIRED_COLUMNS = {
    "Age",
    "Department",
    "JobRole",
    "MonthlyIncome",
    "YearsAtCompany",
    "JobSatisfaction",
    "WorkLifeBalance",
    "OverTime",
    TARGET_COLUMN,
}


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load and validate a labelled CSV dataset for attrition modelling."""
    dataset_path = Path(path)

    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path.resolve()}"
        )

    if dataset_path.suffix.lower() != ".csv":
        raise ValueError("The training dataset must be a CSV file.")

    df = pd.read_csv(dataset_path)

    if df.empty:
        raise ValueError("The dataset is empty.")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "Dataset is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if df[TARGET_COLUMN].isna().any():
        raise ValueError("Attrition contains missing target labels.")

    labels = set(df[TARGET_COLUMN].astype(str).str.strip().unique())
    if not labels.issubset({"Yes", "No"}) or len(labels) != 2:
        raise ValueError(
            "Attrition must contain both 'Yes' and 'No' labels only."
        )

    if df["Department"].isna().any() or df["JobRole"].isna().any():
        raise ValueError("Department and JobRole cannot contain missing values.")

    return df


def prepare_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Separate validated input features from the historical outcome label."""
    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(
            "DataFrame is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if df[TARGET_COLUMN].isna().any():
        raise ValueError("Attrition contains missing target labels.")

    labels = set(df[TARGET_COLUMN].astype(str).str.strip().unique())
    if not labels.issubset({"Yes", "No"}) or len(labels) != 2:
        raise ValueError(
            "Attrition must contain both 'Yes' and 'No' labels only."
        )

    X = df[
        [
            "Age",
            "Department",
            "JobRole",
            "MonthlyIncome",
            "YearsAtCompany",
            "JobSatisfaction",
            "WorkLifeBalance",
            "OverTime",
        ]
    ].copy()

    y = df[TARGET_COLUMN].astype(str).str.strip().map(
        {"No": 0, "Yes": 1}
    )

    numeric_columns = [
        "Age",
        "MonthlyIncome",
        "YearsAtCompany",
        "JobSatisfaction",
        "WorkLifeBalance",
    ]

    for column in numeric_columns:
        X[column] = pd.to_numeric(X[column], errors="raise")

    if X[numeric_columns].isna().any().any():
        raise ValueError("Numeric feature columns cannot contain missing values.")

    if not X["OverTime"].dropna().isin(["Yes", "No"]).all():
        raise ValueError("OverTime must contain 'Yes' or 'No' values.")

    if X["OverTime"].isna().any():
        raise ValueError("OverTime cannot contain missing values.")

    if X[["Department", "JobRole"]].isna().any().any():
        raise ValueError("Department and JobRole cannot contain missing values.")

    return X, y
