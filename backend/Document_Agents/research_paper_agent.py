import json
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


# =====================================================
# LOAD JSON
# =====================================================

def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_front_matter(ctx):

    prompt = f"""
You are writing an IEEE research paper.

Review Paper

Title:
{ctx["review"]["title"]}

Abstract:
{ctx["review"]["abstract"]}

--------------------------------

User Proposal

{json.dumps(ctx["user"], indent=2)}

Generate ONLY valid JSON.

{{
    "title":"",
    "abstract":"",
    "keywords":[]
}}

Rules

- The research contribution comes ONLY from the user proposal.

- The review paper is only background knowledge.

- No markdown.

- No explanations.
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
        except json.JSONDecodeError:
            pass

    raise Exception("Front matter JSON parsing failed.")


def generate_section(section_name, ctx):

    if section_name == "Related Work":
        background = (
            ctx["review"]["sections"].get("Literature Review", "")
            or ctx["review"]["sections"].get("Related Work", "")
        )

    elif section_name == "Methodology":
        background = (
            ctx["review"]["sections"].get("Methodology Analysis", "")
            or ctx["review"]["sections"].get("Methodology", "")
        )

    elif section_name == "Results and Discussion":
        background = (
            ctx["review"]["sections"].get("Challenges and Future Directions", "")
        )

    else:
        background = ctx["review"]["abstract"]

    prompt = f"""
You are writing an IEEE research paper.

Section

{section_name}

------------------------------------------------

Review Paper

Title

{ctx["review"]["title"]}

Abstract

{ctx["review"]["abstract"]}

Review Background

{background}

------------------------------------------------

User Proposal

{json.dumps(ctx["user"], indent=2)}

------------------------------------------------

Rules

- Use the review paper ONLY as literature background.

- The proposed contribution comes ONLY from the user proposal.

- IEEE academic style.

- 800-1000 words.

- No bullet points.

- No section headers inside the text.
"""

    return call_llm(prompt)
# =====================================================
# VALIDATION
# =====================================================

def validate_user_input(user_json):

    required_fields = [
        "title",
        "problem_statement",
        "motivation",
        "methodology",
        "dataset",
        "results"
    ]

    for field in required_fields:

        if field not in user_json:
            raise ValueError(f"Missing field: {field}")


# =====================================================
# CONTEXT
# =====================================================

def build_context(review_json, user_json):

    return {

        "review": {

            "title": review_json.get("title", ""),

            "abstract": review_json.get("abstract", ""),

            "sections": review_json.get("sections", {}),

            "references": review_json.get("references", "")

        },

        "user": user_json

    }



# =====================================================
# MAIN AGENT
# =====================================================

def DAW_research_agent(review_path, user_input_path):

    review_json = load_json(review_path)

    user_json = load_json(user_input_path)

    validate_user_input(user_json)

    ctx = build_context(review_json, user_json)

    front = generate_front_matter(ctx)

    section_titles = [

        "Introduction",

        "Related Work",

        "Methodology",

        "Results and Discussion",

        "Conclusion"

    ]

    sections = {}

    for sec in section_titles:

        print(f"Generating {sec}...")

        sections[sec] = generate_section(sec, ctx)

    return {

        "title": front["title"],

        "abstract": front["abstract"],

        "keywords": front["keywords"],

        "outline": section_titles,

        "sections": sections,

        "references": ctx["review"]["references"]

    }



# =====================================================
# SAVE
# =====================================================

def save_output(
    result,
    output_path="output/Domain2/research_paper.json"
):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4,
            ensure_ascii=False
        )


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    result = DAW_research_agent(
        "output/Domain2/review_paper.json",
        "output/Domain2/user_research_input.json"
    )

    save_output(result)

    print("\nResearch paper generated successfully.")