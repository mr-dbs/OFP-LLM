"""Replays the reports recorded in real games through the relay with stand-in models (sensible, turtle, greedy,
garbage, and the plans the real model gave). Any error, malformed reply or missing order counts as a failure. A team on TAKE_TOWNS must be sent to take
towns (order 3), or to the flag of the town it holds (order 1, version 25).
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder, then the session logs."""
import json, sys, os, io, contextlib, collections, glob, traceback
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]; LOGS = sys.argv[3:]
import relay
NAMES = relay.TEAM_NAMES[1:]

def load(f):
    rows = [json.loads(l) for l in open(f, encoding="utf-8", errors="replace") if l.strip().startswith("{")]
    return [r for r in rows if isinstance(r.get("state"), dict) and "towns" in r["state"]]

def usable(state):
    need_team = ("vehicles", "gun_vehicles", "guns_manned", "immobile", "gun_out", "pos", "base_dist", "can_fight_armour", "has")
    return "base_pos" in state and all(all(k in t for k in need_team) or t["men"] < 1 for t in state["teams"])

def prepare(state):
    s = json.loads(json.dumps(state))
    s.setdefault("points", []); s.setdefault("points_sent", bool(s["points"])); s.setdefault("accidents", {}); s["mode"] = 1
    for p in s["points"]: p["pos"] = tuple(p["pos"])
    for t in s["towns"]:
        if "pos" in t: t["pos"] = tuple(t["pos"])
    if s.get("base_pos"): s["base_pos"] = tuple(s["base_pos"])
    for t in s["teams"]:
        if "pos" in t: t["pos"] = tuple(t["pos"])
        for k, v in (("no_gunner", 0), ("at_soldiers", 0), ("gun_vehicles", 0), ("vehicles", 0), ("guns_manned", 0), ("immobile", 0), ("gun_out", 0), ("known", True)):
            t.setdefault(k, v)
    s["kills"] = [k for k in s["kills"] if k.get("what")]
    return s

def situation_of(messages):
    text = messages[1]["content"]; return json.loads(text[text.index("CURRENT SITUATION:") + 18: text.rindex("Give your orders now.")])

def sensible(messages, think):
    sit = situation_of(messages); teams = sit["your_teams"]; heavy = sit["heavy_factory"]; out = {}
    threatened = [t["town"] for t in sit["your_towns"] if "hostile_seen_minutes_ago" in t]
    spare_def = sit["base_defenders_allowed"]
    for i, t in enumerate(teams):
        role = ("ARMOUR" if i < 4 else "INFANTRY_AT") if heavy else ("INFANTRY_AT" if i % 2 == 0 else "INFANTRY")
        if sit["enemy_aircraft_seen_recently"] and i == 7: role = "INFANTRY_AA"
        order, target = "TAKE_TOWNS", None
        if i == 6 and threatened: order, target = "DEFEND_TOWN", threatened[0]
        elif i == 5 and spare_def > 0: order = "DEFEND_BASE"
        elif i == 3 and sit["enemy_base"].startswith("found"): order = "ATTACK_BASE"
        elif i == 4 and sit["key_terrain"]: order, target = "HOLD_POINT", sit["key_terrain"][0]["name"]
        out[t["name"]] = {"role": role, "order": order, "target": target, "why": "stand-in"}
    return json.dumps({"situation": "stand-in", "teams": out, "intent": "stand-in"}), False

def bad(messages, think):
    sit = situation_of(messages)
    return json.dumps({"situation": "x", "teams": {t["name"]: {"role": "INFANTRY_AA", "order": "DEFEND_BASE", "target": None} for t in sit["your_teams"]}, "intent": "turtle"}), False

def greedy(messages, think):      # asks for every exception it can name, all the time
    sit = situation_of(messages); out = {}
    own = [t["town"] for t in sit["your_towns"]]
    for i, t in enumerate(sit["your_teams"]):
        order, target = [("DEFEND_TOWN", own[0] if own else "Nowhere"), ("HOLD_POINT", "kt1"), ("RETURN_TO_BASE", None), ("ATTACK_BASE", None),
                         ("DEFEND_BASE", None), ("DEFEND_TOWN", own[-1] if own else None), ("TAKE_TOWN", "Lany"), ("AUTO", None)][i % 8]
        out[t["name"]] = {"role": "ARMOUR" if sit["heavy_factory"] and i < 5 else "INFANTRY", "order": order, "target": target}
    return json.dumps({"situation": "x", "teams": out, "intent": "everything at once"}), False

