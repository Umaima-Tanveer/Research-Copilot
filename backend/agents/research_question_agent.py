import json
import os
import re
from langchain_ollama import ChatOllama

# -----------------------
# LLM
# -----------------------
llm = ChatOllama(
    model="qwen3:8b",
    temperature=0
)

# -----------------------
# LOAD INPUTS
# -----------------------
with open("output/Domian1/Run7/research_gap.json", "r", encoding="utf-8") as f:
    research_gap = json.load(f)

with open("output/Domian1/Run7/contributions.json", "r", encoding="utf-8") as f:
    contributions = json.load(f)


gap_count = len(
    research_gap.get("methodological", []) +
    research_gap.get("theoretical", []) +
    research_gap.get("empirical", []) +
    research_gap.get("application", [])
)

contrib_count = len(contributions.get("future_contributions", []))

estimated_rq = max(5, min(15, gap_count + contrib_count))

prompt = f"""
You are a senior research scientist.

Generate HIGH-QUALITY RESEARCH QUESTIONS based on:

1. Research Gaps
2. Future Contributions

========================
STRICT RULES
========================
- Generate approximately {estimated_rq} research questions
- Minimum 5 questions
- Maximum 15 questions
- Number of questions should depend on the number of gaps and contributions
Each question MUST be directly traceable to:
- an identified research gap
OR
- a proposed future contribution

Questions should be:
- researchable
- measurable
- technically meaningful
- suitable for a research paper or thesis
- Avoid duplicates
- Avoid generic questions
- Avoid yes/no questions
- Avoid questions answerable without experimentation
- Avoid questions already solved in the literature
- DO NOT include explanations or motivations
- DO NOT include markdown
- ONLY valid JSON


PRIMARY:
Core questions that directly address major research gaps.

SECONDARY:
Supporting questions that investigate specific aspects of the primary questions.

NOVEL:
Forward-looking questions inspired by proposed future contributions.
========================
OUTPUT FORMAT (STRICT)
========================
{{
    "primary_research_questions": [
        {{
            "id": "RQ1",
            "question": "",

            "derived_from_gap": "",

            "derived_from_contribution": "",

            "paper_titles": []
        }}
    ],

    "secondary_research_questions": [
        {{
            "id": "RQ1",
            "question": "",

            "derived_from_gap": "",

            "derived_from_contribution": "",

            "paper_titles": []

        }}
    ],

    "novel_research_questions": [
        {{
            "id": "RQ1",
            "question": "",

            "derived_from_gap": "",

            "derived_from_contribution": "",

            "paper_titles": []

        }}
    ]
}}


QUESTION GENERATION STRATEGY

Step 1:
Analyze research gaps.

Step 2:
Analyze proposed future contributions.

Step 3:
Identify the most important unanswered research problems.

Step 4:
Convert these problems into clear research questions.

Step 5:
Ensure questions are aligned with the domain represented in the literature.
========================
INPUT DATA
========================

RESEARCH GAPS:
{json.dumps(research_gap, indent=2)}

FUTURE CONTRIBUTIONS:
{json.dumps(contributions, indent=2)}

"""

response = llm.invoke(prompt)
raw_output = response.content.strip()

def extract_json(text):
    text = re.sub(r"```json|```", "", text).strip()

    try:
        return json.loads(text)
    except:
        pass

    matches = re.findall(r"\{.*\}", text, re.DOTALL)
    for m in reversed(matches):
        try:
            return json.loads(m)
        except:
            continue

    return None

parsed = extract_json(raw_output)

os.makedirs("data", exist_ok=True)

if not parsed:
    print("\n JSON PARSING FAILED")
    print(raw_output)

    with open("data/research_questions_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw_output)
    exit()

with open("output/Domian1/Run7/research_questions.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, indent=4, ensure_ascii=False)

print("\n Research Questions Generated Successfully")
print("Saved to output/Domian1/Run7/research_questions.json")