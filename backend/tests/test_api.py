"""Smoke tests for loading, labeling, and the prediction API."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DIABETES_ROW = {
    "Pregnancies": 6,
    "Glucose": 148,
    "BloodPressure": 72,
    "SkinThickness": 35,
    "Insulin": 0,
    "BMI": 33.6,
    "DiabetesPedigreeFunction": 0.627,
    "Age": 50,
}

HEART_ROW = {
    "age": 52,
    "sex": 1,
    "cp": 0,
    "trestbps": 125,
    "chol": 212,
    "fbs": 0,
    "restecg": 1,
    "thalach": 168,
    "exang": 0,
    "oldpeak": 1,
    "slope": 2,
    "ca": 2,
    "thal": 3,
}

BREAST_ROW = {
    "mean radius": 17.99,
    "mean texture": 10.38,
    "mean perimeter": 122.8,
    "mean area": 1001,
    "mean smoothness": 0.1184,
    "mean compactness": 0.2776,
    "mean concavity": 0.3001,
    "mean concave points": 0.1471,
    "mean symmetry": 0.2419,
    "mean fractal dimension": 0.07871,
    "radius error": 1.095,
    "texture error": 0.9053,
    "perimeter error": 8.589,
    "area error": 153.4,
    "smoothness error": 0.006399,
    "compactness error": 0.04904,
    "concavity error": 0.05373,
    "concave points error": 0.01587,
    "symmetry error": 0.03003,
    "fractal dimension error": 0.006193,
    "worst radius": 25.38,
    "worst texture": 17.33,
    "worst perimeter": 184.6,
    "worst area": 2019,
    "worst smoothness": 0.1622,
    "worst compactness": 0.6656,
    "worst concavity": 0.7119,
    "worst concave points": 0.2654,
    "worst symmetry": 0.4601,
    "worst fractal dimension": 0.1189,
}


def test_health_lists_four_systems() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["diseases"] == [
        "diabetes",
        "heart-disease",
        "parkinsons",
        "breast-cancer",
    ]


def test_each_system_has_three_models_and_two_examples() -> None:
    listing = client.get("/api/diseases")
    assert listing.status_code == 200
    bodies = listing.json()
    assert [item["id"] for item in bodies] == [
        "diabetes",
        "heart-disease",
        "parkinsons",
        "breast-cancer",
    ]
    for summary in bodies:
        assert summary["alertPhrase"]
        assert len(summary["models"]) == 3
        assert sum(1 for model in summary["models"] if model["primary"]) == 1
        detail = client.get(f"/api/diseases/{summary['id']}")
        assert detail.status_code == 200
        payload = detail.json()
        assert len(payload["examples"]) == 2
        assert payload["fields"]
        example = payload["examples"][0]
        predicted = client.post(
            f"/api/diseases/{summary['id']}/predict",
            json={"values": example["values"]},
        )
        assert predicted.status_code == 200
        body = predicted.json()
        assert len(body["results"]) == 3
        assert {item["prediction"] for item in body["results"]} <= {0, 1}


def test_known_cases_keep_clinical_labels() -> None:
    diabetes = client.post("/api/diseases/diabetes/predict", json={"values": DIABETES_ROW})
    assert diabetes.status_code == 200
    by_model = {item["modelId"]: item for item in diabetes.json()["results"]}
    assert by_model["random-forest"]["alert"] is True
    assert by_model["svc"]["alertProbability"] is None
    assert by_model["logistic-regression"]["alertProbability"] is not None

    heart = client.post("/api/diseases/heart-disease/predict", json={"values": HEART_ROW})
    assert heart.status_code == 200
    heart_models = {item["modelId"]: item for item in heart.json()["results"]}
    assert heart_models["xgboost"]["prediction"] == 0
    assert heart_models["xgboost"]["label"] == "Higher risk"

    breast = client.post("/api/diseases/breast-cancer/predict", json={"values": BREAST_ROW})
    assert breast.status_code == 200
    assert all(item["prediction"] == 0 for item in breast.json()["results"])
    assert all(item["label"] == "Malignant pattern" for item in breast.json()["results"])


def test_invalid_input_is_rejected() -> None:
    missing = client.post("/api/diseases/diabetes/predict", json={"values": {}})
    assert missing.status_code == 422
    assert "Glucose is required." in missing.json()["detail"]

    wild = {**DIABETES_ROW, "Glucose": 5000}
    out_of_range = client.post("/api/diseases/diabetes/predict", json={"values": wild})
    assert out_of_range.status_code == 422

    bad_thal = {**HEART_ROW, "thal": 9}
    rejected = client.post("/api/diseases/heart-disease/predict", json={"values": bad_thal})
    assert rejected.status_code == 422

    unknown = client.get("/api/diseases/not-a-disease")
    assert unknown.status_code == 404
