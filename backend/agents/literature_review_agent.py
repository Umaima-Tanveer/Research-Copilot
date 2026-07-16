from langchain_ollama import ChatOllama
import json
import os
import re
import csv

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0
)

with open("output/Domian1/Run7/base1.json", "r", encoding="utf-8") as f:
    papers = json.load(f)

results = []


def extract_json(text):
    text = re.sub(r"```json|```", "", text).strip()

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


for paper in papers:

    paper_id = paper.get("paper_id")
    filename = paper.get("filename")

    prompt = f"""
You are an expert research paper analyst.

Using ONLY the structured information below, generate the literature review summary.

Return ONLY valid JSON.

Schema:
{{
    "paper_id": "{paper.get("paper_id")}",
    "filename": "{paper.get("filename")}",
    "title": "",
    "authors": [],
    "publication_year": "",
    "objective": "",
    "methodology": "",
    "dataset": "",
    "performance": "",
    "limitations": ""
}}

Structured Paper Information

Title:
{paper.get("title")}

Authors:
{paper.get("authors")}

Year:
{paper.get("year")}

Abstract:
{paper.get("abstract")}

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

Rules

- Use ONLY the information above.
- Do not hallucinate.
- If a field is missing, use "NOT MENTIONED".
- Return ONLY JSON.
"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    parsed = extract_json(raw)

    if parsed:
        results.append(parsed)
        print(f"Processed: {filename}")
    else:
        print(f"Failed: {filename}")
        print(raw)

json_path = "output/Domian1/Run7/literature_review.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("\n JSON Saved:", json_path)


csv_path = "output/Domian1/Run7/literature_review.csv"

csv_columns = [
    "Paper_Info",
    "Objective",
    "Methodology",
    "Dataset",
    "Performance",
    "Limitations"
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_columns)
    writer.writeheader()

    for item in results:

        title = item.get("title", "Unknown Title")
        authors = item.get("authors", [])

        # convert list of dicts → list of strings
        if isinstance(authors, list):

            cleaned_authors = []

            for a in authors:
                if isinstance(a, str):
                    cleaned_authors.append(a)

                elif isinstance(a, dict):
                    name = a.get("name") or a.get("author") or str(a)
                    cleaned_authors.append(name)

                else:
                    cleaned_authors.append(str(a))

            authors = ", ".join(cleaned_authors)

        year = item.get("publication_year", "Unknown Year")

        paper_info = f"{title} | {authors} | {year}"

        writer.writerow({
            "Paper_Info": paper_info,
            "Objective": item.get("objective", ""),
            "Methodology": item.get("methodology", ""),
            "Dataset": item.get("dataset", ""),
            "Performance": item.get("performance", ""),
            "Limitations": item.get("limitations", "")
        })

print(" CSV Saved:", csv_path)