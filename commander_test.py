"""
commander_test.py (version 5) - Step 4 of the OFP LLM commander project.

No game needed. This sends a FAKE MFCTI game state to your local model and
checks that what comes back is legal and backed by evidence.

Usage (run from the folder this file is in):
    python commander_test.py plan      ask for orders (uses playbook.json if it exists)
    python commander_test.py review    after-action review of a fake game -> writes playbook.json
    python commander_test.py reset     delete playbook.json

Try this order:  reset -> plan -> review -> plan   and compare the two plans.

Uses only the Python standard library. Nothing to install.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

VERSION = 5

# ----------------------------------------------------------------------------
# Settings you can change
# ----------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"
CONTEXT_TOKENS = 8192        # how much text the model can hold at once
THINK_PLAN = "low"           # reasoning effort for in-game orders: low / medium / high
THINK_REVIEW = "medium"      # reasoning effort for the after-action review
MAX_OUT_PLAN = 2500          # hard stop on tokens per call, thinking included
MAX_OUT_REVIEW = 6000
TEMP_PLAN = 0.4              # lower = more predictable, higher = more varied
TEMP_REVIEW = 0.2
MAX_ATTEMPTS = 3             # how many tries the model gets to produce a legal answer
SHOW_THINKING = False        # True prints the model's private reasoning
PLAYBOOK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playbook.json")

# ----------------------------------------------------------------------------
# The fixed menu. Order and role numbers are the real MFCTI 1.16a values.
# ----------------------------------------------------------------------------
ORDERS = {
    "TAKE_TOWNS_AND_BASES": (12, "attack: capture towns, then the enemy base"),
    "DEFEND_TOWNS_AND_BASES": (13, "garrison your most valuable towns"),
    "DEFEND_BASE": (6, "stay at your own base and protect it"),
    "SEARCH_AND_DESTROY": (7, "hunt enemy units and the enemy base"),
    "MOVE_TO_POINT": (4, "go to one named town and hold there; needs a target"),
}

ROLES = {
    "INFANTRY": (0, "riflemen on foot"),
    "INFANTRY_AA": (1, "infantry carrying anti-aircraft missiles; counters helicopters"),
    "INFANTRY_AT": (2, "infantry carrying anti-tank launchers; counters tanks"),
    "INFANTRY_CQB": (3, "close-quarters infantry for fighting inside towns"),
    "BLACK_OPS": (4, "saboteurs who raid the enemy base with satchel charges"),
    "MECHANIZED": (5, "infantry riding in BMPs"),
    "MECHANIZED_AA": (6, "mechanized infantry that also gets a Shilka; counters helicopters"),
    "ARMOUR": (7, "tanks"),
    "ARMOUR_HEAVY": (8, "heavy tanks"),
    "AIR": (9, "helicopters; needs an air factory"),
}

TEAMS = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]

# name: (cost from the mission's Stats.sqs, factory needed, what it is for)
BUY_MENU = {
    "SOLDIER":        (75,    "barracks",      "rifleman"),
    "MG_SOLDIER":     (100,   "barracks",      "machine gunner, good against infantry"),
    "LAW_SOLDIER":    (200,   "barracks",      "light anti-tank rocket, for light armour"),
    "AT_SOLDIER":     (300,   "barracks",      "heavy anti-tank launcher, counters tanks"),
    "AA_SOLDIER":     (300,   "barracks",      "shoulder-fired anti-aircraft missile, counters helicopters"),
    "UAZ":            (250,   "light_factory", "unarmed jeep, transport only"),
    "BRDM":           (350,   "light_factory", "light armoured scout car with a machine gun"),
    "BMP":            (950,   "light_factory", "infantry fighting vehicle, carries a squad"),
    "BMP2":           (1100,  "light_factory", "better infantry fighting vehicle with an autocannon"),
    "SHILKA":         (1000,  "light_factory", "self-propelled anti-aircraft gun, the strongest ground counter to helicopters"),
    "T72":            (1600,  "heavy_factory", "main battle tank"),
    "T80":            (3000,  "heavy_factory", "heavier, tougher tank"),
    "MI17_TRANSPORT": (4000,  "air_factory",   "transport helicopter, carries a squad"),
    "MI17_ARMED":     (8250,  "air_factory",   "transport helicopter with rockets"),
    "MI24":           (11000, "air_factory",   "attack helicopter"),
    "KA50":           (12000, "air_factory",   "attack helicopter"),
    "SU25":           (12000, "air_factory",   "ground-attack jet"),
    "STATIC_M2_GUN":  (100,   "control_center", "fixed machine gun at your base, against infantry"),
    "STATIC_HE_GUN":  (1000,  "control_center", "fixed cannon at your base, against vehicles"),
    "STATIC_AA_GUN":  (1200,  "control_center", "fixed anti-aircraft gun at your base, counters helicopters landing there"),
    "MORTAR":         (4500,  "control_center", "indirect fire against ground targets only; cannot hit aircraft"),
}

# Real Nogova town names and values from the mission. Ownership below is FAKE.
TOWN_VALUES = {
    "Mokra Vrata": 100, "Modrava": 250, "Mokropsy": 175, "Trosky": 150, "Varta": 100,
    "Loukov": 200, "Blata": 100, "Bitov": 100, "Velka Ves": 150, "Mala Ves": 100,
    "Lany": 200, "Lipany": 500, "Okrouhlo": 100, "St Sedlo": 75, "Bor": 75,
    "Davle": 150, "Neveklov": 200, "Kost": 100, "Slapy": 150, "Frymburk": 100,
    "Skalice": 100, "Paseky": 125, "Opatov": 100, "Joudov": 100, "Dolina": 150,
    "Petrovice": 400, "Vidlakov": 250, "Mirov": 200, "Bludov": 150,
}

# ----------------------------------------------------------------------------
# FAKE game state. Later the game itself will produce this.
# ----------------------------------------------------------------------------
FAKE_STATE = {
    "side": "EAST",
    "minute": 24,
    "funds": 12000,
    "income_per_minute": 1450,
    "base": {"control_center": True, "barracks": True, "light_factory": True,
             "heavy_factory": True, "air_factory": False, "static_aa_guns": 0},
    "towns_east": ["Petrovice", "Vidlakov", "Mirov", "Bludov", "Dolina", "Joudov", "Opatov"],
    "towns_west": ["Lipany", "Lany", "Loukov", "Modrava", "Mokropsy", "Neveklov"],
    # every other town is still held by resistance (neutral)
    "teams": {
        "Alpha":   {"role": "MECHANIZED", "men": 9,  "vehicles": ["BMP"],        "order": "TAKE_TOWNS_AND_BASES"},
        "Bravo":   {"role": "MECHANIZED", "men": 7,  "vehicles": ["BMP"],        "order": "TAKE_TOWNS_AND_BASES"},
        "Charlie": {"role": "ARMOUR",     "men": 6,  "vehicles": ["T72", "T72"], "order": "TAKE_TOWNS_AND_BASES"},
        "Delta":   {"role": "ARMOUR",     "men": 3,  "vehicles": ["T72"],        "order": "TAKE_TOWNS_AND_BASES"},
        "Echo":    {"role": "INFANTRY",   "men": 10, "vehicles": [],             "order": "DEFEND_TOWNS_AND_BASES"},
        "Foxtrot": {"role": "INFANTRY",   "men": 4,  "vehicles": [],             "order": "DEFEND_TOWNS_AND_BASES"},
        "Golf":    {"role": "MECHANIZED", "men": 8,  "vehicles": ["BMP2"],       "order": "TAKE_TOWNS_AND_BASES"},
        "Hotel":   {"role": "INFANTRY",   "men": 9,  "vehicles": [],             "order": "TAKE_TOWNS_AND_BASES"},
    },
    "spotted_enemy": [
        {"minute": 19, "what": "2x UH-60 transport helicopter", "near": "Petrovice"},
        {"minute": 21, "what": "infantry squad, about 8 men", "near": "Petrovice"},
        {"minute": 22, "what": "1x AH-1 attack helicopter", "near": "Vidlakov"},
    ],
    "recent_losses": [
        {"minute": 20, "what": "T72 (Delta)", "killed_by": "AH-1", "near": "Vidlakov"},
        {"minute": 22, "what": "6 infantry (Foxtrot)", "killed_by": "infantry", "near": "Petrovice"},
    ],
}

# ----------------------------------------------------------------------------
# FAKE log of a finished game, for the after-action review.
# ----------------------------------------------------------------------------
FAKE_GAME_LOG = {
    "result": "EAST LOST at minute 58",
    "events": [
        {"minute": 6,  "type": "enemy_ground_move",        "what": "West infantry in trucks near Lany"},
        {"minute": 14, "type": "town_lost_to_ground",      "what": "Dolina taken by West infantry"},
        {"minute": 19, "type": "helo_assault",             "what": "2x UH-60 landed infantry near Petrovice"},
        {"minute": 20, "type": "own_vehicle_lost_to_helo", "what": "T72 killed by AH-1 near Vidlakov"},
        {"minute": 23, "type": "town_lost_after_helo_assault", "what": "Petrovice taken (value 400)"},
        {"minute": 31, "type": "helo_assault",             "what": "3x UH-60 landed infantry near Mirov"},
        {"minute": 33, "type": "own_vehicle_lost_to_helo", "what": "2x BMP killed by AH-1 near Mirov"},
        {"minute": 34, "type": "town_lost_after_helo_assault", "what": "Mirov taken (value 200)"},
        {"minute": 41, "type": "no_enemy_tanks_seen",      "what": "no West tanks seen so far this game"},
        {"minute": 47, "type": "helo_assault",             "what": "3x UH-60 landed infantry at the East base"},
        {"minute": 52, "type": "base_building_lost_to_satchel", "what": "control center destroyed by satchel charges"},
    ],
    "east_spending": {"T72": 9, "BMP": 6, "SOLDIER": 40, "AA_SOLDIER": 0, "SHILKA": 0, "STATIC_AA_GUN": 0},
}


# ----------------------------------------------------------------------------
# Talking to the model
# ----------------------------------------------------------------------------
def ask_model(messages, think, temperature, max_tokens):
    """Send a chat to Ollama and return (answer_text, stats_dict). Shows live progress."""
    body = json.dumps({
        "model": MODEL,
        "stream": True,
        "think": think,
        "messages": messages,
        "options": {"num_ctx": CONTEXT_TOKENS, "temperature": temperature,
                    "num_predict": max_tokens},
    }).encode("utf-8")
    request = urllib.request.Request(OLLAMA_URL, data=body,
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    thinking, content, final = [], [], {}
    print("  waiting for the model (the first call can take 20 s while it loads)...")
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            for raw in response:
                line = raw.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    print("\nOllama error:", data["error"])
                    sys.exit(1)
                message = data.get("message", {})
                if message.get("thinking"):
                    thinking.append(message["thinking"])
                if message.get("content"):
                    content.append(message["content"])
                if (len(thinking) + len(content)) % 10 == 0:
                    sys.stdout.write("\r  working... %3ds   thinking %d tokens, answer %d tokens   " % (
                        time.time() - started, len(thinking), len(content)))
                    sys.stdout.flush()
                if data.get("done"):
                    final = data
    except KeyboardInterrupt:
        print("\n\nStopped by you after %ds. So far: thinking %d tokens, answer %d tokens." % (
            time.time() - started, len(thinking), len(content)))
        if thinking:
            print("Last thing it was thinking:", "".join(thinking)[-300:].replace("\n", " "))
        sys.exit(1)
    except urllib.error.HTTPError as error:
        print("\nOllama rejected the request (HTTP %d):" % error.code)
        print(error.read().decode("utf-8", "replace"))
        sys.exit(1)
    except Exception as error:
        print("\nCould not reach Ollama at", OLLAMA_URL)
        print("Error:", error)
        print("Is Ollama running? Try:  ollama ps")
        sys.exit(1)
    sys.stdout.write("\r" + " " * 70 + "\r")

    if SHOW_THINKING and thinking:
        print("----- model thinking -----")
        print("".join(thinking))
        print("--------------------------")
    capped = final.get("done_reason") == "length"
    if capped:
        print("  CAP HIT: used all %d tokens (%d on thinking) before finishing, at think=%s." % (
            max_tokens, len(thinking), think))
        if thinking:
            print("  It was still thinking about: ..." + "".join(thinking)[-250:].replace("\n", " "))

    eval_count = final.get("eval_count", 0)
    eval_seconds = final.get("eval_duration", 0) / 1e9
    stats = {
        "seconds": round(time.time() - started, 1),
        "prompt_tokens": final.get("prompt_eval_count", 0),
        "output_tokens": eval_count,
        "thinking_tokens": len(thinking),
        "tokens_per_second": round(eval_count / eval_seconds, 1) if eval_seconds else 0,
        "think": think,
        "capped": capped,
    }
    return "".join(content), stats


def extract_json(text):
    """Pull the first {...} block out of the model's answer."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found in the answer")
    return json.loads(text[start:end + 1])


