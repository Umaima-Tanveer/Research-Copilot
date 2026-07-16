import json
import os
import re

INPUT_JSON = "output/Domain2/review_paper.json"
OUTPUT_TEX = "output/Domain2/review_paper.tex"

AUTHOR_NAME = "Author Name"
AFFILIATION = "Department Name, Institution Name"
EMAIL = "email@example.com"


with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)


def clean_markdown(text):
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`+", "", text)

    return text.strip()


def latex_escape(text):

    if not text:
        return ""

    text = str(text)

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# Title
title = clean_markdown(data.get("title", "Review Paper"))
title = latex_escape(title)

# Abstract
abstract = clean_markdown(data.get("abstract", ""))
abstract = re.sub(r"(?i)^abstract", "", abstract).strip()
abstract = latex_escape(abstract)

# Keywords
keywords_raw = clean_markdown(data.get("keywords", ""))
keywords_raw = re.sub(r"(?i)keywords?:", "", keywords_raw)
keywords_raw = re.sub(r"\n+", ", ", keywords_raw)
keywords = latex_escape(keywords_raw)

# Sections
sections_tex = ""
sections = data.get("sections", {})

for sec_title, sec_content in sections.items():
    sec_title = clean_markdown(sec_title)
    content = clean_markdown(sec_content)

    # Remove duplicated Roman numeral/uppercase headings if present
    content = re.sub(r"^[IVXLC]+\.\s+[A-Z\s]+", "", content)
    content = latex_escape(content)

    sections_tex += f"\n\\section{{{sec_title}}}\n\n{content}\n"

# References Placeholder
# =========================
# References
# =========================

references = data.get("references", "")

references_tex = "\\begin{thebibliography}{99}\n\n"

if isinstance(references, str):

    refs = references.strip().split("\n")

else:

    refs = references

for i, ref in enumerate(refs, start=1):

    ref = clean_markdown(ref)
    ref = latex_escape(ref)

    # Remove leading [1], [2], ...
    ref = re.sub(r"^\[\d+\]\s*", "", ref)

    references_tex += f"\\bibitem{{ref{i}}}\n{ref}\n\n"

references_tex += "\\end{thebibliography}"

latex_document = rf"""
\documentclass[conference]{{IEEEtran}}

\usepackage{{cite}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{multirow}}
\usepackage{{url}}
\usepackage{{hyperref}}

\begin{{document}}

\title{{{title}}}

\author{{
    \IEEEauthorblockN{{{AUTHOR_NAME}}}
    \IEEEauthorblockA{{
        {AFFILIATION}\\
        {EMAIL}
    }}
}}

\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

\begin{{IEEEkeywords}}
{keywords}
\end{{IEEEkeywords}}

{sections_tex}
{references_tex}

\end{{document}}
"""

os.makedirs("output", exist_ok=True)

with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
    f.write(latex_document)

print(f"\nLaTeX generated:\n{OUTPUT_TEX}\n")