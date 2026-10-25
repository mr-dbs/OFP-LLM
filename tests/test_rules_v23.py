"""Unit tests for what was new in relay version 23: report layout 13, in which the mission says which of the
project's engine changes the game has (0 none, 1 the diagnostic commands, 2 also the fix for a driver left
with a dead commander's driving order). No rule of the commander changed in version 23.
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
# A lone driver holding his dead commander's driving order, as the game of 9 October printed it, plus the new word mm=.
STUCK = ("id=1 gl=1 sl=1 main=1 n=10 subs=1 stack=0 mode=WAIT cmd=NONE state=WAIT plan=VEHICLE away=0 sem=YELLOW ammo=N armor=L "
         "health=N fuel=N asg=0 eng=1 noai=1 flee=0 want=5 ustop=0 engine=0 drv=1 pilot=1 mm=MOVE")
GROUP = "sl=1 main=1 n=10 stack=0 mode=WAIT cmd=NONE state=WAIT"
def team(name, kit, x, y, seat=1, speed=0, ready=True, role=0, layout=13, diag=("", "", "")):
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
NOTHING = object()
def msg(minute, teams, layout=13, mode=1, has_diag=True, level=2):
    """A report as the mission sends it. level=NOTHING leaves the 15th part out, as report script 12 did."""
    m = ["MFCTI", "East", minute * 60, mode, [[n, v, 0, x, y] for (n, v, x, y) in T],
         [900000, HEAVY, True, 0, False, -1, BASE[0], BASE[1]],
         [team("Commander", LEADER, *BASE, seat=0, layout=layout)] + teams, [], [], [], [], layout, [0, 0, 0], has_diag]
    return m if level is NOTHING else m + [level]
def eight(layout=13, **kw):
    out = []
    for n in NAMES:
        kit = tanks(3) if n in NAMES[:4] else SQUAD
        args = dict(seat=1 if n in NAMES[:4] else 0, layout=layout); args.update(kw.get(n, {}))
        out.append(team(n, kit, *args.pop("at", FIELD), **args))
    return out
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(name): return relay.MfctiCommander("East", os.path.join(TMP, name))
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
LEVEL_NOTE = "the game's engine is at level"
DIAG_NOTE = "no engine diagnostics"

check("relay is version 23 or later", relay.VERSION >= 23, relay.VERSION)
check("the relay knows report layout 13 or later", relay.REPORT_LAYOUT >= 13, relay.REPORT_LAYOUT)
check("the relay expects engine level 2", relay.ENGINE_LEVEL == 2, relay.ENGINE_LEVEL)

# 1. layout 13: the engine level
s = state_of(msg(5, eight()))
check("layout 13 is read", s["layout"] == 13)
check("engine level 2 is read", s.get("engine_level") == 2 and s.get("has_diag") is True, (s.get("engine_level"), s.get("has_diag")))
check("the older parts are still read", s["recounts"] == {"west": 0, "east": 0, "resistance": 0} and len(s["teams"]) == 9)
check("engine level 1 is read", state_of(msg(5, eight(), level=1)).get("engine_level") == 1)
zero = state_of(msg(5, eight(), has_diag=False, level=0))
check("engine level 0 without the diagnostics is read", zero.get("engine_level") == 0 and zero.get("has_diag") is False)
check("a level sent as a decimal number (the game prints numbers that way) is read", state_of(json.loads(json.dumps(msg(5, eight(), level=2.0)))).get("engine_level") == 2)
fourteen = state_of(msg(5, eight(), level=NOTHING))
check("a 14-part report makes no claim about the level", "engine_level" not in fourteen and fourteen.get("has_diag") is True and fourteen["layout"] == 13)
for label, value in (("a text", "scalar bool array"), ("nothing", None), ("a list", [2])):
    bad = state_of(msg(5, eight(), level=value))
    check("an unreadable level (%s) is left out and the report is still good" % label, "engine_level" not in bad and len(bad["teams"]) == 9 and bad.get("has_diag") is True, bad.get("engine_level"))
try:
    state_of(msg(5, eight()) + ["one part too many"]); refused = False
except ValueError:
    refused = True
check("a report with 16 parts is refused", refused)
try:
    state_of(msg(5, eight(), layout=relay.REPORT_LAYOUT + 1)); refused = False
except ValueError as error:
    refused = "newer relay" in str(error)
check("a layout newer than the relay knows is refused", refused)
s12 = state_of(msg(5, eight(layout=12), layout=12, level=NOTHING))
check("a layout 12 report (14 parts) is still read", s12["layout"] == 12 and s12.get("has_diag") is True and "engine_level" not in s12)

# 2. the note about the engine: once, and only when something is missing
def notes_of(make, name, **kw):
    c = make(name); said = []
    for m in range(1, 8):
        _, out, _ = handle(c, msg(m, eight(), **kw))
        said.append((LEVEL_NOTE in out, DIAG_NOTE in out))
    return said, c
commander_of = commander
said, c = notes_of(commander_of, "unit23a.jsonl")
check("engine level 2: nothing is said", not any(a or b for a, b in said), said)
said, c = notes_of(commander_of, "unit23b.jsonl", level=1)
check("engine level 1: said once, on the first report", [a for a, _ in said] == [True] + [False] * 6 and not any(b for _, b in said), said)
_, out, _ = handle(commander("unit23b2.jsonl"), msg(1, eight(), level=1))
check("...and the note names the patch script and both levels", "apply_llm_engine.py" in out and "level 1" in out and "expects 2" in out, out[-500:])
said, c = notes_of(commander_of, "unit23c.jsonl", has_diag=False, level=0)
check("no diagnostics at all: the diagnostics note once, and not a second note about the level",
      [b for _, b in said] == [True] + [False] * 6 and not any(a for a, _ in said), said)
said, c = notes_of(commander_of, "unit23d.jsonl", level=NOTHING)
check("a report that does not state the level: nothing is said about it", not any(a for a, _ in said), said)
def observer_notes(name, **kw):
    o = relay.MfctiObserver("East", os.path.join(TMP, name)); said = []
    for m in range(1, 6):
        with contextlib.redirect_stdout(io.StringIO()) as out: o.handle(state_of(msg(m, eight(), mode=0, **kw)))
        said.append(LEVEL_NOTE in out.getvalue())
    return said, o
said, o = observer_notes("unit23e.jsonl", level=1)
check("observer mode (the stock mission) at level 1: said once, on the first report", said == [True, False, False, False, False], said)
said, o = observer_notes("unit23f.jsonl")
check("observer mode at level 2: nothing is said", not any(said), said)
text = open(o.log_path).read()
check("the log line holds the exact text the trial script looks for", '"engine_level": 2' in text and '"has_diag": true' in text)

# 3. the new word in the vehicle text
c = commander("unit23g.jsonl"); lines = []
for m in range(9, 15):
    _, out, st = handle(c, msg(m, eight(Charlie=dict(diag=(STUCK, STUCK, GROUP)))))
    lines += [l for l in out.splitlines() if "KICK" in l and "Charlie" in l]
w = relay.diag_words(st["teams"][3]["diag"]["vehicle"])
check("the driving order (mm=) and the combat mode can be read from the vehicle text", (w.get("mm"), w.get("sem"), w.get("noai"), w.get("plan")) == ("MOVE", "YELLOW", "1", "VEHICLE"), w)
check("a team that stands still is kicked as before, and the kick line carries the text", len(lines) == 1 and "mm=MOVE" in lines[0], lines)
rows = [json.loads(l) for l in open(c.log_path)]
check("the text is in the logged state", rows[-1]["state"]["teams"][3]["diag"]["vehicle"] == STUCK and rows[-1]["state"]["engine_level"] == 2)

# 4. no rule changed: the same game reported in layout 12 and in layout 13 gets the same orders
def orders(layout, name, **kw):
    c = commander(name); out = []
    for m in range(1, 16):
        teams = eight(layout=layout, Alpha=dict(at=FIELD if m < 6 else (FIELD[0] + 40 * m, FIELD[1])), Echo=dict(at=BASE if m < 4 else FIELD))
        reply, _, _ = handle(c, msg(m, teams, layout=layout, **kw))
        out.append(json.loads(reply)[1])
    return out
check("layout 12 and layout 13 reports of the same game get the same orders, report by report",
      orders(12, "unit23h.jsonl", level=NOTHING) == orders(13, "unit23i.jsonl"))
check("...and so do engine levels 1 and 2", orders(13, "unit23j.jsonl", level=1) == orders(13, "unit23k.jsonl", level=2))

# 5. raw game text and the reply
relay.LOG_DIR = TMP
r = relay.Relay(); r.log_path = os.path.join(TMP, "unit23_relay.jsonl"); open(r.log_path, "w").close()
with contextlib.redirect_stdout(io.StringIO()): raw_reply = r.handle(json.dumps(msg(5, eight(Charlie=dict(diag=(STUCK, STUCK, GROUP))))))
parsed = json.loads(raw_reply)
check("raw game text with layout 13 goes through the relay; the reply format is unchanged",
      parsed[0] == 1 and len(parsed[1]) == 9 and all(len(e) == 4 for e in parsed[1]) and isinstance(parsed[2], str), raw_reply)
row = json.loads(open(r.log_path, encoding="utf-8").read().splitlines()[-1])
check("...and the level is in the relay's own log", row["state"].get("engine_level") == 2, row["state"].get("engine_level"))
asked = []
def model(messages, think):
    asked.append(" ".join(m["content"] for m in messages)); return json.dumps(plan()), False
relay.ask_model = model
handle(commander("unit23l.jsonl"), msg(5, eight(Charlie=dict(diag=(STUCK, STUCK, GROUP)))))
check("neither the engine level nor the engine's texts go to the model", asked and not any("engine_level" in a or "mm=MOVE" in a or "engine level" in a.lower() for a in asked))

print("%d checks passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
