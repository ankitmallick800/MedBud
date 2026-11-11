import type { DiseaseDetail, DiseaseSummary, Prediction } from "./types";

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (Array.isArray(body.detail)) {
      return body.detail.map(String).join(" ");
    }
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // The body was not JSON.
  }
  return `The request failed (${response.status}).`;
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<T>;
}

export function getDiseases(signal?: AbortSignal): Promise<DiseaseSummary[]> {
  return getJson("/api/diseases", signal);
}

export function getDisease(id: string, signal?: AbortSignal): Promise<DiseaseDetail> {
  return getJson(`/api/diseases/${id}`, signal);
}

export async function predictDisease(
  id: string,
  values: Record<string, number>,
): Promise<Prediction> {
  const response = await fetch(`/api/diseases/${id}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json() as Promise<Prediction>;
}
