import json
import re
import requests
import os

from concurrent.futures import ThreadPoolExecutor, as_completed

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"

session = requests.Session()
# =====================================
# LLM CALL
# =====================================
def call_llm(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": 8192
        }
    }

    response = session.post(
        OLLAMA_URL,
        json=payload,
        timeout=600
    )

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()["response"].strip()


# =====================================
# SAFE JSON EXTRACTION
# =====================================
def extract_json(text):

    text = re.sub(
        r"```json|```",
        "",
        text
    ).strip()

    try:
        return json.loads(text)

    except:
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                return None

    return None

def process_paper(index, paper):
    result = extract_paper_intelligence(paper)
    return index, result

# =====================================
# PAPER INTELLIGENCE EXTRACTION
# =====================================
def extract_paper_intelligence(paper):

    paper_id = paper.get("paper_id")
    filename = paper.get("filename")

    # Use first part of paper to stay within context
    text = paper.get("text", "")[:15000]

    prompt = f"""
You are an expert research paper analyst.

Extract structured research intelligence.

Return ONLY valid JSON.

RULES:
- No markdown
- No explanations
- No hallucinations
- Use null if information is unavailable
- Keep fields concise
- Maximum 2-3 sentences per field
- Extract only from paper content

OUTPUT FORMAT:

{{
    "paper_id": "{paper_id}",
    "filename": "{filename}",

    "title": "",
    "authors": [],
    "year": null,

    "abstract": "",
    "keywords": [],

    "domain": "",
    "research_area": "",

    "problem_statement": "",

    "methodology": "",
    "dataset": "",

    "evaluation_metrics": [],

    "performance": "",

    "contribution": "",

    "limitations": "",

    "future_work": "",

    "task_type": "",

    "model_type": ""
}}

PAPER:
{text}
"""

    raw = call_llm(prompt)

    return extract_json(raw)


# =====================================
# RUN PIPELINE B
# =====================================
def run_pipeline_b(input_path, output_path):

    with open(input_path, "r", encoding="utf-8") as f:
        papers = json.load(f)

    results = [None] * len(papers)

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [
            executor.submit(process_paper, i, paper)
            for i, paper in enumerate(papers)
            if paper.get("text", "").strip()
        ]

        completed = 0
        total = len(futures)

        for future in as_completed(futures):

            try:
                idx, result = future.result()

                if result:
                    results[idx] = result

            except Exception as e:
                print(e)

            completed += 1

            if completed % 2 == 0 or completed == total:
                print(f"{completed}/{total} completed")

    results = [r for r in results if r]

    os.makedirs("data", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nPipeline B Saved → {output_path}")
    print(f"Total Papers Processed: {len(results)}")

# =====================================
# MAIN
# =====================================
if __name__ == "__main__":

    run_pipeline_b(
        "output/Domian1/Run7/extracted_papers.json",
        "output/Domian1/Run7/base1.json"
    )