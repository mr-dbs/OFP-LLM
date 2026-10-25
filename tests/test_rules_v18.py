"""Unit tests written for relay version 18 and still required to pass: each rule on a constructed situation.
Started by run_tests.py. Arguments: the folder that holds relay.py, a scratch folder."""
import json, sys, os, io, contextlib, copy
sys.path.insert(0, sys.argv[1]); TMP = sys.argv[2]
import relay

T = [("Lany", 200, 10000, 4300), ("Varta", 100, 8900, 7000), ("Petrovice", 400, 3000, 5400), ("Mala Ves", 100, 8000, 4700)]
BASE = (10019, 4009)
def man(t, w=""): return [t, w, False]
SQUAD = [man("SoldierEB")] * 5 + [man("SoldierELAW", "RPGLauncher")] * 4
TANKS = [["MFCTI116T80", "V", True, True, True, 0.8, True], ["MFCTI116T80", "V", True, True, True, 0.8, True]]
TANKS_GUN_OUT = [["MFCTI116T80", "V", True, False, True, 0.8, True]]
LEADER = [man("SoldierEAT", "AT4Launcher")]
def team(name, kit, x, y, men=None):
    men = men if men is not None else (len(kit) if kit and kit[0][1] != "V" else 3 * len(kit))
    return [name, False, 0, 4, True, 100000, men, 0, 100, False, True, kit, x, y, ((x - BASE[0]) ** 2 + (y - BASE[1]) ** 2) ** .5]
def msg(minute, built, owners, teams, enemy=(), kills=(), deaths=(), points=(("kt1", 3522, 5173), ("kt6", 8725, 4196), ("hlz1", 4810, 4498)), base_seen=False):
    return ["MFCTI", "East", minute * 60, 1, [[n, v, o, x, y] for (n, v, x, y), o in zip(T, owners)],
            [900000, built, True, 0, base_seen, 2 if base_seen else -1, BASE[0], BASE[1]],
            [team("Commander", LEADER, *BASE)] + teams, [list(e) for e in enemy], [list(k) for k in kills], [list(d) for d in deaths], [list(p) for p in points]]
HEAVY = [1, 1, 1, 1, 0, 0, 1, 0]; LIGHT = [1, 1, 1, 0, 0, 0, 0, 0]; NONE = [0] * 8
NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
def eight(kits, where=None):
    where = where or {}
    return [team(n, kits.get(n, SQUAD), *where.get(n, (9000, 5000))) for n in NAMES]
def state_of(m): return relay.parse_mfcti(json.loads(json.dumps(m)))
def commander(): return relay.MfctiCommander("East", os.path.join(TMP, "unit.jsonl"))
def plan(**orders):
    out = {}
    for n in NAMES:
        role, order, target = orders.get(n, ("INFANTRY", "TAKE_TOWNS", None))
        out[n] = {"role": role, "order": order, "target": target, "why": "test"}
    return {"situation": "s", "teams": out, "intent": "i"}
def quiet(f, *a):
    with contextlib.redirect_stdout(io.StringIO()) as out: r = f(*a)
    return r, out.getvalue()
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1
    else: fail += 1; print("FAIL:", label, extra)

# 1. force mix with a heavy factory
c = commander(); s = state_of(msg(10, HEAVY, [0, 0, 0, 0], eight({}))); teams = c.commanded(s); c.find_changes(s, teams)
p = plan(); c.tidy(p); c.enforce(p, s, teams); probs = c.validate(p, s, teams)
check("all infantry with a heavy factory is rejected", any("ARMOUR or ARMOUR_HEAVY" in x for x in probs), probs)
p = plan(**{n: ("ARMOUR", "TAKE_TOWNS", None) for n in NAMES}); c.tidy(p); probs = c.validate(p, s, teams)
check("eight vehicle teams are rejected (limit 6)", any("vehicle role" in x for x in probs), probs)
p = plan(**{n: ("ARMOUR", "TAKE_TOWNS", None) for n in NAMES[:4]}); c.tidy(p); probs = c.validate(p, s, teams)
check("four tank teams and four infantry is legal", probs == [], probs)
p = plan(Alpha=("ARMOUR", "TAKE_TOWNS", None), Bravo=("INFANTRY_AA", "TAKE_TOWNS", None)); c.tidy(p); probs = c.validate(p, s, teams)
check("anti-air role with no aircraft is rejected", any("no enemy aircraft" in x for x in probs), probs)
s2 = state_of(msg(10, LIGHT, [0, 0, 0, 0], eight({}))); c2 = commander(); t2 = c2.commanded(s2); c2.find_changes(s2, t2)
p = plan(Alpha=("ARMOUR", "TAKE_TOWNS", None)); c2.tidy(p); probs = c2.validate(p, s2, t2)
check("ARMOUR with only a light factory is rejected", any("no heavy factory" in x for x in probs), probs)
p = plan(); c2.tidy(p); probs = c2.validate(p, s2, t2)
check("all infantry with no heavy factory is legal", probs == [], probs)

