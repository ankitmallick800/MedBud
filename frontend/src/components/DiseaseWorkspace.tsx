import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { predictDisease } from "../api";
import { fieldDomId } from "../format";
import type { DiseaseDetail, ExampleCase, FieldSchema, Prediction } from "../types";
import { ResultPanel } from "./ResultPanel";

type DiseaseWorkspaceProps = {
  disease: DiseaseDetail;
};

type FieldGroup = {
  name: string;
  fields: FieldSchema[];
};

function groupFields(fields: FieldSchema[]): FieldGroup[] {
  const groups: FieldGroup[] = [];
  for (const field of fields) {
    const current = groups[groups.length - 1];
    if (!current || current.name !== field.group) {
      groups.push({ name: field.group, fields: [field] });
    } else {
      current.fields.push(field);
    }
  }
  return groups;
}

function blankValues(fields: FieldSchema[]): Record<string, string> {
  const values: Record<string, string> = {};
  for (const field of fields) {
    values[field.key] = "";
  }
  return values;
}

function valuesFromExample(example: ExampleCase): Record<string, string> {
  const values: Record<string, string> = {};
  for (const [key, value] of Object.entries(example.values)) {
    values[key] = String(value);
  }
  return values;
}

function validate(disease: DiseaseDetail, values: Record<string, string>): string | null {
  for (const field of disease.fields) {
    const raw = values[field.key]?.trim() ?? "";
    if (raw === "") {
      return `${field.label} is required.`;
    }
    const number = Number(raw);
    if (!Number.isFinite(number)) {
      return `${field.label} must be a number.`;
    }
    if (field.integer && !Number.isInteger(number)) {
      return `${field.label} must be a whole number.`;
    }
    if (field.widget === "select") {
      const allowed = field.options.some((option) => option.value === number);
      if (!allowed) {
        return `${field.label} is not one of the listed choices.`;
      }
      continue;
    }
    if (field.minimum !== null && number < field.minimum) {
      return `${field.label} must be at least ${field.minimum}.`;
    }
    if (field.maximum !== null && number > field.maximum) {
      return `${field.label} must be at most ${field.maximum}.`;
    }
  }
  return null;
}

function payloadFrom(disease: DiseaseDetail, values: Record<string, string>): Record<string, number> {
  const payload: Record<string, number> = {};
  for (const field of disease.fields) {
    const number = Number(values[field.key]);
    payload[field.key] = field.integer ? Math.round(number) : number;
  }
  return payload;
}

type FieldControlProps = {
  diseaseId: string;
  field: FieldSchema;
  value: string;
  onChange: (key: string, value: string) => void;
};

function FieldControl({ diseaseId, field, value, onChange }: FieldControlProps) {
  const id = fieldDomId(diseaseId, field.key);
  const shared = {
    id,
    name: field.key,
    value,
    required: true,
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      onChange(field.key, event.target.value);
    },
  };

  return (
    <div className="field">
      <span className="label-row">
        <label htmlFor={id}>{field.label}</label>
        {field.unit ? <span className="unit">{field.unit}</span> : null}
      </span>
      {field.widget === "select" ? (
        <select {...shared}>
          <option value="">Select</option>
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          {...shared}
          type="number"
          inputMode={field.integer ? "numeric" : "decimal"}
          step={field.step ?? "any"}
          min={field.minimum ?? undefined}
          max={field.maximum ?? undefined}
          placeholder={field.placeholder ?? undefined}
        />
      )}
    </div>
  );
}

export function DiseaseWorkspace({ disease }: DiseaseWorkspaceProps) {
  const [values, setValues] = useState<Record<string, string>>(() => blankValues(disease.fields));
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const requestId = useRef(0);
  const resultRef = useRef<HTMLDivElement>(null);
  const groups = groupFields(disease.fields);

  useEffect(() => {
    if (!result || !window.matchMedia("(max-width: 980px)").matches) {
      return;
    }
    resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [result]);

  function updateField(key: string, next: string) {
    setValues((current) => ({ ...current, [key]: next }));
  }

  function loadExample(example: ExampleCase) {
    setValues(valuesFromExample(example));
    setResult(null);
    setError(null);
  }

  function clearForm() {
    setValues(blankValues(disease.fields));
    setResult(null);
    setError(null);
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const problem = validate(disease, values);
    if (problem) {
      setError(problem);
      setResult(null);
      return;
    }
    const id = requestId.current + 1;
    requestId.current = id;
    setPending(true);
    setError(null);
    try {
      const prediction = await predictDisease(disease.id, payloadFrom(disease, values));
      if (requestId.current !== id) {
        return;
      }
      setResult(prediction);
    } catch (caught) {
      if (requestId.current !== id) {
        return;
      }
      setResult(null);
      setError(caught instanceof Error ? caught.message : "The prediction failed.");
    } finally {
      if (requestId.current === id) {
        setPending(false);
      }
    }
  }

  return (
    <div className={result ? "workspace with-result" : "workspace"}>
      <form className="form-card" onSubmit={onSubmit} noValidate autoComplete="off">
        <div className="example-row">
          {disease.examples.map((example) => (
            <button
              key={example.id}
              type="button"
              className="button secondary"
              onClick={() => loadExample(example)}
            >
              {example.id === "alert" ? "Positive" : "Negative"}
            </button>
          ))}
          <button type="button" className="button ghost" onClick={clearForm}>
            Clear
          </button>
        </div>

        {groups.map((group) => (
          <fieldset key={group.name}>
            <legend>{group.name}</legend>
            <div className="fields">
              {group.fields.map((field) => (
                <FieldControl
                  key={field.key}
                  diseaseId={disease.id}
                  field={field}
                  value={values[field.key] ?? ""}
                  onChange={updateField}
                />
              ))}
            </div>
          </fieldset>
        ))}

        <div className="actions">
          <button type="submit" className="button" disabled={pending}>
            {pending ? "Predicting…" : "Predict"}
          </button>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>
      </form>

      {result ? (
        <div ref={resultRef}>
          <ResultPanel result={result} />
        </div>
      ) : null}
    </div>
  );
}
