export type FieldOption = {
  value: number;
  label: string;
};

export type FieldSchema = {
  key: string;
  label: string;
  hint: string;
  group: string;
  widget: "number" | "select";
  step: number | null;
  unit: string | null;
  options: FieldOption[];
  integer: boolean;
  minimum: number | null;
  maximum: number | null;
  placeholder: string | null;
};

export type ModelInfo = {
  id: string;
  name: string;
  reportedAccuracy: number;
  primary: boolean;
  featureCount: number;
};

export type ExampleCase = {
  id: string;
  label: string;
  description: string;
  values: Record<string, number>;
};

export type DiseaseSummary = {
  id: string;
  name: string;
  shortName: string;
  description: string;
  datasetNote: string;
  note: string | null;
  disclaimer: string;
  alertPhrase: string;
  models: ModelInfo[];
};

export type DiseaseDetail = DiseaseSummary & {
  fields: FieldSchema[];
  examples: ExampleCase[];
};

export type ModelResult = {
  modelId: string;
  modelName: string;
  reportedAccuracy: number;
  primary: boolean;
  featureCount: number;
  prediction: number;
  label: string;
  explanation: string;
  alert: boolean;
  alertProbability: number | null;
};

export type Prediction = {
  diseaseId: string;
  results: ModelResult[];
  agreement: {
    alertVotes: number;
    total: number;
    unanimous: boolean;
    summary: string;
  };
};