# 2. the old names for the normal order are accepted
p = plan(Alpha=("ARMOUR", "TAKE_TOWN", "Lany"), Bravo=("ARMOUR", "AUTO", None), Charlie=("ARMOUR", "take towns", None), Delta=("armour", "TAKE_TOWNS", "Varta"))
c.tidy(p)
check("TAKE_TOWN / AUTO / 'take towns' all become TAKE_TOWNS with no target", all(p["teams"][n]["order"] == "TAKE_TOWNS" and p["teams"][n]["target"] is None for n in NAMES[:4]), p["teams"])
check("...and the plan is legal", c.validate(p, s, teams) == [], c.validate(p, s, teams))
p = plan(Alpha=(["x"], {"y": 1}, 5)); c.tidy(p); probs = c.validate(p, s, teams)
check("a role and order that are not text are rejected cleanly", any("is not a role" in x for x in probs), probs)

# 3. exceptions with no grounds are put back on TAKE_TOWNS
tank4 = {n: TANKS for n in NAMES[:4]}
c = commander(); s = state_of(msg(10, HEAVY, [1, 0, 0, 0], eight(tank4))); teams = c.commanded(s); c.find_changes(s, teams)
roles = {n: ("ARMOUR", "TAKE_TOWNS", None) for n in NAMES[:4]}
p = plan(**dict(roles, Echo=("INFANTRY", "DEFEND_TOWN", "Lany"), Foxtrot=("INFANTRY", "DEFEND_BASE", None), Golf=("INFANTRY", "RETURN_TO_BASE", None),
                Hotel=("INFANTRY", "ATTACK_BASE", None), Alpha=("ARMOUR", "HOLD_POINT", "kt6")))
c.tidy(p); notes = c.enforce(p, s, teams)
check("five groundless exceptions are all put back", len(notes) == 5 and all(p["teams"][n]["order"] == "TAKE_TOWNS" for n in NAMES), notes)
check("...and the plan is then legal", c.validate(p, s, teams) == [], c.validate(p, s, teams))

# 4. exceptions with grounds are kept
enemy = [("MFCTI116M1A1", 0, False, True, 0), ("SoldierWB", 0, True, True, 0)]          # enemy tank and man at Lany (ours, next to base)
c = commander(); s = state_of(msg(40, HEAVY, [1, 0, 0, 0], eight(tank4, {"Echo": (9950, 4350), "Golf": BASE, "Hotel": BASE}), enemy=enemy, base_seen=True))
teams = c.commanded(s); c.find_changes(s, teams)
p = plan(**dict(roles, Echo=("INFANTRY", "DEFEND_TOWN", "Lany"), Foxtrot=("INFANTRY", "DEFEND_TOWN", "lany"), Golf=("INFANTRY", "DEFEND_BASE", None),
                Hotel=("INFANTRY", "DEFEND_BASE", None), Delta=("ARMOUR", "ATTACK_BASE", None), Charlie=("ARMOUR", "HOLD_POINT", "KT6")))
