"""
Rule-Based Expert System: Computer Troubleshooting
Inference method: Forward chaining (data-driven)
Conflict resolution: highest priority first, then first applicable
"""

# ------------------------------------------------------------------
# 1. KNOWLEDGE BASE: FACTS (symptoms the user can report)
# ------------------------------------------------------------------
FACT_QUESTIONS = {
    "no_power_light":       "Is the power light completely off / PC does not turn on?",
    "loose_cable":          "Is the power cable loose or unplugged?",
    "dead_outlet":          "Do other devices fail when plugged into the same outlet?",
    "burning_smell":        "Is there a burning smell from the PC?",
    "no_display":           "Is the screen blank (PC seems on)?",
    "beeps":                "Does the PC make beep sounds at startup?",
    "monitor_light_off":    "Is the monitor's power light off?",
    "slow":                 "Is the PC running very slowly?",
    "many_startup_programs": "Are there many programs that open at startup?",
    "disk_full":            "Is the disk almost full (>90%)?",
    "old_hdd":              "Does the PC use an old mechanical hard drive (HDD)?",
    "popups":               "Do you see unexpected pop-up ads?",
    "unknown_programs":     "Are there programs you did not install?",
    "loud_fan":             "Is the fan unusually loud?",
    "hot_case":             "Is the PC case very hot?",
    "dusty":                "Is the inside of the PC dusty?",
    "random_shutdown":      "Does the PC shut down randomly?",
    "no_internet":          "Is there no internet connection?",
    "other_devices_ok":     "Do other devices connect to the internet fine?",
    "wifi_disconnected":    "Is the PC disconnected from Wi-Fi?",
    "blue_screen":          "Do you get a blue screen (BSOD)?",
    "recent_driver_update": "Did you update a driver recently?",
}

# ------------------------------------------------------------------
# 2. KNOWLEDGE BASE: IF-THEN RULES (20 rules)
# Each rule: id, IF (set of conditions), THEN (new fact), priority
# Facts starting with "diagnosis:" are final conclusions.
# Other new facts are intermediate and may trigger further rules.
# ------------------------------------------------------------------
RULES = [
    # --- Power problems ---
    {"id": "R1",  "if": {"no_power_light", "loose_cable"},
     "then": "diagnosis: Loose power cable. Reconnect the cable firmly.", "priority": 2},
    {"id": "R2",  "if": {"no_power_light", "dead_outlet"},
     "then": "diagnosis: Faulty power outlet. Use a different outlet or power strip.", "priority": 2},
    {"id": "R3",  "if": {"no_power_light", "burning_smell"},
     "then": "diagnosis: Power supply (PSU) failure. Unplug immediately and replace the PSU.", "priority": 5},

    # --- Display problems ---
    {"id": "R4",  "if": {"no_display", "beeps"},
     "then": "memory_problem", "priority": 3},
    {"id": "R5",  "if": {"memory_problem"},
     "then": "diagnosis: RAM not seated or faulty. Reseat the RAM sticks or replace them.", "priority": 3},
    {"id": "R6",  "if": {"no_display", "monitor_light_off"},
     "then": "diagnosis: Monitor power or cable issue. Check the monitor power and video cable.", "priority": 2},

    # --- Performance problems ---
    {"id": "R7",  "if": {"slow", "many_startup_programs"},
     "then": "diagnosis: Too many startup programs. Disable unneeded startup apps.", "priority": 1},
    {"id": "R8",  "if": {"slow", "disk_full"},
     "then": "diagnosis: Low disk space. Delete unused files or add storage.", "priority": 2},
    {"id": "R9",  "if": {"slow", "old_hdd"},
     "then": "diagnosis: Slow mechanical drive. Upgrade to an SSD.", "priority": 1},

    # --- Malware ---
    {"id": "R10", "if": {"slow", "popups", "unknown_programs"},
     "then": "malware_suspected", "priority": 4},
    {"id": "R11", "if": {"popups", "unknown_programs"},
     "then": "malware_suspected", "priority": 4},
    {"id": "R12", "if": {"malware_suspected"},
     "then": "diagnosis: Possible malware. Run a full antivirus scan and uninstall unknown programs.", "priority": 4},

    # --- Overheating ---
    {"id": "R13", "if": {"loud_fan", "hot_case"},
     "then": "overheating", "priority": 3},
    {"id": "R14", "if": {"overheating", "dusty"},
     "then": "diagnosis: Dust blocking airflow. Clean the fans and vents.", "priority": 3},
    {"id": "R15", "if": {"overheating", "random_shutdown"},
     "then": "diagnosis: Thermal shutdown. Check the CPU cooler and replace thermal paste.", "priority": 4},

    # --- Network ---
    {"id": "R16", "if": {"no_internet", "other_devices_ok"},
     "then": "pc_network_problem", "priority": 2},
    {"id": "R17", "if": {"pc_network_problem", "wifi_disconnected"},
     "then": "diagnosis: PC Wi-Fi disconnected. Reconnect to Wi-Fi or restart the network adapter.", "priority": 2},
    {"id": "R18", "if": {"no_internet"},          # fires only if other devices are NOT ok (see below)
     "then": "router_check", "priority": 1},
    {"id": "R19", "if": {"router_check"},
     "then": "diagnosis: Router or ISP problem. Restart the router and contact your ISP.", "priority": 1},

    # --- Crashes ---
    {"id": "R20", "if": {"blue_screen", "recent_driver_update"},
     "then": "diagnosis: Faulty driver. Roll back the recently updated driver.", "priority": 3},
]