LOWER_THINK = {"high": "medium", "medium": "low", "low": "low"}


def ask_for_json(messages, validate, think, temperature, max_tokens):
    """Ask, parse, validate. On failure, show the model its mistakes and try again.
    If it ran out of tokens while thinking, the next try uses a lower reasoning level."""
    all_stats = []
    parsed, problems = None, []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        answer, stats = ask_model(messages, think, temperature, max_tokens)
        all_stats.append(stats)
        try:
            parsed = extract_json(answer)
            problems = validate(parsed)
        except ValueError as error:
            parsed, problems = None, ["Answer was not valid JSON: %s" % error]
        if not problems:
            break
        if attempt < MAX_ATTEMPTS:
            if stats["capped"]:
                think = LOWER_THINK[think]
                print("Attempt %d ran out of tokens. Trying again at think=%s." % (attempt, think))
                continue
            print("Attempt %d rejected, asking the model to fix it:" % attempt)
            for problem in problems:
                print("   -", problem)
            messages = messages + [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": "Your answer was rejected for these reasons:\n- "
                 + "\n- ".join(problems) + "\nSend the corrected JSON only."},
            ]
    return parsed, problems, all_stats


def print_stats(stats):
    for number, s in enumerate(stats, 1):
        print("call %d (think=%s): %ss, %d tokens in, %d out (%d thinking), %s tokens/s" % (
            number, s["think"], s["seconds"], s["prompt_tokens"], s["output_tokens"],
            s["thinking_tokens"], s["tokens_per_second"]))


