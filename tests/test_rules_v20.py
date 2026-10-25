"""Unit tests for what was new in relay version 20: fitness by platform, the frozen-leader signature,
teams that do not form, rules-only mode, the report layout number and the decision log.
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
def tanks(n, fire=True, driver=True, move=True): return [["MFCTI116T80", "V", move, fire, True, 0.8, True, driver] for _ in range(n)]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, men=None, seat=1, speed=0, ready=True, far=0, near=0, height=0.0, hurt=0.0, role=0):
    men = men if men is not None else (len(kit) if kit and kit[0][1] != "V" else 3 * len(kit))
    near_m = ((x - T[near][2]) ** 2 + (y - T[near][3]) ** 2) ** .5
    return [name, False, role, 12, True, 100000, men, near, near_m, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5,
            seat, speed, ready, far, height, hurt]
def msg(minute, built, owners, teams, deaths=(), layout=10):
    m = ["MFCTI", "East", minute * 60, 1, [[n, v, o, x, y] for (n, v, x, y), o in zip(T, owners)],
         [900000, built, True, 0, False, -1, BASE[0], BASE[1]],
         [team("Commander", LEADER, *BASE, seat=0)] + teams, [], [], [list(d) for d in deaths], []]
    return m + [layout] if layout is not None else m
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]; NONE = [0] * 8
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
FIELD = (9000, 5600)
def eight(kits=None, where=None, **kw):
    kits, where = kits or {}, where or {}
    return [team(n, kits.get(n, SQUAD), *where.get(n, FIELD), **dict(dict(seat=1 if kits.get(n, SQUAD)[0][1] == "V" else 0), **kw.get(n, {}))) for n in NAMES]
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(): return relay.MfctiCommander("East", os.path.join(TMP, "unit20.jsonl"))
def plan(**orders):
    out = {}
    for n in NAMES:
        role, order, target = orders.get(n, ("ARMOUR" if n in NAMES[:4] else "INFANTRY", "TAKE_TOWNS", None))
        out[n] = {"role": role, "order": order, "target": target, "why": "test"}
    return {"situation": "s", "teams": out, "intent": "i"}
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:700])
def again_of(reply, name): return json.loads(reply)[1][NAMES.index(name) + 1][3]
def run(c, minute, kits=None, where=None, owners=(0, 0, 0, 0), deaths=(), built=HEAVY, layout=10, **kw):
    s = state_of(msg(minute, built, list(owners), eight(kits, where, **kw), deaths=deaths, layout=layout))
    with contextlib.redirect_stdout(io.StringIO()) as out: reply = c.handle(s)
    return reply, out.getvalue(), s
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
kits = {n: tanks(4) for n in NAMES[:4]}
AT_BASE = {"Alpha": (BASE[0] + 20, BASE[1] + 10)}

check("relay is version 20 or later", relay.VERSION >= 20, relay.VERSION)

# 1. the report layout number and the two new values
s = state_of(msg(5, HEAVY, [0, 0, 0, 0], eight(kits, Alpha=dict(height=3.4, hurt=0.27))))
check("layout 10 is read", s["layout"] == 10 and s["teams"][1]["leader_height"] == 3.4 and s["teams"][1]["leader_vehicle_damage"] == 0.27, s["teams"][1])
try:
    state_of(msg(5, HEAVY, [0, 0, 0, 0], eight(kits), layout=relay.REPORT_LAYOUT + 1)); refused = False
except ValueError as error:
    refused = "newer relay" in str(error)
check("a layout newer than the relay knows is refused with a plain reason", refused)
old = msg(5, HEAVY, [0, 0, 0, 0], eight(kits), layout=None)
for entry in old[6]: del entry[19:]
c = commander(); s_old = state_of(old)
with contextlib.redirect_stdout(io.StringIO()) as out: c.handle(s_old)
check("a version 9 report is still read, with a warning once", s_old["layout"] is None and "report layout" in out.getvalue() and "leader_height" not in s_old["teams"][1], out.getvalue()[-300:])
with contextlib.redirect_stdout(io.StringIO()) as out: c.handle(state_of(msg(6, HEAVY, [0, 0, 0, 0], eight(kits), layout=None)))
check("...and only once", "report layout" not in out.getvalue())

# 2. fit to fight, by platform
cases = {"Alpha": tanks(1),                                   # one crewed working tank, three men
         "Bravo": tanks(1, fire=False),                       # its only gun is out
         "Charlie": tanks(1, move=False) + tanks(1),          # one immobile, one working
         "Delta": tanks(1, driver=False),                     # nobody to drive it
         "Echo": SQUAD[:3], "Foxtrot": SQUAD[:4]}
c = commander(); s = state_of(msg(20, HEAVY, [0, 0, 0, 0], eight(dict(kits, **cases)))); teams = c.commanded(s); c.find_changes(s, teams)
fit = {t["name"]: c.fit(t) for t in teams}
check("one crewed, working tank is fit", fit["Alpha"])
check("a team whose only gun is out is not", not fit["Bravo"] and "half its guns" not in c.unfit_reason(teams[1]), c.unfit_reason(teams[1]))
check("one immobile tank and one working tank: fit", fit["Charlie"])
check("a tank with nobody to drive it is not a working vehicle", not fit["Delta"])
check("on foot, three men is not fit and four is", not fit["Echo"] and fit["Foxtrot"])
p = plan(**{n: ("ARMOUR" if n in NAMES[:4] else "INFANTRY", "RETURN_TO_BASE", None) for n in NAMES}); c.tidy(p); c.enforce(p, s, teams)
o = {n: p["teams"][n]["order"] for n in NAMES}
check("recalls of vehicle teams follow fitness", (o["Alpha"], o["Bravo"], o["Charlie"], o["Delta"]) ==
      ("TAKE_TOWNS", "RETURN_TO_BASE", "TAKE_TOWNS", "RETURN_TO_BASE"), o)
check("a fit foot team is not recalled; one of three men counts as re-forming, which the mission handles itself",
      (o["Foxtrot"], o["Echo"]) == ("TAKE_TOWNS", "TAKE_TOWNS"), o)
old_team = dict(teams[0]); del old_team["fit_vehicles"]
check("a log from before version 20 (no count of working vehicles) is still judged", c.fit(old_team))

# 3. the frozen-leader signature: kicked on the second report in a row that shows it
frozen = dict(seat=1, speed=0, ready=False)
c = commander(); got = {}
for m in range(9, 16):
    reply, out, _ = run(c, m, kits, AT_BASE, Alpha=frozen)
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("signature at base: kicked 2 minutes after it is first seen standing, not 4", min(got) == 12, got)
check("the kick line names the signature", "Frozen-leader signature" in open(c.log_path).read())
c = commander(); got = {}
for m in range(9, 16):
    reply, out, _ = run(c, m, kits, AT_BASE, Alpha=dict(seat=1, speed=0, ready=True))
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("a mounted leader holding no order of his own waits the usual 4 minutes", min(got) == 14, got)
c = commander(); got = {}
for m in range(9, 14):
    reply, out, _ = run(c, m, kits, {"Echo": FIELD}, Echo=dict(seat=0, speed=0, ready=False))
    if again_of(reply, "Echo"): got[m] = again_of(reply, "Echo")
check("a leader on foot never shows the signature", not got, got)
c = commander(); got = {}
for m in range(9, 14):
    reply, out, _ = run(c, m, kits, AT_BASE, Alpha=dict(seat=1, speed=14 if m % 2 else 0, ready=False))
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("the signature must hold on two reports in a row", not got, got)
c = commander(); got = {}
for m in range(9, 30):
    reply, out, _ = run(c, m, kits, AT_BASE, Alpha=frozen)
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("a signature that survives the kicks: three quick kicks, then one every ten minutes", list(got)[:4] == [12, 14, 16, 26], got)

# 4. a team that does not form
lone = dict(kits, Alpha=LEADER)
c = commander(); outs = ""
for m in range(8, 17):
    reply, out, _ = run(c, m, lone, AT_BASE, Alpha=dict(seat=0, role=7))
    outs += out
check("a lone tank leader at base for 6 minutes is logged once as not forming", outs.count("   FORM  Alpha") == 1 and "probably the factory queue" in outs, outs[-400:])
rows = [json.loads(l) for l in open(c.log_path)]
check("...and the note is in the session log", any(r.get("forming") for r in rows))
asked = []
rerole = plan(Alpha=("INFANTRY_AT", "TAKE_TOWNS", None), Echo=("ARMOUR", "TAKE_TOWNS", None))
def model(messages, think):
    asked.append(messages[1]["content"])
    return json.dumps(rerole if "cannot get vehicles" in messages[1]["content"] else plan()), False
relay.ask_model = model
full = {n: tanks(4) for n in NAMES[1:5]}; full["Alpha"] = LEADER       # the other teams hold 16 vehicles
c = commander(); roles = {}
for m in range(8, 17):
    run(c, m, full, AT_BASE, Alpha=dict(seat=0, role=7))
    roles[m] = c.standing["Alpha"]["role"]
told = [a for a in asked if "cannot get vehicles" in a and "Alpha" in a]
check("near the vehicle limit the commander is told, once, that the tank team cannot form", len(told) == 1, len(told))
changed = min((m for m, r in roles.items() if r == "INFANTRY_AT"), default=None)
check("...and its role is changed on that report, inside the 8 minutes a role is normally kept", roles[8] == "ARMOUR" and changed is not None and changed - 8 < 8, roles)
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)

# 5. rules-only mode: the model is never asked
calls = []
relay.ask_model = lambda messages, think: (calls.append(1), json.dumps(plan()))[1:] + (False,)
relay.RULES_ONLY = True
c = commander()
reply, out, _ = run(c, 0.4, {n: LEADER for n in NAMES}, {n: BASE for n in NAMES}, built=NONE)
reply2, out2, _ = run(c, 12, kits, AT_BASE)
relay.RULES_ONLY = False
row = [json.loads(l) for l in open(c.log_path)][-1]
check("rules only: the model is not called", not calls, len(calls))
check("rules only: four tank teams from the first report, every team on TAKE_TOWNS", sum(1 for o in c.standing.values() if o["role"] == "ARMOUR") == 4
      and all(o["order"] == "TAKE_TOWNS" for o in c.standing.values()), c.standing)
check("rules only: said on the console and marked in the log", "RULES ONLY" in out and row.get("decision", {}).get("rules_only") is True, row.get("decision"))
check("rules only: replies are the normal ones", json.loads(reply2)[1][1][1] == 3, reply2)

# 6. the decision log: the prompt and every attempt with its rejection reasons
answers = iter([json.dumps(plan(**{n: ("INFANTRY", "TAKE_TOWNS", None) for n in NAMES})), json.dumps(plan())])
relay.ask_model = lambda messages, think: (next(answers), False)
c = commander(); run(c, 10, kits, AT_BASE)
row = [json.loads(l) for l in open(c.log_path)][-1]; d = row.get("decision", {})
check("the log keeps the prompt and the system prompt of the first call", "CURRENT SITUATION" in d.get("prompt", "") and "commander in MFCTI" in d.get("system_prompt", ""), list(d))
check("...and both attempts, the first with why it was rejected", len(d.get("attempts", [])) == 2 and any("ARMOUR" in x for x in d["attempts"][0]["problems"])
      and d["attempts"][1]["problems"] == [], [a.get("problems") for a in d.get("attempts", [])])

print("rules from version 20: %d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
