import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDiseases } from "../api";
import { formatAccuracy } from "../format";
import type { DiseaseSummary } from "../types";

export function HomePage() {
  const [diseases, setDiseases] = useState<DiseaseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    document.title = "MedBud";
    getDiseases(controller.signal)
      .then((items) => {
        setDiseases(items);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (caught instanceof Error && caught.name === "AbortError") {
          return;
        }
        setError(
          caught instanceof Error ? caught.message : "The prediction API is not responding.",
        );
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="home">
      <header className="page-head">
        <p className="eyebrow">Educational classifier demo</p>
        <h1>Four disease models, one place to try them.</h1>
        <p className="lede">
          MedBud runs the saved models for diabetes, heart disease, Parkinson's
          disease, and breast cancer. Each screen asks for the measurements
          that model was trained on and shows all three classifiers.
        </p>
      </header>

      {error ? (
        <p className="banner" role="alert">
          {error} Start the API on port 8000, then refresh this page.
        </p>
      ) : null}

      {diseases ? (
        <div className="card-grid">
          {diseases.map((disease, index) => {
            const primary = disease.models.find((model) => model.primary);
            return (
              <Link key={disease.id} className="system-card" to={`/${disease.id}`}>
                <span className="index">{String(index + 1).padStart(2, "0")}</span>
                <h2>{disease.shortName}</h2>
                <p>{disease.description}</p>
                <p className="meta">{disease.datasetNote}</p>
                {primary ? (
                  <p className="primary-line">
                    Primary model · {primary.name} · {formatAccuracy(primary.reportedAccuracy)}
                  </p>
                ) : null}
              </Link>
            );
          })}
        </div>
      ) : error ? null : (
        <p className="status">Loading the four systems…</p>
      )}

      <p className="disclaimer">
        MedBud compares entries with saved classifiers. It is not a medical
        device, and it does not diagnose or rule out disease. Nothing you type
        is stored.
      </p>
    </div>
  );
}