def lever_text():
    roles = "\n".join("  %s: %s" % (name, note) for name, (_, note) in ROLES.items())
    orders = "\n".join("  %s: %s" % (name, note) for name, (_, note) in ORDERS.items())
    menu = "\n".join("  %s: %d (needs %s) - %s" % (name, cost, needs, note)
                     for name, (cost, needs, note) in BUY_MENU.items())
    return roles, orders, menu


# ----------------------------------------------------------------------------
# PLAN: state in, orders out
# ----------------------------------------------------------------------------
PLAN_SYSTEM = """You are the East commander in MFCTI, a capture-the-island wargame in Operation Flashpoint.
You win by holding towns (they pay income) and destroying the enemy base.
You command 8 AI teams. You do not control individual soldiers.

For each team you choose a ROLE and an ORDER.
A role decides what the team is re-equipped with from now on. It does not swap vehicles it already has.
ROLES:
{roles}
ORDERS:
{orders}
Only MOVE_TO_POINT uses "target" (a town name). For every other order set "target": null.

You may also buy things, if you own the building they need:
{menu}
Total cost must not be more than your funds. Money you do not spend is saved for later.

Rules for a good plan:
- You only know what your side has spotted. Work out what the enemy is doing and counter THAT threat
  with the roles and purchases that actually counter it.
- Keep enough teams taking towns that you do not lose the economy.
- Your orders must match your intent. If the intent says a team defends the base, a team must have DEFEND_BASE.
- A threat that is killing your units right now deserves a real share of your funds.

- Work in this order: list the threats first, name what counters each one, then write orders and
  purchases that USE those counters. A plan that names a counter and then does not use it is rejected.

Answer with ONE JSON object and nothing else, in exactly this shape and field order:
{{
  "threats": [
    {{"threat": "what the enemy is doing, from what you spotted or the playbook",
      "counters": ["ROLE or PURCHASE names from the lists above that counter it"]}}
  ],
  "teams": {{
    "Alpha": {{"role": "ROLE", "order": "ORDER", "target": null}},
    "... one entry for each of the 8 teams ...": {{}}
  }},
  "purchases": [{{"unit": "UNIT_NAME", "qty": 1}}],
  "unspent_reason": "one sentence on why you kept the money you did not spend",
  "intent": "one or two sentences on your plan"
}}"""


