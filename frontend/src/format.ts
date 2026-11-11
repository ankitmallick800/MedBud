export function formatAccuracy(value: number): string {
  if (Number.isInteger(value)) {
    return `${value}%`;
  }
  return `${value.toFixed(3)}%`;
}

export function formatProbability(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function fieldDomId(diseaseId: string, key: string): string {
  return `${diseaseId}-${key.replace(/[^a-zA-Z0-9]+/g, "-")}`;
}