c.tidy(p); notes = c.enforce(p, s, teams); o = {n: (p["teams"][n]["order"], p["teams"][n]["target"]) for n in NAMES}
check("DEFEND_TOWN at a threatened own town is kept for the nearest team", o["Echo"][0] == "DEFEND_TOWN", o)
check("...and the second team on the same town is put back", o["Foxtrot"][0] == "TAKE_TOWNS", o)
check("two base defenders are allowed once the enemy is near", o["Golf"][0] == "DEFEND_BASE" and o["Hotel"][0] == "DEFEND_BASE", o)
check("ATTACK_BASE is kept once the base is found", o["Delta"][0] == "ATTACK_BASE", o)
check("HOLD_POINT near an enemy sighting is kept", o["Charlie"][0] == "HOLD_POINT", (o, c.key_terrain(s)))
check("the plan with real exceptions is legal", c.validate(p, s, teams) == [], c.validate(p, s, teams))
kt = [k["name"] for k in c.key_terrain(s)]
check("only key terrain near the enemy sighting is offered", kt == ["kt6"], kt)

# 5. standing exceptions end when their grounds do
relay.ask_model = lambda messages, think: (json.dumps(p), False)
c = commander(); (_, out) = quiet(c.handle, s)
check("orders are standing after the first plan", c.standing["Echo"]["order"] == "DEFEND_TOWN" and c.standing["Golf"]["order"] == "DEFEND_BASE", c.standing)
r = json.loads(c.reply(s)); codes = {n: r[1][i + 1] for i, n in enumerate(NAMES)}
check("reply codes: take towns 3, attack base 2, defend base at base 4", codes["Alpha"][1] == 3 and codes["Delta"][1] == 2 and codes["Golf"][1] == 4, codes)
check("reply codes: a town guard already at its town defends in place (4), hold point goes to point 100+1", codes["Echo"][1:3] == [4, -1] and codes["Charlie"][1:3] == [1, 101], codes)
far = state_of(msg(40.5, HEAVY, [1, 0, 0, 0], eight(tank4, {"Echo": (9000, 5000), "Golf": BASE, "Hotel": BASE}), enemy=enemy, base_seen=True))
r = json.loads(c.reply(far)); check("reply codes: a town guard not there yet is sent to the town (1, town 0)", r[1][5][1:3] == [1, 0], r[1][5])
later = state_of(msg(52, HEAVY, [1, 0, 0, 0], eight(tank4, {"Echo": (9950, 4350), "Golf": BASE, "Hotel": BASE}), base_seen=True))
(_, out) = quiet(c.handle, later)
check("12 quiet minutes later the town guard is back on TAKE_TOWNS", c.standing["Echo"]["order"] == "TAKE_TOWNS", (c.standing["Echo"], out[-600:]))
later2 = state_of(msg(60, HEAVY, [1, 0, 0, 0], eight(tank4, {"Golf": BASE, "Hotel": BASE}), base_seen=True)); (_, out) = quiet(c.handle, later2)
n_def = sum(1 for n in NAMES if c.standing[n]["order"] == "DEFEND_BASE")
check("with the enemy gone only one base defender remains", n_def == 1, {n: c.standing[n]["order"] for n in NAMES})
check("the key terrain holder is back on TAKE_TOWNS once the enemy is gone", c.standing["Charlie"]["order"] == "TAKE_TOWNS", c.standing["Charlie"])
check("RULE lines are printed", "RULE" in out, out[-400:])

# 6. repair: all guns out -> home; repaired at base -> back to taking towns
c = commander(); kits = dict(tank4, Alpha=TANKS_GUN_OUT)
s = state_of(msg(20, HEAVY, [0, 0, 0, 0], eight(kits))); teams = c.commanded(s); c.find_changes(s, teams)
p = plan(**roles); c.tidy(p); notes = c.enforce(p, s, teams)
check("a team whose every gun is out is sent home", p["teams"]["Alpha"]["order"] == "RETURN_TO_BASE", notes)
check("...and that plan is legal", c.validate(p, s, teams) == [], c.validate(p, s, teams))
relay.ask_model = lambda messages, think: (json.dumps(plan(**roles)), False)
quiet(c.handle, s)
check("standing order is RETURN_TO_BASE", c.standing["Alpha"]["order"] == "RETURN_TO_BASE", c.standing["Alpha"])
home = lambda minute, kit: state_of(msg(minute, HEAVY, [0, 0, 0, 0], eight(dict(tank4, Alpha=kit), {"Alpha": BASE})))
quiet(c.handle, home(22, TANKS_GUN_OUT)); check("still home while damaged", c.standing["Alpha"]["order"] == "RETURN_TO_BASE", c.standing["Alpha"])
quiet(c.handle, home(24, TANKS)); check("repaired but home under 3 minutes: stays", c.standing["Alpha"]["order"] == "RETURN_TO_BASE", c.standing["Alpha"])
quiet(c.handle, home(26, TANKS)); check("repaired and home 3 minutes: back on TAKE_TOWNS", c.standing["Alpha"]["order"] == "TAKE_TOWNS", c.standing["Alpha"])
c = commander(); quiet(c.handle, s); quiet(c.handle, home(22, TANKS_GUN_OUT)); quiet(c.handle, home(31, TANKS_GUN_OUT))
check("never repaired: released after 8 minutes at base anyway", c.standing["Alpha"]["order"] == "TAKE_TOWNS", c.standing["Alpha"])