def load_playbook_text():
    if not os.path.exists(PLAYBOOK_FILE):
        return ""
    with open(PLAYBOOK_FILE, "r", encoding="utf-8") as handle:
        return handle.read()


def build_plan_messages():
    roles, orders, menu = lever_text()
    system = PLAN_SYSTEM.format(roles=roles, orders=orders, menu=menu)
    user = "CURRENT SITUATION:\n" + json.dumps(FAKE_STATE, indent=1)
    user += "\n\nTOWN VALUES (income):\n" + json.dumps(TOWN_VALUES)
    playbook = load_playbook_text()
    if playbook:
        user += ("\n\nPLAYBOOK - what you learned from earlier games against this same opponent."
                 "\nUse it to prepare for what they tend to do:\n" + playbook)
    user += "\n\nGive your orders now."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def norm(name):
    """'Shilka' or 'infantry aa' -> 'SHILKA' / 'INFANTRY_AA'. Harmless, so fix it here."""
    if isinstance(name, str):
        return name.strip().upper().replace(" ", "_").replace("-", "_")
    return name


def validate_plan(plan):
    problems = []
    teams = plan.get("teams")
    if not isinstance(teams, dict):
        return ['"teams" is missing or is not an object']
    for entry in teams.values():
        if isinstance(entry, dict):
            entry["role"] = norm(entry.get("role"))
            entry["order"] = norm(entry.get("order"))
    for item in plan.get("purchases") or []:
        if isinstance(item, dict):
            item["unit"] = norm(item.get("unit"))
    for threat in plan.get("threats") or []:
        if isinstance(threat, dict) and isinstance(threat.get("counters"), list):
            threat["counters"] = [norm(c) for c in threat["counters"]]
    for name in TEAMS:
        entry = teams.get(name)
        if not isinstance(entry, dict):
            problems.append("team %s is missing" % name)
            continue
        if entry.get("role") not in ROLES:
            problems.append("team %s has an illegal role: %r" % (name, entry.get("role")))
        order = entry.get("order")
        if order not in ORDERS:
            problems.append("team %s has an illegal order: %r" % (name, order))
        target = entry.get("target")
        if order == "MOVE_TO_POINT" and target not in TOWN_VALUES:
            problems.append("team %s MOVE_TO_POINT needs a real town as target, got %r" % (name, target))
        if order != "MOVE_TO_POINT" and target is not None:
            entry["target"] = None          # harmless, so fix it here instead of spending a retry
            plan.setdefault("_notes", []).append("ignored a target on %s (%s takes none)" % (name, order))
        if entry.get("role") == "AIR" and not FAKE_STATE["base"]["air_factory"]:
            problems.append("team %s cannot have role AIR: you have no air factory" % name)
    for name in teams:
        if name not in TEAMS:
            problems.append("unknown team: %r" % name)

    total = 0
    purchases = plan.get("purchases", [])
    if not isinstance(purchases, list):
        problems.append('"purchases" must be a list')
        purchases = []
    for item in purchases:
        unit = item.get("unit") if isinstance(item, dict) else None
        qty = item.get("qty") if isinstance(item, dict) else None
        if unit not in BUY_MENU:
            problems.append("illegal purchase: %r" % unit)
            continue
        cost, needs, _ = BUY_MENU[unit]
        if not FAKE_STATE["base"].get(needs, False):
            problems.append("cannot buy %s: you have no %s" % (unit, needs))
        elif not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
            problems.append("purchase %s has a bad qty: %r" % (unit, qty))
        else:
            total += cost * qty
    if total > FAKE_STATE["funds"]:
        problems.append("purchases cost %d but funds are only %d" % (total, FAKE_STATE["funds"]))
    reason = plan.get("unspent_reason")
    if not isinstance(reason, str) or not reason.strip():
        problems.append('"unspent_reason" is missing')

    in_use = set()
    for entry in teams.values():
        if isinstance(entry, dict):
            in_use.add(entry.get("role"))
    for item in purchases:
        if isinstance(item, dict):
            in_use.add(item.get("unit"))
    threats = plan.get("threats")
    if not isinstance(threats, list) or not threats:
        problems.append('"threats" must be a non-empty list')
    else:
        for number, threat in enumerate(threats, 1):
            counters = threat.get("counters") if isinstance(threat, dict) else None
            if not isinstance(counters, list) or not counters:
                problems.append("threat #%d names no counters" % number)
                continue
            unknown = [c for c in counters if c not in ROLES and c not in BUY_MENU]
            if unknown:
                problems.append("threat #%d has counters that are not a ROLE or PURCHASE name: %s" % (
                    number, ", ".join(str(c) for c in unknown)))
            elif not any(c in in_use for c in counters):
                problems.append("threat #%d: you named %s as counters but no team has that role and "
                                "nothing like it is bought" % (number, ", ".join(counters)))
    return problems


