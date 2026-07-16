import json
import os
import re
from json import JSONDecoder
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    num_ctx=32768,
    num_predict=8192
)
# =====================================
# LOAD PAPERS
# =====================================
with open("output/Domian1/Run7/extracted_papers.json", "r", encoding="utf-8") as f:
    papers = json.load(f)


# =====================================
# SAFE JSON EXTRACTION
# =====================================

def extract_json(text):

    text = re.sub(r"```json|```", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    candidate = text[start:end+1]

    # -----------------------------------
    # Repair common LLM JSON mistakes
    # -----------------------------------

    # Missing comma after string before next key
    candidate = re.sub(
        r'(")\s*\n\s*(")',
        r'\1,\n\2',
        candidate
    )

    # Missing comma after } before next key
    candidate = re.sub(
        r'}\s*\n\s*(")',
        r'},\n\1',
        candidate
    )

    # Missing comma after ] before next key
    candidate = re.sub(
        r']\s*\n\s*(")',
        r'],\n\1',
        candidate
    )

    try:
        return json.loads(candidate)

    except json.JSONDecodeError as e:

        # Automatically fix a missing comma
        if "Expecting ',' delimiter" in str(e):

            fixed = candidate[:e.pos] + "," + candidate[e.pos:]

            try:
                print("✓ Fixed missing comma automatically.")
                return json.loads(fixed)

            except json.JSONDecodeError:
                pass

        print("\nJSON ERROR")
        print(e)

        err = e.pos
        print(candidate[max(0, err-200):err+200])

        return None


# =====================================
# PROCESS PAPERS
# =====================================
results = []

total = len(papers)

for i, paper in enumerate(papers, start=1):

    paper_id = paper.get("paper_id")
    filename = paper.get("filename")
    text = paper.get("text", "")[:20000]

    prompt = f"""


<document>

{text}

</document>

You are an expert research paper analyst.

Your task is to convert an academic paper into a highly structured knowledge base.

Extract ONLY information explicitly supported by the paper.

Return ONLY valid JSON.

RULES

- Do not hallucinate.
- Do not infer unsupported facts.
- Use null when unavailable.
- Keep summaries concise.
- Lists should contain short phrases.
- Preserve technical terminology.
- Maximum 2–3 sentences for textual summaries.
- Dont leave the year NULL
- Return ONLY JSON.

Extract metadata from the beginning of the paper whenever available.

Priority:

1. Title
2. Authors
3. Venue
4. Year
5. DOI

OUTPUT FORMAT

{{
  "paper_id": {paper_id},
  "filename": "{filename}",

  "metadata": {{
    "title": "",
    "authors": [],
    "year": "",
    "venue": "",
    "doi": "",
    "keywords": []
  }},

  "abstract": "",

  "research": {{
    "problem": "",
    "motivation": "",
    "objective": "",
    "research_questions": []
  }},

  "methodology": {{
    "summary": "",
    "algorithms": [],
    "models": [],
    "datasets": [],
    "features": [],
    "preprocessing": [],
    "training_strategy": "",
    "evaluation_metrics": []
  }},

  "experiments": {{
    "experimental_setup": "",
    "baselines": [],
    "results": "",
    "performance": {{
      "accuracy": "",
      "precision": "",
      "recall": "",
      "f1": "",
      "auc": ""
    }}
  }},

  "analysis": {{
    "contributions": [],
    "advantages": [],
    "limitations": [],
    "future_work": [],
    "applications": [],
    "research_gap": ""
  }},

  "sections": {{
    "introduction": "",
    "related_work": "",
    "methodology": "",
    "results": "",
    "discussion": "",
    "conclusion": ""
  }}
}}

IMPORTANT

Return EXACTLY ONE valid JSON object.

The output MUST be accepted by Python's json.loads().

Rules:

- No markdown.
- No JSON code fences.
- No comments.
- No explanations.
- No notes.
- No trailing commas.
- Do not omit commas.
- Use double quotes only.
- Do not output anything before the opening brace.
- Do not output anything after the closing brace.

If information is unavailable:

- string -> null
- list -> []


The JSON must exactly follow the schema above.

Begin directly with the JSON object.

"""

    response = llm.invoke(prompt)

    raw_output = response.content

    print(f"\nPaper {paper_id}")
    print("Output length:", len(raw_output))
    print(raw_output)

    parsed = extract_json(raw_output)

    if parsed is None:
        print(f"\nFailed to parse JSON for Paper {paper_id}")
        continue

    # ----------------------------
    # Validate required fields
    # ----------------------------
    required = [
        "paper_id",
        "filename",
        "metadata",
        "abstract",
        "research",
        "methodology",
        "experiments",
        "analysis",
        "sections"
    ]

    missing = [k for k in required if k not in parsed]

    if missing:
        print(f"\nPaper {paper_id} is incomplete.")
        print("Missing keys:", missing)
        continue

    # ----------------------------
    # Save parsed paper
    # ----------------------------
    results.append(parsed)

    print(f"{i}/{total} completed")

# =====================================
# SAVE OUTPUT
# =====================================
os.makedirs("output/Domian1/Run7", exist_ok=True)

with open("output/Domian1/Run7/base2.json", "w", encoding="utf-8") as f:
    json.dump(
        results,
        f,
        indent=4,
        ensure_ascii=False
    )

print("\nStructured Knowledge Base Generated Successfully")