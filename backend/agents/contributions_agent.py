import json
import os
import re
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0
)

with open("output/Domian1/Run7/literature_review.json", "r", encoding="utf-8") as f:
    literature_review = json.load(f)

with open("output/Domian1/Run7/research_gap.json", "r", encoding="utf-8") as f:
    research_gap = json.load(f)


prompt = f"""
You are a senior research scientist and innovation strategist.

You are given:

1. Literature Review (background knowledge)
2. Research Gaps (PRIMARY SOURCE)

Research gaps must drive the contribution generation.

Literature review should only be used to:
- understand existing approaches
- avoid proposing already solved ideas
- understand current limitations

The proposed contribution must directly address the identified research gap.

========================
YOUR TASK
========================
For EACH research gap:

- Propose ONE novel but realistic contribution
- Explain the technical idea
- Explain how it addresses the gap
- Explain implementation direction
- Ensure it is feasible as a future research project
- Avoid generic suggestions

========================
STRICT RULES
========================
- ONLY use gaps provided (do NOT invent new gaps)
- DO NOT hallucinate papers or results
- Each contribution MUST be grounded in a gap
- Keep outputs concise and technical
- Return ONLY valid JSON
- No explanations, no markdown
- Explain how the contribution can help in the impact properly and in detail.
- Contributions must be derived from the identified research gaps
- Do not simply restate the gap
- Do not propose contributions already present in the literature review
- Each contribution should represent a potential future research direction
- Contributions should be specific enough to form the basis of a research paper

========================
OUTPUT FORMAT
========================
{{
  "future_contributions": [
    {{
      "gap": "",

      "proposed_contribution": "",

      "technical_approach": "",

      "expected_impact": "",

      "implementation_feasibility": ""
    }}
  ]
}}


CONTRIBUTION GENERATION STRATEGY

Step 1:
Analyze the literature review to understand existing methods.

Step 2:
Analyze the research gaps.

Step 3:
For each gap, identify what is currently missing.

Step 4:
Propose a realistic contribution that could solve or reduce that gap.

Step 5:
Explain the expected impact and feasibility.

Return only JSON.

========================
INPUT DATA
========================

LITERATURE REVIEW:
{json.dumps(literature_review, indent=2)}

RESEARCH GAPS:
{json.dumps(research_gap, indent=2)}
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
    print("\nRAW OUTPUT:\n", raw_output)

    with open("data/Domian1/contributions_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw_output)

    exit()

with open("output/Domian1/Run7/contributions.json", "w", encoding="utf-8") as f:
    json.dump(parsed, f, indent=4, ensure_ascii=False)

print("\n Contributions Generated Successfully")