def run_plan():
    using_playbook = os.path.exists(PLAYBOOK_FILE)
    print("Model: %s    Playbook: %s" % (MODEL, "YES" if using_playbook else "none"))
    print("Asking for orders...\n")
    plan, problems, stats = ask_for_json(build_plan_messages(), validate_plan, THINK_PLAN, TEMP_PLAN,
                                         MAX_OUT_PLAN)

    if plan:
        print("THREATS IT SEES:")
        for threat in plan.get("threats", []) or []:
            if isinstance(threat, dict):
                print("   - %s" % threat.get("threat", ""))
                print("       counters: %s" % ", ".join(str(c) for c in threat.get("counters", []) or []))
        print("INTENT:", plan.get("intent", ""))
        print()
        print("%-8s %-13s -> %-14s %-23s %s" % ("TEAM", "OLD ROLE", "NEW ROLE", "ORDER", "TARGET"))
        teams = plan.get("teams") if isinstance(plan.get("teams"), dict) else {}
        for name in TEAMS:
            entry = teams.get(name) if isinstance(teams.get(name), dict) else {}
            old = FAKE_STATE["teams"][name]
            changed = "*" if (entry.get("role") != old["role"] or entry.get("order") != old["order"]) else " "
            print("%-8s %-13s -> %-14s %-23s %s %s" % (
                name, old["role"], entry.get("role", "?"), entry.get("order", "?"),
                entry.get("target") or "", changed))
        print("(* = changed from the current role or order)")
        print()
        print("PURCHASES:")
        total = 0
        for item in plan.get("purchases", []) or []:
            if isinstance(item, dict) and item.get("unit") in BUY_MENU and isinstance(item.get("qty"), int):
                line_cost = BUY_MENU[item["unit"]][0] * item["qty"]
                total += line_cost
                print("   %2d x %-16s %6d" % (item["qty"], item["unit"], line_cost))
        funds = FAKE_STATE["funds"]
        print("   total %d of %d funds (%d%%)" % (total, funds, round(100 * total / funds)))
        print("   unspent because:", plan.get("unspent_reason", ""))
        for note in plan.get("_notes", []):
            print("   note:", note)
        print()

    print("RESULT:", "LEGAL - the game could carry this out" if not problems else "REJECTED")
    for problem in problems:
        print("   -", problem)
    print_stats(stats)


