import json
import os
from langchain_ollama import ChatOllama

# ---------------------------
# LLM INIT
# ---------------------------
llm = ChatOllama(
    model="qwen3:8b",
    temperature=0
)

# ---------------------------
# LOAD DATA
# ---------------------------
with open("output/Domian1/Run7/base1.json", "r", encoding="utf-8") as f:
    papers = json.load(f)

combined_context = ""

for i, paper in enumerate(papers):

    combined_context += f"""

========================
Paper {paper.get("paper_id")}
========================

Title:
{paper.get("title")}

Authors:
{paper.get("authors")}

Year:
{paper.get("year")}

Abstract:
{paper.get("abstract")}

Research Area:
{paper.get("research_area")}

Problem Statement:
{paper.get("problem_statement")}

Methodology:
{paper.get("methodology")}

Dataset:
{paper.get("dataset")}

Evaluation Metrics:
{paper.get("evaluation_metrics")}

Performance:
{paper.get("performance")}

Contribution:
{paper.get("contribution")}

Limitations:
{paper.get("limitations")}

Future Work:
{paper.get("future_work")}
"""

# ---------------------------
# STRICT PROMPT (VERY IMPORTANT)
# ---------------------------
prompt = f"""
YOU ARE A STRICT JSON GENERATION ENGINE.

CRITICAL RULES:
- Output ONLY valid JSON
- NO explanations
- NO markdown
- NO headings
- NO numbering
- NO extra text before or after JSON
- If you fail, output is INVALID

TASK:
Extract top 6–7 high-impact research gaps across ALL papers.

OUTPUT FORMAT (MUST FOLLOW EXACTLY):

{{
  "methodological": [
    {{
      "gap": "",
      "impact": "High|Medium|Low",
      "reason": "",
      "papers": []
    }}
  ],
  "theoretical": [],
  "empirical": [],
  "application": []
}}

RULES:
- max total gaps = 7
- no duplicates
- paper names only (no filenames, no IDs)
- keep reasoning short
- prioritize HIGH impact

STRUCTURED PAPER SUMMARIES:

{combined_context}
"""


# ---------------------------
# SAFE JSON PARSER (FIXED)
# ---------------------------
def extract_json(text: str):
    if not text:
        return None

    # remove code fences
    text = text.replace("```json", "").replace("```", "").strip()

    # find first valid JSON block safely
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    candidate = text[start:end+1]

    try:
        return json.loads(candidate)
    except:
        return None


# ---------------------------
# RETRY LOGIC (VERY IMPORTANT FOR STABILITY)
# ---------------------------
def get_llm_output(prompt, retries=2):
    for attempt in range(retries + 1):
        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        parsed = extract_json(raw_output)

        if parsed:
            return parsed

        # strengthen prompt on retry
        prompt = prompt + "\n\nSTRICT: Return ONLY valid JSON. No text allowed."

    return None


# ---------------------------
# EXECUTION
# ---------------------------
parsed = get_llm_output(prompt)

os.makedirs("output/Domian1/Run7", exist_ok=True)

if not parsed:
    print("\nJSON PARSING FAILED")
    print("\nRAW OUTPUT (LAST ATTEMPT):\n")
    print(raw_output)
    exit()

# ---------------------------
# SAVE OUTPUT
# ---------------------------
with open("output/Domian1/Run7/research_gap.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, indent=4, ensure_ascii=False)

print("\n Research Gap Analysis Completed")