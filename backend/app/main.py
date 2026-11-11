"""HTTP API for the four MedBud prediction systems."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.catalog import DISCLAIMER
from app.engine import REGISTRY, InputError, LoadedDisease, get_disease, predict

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "frontend" / "dist"


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class OptionOut(ApiModel):
    value: int
    label: str


class FieldOut(ApiModel):
    key: str
    label: str
    hint: str
    group: str
    widget: str
    step: float | None = None
    unit: str | None = None
    options: list[OptionOut] = []
    integer: bool = False
    minimum: float | None = None
    maximum: float | None = None
    placeholder: str | None = None


class ModelOut(ApiModel):
    id: str
    name: str
    reported_accuracy: float
    primary: bool
    feature_count: int


class ExampleOut(ApiModel):
    id: str
    label: str
    description: str
    values: dict[str, float | int]


class DiseaseSummary(ApiModel):
    id: str
    name: str
    short_name: str
    description: str
    dataset_note: str
    note: str | None
    disclaimer: str
    alert_phrase: str
    models: list[ModelOut]


class DiseaseDetail(DiseaseSummary):
    fields: list[FieldOut]
    examples: list[ExampleOut]


class PredictIn(ApiModel):
    values: dict[str, Any]


class ModelResultOut(ApiModel):
    model_id: str
    model_name: str
    reported_accuracy: float
    primary: bool
    feature_count: int
    prediction: int
    label: str
    explanation: str
    alert: bool
    alert_probability: float | None


class AgreementOut(ApiModel):
    alert_votes: int
    total: int
    unanimous: bool
    summary: str


class PredictionOut(ApiModel):
    disease_id: str
    results: list[ModelResultOut]
    agreement: AgreementOut


def _models(disease: LoadedDisease) -> list[ModelOut]:
    return [
        ModelOut(
            id=model.spec_id,
            name=model.name,
            reported_accuracy=model.reported_accuracy,
            primary=model.primary,
            feature_count=len(model.features),
        )
        for model in disease.models
    ]


def _summary(disease: LoadedDisease) -> DiseaseSummary:
    spec = disease.spec
    return DiseaseSummary(
        id=spec.id,
        name=spec.name,
        short_name=spec.short_name,
        description=spec.description,
        dataset_note=spec.dataset_note,
        note=spec.note,
        disclaimer=DISCLAIMER,
        alert_phrase=spec.alert_phrase,
        models=_models(disease),
    )


def _detail(disease: LoadedDisease) -> DiseaseDetail:
    summary = _summary(disease)
    return DiseaseDetail(
        **summary.model_dump(),
        fields=[
            FieldOut(
                key=item.key,
                label=item.label,
                hint=item.hint,
                group=item.group,
                widget=item.widget,
                step=item.step,
                unit=item.unit,
                options=[OptionOut(value=value, label=label) for value, label in item.options],
                integer=item.integer,
                minimum=item.minimum,
                maximum=item.maximum,
                placeholder=item.placeholder,
            )
            for item in disease.spec.fields
        ],
        examples=[
            ExampleOut(id=item.id, label=item.label, description=item.description, values=item.values)
            for item in disease.examples
        ],
    )


app = FastAPI(title="MedBud", version="1.0.0", docs_url="/api/docs", redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InputError)
def handle_input_error(_request, exc: InputError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors})


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "diseases": list(REGISTRY)}


@app.get("/api/diseases", response_model=list[DiseaseSummary])
def list_diseases() -> list[DiseaseSummary]:
    return [_summary(disease) for disease in REGISTRY.values()]


@app.get("/api/diseases/{disease_id}", response_model=DiseaseDetail)
def disease_detail(disease_id: str) -> DiseaseDetail:
    disease = get_disease(disease_id)
    if disease is None:
        raise HTTPException(status_code=404, detail="Unknown prediction system.")
    return _detail(disease)


@app.post("/api/diseases/{disease_id}/predict", response_model=PredictionOut)
def predict_disease(disease_id: str, payload: PredictIn) -> PredictionOut:
    disease = get_disease(disease_id)
    if disease is None:
        raise HTTPException(status_code=404, detail="Unknown prediction system.")
    return PredictionOut.model_validate(predict(disease, payload.values))


def _mount_frontend() -> None:
    index = DIST / "index.html"
    if not index.is_file():
        return

    @app.get("/", include_in_schema=False)
    def spa_index() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found.")
        candidate = (DIST / full_path).resolve()
        if candidate.is_file() and DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)


_mount_frontend()