# ----------------------------------------------------------------------------
# REVIEW: finished game in, playbook out
# ----------------------------------------------------------------------------
def count_facts(log):
    """The code does the counting. Returns {event_type: {"times", "minutes", "what"}}."""
    facts = {}
    for event in log["events"]:
        fact = facts.setdefault(event["type"], {"times": 0, "minutes": [], "what": []})
        fact["times"] += 1
        fact["minutes"].append(event["minute"])
        fact["what"].append(event["what"])
    return facts


def facts_text(facts):
    lines = []
    for name, fact in facts.items():
        lines.append("  %s: %d time(s), minute %s - %s" % (
            name, fact["times"], ", ".join(str(m) for m in fact["minutes"]), "; ".join(fact["what"])))
    return "\n".join(lines)


REVIEW_SYSTEM = """You are the East commander in MFCTI, a capture-the-island wargame in Operation Flashpoint.
The game is over. Below are the facts of the game, already counted for you, and what you spent money on.
Write a short, honest after-action review to read before the next game against the same opponent.

Every finding must name the one FACT it rests on: a fact name from the list, or "spending".
Do not claim a cause the facts do not show. Do not recount the facts; they are already counted.

Next game you can only change three things. Every change must name one item from these lists:
ROLES (lever "ROLE", qty = number of teams):
{roles}
ORDERS (lever "ORDER", qty = number of teams):
{orders}
PURCHASES (lever "PURCHASE", qty = number of units):
{menu}
Each change must counter one of your findings, and the item must actually be able to counter it.
Give 3 to 5 changes, most important first.

Answer with ONE JSON object and nothing else, in exactly this shape:
{{
  "opponent_tendencies": [{{"finding": "short statement", "fact": "FACT_NAME"}}],
  "what_beat_us":        [{{"finding": "short statement", "fact": "FACT_NAME"}}],
  "changes_next_game":   [{{"lever": "ROLE", "item": "NAME", "qty": 1, "by_minute": 10, "because": "short reason"}}]
}}"""


