import subprocess
import time
import csv
import os
import threading
import psutil

from datetime import datetime

# ==========================================================
# CONFIG
# ==========================================================

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RUNTIME_CSV = os.path.join(OUTPUT_DIR, "runtime.csv")

# ==========================================================
# AGENTS PIPELINE
# ==========================================================

AGENTS = [
    "backend/rag/pdf_reader.py",

    "backend/Data_Store/ground_truth.py",
    "backend/Data_Store/context_router.py",

    "backend/agents/research_map_agent.py",
    "backend/agents/literature_review_agent.py",
    "backend/agents/research_gap_agent.py",
    "backend/agents/contributions_agent.py",
    "backend/agents/research_question_agent.py"
    # "backend/agents/review_paper_agent.py",
    # "backend/agents/research_paper_agent.py",

    # "backend/agents/latex_builder.py",
    # "backend/agents/pdf_builder.py",
    # "backend/agents/latex_research.py",
    # "backend/agents/pdf_research.py"
]

# ==========================================================
# SYSTEM MONITOR
# ==========================================================

peak_ram = 0
ram_samples = []
cpu_samples = []

monitor_running = False


def monitor_resources():

    global peak_ram

    process = psutil.Process(os.getpid())

    while monitor_running:

        try:
            ram_mb = process.memory_info().rss / (1024 * 1024)

            cpu_percent = psutil.cpu_percent(interval=None)

            ram_samples.append(ram_mb)
            cpu_samples.append(cpu_percent)

            peak_ram = max(peak_ram, ram_mb)

        except:
            pass

        time.sleep(1)


# ==========================================================
# GET RUN ID
# ==========================================================

def get_run_id():

    if not os.path.exists(RUNTIME_CSV):
        return 1

    with open(RUNTIME_CSV, "r", encoding="utf-8") as f:

        rows = list(csv.DictReader(f))

        if not rows:
            return 1

        return max(int(r["Run"]) for r in rows) + 1


# ==========================================================
# RUN SINGLE FILE
# ==========================================================

def run_script(path):

    script_name = os.path.basename(path)

    print(f"\n▶ {script_name}")

    start = time.perf_counter()

    result = subprocess.run(
        ["python", path],
        capture_output=True,
        text=True
    )

    end = time.perf_counter()

    if result.returncode != 0:

        print(result.stderr)

        raise RuntimeError(
            f"{script_name} failed"
        )

    runtime = round(
        (end - start) / 60,
        4
    )

    print(f"   Runtime: {runtime} min")

    return script_name, runtime


# ==========================================================
# SAVE CSV
# ==========================================================

def save_csv(run_id, runtime_data):

    file_exists = os.path.exists(RUNTIME_CSV)

    fieldnames = [
        "Run",
        "Timestamp"
    ] + list(runtime_data.keys())

    with open(
        RUNTIME_CSV,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        row = {
            "Run": run_id,
            "Timestamp": datetime.now().isoformat()
        }

        row.update(runtime_data)

        writer.writerow(row)


# ==========================================================
# MAIN
# ==========================================================

def main():

    global monitor_running

    print("\n===================================")
    print("RUNTIME EVALUATION STARTED")
    print("===================================\n")

    run_id = get_run_id()

    runtime_data = {}

    total_runtime = 0

    # --------------------------------
    # Start Resource Monitor
    # --------------------------------

    monitor_running = True

    monitor_thread = threading.Thread(
        target=monitor_resources,
        daemon=True
    )

    monitor_thread.start()

    # --------------------------------
    # Run All Scripts
    # --------------------------------

    for script in AGENTS:

        script_name, runtime = run_script(script)

        runtime_data[script_name] = runtime

        total_runtime += runtime

    # --------------------------------
    # Stop Monitor
    # --------------------------------

    monitor_running = False

    monitor_thread.join(timeout=2)

    # --------------------------------
    # Resource Statistics
    # --------------------------------

    avg_ram = (
        sum(ram_samples) / len(ram_samples)
        if ram_samples else 0
    )

    avg_cpu = (
        sum(cpu_samples) / len(cpu_samples)
        if cpu_samples else 0
    )

    runtime_data["Total_Runtime"] = round(
        total_runtime,
        4
    )

    runtime_data["Peak_RAM_MB"] = round(
        peak_ram,
        2
    )

    runtime_data["Avg_RAM_MB"] = round(
        avg_ram,
        2
    )

    runtime_data["Avg_CPU_Percent"] = round(
        avg_cpu,
        2
    )

    # --------------------------------
    # Save
    # --------------------------------

    save_csv(
        run_id,
        runtime_data
    )

    # --------------------------------
    # Summary
    # --------------------------------

    print("\n===================================")
    print("EVALUATION COMPLETE")
    print("===================================\n")

    print(f"Run ID           : {run_id}")
    print(f"Total Runtime    : {total_runtime:.4f} min")
    print(f"Peak RAM         : {peak_ram:.2f} MB")
    print(f"Average RAM      : {avg_ram:.2f} MB")
    print(f"Average CPU      : {avg_cpu:.2f} %")
    print(f"Saved CSV        : {RUNTIME_CSV}")


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":
    main()