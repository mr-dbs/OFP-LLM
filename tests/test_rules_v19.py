"""Unit tests for what was new in relay version 19: the kick, the opening, the new report fields.
Three checks were rewritten for version 20, which judges fitness by platform and no longer lets growth
at base restart the clock; they are marked "version 20".
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay
T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
def tanks(n, fire=True, driver=True): return [["MFCTI116T80", "V", True, fire, True, 0.8, True, driver] for _ in range(n)]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, men=None, seat=1, speed=0, ready=True, far=0, near=0, near_m=None):
    men = men if men is not None else (len(kit) if kit and kit[0][1] != "V" else 3 * len(kit))
    near_m = near_m if near_m is not None else ((x - T[near][2]) ** 2 + (y - T[near][3]) ** 2) ** .5
    return [name, False, 0, 12, True, 100000, men, near, near_m, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5, seat, speed, ready, far]
def msg(minute, built, owners, teams, deaths=()):
    return ["MFCTI", "East", minute * 60, 1, [[n, v, o, x, y] for (n, v, x, y), o in zip(T, owners)],
            [900000, built, True, 0, False, -1, BASE[0], BASE[1]],
            [team("Commander", LEADER, *BASE, seat=0)] + teams, [], [], [list(d) for d in deaths], []]
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]; LIGHT = [1, 1, 1, 0, 0, 0, 0, 0]; NONE = [0] * 8
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
FIELD = (9000, 5600)                       # in the field, far from every town centre and from base
def eight(kits=None, where=None, **kw):
    kits, where = kits or {}, where or {}
    return [team(n, kits.get(n, SQUAD), *where.get(n, FIELD), **kw.get(n, {})) for n in NAMES]
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(): return relay.MfctiCommander("East", os.path.join(TMP, "unit19.jsonl"))
def plan(**orders):
    out = {}
    for n in NAMES:
        role, order, target = orders.get(n, ("ARMOUR" if n in NAMES[:4] else "INFANTRY", "TAKE_TOWNS", None))
        out[n] = {"role": role, "order": order, "target": target, "why": "test"}
    return {"situation": "s", "teams": out, "intent": "i"}
def quiet(f, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out: r = f(*a)
    return r, out.getvalue()
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, str(extra)[:600])
def again_of(reply, name): return json.loads(reply)[1][NAMES.index(name) + 1][3]
def run(c, minute, kits=None, where=None, owners=(0, 0, 0, 0), deaths=(), built=HEAVY, **kw):
    s = state_of(msg(minute, built, list(owners), eight(kits, where, **kw), deaths=deaths))
    reply, out = quiet(c.handle, s)
    return reply, out, s

check("relay is version 19 or later", relay.VERSION >= 19, relay.VERSION)

# 1. the new report fields
s = state_of(msg(5, HEAVY, [0, 0, 0, 0], eight({"Alpha": tanks(2) + tanks(1, driver=False)}, Alpha=dict(seat=3, speed=14, ready=False, far=2))))
a = s["teams"][1]
check("leader seat, speed, ready and left-behind are read", (a["leader_seat"], a["speed"], a["leader_ready"], a["left_behind"]) == ("commander", 14, False, 2), a)
check("a vehicle without a driver is counted and named", a["no_driver"] == 1 and "no driver" in a["has"], a["has"])
old = msg(5, HEAVY, [0, 0, 0, 0], eight())
for t in old[6]: del t[15:]; t[11] = [k[:7] for k in t[11]]
s_old = state_of(old)
check("a version 8 report (no new fields) is still read", "leader_seat" not in s_old["teams"][1] and s_old["teams"][1]["men"] == 9)

# 2. the opening: tank teams are named before the heavy factory exists
c = commander(); s = state_of(msg(0.4, NONE, [0, 0, 0, 0], eight({n: LEADER for n in NAMES}, {n: BASE for n in NAMES}))); teams = c.commanded(s); c.find_changes(s, teams)
p = plan(**{n: ("INFANTRY", "TAKE_TOWNS", None) for n in NAMES}); c.tidy(p); probs = c.validate(p, s, teams)
check("opening: a plan with no tank teams is sent back", any("This is the opening" in x for x in probs), probs)
p = plan(); c.tidy(p); probs = c.validate(p, s, teams)
check("opening: four ARMOUR teams with no heavy factory is legal", probs == [], probs)
fb = c.fallback_plan(s, teams)
check("opening: the fallback names four tank teams and is legal", sum(1 for e in fb["teams"].values() if e["role"] == "ARMOUR") == 4 and c.validate(fb, s, teams) == [], fb["teams"])
late = state_of(msg(7, LIGHT, [0, 0, 0, 0], eight())); c2 = commander(); t2 = c2.commanded(late); c2.find_changes(late, t2)
p = plan(); c2.tidy(p); probs = c2.validate(p, late, t2)
check("after 6 minutes with no heavy factory ARMOUR is refused", any("no heavy factory after 6 minutes" in x for x in probs), probs)
fb = c2.fallback_plan(late, t2)
check("...and the fallback then has no tank teams and is legal", not any(e["role"] == "ARMOUR" for e in fb["teams"].values()) and c2.validate(fb, late, t2) == [], fb["teams"])
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
c = commander(); run(c, 0.4, {n: LEADER for n in NAMES}, {n: BASE for n in NAMES}, built=NONE)
check("opening plan stands with four ARMOUR teams", sum(1 for o in c.standing.values() if o["role"] == "ARMOUR") == 4, c.standing)
asked = []
relay.ask_model = lambda messages, think: (asked.append(messages[1]["content"]), json.dumps(plan(**{n: ("INFANTRY_AT", "TAKE_TOWNS", None) for n in NAMES})))[1:] + (False,)
reply, out, _ = run(c, 6.2, {n: LEADER for n in NAMES}, {n: BASE for n in NAMES}, built=LIGHT)
check("at minute 6 with no heavy factory the commander is told to re-role the waiting tank teams", asked and "still no heavy factory after 6 minutes" in asked[-1], out[-500:])
check("...and the tank teams become infantry", not any(o["role"] == "ARMOUR" for o in c.standing.values()), c.standing)

# 3. fit to fight: six men is not a reason to come home
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
kits = {n: tanks(4) for n in NAMES[:4]}
c = commander(); s = state_of(msg(20, HEAVY, [0, 0, 0, 0], eight(dict(kits, Alpha=tanks(2), Bravo=tanks(1), Charlie=tanks(2) + tanks(2, fire=False), Delta=tanks(3) + tanks(1, fire=False)))))
teams = c.commanded(s); c.find_changes(s, teams)
p = plan(**{n: ("ARMOUR", "RETURN_TO_BASE", None) for n in NAMES[:4]}); c.tidy(p); notes = c.enforce(p, s, teams)
o = {n: p["teams"][n]["order"] for n in NAMES[:4]}
check("a tank team of six (two tanks) in the field is fit: recall refused", o["Alpha"] == "TAKE_TOWNS", notes)
check("version 20: one crewed, working tank is fit although it is three men: recall refused", o["Bravo"] == "TAKE_TOWNS", notes)
check("a team with half its guns out may come home", o["Charlie"] == "RETURN_TO_BASE", notes)
check("a team with one gun in four out stays out", o["Delta"] == "TAKE_TOWNS", notes)
msgs = c.build_messages(s, teams, ["x"]); sit = json.loads(msgs[1]["content"].split("CURRENT SITUATION:")[1].rsplit("Give your orders now.", 1)[0])
st = {t["name"]: t["status"] for t in sit["your_teams"]}
check("version 20: the commander is shown the reasons", st["Bravo"] == "ready, in the field" and "half its guns" in st["Charlie"] and st["Alpha"] == "ready, in the field", st)
check("the briefing states both ways to win", "hold every town on the map" in msgs[0]["content"] and "mobile HQ and all four of his" in msgs[0]["content"])
check("the briefing has no unfilled placeholders", "{" not in msgs[0]["content"].split("Answer with ONE JSON object")[0])

# 4. a frozen team is kicked: a full tank team that never leaves base
AT_BASE = {"Alpha": (BASE[0] + 20, BASE[1] + 10)}
c = commander(); kicks = {}; field = {}
for m in range(9, 45):
    reply, out, _ = run(c, m, kits, AT_BASE)
    if again_of(reply, "Alpha"): kicks[m] = again_of(reply, "Alpha")
    if again_of(reply, "Bravo"): field[m] = again_of(reply, "Bravo")
check("at base: kicked after 4 minutes still, twice more 4 minutes apart, then every 10; never bumped among the buildings",
      kicks == {14: 2, 18: 2, 22: 2, 32: 2, 42: 2}, kicks)
check("in the field: the same, and from the third kick on with the bump", field == {14: 2, 18: 2, 22: 3, 32: 3, 42: 3}, field)
check("kicks are written to the log", any("kicks" in json.loads(l) and json.loads(l)["kicks"] for l in open(c.log_path)))
c = commander(); told = []
relay.ask_model = lambda messages, think: (told.append(messages[1]["content"]), json.dumps(plan()))[1:] + (False,)
for m in range(9, 28): run(c, m, kits, AT_BASE)
check("after three failed kicks the commander is told once", sum("3 attempts to get it moving have failed" in t and "Alpha has stood still" in t for t in told) == 1, len(told))
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
s = state_of(msg(28, HEAVY, [0, 0, 0, 0], eight(kits, AT_BASE))); teams = c.commanded(s)
sit = json.loads(c.build_messages(s, teams, ["x"])[1]["content"].split("CURRENT SITUATION:")[1].rsplit("Give your orders now.", 1)[0])
check("its status tells the commander it is not answering orders", "not answering orders" in sit["your_teams"][0]["status"], sit["your_teams"][0])

# 5. a kicked team that gets going is released, and may be kicked again later
c = commander()
for m in range(9, 15): reply, out, _ = run(c, m, kits, AT_BASE)
check("first kick at minute 14", again_of(reply, "Alpha") == 2)
reply, out, _ = run(c, 15, kits, {"Alpha": (BASE[0] + 80, BASE[1] + 10)})
check("60 m on is not yet moving again", "moving again" not in out and "Alpha" in c.freeze and c.freeze["Alpha"]["kicks"] == 1)
reply, out, _ = run(c, 16, kits, {"Alpha": (BASE[0] + 400, BASE[1] + 10)})
check("400 m on it is moving again and the count starts over", "moving again after 1 kick" in out and c.freeze["Alpha"]["kicks"] == 0, out[-300:])

# 6. teams that must not be kicked
def never(label, kits_, where_, minutes=range(9, 22), plan_=None, name="Alpha", **kw):
    relay.ask_model = lambda messages, think: (json.dumps(plan_ or plan()), False)
    c = commander(); got = []
    for m in minutes:
        reply, out, _ = run(c, m, kits_, where_, **kw)
        got.append(again_of(reply, name))
    check(label, not any(g >= 2 for g in got), got)
    relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
never("a one-tank team at base is still filling up: not kicked", dict(kits, Alpha=tanks(1)), AT_BASE)
never("eight infantry at base are still filling up: not kicked", dict(kits, Echo=SQUAD[:8]), {"Echo": BASE}, name="Echo")
never("a lone leader is not kicked", dict(kits, Alpha=LEADER), AT_BASE)
never("a team defending the base where it stands is not kicked", kits, dict(AT_BASE, Hotel=BASE), minutes=range(39, 52), plan_=plan(Hotel=("INFANTRY", "DEFEND_BASE", None)), name="Hotel")
c = commander(); got = []
for m in range(9, 22):
    reply, out, _ = run(c, m, kits, AT_BASE, deaths=[(1, "SoldierGLAW", False)] if m % 3 == 0 else ())
    got.append(again_of(reply, "Alpha"))
check("a team losing men every few minutes is fighting: not kicked", not any(got), got)
c = commander(); got = []
for i, m in enumerate(range(9, 20)):
    reply, out, _ = run(c, m, dict(kits, Alpha=tanks(2 + min(2, i // 3))), AT_BASE)
    got.append(again_of(reply, "Alpha"))
check("version 20: a team at dispatch size that keeps growing at base is still kicked after 4 minutes", got[5] == 2 and not any(got[:5]), got)
# at the town it is taking: 8 minutes, not 4
AT_TOWN = {"Alpha": (T[1][2] + 60, T[1][3])}
c = commander(); got = {}
for m in range(9, 20):
    reply, out, _ = run(c, m, kits, AT_TOWN, Alpha=dict(near=1))
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("60 m from the town it is taking: kicked after 8 minutes, not 4", got == {18: 2}, got)
c = commander(); got = {}
for m in range(9, 20):
    reply, out, _ = run(c, m, kits, AT_TOWN, owners=(0, 1, 0, 0), Alpha=dict(near=1))
    if again_of(reply, "Alpha"): got[m] = again_of(reply, "Alpha")
check("in a town that is already ours: kicked after 4 minutes", got.get(14) == 2, got)

# 7. a team sent to a place that does not set out is kicked towards that place
relay.ask_model = lambda messages, think: (json.dumps(plan(Bravo=("ARMOUR", "RETURN_TO_BASE", None))), False)
c = commander(); bravo3 = dict(kits, Bravo=tanks(1) + tanks(1, fire=False))
got = {}
for m in range(19, 30):
    reply, out, _ = run(c, m, bravo3, {"Bravo": (9000, 5600)})
    e = json.loads(reply)[1][2]
    if e[3] >= 2: got[m] = e
check("a team with half its guns out, ordered home, that stands still in the field is kicked with the go-to-base order", got and all(e[1:3] == [1, -2] for e in got.values()) and min(got) == 24, got)

# 8. an order that changes in the same report cancels the kick
seq = iter([plan()] * 3 + [plan(Alpha=("ARMOUR", "RETURN_TO_BASE", None))] * 20)
cur = [plan()]
c = commander()
relay.ask_model = lambda messages, think: (json.dumps(cur[0]), False)
half = dict(kits, Alpha=tanks(2) + tanks(2, fire=False))
for m in range(9, 14): reply, out, _ = run(c, m, half, {"Alpha": (9000, 5600)})
cur[0] = plan(Alpha=("ARMOUR", "RETURN_TO_BASE", None))
reply, out, _ = run(c, 14, half, {"Alpha": (9000, 5600)}, deaths=[(2, "SoldierGLAW", False), (2, "SoldierGLAW", False)])
check("the model was asked and changed Alpha's order at the minute a kick was due", c.standing["Alpha"]["order"] == "RETURN_TO_BASE", (c.standing["Alpha"], out[-400:]))
check("...so no kick is sent on the old order", again_of(reply, "Alpha") < 2, reply)

print("rules from version 19: %d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
