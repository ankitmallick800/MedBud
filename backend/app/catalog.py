"""Descriptions, inputs, and model lineup for each prediction system."""

from dataclasses import dataclass, field


@dataclass
class Field:
    key: str
    label: str
    hint: str
    group: str
    widget: str = "number"
    step: float | None = None
    unit: str | None = None
    options: tuple[tuple[int, str], ...] = ()
    integer: bool = False
    minimum: float | None = None
    maximum: float | None = None
    placeholder: str | None = None


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    file_stem: str
    reported_accuracy: float
    primary: bool = False


@dataclass
class DiseaseSpec:
    id: str
    name: str
    short_name: str
    description: str
    dataset_file: str
    dataset_note: str
    note: str | None
    alert_value: int
    alert_phrase: str
    labels: dict[int, str]
    explanations: dict[int, str]
    preprocess: str
    target_column: str
    target_alert: int | str
    example_copy: dict[str, tuple[str, str]]
    fields: list[Field]
    models: list[ModelSpec]
    rename: dict[str, str] = field(default_factory=dict)


def number(
    key: str,
    label: str,
    hint: str,
    group: str,
    *,
    step: float | None = None,
    unit: str | None = None,
    integer: bool = False,
) -> Field:
    return Field(key, label, hint, group, step=step, unit=unit, integer=integer)


def choice(
    key: str,
    label: str,
    hint: str,
    group: str,
    options: tuple[tuple[int, str], ...],
) -> Field:
    return Field(key, label, hint, group, widget="select", integer=True, options=options)


DISCLAIMER = (
    "MedBud compares entries with saved classifiers. It is not a medical device, "
    "and it does not diagnose or rule out disease."
)


DIABETES = DiseaseSpec(
    id="diabetes",
    name="Diabetes prediction",
    short_name="Diabetes",
    description=(
        "Estimates whether a profile resembles the diabetic group in the Pima Indians "
        "diabetes data. Inputs are the eight measurements the saved models expect."
    ),
    dataset_file="diabetes.csv",
    dataset_note="768 records · 8 measurements · Pima Indians diabetes data",
    note=(
        "Zeros were sometimes used for a missing lab in this dataset, especially insulin "
        "and skin thickness. The saved models saw those zeros during training."
    ),
    alert_value=1,
    alert_phrase="a diabetic pattern",
    labels={1: "Diabetic pattern", 0: "No diabetic pattern"},
    explanations={
        1: "This profile is closer to the diabetic group in the training data.",
        0: "This profile is closer to the non-diabetic group in the training data.",
    },
    preprocess="scale",
    target_column="Outcome",
    target_alert=1,
    example_copy={
        "alert": ("Recorded diabetic case", "A dataset row whose recorded outcome is diabetic."),
        "clear": ("Recorded non-diabetic case", "A dataset row whose recorded outcome is not diabetic."),
    },
    fields=[
        number("Pregnancies", "Pregnancies", "Number of times pregnant.", "History", step=1, integer=True),
        number("Age", "Age", "Age in years.", "History", step=1, unit="years", integer=True),
        number(
            "DiabetesPedigreeFunction",
            "Diabetes pedigree",
            "Family-history score used in the original study.",
            "History",
            step=0.001,
        ),
        number("Glucose", "Glucose", "Plasma glucose concentration from a 2-hour test.", "Labs", step=1, unit="mg/dL"),
        number("BloodPressure", "Blood pressure", "Diastolic blood pressure.", "Labs", step=1, unit="mm Hg"),
        number("SkinThickness", "Skin thickness", "Triceps skinfold thickness.", "Labs", step=1, unit="mm"),
        number("Insulin", "Insulin", "2-hour serum insulin.", "Labs", step=1, unit="mu U/mL"),
        number("BMI", "BMI", "Body mass index.", "Labs", step=0.1, unit="kg/m²"),
    ],
    models=[
        ModelSpec("random-forest", "Random forest", "random_forest", 75.324, primary=True),
        ModelSpec("logistic-regression", "Logistic regression", "logistic_regression", 70.129),
        ModelSpec("svc", "Support vector classifier", "svc", 69.480),
    ],
)


