import json
import requests
import re
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0.2,
    num_ctx=32768
)


# =========================
# LLM CALL
# =========================
def call_llm(prompt):
    response = llm.invoke(prompt)
    return response.content.strip()


# =========================
# LOAD DATA
# =========================
def load_papers(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



# =========================
# CORPUS BUILDER
# =========================
def build_corpus(papers):

    abstracts = []
    keywords = []
    sections = []

    for paper in papers:

        abstracts.append(paper.get("abstract", ""))

        metadata = paper.get("metadata", {})
        keywords.extend(metadata.get("keywords", []))

        sec = paper.get("sections", {})

        for name, content in sec.items():
            if content:
                sections.append(f"{name}\n{content}")

    return {
        "abstracts": "\n\n".join(abstracts),
        "keywords": keywords,
        "sections": "\n\n".join(sections)
    }

# =========================
# FRONT MATTER
# =========================
def generate_front_matter(corpus):

    prompt = f"""
You are writing the front matter of an IEEE review paper.

Return ONLY valid JSON.

RULES

- No markdown
- No explanations
- No additional text

Generate:

1. A concise IEEE-style survey paper title (12–20 words)
2. A 200–250 word abstract
3. EXACTLY 6 keywords

OUTPUT FORMAT

{{
    "title": "",
    "abstract": "",
    "keywords": []
}}

TEXT

{corpus["abstracts"][:15000]}
"""

    raw = call_llm(prompt)

    try:
        return json.loads(raw)
    except:
        pass

    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(raw)
    except:
        pass

    start = raw.find("{")
    end = raw.rfind("}")

    if start != -1 and end != -1:
        try:
            return json.loads(raw[start:end+1])
        except:
            pass

    raise Exception("Front matter JSON parsing failed.")

# =========================
# SECTION GENERATION
# =========================
def generate_section(title, corpus):
    prompt = f"""
Write IEEE review section.

Section: {title}

RULES:
- 800–1000 words
- no bullet points
- no section headers inside text
- synthesis only

TEXT:
{corpus["sections"]}
"""
    return call_llm(prompt)


# =========================
# REFERENCES
# =========================
import re

def generate_references(papers):

    refs = []

    for i, paper in enumerate(papers, 1):

        meta = paper.get("metadata", {})

        title = meta.get("title", "Unknown")
        authors = meta.get("authors", [])
        year = meta.get("year", "n.d.")
        venue = meta.get("venue", "")
        doi = meta.get("doi", "")

        cleaned = []

        for author in authors:

            if isinstance(author, dict):
                author = author.get("name", "Unknown")

            # Remove affiliation numbers like 1, 2, 1,2, 3,4 etc.
            author = re.sub(r"\d+(,\d+)*$", "", str(author)).strip()

            cleaned.append(author)

        authors_str = ", ".join(cleaned)

        reference = f'[{i}] {authors_str}, "{title},"'

        if venue:
            reference += f" {venue},"

        if year:
            reference += f" {year}."

        if doi:
            reference += f" doi: {doi}."

        refs.append(reference)

    return "\n".join(refs)


# =========================
# PIPELINE
# =========================
def DAW_review_agent():
    papers = load_papers("output/Domain2/Review_base.json")
    corpus = build_corpus(papers)
    front = generate_front_matter(corpus)

    title = front["title"]
    abstract = front["abstract"]
    keywords = front["keywords"]

    section_titles = [
        "Introduction",
        "Literature Review",
        "Methodology Analysis",
        "Challenges and Future Directions",
        "Conclusion"
    ]

    sections = {}
    for sec in section_titles:
        sections[sec] = generate_section(sec, corpus)

    references = generate_references(papers)

    return {
        "title": title,
        "abstract": abstract,
        "keywords": keywords,
        "outline": section_titles,
        "sections": sections,
        "references": references
    }


# =========================
# SAVE
# =========================
def save_review_paper(result, output_file="output/Domain2/review_paper.json"):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    result = DAW_review_agent()
    save_review_paper(result)
    print("\nReview paper generated successfully.")