# 7. reply before and after the barracks; lone leaders
c = commander(); lone = {n: LEADER for n in NAMES}
relay.ask_model = lambda messages, think: (json.dumps(plan()), False)
s0 = state_of(msg(0.4, NONE, [0, 0, 0, 0], eight(lone, {n: BASE for n in NAMES}))); (rep0, _) = quiet(c.handle, s0)
r = json.loads(rep0); check("no barracks yet: leaders are kept at base", all(e[1:3] == [1, -2] for e in r[1][1:]), r[1])
check("the commander slot is left alone", r[1][0] == [-1, -1, -1, 0], r[1][0])
s1 = state_of(msg(3, LIGHT, [0, 0, 0, 0], eight(lone, {n: BASE for n in NAMES}))); (rep1, _) = quiet(c.handle, s1)
r = json.loads(rep1); check("barracks built: every team gets 'take towns by itself' (3), lone leaders included", all(e[1] == 3 for e in r[1][1:]), r[1])

# 8. the fallback is always legal
for label, st in (("no factory", s0), ("light factory", s1), ("heavy factory", s), ("heavy, enemy near, base found", later)):
    c = commander(); teams = c.commanded(st); c.find_changes(st, teams); fb = c.fallback_plan(st, teams)
    check("fallback legal: " + label, c.validate(fb, st, teams) == [], c.validate(fb, st, teams))
air = state_of(msg(30, HEAVY, [0, 0, 0, 0], eight(tank4), enemy=[("MFCTI116AH64", 1, False, True, 0)]))
c = commander(); teams = c.commanded(air); c.find_changes(air, teams); fb = c.fallback_plan(air, teams)
check("fallback with aircraft about has an anti-air team and is legal", c.validate(fb, air, teams) == [] and any(v["role"] == "INFANTRY_AA" for v in fb["teams"].values()), fb["teams"])
p = plan(**roles); c.tidy(p); probs = c.validate(p, air, teams)
check("aircraft active and no anti-air role is rejected", any("anti-air role" in x for x in probs), probs)

# 9. a model that never gives a legal plan -> fallback, never a stall
relay.ask_model = lambda messages, think: ("I think we should defend.", False)
c = commander(); (rep, out) = quiet(c.handle, s)
check("garbage from the model -> FALLBACK", "FALLBACK" in out and "NO LEGAL PLAN" not in out, out[-300:])
check("...and four tank teams on TAKE_TOWNS", sum(1 for v in c.standing.values() if v["role"] == "ARMOUR") == 4 and all(v["order"] in ("TAKE_TOWNS", "RETURN_TO_BASE") for v in c.standing.values()), c.standing)

# 10. junk kills and sightings are dropped, not reported
m = msg(20, HEAVY, [0, 0, 0, 0], eight(tank4), enemy=[("", 0, False, True, 0), (None, -1, False, None, 1)], kills=[("", -1, 1), ("MFCTI116M1A1", 0, 1)])
st = state_of(m); check("junk kill and sightings dropped", len(st["kills"]) == 1 and st["seen"] == [], (st["kills"], st["seen"]))

print("rules from version 18: %d passed, %d failed" % (ok, fail))
sys.exit(1 if fail else 0)