# ------------------------------------------------------------------
# 3. INFERENCE ENGINE: FORWARD CHAINING
# ------------------------------------------------------------------
class ForwardChainingEngine:
    def __init__(self, rules):
        self.rules = rules

    def run(self, initial_facts, verbose=True):
        working_memory = set(initial_facts)
        fired = set()          # rules already fired (termination criterion)
        trace = []             # explanation: (rule id, conditions, conclusion)
        step = 0

        while True:
            # Step 1: MATCH - build the conflict set
            conflict_set = [
                r for r in self.rules
                if r["id"] not in fired
                and r["if"].issubset(working_memory)
                and not self._blocked(r, working_memory)
            ]
            if not conflict_set:           # no more applicable rules -> stop
                break

            # Step 2: CONFLICT RESOLUTION - highest priority, then first listed
            rule = max(conflict_set, key=lambda r: (r["priority"], -self.rules.index(r)))

            # Step 3: FIRE the rule - add its conclusion to working memory
            step += 1
            fired.add(rule["id"])
            working_memory.add(rule["then"])
            trace.append((rule["id"], sorted(rule["if"]), rule["then"]))

            if verbose:
                print(f"  Step {step}: fired {rule['id']} "
                      f"(conflict set: {[r['id'] for r in conflict_set]})")

        diagnoses = [f.replace("diagnosis: ", "") for f in working_memory
                     if f.startswith("diagnosis:")]
        return diagnoses, trace

    @staticmethod
    def _blocked(rule, memory):
        # R18 is a default rule: only applies if other devices ALSO have no internet
        return rule["id"] == "R18" and "other_devices_ok" in memory


# ------------------------------------------------------------------
# 4. USER INTERFACE + EXPLANATION
# ------------------------------------------------------------------
def explain(trace):
    print("\n  Explanation (why):")
    for rid, conds, concl in trace:
        c = concl.replace("diagnosis: ", "DIAGNOSIS -> ")
        print(f"   {rid}: IF {' AND '.join(conds)} THEN {c}")


def show_result(diagnoses, trace):
    print("\n  RESULT:")
    if not diagnoses:
        print("   No diagnosis found. Please consult a technician.")
    for i, d in enumerate(sorted(diagnoses), 1):
        print(f"   {i}. {d}")
    explain(trace)


def interactive():
    print("=== PC Troubleshooting Expert System ===")
    print("Answer y/n.\n")
    facts = set()
    for key, question in FACT_QUESTIONS.items():
        if input(f"{question} (y/n): ").strip().lower().startswith("y"):
            facts.add(key)
    print("\nRunning inference...")
    engine = ForwardChainingEngine(RULES)
    diagnoses, trace = engine.run(facts)
    show_result(diagnoses, trace)


def demo():
    scenarios = {
        "Scenario 1: PC won't turn on, burning smell":
            {"no_power_light", "burning_smell"},
        "Scenario 2: Slow PC with pop-ups and unknown programs":
            {"slow", "popups", "unknown_programs", "old_hdd"},
        "Scenario 3: Loud, hot PC that shuts down randomly":
            {"loud_fan", "hot_case", "dusty", "random_shutdown"},
        "Scenario 4: No internet on any device":
            {"no_internet"},
        "Scenario 5: Blank screen with beeps":
            {"no_display", "beeps"},
    }
    engine = ForwardChainingEngine(RULES)
    for title, facts in scenarios.items():
        print("=" * 70)
        print(title)
        print("  Input facts:", sorted(facts))
        diagnoses, trace = engine.run(facts)
        show_result(diagnoses, trace)
        print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive()
    else:
        demo()