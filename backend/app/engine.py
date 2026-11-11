"""Load the saved models and run the same preprocessing the notebooks used."""

from __future__ import annotations

import json
import math
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.catalog import DISEASES, DiseaseSpec, Field

def _artifact_root() -> Path:
    """Repo root locally. The Vercel build copies artifacts into backend/."""
    here = Path(__file__).resolve()
    backend_dir = here.parents[1]
    for candidate in (here.parents[2], backend_dir):
        if (candidate / "ml").is_dir() and (candidate / "datasets").is_dir():
            return candidate
    return here.parents[2]


ROOT = _artifact_root()
ML_ROOT = ROOT / "ml"
DATA_ROOT = ROOT / "datasets"


class InputError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass
class LoadedModel:
    spec_id: str
    name: str
    reported_accuracy: float
    primary: bool
    features: list[str]
    estimator: Any


@dataclass
class Example:
    id: str
    label: str
    description: str
    values: dict[str, float | int]


@dataclass
class LoadedDisease:
    spec: DiseaseSpec
    columns: list[str]
    models: list[LoadedModel]
    examples: list[Example]
    scaler: Any
    frame: pd.DataFrame
    heart: dict[str, Any] | None = None


def _read_pickle(path: Path) -> Any:
    with path.open("rb") as handle:
        return pickle.load(handle)


def _feature_list(path: Path) -> list[str]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
        raise RuntimeError(f"{path} must be a list of feature names.")
    return payload


def _bounds(series: pd.Series, integer: bool) -> tuple[float, float, str]:
    values = series.astype(float)
    low = float(values.min())
    high = float(values.max())
    span = high - low
    pad = span * 0.08 if span else 1.0
    low -= pad
    high += pad
    if float(values.min()) >= 0 and low < 0:
        low = 0.0
    if integer:
        low = float(math.floor(low))
        high = float(math.ceil(high))
        placeholder = str(int(round(float(values.median()))))
    else:
        low = round(low, 6)
        high = round(high, 6)
        placeholder = f"{float(values.median()):.6g}"
    return low, high, placeholder


def _prepare_frame(spec: DiseaseSpec) -> pd.DataFrame:
    frame = pd.read_csv(DATA_ROOT / spec.dataset_file)
    if spec.rename:
        frame = frame.rename(columns=spec.rename)
    unnamed = [column for column in frame.columns if str(column).startswith("Unnamed") or str(column).strip() == ""]
    if unnamed:
        frame = frame.drop(columns=unnamed)
    return frame


def _load_models(spec: DiseaseSpec, allowed_features: list[str]) -> list[LoadedModel]:
    folder = ML_ROOT / spec.id
    loaded: list[LoadedModel] = []
    primary_count = 0
    allowed = set(allowed_features)
    for model_spec in spec.models:
        if model_spec.primary:
            primary_count += 1
        features = _feature_list(folder / "features" / f"{model_spec.file_stem}.json")
        missing = [name for name in features if name not in allowed]
        if missing:
            raise RuntimeError(f"{spec.id} {model_spec.id} is missing features: {missing}")
        estimator = _read_pickle(folder / "models" / f"{model_spec.file_stem}.sav")
        loaded.append(
            LoadedModel(
                spec_id=model_spec.id,
                name=model_spec.name,
                reported_accuracy=model_spec.reported_accuracy,
                primary=model_spec.primary,
                features=features,
                estimator=estimator,
            )
        )
    if primary_count != 1:
        raise RuntimeError(f"{spec.id} needs exactly one primary model.")
    return loaded


def _scaled_frame(values: dict[str, float], columns: list[str], scaler: Any) -> pd.DataFrame:
    row = pd.DataFrame([{column: values[column] for column in columns}], columns=columns)
    scaled = pd.DataFrame(scaler.transform(row), columns=columns)
    return scaled


