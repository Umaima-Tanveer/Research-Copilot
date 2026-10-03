import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found in llm_judge/.env"
    )

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "openai/gpt-oss-20b"


# ============================================================
# 2. DIRECTORIES
# ============================================================

GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"
SKB_DIR = BASE_DIR / "skb"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 3. PAPER MAPPING
# ============================================================
#
# Ground-truth files:
#
# paper1.json
# paper2.json
# ...
#
# SKB files may have different names.
#
# IMPORTANT:
# Put the ACTUAL SKB filename corresponding to each
# ground-truth file here.
#
# Example:
#
# "paper1.json": "IEEE_Access_2023.json"
#
# ============================================================

PAPER_MAPPING = {
    "paper1.json": "paper1.json",
    "paper2.json": "paper2.json",
    "paper3.json": "paper3.json",
    "paper4.json": "paper4.json",
    "paper5.json": "paper5.json",

    # Add paper6-paper10 when ready.
}


# ============================================================
# 4. FIELDS TO EVALUATE
# ============================================================

FIELDS = [
    "dataset",
    "accuracy",
    "limitation"
]


# ============================================================
# 5. LLM-AS-A-JUDGE PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an independent academic evaluator.

Your task is to compare ONE factual field extracted by an AI
research assistant against a manually verified human Ground Truth.

The Ground Truth is the reference standard.

Use ONLY the Ground Truth and AI Output provided.

Do NOT use outside knowledge.

Do NOT search for the paper.

Do NOT infer information that is not explicitly present.

SCORING:

1.0 = EXACT / SEMANTIC MATCH

The AI output correctly represents the Ground Truth fact.
Minor wording differences are acceptable.

0.5 = PARTIAL MATCH

The AI output captures the central fact correctly but misses
important context, conditions, or details.

There must not be a materially contradictory value.

0.0 = INCORRECT / MISSING / UNSUPPORTED

Use 0.0 when the AI output:
- contradicts the Ground Truth,
- gives an incorrect value,
- gives an incorrect dataset,
- gives an incorrect limitation,
- or does not contain the required factual information.

IMPORTANT:

For numerical results such as accuracy, evaluate the number
together with the associated metric, model/method, dataset,
and experimental condition when those details are part of
the Ground Truth.

For dataset information, consider important details such as
dataset name, source, number of participants/devices,
number of classes, and experimental conditions when present.

For limitations, evaluate whether the limitation expressed by
the AI output is actually supported by the Ground Truth.

Return ONLY valid JSON in exactly this format:

{
    "score": 1.0,
    "reasoning": "Short factual explanation."
}

The score MUST be exactly one of:

1.0
0.5
0.0
"""


# ============================================================
# 6. LOAD JSON
# ============================================================

def load_json(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# 7. EXTRACT PAPER ID
# ============================================================

def get_paper_id(ground_truth):

    return (
        ground_truth.get("paper_id")
        or ground_truth.get("file_name")
        or ground_truth.get("filename")
        or "Unknown Paper"
    )


# ============================================================
# 8. EXTRACT FACTS FROM GROUND TRUTH
# ============================================================

def extract_ground_truth_field(
    ground_truth,
    field
):
    """
    Extract the manually verified value.

    Supports both simple structures and nested structures.
    """

    # Direct field
    if field in ground_truth:
        return ground_truth[field]

    # Dataset
    if field == "dataset":

        dataset = ground_truth.get(
            "dataset"
        )

        if dataset is not None:
            return dataset

    # Accuracy / primary performance
    if field == "accuracy":

        if "accuracy" in ground_truth:
            return ground_truth["accuracy"]

        primary = ground_truth.get(
            "primary_performance"
        )

        if primary is not None:
            return primary

    # Limitation
    if field == "limitation":

        if "limitation" in ground_truth:
            return ground_truth["limitation"]

        analysis = ground_truth.get(
            "analysis"
        )

        if isinstance(analysis, dict):

            if "limitations" in analysis:
                return analysis["limitations"]

    return "NOT REPORTED"


# ============================================================
# 9. EXTRACT FACTS FROM SKB
# ============================================================

def extract_skb_field(
    skb,
    field
):
    """
    Extract the corresponding factual information from the
    ResearchCopilot SKB.

    This function deliberately checks common locations rather
    than passing the entire SKB to the judge.
    """

    # --------------------------------------------------------
    # DATASET
    # --------------------------------------------------------

    if field == "dataset":

        methodology = skb.get(
            "methodology",
            {}
        )

        if isinstance(methodology, dict):

            if "datasets" in methodology:
                return methodology["datasets"]

            if "dataset" in methodology:
                return methodology["dataset"]

        if "dataset" in skb:
            return skb["dataset"]

        return "MISSING"

    # --------------------------------------------------------
    # ACCURACY
    # --------------------------------------------------------

    if field == "accuracy":

        experiments = skb.get(
            "experiments",
            {}
        )

        if isinstance(experiments, dict):

            performance = experiments.get(
                "performance",
                {}
            )

            if isinstance(performance, dict):

                if "accuracy" in performance:
                    return performance["accuracy"]

            if "accuracy" in experiments:
                return experiments["accuracy"]

        if "accuracy" in skb:
            return skb["accuracy"]

        return "MISSING"

    # --------------------------------------------------------
    # LIMITATION
    # --------------------------------------------------------

    if field == "limitation":

        analysis = skb.get(
            "analysis",
            {}
        )

        if isinstance(analysis, dict):

            if "limitations" in analysis:
                return analysis["limitations"]

            if "limitation" in analysis:
                return analysis["limitation"]

        if "limitations" in skb:
            return skb["limitations"]

        if "limitation" in skb:
            return skb["limitation"]

        return "MISSING"

    return "MISSING"


# ============================================================
# 10. LLM JUDGE
# ============================================================

def get_judge_score(
    field_name,
    ground_truth,
    ai_output
):

    user_content = f"""
