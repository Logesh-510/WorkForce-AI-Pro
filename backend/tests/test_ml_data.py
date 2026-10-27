
import pandas as pd
import pytest

from app.ml.data import load_dataset, prepare_features


@pytest.fixture
def valid_dataset():
    return pd.DataFrame(
        {
            "Age": [29, 42, 35, 50],
            "Department": ["IT", "Sales", "HR", "IT"],
            "JobRole": [
                "Developer",
                "Sales Executive",
                "HR Specialist",
                "Manager",
            ],
            "MonthlyIncome": [4000, 3500, 4200, 6000],
            "YearsAtCompany": [2, 10, 5, 20],
            "JobSatisfaction": [3, 2, 4, 3],
            "WorkLifeBalance": [3, 2, 3, 4],
            "OverTime": ["Yes", "No", "No", "Yes"],
            "Attrition": ["Yes", "No", "No", "Yes"],
        }
    )


def test_prepare_features_separates_target(valid_dataset):
    X, y = prepare_features(valid_dataset)

    assert "Attrition" not in X.columns
    assert len(X) == len(y) == 4
    assert set(y.unique()) == {0, 1}


def test_load_dataset_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "missing.csv")


def test_load_dataset_rejects_missing_columns(tmp_path):
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Age": [30], "Attrition": ["Yes"]}).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing required columns"):
        load_dataset(path)


def test_load_dataset_rejects_single_class(tmp_path, valid_dataset):
    valid_dataset["Attrition"] = ["Yes", "Yes", "Yes", "Yes"]
    path = tmp_path / "single_class.csv"
    valid_dataset.to_csv(path, index=False)

    with pytest.raises(ValueError, match="both 'Yes' and 'No'"):
        load_dataset(path)


def test_prepare_features_rejects_invalid_target(valid_dataset):
    valid_dataset.loc[0, "Attrition"] = "Unknown"

    with pytest.raises(ValueError, match="both 'Yes' and 'No'"):
        prepare_features(valid_dataset)


def test_prepare_features_rejects_invalid_overtime(valid_dataset):
    valid_dataset.loc[0, "OverTime"] = "Sometimes"

    with pytest.raises(ValueError, match="OverTime"):
        prepare_features(valid_dataset)
