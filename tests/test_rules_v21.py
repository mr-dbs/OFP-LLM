"""Unit tests for what was new in relay version 21: report layout 11 (what the game says about the vehicle a
leader sits in) and the count of towns handed over by the mission's capture-circle recount.
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
def tanks(n): return [["MFCTI116T80", "V", True, True, True, 0.8, True, True] for _ in range(n)]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, seat=1, speed=0, ready=True, far=0, height=0.0, hurt=0.0, role=0,
         stopped=False, engine=True, fuel=0.9, split=False, sub_order=True, follows=0, layout=11):
    men = len(kit) if kit and kit[0][1] != "V" else 3 * len(kit)
    near_m = ((x - T[0][2]) ** 2 + (y - T[0][3]) ** 2) ** .5
    entry = [name, False, role, 12, True, 100000, men, 0, near_m, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5,
             seat, speed, ready, far, height, hurt]
    if layout >= 11:
        entry += [stopped, engine, fuel, split, sub_order, follows]
    return entry
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
FIELD = (9000, 5600)
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]
def msg(minute, teams, layout=11, recounts=(0, 0, 0)):
    m = ["MFCTI", "East", minute * 60, 1, [[n, v, 0, x, y] for (n, v, x, y) in T],
         [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]],
         [team("Commander", LEADER, *BASE, seat=0, layout=layout)] + teams, [], [], [], [], layout]
    return m + [list(recounts)] if recounts is not None else m
def eight(layout=11, **kw):
    out = []
    for n in NAMES:
        kit = tanks(3) if n in NAMES[:4] else SQUAD
        args = dict(seat=1 if n in NAMES[:4] else 0, layout=layout); args.update(kw.get(n, {}))
        out.append(team(n, kit, *args.pop("at", FIELD), **args))
    return out
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(): return relay.MfctiCommander("East", os.path.join(TMP, "unit21.jsonl"))
def plan():
    return {"situation": "s", "intent": "i", "teams": {n: {"role": "ARMOUR" if n in NAMES[:4] else "INFANTRY", "order": "TAKE_TOWNS",
                                                             "target": None, "why": "test"} for n in NAMES}}
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:700])
def handle(c, m):
    s = state_of(m)
    with contextlib.redirect_stdout(io.StringIO()) as out: reply = c.handle(s)
    return reply, out.getvalue(), s

check("relay is version 21 or later", relay.VERSION >= 21, relay.VERSION)
check("the relay knows report layout 11 or later", relay.REPORT_LAYOUT >= 11, relay.REPORT_LAYOUT)

# 1. layout 11: the six values about the leader's vehicle, and the recount totals
s = state_of(msg(5, eight(Alpha=dict(stopped=True, engine=False, fuel=0.456, split=True, sub_order=True, follows=37.6)), recounts=(1, 4, 2)))
a = s["teams"][1]
check("layout 11 is read", s["layout"] == 11)
check("the vehicle's stop order, engine and fuel are read", (a["vehicle_stopped"], a["vehicle_engine_on"], a["vehicle_fuel"]) == (True, False, 0.46), a)
check("the commanding crewman's subgroup is read", (a["crew_split"], a["crew_order"], a["crew_follows_m"]) == (True, True, 38), a)
check("a leader on foot has no vehicle to describe", "crew_split" not in s["teams"][5] and "vehicle_fuel" not in s["teams"][5], s["teams"][5])
check("the recount totals are read as West, East, resistance", s["recounts"] == {"west": 1, "east": 4, "resistance": 2}, s.get("recounts"))
check("the older values are still read", a["leader_seat"] == "driver" and a["leader_ready"] is True and "leader_height" in a)

# 2. older and newer layouts
s10 = state_of(msg(5, eight(layout=10), layout=10, recounts=None))
check("a layout 10 report (12 parts) is still read, without the new values", s10["layout"] == 10 and "crew_split" not in s10["teams"][1] and "recounts" not in s10, s10["teams"][1])
c = commander(); _, out, _ = handle(c, msg(5, eight(layout=10), layout=10, recounts=None))
check("...with a note to install the newer mission scripts", "report layout 10" in out and "expects %d" % relay.REPORT_LAYOUT in out, out[-300:])
try:
    state_of(msg(5, eight(), layout=relay.REPORT_LAYOUT + 1)); refused = False
except ValueError as error:
    refused = "newer relay" in str(error)
check("a layout newer than the relay knows is refused", refused)
bad = msg(5, eight()); bad[12] = "broken"
check("a damaged recount entry is ignored, not fatal", "recounts" not in state_of(bad))
bad = msg(5, eight()); bad[12] = [0, None, 2]
check("...and so is one with an unreadable number in it", "recounts" not in state_of(bad) and len(state_of(bad)["teams"]) == 9)
try:
    state_of(msg(5, eight()) + ["too many"] * 6); refused = False
except ValueError:
    refused = True
check("a report with far more parts than any layout has is refused", refused)

holed = msg(5, eight()); holed[6][1][23] = None
h = state_of(holed)
check("one unreadable value among the new ones: they are left out for that team, the rest is read",
      "crew_split" not in h["teams"][1] and "vehicle_stopped" not in h["teams"][1] and "crew_split" in h["teams"][2] and h["teams"][1]["men"] == 9, h["teams"][1])
relay.LOG_DIR = TMP
r = relay.Relay(); r.log_path = os.path.join(TMP, "unit21_relay.jsonl"); open(r.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()) as out: raw_reply = r.handle(json.dumps(msg(5, eight(Alpha=dict(split=True)), recounts=(0, 3, 1))))
row = json.loads(open(r.log_path, encoding="utf-8").read().splitlines()[-1])
check("raw game text with layout 11 goes through the relay and is answered", json.loads(raw_reply)[0] == 1 and len(json.loads(raw_reply)[1]) == 9, raw_reply)
check("...and logged with the new values", row["state"]["teams"][1].get("crew_split") is True and row["state"]["recounts"]["east"] == 3, row["state"]["teams"][1])

# 3. the kick line says what the game reports about the vehicle
def kick_lines(**alpha):
    c = commander(); lines = []
    for m in range(9, 15):
        _, out, _ = handle(c, msg(m, eight(Alpha=dict(dict(at=(BASE[0] + 3000, BASE[1] + 2000), speed=0, ready=True), **alpha))))
        lines += [l for l in out.splitlines() if "KICK" in l and "Alpha" in l]
    return lines, c
lines, c = kick_lines(split=True, sub_order=True, follows=0, engine=True, fuel=0.9)
check("a team that stands still is still kicked after 4 minutes", len(lines) == 1, lines)
check("the kick line names the split crew and its order", lines and "different subgroup from the leader, which holds an order" in lines[0], lines)
check("...and the engine and fuel", lines and "engine on" in lines[0] and "fuel 90%" in lines[0], lines)
check("...and it is in the session log", any("different subgroup" in k for r in map(json.loads, open(c.log_path)) for k in r.get("kicks") or []))
lines, _ = kick_lines(split=False, sub_order=False, stopped=True, engine=False, fuel=0.0, follows=212)
check("no split, no order, stopped, engine off, no fuel, following a man 212 m away: all said",
      lines and all(w in lines[0] for w in ("told to stop", "engine off", "fuel 0%", "leader's subgroup, which holds no order", "follows a man 212 m away")), lines)
c = commander(); lines = []
for m in range(9, 15):
    _, out, _ = handle(c, msg(m, eight(layout=10, Alpha=dict(at=(BASE[0] + 3000, BASE[1] + 2000), speed=0, ready=True)), layout=10, recounts=None))
    lines += [l for l in out.splitlines() if "KICK" in l and "Alpha" in l]
check("a layout 10 report still gives a kick line, without the new words", len(lines) == 1 and "subgroup" not in lines[0] and "damaged" in lines[0], lines)

# 4. the board and the recount line
c = commander()
_, out, _ = handle(c, msg(5, eight(Alpha=dict(split=True)), recounts=(0, 0, 0)))
check("the board marks a leader whose vehicle answers to another subgroup", "his vehicle answers to another subgroup" in out, out[-600:])
check("the first report prints the recount totals", out.count("   COUNT ") == 1 and "0 towns to East" in out, out[-300:])
_, out, _ = handle(c, msg(6, eight(), recounts=(0, 0, 0)))
check("unchanged totals are not printed again", "   COUNT " not in out)
_, out, _ = handle(c, msg(7, eight(), recounts=(0, 2, 1)))
check("changed totals are printed", "handed 2 towns to East, 0 to West, 1 to the resistance" in out, out[-300:])
rows = [json.loads(l) for l in open(c.log_path)]
check("the totals are in the session log", rows[-1]["state"].get("recounts") == {"west": 0, "east": 2, "resistance": 1}, rows[-1]["state"].get("recounts"))

# 5. nothing else moved: the reply still has nine entries of four numbers
reply, _, _ = handle(commander(), msg(5, eight()))
r = json.loads(reply)
check("the reply format is unchanged", r[0] == 1 and len(r[1]) == 9 and all(len(e) == 4 for e in r[1]) and isinstance(r[2], str), reply)

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