HEART = DiseaseSpec(
    id="heart-disease",
    name="Heart disease prediction",
    short_name="Heart disease",
    description=(
        "Estimates heart-disease risk from the 13 clinical inputs used to train these models. "
        "Age, blood pressure, cholesterol, and the exercise test are entered as numbers. "
        "The remaining inputs are the coded categories from the dataset."
    ),
    dataset_file="heart-disease.csv",
    dataset_note="1,025 rows · 302 unique records · 13 clinical inputs",
    note=(
        "Higher risk is the recorded target 0. That group has more colored vessels, "
        "more exercise-induced angina, and more ST depression. Some copies of this file "
        "describe the target the other way around. These results follow the measurements. "
        "Reported scores near 100% come from a file that repeats the same patients."
    ),
    alert_value=0,
    alert_phrase="higher heart-disease risk",
    labels={0: "Higher risk", 1: "Lower risk"},
    explanations={
        0: "This profile matches the higher-risk group: more vessel disease, angina, and ST depression.",
        1: "This profile matches the lower-risk group in the training file.",
    },
    preprocess="heart",
    target_column="target",
    target_alert=0,
    example_copy={
        "alert": ("Recorded higher-risk case", "A dataset row in the higher-risk group (target 0)."),
        "clear": ("Recorded lower-risk case", "A dataset row in the lower-risk group (target 1)."),
    },
    fields=[
        number("age", "Age", "Age in years.", "Patient", step=1, unit="years", integer=True),
        choice("sex", "Sex", "Sex recorded in the dataset.", "Patient", ((0, "Female"), (1, "Male"))),
        choice(
            "cp",
            "Chest pain type",
            "Coded chest-pain category.",
            "Symptoms",
            (
                (0, "Typical angina"),
                (1, "Atypical angina"),
                (2, "Non-anginal pain"),
                (3, "Asymptomatic"),
            ),
        ),
        choice(
            "exang",
            "Exercise-induced angina",
            "Whether exercise brought on angina.",
            "Symptoms",
            ((0, "No"), (1, "Yes")),
        ),
        number("trestbps", "Resting blood pressure", "Blood pressure on admission.", "Resting tests", step=1, unit="mm Hg", integer=True),
        number("chol", "Serum cholesterol", "Serum cholesterol.", "Resting tests", step=1, unit="mg/dL", integer=True),
        choice(
            "fbs",
            "Fasting blood sugar",
            "Whether fasting blood sugar is above 120 mg/dL.",
            "Resting tests",
            ((0, "120 mg/dL or below"), (1, "Above 120 mg/dL")),
        ),
        choice(
            "restecg",
            "Resting ECG",
            "Resting electrocardiogram result.",
            "Resting tests",
            (
                (0, "Normal"),
                (1, "ST-T wave abnormality"),
                (2, "Probable left ventricular hypertrophy"),
            ),
        ),
        number("thalach", "Max heart rate", "Maximum heart rate achieved during the test.", "Exercise test", step=1, unit="bpm", integer=True),
        number("oldpeak", "ST depression", "ST depression induced by exercise, relative to rest.", "Exercise test", step=0.1),
        choice(
            "slope",
            "ST slope",
            "Slope of the peak exercise ST segment.",
            "Exercise test",
            ((0, "Upsloping"), (1, "Flat"), (2, "Downsloping")),
        ),
        choice(
            "ca",
            "Major vessels",
            "Number of major vessels colored by fluoroscopy.",
            "Imaging",
            tuple((value, str(value)) for value in range(5)),
        ),
        choice(
            "thal",
            "Thalassemia stress test",
            "Coded result. Normal is 2 in this file.",
            "Imaging",
            (
                (0, "Missing or unknown"),
                (1, "Fixed defect"),
                (2, "Normal"),
                (3, "Reversible defect"),
            ),
        ),
    ],
    models=[
        ModelSpec("xgboost", "XGBoost", "xgboost", 100, primary=True),
        ModelSpec("random-forest", "Random forest", "random_forest", 100),
        ModelSpec("logistic-regression", "Logistic regression", "logistic_regression", 88.311),
    ],
)