def _heart_frame(disease: LoadedDisease, values: dict[str, float]) -> pd.DataFrame:
    heart = disease.heart or {}
    columns: list[str] = heart["columns"]
    categorical: list[str] = heart["categorical"]
    encoder = heart["encoder"]
    encoded_columns: list[str] = heart["encoded_columns"]
    training_columns: list[str] = heart["training_columns"]
    raw = pd.DataFrame([{column: values[column] for column in columns}], columns=columns)
    raw[categorical] = raw[categorical].apply(lambda series: series.map(lambda value: str(int(value))))
    encoded = encoder.transform(raw[categorical])
    if hasattr(encoded, "toarray"):
        encoded = encoded.toarray()
    encoded_frame = pd.DataFrame(encoded, columns=encoded_columns)
    numeric = raw.drop(columns=categorical).reset_index(drop=True)
    combined = pd.concat([numeric, encoded_frame], axis=1)
    combined = combined[training_columns]
    return pd.DataFrame(disease.scaler.transform(combined), columns=training_columns)


def _model_matrix(disease: LoadedDisease, values: dict[str, float]) -> pd.DataFrame:
    if disease.spec.preprocess == "heart":
        return _heart_frame(disease, values)
    return _scaled_frame(values, disease.columns, disease.scaler)


def _alert_probability(estimator: Any, matrix: pd.DataFrame, alert_value: int) -> float | None:
    if not hasattr(estimator, "predict_proba"):
        return None
    probabilities = estimator.predict_proba(matrix)[0]
    classes = [int(label) for label in estimator.classes_]
    if alert_value not in classes:
        return None
    return float(probabilities[classes.index(alert_value)])


def _predict_one(model: LoadedModel, matrix: pd.DataFrame, spec: DiseaseSpec) -> dict[str, Any]:
    features = matrix[model.features]
    prediction = int(model.estimator.predict(features)[0])
    alert_probability = _alert_probability(model.estimator, features, spec.alert_value)
    return {
        "model_id": model.spec_id,
        "model_name": model.name,
        "reported_accuracy": model.reported_accuracy,
        "primary": model.primary,
        "feature_count": len(model.features),
        "prediction": prediction,
        "label": spec.labels[prediction],
        "explanation": spec.explanations[prediction],
        "alert": prediction == spec.alert_value,
        "alert_probability": alert_probability,
    }


def predict(disease: LoadedDisease, raw_values: dict[str, Any]) -> dict[str, Any]:
    values = _validate(disease, raw_values)
    matrix = _model_matrix(disease, values)
    results = [_predict_one(model, matrix, disease.spec) for model in disease.models]
    alert_votes = sum(1 for result in results if result["alert"])
    total = len(results)
    phrase = disease.spec.alert_phrase
    if alert_votes == total:
        summary = f"All {total} models flag {phrase}."
    elif alert_votes == 0:
        summary = f"None of the {total} models flag {phrase}."
    else:
        summary = f"{alert_votes} of {total} models flag {phrase}. They do not all agree."
    return {
        "disease_id": disease.spec.id,
        "results": results,
        "agreement": {
            "alert_votes": alert_votes,
            "total": total,
            "unanimous": alert_votes in (0, total),
            "summary": summary,
        },
    }


def _validate(disease: LoadedDisease, raw_values: dict[str, Any]) -> dict[str, float]:
    if not isinstance(raw_values, dict):
        raise InputError(["Values must be an object of measurements."])
    errors: list[str] = []
    cleaned: dict[str, float] = {}
    for field in disease.spec.fields:
        if field.key not in raw_values or raw_values[field.key] is None or raw_values[field.key] == "":
            errors.append(f"{field.label} is required.")
            continue
        try:
            value = float(raw_values[field.key])
        except (TypeError, ValueError):
            errors.append(f"{field.label} must be a number.")
            continue
        if not math.isfinite(value):
            errors.append(f"{field.label} must be a finite number.")
            continue
        if field.integer and abs(value - round(value)) > 1e-6:
            errors.append(f"{field.label} must be a whole number.")
            continue
        if field.widget == "select":
            allowed = {option for option, _label in field.options}
            if int(round(value)) not in allowed:
                errors.append(f"{field.label} is not one of the listed choices.")
                continue
            cleaned[field.key] = float(int(round(value)))
            continue
        if field.minimum is not None and value < field.minimum:
            errors.append(f"{field.label} must be at least {field.minimum:g}.")
            continue
        if field.maximum is not None and value > field.maximum:
            errors.append(f"{field.label} must be at most {field.maximum:g}.")
            continue
        cleaned[field.key] = float(int(round(value))) if field.integer else value
    if errors:
        raise InputError(errors)
    return cleaned


