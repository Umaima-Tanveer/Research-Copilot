import os
import csv
import matplotlib.pyplot as plt

# ==========================================================
# CONFIG & PATHS
# ==========================================================
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RUNTIME_CSV = "output/runtime.csv"
RUNTIME_DOCS_CSV = "output/runtime_document.csv"

MANUAL_VS_RESEARCH_COPILOT = os.path.join(OUTPUT_DIR, "manual_vs_research_copilot.png")
MANUAL_VS_RESEARCH_COPILOT_PDF = os.path.join(OUTPUT_DIR, "manual_vs_research_copilot.pdf")

# ==========================================================
# ENGINE MAPPING DEFINITIONS
# ==========================================================
# Map individual scripts across both CSV files into 4 core engines
ENGINE_MAPPINGS = {
    "PDF_Ingestion": [
        "pdf_reader.py"
    ],
    "Database": [
        "ground_truth.py",
        "context_router.py"
    ],
    "ResearchEngine": [
        "research_map_agent.py",
        "literature_review_agent.py",
        "research_gap_agent.py",
        "contributions_agent.py",
        "research_question_agent.py",
        "Review_base.py",
        "review_paper_agent.py",
        "research_paper_agent.py"
    ],
    "GenerationEngine": [
        "latex_builder.py",
        "pdf_builder.py",
        "latex_research.py",
        "pdf_research.py"
    ]
}


def load_csv_data(filepath):
    """Loads CSV rows safely if file exists."""
    if not os.path.exists(filepath):
        print(f"⚠️️ Warning: File '{filepath}' not found.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_engine_averages():
    """Reads runtime CSVs and computes mean execution time (minutes) per engine."""
    rows_runtime = load_csv_data(RUNTIME_CSV)
    rows_docs = load_csv_data(RUNTIME_DOCS_CSV)
    
    script_totals = {}
    script_counts = {}

    def process_rows(rows):
        for row in rows:
            for key, val in row.items():
                if key in ["Run", "Timestamp", "Total_Runtime", "Peak_RAM_MB", "Avg_RAM_MB", "Avg_CPU_Percent"]:
                    continue
                try:
                    time_val = float(val)
                    script_totals[key] = script_totals.get(key, 0.0) + time_val
                    script_counts[key] = script_counts.get(key, 0) + 1
                except (ValueError, TypeError):
                    continue

    process_rows(rows_runtime)
    process_rows(rows_docs)

    # Calculate average time per script
    script_averages = {
        script: script_totals[script] / script_counts[script]
        for script in script_totals if script_counts[script] > 0
    }

    # Aggregate script averages into the 4 main component engines
    engine_averages = {}
    for engine, scripts in ENGINE_MAPPINGS.items():
        total_engine_time = sum(script_averages.get(script, 0.0) for script in scripts)
        engine_averages[engine] = total_engine_time

    return engine_averages


def generate_manual_vs_research_copilot(avg_data):
    """Calculates REU workload compression metrics and generates comparison charts."""
    # Multipliers reflecting task complexity and mental friction
    cognitive_weights = {
        "PDF_Ingestion": 1.2,     # Layout extraction & scanning
        "Database": 2.0,          # Serialization & target indexing
        "ResearchEngine": 3.8,    # Analytical load (synthesis, gap identification)
        "GenerationEngine": 1.5   # Formatted output & LaTeX compilation
    }

    # Estimated human time (minutes) for a researcher manually processing ~5 papers
    human_duration_baseline = {
        "PDF_Ingestion": 30.0,
        "Database": 60.0,
        "ResearchEngine": 240.0,
        "GenerationEngine": 45.0
    }

    research_copilot_reu = 0.0
    manual_reu = 0.0

    for engine_name, weight in cognitive_weights.items():
        actual_research_copilot_time = avg_data.get(engine_name, 0.0)
        baseline_human_time = human_duration_baseline.get(engine_name, 0.0)
        
        research_copilot_reu += actual_research_copilot_time * weight
        manual_reu += baseline_human_time * weight

    research_copilot_reu = round(research_copilot_reu, 2)
    manual_reu = round(manual_reu, 2)
    
    workload_efficiency_gain = (
        round(((manual_reu - research_copilot_reu) / manual_reu) * 100, 2)
        if manual_reu > 0 else 0.0
    )

    print("\n=======================================================")
    print("             REU MATHEMATICAL RUN LOGS")
    print("=======================================================")
    print(f"  • Cumulative Manual Baseline Workload : {manual_reu} REU")
    print(f"  • Cumulative Research Copilot Workload : {research_copilot_reu} REU")
    print(f"  • Core Workload Compression Ratio     : {workload_efficiency_gain}% Efficiency Improvement")
    print("=======================================================\n")

    labels = ["Manual Workflow\n(Modeled Load)", "Research Copilot\n(Automated Framework)"]
    values = [manual_reu, research_copilot_reu]

    plt.figure(figsize=(6, 5), dpi=300)
    bars = plt.bar(labels, values, color=["#7f7f7f", "#1f4e79"])
    plt.title("Workload Optimization via Research Effort Units (REU)", fontweight="bold", fontsize=11)
    plt.ylabel("REU Metric Scale (Time × Cognitive Load)")
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2, 
            h + (manual_reu * 0.01 if manual_reu > 0 else 1.0), 
            f"{h:.1f} REU", 
            ha="center", 
            va="bottom", 
            fontweight="bold"
        )

    plt.tight_layout()
    plt.savefig(MANUAL_VS_RESEARCH_COPILOT, dpi=300, bbox_inches="tight")
    plt.savefig(MANUAL_VS_RESEARCH_COPILOT_PDF, bbox_inches="tight")
    plt.close()
    
    print(f"✅ Charts successfully saved to '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    avg_data = compute_engine_averages()
    generate_manual_vs_research_copilot(avg_data)