Evaluating Field: {field_name}

Human Ground Truth:
{json.dumps(ground_truth, ensure_ascii=False)}

AI System Extracted Output:
{json.dumps(ai_output, ensure_ascii=False)}

Compare the AI output against the Ground Truth.

Return ONLY:

{{
    "score": 1.0,
    "reasoning": "Short factual explanation."
}}
"""

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],

            response_format={
                "type": "json_object"
            },

            temperature=0
        )

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        # Remove accidental Markdown fences
        content = (
            content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        result = json.loads(content)

        score = float(
            result.get(
                "score",
                0.0
            )
        )

        reasoning = result.get(
            "reasoning",
            ""
        )

        if score not in [0.0, 0.5, 1.0]:

            raise ValueError(
                f"Invalid score returned: {score}"
            )

        return score, reasoning

    except Exception as e:

        print(
            f"      ERROR judging {field_name}: {e}"
        )

        return 0.0, f"Judge error: {e}"


# ============================================================
# 11. FIND SKB FILE
# ============================================================

def find_skb_file(gt_filename):

    # First use explicit mapping
    if gt_filename in PAPER_MAPPING:

        mapped_file = (
            SKB_DIR /
            PAPER_MAPPING[gt_filename]
        )

        if mapped_file.exists():
            return mapped_file

        print(
            f"   WARNING: Mapping points to missing file: "
            f"{mapped_file.name}"
        )

        return None

    # Otherwise try same filename
    same_name = SKB_DIR / gt_filename

    if same_name.exists():
        return same_name

    return None


# ============================================================
# 12. RUN EVALUATION
# ============================================================

print()
print("=" * 70)
print("ResearchCopilot LLM-as-a-Judge")
print("=" * 70)
print(f"Model: {MODEL}")
print()

evaluation_records = []


gt_files = sorted(
    GROUND_TRUTH_DIR.glob("*.json")
)


if not gt_files:

    raise FileNotFoundError(
        f"No JSON files found in {GROUND_TRUTH_DIR}"
    )


print(
    f"Ground Truth files found: {len(gt_files)}"
)

print()


# ============================================================
# PROCESS EACH PAPER
# ============================================================

for paper_number, gt_file in enumerate(
    gt_files,
    start=1
):

    print(
        f"[{paper_number}/{len(gt_files)}] "
        f"Processing: {gt_file.name}"
    )

    skb_file = find_skb_file(
        gt_file.name
    )

    if skb_file is None:

        print(
            "   SKIPPED: Corresponding SKB not found."
        )

        print()

        continue

    try:

        ground_truth = load_json(
            gt_file
        )

        skb = load_json(
            skb_file
        )

    except Exception as e:

        print(
            f"   ERROR loading JSON: {e}"
        )

        continue


    paper_id = get_paper_id(
        ground_truth
    )

    print(
        f"   Paper ID: {paper_id}"
    )

    print(
        f"   SKB: {skb_file.name}"
    )


    # --------------------------------------------------------
    # EVALUATE THREE FACTUAL FIELDS
    # --------------------------------------------------------

    for field in FIELDS:

        ground_truth_value = (
            extract_ground_truth_field(
                ground_truth,
                field
            )
        )

        ai_output_value = (
            extract_skb_field(
                skb,
                field
            )
        )


        print(
            f"   Evaluating: {field}"
        )


        score, reasoning = get_judge_score(
            field,
            ground_truth_value,
            ai_output_value
        )


        # ----------------------------------------------------
        # SAVE RECORD
        # ----------------------------------------------------

        domain = (
            "RFFI"
            if "RFFI" in paper_id.upper()
            else "Emotion Recognition"
        )


        evaluation_records.append({

            "Paper ID": paper_id,

            "Paper File": gt_file.name,

            "Domain": domain,

            "Target Field": field,

            "Ground Truth": json.dumps(
                ground_truth_value,
                ensure_ascii=False
            ),

            "AI Output": json.dumps(
                ai_output_value,
                ensure_ascii=False
            ),

            "Judge Score": score,

            "Reasoning": reasoning

        })


        print(
            f"      Score: {score}"
        )

        print(
            f"      Reason: {reasoning}"
        )

    print()


# ============================================================
# 13. CREATE DATAFRAME
# ============================================================

if not evaluation_records:

    raise RuntimeError(
        "No evaluation records were generated."
    )


df = pd.DataFrame(
    evaluation_records
)


# ============================================================
# 14. SAVE DETAILED RESULTS
# ============================================================

detailed_csv = (
    RESULTS_DIR /
    "golden_dataset_eval_results.csv"
)

df.to_csv(
    detailed_csv,
    index=False,
    encoding="utf-8"
)


# ============================================================
# 15. FIELD-LEVEL SUMMARY
# ============================================================

summary = (
    df
    .groupby("Target Field")["Judge Score"]
    .agg(
        [
            "count",
            "mean"
        ]
    )
    .reset_index()
)


summary.columns = [
    "Target Evaluation Field",
    "Number of Evaluations",
    "Mean Score"
]


summary["Mean Score (%)"] = (
    summary["Mean Score"] * 100
)


summary_csv = (
    RESULTS_DIR /
    "field_level_summary.csv"
)

summary.to_csv(
    summary_csv,
    index=False
)


# ============================================================
# 16. OVERALL SCORE
# ============================================================

overall_score = df[
    "Judge Score"
].mean()

print()
print("=" * 70)
print("STATISTICAL SUMMARY")
print("=" * 70)

print()

print(
    summary.to_string(
        index=False
    )
)

print()

print(
    f"Overall Mean Factual Alignment: "
    f"{overall_score:.4f}"
)

print(
    f"Overall Mean Factual Alignment: "
    f"{overall_score * 100:.2f}%"
)


# ============================================================
# 17. EXACT / PARTIAL / INCORRECT DISTRIBUTION
# ============================================================

exact_count = (
    df["Judge Score"] == 1.0
).sum()

partial_count = (
    df["Judge Score"] == 0.5
).sum()

incorrect_count = (
    df["Judge Score"] == 0.0
).sum()

total = len(df)


print()
print(
    "Score Distribution:"
)

print(
    f"EXACT     (1.0): "
    f"{exact_count}/{total} "
    f"({exact_count / total * 100:.2f}%)"
)

print(
    f"PARTIAL   (0.5): "
    f"{partial_count}/{total} "
    f"({partial_count / total * 100:.2f}%)"
)

print(
    f"INCORRECT (0.0): "
    f"{incorrect_count}/{total} "
    f"({incorrect_count / total * 100:.2f}%)"
)


# ============================================================
# 18. SAVE JSON RESULTS
# ============================================================

json_output = (
    RESULTS_DIR /
    "golden_dataset_eval_results.json"
)

with open(
    json_output,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        evaluation_records,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# 19. FINAL OUTPUT
# ============================================================

print()
print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)

print(
    f"Detailed CSV: {detailed_csv}"
)

print(
    f"Summary CSV:  {summary_csv}"
)

print(
    f"JSON Results:  {json_output}"
)

print("=" * 70)