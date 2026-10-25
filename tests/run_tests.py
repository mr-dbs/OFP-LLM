"""run_tests.py - runs every check on relay.py and on the mission scripts, and says what passed.

    python tests\\run_tests.py                 from C:\\ofp-llm, where relay.py is
    python tests\\run_tests.py --all-logs      also replays every session log in the logs folder (slower)

Nothing here talks to the game or to the model. The model is replaced by stand-ins, and every file the
tests write goes into a temporary folder. Uses only the Python standard library.
"""
import glob, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                         # the folder that holds relay.py
FIXTURES = os.path.join(HERE, "fixtures")
MISSIONS = os.path.join(os.path.expanduser("~"), "Documents", "Cold War Assault", "Missions")
MISSION_SCRIPTS = ["LLM/Init.sqs", "LLM/Report.sqs", "LLM/AirBuy.sqs", "LLM/TownWatch.sqs", "Main/UpdateIndependentAI.sqs",
                   "Main/UpdateCommanderAI.sqs", "Main/UpdateServer.sqs", "Main/UpdateVotes.sqs", "Main/PlaceSides.sqs"]


def run(label, script, *arguments):
    scratch = tempfile.mkdtemp(prefix="ofp_llm_tests_")
    command = [sys.executable, os.path.join(HERE, script)] + [a.replace("<scratch>", scratch) for a in arguments]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    passed = result.returncode == 0
    print("%-4s %-34s %s" % ("ok" if passed else "FAIL", label, lines[-1] if lines else "(no output)"))
    if not passed:
        for line in lines[:-1][-25:]:
            print("        " + line[:300])
        for line in result.stderr.splitlines()[-12:]:
            print("        " + line[:300])
    return passed


def main():
    if not os.path.exists(os.path.join(ROOT, "relay.py")):
        print("relay.py is not in %s. Put the tests folder next to relay.py." % ROOT)
        return 1
    version = next((l.split("=")[1].strip() for l in open(os.path.join(ROOT, "relay.py"), encoding="utf-8")
                    if l.startswith("VERSION = ")), "?")
    print("testing relay.py version %s in %s\n" % (version, ROOT))
    results = [
        run("rules from version 18", "test_rules_v18.py", ROOT, "<scratch>"),
        run("rules from version 19", "test_rules_v19.py", ROOT, "<scratch>"),
        run("rules from version 20", "test_rules_v20.py", ROOT, "<scratch>"),
        run("report layout 11 (version 21)", "test_rules_v21.py", ROOT, "<scratch>"),
        run("engine diagnostics (version 22)", "test_rules_v22.py", ROOT, "<scratch>"),
        run("engine level (version 23)", "test_rules_v23.py", ROOT, "<scratch>"),
        run("model deadline (version 24)", "test_rules_v24.py", ROOT, "<scratch>"),
        run("hold what you take (version 25)", "test_rules_v25.py", ROOT, "<scratch>"),
        run("base defence (version 26)", "test_rules_v26.py", ROOT, "<scratch>"),
        run("killer side, mortars (version 27)", "test_rules_v27.py", ROOT, "<scratch>"),
        run("mortar crew (version 28)", "test_rules_v28.py", ROOT, "<scratch>"),
        run("crew size, lift fire (version 29)", "test_rules_v29.py", ROOT, "<scratch>"),
        run("commander's guard (version 30)", "test_rules_v30.py", ROOT, "<scratch>"),
        run("one side on rules (version 31)", "test_rules_v31.py", ROOT, "<scratch>"),
        run("air response (version 32)", "test_rules_v32.py", ROOT, "<scratch>"),
        run("end to end", "test_end_to_end.py", ROOT, "<scratch>", os.path.join(FIXTURES, "damaged_report.jsonl")),
    ]
    logs = sorted(glob.glob(os.path.join(FIXTURES, "session_*.jsonl")))
    if "--all-logs" in sys.argv:
        logs += sorted(glob.glob(os.path.join(ROOT, "logs", "session_*.jsonl")))
    results.append(run("replay of %d logged games" % len(logs), "test_replays.py", ROOT, "<scratch>", *logs))

    scripts = []
    for folder in sorted(glob.glob(os.path.join(MISSIONS, "mfcti116a_*.noe")) + glob.glob(os.path.join(MISSIONS, "mfcti116a_*.Eden"))):
        scripts += [os.path.join(folder, *name.split("/")) for name in MISSION_SCRIPTS
                    if os.path.exists(os.path.join(folder, *name.split("/")))]
    if scripts:
        results.append(run("mission scripts (%d files)" % len(scripts), "sqs_check.py", *scripts))
    else:
        print("skip mission scripts: no mfcti116a_*.noe or .Eden folder in %s" % MISSIONS)

    print("\n%d of %d groups passed" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
