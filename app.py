from flask import Flask, render_template, request
import pc_expert_system as backend

app = Flask(__name__)

# Kelompok pertanyaan untuk tampilan UI.
QUESTION_CATEGORIES = {
    "Power & Hardware": [
        "no_power_light",
        "loose_cable",
        "dead_outlet",
        "burning_smell",
    ],
    "Display": [
        "no_display",
        "beeps",
        "monitor_light_off",
    ],
    "Performance": [
        "slow",
        "many_startup_programs",
        "disk_full",
        "old_hdd",
    ],
    "Malware": [
        "popups",
        "unknown_programs",
    ],
    "Overheating": [
        "loud_fan",
        "hot_case",
        "dusty",
        "random_shutdown",
    ],
    "Network": [
        "no_internet",
        "other_devices_ok",
        "wifi_disconnected",
    ],
    "System Crash": [
        "blue_screen",
        "recent_driver_update",
    ],
}


@app.route("/")
def index():
    return render_template(
        "index.html",
        total_questions=len(backend.FACT_QUESTIONS),
        total_rules=len(backend.RULES),
    )


@app.route("/diagnosis", methods=["GET", "POST"])
def diagnosis():
    if request.method == "GET":
        return render_template(
            "diagnosis.html",
            categories=QUESTION_CATEGORIES,
            questions=backend.FACT_QUESTIONS,
        )

    # Ambil jawaban Ya dari formulir.
    facts = {
        key
        for key in backend.FACT_QUESTIONS
        if request.form.get(key) == "yes"
    }

    # Gunakan mesin inferensi dari backend asli.
    engine = backend.ForwardChainingEngine(backend.RULES)
    diagnoses, trace = engine.run(facts, verbose=False)

    # Siapkan jejak inferensi untuk ditampilkan di UI.
    trace_data = []

    for rule_id, conditions, conclusion in trace:
        trace_data.append({
            "rule_id": rule_id,
            "conditions": conditions,
            "conclusion": conclusion.replace(
                "diagnosis: ", ""
            ),
        })

    return render_template(
        "result.html",
        diagnoses=sorted(diagnoses),
        trace=trace_data,
        answered=len(request.form),
        total_questions=len(backend.FACT_QUESTIONS),
    )


if __name__ == "__main__":
    app.run(debug=True)