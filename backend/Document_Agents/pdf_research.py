import os
import shutil
import subprocess


TEX_FILE = "output/Domain2/research_paper.tex"
OUTPUT_DIR = "output/Domain2"
PDF_NAME = "research_paper.pdf"
PDF_PATH = os.path.join(OUTPUT_DIR, PDF_NAME)
LOG_FILE = os.path.join(OUTPUT_DIR, "research_paper.log")



def fix_unicode_latex(text):
    """
    Converts unsafe Unicode into LaTeX-safe equivalents
    """

    replacements = {
        "≤": r"$\leq$",
        "≥": r"$\geq$",
        "≈": r"$\approx$",
        "→": r"$\rightarrow$",
        "—": "--",
        "“": "\"",
        "”": "\"",
        "’": "'",
        "•": r"\item ",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def sanitize_full_text(text):
    """
    FINAL SAFETY LAYER:
    Removes any remaining illegal Unicode for LaTeX
    """

    text = fix_unicode_latex(text)

    # fallback: remove anything LaTeX cannot handle
    text = text.encode("ascii", "ignore").decode()

    return text


def check_environment():
    print("\n[CHECK] Validating environment...\n")

    if not os.path.exists(TEX_FILE):
        raise FileNotFoundError(f"LaTeX file not found: {TEX_FILE}")

    if shutil.which("pdflatex") is None:
        raise RuntimeError("pdflatex not installed")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[OK] Environment ready\n")


def compile_latex():
    print("=" * 60)
    print("COMPILING IEEE REVIEW PAPER")
    print("=" * 60)

    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={OUTPUT_DIR}",
        TEX_FILE,
    ]

    try:
        # Pass 1
        print("[PASS 1] compiling structure...")
        subprocess.run(command, check=True)

        # Pass 2
        print("[PASS 2] resolving references...")
        subprocess.run(command, check=True)

    except subprocess.CalledProcessError as e:
        # save logs
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(str(e))

        raise RuntimeError(
            f"\n LaTeX FAILED\nCheck log: {LOG_FILE}\n"
        )


def verify_pdf():
    print("\n[VERIFY] Checking PDF...\n")

    if not os.path.exists(PDF_PATH):
        raise RuntimeError("PDF NOT GENERATED")

    size = os.path.getsize(PDF_PATH) / 1024

    print("=" * 60)
    print(" IEEE PAPER GENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"PDF: {PDF_PATH}")
    print(f"Size: {size:.2f} KB")
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("IEEE PDF GENERATOR (FINAL FIXED VERSION)")
    print("=" * 60)

    check_environment()

    # IMPORTANT: sanitize TEX FILE BEFORE COMPILING
    with open(TEX_FILE, "r", encoding="utf-8") as f:
        tex_content = f.read()

    tex_content = sanitize_full_text(tex_content)

    with open(TEX_FILE, "w", encoding="utf-8") as f:
        f.write(tex_content)

    compile_latex()
    verify_pdf()

    print("\n[CLEANUP] Skipping cleanup for safety (optional)\n")


if __name__ == "__main__":
    try:
        main()

    except subprocess.CalledProcessError:
        print("\n LaTeX COMPILATION FAILED")
        print("Check output/research_paper.log")

    except Exception as e:
        print("\nERROR:")
        print(e)