def garbage(messages, think): return "Commander here. Hold the line!", False

total_fail = 0
for f in LOGS:
    rows = load(f); states = [prepare(r["state"]) for r in rows if usable(r["state"])]
    if len(states) < 5: print("%s: skipped (older log format, %d of %d reports usable)" % (os.path.basename(f), len(states), len(rows))); continue
    recorded = [(r["state"]["minute"], r["plan"]) for r in rows if r.get("plan")]
    def replayed(messages, think):
        sit = situation_of(messages); p = min(recorded, key=lambda x: abs(x[0] - sit["minute"]))[1]
        return json.dumps(p), False
    models = [("sensible", sensible), ("turtle", bad), ("greedy", greedy), ("garbage", garbage)] + ([("recorded plans", replayed)] if recorded else [])
    for label, model in models:
        relay.ask_model = model
        c = relay.MfctiCommander("East", os.path.join(TMP, "replay.jsonl"))
        out = io.StringIO(); errors = 0; bad_reply = 0; time_by = collections.Counter(); prev = 0; code3_missing = 0
        held_reports = 0
        for s in states:
            town_number = {t["name"]: k for k, t in enumerate(s["towns"])}
            try:
                with contextlib.redirect_stdout(out): rep = c.handle(s)
                r = json.loads(rep)
                ok = r[0] == 1 and len(r[1]) == 9 and all(len(e) == 4 and e[1] in (-1, 1, 2, 3, 4) and e[3] in (0, 1, 2, 3) for e in r[1]) and isinstance(r[2], str)
                if not ok: bad_reply += 1
                dt = s["minute"] - prev; prev = s["minute"]
                for i, n in enumerate(NAMES):
                    st = c.standing.get(n)
                    if st:
                        time_by[st["order"]] += dt
                        if st["order"] == "TAKE_TOWNS" and "barracks" in s["buildings"]:
                            hold = getattr(c, "holds", {}).get(n)          # version 25: a team that holds a town it took
                            want = [1, town_number[hold["town"]]] if hold else [3, -1]
                            if n in getattr(c, "counter", {}) and getattr(c, "counter_point", None) and (s.get("layout") or 0) >= 14:
                                want = [1, 200]                             # version 26: counterattacking at the base
                            if r[1][i + 1][1:3] != want: code3_missing += 1
                            if hold: held_reports += 1
            except Exception:
                errors += 1
                if errors == 1: print(traceback.format_exc())
        text = out.getvalue(); tot = sum(time_by.values()) or 1
        kicked = collections.Counter(l.split()[1].rstrip(":") for l in text.splitlines() if l.startswith("   KICK  ") and ": kick " in l)
        unfroze = sum(1 for l in text.splitlines() if l.startswith("   KICK  ") and "moving again" in l)
        fails = errors + bad_reply + code3_missing + text.count("NO LEGAL PLAN")
        total_fail += fails
        holds = sum(1 for l in text.splitlines() if l.startswith("   HOLD  ") and " holds " in l)
        print("%s | %-18s | reports %3d | model calls %3d | fallbacks %3d | NO LEGAL PLAN %d | errors %d | bad replies %d | put back %3d | ended %3d | kicks %s, moving again %d | holds %d (%d team-reports) | team-time: %s" % (
            os.path.basename(f)[8:23], label, len(states), c.model_calls, text.count("FALLBACK:"), text.count("NO LEGAL PLAN"), errors, bad_reply,
            text.count("(the plan asked otherwise)"), text.count("   RULE  ") - text.count("(the plan asked otherwise)"), dict(kicked) or "none", unfroze, holds, held_reports,
            ", ".join("%s %d%%" % (k, round(100 * v / tot)) for k, v in time_by.most_common())))
        if label == "sensible": open(os.path.join(TMP, "console_%s.txt" % os.path.basename(f)[8:23]), "w").write(text)
print("\nTOTAL failures across all replays:", total_fail)
sys.exit(1 if total_fail else 0)
