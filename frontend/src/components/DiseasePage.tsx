import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getDisease } from "../api";
import type { DiseaseDetail } from "../types";
import { DiseaseWorkspace } from "./DiseaseWorkspace";

export function DiseasePage() {
  const { diseaseId = "" } = useParams();
  return <DiseaseLoader key={diseaseId} diseaseId={diseaseId} />;
}

function DiseaseLoader({ diseaseId }: { diseaseId: string }) {
  const [disease, setDisease] = useState<DiseaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getDisease(diseaseId, controller.signal)
      .then((detail) => {
        document.title = `${detail.shortName} · MedBud`;
        setDisease(detail);
      })
      .catch((caught: unknown) => {
        if (caught instanceof Error && caught.name === "AbortError") {
          return;
        }
        setError(caught instanceof Error ? caught.message : "Could not load this page.");
      });
    return () => controller.abort();
  }, [diseaseId]);

  if (error) {
    return (
      <p className="banner" role="alert">
        {error}
      </p>
    );
  }

  if (!disease) {
    return <p className="status">Loading…</p>;
  }

  return (
    <article>
      <h1>{disease.shortName}</h1>
      <DiseaseWorkspace key={disease.id} disease={disease} />
    </article>
  );
}
