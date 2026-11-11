# MedBud

MedBud is a Vite web app for four saved classifiers:

1. Diabetes prediction
2. Heart disease prediction
3. Parkinson's disease prediction
4. Breast cancer prediction

The interface is React. Predictions run in a FastAPI service that loads the original scikit-learn and XGBoost models, scalers, and selected-feature lists. It is an educational demo, not a medical device, and it does not diagnose or rule out disease.

## Layout

```
frontend/     Vite + React app
backend/      FastAPI prediction service
ml/           models, scalers, and selected features
datasets/     source tables
notebooks/    original training notebooks
legacy/       archived Streamlit script
scripts/      local dev helper
```

Each disease lives in its own folder under `ml/`:

```
ml/<disease>/
  models/          trained classifiers
  features/        columns kept for each model
  preprocessing/   scaler, and the heart-disease encoder
```

The breast cancer model files were originally named as Parkinson's models. They are stored under `ml/breast-cancer/` with names that match the classifier.

## Run it

Requirements: Node 20+, [uv](https://docs.astral.sh/uv/), and Python 3.12 (uv can install that interpreter).

```bash
./scripts/dev.sh
```

The app is at http://127.0.0.1:5173 and the API is at http://127.0.0.1:8000. API docs are at http://127.0.0.1:8000/api/docs.

To run the two processes yourself:

```bash
cd backend && uv sync --python 3.12 && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend && npm install && npm run dev
```

A production build of the frontend is served by the API when `frontend/dist` exists:

```bash
cd frontend && npm run build
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run build
```

## Models

Each system keeps the three classifiers from the original notebooks. The primary model is the one that screen used as its main result. Accuracies below are those reported test figures.

| System | Primary model | Also loaded |
| --- | --- | --- |
| Diabetes | Random forest, 75.324% | Logistic regression 70.129%, support vector classifier 69.480% |
| Heart disease | XGBoost, 100% | Random forest 100%, logistic regression 88.311% |
| Parkinson's | K-nearest neighbors, 100% | Random forest 94.871%, XGBoost 92.307% |
| Breast cancer | XGBoost, 97.368% | Logistic regression 97.368%, K-nearest neighbors 96.491% |

The support vector classifier was saved without probabilities, so that result has a label only.

Heart disease labels follow the measurements in `datasets/heart-disease.csv`. Recorded target `0` is the higher-risk group: more colored vessels, more exercise-induced angina, and more ST depression. The file has 1,025 rows and 302 unique records, which is why two of the reported scores are 100%.

Breast cancer class `0` is malignant and class `1` is benign.

## What a screen does

Enter the measurements, or load a recorded case from the dataset. The API scales the values the same way the notebooks did. Heart disease inputs are one-hot encoded before scaling. Each model then sees only its selected features. The page shows all three results and whether they agree.