def validate_review(review):
    problems = []
    facts = count_facts(FAKE_GAME_LOG)
    for key in ("opponent_tendencies", "what_beat_us"):
        findings = review.get(key)
        if not isinstance(findings, list) or not findings:
            problems.append('"%s" must be a non-empty list' % key)
            continue
        for number, item in enumerate(findings, 1):
            label = "%s #%d" % (key, number)
            if not isinstance(item, dict) or not isinstance(item.get("finding"), str):
                problems.append("%s must be an object with a finding" % label)
            elif item.get("fact") != "spending" and item.get("fact") not in facts:
                problems.append("%s: %r is not a fact name. Use one of: %s, spending" % (
                    label, item.get("fact"), ", ".join(facts)))

    changes = review.get("changes_next_game")
    lever_lists = {"ROLE": ROLES, "ORDER": ORDERS, "PURCHASE": BUY_MENU}
    if not isinstance(changes, list) or not changes:
        problems.append('"changes_next_game" must be a non-empty list')
    else:
        for number, item in enumerate(changes, 1):
            label = "changes_next_game #%d" % number
            if not isinstance(item, dict):
                problems.append("%s must be an object" % label)
                continue
            item["lever"], item["item"] = norm(item.get("lever")), norm(item.get("item"))
            lever, name, qty = item.get("lever"), item.get("item"), item.get("qty")
            if lever not in lever_lists:
                problems.append("%s: lever must be ROLE, ORDER or PURCHASE, got %r" % (label, lever))
            elif name not in lever_lists[lever]:
                problems.append("%s: %r is not a valid %s" % (label, name, lever))
            if not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
                problems.append("%s: qty must be a whole number of 1 or more" % label)
            elif lever in ("ROLE", "ORDER") and qty > len(TEAMS):
                problems.append("%s: you only have %d teams" % (label, len(TEAMS)))
            if not isinstance(item.get("by_minute"), int):
                problems.append('%s: "by_minute" must be a whole number' % label)
            if not isinstance(item.get("because"), str) or not item.get("because", "").strip():
                problems.append('%s: "because" is missing' % label)
    return problems


