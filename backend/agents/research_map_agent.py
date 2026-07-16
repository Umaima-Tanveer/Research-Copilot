import json
import os
import re
import itertools
import networkx as nx
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0
)

# =========================
# LOAD PAPERS
# =========================
with open("output/Domian1/Run7/base1.json", "r", encoding="utf-8") as f:
    papers = json.load(f)


# =========================
# JSON PARSER
# =========================
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


# =========================
# BUILD NODES
# =========================
nodes = []

for p in papers:
    nodes.append({
        "id": p.get("paper_id"),
        "title": p.get("title", ""),
        "year": p.get("year"),
        "dataset": p.get("dataset", ""),
        "methodology": p.get("methodology", ""),
        "task_type": p.get("task_type", ""),
        "contribution": p.get("contribution", "")
    })


# =========================
# BUILD EDGES
# =========================
edges = []

pairs = list(itertools.combinations(papers, 2))

total = len(pairs)

for i, (p1, p2) in enumerate(pairs, start=1):

    prompt = f"""
You are building a scientific research knowledge graph.

Compare TWO research papers using structured metadata.

Return ONLY valid JSON.

RELATION TYPES:
- extends
- improves
- compares
- contradicts
- uses_same_method
- uses_same_dataset
- unrelated

OUTPUT FORMAT:
{{
    "paper1": "{p1['paper_id']}",
    "paper2": "{p2['paper_id']}",
    "relation": "",
    "similarity": 0.0,
    "reason": "",
    "shared_concepts": []
}}

PAPER 1:
Title: {p1.get('title')}
Methodology: {p1.get('methodology')}
Dataset: {p1.get('dataset')}
Task: {p1.get('task_type')}
Contribution: {p1.get('contribution')}

PAPER 2:
Title: {p2.get('title')}
Methodology: {p2.get('methodology')}
Dataset: {p2.get('dataset')}
Task: {p2.get('task_type')}
Contribution: {p2.get('contribution')}
"""

    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    parsed = extract_json(raw_output)

    if parsed:
        edges.append(parsed)
    else:
        print(f"Failed to parse relation between Paper {p1['paper_id']} and Paper {p2['paper_id']}")

    print(f"{i}/{total} completed")


# =========================
# SAVE JSON
# =========================
os.makedirs("output/Domian1/Run7", exist_ok=True)

with open("output/Domian1/Run7/research_map.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "nodes": nodes,
            "edges": edges
        },
        f,
        indent=4,
        ensure_ascii=False
    )


# =========================
# BUILD GRAPH
# =========================
G = nx.DiGraph()

for node in nodes:
    G.add_node(
        node["id"],
        title=node["title"],
        year=node["year"]
    )

for edge in edges:
    G.add_edge(
        edge["paper1"],
        edge["paper2"],
        relation=edge.get("relation", ""),
        similarity=edge.get("similarity", 0),
        reason=edge.get("reason", "")
    )


# =========================
# SAVE IMAGE
# =========================
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 8))

pos = nx.spring_layout(G, seed=42)

labels = nx.get_edge_attributes(G, "relation")

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=2000,
    node_color="lightblue"
)

nx.draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=labels
)

plt.title("Research Paper Knowledge Map")

plt.savefig("output/Domian1/Run7/research_graph.png")

plt.close()

print("\nResearch Map Generated Successfully")