PARKINSONS = DiseaseSpec(
    id="parkinsons",
    name="Parkinson's disease prediction",
    short_name="Parkinson's",
    description=(
        "Estimates whether a voice recording resembles people with Parkinson's disease "
        "in the Oxford Parkinson's voice data. All 22 acoustic measures are required."
    ),
    dataset_file="parkinsons.csv",
    dataset_note="195 recordings · 22 voice measures · Oxford Parkinson's disease data",
    note="These inputs come from a sustained vowel recording, not from a clinic exam.",
    alert_value=1,
    alert_phrase="a parkinsonian voice pattern",
    labels={1: "Parkinsonian pattern", 0: "No parkinsonian pattern"},
    explanations={
        1: "This voice profile is closer to the Parkinson's group in the training data.",
        0: "This voice profile is closer to the healthy-control group in the training data.",
    },
    preprocess="scale",
    target_column="status",
    target_alert=1,
    example_copy={
        "alert": ("Recorded Parkinson's case", "A recording whose recorded status is Parkinson's disease."),
        "clear": ("Recorded healthy control", "A recording whose recorded status is a healthy control."),
    },
    fields=[
        number("MDVP:Fo(Hz)", "Average frequency", "Average vocal fundamental frequency.", "Frequency", unit="Hz"),
        number("MDVP:Fhi(Hz)", "Maximum frequency", "Maximum vocal fundamental frequency.", "Frequency", unit="Hz"),
        number("MDVP:Flo(Hz)", "Minimum frequency", "Minimum vocal fundamental frequency.", "Frequency", unit="Hz"),
        number("MDVP:Jitter(%)", "Jitter", "Variation in fundamental frequency, as a percentage.", "Jitter", unit="%"),
        number("MDVP:Jitter(Abs)", "Absolute jitter", "Absolute jitter in cycle-to-cycle frequency.", "Jitter"),
        number("MDVP:RAP", "RAP", "Relative amplitude perturbation.", "Jitter"),
        number("MDVP:PPQ", "PPQ", "Five-point period perturbation quotient.", "Jitter"),
        number("Jitter:DDP", "Jitter DDP", "Average absolute difference of period differences.", "Jitter"),
        number("MDVP:Shimmer", "Shimmer", "Variation in amplitude.", "Shimmer"),
        number("MDVP:Shimmer(dB)", "Shimmer in decibels", "Shimmer measured in decibels.", "Shimmer", unit="dB"),
        number("Shimmer:APQ3", "APQ3", "Three-point amplitude perturbation quotient.", "Shimmer"),
        number("Shimmer:APQ5", "APQ5", "Five-point amplitude perturbation quotient.", "Shimmer"),
        number("MDVP:APQ", "APQ", "Amplitude perturbation quotient.", "Shimmer"),
        number("Shimmer:DDA", "Shimmer DDA", "Average absolute difference of amplitude differences.", "Shimmer"),
        number("NHR", "Noise-to-harmonics", "Ratio of noise to tonal components.", "Noise and complexity"),
        number("HNR", "Harmonics-to-noise", "Ratio of tonal components to noise.", "Noise and complexity", unit="dB"),
        number("RPDE", "RPDE", "Recurrence period density entropy.", "Noise and complexity"),
        number("DFA", "DFA", "Detrended fluctuation analysis signal exponent.", "Noise and complexity"),
        number("spread1", "Spread 1", "Nonlinear measure of fundamental-frequency variation.", "Noise and complexity"),
        number("spread2", "Spread 2", "Nonlinear measure of fundamental-frequency variation.", "Noise and complexity"),
        number("D2", "D2", "Correlation dimension.", "Noise and complexity"),
        number("PPE", "PPE", "Pitch period entropy.", "Noise and complexity"),
    ],
    models=[
        ModelSpec("knn", "K-nearest neighbors", "knn", 100, primary=True),
        ModelSpec("random-forest", "Random forest", "random_forest", 94.871),
        ModelSpec("xgboost", "XGBoost", "xgboost", 92.307),
    ],
)


BREAST_RENAME = {
    "radius_mean": "mean radius",
    "texture_mean": "mean texture",
    "perimeter_mean": "mean perimeter",
    "area_mean": "mean area",
    "smoothness_mean": "mean smoothness",
    "compactness_mean": "mean compactness",
    "concavity_mean": "mean concavity",
    "concave points_mean": "mean concave points",
    "symmetry_mean": "mean symmetry",
    "fractal_dimension_mean": "mean fractal dimension",
    "radius_se": "radius error",
    "texture_se": "texture error",
    "perimeter_se": "perimeter error",
    "area_se": "area error",
    "smoothness_se": "smoothness error",
    "compactness_se": "compactness error",
    "concavity_se": "concavity error",
    "concave points_se": "concave points error",
    "symmetry_se": "symmetry error",
    "fractal_dimension_se": "fractal dimension error",
    "radius_worst": "worst radius",
    "texture_worst": "worst texture",
    "perimeter_worst": "worst perimeter",
    "area_worst": "worst area",
    "smoothness_worst": "worst smoothness",
    "compactness_worst": "worst compactness",
    "concavity_worst": "worst concavity",
    "concave points_worst": "worst concave points",
    "symmetry_worst": "worst symmetry",
    "fractal_dimension_worst": "worst fractal dimension",
}


