import { formatProbability } from "../format";
import type { Prediction } from "../types";

type ResultPanelProps = {
  result: Prediction;
};

export function ResultPanel({ result }: ResultPanelProps) {
  const primary = result.results.find((item) => item.primary) ?? result.results[0];
  if (!primary) {
    return null;
  }
  const tone = primary.alert ? "alert" : "clear";

  return (
    <section className={`result result-${tone}`} aria-live="polite">
      <h2>{primary.label}</h2>
      {primary.alertProbability !== null ? (
        <p className="prob">{formatProbability(primary.alertProbability)}</p>
      ) : null}
      <ul className="model-list">
        {result.results.map((item) => (
          <li key={item.modelId} className={item.alert ? "is-alert" : "is-clear"}>
            <span>
              <strong>{item.modelName}</strong>
              <small>{item.label}</small>
            </span>
            {item.alertProbability !== null ? (
              <span>{formatProbability(item.alertProbability)}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