def finding_line(item, facts):
    """The code, not the model, states how often something happened."""
    if item["fact"] == "spending":
        return "%s  [from spending]" % item["finding"]
    fact = facts[item["fact"]]
    seen = "seen once" if fact["times"] == 1 else "seen %d times" % fact["times"]
    return "%s  [%s, minute %s]" % (item["finding"], seen, ", ".join(str(m) for m in fact["minutes"]))


def change_line(item):
    unit = "teams" if item["lever"] in ("ROLE", "ORDER") else "units"
    return "%d %s %s by minute %d - %s" % (item["qty"], unit, item["item"], item["by_minute"], item["because"])


def run_review():
    print("Model: %s" % MODEL)
    print("Reviewing the fake game...\n")
    facts = count_facts(FAKE_GAME_LOG)
    roles, orders, menu = lever_text()
    system = REVIEW_SYSTEM.format(roles=roles, orders=orders, menu=menu)
    user = ("RESULT: %s\n\nFACTS (counted by the game):\n%s\n\nYOUR SPENDING (units bought):\n%s" % (
        FAKE_GAME_LOG["result"], facts_text(facts), json.dumps(FAKE_GAME_LOG["east_spending"])))
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    review, problems, stats = ask_for_json(messages, validate_review, THINK_REVIEW, TEMP_REVIEW,
                                           MAX_OUT_REVIEW)
    if problems or not review:
        print("Review REJECTED after %d attempts. Nothing was saved." % MAX_ATTEMPTS)
        for problem in problems:
            print("   -", problem)
        print_stats(stats)
        return

    playbook = {
        "games_played": 1,
        "last_result": FAKE_GAME_LOG["result"],
        "opponent_tendencies": [finding_line(x, facts) for x in review["opponent_tendencies"]],
        "what_beat_us": [finding_line(x, facts) for x in review["what_beat_us"]],
        "changes_to_make": [change_line(x) for x in review["changes_next_game"]],
    }
    with open(PLAYBOOK_FILE, "w", encoding="utf-8") as handle:
        json.dump(playbook, handle, indent=1)

    for key in ("opponent_tendencies", "what_beat_us", "changes_to_make"):
        print(key.upper().replace("_", " ") + ":")
        for line in playbook[key]:
            print("   -", line)
        print()
    print("Saved to", PLAYBOOK_FILE)
    print_stats(stats)


def run_reset():
    if os.path.exists(PLAYBOOK_FILE):
        os.remove(PLAYBOOK_FILE)
        print("Deleted", PLAYBOOK_FILE)
    else:
        print("No playbook to delete.")


if __name__ == "__main__":
    print("commander_test version %d" % VERSION)
    command = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if command == "plan":
        run_plan()
    elif command == "review":
        run_review()
    elif command == "reset":
        run_reset()
    else:
        print(__doc__)
