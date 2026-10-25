r"""Scorecard for a game you played against the LLM commander: how well did it notice you and answer you?

Usage:  python tools\scorecard.py SESSION [SESSION ...]     (logs\session_*.jsonl of the games you played)
        python tools\scorecard.py --side East SESSION        (the side the LLM commanded; East by default)

One card per game, from the commander's own reports. "The enemy" is your side: in a game you play, that is you
and the AI teams with you; the reports cannot tell you apart from them. Add your own two lines under each card:
did it make you change plans, and how threatening was it, 1 to 5."""
import json, sys, os, collections
args = sys.argv[1:]
side = "East"
if "--side" in args:
    i = args.index("--side"); side = args[i + 1].capitalize(); del args[i:i + 2]
AIR = ("attack helicopter", "attack plane", "transport helicopter")
def rows_of(path):
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.startswith("{"):
            continue
        try:
            x = json.loads(line)
        except ValueError:
            continue
        if x.get("side", side) == side and isinstance(x.get("state"), dict) and isinstance(x["state"].get("towns"), list):
            out.append(x)
    return out
for path in args:
    rows = rows_of(path)
    if not rows:
        print("\n%s: no reports for %s" % (os.path.basename(path), side)); continue
    first_seen = first_air = first_air_wave = None
    seen_reports = 0
    waves, base_alarms, hunters = [], [], set()
    our_losses_to_enemy = collections.Counter()
    for x in rows:
        st, minute = x["state"], x["state"]["minute"]
        enemy = [s for s in st["seen"] if s["whose"] == "enemy"]
        if enemy:
            seen_reports += 1
            first_seen = minute if first_seen is None else first_seen
        if first_air is None and any(s["class"] in AIR for s in enemy):
            first_air = minute
        notes = x.get("defence") or []
        for n in notes:
            if n.startswith("AIR THREAT: ") and "seen at" in n:
                waves.append(minute)
                first_air_wave = minute if first_air_wave is None else first_air_wave
            if n.startswith("BASE UNDER FIRE"):
                base_alarms.append(minute)
        if x.get("air_hunter"):
            hunters.add(x["air_hunter"])
        for k in st.get("killers", []):
            our_losses_to_enemy[k["what"]] += 1
    last = rows[-1]["state"]
    ours = sum(1 for t in last["towns"] if t["owner"] == "us")
    theirs = sum(1 for t in last["towns"] if t["owner"] == "enemy")
    plans = [x["seconds"] for x in rows if isinstance(x.get("seconds"), (int, float))]
    failed = sum(1 for x in rows if x.get("model_failed"))
    def m(v): return "never" if v is None else "minute %.0f" % v
    print("\n==== %s | %s commanded by the relay (version %s) | %d reports, minutes %.0f to %.0f" % (
        os.path.basename(path), side, rows[0].get("relay"), len(rows), rows[0]["state"]["minute"], last["minute"]))
    print("   noticed the enemy first:        %s; enemy in view in %d of %d reports (%.0f%%)" % (
        m(first_seen), seen_reports, len(rows), 100.0 * seen_reports / len(rows)))
    print("   enemy aircraft first seen:      %s" % m(first_air))
    print("   anti-air response waves:        %d%s" % (len(waves), (" (minutes %s)" % ", ".join("%.0f" % w for w in waves)) if waves else ""))
    if first_air is not None:
        print("   aircraft seen to first wave:    %s" % ("no wave" if first_air_wave is None else "%.1f minutes" % (first_air_wave - first_air)))
    print("   attack helicopter team:         %s" % (", ".join(sorted(hunters)) or "none"))
    print("   base alarms:                    %d" % len(base_alarms))
    print("   its men killed by the enemy:    %d%s" % (sum(our_losses_to_enemy.values()),
          (" (by %s)" % ", ".join("%s %d" % kv for kv in our_losses_to_enemy.most_common(4))) if our_losses_to_enemy else ""))
    print("   towns at the end:               %s %d, enemy %d, of %d" % (side, ours, theirs, len(last["towns"])))
    if plans or failed:
        print("   model plans:                    %d, median %.1f s, %d with no plan in time" % (
            len(plans), sorted(plans)[len(plans) // 2] if plans else 0, failed))
    print("   YOU: changed your plans because of it?  ___    threat, 1 to 5:  ___")