def _is_alert_row(spec: DiseaseSpec, row: pd.Series) -> bool:
    recorded = row[spec.target_column]
    if isinstance(spec.target_alert, str):
        return str(recorded) == spec.target_alert
    return int(recorded) == int(spec.target_alert)


def _row_values(spec: DiseaseSpec, row: pd.Series) -> dict[str, float | int]:
    values: dict[str, float | int] = {}
    for field in spec.fields:
        number = float(row[field.key])
        if field.integer or number.is_integer():
            values[field.key] = int(round(number))
        else:
            values[field.key] = number
    return values


def _pick_examples(disease: LoadedDisease) -> list[Example]:
    spec = disease.spec
    chosen: dict[str, Example] = {}
    primary = next(model for model in disease.models if model.primary)
    for _index, row in disease.frame.iterrows():
        if row[spec.fields[0].key] != row[spec.fields[0].key]:
            continue
        kind = "alert" if _is_alert_row(spec, row) else "clear"
        if kind in chosen:
            continue
        values = _row_values(spec, row)
        matrix = _model_matrix(disease, {key: float(value) for key, value in values.items()})
        prediction = int(primary.estimator.predict(matrix[primary.features])[0])
        agrees = (prediction == spec.alert_value) == (kind == "alert")
        if not agrees:
            continue
        label, description = spec.example_copy[kind]
        chosen[kind] = Example(kind, label, description, values)
        if len(chosen) == 2:
            break
    missing = [kind for kind in ("alert", "clear") if kind not in chosen]
    if missing:
        raise RuntimeError(f"{spec.id} is missing example rows: {missing}")
    return [chosen["alert"], chosen["clear"]]


def _apply_bounds(spec: DiseaseSpec, frame: pd.DataFrame) -> None:
    for field in spec.fields:
        if field.widget != "number":
            continue
        minimum, maximum, placeholder = _bounds(frame[field.key], field.integer)
        field.minimum = minimum
        field.maximum = maximum
        field.placeholder = placeholder


def _load_disease(spec: DiseaseSpec) -> LoadedDisease:
    folder = ML_ROOT / spec.id / "preprocessing"
    columns = [str(column) for column in list(_read_pickle(folder / "columns.pkl"))]
    field_keys = [field.key for field in spec.fields]
    if set(field_keys) != set(columns):
        raise RuntimeError(f"{spec.id} fields do not match columns.pkl.")
    frame = _prepare_frame(spec)
    missing_columns = [key for key in field_keys + [spec.target_column] if key not in frame.columns]
    if missing_columns:
        raise RuntimeError(f"{spec.id} dataset is missing {missing_columns}.")
    _apply_bounds(spec, frame)
    scaler = _read_pickle(folder / "scaler.pkl")
    heart: dict[str, Any] | None = None
    if spec.preprocess == "heart":
        categorical = [str(column) for column in _read_pickle(folder / "cat_columns.pkl")]
        encoder = _read_pickle(folder / "encoder.pkl")
        encoded_columns = [str(column) for column in list(_read_pickle(folder / "encoded_columns.pkl"))]
        training_columns = [str(column) for column in list(_read_pickle(folder / "training_columns.pkl"))]
        for index, column in enumerate(categorical):
            field = next(item for item in spec.fields if item.key == column)
            expected = [int(category) for category in encoder.categories_[index]]
            actual = [value for value, _label in field.options]
            if actual != expected:
                raise RuntimeError(f"{spec.id} options for {column} do not match the encoder.")
        heart = {
            "columns": columns,
            "categorical": categorical,
            "encoder": encoder,
            "encoded_columns": encoded_columns,
            "training_columns": training_columns,
        }
        models = _load_models(spec, training_columns)
    else:
        models = _load_models(spec, columns)
    disease = LoadedDisease(spec, columns, models, [], scaler, frame, heart)
    disease.examples = _pick_examples(disease)
    return disease


REGISTRY: dict[str, LoadedDisease] = {spec.id: _load_disease(spec) for spec in DISEASES}


def get_disease(disease_id: str) -> LoadedDisease | None:
    return REGISTRY.get(disease_id)