def _breast_fields() -> list[Field]:
    mean_hints = {
        "mean radius": "Mean distance from the center to points on the perimeter.",
        "mean texture": "Standard deviation of gray-scale values.",
        "mean perimeter": "Mean perimeter of the cell nucleus.",
        "mean area": "Mean area of the cell nucleus.",
        "mean smoothness": "Mean local variation in radius lengths.",
        "mean compactness": "Mean compactness, perimeter squared over area.",
        "mean concavity": "Mean severity of concave portions of the contour.",
        "mean concave points": "Mean number of concave portions of the contour.",
        "mean symmetry": "Mean symmetry of the nucleus.",
        "mean fractal dimension": "Mean coastline approximation of the contour.",
    }
    error_hints = {
        "radius error": "Standard error of the radius.",
        "texture error": "Standard error of the texture.",
        "perimeter error": "Standard error of the perimeter.",
        "area error": "Standard error of the area.",
        "smoothness error": "Standard error of the smoothness.",
        "compactness error": "Standard error of the compactness.",
        "concavity error": "Standard error of the concavity.",
        "concave points error": "Standard error of the concave points.",
        "symmetry error": "Standard error of the symmetry.",
        "fractal dimension error": "Standard error of the fractal dimension.",
    }
    worst_hints = {
        "worst radius": "Largest radius measured for the nucleus.",
        "worst texture": "Largest texture value measured.",
        "worst perimeter": "Largest perimeter measured.",
        "worst area": "Largest area measured.",
        "worst smoothness": "Largest smoothness value measured.",
        "worst compactness": "Largest compactness value measured.",
        "worst concavity": "Largest concavity value measured.",
        "worst concave points": "Largest concave-points value measured.",
        "worst symmetry": "Largest symmetry value measured.",
        "worst fractal dimension": "Largest fractal-dimension value measured.",
    }
    fields: list[Field] = []
    for key, hint in mean_hints.items():
        fields.append(number(key, key.capitalize(), hint, "Mean"))
    for key, hint in error_hints.items():
        fields.append(number(key, key.capitalize(), hint, "Standard error"))
    for key, hint in worst_hints.items():
        fields.append(number(key, key.capitalize(), hint, "Worst"))
    return fields


BREAST = DiseaseSpec(
    id="breast-cancer",
    name="Breast cancer prediction",
    short_name="Breast cancer",
    description=(
        "Classifies a fine-needle aspirate profile as closer to malignant or benign "
        "cases in the Wisconsin diagnostic data. Class 0 is malignant."
    ),
    dataset_file="breast-cancer.csv",
    dataset_note="569 tumors · 30 nucleus measurements · Wisconsin diagnostic data",
    note="Malignant is the class the models label 0. Benign is class 1.",
    alert_value=0,
    alert_phrase="a malignant pattern",
    labels={0: "Malignant pattern", 1: "Benign pattern"},
    explanations={
        0: "This nucleus profile is closer to the malignant group in the training data.",
        1: "This nucleus profile is closer to the benign group in the training data.",
    },
    preprocess="scale",
    target_column="diagnosis",
    target_alert="M",
    example_copy={
        "alert": ("Recorded malignant case", "A dataset row whose recorded diagnosis is malignant."),
        "clear": ("Recorded benign case", "A dataset row whose recorded diagnosis is benign."),
    },
    fields=_breast_fields(),
    models=[
        ModelSpec("xgboost", "XGBoost", "xgboost", 97.368, primary=True),
        ModelSpec("logistic-regression", "Logistic regression", "logistic_regression", 97.368),
        ModelSpec("knn", "K-nearest neighbors", "knn", 96.491),
    ],
    rename=BREAST_RENAME,
)


DISEASES: tuple[DiseaseSpec, ...] = (DIABETES, HEART, PARKINSONS, BREAST)
