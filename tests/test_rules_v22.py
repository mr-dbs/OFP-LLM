"""Unit tests for what was new in relay version 22: report layout 12, which carries three texts per team from
the engine's diagnostic commands (llmUnitInfo, llmGroupInfo) while the team's leader stands still.
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
VEH = "id=3 gl=1 sl=3 main=0 n=1 subs=2 stack=2 mode=WAIT cmd=ATTACK ctx=AUTO step=Wait dist=154 left=312 tgt=T80 tgtdead=0 state=BUSY plan=LEADERPLANNED away=1 sem=RED ammo=N armor=N health=N fuel=N asg=1 eng=1 noai=0 flee=0 want=3 ustop=0 engine=0 drv=1 pilot=1"
LEAD = "id=1 gl=1 sl=2 main=1 n=5 subs=2 stack=1 mode=PLANANDGO cmd=MOVE ctx=MISSION dist=2049 state=INCARGO plan=NONE away=0 sem=RED ammo=N armor=N health=N fuel=N asg=0 eng=0 noai=0 flee=0"
GROUP = "sl=2 main=1 n=5 stack=1 mode=PLANANDGO cmd=MOVE ctx=MISSION dist=2049 state=BUSY / sl=3 main=0 n=1 stack=2 mode=WAIT cmd=ATTACK ctx=AUTO tgt=T80 tgtdead=0 state=BUSY"
def team(name, kit, x, y, seat=1, speed=0, ready=True, role=0, layout=12, diag=("", "", "")):
    men = len(kit) if kit and kit[0][1] != "V" else 3 * len(kit)
    near_m = ((x - T[0][2]) ** 2 + (y - T[0][3]) ** 2) ** .5
    entry = [name, False, role, 12, True, 100000, men, 0, near_m, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5,
             seat, speed, ready, 0, 0.0, 0.0]
    if layout >= 11: entry += [False, True, 0.9, False, True, 0]
    if layout >= 12: entry += list(diag)
    return entry
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
FIELD = (BASE[0] + 3000, BASE[1] + 2000)
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]
def msg(minute, teams, layout=12, mode=1, commander_diag=("", "", ""), has_diag=True):
    m = ["MFCTI", "East", minute * 60, mode, [[n, v, 0, x, y] for (n, v, x, y) in T],
         [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]],
         [team("Commander", LEADER, *BASE, seat=0, layout=layout, diag=commander_diag)] + teams, [], [], [], [], layout, [0, 0, 0]]
    return m + [has_diag] if layout >= 12 and has_diag is not None else m
def eight(layout=12, **kw):
    out = []
    for n in NAMES:
        kit = tanks(3) if n in NAMES[:4] else SQUAD
        args = dict(seat=1 if n in NAMES[:4] else 0, layout=layout); args.update(kw.get(n, {}))
        out.append(team(n, kit, *args.pop("at", FIELD), **args))
    return out
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(name="unit22.jsonl"): return relay.MfctiCommander("East", os.path.join(TMP, name))
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

check("relay is version 22 or later", relay.VERSION >= 22, relay.VERSION)
check("the relay knows report layout 12 or later", relay.REPORT_LAYOUT >= 12, relay.REPORT_LAYOUT)

# 1. layout 12: the three texts
s = state_of(msg(5, eight(Alpha=dict(diag=(VEH, LEAD, GROUP)))))
a = s["teams"][1]
check("layout 12 is read", s["layout"] == 12)
check("the three texts are kept as sent", a.get("diag") == {"vehicle": VEH, "leader": LEAD, "group": GROUP}, a.get("diag"))
check("a team that sent none has no entry", "diag" not in s["teams"][2])
check("the report says the game has the diagnostics", s.get("has_diag") is True)
check("the older values are still read", a.get("crew_split") is False and a["leader_seat"] == "driver" and s["recounts"]["east"] == 0, a)
w = relay.diag_words(a["diag"]["vehicle"])
check("the words can be read one by one", (w["cmd"], w["ctx"], w["tgt"], w["left"], w["sem"]) == ("ATTACK", "AUTO", "T80", "312", "RED"), w)
moving = state_of(msg(5, eight()))
check("a report in which nobody stood still still says the game has the diagnostics", moving.get("has_diag") is True and all("diag" not in t for t in moving["teams"]))
none = state_of(msg(5, eight(), has_diag=False))
check("a game without the commands says so in the report", none.get("has_diag") is False)
thirteen = state_of(msg(5, eight(), has_diag=None))
check("a 13-part layout 12 report is read and makes no claim either way", thirteen["layout"] == 12 and "has_diag" not in thirteen and thirteen["recounts"]["east"] == 0)
try:
    state_of(msg(5, eight()) + ["part"] * 6); refused = False
except ValueError:
    refused = True
check("a report with far more parts than any layout is refused", refused)
s11 = state_of(msg(5, eight(layout=11), layout=11))
check("a layout 11 report is still read, and makes no claim about diagnostics", s11["layout"] == 11 and "has_diag" not in s11 and "crew_split" in s11["teams"][1])
odd = state_of(msg(5, eight(Alpha=dict(diag=('cmd=MOVE "quoted"\nnext', 7, None)))))
check("a text with quotes or line breaks is cleaned; a value that is not text is left out",
      odd["teams"][1]["diag"] == {"vehicle": "cmd=MOVE 'quoted' next"}, odd["teams"][1].get("diag"))
long_text = state_of(msg(5, eight(Alpha=dict(diag=("x=1 " * 400, "", "y=2 " * 900)))))
check("an overlong text is cut: 600 characters for a unit, 2000 for the list of subgroups",
      len(long_text["teams"][1]["diag"]["vehicle"]) == 600 and len(long_text["teams"][1]["diag"]["group"]) == 2000)

# 2. the kick line carries the engine's words
c = commander(); lines = []
for m in range(9, 15):
    _, out, _ = handle(c, msg(m, eight(Alpha=dict(diag=(VEH, LEAD, GROUP)))))
    lines += [l for l in out.splitlines() if "KICK" in l and "Alpha" in l]
check("a team that stands still is kicked as before", len(lines) == 1, lines)
check("the kick line names the order at the front of the queue", lines and "Engine:" in lines[0] and "cmd=ATTACK ctx=AUTO" in lines[0], lines)
check("...and the leader's own subgroup and every subgroup", lines and "the leader himself [id=1" in lines[0] and "subgroups [sl=2" in lines[0], lines)
check("...and it is in the session log", any("cmd=ATTACK ctx=AUTO" in k for r in map(json.loads, open(c.log_path)) for k in r.get("kicks") or []))
rows = [json.loads(l) for l in open(c.log_path)]
check("the texts are in the logged state", rows[-1]["state"]["teams"][1]["diag"]["group"] == GROUP)
c = commander("unit22b.jsonl"); lines = []
for m in range(9, 15):
    _, out, _ = handle(c, msg(m, eight(Alpha=dict(diag=(LEAD, LEAD, "")))))
    lines += [l for l in out.splitlines() if "KICK" in l and "Alpha" in l]
check("when the leader commands his own vehicle the same text is not printed twice", lines and lines[0].count("id=1 gl=1") == 1, lines)
c = commander("unit22c.jsonl"); lines = []
for m in range(9, 15):
    _, out, _ = handle(c, msg(m, eight()))
    lines += [l for l in out.splitlines() if "KICK" in l and "Alpha" in l]
check("without the texts the kick line is as in version 21", len(lines) == 1 and "Engine:" not in lines[0] and "fuel 90%" in lines[0], lines)

# 3. the note when the game was not rebuilt
c = commander("unit22d.jsonl"); notes = []
for m in range(1, 8):
    _, out, _ = handle(c, msg(m, eight(), has_diag=False))
    notes.append("no engine diagnostics" in out)
check("a game without the commands: said once, on the first report", notes == [True] + [False] * 6, notes)
c = commander("unit22e.jsonl"); notes = []
for m in range(1, 8):
    _, out, _ = handle(c, msg(m, eight(), commander_diag=(LEAD, "", "") if m < 3 else ("", "", "")))
    notes.append("no engine diagnostics" in out)
check("a game with the commands, and reports where everybody is moving: nothing is said", not any(notes), notes)
c = commander("unit22f.jsonl"); notes = []
for m in range(1, 8):
    _, out, _ = handle(c, msg(m, eight(layout=11), layout=11))
    notes.append("no engine diagnostics" in out)
check("an older report layout: nothing is said about diagnostics", not any(notes), notes)
o = relay.MfctiObserver("East", os.path.join(TMP, "unit22g.jsonl")); notes = []
for m in range(1, 6):
    with contextlib.redirect_stdout(io.StringIO()) as out: o.handle(state_of(msg(m, eight(), mode=0, has_diag=False)))
    notes.append("no engine diagnostics" in out.getvalue())
check("observer mode (the stock mission) without the commands: said once, on the first report", notes == [True, False, False, False, False], notes)
o = relay.MfctiObserver("East", os.path.join(TMP, "unit22h.jsonl")); said = False
for m in range(1, 6):
    with contextlib.redirect_stdout(io.StringIO()) as out: o.handle(state_of(msg(m, eight(), mode=0, commander_diag=(LEAD, "", ""))))
    said = said or "no engine diagnostics" in out.getvalue()
last = json.loads(open(o.log_path).read().splitlines()[-1])["state"]
check("observer mode with the commands: nothing is said, and the texts and the flag are logged",
      not said and last["teams"][0]["diag"]["vehicle"] == LEAD and last["has_diag"] is True)
check("the log line holds the exact text the trial script looks for", '"has_diag": true' in open(o.log_path).read())

# 4. raw game text and the reply
relay.LOG_DIR = TMP
r = relay.Relay(); r.log_path = os.path.join(TMP, "unit22_relay.jsonl"); open(r.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()): raw_reply = r.handle(json.dumps(msg(5, eight(Alpha=dict(diag=(VEH, LEAD, GROUP))))))
parsed = json.loads(raw_reply)
check("raw game text with layout 12 goes through the relay; the reply format is unchanged",
      parsed[0] == 1 and len(parsed[1]) == 9 and all(len(e) == 4 for e in parsed[1]), raw_reply)
asked = []
def model(messages, think):
    asked.append(messages[1]["content"]); return json.dumps(plan()), False
relay.ask_model = model
handle(commander("unit22i.jsonl"), msg(5, eight(Alpha=dict(diag=(VEH, LEAD, GROUP)))))
check("the engine's texts do not go to the model", asked and not any("ctx=AUTO" in a or "llmUnitInfo" in a for a in asked))

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
