"""
relay.py (version 33) - the relay between the game and your local model.

The game reports each commander's situation here once a minute. This program
works out what changed. If nothing did, the standing orders go straight back
and the model is not asked. If something did, it asks the model, checks the
answer against the facts, and returns orders the game's scripts can read.

New in version 33 (25 October, his third game: he flew an armed UH-60, which the game calls a transport
helicopter, killed 20 of East's men with rockets, and the air response never started, because it waited only for
attack helicopters and planes):
  - the air response starts for ANY enemy aircraft, transport helicopters included

Version 32 (22 October, after his game in an AH-64: East saw him at minute 42, switched one team to
anti-air and nothing reached him; "if there is even a single enemy attack helo in the air, there has to be an
immediate response"):
  - AIR RESPONSE, a reflex, not the model's choice: the report an enemy attack helicopter or plane is first seen,
    the commander buys 2 anti-air soldiers into each of the 3 teams nearest it (they run out and join their team
    wherever it is) and 2 into his own guard at the base. Again every 5 minutes while enemy aircraft are seen.
    With an air factory, one team, the fit one nearest the base, becomes the side's attack helicopter team (role
    AIR) for the rest of the game. The model is told; it cannot undo it
  - needs LLM\\Report.sqs version 19 and LLM\\AirBuy.sqs (the 7th part of the reply is the list to buy)

Version 31 (19 October: both sides under the relay, to give the commander a real opponent):
  - --rules-side=West (or East): that side is commanded by the rules alone, the other by the model. With
    LLM\\Init.sqs version 11 and llmTestSides = [east, west] in LLM\\TestStart.sqf the mission hands both sides
    to the relay; run_trials.ps1 version 18 sets this up (kinds duel, versus and versusflip)
  - the log line at the start says which side, if any, is rules only

Version 30 (after the first Everon trial, 18 October, and his own way of defending a base as commander):
  - COMMANDER'S GUARD: with LLM\\Report.sqs version 18 the mission keeps 4 HE stations at the base besides the 2
    mortars, and the commander buys one soldier per gun into his own team, who mans it. No field team is tied up
    as mortar crew any more; the crew of version 28 is used only with an older report
  - RESISTANCE AT THE BASE: resistance that kills our men from within 400 m of the base is an attack on it.
    The enemy side still counts from 2000 m. (On Everon the start at Durras lies 300 m from a resistance town,
    whose garrison killed 12 of our men at the base without any alarm)
  - an older-report crew is kept while it has 2 men, not dropped as soon as it falls below 4
  - the HE stations, how many are manned, and the guard's size are in the log and in base_under_fire

Version 29 (after the third base-defence test, 17 October: two mortars built and manned, but the crew
team refilled at the barracks next to them to 12 men):
  - CREW SIZE: the reply names the crew team (its 6th part), and the mission stops that team buying men once it
    has llmCrewMax (4, set in LLM\\Init.sqs). A small team is preferred as crew: the nearest fit foot team with
    at most 6 men within 1500 m of the base, else the nearest fit foot team as before
  - LIFT FIRE: the mortars stop firing while any of our teams, or the base itself, is within 200 m of the point
    they fire on (the counterattack goes to that same point), and fire again when it is clear
  - the rounds the mortars have fired are in the log ("mortar_shots" in the state)
  - needs LLM\\Report.sqs version 17, which takes the crew from the reply, ends a fire mission when the reply has
    none, and counts the rounds fired; LLM\\Init.sqs version 9; and the crew cap in Main\\UpdateIndependentAI.sqs

Version 28 (after the second base-defence test, 16 and 17 October: no false alarms any more, but still no
mortars. The stock commander never reaches its mortar build for an LLM side, and a mortar the mission builds has
no gunner: only a team on the stock defend script mans the guns at a base):
  - MORTAR CREW: while the side has mortars, one foot team, the fit one nearest the base, is its crew. It goes to
    the base and defends it (order 4), which mans the mortars. It is kept until the mortars are gone or it is no
    longer fit, is never sent to counterattack or to hold a town, and is not kicked. The model is told its name
  - needs LLM\\Report.sqs version 16, which builds the side's two mortars itself (35 m east and west of the base,
    through the request a player's build uses, paid from the side's funds) and reports how many are manned

Version 27 (after the base-defence test of 15 October: the counterattack and place 0 worked, the teams
reached the attacker's position within 2 to 50 m, and the made-up attacker ran its 8 minutes. Two faults: the
resistance garrison of a town near the base, killing our men from 0.8 to 2 km, also counted as an attack on the
base and kept three teams chasing it for up to 18 minutes; and East had no mortars in either game, so no fire
mission was ever given):
  - only the enemy side's killers count. Needs LLM\\Report.sqs version 15, which sends the killer's side.
    With version 14 every killer counts, as before
  - the report says whether mortars are switched off by the addon or the server; the relay says so once
  - LLM\\Report.sqs 15 comes with Main\\UpdateCommanderAI.sqs changed: a side the LLM commands builds its two
    mortars as soon as it has the money (the stock commander builds one with a 6 percent chance per pass)

Version 26 (after his first game against it, 12 October: he sat in a tank 1 km from the East base and
shot it up from cover for minutes. Nobody counterattacked, no fire mission came, and the model was told only
"a single Abrams near Velka Ves": losses and sightings were reported by nearest town, so nothing said that the
base itself was under fire, or from where):
  - BASE UNDER FIRE: anything of the enemy side seen within BASE_THREAT_METRES (2000) of the base, or a killer
    of our men standing that close, starts a threat. It ends after BASE_THREAT_CLEAR_MINUTES (4) without such
    evidence. The model is told when it starts, every 3 minutes while it lasts, and when it ends, with the
    attacker, its distance and what is being done about it ("base_under_fire" in the situation)
  - COUNTERATTACK by rule: up to COUNTER_TEAMS (3) fit teams within COUNTER_REACH_METRES (4000) of the attacker,
    able to fight armour if it is armoured, teams with working vehicles first, are sent to the attacker's
    position (order 1, place 0). They follow it when it moves more than 150 m and go back to their own orders
    when the threat ends. They are not kicked and do not hold towns meanwhile. Aircraft alone start no
    counterattack
  - FIRE MISSION: while the threat lasts the side's mortars (built by the stock commander) are told to fire on
    the attacker's position. The aim point changes only when the attacker moves more than 150 m, because a
    mortar re-aims for 50 seconds every time the point changes
  - --no-defence switches both off. --test-threat=N makes up an attacker 800 m from the base at game minute N
    for 8 minutes, so a headless game exercises the whole chain
  - needs report layout 14 (LLM\\Report.sqs version 14): positions of what is seen, the killer's position for
    each man lost, the mortars, and two new parts of the reply (places and a fire mission). With an older
    report script nothing of this is used

Version 25 (after the nine-game trial of 10 October on version 24: stock 12, 9, 14; rules only 15, 15,
18; model 18, 13, 16. No commanded team froze and losses did not rise. What limits a game now: a team that
takes a town leaves at once, the defenders who hid come back to the flag and take the town again, and the
team returns. A rules-only game made 23 to 25 captures to end with 15 to 18 towns; most lost towns were lost
within three minutes of being taken. The stock mission does the same):
  - HOLD: the team nearest a town its side has just taken (within HOLD_REACH_METRES, on the order TAKE_TOWNS)
    goes back to the flag and stays HOLD_MIN_MINUTES (2) once it is there, and longer while it is still
    killing or losing men there or the town has been taken back, up to HOLD_MAX_MINUTES (5) in all. Then it goes on taking towns. A holding
    team is not kicked for standing still. Its standing order does not change and the model is told nothing
    new; the hold is a rule on top of the plan. The option --no-hold switches it off
  - each log row says which teams hold which towns ("holding"), and why a hold ended
  - needs the mission scripts of 9 October, fifth pack, as before

Version 24 (after the overnight trial of 10 October on version 23. In the two rules-only games the
team fixes held: no leader hiding or attacking on the engine's own order, and men lost did not rise. In none
of the six games was a driver stuck on a lost commander's order. Both model games were lost to the model
itself: it ran at 58 and then 7 tokens a second where it had run at 110 to 140, so one answer took one to
two minutes. The relay waited up to 170 seconds for each, the game had given up long before, and the
commander went silent: 12 and 17 reports in a game where a model game has 52 to 58):
  - one plan may take MODEL_DEADLINE seconds of real time (30), all attempts together. Then the rule-based
    plan is used for that report, the same plan a --rules game uses. The option --deadline=N changes it
  - after MODEL_FAILS_TO_REST failures in a row (2) the model is left alone for MODEL_REST_SECONDS (180) and
    the rules command; then it is tried again. Every such report is marked "model_failed" in the session log
  - a model that fails before any orders exist no longer leaves the teams without orders: the rules give them
  - needs the mission scripts of 9 October, fifth pack, as before. No rule of the commander changed

Version 23 (after six matched headless games on version 22 with the engine's diagnostic commands:
stock 12, 16; rules only 15, 13; model 12, 12. The diagnostics named what holds a team that stands still.
Three causes, none of them in the relay:
  1. the mission sets every team to combat mode "RED". Under it the game lets each man hide on his own,
     in a subgroup of his own, when an enemy is known and nobody has given him a target. The team's order
     then sits in an empty main subgroup until every man has stopped hiding. Foot teams, all three kinds.
  2. the unit that commands the leader's tank goes off to attack a target, in a subgroup of its own, and
     that attack does not end while the target is known and alive. The leader rides along; the team's
     order waits in the same empty main subgroup. One tank team stood 22, 13 and 8 minutes this way through nine kicks.
  3. an engine fault: a tank driver who is left in command of his tank when its commander is killed keeps
     that commander's last driving order. He stays at that spot, and every later order ends at once because
     he reports that he has arrived. Two teams, 17 and 20 minutes, one of them in a stock game.
The mission scripts of the fifth pack of 9 October answer 1 and 2 for teams the LLM commands (combat mode
"YELLOW": fire at will and keep formation; and the crew of the leader's vehicle are never handed a target
by the team leader). The engine patch apply_llm_engine.py answers 3 for every vehicle in the game.
No rule changed in this version of the relay):
  - reads report layout 13: the report says which of the project's engine changes the game has
    (0 none, 1 diagnostics, 2 diagnostics and the driver fix). The relay says so once if it is below 2
  - the diagnostic text for a vehicle now ends with mm=, the driving order its commander last gave its
    driver (FORMATION means none). tools\\frozen_diag.py counts what held each standing team
  - needs mission scripts of 9 October, fifth pack (report script version 13)

Version 22 (after nine matched headless games on version 21 with the capture-circle recount: stock
12, 6, 12; rules only 17, 12, 13; model 18, 15, 13. No team stood at a flag without taking it. What decided
games was teams that stand still with an order pending: a tank team stood 38 minutes through five kicks.
The engine source says why a kick cannot help: an order from a script goes to the back of a subgroup's
queue, and an order the engine issues by itself goes to the front and is not removed by a script order.
No rule changed in this version; it only looks):
  - reads report layout 12: three texts per team from the engine's new diagnostic commands (llmUnitInfo,
    llmGroupInfo; engine patch apply_llm_diag.py, now apply_llm_engine.py), sent while a team's leader stands still. They name the
    order at the front of the queue, who issued it, and the unit's state. Printed with every kick and
    kept in the session log; tools\\frozen_diag.py lists them for every team that stood still
  - the report says whether the game has those commands; the relay says so once if it does not
  - needs mission scripts of 9 October, fourth pack (report script version 12)

Version 21 (after nine matched headless games on version 20: stock 15, 11, 14; rules only 14, 9, 12;
model 16, 14, 18, from the same three starts. The rules-only games were lost to a fault in the mission, not
in the commander: a town's capture circle is only counted when it goes from empty to occupied, so teams that
crowd round a flag, or one abandoned vehicle beside it, stop the town changing hands. Seven teams stood round
one flag for 36 minutes. The mission scripts of the third pack of 9 October repair that (LLM\\TownWatch.sqs);
nothing in the relay's rules changed):
  - reads report layout 11. For the vehicle the leader is in: told to stop, engine running, fuel, and
    whether the crewman who commands it is in a different subgroup from the leader, whether that subgroup
    holds an order, and how far away the man it follows is. Three teams in the trial were not freed by any
    kick; these values are there to show why. They are printed with every kick and kept in the session log
  - reads how many towns the mission's recount has handed to each side and prints it when it changes
  - needs mission scripts of 9 October, third pack (report script version 11)

Version 20 (after three headless games on version 19, which took 16, 14 and 15 towns; the stock
commander's two full games ended at 12 and 13. All six teams that froze at base were freed by one kick,
but only after 7 to 10 minutes each. Two tank teams parked on a town they had just taken were not freed by
any kick. Eight of eleven recalls were of a single, working, fully crewed vehicle):
  - the frozen-leader signature is kicked at once. A leader in a vehicle who holds an order of his own,
    at speed 0, in the same place on two reports in a row: that was every base freeze in the trial and
    nothing else. Growth at base no longer restarts the clock for a team already at dispatch size
  - fit to fight is judged by platform: a vehicle team by vehicles that can move and fire, a foot team by
    men. A crewed, working single vehicle is fit
  - rules-only mode (python relay.py FILE --rules): the model is never asked and the fallback plan is used.
    This is the control run that shows what the model adds
  - a team that stays below dispatch size at base without growing is logged (FORM), and the commander is
    told when the side is near its vehicle limit, where a tank team cannot form at all
  - the report carries a layout number. A newer layout than this relay knows is refused; an older one is
    read, with a warning. Two more values per team: the leader's vehicle's height and damage
  - the session log keeps the prompt, every attempt with its rejection reasons, and the model's timings
  - needs mission scripts of 9 October, second pack (report script version 10)

Version 19 (after three headless games on version 18, which took 9, 5 and 4 towns. The model and the
relay made no errors; the time was lost in the game. Whole tank teams stood still at base for the rest of
the game with nothing wrong with them, infantry leaders waited at the heavy factory where they can buy
nothing, and teams the mission had sent out six strong were called home as "half strength"):
  - a formed team that stands still for 4 minutes while its order tells it to move is kicked: every member
    is ordered to the goal one by one, which got a frozen team moving in the trial where the group order
    did not. Three kicks four minutes apart, then one every ten; from the third on, away from base, with
    the 50 m bump. Needs report script version 9. Why it works (engine source, AIGroup::Move and
    AIGroup::IssueCommand): a group order goes to the team's main body only, and a leader who was given an
    order by name is outside the main body until that order is finished. A new order by name replaces it
  - RETURN_TO_BASE is only for a team down to three men or with half its guns out. Six men is the size at
    which the mission sends a tank team out, not a reason to bring it home
  - in the first 6 minutes the tank teams are named before the heavy factory is built. They wait for it and
    buy nothing; any other role starts buying infantry, which leaves room for fewer tanks
  - the briefing states the real win conditions: every town, or the enemy mobile HQ and all his factories
  - each team now reports its leader's seat and speed, whether he has finished his last move order,
    vehicles without a driver and members left behind, so a team that stands still can be explained
  - needs mission scripts of 9 October or later (report script version 9, patched team script)

Version 18 (after six headless games: the stock commander took 12 and 13 towns in 80 minutes, the
model 6, 9 and 10. The stock teams left a captured town within two minutes and went to the nearest town
that was not theirs; the model's teams waited six to nine minutes and were sent 1.3 to 3.4 times as far):
  - the fighting is left to the mission's own team script. The normal order is TAKE_TOWNS: the team takes
    the nearest town that is not yours, then the next, by itself. The model no longer names a town per team
  - the model's job is the force mix (each team's role) and the exceptions: defend a threatened town, defend
    the base, hold key terrain, attack the enemy base, send a team home for repair
  - an exception with no grounds is not rejected: the team is put back on TAKE_TOWNS, and an exception that
    was granted ends by itself when its grounds do (the threat passes, the team is repaired)
  - with a heavy factory at least 4 teams must be tank teams, and no more than 6 may have a vehicle role,
    because the mission limits a side to 20 vehicles
  - key terrain is offered only while the enemy side has been seen near it
  - gone: holding a captured town, re-sending town orders, the bump for stuck vehicles, the armour memory
  - the relay keeps logging if its window is closed or its output is redirected, and every failure is
    written to the session log with its cause
  - needs mission scripts of 8 October or later (the stock commander now buys for the roles set here)

Version 17 (after the second headless run, where the two tank teams sat on captured towns for 40 minutes
and an infantry team was re-tasked four times before it reached anything):
  - DEFEND_TOWN is only for a town where something hostile was seen in the last 10 minutes, one team per town
  - a team strong against armour may not sit on DEFEND_BASE while nothing threatens the base
  - RETURN_TO_BASE is only for a team that needs it: half its men gone, or a damaged or unmanned vehicle
  - a team on the march keeps its order until it arrives (12 minutes at most) unless something happens to it
  - a report with an unreadable sighting in it is repaired, not thrown away

Version 16: wording only. A stuck vehicle team is bumped 50 m, not 150 (report script version 7).

Version 15 (after the first headless run):
  - HOLD_POINT is only offered for key terrain near the base, a town you hold or a town the enemy holds,
    and only to a team within 3 km of it. The model sent a team on an 8 km walk to a hill nobody was near
  - a team that captures a town now holds it until no hostile has been seen there for 3 minutes (10 at most)
  - a vehicle team that has an order to move and has not moved for 6 minutes is lifted clear and sent again
    (needs report script version 6)

Version 14: the start-up line now says whether the mission sent a key terrain list at all.

Version 13:
  - key terrain: the mission now reports the kt and hlz objects placed in the editor. The commander is shown
    the key terrain with the mission maker's descriptions and may send ONE team to hold a point (HOLD_POINT)

Version 12 (same as 11, with the factory announcement corrected). Version 11 (after the second game under model command: 7 towns at minute 81, stock commander 12):
  - ARMOUR roles need a HEAVY factory. With only a light factory MFCTI makes an "armour" team buy Shilkas
  - anti-air roles are refused until enemy aircraft have actually been seen
  - base defence scales with the threat: none in the first 30 minutes unless the enemy is near
  - a team at base with a town order has the order re-sent every 2 minutes (MFCTI drops it while refilling)
  - a team sitting at its target without capturing it is reported and nudged, not left there for an hour
  - a team that captures a town holds it for 3 minutes before moving on, so resistance cannot take it straight back
  - a team the model leaves out of its answer keeps its standing order; the plan is not rejected for that

Since version 10 (after the first full MFCTI game under model command, which it lost by sitting at base):
  - posture is enforced: at most 2 teams defend the base, at least half the ready teams attack,
    and a fit team that is already at base cannot be ordered to return to base
  - roles are enforced: once a vehicle factory exists, at least 3 teams must have a vehicle role
  - a team refitting inside the base is no longer reported as stuck
  - losses are recorded where the fight was, not at the base where the leader respawned
  - armour seen at a town is remembered; only a team strong against armour may be sent there
  - helicopter sightings and enemy town captures no longer wake the model every minute
  - a lone leader is held at base until his team has formed
  - "no gunner" is told apart from "gun out" (needs the version 4 report script)

Since version 9:
  - MFCTI control: the model now commands a side in the MFCTI mission. For each team it
    picks a role and an order (take a named town, defend a town, defend the base, return
    to base for repair, attack the enemy base, or act on its own)
  - knows the MFCTI addon's own vehicle names, static guns and support trucks
  - losses caused by a crash or by friendly fire are reported as such

Since version 7:
  - understands reports from the MFCTI mission (observer mode): it prints each side's
    towns, funds, buildings, teams, sightings, kills and losses, and sends no orders

Since version 6:
  - it remembers what has been destroyed, so it stops planning around an enemy that is dead
  - a running battle record per point: men lost there, to what, and what was destroyed there
  - a group that recovers from fleeing, or is stuck, has its order sent again

Since version 5:
  - each vehicle reports whether it can still move and fire, and has ammo and fuel
  - a new order, DISMOUNT: crews leave vehicles that cannot move and carry on on foot
  - an enemy vehicle that sits still and hurts nobody is flagged as probably disabled
  - passengers riding in a vehicle are counted; soldiers are no longer mistaken for vehicles

Since version 4:
  - each group's make-up (riflemen, RPGs, tanks, helicopters) and what it can fight
  - kills your groups made, and what killed your own men
  - a group that is not carrying out its order is reported as not moving
  - an enemy moving back and forth no longer triggers a new decision every minute
  - one commander per side, so two sides can be run at once

Run:   python relay.py          (leave the window open; Ctrl+C to stop)
       python relay.py FILE     (the same, with everything it would print written to FILE instead;
                                 run_trials.ps1 starts it this way)
       python relay.py FILE --rules   (the control run: the model is never asked)
Uses only the Python standard library.
"""

import builtins
import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = 33
REPORT_LAYOUT = 14           # the layout number LLM\\Report.sqs version 14 sends as the 12th part of a report
ENGINE_LEVEL = 2             # what the engine patch apply_llm_engine.py gives: 1 diagnostics, 2 also the driver fix
RULES_ONLY = False           # set by --rules: never ask the model, use the rule-based fallback plan
RULES_SIDES = set()          # set by --rules-side=West (or East): only that side is commanded by the rules alone
LAST_MODEL_STATS = {}        # what Ollama said about its last answer: token counts and timings
MODEL_DEADLINE_AT = None     # while a plan is being asked for: the clock time after which the model's answer is too late


def clock():
    """Real time in seconds. A function of its own so the tests can move it."""
    return time.time()

# ----------------------------------------------------------------------------
# Settings you can change
# ----------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8777
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gpt-oss:20b"
THINK = "low"                # reasoning effort: low / medium / high
CONTEXT_TOKENS = 8192
MAX_OUTPUT_TOKENS = 2500
TEMPERATURE = 0.4
MAX_ATTEMPTS = 3
MODEL_DEADLINE = 30          # real seconds the model has for one plan, all attempts together. After that the rules decide
HOLD_TAKEN_TOWNS = True      # the team that takes a town holds it for a while before it goes on. --no-hold turns this off
HOLD_REACH_METRES = 600      # the nearest team on TAKE_TOWNS this close to a town just taken is the one that holds it
HOLD_AT_FLAG_METRES = 60     # this close to the flag counts as being there
HOLD_MIN_MINUTES = 2         # it stays at least this long once it is at the flag
HOLD_MAX_MINUTES = 5         # and never longer than this from the moment the hold began
BASE_DEFENCE = True          # counterattack and mortar fire when the base is under fire. --no-defence turns this off
BASE_THREAT_METRES = 2000    # the enemy seen this close to the base, or killing our men from this close, is a threat to it
BASE_THREAT_CLEAR_MINUTES = 4  # the threat ends after this long without such evidence
BASE_THREAT_REMIND_MINUTES = 3 # while it lasts the model is told again this often
COUNTER_TEAMS = 3            # at most this many teams counterattack
COUNTER_REACH_METRES = 4000  # only teams this close to the attacker are sent
COUNTER_RETARGET_METRES = 150  # the counterattack follows the attacker when it moves further than this
FIRE_RETARGET_METRES = 150   # the mortars are re-aimed only when the attacker moves further than this
DANGER_CLOSE_METRES = 200    # the mortars lift fire while one of our teams, or the base, is this close to their target
CREW_PREFER_MEN = 6          # a foot team with at most this many men is preferred as the mortar crew
CREW_KEEP_MEN = 2            # a crew is kept while it has this many men (it refills at the barracks)
RESISTANCE_BASE_METRES = 400 # resistance killing our men from this close to the base is an attack on it
AIR_RESPONSE = True          # buy anti-air soldiers the moment enemy attack aircraft are seen
AIR_TEAMS = 3                # this many teams nearest the aircraft get anti-air soldiers
AIR_SOLDIERS_PER_TEAM = 2    # and this many each (never past 11 men in a team)
AIR_BASE_SOLDIERS = 2        # and the commander's guard at the base this many
AIR_REBUY_MINUTES = 5        # while enemy aircraft are still seen, another wave after this long
AIR_THREAT_CLASSES = ("attack helicopter", "attack plane", "transport helicopter")   # an armed transport helicopter kills too
CREW_PREFER_METRES = 1500    # if it is within this distance of the base
TEST_THREAT_MINUTE = None    # --test-threat=N: a made-up attacker 800 m from the base from game minute N
TEST_THREAT_LENGTH = 8       # for this many game minutes
AIR_CLASSES = ("attack helicopter", "transport helicopter", "attack plane")
HOLD_QUIET_MINUTES = 1.5     # "quiet" means the town ours, no kill at it and no man of the team lost for this long
MODEL_FAILS_TO_REST = 2      # this many failures in a row and the model is left alone for a while
MODEL_REST_SECONDS = 180     # how long, in real seconds. The rule-based plan commands until then
REVIEW_MINUTES = 8           # with no news, re-think the plan this often (game minutes)
COMMIT_MINUTES = 3           # a team keeps a new order at least this long unless it is in trouble
DEFEND_MEMORY_MINUTES = 10   # DEFEND_TOWN needs something hostile seen at the town within this long
REFIT_MEN = 3                # a team ON FOOT this small or smaller is not fit to fight. Vehicle teams are judged by vehicles
SIGHTING_MEMORY_MINUTES = 5  # an enemy seen again at the same place within this time is not news
ROLE_COMMIT_MINUTES = 8      # a team keeps a new role at least this long unless it was wiped out
MAX_BASE_DEFENDERS = 2       # the most ready teams that may sit on DEFEND_BASE once the enemy is near
QUIET_OPENING_MINUTES = 30   # no base defence at all this early unless the enemy has been seen near
AA_MEMORY_MINUTES = 30       # anti-air roles are allowed only this long after enemy aircraft were last seen
RESEND_AT_BASE_MINUTES = 2   # a team at base that was sent to defend a town or hold a point has the order re-sent this often
POINT_NEAR_METRES = 2000     # key terrain is offered only this close to a town where the enemy side was seen
POINT_ENEMY_MINUTES = 15     # and only this long after it was seen there
POINT_REACH_METRES = 3000    # and only to a team this close to it
MAX_POINT_TEAMS = 1          # how many teams may be sent to hold key terrain at once
MIN_TANK_TEAMS = 4           # with a heavy factory, at least this many teams must be ARMOUR or ARMOUR_HEAVY
MAX_VEHICLE_TEAMS = 6        # no more than this many teams may have a vehicle role
VEHICLE_LIMIT = 20           # the mission's own limit on vehicles per side (maxVehicles in InitServer.sqs)
READY_MEN = 4                # a team with fewer members and no vehicle is still forming
STRONG_AT_SOLDIERS = 4       # this many anti-tank soldiers (or one working gun vehicle) counts as strong against armour
BASE_RADIUS = 300            # metres from base that counts as "at base"
REFIT_MINUTES = 8            # a team may sit at base this long buying or repairing before it is put back to work
REFIT_DONE_MINUTES = 3       # a team sent home goes back to taking towns after this long there, once repaired
AIR_ALERT_MINUTES = 10       # enemy aircraft wake the model at most this often
STUCK_MINUTES = 4            # no progress toward its point for this long = "not moving"
FROZEN_MINUTES = 4           # a formed team that has not moved at all for this long, with an order to move, is kicked
FROZEN_AT_TOWN_MINUTES = 8   # the same for a team within 150 m of the town it is taking: it may be fighting for it
FROZEN_METRES = 25           # "has not moved" means its leader is within this distance of where he stood
UNFROZEN_METRES = 150        # a kicked team counts as moving again once it is this far from where it froze
MAX_KICKS = 3                # quick kicks per freeze. From the third on, away from base, the vehicles are also set down 50 m on (the bump)
SLOW_KICK_MINUTES = 10       # after the quick kicks have failed, one more this often
DISPATCH_MEN_VEHICLES = 6    # the mission sends a team with vehicles out at this size
DISPATCH_MEN_FOOT = 9        # and a team on foot at this size. Smaller teams at base are still filling up
OPENING_MINUTES = 6          # before the heavy factory is built, tank teams may be named this early in the game
SIGNATURE_REPORTS = 2        # reports in a row with the frozen-leader signature before the kick
SIGNATURE_KICK_MINUTES = 2   # and the shortest time between two such kicks
FORMATION_STALL_MINUTES = 6  # a team below dispatch size at base that has not grown for this long is logged
NEAR_VEHICLE_LIMIT = 4       # teams' vehicles within this many of the limit: tank teams may be unable to form
HARMLESS_MINUTES = 6         # an enemy vehicle still and harmless this long is "probably disabled"
KILL_MEMORY_MINUTES = 30     # how long a destroyed enemy stays on the commander's "already dead" list
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# Order modes. The number is what the game script receives.
MODES = {
    "ATTACK": (0, "move there and engage anything on the way"),
    "DEFEND": (1, "move there and hold it, returning fire"),
    "AMBUSH": (2, "move there quietly and hold fire until attacked"),
    "DISMOUNT": (3, "crews abandon any vehicle that cannot move, then the group goes there on foot"),
}
LOWER_THINK = {"high": "medium", "medium": "low", "low": "low"}


def print(*args, **kwargs):
    """The relay must keep working when nobody can read it: the window closed, or output sent to a file."""
    try:
        builtins.print(*args, **kwargs)
        sys.stdout.flush()
    except (OSError, ValueError):
        pass


# ----------------------------------------------------------------------------
# What the game's class names mean
# ----------------------------------------------------------------------------
# category -> (how it moves, is it armoured, can it fight armour, can it fight aircraft)
CATEGORIES = {
    "infantry":          ("on foot",  False, False, False),
    "tank":              ("tracked",  True,  True,  False),
    "armoured vehicle":  ("tracked",  True,  True,  False),
    "anti-air vehicle":  ("tracked",  True,  False, True),
    "attack helicopter": ("air",      False, True,  False),
    "transport helicopter": ("air",   False, False, False),
    "attack plane":      ("air",      False, True,  False),
    "car or truck":      ("wheeled",  False, False, False),
    "static gun":        ("fixed in place", False, False, False),
    "unknown vehicle":   ("vehicle",  False, False, False),
}

VEHICLES = [   # (start of class name, plain name, category). First match wins, so longer names go first.
    ("m2staticmg", "static machine gun", "static gun"), ("hestaticmg", "static HE gun", "static gun"),
    ("aastaticmg", "static anti-air gun", "static gun"), ("eastmortar", "mortar", "static gun"),
    ("westmortar", "mortar", "static gun"), ("mortar", "mortar", "static gun"),
    ("eastmobilehq", "mobile HQ", "armoured vehicle"), ("westmobilehq", "mobile HQ", "armoured vehicle"),
    ("eastsalvager", "salvage truck", "car or truck"), ("westsalvager", "salvage truck", "car or truck"),
    ("truck5treammo", "ammo truck", "car or truck"), ("uralreammo", "ammo truck", "car or truck"),
    ("m113", "M113 armoured carrier", "armoured vehicle"),
    ("m1a1", "M1A1 Abrams tank", "tank"), ("m1abrams", "M1 Abrams tank", "tank"), ("m1", "M1 Abrams tank", "tank"),
    ("m3a2", "M3 Bradley", "armoured vehicle"), ("shilka", "Shilka anti-air gun", "anti-air vehicle"),
    ("ka50", "Ka-50 attack helicopter", "attack helicopter"),
    ("m60", "M60 tank", "tank"),
    ("t80", "T-80 tank", "tank"), ("t72", "T-72 tank", "tank"), ("t55", "T-55 tank", "tank"),
    ("m113", "M113 armoured carrier", "armoured vehicle"), ("m2a2", "M2 Bradley", "armoured vehicle"),
    ("bmp2", "BMP-2", "armoured vehicle"), ("bmp", "BMP-1", "armoured vehicle"),
    ("brdm", "BRDM scout car", "armoured vehicle"),
    ("zsu", "Shilka anti-air gun", "anti-air vehicle"), ("vulcan", "Vulcan anti-air gun", "anti-air vehicle"),
    ("mi24", "Mi-24 attack helicopter", "attack helicopter"), ("kamov", "Ka-50 attack helicopter", "attack helicopter"),
    ("cobra", "AH-1 Cobra attack helicopter", "attack helicopter"), ("ah1", "AH-1 attack helicopter", "attack helicopter"),
    ("ah64", "AH-64 Apache attack helicopter", "attack helicopter"),
    ("mi17", "Mi-17 transport helicopter", "transport helicopter"), ("uh60", "UH-60 transport helicopter", "transport helicopter"),
    ("ch47", "CH-47 transport helicopter", "transport helicopter"), ("oh58", "OH-58 scout helicopter", "transport helicopter"),
    ("su25", "Su-25 attack plane", "attack plane"), ("a10", "A-10 attack plane", "attack plane"),
    ("uaz", "UAZ jeep", "car or truck"), ("ural", "Ural truck", "car or truck"), ("jeep", "jeep", "car or truck"),
    ("hmmwv", "HMMWV", "car or truck"), ("truck", "truck", "car or truck"), ("skoda", "car", "car or truck"),
]

LIGHTLY_ARMED = ("m113", "brdm", "eastmobilehq", "westmobilehq")   # armoured, but no use against armour
STATIC_FIGHTS_ARMOUR = ("hestaticmg",)
STATIC_FIGHTS_AIR = ("aastaticmg",)

INFANTRY_LABELS = ("rifleman", "grenadier", "machine gunner", "sniper", "medic", "officer",
                   "anti-tank soldier", "anti-air missile soldier", "special forces soldier",
                   "vehicle crewman on foot")

ANTI_TANK_LAUNCHERS = ("law", "rpg", "at4", "carlgustav", "atlauncher")
ANTI_AIR_LAUNCHERS = ("aalauncher", "9k32", "stinger", "strela")


def describe(class_name, launcher="", is_man=None):
    """Returns (plain name, category, anti_tank, anti_air) for one man or one vehicle.
    is_man comes from the game when it knows; otherwise it is guessed from the class name."""
    name = str(class_name)
    low = name.lower()
    if low.startswith("mfcti116"):          # the MFCTI addon's own copies of the standard classes
        low = low[len("mfcti116"):]
        name = name[len("mfcti116"):]
    is_person = is_man if is_man is not None else (
        low.startswith(("soldier", "officer", "civilian", "heavyg")) or "soldier" in low
        or "grenadier" in low)
    if not is_person:
        for prefix, label, category in VEHICLES:
            if low.startswith(prefix):
                _, _, fights_armour, fights_air = CATEGORIES[category]
                if prefix in LIGHTLY_ARMED:
                    fights_armour = False
                if prefix in STATIC_FIGHTS_ARMOUR:
                    fights_armour = True
                if prefix in STATIC_FIGHTS_AIR:
                    fights_air = True
                return label, category, fights_armour, fights_air
        return "%s (unrecognised vehicle)" % name, "unknown vehicle", False, False

    weapon = str(launcher).lower()
    anti_air = any(token in weapon for token in ANTI_AIR_LAUNCHERS) or (not weapon and low.endswith("aa"))
    anti_tank = (not anti_air) and (any(token in weapon for token in ANTI_TANK_LAUNCHERS)
                                   or (not weapon and (low.endswith("law") or low.endswith("at"))))
    if anti_air:
        label = "anti-air missile soldier"
    elif anti_tank:
        label = "anti-tank soldier"
    elif "mg" in low[-3:]:
        label = "machine gunner"
    elif "sniper" in low:
        label = "sniper"
    elif "medic" in low:
        label = "medic"
    elif "officer" in low:
        label = "officer"
    elif "crew" in low or "pilot" in low:
        label = "vehicle crewman on foot"
    elif "saboteur" in low:
        label = "special forces soldier"
    elif "grenadier" in low or low.startswith("heavyg"):
        label = "grenadier"
    else:
        label = "rifleman"
    return label, "infantry", anti_tank, anti_air


def count_text(counts):
    """{"rifleman": 6, "anti-tank soldier": 2} -> "6 x rifleman, 2 x anti-tank soldier" """
    return ", ".join("%d x %s" % (n, label) for label, n in sorted(counts.items(), key=lambda kv: -kv[1]))


def describe_group(kit, men):
    """Turns the game's raw list into what the commander needs to know.
    A man is [class, launcher, riding]. A vehicle is [class, "V", canMove, canFire, hasAmmo, fuel]
    with an optional seventh field, hasGunner, and eighth, hasDriver.
    (The older two-field form [class, launcher] is still accepted.)"""
    counts, categories = {}, {}
    anti_tank = anti_air = False
    immobile = gun_out = no_gunner = working_vehicles = at_soldiers = gun_vehicles = no_driver = fit_vehicles = 0
    for entry in kit:
        is_vehicle = len(entry) >= 6 and entry[1] == "V"
        if is_vehicle:
            label, category, at, aa = describe(entry[0], is_man=False)
            can_move, can_fire, has_ammo, fuel = bool(entry[2]), bool(entry[3]), bool(entry[4]), float(entry[5])
            faults = []
            if not can_move:
                faults.append("cannot move")
                immobile += 1
            elif fuel < 0.1:
                faults.append("almost out of fuel")
            elif len(entry) >= 8 and not bool(entry[7]):
                faults.append("no driver")
                no_driver += 1
            if not can_fire and len(entry) >= 7 and not bool(entry[6]):
                faults.append("no gunner")          # repair cannot fix this
                no_gunner += 1
            elif not can_fire:
                faults.append("gun out")
                gun_out += 1
            elif not has_ammo:
                faults.append("out of ammo")
            if not can_fire or not has_ammo:
                at = aa = False
            if can_move:
                working_vehicles += 1
            if can_move and can_fire and not (len(entry) >= 8 and not bool(entry[7])) and describe(entry[0], is_man=False)[1] != "static gun":
                fit_vehicles += 1               # it can drive and shoot: a fighting vehicle whatever else the team has lost
            if at and can_move:
                gun_vehicles += 1
            if faults:
                label = "%s (%s)" % (label, ", ".join(faults))
        elif len(entry) >= 3:
            label, category, at, aa = describe(entry[0], entry[1], is_man=True)
            if label == "anti-tank soldier":
                at_soldiers += 1
        else:
            label, category, at, aa = describe(entry[0], entry[1] if len(entry) > 1 else "")
        counts[label] = counts.get(label, 0) + 1
        categories[category] = categories.get(category, 0) + 1
        anti_tank, anti_air = anti_tank or at, anti_air or aa
    if not kit:
        return {"kind": "infantry", "moves": "on foot", "has": "%d men (make-up not reported)" % men,
                "can_fight_armour": False, "can_fight_aircraft": False, "known": False,
                "immobile": 0, "gun_out": 0, "no_gunner": 0, "at_soldiers": 0, "gun_vehicles": 0, "no_driver": 0,
                "fit_vehicles": 0}
    vehicles = {c: n for c, n in categories.items() if c != "infantry"}
    if not vehicles:
        kind, moves = "infantry", "on foot"
    else:
        main = max(vehicles, key=vehicles.get)
        kind = main if "infantry" not in categories else "%s with infantry" % main
        moves = CATEGORIES[main][0] if (working_vehicles or not immobile) else "stuck: every vehicle is disabled"
    return {"kind": kind, "moves": moves, "has": count_text(counts),
            "can_fight_armour": anti_tank, "can_fight_aircraft": anti_air, "known": True,
            "immobile": immobile, "gun_out": gun_out, "no_gunner": no_gunner,
            "at_soldiers": at_soldiers, "gun_vehicles": gun_vehicles, "no_driver": no_driver,
            "fit_vehicles": fit_vehicles}


# ----------------------------------------------------------------------------
# Reading the game's message
# ----------------------------------------------------------------------------
def parse_state(message):
    """["PLAN", side, seconds, points, links, groups, enemy, kills, deaths]
    (kills and deaths are optional, so older mission scripts still work)"""
    if not (isinstance(message, list) and len(message) in (7, 9) and message[0] == "PLAN"):
        raise ValueError("message is not a PLAN with 7 or 9 parts")
    side, seconds, points, links, groups, enemy = message[1:7]
    kills, deaths = (message[7], message[8]) if len(message) == 9 else ([], [])
    state = {"side": str(side), "minute": round(float(seconds) / 60.0, 1),
             "points": [{"name": str(p[0]), "type": str(p[1])} for p in points],
             "links": [], "groups": [], "enemy": [], "kills": [], "deaths": {}}
    names = [p["name"] for p in state["points"]]
    if len(set(names)) != len(names) or not names:
        raise ValueError("point names must exist and be unique")

    def point_name(index):
        index = int(index)
        return names[index] if 0 <= index < len(names) else None

    for a, b in links:
        if point_name(a) and point_name(b):
            state["links"].append([point_name(a), point_name(b)])

    for entry in groups:
        name, men, near, order_point, order_mode = entry[:5]
        mode_name = next((m for m, (number, _) in MODES.items() if number == int(order_mode)), "ATTACK")
        kit = entry[7] if len(entry) > 7 and isinstance(entry[7], list) else []
        group = {
            "name": str(name), "men": int(men), "near": point_name(near),
            "fleeing": bool(entry[5]) if len(entry) > 5 else False,
            "can_walk": bool(entry[6]) if len(entry) > 6 else True,
            "to_go": float(entry[8]) if len(entry) > 8 else -1.0,
            "current_order": ({"point": point_name(order_point), "mode": mode_name}
                              if point_name(order_point) else None),
        }
        group.update(describe_group(kit, group["men"]))
        state["groups"].append(group)
    if not state["groups"]:
        raise ValueError("no groups in the message")

    seen = {}
    for entry in enemy:      # one entry per enemy man or vehicle: [class, nearestPoint, isMan, moving]
        kind = str(entry[0])
        if len(entry) >= 4:
            near, is_man, moving, number = point_name(entry[1]), bool(entry[2]), bool(entry[3]), 1
        else:                # older forms: [class, point] or [class, men, point]
            near, is_man, moving = point_name(entry[-1]), None, True
            number = int(entry[1]) if len(entry) == 3 else 1
        record = seen.setdefault((kind, near), {"count": 0, "moving": False, "is_man": is_man})
        record["count"] += number
        record["moving"] = record["moving"] or moving
    for (kind, near), record in sorted(seen.items(), key=lambda item: -item[1]["count"]):
        label, category, _, _ = describe(kind, is_man=record["is_man"])
        state["enemy"].append({"what": label, "class": category, "count": record["count"], "near": near,
                               "armoured": CATEGORIES[category][1], "raw": kind,
                               "moving": record["moving"]})

    group_names = [g["name"] for g in state["groups"]]
    for kind, near, by in kills:     # [victim class, nearestPoint, index of our group or -1]
        by = int(by)
        state["kills"].append({"what": describe(kind)[0], "near": point_name(near),
                               "by": group_names[by] if 0 <= by < len(group_names) else None})
    for index, killer in deaths:     # [index of our group, class of what killed the man]
        index = int(index)
        if 0 <= index < len(group_names):
            label = "an unseen enemy" if str(killer) in ("unknown", "") else describe(killer)[0]
            per_group = state["deaths"].setdefault(group_names[index], {})
            per_group[label] = per_group.get(label, 0) + 1
    return state


# ----------------------------------------------------------------------------
# Talking to the model
# ----------------------------------------------------------------------------
def ask_model(messages, think):
    body = json.dumps({
        "model": MODEL, "stream": False, "think": think, "messages": messages,
        "options": {"num_ctx": CONTEXT_TOKENS, "temperature": TEMPERATURE,
                    "num_predict": MAX_OUTPUT_TOKENS},
    }).encode("utf-8")
    request = urllib.request.Request(OLLAMA_URL, data=body,
                                     headers={"Content-Type": "application/json"})
    timeout = 170
    if MODEL_DEADLINE_AT is not None:            # a plan for the game: what is left of its time, and no call without any
        timeout = MODEL_DEADLINE_AT - clock()
        if timeout < 1.5:
            raise TimeoutError("the %d seconds allowed for one plan are used up" % MODEL_DEADLINE)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    LAST_MODEL_STATS.clear()
    LAST_MODEL_STATS.update({key: data[key] for key in ("prompt_eval_count", "eval_count", "prompt_eval_duration",
                                                        "eval_duration", "total_duration", "done_reason") if key in data})
    return data.get("message", {}).get("content", ""), data.get("done_reason") == "length"


def extract_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("no JSON object found in the answer")
    return json.loads(text[start:end + 1])


def norm(name):
    if isinstance(name, str):
        return name.strip().upper().replace(" ", "_").replace("-", "_")
    return name


PLAN_SYSTEM = """You are the {side} field commander in an Operation Flashpoint wargame.
You command the groups listed below. You do not control individual soldiers or vehicles.
You win by holding the points of type "town" and destroying enemy groups without losing your own.
You do not know where the enemy started.

THE MAP - named points and what they are:
{points}
Direct routes between points:
{links}

For each of your groups choose a POINT to go to and a MODE:
{modes}

Know your own groups. Each one lists what it is made of, how it moves, and what it can fight:
- "on foot" groups are slow. Do not send them across the map to a fight that will be over
  before they arrive. Tracked, wheeled and air groups get there quickly.
- can_fight_armour false means the group cannot hurt tanks or armoured vehicles at all.
  The game will REJECT an ATTACK order that sends such a group to a point where armour is spotted.
  Use it to DEFEND or AMBUSH somewhere the armour is not, and send a group that can fight armour.
- can_fight_aircraft false means it can do nothing about helicopters or planes.
- A vehicle listed as "cannot move" is stuck where it is. Its crew will sit in it for the rest of
  the game unless you order DISMOUNT, which makes them abandon it and go on foot.
  A vehicle with "gun out" can still drive but cannot fight.

Rules for a good plan:
- You only know what your groups have spotted. An empty enemy list means unseen, not absent.
- Think about where the enemy must travel to reach the towns, and consider waiting for him there.
- To go after a spotted enemy, send a group that can fight it to the point he was spotted near, in ATTACK mode.
- Losses show where the enemy is even when nobody saw him. A group listed under taking_fire is
  being killed where it stands, and "killed_by" says what is doing it. Decide for it: fight there,
  be reinforced there, or move away. Repeating an order that is getting a group killed needs a real reason.
- "enemy_destroyed_so_far" lists what is already dead. It is gone. Never order an attack on
  something from that list, and drop it from your intent.
- "battle_record" shows what each point has cost you. If a point keeps killing your men, stop feeding
  groups into it one at a time: go around it, wait for it, or send a different kind of group.
- A group marked "not moving" is not carrying out its order. It is pinned or busy fighting where it is.
- A group marked fleeing has broken and will ignore orders until it recovers.
- An enemy vehicle noted as "still and harmless" has not moved or hurt anyone for several minutes.
  It is probably disabled or abandoned. Finish it with a group that can fight armour, in ATTACK mode,
  or leave it alone. Do not keep your whole force sitting beside it.
- Your groups win nothing by sitting together on one point while the towns stand empty.
- Do not send every group to the same point. Do not leave every town empty.
- A group that keeps changing direction never arrives. REPEAT a group's current order unless
  WHAT CHANGED gives a real reason to change it. A group still on its way is not a reason.

Work in this order: say what you know and expect, then give one order per group.
Answer with ONE JSON object and nothing else, in exactly this shape and field order:
{{
  "threats": ["short statement of what the enemy is doing or is likely to do"],
  "orders": {{
    "GROUP NAME": {{"point": "POINT NAME", "mode": "MODE", "why": "a few words"}}
  }},
  "intent": "one short sentence on your plan"
}}"""


def build_messages(state, alive, changes, memory):
    points = "\n".join("  %s (%s)" % (p["name"], p["type"]) for p in state["points"])
    links = "\n".join("  %s <-> %s" % (a, b) for a, b in state["links"]) or "  (none given)"
    modes = "\n".join("  %s: %s" % (name, note) for name, (_, note) in MODES.items())
    system = PLAN_SYSTEM.format(side=state["side"], points=points, links=links, modes=modes)

    groups = []
    for group in alive:
        order = memory["standing"].get(group["name"])
        entry = {"name": group["name"], "kind": group["kind"], "moves": group["moves"],
                 "men": group["men"], "has": group["has"],
                 "can_fight_armour": group["can_fight_armour"],
                 "can_fight_aircraft": group["can_fight_aircraft"],
                 "near": group["near"]}
        if order:
            entry["current_order"] = {"point": order["point"], "mode": order["mode"]}
            entry["status"] = "arrived" if group["near"] == order["point"] else "on the way"
        else:
            entry["current_order"] = None
        if group["fleeing"]:
            entry["status"] = "fleeing"
        elif not group["can_walk"]:
            entry["status"] = "leader wounded or vehicle disabled, cannot move"
        elif group["name"] in memory["stuck"]:
            entry["status"] = "not moving for %d minutes (pinned or fighting near %s)" % (
                memory["stuck"][group["name"]], group["near"])
        groups.append(entry)

    situation = {
        "minute": state["minute"],
        "you_started_near": memory["started_near"],
        "your_groups": groups,
        "enemy_spotted_now": [dict({"what": e["what"], "class": e["class"], "count": e["count"],
                                    "near": e["near"]},
                                   **({"note": memory["harmless"][(e["raw"], e["near"])]}
                                      if (e["raw"], e["near"]) in memory["harmless"] else {}))
                              for e in state["enemy"]],
        "taking_fire": memory["under_fire"],
        "enemy_destroyed_so_far": memory["destroyed"],
        "battle_record": memory["record"],
    }
    user = ""
    if memory["intent"]:
        user += "YOUR STANDING PLAN (written before the changes below): " + memory["intent"] + "\n\n"
    user += "WHAT CHANGED:\n" + "\n".join("- " + c for c in changes) + "\n\n"
    user += "CURRENT SITUATION:\n" + json.dumps(situation, indent=1) + "\n\nGive your orders now."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def validate_plan(plan, state, alive):
    problems = []
    orders = plan.get("orders")
    if not isinstance(orders, dict):
        return ['"orders" is missing or is not an object']
    point_names = {norm(p["name"]): p["name"] for p in state["points"]}
    armour_at = {}
    for enemy in state["enemy"]:
        if enemy["armoured"]:
            armour_at.setdefault(enemy["near"], []).append(enemy["what"])
    by_name = {norm(name): value for name, value in orders.items()}
    chosen = []
    for group in alive:
        entry = by_name.get(norm(group["name"]))
        if not isinstance(entry, dict):
            problems.append("no order for group %s" % group["name"])
            continue
        if norm(entry.get("point")) not in point_names:
            problems.append("group %s: %r is not a point. Use one of: %s" % (
                group["name"], entry.get("point"), ", ".join(point_names.values())))
            continue
        if norm(entry.get("mode")) not in MODES:
            problems.append("group %s: %r is not a mode. Use one of: %s" % (
                group["name"], entry.get("mode"), ", ".join(MODES)))
            continue
        point = point_names[norm(entry["point"])]
        chosen.append(point)
        if norm(entry["mode"]) == "ATTACK" and group["known"] and not group["can_fight_armour"] \
                and point in armour_at:
            problems.append("group %s cannot fight armour, and %s is spotted at %s. Do not ATTACK there "
                            "with it. Give it DEFEND or AMBUSH at a point with no armour, or send a "
                            "group that can fight armour." % (
                                group["name"], ", ".join(sorted(set(armour_at[point]))), point))
    if len(alive) >= 3 and len(chosen) == len(alive) and len(set(chosen)) == 1:
        problems.append("every group is ordered to %s, which leaves the rest of the map empty. "
                        "Send at least one group somewhere else." % chosen[0])
    return problems


def plan_orders(state, alive, changes, memory):
    """Returns (plan, problems). Retries when the answer is illegal."""
    messages = build_messages(state, alive, changes, memory)
    think = THINK
    plan, problems = None, ["the model was never asked"]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        answer, capped = ask_model(messages, think)
        try:
            plan = extract_json(answer)
            problems = validate_plan(plan, state, alive)
        except ValueError as error:
            plan, problems = None, ["answer was not valid JSON: %s" % error]
        if not problems:
            return plan, []
        print("   attempt %d rejected: %s" % (attempt, "; ".join(problems)))
        if capped:
            think = LOWER_THINK[think]
        elif attempt < MAX_ATTEMPTS:
            messages = messages + [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": "Your answer was rejected for these reasons:\n- "
                 + "\n- ".join(problems) + "\nSend the corrected JSON only."},
            ]
    return plan, problems


# ----------------------------------------------------------------------------
# Writing the reply the game's script will read
# ----------------------------------------------------------------------------
def clean_text(text, limit=150):
    """Text for a game hint: plain ASCII, no quotes, one line, short."""
    text = str(text).replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "'").replace('"', "'")
    text = " ".join(text.split())
    text = text.encode("ascii", "ignore").decode("ascii")
    return text[:limit]


def game_reply(state, standing, intent, again=()):
    """[1, [[pointIndex, modeNumber, again], ...one per group in the game's order...], "intent"]
    "again" is 1 when the game should issue the order afresh even though it has not changed.
    A group with no order (destroyed) gets [-1,0,0], which the game script skips."""
    point_index = {p["name"]: i for i, p in enumerate(state["points"])}
    pairs = []
    for group in state["groups"]:
        order = standing.get(group["name"])
        if order and group["men"] > 0:
            pairs.append("[%d,%d,%d]" % (point_index[order["point"]], MODES[order["mode"]][0],
                                         1 if group["name"] in again else 0))
        else:
            pairs.append("[-1,0,0]")
    return '[1,[%s],"%s"]' % (",".join(pairs), clean_text(intent))


def game_error(reason):
    return '[0,"%s"]' % clean_text(reason)


# ----------------------------------------------------------------------------
# One commander: remembers the last report so it can work out what changed
# ----------------------------------------------------------------------------
class Commander:
    def __init__(self, side, log_path):
        self.side = side
        self.log_path = log_path
        self.cycle = 0
        self.new_game()

    def new_game(self):
        self.last_minute = -1.0
        self.last_men = {}
        self.last_near = {}
        self.sighting_seen = {}       # (class, point) -> minute last seen
        self.last_fleeing = set()
        self.vehicle_faults = {}      # group -> (vehicles that cannot move, vehicles with gun out)
        self.still_since = {}         # (class, point) -> minute an enemy vehicle was first seen standing still
        self.last_hurt_by = {}        # plain name -> minute it last killed one of ours
        self.harmless = {}            # (class, point) -> note for the commander
        self.destroyed = []           # [{"what", "near", "by", "minute"}] enemy known to be dead
        self.record = {}              # point -> {"lost", "to": {name: n}, "destroyed": {name: n}}
        self.again = set()            # groups whose order should be issued afresh this cycle
        self.kill_points = set()      # points where an enemy died this cycle
        self.progress = {}            # group -> {"point", "best", "since"}
        self.stuck = {}               # group -> minutes without progress
        self.started_near = None
        self.standing = {}            # group -> {"point", "mode", "since"}
        self.standing_intent = ""
        self.last_plan_minute = None
        self.model_calls = 0

    def log(self, record):
        record["side"] = self.side
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def find_changes(self, state, alive):
        """What happened since the last report. No changes means the model is not asked."""
        minute = state["minute"]
        changes, losses, under_fire = [], {}, []
        self.again = set()
        self.kill_points = set()

        for kill in state["kills"]:
            is_man = kill["what"] in INFANTRY_LABELS
            verb = "killed" if is_man else "destroyed"
            if kill["by"]:
                changes.append("%s %s an enemy %s near %s. It is gone." % (kill["by"], verb, kill["what"], kill["near"]))
            else:
                changes.append("An enemy %s near %s is dead. It is gone." % (kill["what"], kill["near"]))
            self.destroyed.append({"what": kill["what"], "near": kill["near"], "by": kill["by"], "minute": minute})
            self.kill_points.add(kill["near"])
            entry = self.record.setdefault(kill["near"], {"lost": 0, "to": {}, "destroyed": {}})
            entry["destroyed"][kill["what"]] = entry["destroyed"].get(kill["what"], 0) + 1
        self.destroyed = [d for d in self.destroyed if minute - d["minute"] <= KILL_MEMORY_MINUTES][-20:]

        for group in state["groups"]:
            before = self.last_men.get(group["name"])
            if before is not None and group["men"] < before:
                lost = before - group["men"]
                losses[group["name"]] = lost
                where = group["near"] or self.last_near.get(group["name"])
                killers = state["deaths"].get(group["name"], {})
                entry = self.record.setdefault(where, {"lost": 0, "to": {}, "destroyed": {}})
                entry["lost"] += lost
                for label, number in killers.items():
                    entry["to"][label] = entry["to"].get(label, 0) + number
                by = (" Killed by: %s." % count_text(killers)) if killers else ""
                if group["men"] > 0:
                    changes.append("%s lost %d men near %s and has %d left.%s The enemy is at or near %s." % (
                        group["name"], lost, where, group["men"], by, where))
                    under_fire.append({"group": group["name"], "near": where, "lost": lost,
                                       "left": group["men"], "killed_by": count_text(killers) or "unknown"})
                else:
                    changes.append("%s was destroyed near %s.%s The enemy is at or near %s." % (
                        group["name"], where, by, where))
            self.last_men[group["name"]] = group["men"]
            if group["near"]:
                self.last_near[group["name"]] = group["near"]

        for enemy in state["enemy"]:
            key = (enemy["raw"], enemy["near"])
            last = self.sighting_seen.get(key)
            if last is None or minute - last > SIGHTING_MEMORY_MINUTES:
                changes.append("NEW SIGHTING: %d x %s near %s" % (enemy["count"], enemy["what"], enemy["near"]))
            self.sighting_seen[key] = minute

        # Our own vehicles: say so when one is newly unable to move or to fire.
        for group in alive:
            before = self.vehicle_faults.get(group["name"], (0, 0))
            if group["immobile"] > before[0]:
                changes.append("%s now has a vehicle that cannot move. Its crew will stay in it unless "
                               "ordered to DISMOUNT. The group has: %s" % (group["name"], group["has"]))
            if group["gun_out"] > before[1]:
                changes.append("%s now has a vehicle whose gun is out. The group has: %s" % (
                    group["name"], group["has"]))
            self.vehicle_faults[group["name"]] = (group["immobile"], group["gun_out"])

        # Enemy vehicles that sit still and hurt nobody are probably disabled.
        for killers in state["deaths"].values():
            for label in killers:
                self.last_hurt_by[label] = minute
        present = set()
        for enemy in state["enemy"]:
            key = (enemy["raw"], enemy["near"])
            if enemy["class"] == "infantry":
                continue
            present.add(key)
            if enemy["moving"]:
                self.still_since.pop(key, None)
                self.harmless.pop(key, None)
                continue
            since = self.still_since.setdefault(key, minute)
            quiet_since = max(since, self.last_hurt_by.get(enemy["what"], -99))
            if minute - quiet_since >= HARMLESS_MINUTES:
                if key not in self.harmless:
                    changes.append("The enemy %s near %s has not moved or hurt anyone for %d minutes. "
                                   "It is probably disabled or abandoned." % (
                                       enemy["what"], enemy["near"], round(minute - quiet_since)))
                self.harmless[key] = "still and harmless for %d minutes: probably disabled" % round(
                    minute - quiet_since)
            else:
                self.harmless.pop(key, None)
        for key in list(self.still_since):
            if key not in present:
                self.still_since.pop(key, None)
                self.harmless.pop(key, None)

        fleeing = {group["name"] for group in alive if group["fleeing"]}
        for name in sorted(fleeing - self.last_fleeing):
            changes.append("%s has broken and is fleeing. It will ignore orders until it recovers." % name)
        for name in sorted(self.last_fleeing - fleeing):
            if any(group["name"] == name for group in alive):
                changes.append("%s has recovered and will follow orders again." % name)
                self.again.add(name)
        self.last_fleeing = fleeing

        # Is each group actually carrying out its order? Watch the distance to its point.
        for group in alive:
            order = self.standing.get(group["name"])
            name = group["name"]
            if not order or group["to_go"] < 0 or group["fleeing"] or group["near"] == order["point"] \
                    or group["to_go"] < 150:
                self.progress.pop(name, None)
                self.stuck.pop(name, None)
                continue
            track = self.progress.get(name)
            if not track or track["point"] != order["point"]:
                self.progress[name] = {"point": order["point"], "best": group["to_go"], "since": minute}
                self.stuck.pop(name, None)
            elif group["to_go"] < track["best"] - 100:
                track["best"], track["since"] = group["to_go"], minute
                self.stuck.pop(name, None)
            elif minute - track["since"] >= STUCK_MINUTES:
                if name not in self.stuck:
                    changes.append("%s has not moved toward %s for %d minutes. It is pinned or fighting near %s."
                                   % (name, order["point"], round(minute - track["since"]), group["near"]))
                    track["nudged"] = minute
                    self.again.add(name)
                elif minute - track.get("nudged", minute) >= STUCK_MINUTES:
                    track["nudged"] = minute
                    self.again.add(name)
                self.stuck[name] = round(minute - track["since"])

        if self.started_near is None and alive:
            places = [group["near"] for group in alive if group["near"]]
            self.started_near = max(set(places), key=places.count) if places else None

        if any(group["name"] not in self.standing for group in alive):
            changes.insert(0, "First report. No orders have been given yet.")
        elif not changes and self.last_plan_minute is not None \
                and minute - self.last_plan_minute >= REVIEW_MINUTES:
            changes.append("Nothing new for %d minutes. Review the plan; keep it if it still makes sense."
                           % REVIEW_MINUTES)
        return changes, losses, under_fire

    def may_change(self, group, state, losses):
        """A group that was given an order recently keeps it unless it is in trouble."""
        order = self.standing.get(group["name"])
        if not order or state["minute"] - order["since"] >= COMMIT_MINUTES:
            return True
        if group["name"] in losses or group["name"] in self.stuck:
            return True
        if order["point"] in self.kill_points:      # what it was sent after may be dead now
            return True
        return any(enemy["near"] in (group["near"], order["point"]) for enemy in state["enemy"])

    def handle(self, state, raw_text):
        self.cycle += 1
        started = time.time()
        minute = state["minute"]
        if minute < self.last_minute:
            print("\n=== %s: the game clock went backwards: new game, memory of the last one cleared ===" % self.side)
            self.new_game()
        self.last_minute = minute

        alive = [group for group in state["groups"] if group["men"] > 0]
        changes, losses, under_fire = self.find_changes(state, alive)

        print("\n%s cycle %d  (game minute %s)" % (self.side, self.cycle, minute))
        for group in state["groups"]:
            order = self.standing.get(group["name"])
            if group["men"] < 1:
                print("   %-9s destroyed" % group["name"])
                continue
            flag = ""
            if group["fleeing"]:
                flag = "  FLEEING"
            elif not group["can_walk"]:
                flag = "  CANNOT MOVE"
            elif group["name"] in self.stuck:
                flag = "  NOT MOVING %d min" % self.stuck[group["name"]]
            print("   %-9s near %-16s order: %-26s%s" % (
                group["name"], group["near"],
                "%s at %s" % (order["mode"], order["point"]) if order else "none", flag))
            print("             %s, %s: %s" % (group["kind"], group["moves"], group["has"]))
        for enemy in state["enemy"]:
            note = self.harmless.get((enemy["raw"], enemy["near"]))
            print("   SPOTTED: %d x %s near %s%s" % (enemy["count"], enemy["what"], enemy["near"],
                                                    ("   [%s]" % note) if note else ""))

        if not alive:
            print("   ALL GROUPS DESTROYED. Nothing left to command.")
            self.log({"cycle": self.cycle, "state": state, "result": "all groups destroyed"})
            return game_error("all groups destroyed")

        if not changes:
            print("   no change: standing orders kept, model not asked%s" % (
                ("   (order re-sent to %s)" % ", ".join(sorted(self.again))) if self.again else ""))
            self.log({"cycle": self.cycle, "state": state, "result": "no change"})
            return game_reply(state, self.standing, self.standing_intent, self.again)

        for change in changes:
            print("   CHANGE: %s" % change)
        memory = {"standing": self.standing, "intent": self.standing_intent, "stuck": self.stuck,
                  "under_fire": under_fire, "started_near": self.started_near,
                  "harmless": self.harmless,
                  "destroyed": [{"what": d["what"], "near": d["near"],
                                 "minutes_ago": round(minute - d["minute"])} for d in self.destroyed],
                  "record": [{"point": point, "your_men_lost_there": entry["lost"],
                              "lost_to": count_text(entry["to"]) or "unknown",
                              "enemy_destroyed_there": count_text(entry["destroyed"]) or "nothing"}
                             for point, entry in self.record.items() if point]}
        try:
            plan, problems = plan_orders(state, alive, changes, memory)
        except (urllib.error.URLError, OSError) as error:
            print("   could not reach the model:", error)
            self.log({"cycle": self.cycle, "state": state, "error": str(error)})
            return game_error("relay could not reach the model")
        self.model_calls += 1
        seconds = round(time.time() - started, 1)

        if problems or not plan:
            print("   NO LEGAL PLAN after %d attempts (%ss). The game keeps its current orders." % (
                MAX_ATTEMPTS, seconds))
            self.log({"cycle": self.cycle, "state": state, "changes": changes, "plan": plan,
                      "problems": problems})
            if self.standing:
                return game_reply(state, self.standing, self.standing_intent, self.again)
            return game_error("model gave no legal plan")

        point_names = {norm(p["name"]): p["name"] for p in state["points"]}
        by_name = {norm(name): value for name, value in plan["orders"].items()}
        for threat in plan.get("threats", []) or []:
            print("   expects: %s" % clean_text(threat, 200))
        for group in alive:
            entry = by_name[norm(group["name"])]
            wanted = {"point": point_names[norm(entry["point"])], "mode": norm(entry["mode"])}
            current = self.standing.get(group["name"])
            why = clean_text(entry.get("why", ""), 80)
            if current and current["point"] == wanted["point"] and current["mode"] == wanted["mode"]:
                print("   KEEP  %-9s %-7s %-16s %s" % (group["name"], wanted["mode"], wanted["point"], why))
            elif not self.may_change(group, state, losses):
                print("   HELD  %-9s stays %s at %s (ordered %.1f min ago; model wanted %s at %s)" % (
                    group["name"], current["mode"], current["point"], minute - current["since"],
                    wanted["mode"], wanted["point"]))
            else:
                wanted["since"] = minute
                self.standing[group["name"]] = wanted
                print("   ORDER %-9s %-7s %-16s %s" % (group["name"], wanted["mode"], wanted["point"], why))
        self.standing_intent = clean_text(plan.get("intent", ""))
        self.last_plan_minute = minute
        print("   intent: %s   (%ss, model call %d)" % (self.standing_intent, seconds, self.model_calls))

        reply = game_reply(state, self.standing, self.standing_intent, self.again)
        for name in sorted(self.again):
            print("   RE-SENT order to %s" % name)
        self.log({"cycle": self.cycle, "state": state, "changes": changes, "losses": losses,
                  "plan": plan, "standing": self.standing, "reply": reply, "seconds": seconds})
        return reply


# ----------------------------------------------------------------------------
# MFCTI, observer mode: read the mission's report and print it. No orders are sent.
# ----------------------------------------------------------------------------
MFCTI_ORDERS = {1: "TAKE TOWNS (assault)", 2: "DEFEND", 3: "BLACK OPS", 4: "MOVE TO WAYPOINT",
                5: "new waypoint order", 6: "DEFEND BASE", 7: "SEARCH AND DESTROY",
                8: "command vehicles", 9: "disembark vehicles", 10: "embark transport",
                11: "disembark transport", 12: "TAKE TOWNS AND BASES", 13: "DEFEND TOWNS AND BASES",
                14: "recycle", 40: "new order", 50: "salvage", 51: "utility", 100: "none"}
MFCTI_ROLES = {0: "INFANTRY", 1: "INFANTRY_AA", 2: "INFANTRY_AT", 3: "INFANTRY_CQB", 4: "BLACK_OPS",
               5: "MECHANIZED", 6: "MECHANIZED_AA", 7: "ARMOUR", 8: "ARMOUR_HEAVY", 9: "AIR"}
MFCTI_BUILDINGS = ["control centre", "barracks", "light factory", "heavy factory", "air factory",
                   "ammo depot", "repair depot", "field hospital"]


TEAM_NAMES = ["Commander", "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]


def engine_note(state):
    """One line about what the game's engine lacks, or None. The mission reports it from layout 13 on."""
    if state.get("has_diag") is False:
        return ("NOTE: no engine diagnostics in the reports. The game was not rebuilt with apply_llm_engine.py, "
                "so a team that stands still cannot be explained in this game.")
    level = state.get("engine_level")
    if level is not None and level < ENGINE_LEVEL:
        return ("NOTE: the game's engine is at level %d of this project's changes and this relay expects %d. Run "
                "apply_llm_engine.py on the engine source and rebuild. Until then a driver left in command of a vehicle "
                "whose commander was killed stays where that commander last sent him." % (level, ENGINE_LEVEL))
    return None


def diag_words(text):
    """'id=3 cmd=MOVE ctx=MISSION' -> {'id': '3', 'cmd': 'MOVE', 'ctx': 'MISSION'}. For the tools and the tests."""
    return dict(word.split("=", 1) for word in str(text).split() if "=" in word)


def engine_diagnosis(team):
    """Report script version 12: the engine's diagnostic texts for a team, for a kick line."""
    diag = team.get("diag")
    if not diag:
        return ""
    parts = []
    if diag.get("vehicle"):
        parts.append("the unit commanding his vehicle [%s]" % diag["vehicle"])
    if diag.get("leader") and diag.get("leader") != diag.get("vehicle"):
        parts.append("the leader himself [%s]" % diag["leader"])
    if diag.get("group"):
        parts.append("subgroups [%s]" % diag["group"])
    return ". Engine: " + "; ".join(parts) if parts else ""


def vehicle_diagnosis(team):
    """Report script version 11: what the game says about the vehicle a leader sits in, for a kick line."""
    if "crew_split" not in team:
        return ""
    words = []
    if team["vehicle_stopped"]:
        words.append("told to stop")
    words.append("engine %s" % ("on" if team["vehicle_engine_on"] else "off"))
    words.append("fuel %d%%" % round(100 * team["vehicle_fuel"]))
    if team["crew_split"]:
        words.append("the crewman who commands it is in a different subgroup from the leader, which %s" % (
            "holds an order" if team["crew_order"] else "holds no order"))
    else:
        words.append("its commander is in the leader's subgroup, which %s" % (
            "holds an order" if team["crew_order"] else "holds no order"))
    if team["crew_follows_m"] > 0:
        words.append("that subgroup follows a man %d m away" % team["crew_follows_m"])
    return "; " + ", ".join(words)


def parse_mfcti(message):
    """Observer report (9 parts):
         ["MFCTI", side, seconds, towns, side info, teams, enemy, kills, deaths]
       Control report (10 parts), which adds a mode number and map positions:
         ["MFCTI", side, seconds, mode, towns, side info, teams, enemy, kills, deaths]"""
    if not (isinstance(message, list) and len(message) in (9, 10, 11, 12, 13, 14, 15) and message[0] == "MFCTI"):
        raise ValueError("message is not an MFCTI report with 9 to 15 parts")
    points = []
    layout = None
    recounts = None
    has_diag = None
    engine_level = None
    if len(message) >= 12:
        layout = int(message[11])
        if layout > REPORT_LAYOUT:
            raise ValueError("the mission sends report layout %d and this relay knows up to %d: use a newer relay.py"
                             % (layout, REPORT_LAYOUT))
        if len(message) >= 14:
            has_diag = message[13] is True
        if len(message) == 15:
            try:
                engine_level = int(message[14])
            except (TypeError, ValueError):
                engine_level = None          # unreadable: the report is good without it
        if len(message) >= 13 and isinstance(message[12], list) and len(message[12]) >= 3:
            try:
                recounts = {"west": int(message[12][0]), "east": int(message[12][1]), "resistance": int(message[12][2])}
            except (TypeError, ValueError):
                recounts = None              # unreadable: the report is good without it
        message = message[:11]
    if len(message) == 11:
        _, side, seconds, mode, towns, info, teams, enemy, kills, deaths, points = message
    elif len(message) == 10:
        _, side, seconds, mode, towns, info, teams, enemy, kills, deaths = message
    else:
        _, side, seconds, towns, info, teams, enemy, kills, deaths = message
        mode = 0
    owners = {0: "nobody", 1: "us", 2: "enemy"}
    state = {"side": str(side), "minute": round(float(seconds) / 60.0, 1), "mode": int(mode), "towns": [],
             "points": [{"name": str(p[0]), "pos": (float(p[1]), float(p[2]))} for p in points],
             "points_sent": len(message) == 11, "layout": layout}
    if recounts is not None:                 # towns the mission's recount (LLM\\TownWatch.sqs) has handed to each side
        state["recounts"] = recounts
    if has_diag is not None:                 # does the game have the diagnostic commands (engine patch apply_llm_engine.py)
        state["has_diag"] = has_diag
    if engine_level is not None:             # which of the project's engine changes the game has (see ENGINE_LEVEL)
        state["engine_level"] = engine_level
    for t in towns:
        town = {"name": str(t[0]), "value": int(t[1]), "owner": owners.get(int(t[2]), "nobody")}
        if len(t) >= 5:
            town["pos"] = (float(t[3]), float(t[4]))
        state["towns"].append(town)
    names = [t["name"] for t in state["towns"]]

    def town(index):
        index = int(index)
        return names[index] if 0 <= index < len(names) else None

    funds, built, mhq_alive, mhq_near, base_seen, base_near = info[:6]
    state["funds"] = int(funds)
    state["buildings"] = [MFCTI_BUILDINGS[i] for i, n in enumerate(built) if int(n) > 0]
    state["mhq"] = {"alive": bool(mhq_alive), "near": town(mhq_near)}
    state["enemy_base"] = town(base_near) if base_seen else None
    state["base_pos"] = (float(info[6]), float(info[7])) if len(info) >= 8 else None
    if len(info) >= 10:                      # layout 14: mortars, and how many of them still have shells
        try:
            state["mortars"], state["mortars_with_shells"] = int(info[8]), int(info[9])
        except (TypeError, ValueError):
            pass
    if len(info) >= 12:                      # Report.sqs 15: mortars switched off by the addon, or a public server
        state["mortars_off"] = info[10] is True or info[11] is True
    if len(info) >= 13:                      # Report.sqs 17: rounds the side's mortars have fired this game
        try:
            state["mortar_shots"] = int(info[12])
        except (TypeError, ValueError):
            pass
    if len(info) >= 16:                      # Report.sqs 18: HE stations, how many manned, the commander's guard
        try:
            state["he_stations"], state["he_manned"], state["guards"] = int(info[13]), int(info[14]), int(info[15])
        except (TypeError, ValueError):
            pass

    state["teams"] = []
    for entry in teams:
        name, human, role, order, independent, team_funds, men, near, dist, fleeing, can_move, kit = entry[:12]
        team = {"name": str(name), "player_led": bool(human),
                "role": MFCTI_ROLES.get(int(role), "-"), "order": MFCTI_ORDERS.get(int(order), "-"),
                "independent": bool(independent), "funds": int(team_funds), "men": int(men),
                "near": town(near), "metres_from_it": round(float(dist)),
                "fleeing": bool(fleeing), "can_move": bool(can_move)}
        if len(entry) >= 15:
            team["pos"] = (float(entry[12]), float(entry[13]))
            team["base_dist"] = round(float(entry[14]))
        if len(entry) >= 19:                 # report script version 9
            seats = {0: "on foot", 1: "driver", 2: "gunner", 3: "commander", 4: "passenger"}
            team["leader_seat"] = seats.get(int(entry[15]), "?")
            team["speed"] = round(float(entry[16]))
            team["leader_ready"] = bool(entry[17])
            team["left_behind"] = int(entry[18])
        if len(entry) >= 21 and team.get("leader_seat") != "on foot":      # report script version 10; a leader on
            team["leader_height"] = round(float(entry[19]), 1)             # foot has no vehicle to describe
            team["leader_vehicle_damage"] = round(float(entry[20]), 2)
        if len(entry) >= 27 and team.get("leader_seat") != "on foot":      # report script version 11
            try:
                team.update({
                    "vehicle_stopped": bool(entry[21]),            # told to stop (the "stop" order)
                    "vehicle_engine_on": bool(entry[22]),
                    "vehicle_fuel": round(float(entry[23]), 2),
                    "crew_split": bool(entry[24]),                 # the man who commands the vehicle is in another subgroup
                    "crew_order": bool(entry[25]),                 # the subgroup he is in holds an order
                    "crew_follows_m": round(float(entry[26]))})    # metres to the man that subgroup follows
            except (TypeError, ValueError):
                pass                                               # one unreadable value: the report is good without these
        if len(entry) >= 30:                 # report script version 12: the engine's own words, while the leader stands still
            diag = {key: clean_text(entry[index], limit) for key, index, limit in (("vehicle", 27, 600), ("leader", 28, 600), ("group", 29, 2000))
                    if isinstance(entry[index], str) and entry[index].strip()}
            if diag:
                team["diag"] = diag
        team.update(describe_group(kit, team["men"]))
        team["vehicles"] = sum(1 for k in kit if len(k) >= 6 and k[1] == "V"
                               and describe(k[0], is_man=False)[1] != "static gun")
        team["guns_manned"] = sum(1 for k in kit if len(k) >= 6 and k[1] == "V"
                                  and describe(k[0], is_man=False)[1] == "static gun")
        state["teams"].append(team)

    seen = {}
    enemy = [e for e in enemy if isinstance(e, list) and len(e) in (5, 7) and isinstance(e[0], str) and e[0]
             and isinstance(e[1], (int, float)) and e[1] >= 0]
    for entry in enemy:
        kind, near, is_man, moving, whose = entry[:5]
        key = (str(kind), town(near), "resistance" if int(whose) == 1 else "enemy")
        record = seen.setdefault(key, {"count": 0, "moving": False, "is_man": bool(is_man), "positions": []})
        record["count"] += 1
        record["moving"] = record["moving"] or bool(moving)
        if len(entry) == 7 and isinstance(entry[5], (int, float)) and isinstance(entry[6], (int, float)):
            record["positions"].append((float(entry[5]), float(entry[6])))     # layout 14
    state["seen"] = []
    for (kind, near, whose), r in sorted(seen.items(), key=lambda kv: (kv[0][2], -kv[1]["count"])):
        label, category, _, _ = describe(kind, is_man=r["is_man"])
        state["seen"].append({"what": label, "class": category, "count": r["count"], "near": near,
                              "whose": whose, "moving": r["moving"], "raw": kind,
                              "armoured": CATEGORIES[category][1], "positions": r["positions"]})

    kills = [k for k in kills if isinstance(k, list) and len(k) == 3 and isinstance(k[0], str) and k[0]
             and isinstance(k[1], (int, float)) and isinstance(k[2], (int, float))]
    state["kills"] = [{"what": describe(kind)[0], "near": town(near),
                       "by": TEAM_NAMES[int(by)] if 0 <= int(by) < len(TEAM_NAMES) else None}
                      for kind, near, by in kills]
    state["deaths"], state["accidents"], state["killers"] = {}, {}, []
    state["resistance_killers"] = []
    for entry in deaths:
        index, killer = int(entry[0]), str(entry[1])
        own = bool(entry[2]) if len(entry) > 2 else False
        team_name = TEAM_NAMES[index] if 0 <= index < len(TEAM_NAMES) else "?"
        if own:
            state["accidents"][team_name] = state["accidents"].get(team_name, 0) + 1
            continue
        enemy_killer = len(entry) < 6 or entry[5] == 0          # Report.sqs 15 sends the side: 0 enemy, 1 resistance
        resistance_killer = len(entry) >= 6 and entry[5] == 1
        if len(entry) >= 5 and (enemy_killer or resistance_killer) and killer not in ("unknown", "") \
                and isinstance(entry[3], (int, float)) and isinstance(entry[4], (int, float)) and entry[3] >= 0 and entry[4] >= 0:
            label, category, _, _ = describe(killer)                     # layout 14: where the killer stood
            state["killers" if enemy_killer else "resistance_killers"].append({
                "team": team_name, "what": label, "class": category,
                "armoured": CATEGORIES[category][1], "pos": (float(entry[3]), float(entry[4]))})
        label = "an unseen enemy" if killer in ("unknown", "") else describe(killer)[0]
        per_team = state["deaths"].setdefault(team_name, {})
        per_team[label] = per_team.get(label, 0) + 1
    return state


def print_mfcti_board(side, title, state, last_owner, standing=None):
    """The board printed for every MFCTI report, observer or commander."""
    ours = [t for t in state["towns"] if t["owner"] == "us"]
    theirs = [t for t in state["towns"] if t["owner"] == "enemy"]
    free = [t for t in state["towns"] if t["owner"] == "nobody"]
    print("\n%s %s  (game minute %s)   funds %d" % (side.upper(), title, state["minute"], state["funds"]))
    print("   base: %s | mobile HQ %s near %s | enemy base: %s" % (
        ", ".join(state["buildings"]) or "nothing built",
        "alive" if state["mhq"]["alive"] else "DESTROYED", state["mhq"]["near"],
        ("found near %s" % state["enemy_base"]) if state["enemy_base"] else "not found"))
    print("   towns: ours %d (value %d) | enemy %d (value %d) | unclaimed %d" % (
        len(ours), sum(t["value"] for t in ours), len(theirs), sum(t["value"] for t in theirs), len(free)))
    if ours:
        print("      ours:  %s" % ", ".join(t["name"] for t in ours))
    if theirs:
        print("      enemy: %s" % ", ".join(t["name"] for t in theirs))
    for t in state["towns"]:
        before = last_owner.get(t["name"])
        if before is not None and before != t["owner"]:
            print("   TOWN CHANGED HANDS: %s, %s -> %s" % (t["name"], before, t["owner"]))
    for team in state["teams"]:
        if team["men"] < 1:
            print("   %-9s wiped out, waiting to respawn" % team["name"])
            continue
        flags = "".join([" PLAYER" if team["player_led"] else "",
                         " FLEEING" if team["fleeing"] else "",
                         " CANNOT MOVE" if not team["can_move"] else ""])
        if standing is not None and team["name"] in standing:
            order = standing[team["name"]]
            doing = "%s%s" % (order["order"], (" " + order["target"]) if order.get("target") else "")
        else:
            doing = team["order"]
        print("   %-9s %-13s %-24s %d m from %s%s" % (
            team["name"], team["role"], doing, team["metres_from_it"], team["near"], flags))
        extra = ""
        if "leader_seat" in team and (team["vehicles"] or team.get("left_behind")):
            extra = "   [leader %s, speed %d%s%s%s]" % (
                team["leader_seat"], team["speed"], "" if team["leader_ready"] else ", on a move order",
                (", %d left behind" % team["left_behind"]) if team.get("left_behind") else "",
                ", his vehicle answers to another subgroup" if team.get("crew_split") else "")
        print("             %s, %s: %s%s" % (team["kind"], team["moves"], team["has"], extra))
    for item in state["seen"]:
        print("   SPOTTED (%s): %d x %s near %s%s" % (
            item["whose"], item["count"], item["what"], item["near"], "" if item["moving"] else ", not moving"))
    for kill in state["kills"]:
        print("   KILL: %s near %s%s" % (kill["what"], kill["near"], (", by %s" % kill["by"]) if kill["by"] else ""))
    for name, killers in state["deaths"].items():
        print("   LOSSES: %s lost %d: %s" % (name, sum(killers.values()), count_text(killers)))
    for name, number in state["accidents"].items():
        print("   LOSSES: %s lost %d to a crash or friendly fire" % (name, number))


class MfctiObserver:
    """Mode 0: print each report. No orders are sent; the stock AI commander stays in command."""

    def __init__(self, side, log_path):
        self.side = side
        self.log_path = log_path
        self.cycle = 0
        self.last_minute = -1.0
        self.last_owner = {}

    def handle(self, state):
        self.cycle += 1
        if state["minute"] < self.last_minute:
            print("\n=== %s: the game clock went backwards: new game ===" % self.side)
            self.last_owner = {}
        self.last_minute = state["minute"]
        with open(self.log_path, "a", encoding="utf-8") as handle:        # the log first: it is the record
            handle.write(json.dumps({"mfcti": True, "relay": VERSION, "cycle": self.cycle, "state": state}) + "\n")
        print_mfcti_board(self.side, "MFCTI report %d" % self.cycle, state, self.last_owner)
        if self.cycle == 1 and engine_note(state):
            print("   " + engine_note(state))
        for t in state["towns"]:
            self.last_owner[t["name"]] = t["owner"]
        return '[1,[],"observing"]'


# ----------------------------------------------------------------------------
# MFCTI, control mode: the model commands the side
# ----------------------------------------------------------------------------
# Key terrain (kt) and landing zones (hlz) placed in the mission, described by the mission maker.
# A point that is in the mission but not in this table is still shown, with no description.
KEY_TERRAIN = {
    "kt1": {"type": "overwatch", "text": "High ground overlooking Petrovice, the central town of the main island"},
    "kt2": {"type": "hill", "text": "Hill overlooking the airfield. Matters if the enemy builds aircraft there"},
    "kt3": {"type": "hill", "text": "Hill 109 near Petrovice. A strong position to hold and defend"},
    "kt4": {"type": "overwatch", "text": "Overwatch position near Skalice and Paseky"},
    "kt5": {"type": "ambush", "text": "Ambush position in the north, covering the northern passage"},
    "kt6": {"type": "overwatch", "text": "Overwatch position near Mala Ves and Davle"},
    "kt7": {"type": "ambush", "infantry_only": True,
            "text": "Castle ruin on a ridge in the east, overlooking the road north. Excellent anti-tank ambush. Infantry on foot only"},
    "kt8": {"type": "hill", "text": "Hill in the north overlooking the route that comes up from the south"},
    "hlz1": {"type": "landing zone", "text": "Landing zone near Petrovice, for troops going to kt1 or kt3"},
    "hlz2": {"type": "landing zone", "text": "Landing zone in the centre of the map"},
    "hlz3": {"type": "landing zone", "text": "Landing zone on the road between Bludov and Mirov, which is a chokepoint"},
    "hlz4": {"type": "landing zone", "text": "Landing zone in the centre of the map"},
    "hlz5": {"type": "landing zone", "text": "Landing zone near Skalice and Neveklov"},
    "hlz6": {"type": "landing zone", "text": "Landing zone near Bitov and Lany"},
    "hlz7": {"type": "landing zone", "text": "Landing zone near Lany and Bor"},
    "hlz8": {"type": "landing zone", "text": "Landing zone near St Sedlo"},
    "hlz9": {"type": "landing zone", "text": "Landing zone near Varta and Blata"},
}

MFCTI_ROLE_NOTES = {
    "INFANTRY": "riflemen on foot; cheap, slow",
    "INFANTRY_AA": "infantry with anti-air missiles. Useless against tanks and infantry. Only once enemy aircraft are seen",
    "INFANTRY_AT": "infantry with anti-tank launchers",
    "INFANTRY_CQB": "infantry for fighting inside towns",
    "BLACK_OPS": "special forces and snipers on foot, for raiding the enemy base",
    "MECHANIZED": "infantry carried in armoured vehicles; needs a vehicle factory",
    "MECHANIZED_AA": "mechanized infantry plus a Shilka anti-air gun; thin armour. Only once enemy aircraft are seen",
    "ARMOUR": "tanks; needs a HEAVY factory. A light factory is not enough",
    "ARMOUR_HEAVY": "the heaviest tanks; needs a heavy factory",
    "AIR": "helicopters; needs an air factory. At most one team",
}
MFCTI_ROLE_NUMBER = {name: number for number, name in MFCTI_ROLES.items()}
MFCTI_ORDER_NOTES = {
    "TAKE_TOWNS": "the normal order. The team captures the nearest town that is not yours, then the next "
                  "nearest, and so on, by itself. It needs no target and no further orders",
    "DEFEND_TOWN": 'guard one of your own towns. Only for a town where the enemy or resistance was seen in the '
                   'last %d minutes. "target" = that town' % DEFEND_MEMORY_MINUTES,
    "DEFEND_BASE": "stay at your base and man its guns. Only as many teams as base_defenders_allowed",
    "RETURN_TO_BASE": "only for a team in the field marked not fit to fight: no working vehicle or half its guns out, "
                      "or, on foot, three men or fewer",
    "ATTACK_BASE": "attack the enemy base. Only allowed once the enemy base has been found",
    "HOLD_POINT": 'go to one key terrain point and hold it. "target" = a name from "key_terrain". At most one team',
}
# What the model may call the normal order. All of these mean TAKE_TOWNS.
ORDER_ALIASES = {"TAKE_TOWN": "TAKE_TOWNS", "AUTO": "TAKE_TOWNS", "TAKE_TOWNS_AND_BASES": "TAKE_TOWNS",
                 "ATTACK_TOWNS": "TAKE_TOWNS", "CAPTURE_TOWNS": "TAKE_TOWNS"}
ATTACK_ORDERS = ("TAKE_TOWNS", "ATTACK_BASE")
NEEDS_VEHICLE_FACTORY = ("MECHANIZED", "MECHANIZED_AA", "ARMOUR", "ARMOUR_HEAVY")
NEEDS_HEAVY_FACTORY = ("ARMOUR", "ARMOUR_HEAVY")      # with only a light factory these buy Shilkas, not tanks
TANK_ROLES = ("ARMOUR", "ARMOUR_HEAVY")
VEHICLE_ROLES = ("MECHANIZED", "MECHANIZED_AA", "ARMOUR", "ARMOUR_HEAVY", "AIR")
AA_ROLES = ("INFANTRY_AA", "MECHANIZED_AA")

MFCTI_SYSTEM = """You are the {side} commander in MFCTI, a capture-the-island wargame in Operation Flashpoint.
There are two ways to win: hold every town on the map, or destroy the enemy's mobile HQ and all four of his
factories (barracks, light, heavy, air). He beats you the same two ways. A side whose mobile HQ is alive
cannot lose by destruction, and a side that loses its mobile HQ can build nothing new. Destroyed factories
can be repaired. Each town you hold pays income according to its value.
You command up to 8 AI teams, never individual soldiers.

You do NOT steer teams from town to town. Each team leader fights his own battle. On the order TAKE_TOWNS a
team captures the nearest town that is not yours, moves straight on to the next, and keeps going without
waiting for you. That is faster than any order you could send it. Your job is the level above that:
  1. the force mix: which ROLE each team has, which decides what it buys;
  2. the few exceptions: a team that must defend, come home, hold ground or attack the enemy base.

How teams work. The game does all of this by itself:
- A team starts as one leader. He buys his own men and vehicles at your base, according to the team's ROLE.
- A team leaves base by itself once it has formed: two vehicles for a tank team, nine men for infantry.
- A team marked "standing still" has stopped answering its orders. The game master is trying to get it
  moving; there is nothing you can order that helps. Do not count on it until the mark is gone.
- A team that is wiped out reappears at your base later, as a single leader, and forms up again.
- A damaged vehicle is repaired within a minute of stopping at your base. A vehicle marked "no gunner"
  cannot be fixed by repair; the team simply has one gun fewer.
- Every unclaimed town is held by resistance: infantry, often with a tank or two. Tank teams take towns.
  Infantry on foot is slow and dies to armour.
- Your whole side may own at most {vehicle_limit} vehicles. A team whose role needs vehicles it cannot buy
  sits at base and does nothing.

For each team choose a ROLE and an ORDER.
ROLES decide what the team buys. A new role does not replace what a team already has, so set roles early
and leave them alone unless something changes.
{roles}
ORDERS:
{orders}

Rules on the force mix. A plan that breaks one is rejected:
- ARMOUR and ARMOUR_HEAVY need a heavy factory. Once you have one, at least {tank_teams} teams must be ARMOUR
  or ARMOUR_HEAVY.
- The opening is the exception. In the first {opening} minutes, before the heavy factory is built, name your
  {tank_teams} tank teams anyway: an ARMOUR team with no heavy factory waits at base and buys nothing, while
  every other role starts buying infantry at once, which leaves it room for fewer tanks later. If there is
  still no heavy factory after {opening} minutes, ARMOUR is refused until there is one.
- No more than {vehicle_teams} teams may have a vehicle role (MECHANIZED, MECHANIZED_AA, ARMOUR, ARMOUR_HEAVY, AIR).
- INFANTRY_AA and MECHANIZED_AA are refused unless "enemy_aircraft_seen_recently" is true. While enemy
  aircraft are active, at least one team must have an anti-air role.
- AIR: at most one team.

Rules on the exceptions. TAKE_TOWNS is the default. An exception with no grounds is not rejected: the game
master simply puts the team back on TAKE_TOWNS, and does the same later when the grounds have gone.
- DEFEND_BASE: only as many ready teams as "base_defenders_allowed", which can be 0. A team with tanks may
  not sit on DEFEND_BASE while nothing threatens the base.
- DEFEND_TOWN: only one of your towns marked "hostile_seen_minutes_ago", one team per town.
- RETURN_TO_BASE: only a team in the field marked "not fit to fight". For a team with vehicles that means no
  vehicle left that can both move and fire, or half its guns out. For a team on foot it means three men or
  fewer. One crewed, working tank is a fit team. A team that has merely taken losses stays out; the mission
  sends it new vehicles and men where it is. A team sent home goes back to TAKE_TOWNS by itself once repaired.
- ATTACK_BASE: only once the enemy base has been found.
- HOLD_POINT: only a point listed in "key_terrain", one team at most, and that team must be near it.
- The team named in "mortar_crew" (when the base is under fire) mans the base mortars; that is done for you.
- When "base_under_fire" is not "no", the teams listed there are counterattacking the attacker and the mortars
  fire on it. That is done for you and your orders do not change it. You may add DEFEND_BASE for another team.
- At least half of your ready teams must be on TAKE_TOWNS or ATTACK_BASE.

Advice:
- When in doubt, TAKE_TOWNS. Every exception takes a team away from taking towns, so each one needs a
  reason you can point to in WHAT CHANGED or in the situation.
- Anti-air does nothing against tanks or infantry.
- Enemy helicopters are a reason to give ONE team an anti-air role, not a reason to bring teams home.
- "key_terrain" is ground the mission maker marked as important, with his note on each. It is listed only
  while the enemy has been seen near it.
- REPEAT each team's current role and order unless WHAT CHANGED gives a real reason to change it.

Answer with ONE JSON object and nothing else, in exactly this shape and field order:
{{
  "situation": "one or two sentences on how the game stands and what the enemy is doing",
  "teams": {{
    "TEAM NAME": {{"role": "ROLE", "order": "ORDER", "target": "TOWN or POINT NAME, or null", "why": "a few words"}}
  }},
  "intent": "one short sentence on your plan"
}}"""


def distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


class MfctiCommander:
    """Mode 1. The model sets each team's role and the exceptions; this class checks and paces it.
    The fighting itself is left to the mission's own team script (the order TAKE_TOWNS)."""

    def __init__(self, side, log_path):
        self.side = side
        self.log_path = log_path
        self.cycle = 0
        self.new_game()

    def new_game(self):
        self.last_minute = -1.0
        self.last_owner = {}
        self.last_men = {}
        self.last_buildings = set()
        self.last_faults = {}
        self.last_fleeing = set()
        self.was_ready = {}
        self.base_was_found = False
        self.sighting_seen = {}
        self.standing = {}            # team -> {"role","order","target","since","role_since"}
        self.standing_intent = ""
        self.last_plan_minute = None
        self.record = {}              # town -> men lost there, to what, and what was destroyed there
        self.progress = {}
        self.stuck = {}
        self.again = set()
        self.model_calls = 0
        self.prev_near = {}           # team -> the town it was near on the previous report
        self.base_since = {}          # team -> minute it came inside the base
        self.air_alert_minute = None  # when enemy aircraft last woke the model
        self.air_seen_minute = None   # when enemy aircraft were last seen at all
        self.factory_minute = None    # when the heavy factory appeared
        self.enemy_near_minute = None # when enemy ground forces were last seen at our base or towns
        self.last_resend = {}         # team -> minute its order was last re-sent
        self.hostile_at = {}          # town -> minute anything hostile was last seen there
        self.freeze = {}              # team -> where and since when it has stood still, and the kicks given
        self.kick = {}                # team -> 2 or 3: the kick to send with this reply
        self.opening_closed = False   # True once the opening has ended without a heavy factory
        self.forming = {}             # team -> since when it has been below dispatch size at base without growing
        self.last_decision = {}       # the prompt and every attempt of the last model call, for the log
        self.layout_warned = False
        self.recounts_seen = None     # the mission's recount totals last printed
        self.diag_noted = False       # the note about missing engine diagnostics has been printed
        self.holds = {}               # team -> the town it holds after taking it: {"town","since","at_flag","fight"}
        self.base_threat = None       # while the base is under fire: {"since","last","said","pos","what","metres","how","armoured"}
        self.counter = {}             # team -> minute it was sent against the attacker
        self.counter_point = None     # where the counterattack goes (place 0 of the reply)
        self.fire_point = None        # where the mortars are told to fire
        self.crew = None              # the team that mans the mortars at base
        self.fire_lifted = False      # the mortars hold fire: one of ours is too close to their target
        self.air_wave_at = None       # game minute of the last anti-air buying wave
        self.air_buy = []             # [[team number, soldiers]] to buy with this reply
        self.air_hunter = None        # the team given the AIR role to hunt enemy aircraft
        self.model_fail_run = 0       # how many plans in a row the model failed to answer in time
        self.model_failed_total = 0
        self.model_rest_until = 0.0   # clock time until which the model is not asked
        self.enemy_at = {}            # town -> minute the enemy side's ground forces were last seen there

    def rules_only(self):
        """True when this side is commanded by the rules alone: --rules for both sides, --rules-side=X for one."""
        return RULES_ONLY or self.side in RULES_SIDES

    def log(self, record):
        record["side"] = self.side
        record["mfcti"] = True
        if self.rules_only():
            record["rules_only"] = True
        record["relay"] = VERSION
        if self.holds:
            record["holding"] = {name: hold["town"] for name, hold in self.holds.items()}
        if self.base_threat:
            record["base_threat"] = dict(self.base_threat)
            record["counter"] = sorted(self.counter)
            record["counter_point"] = self.counter_point
            record["fire"] = self.fire_point
            record["fire_lifted"] = self.fire_lifted
        if self.crew:
            record["crew"] = self.crew
        if self.air_buy:
            record["air_buy"] = [list(x) for x in self.air_buy]
        if self.air_hunter:
            record["air_hunter"] = self.air_hunter
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    # ----- what each team can be told -------------------------------------------------
    def commanded(self, state):
        return [t for t in state["teams"] if t["name"] != "Commander" and not t["player_led"]]

    @staticmethod
    def is_ready(team):
        return team["men"] >= READY_MEN or team["vehicles"] > 0

    @classmethod
    def can_fight(cls, team):
        return team["men"] > 0 and cls.is_ready(team) and not team["fleeing"]

    @staticmethod
    def at_base(team):
        return team["men"] > 0 and team.get("base_dist", 99999) < BASE_RADIUS

    @staticmethod
    def damaged(team):
        """Vehicles the repair depot could fix. A missing gunner is not one of them."""
        return team["immobile"] + team["gun_out"]

    @staticmethod
    def guns_half_out(team):
        return team["vehicles"] > 0 and 2 * team["gun_out"] >= team["vehicles"]

    @staticmethod
    def working_vehicles(team):
        """Vehicles that can both move and fire. Older logs do not carry the count, so it is worked out."""
        if "fit_vehicles" in team:
            return team["fit_vehicles"]
        return max(0, team["vehicles"] - team["immobile"] - team["gun_out"] - team["no_gunner"])

    @classmethod
    def fit(cls, team):
        """Fit to fight, judged by platform. A team with vehicles: at least one that can move and fire, and
        fewer than half its guns out; how many men that takes does not matter. A team on foot: more than
        three men. A team that has only taken losses stays in the field: the mission reinforces it there."""
        if team["vehicles"] > 0:
            return cls.working_vehicles(team) >= 1 and not cls.guns_half_out(team)
        return team["men"] > REFIT_MEN

    @classmethod
    def unfit_reason(cls, team):
        if team["vehicles"] > 0:
            return "half its guns are out" if cls.guns_half_out(team) and cls.working_vehicles(team) else \
                "no vehicle left that can both move and fire"
        return "on foot with three men or fewer"

    def dispatch_men(self, team):
        """The size at which the mission sends this team out by itself."""
        order = self.standing.get(team["name"])
        mounted = team["vehicles"] > 0 or (order and order["role"] in VEHICLE_ROLES)
        return DISPATCH_MEN_VEHICLES if mounted else DISPATCH_MEN_FOOT

    def opening(self, state):
        """The first minutes, before the heavy factory is built: tank teams may be named in advance."""
        return state["minute"] < OPENING_MINUTES and "heavy factory" not in state["buildings"]

    def moving_goal(self, team, order, state):
        """Where the team's order tells it to go, None if the order does not tell it to move.
        "towns" stands for TAKE_TOWNS, where the mission's team script picks the town."""
        if not order or team["men"] < 1 or "pos" not in team:
            return None
        kind = order["order"]
        if kind == "TAKE_TOWNS":
            return "towns" if "barracks" in state["buildings"] else None
        goal = None
        if kind == "DEFEND_TOWN":
            goal = next((t.get("pos") for t in state["towns"] if t["name"] == order.get("target")), None)
        elif kind in ("RETURN_TO_BASE", "DEFEND_BASE"):
            goal = state["base_pos"]
        elif kind == "HOLD_POINT":
            goal = next((p["pos"] for p in state.get("points", []) if p["name"] == order.get("target")), None)
        return goal if goal and distance(team["pos"], goal) >= 200 else None

    def update_holds(self, state, teams):
        """Hold what you take. Ends the holds that are over and starts one for each town that became ours since
        the last report, for the nearest team that is taking towns (not one that is still filling up at base).
        Returns notes for the console and the log. Must run before self.last_owner is brought up to date for this report."""
        minute = state["minute"]
        notes = []
        towns = {t["name"]: t for t in state["towns"]}
        by_name = {t["name"]: t for t in teams}
        for name in list(self.holds):
            hold, team, order = self.holds[name], by_name.get(name), self.standing.get(name)
            town = towns.get(hold["town"])
            reason = None
            if not HOLD_TAKEN_TOWNS:
                reason = "holding is switched off"
            elif not team or team["men"] < 1 or "pos" not in team or not town or not town.get("pos"):
                reason = "the team is gone"
            elif not order or order["order"] != "TAKE_TOWNS":
                reason = "its order is now %s" % (order["order"] if order else "nothing")
            elif name in self.counter:
                reason = "it is counterattacking the enemy at the base"
            elif name == self.crew:
                reason = "it is the mortar crew"
            elif not self.is_ready(team) or team["fleeing"]:
                reason = "the team is no longer fit to hold"
            else:
                if hold["at_flag"] is None and distance(team["pos"], town["pos"]) <= HOLD_AT_FLAG_METRES:
                    hold["at_flag"] = minute
                lost = sum(state["deaths"].get(name, {}).values())
                kills = sum(1 for k in state["kills"] if k.get("near") == hold["town"])
                if lost or kills or town["owner"] != "us":      # a town taken back is a fight too
                    hold["fight"] = minute
                if minute - hold["since"] >= HOLD_MAX_MINUTES:
                    reason = "%d minutes are up%s" % (HOLD_MAX_MINUTES, "" if town["owner"] == "us" else ", and the town is not ours")
                elif (hold["at_flag"] is not None and minute - hold["at_flag"] >= HOLD_MIN_MINUTES and town["owner"] == "us"
                      and minute - hold["fight"] >= HOLD_QUIET_MINUTES):
                    reason = "it has been quiet for %.1f minutes" % (minute - max(hold["fight"], hold["at_flag"]))
            if reason:
                del self.holds[name]
                seen = round(minute - self.hostile_at[hold["town"]], 1) if hold["town"] in self.hostile_at else None
                notes.append("%s stops holding %s after %.1f minutes: %s%s" % (
                    name, hold["town"], minute - hold["since"], reason,
                    "" if seen is None else ". Something hostile was last seen there %.1f minutes ago" % seen))
        if not HOLD_TAKEN_TOWNS or "barracks" not in state["buildings"]:
            return notes
        for town in state["towns"]:
            before = self.last_owner.get(town["name"])
            if town["owner"] != "us" or before in (None, "us") or not town.get("pos"):
                continue
            if any(hold["town"] == town["name"] for hold in self.holds.values()):
                continue
            near = [(distance(team["pos"], town["pos"]), team) for team in teams
                    if "pos" in team and team["name"] not in self.holds and team["name"] not in self.counter
                    and team["name"] != self.crew
                    and not team["fleeing"] and self.is_ready(team)
                    and (self.standing.get(team["name"]) or {}).get("order") == "TAKE_TOWNS"
                    and not (self.at_base(team) and team["men"] < self.dispatch_men(team))]     # still filling up at base
            near = [item for item in near if item[0] <= HOLD_REACH_METRES]
            if not near:
                continue
            metres, team = min(near, key=lambda item: item[0])
            self.holds[team["name"]] = {"town": town["name"], "since": minute, "fight": minute,
                                        "at_flag": minute if metres <= HOLD_AT_FLAG_METRES else None}
            notes.append("%s holds %s, which has just been taken (it is %d m from the flag): at least %d minutes at the flag, "
                         "at most %d in all" % (team["name"], town["name"], round(metres), HOLD_MIN_MINUTES, HOLD_MAX_MINUTES))
        return notes

    def update_crew(self, state, teams):
        """While the side has mortars, one foot team defends the base and so mans them (the stock defend script
        puts a team's men into unmanned guns at its base). Returns notes."""
        notes = []
        mortars = state.get("mortars", 0) if (state.get("layout") or 0) >= 14 else 0
        guard = "guards" in state                # Report.sqs 18: the commander's own men man the guns
        by_name = {t["name"]: t for t in teams}
        if self.crew:
            team = by_name.get(self.crew)
            why = None
            if guard:
                why = "the commander's guard mans the guns"
            elif not BASE_DEFENCE or mortars < 1:
                why = "the side has no mortars"
            elif not team or team["men"] < 1:
                why = "the team is gone"
            elif team["player_led"] or team["fleeing"] or (team["men"] < CREW_KEEP_MEN and not team["vehicles"]):
                why = "the team is no longer fit"
            if why:
                notes.append("%s is no longer the mortar crew: %s" % (self.crew, why))
                self.crew = None
        if self.crew or guard or not BASE_DEFENCE or mortars < 1:
            return notes
        base = state.get("base_pos")
        foot = [t for t in teams if "pos" in t and t["vehicles"] == 0 and t["men"] >= 1 and not t["player_led"]
                and not t["fleeing"] and self.is_ready(t) and t["name"] not in self.counter
                and (self.standing.get(t["name"]) or {}).get("order") != "RETURN_TO_BASE"]
        if not foot or base is None:
            return notes
        small = [t for t in foot if t["men"] <= CREW_PREFER_MEN and distance(t["pos"], base) <= CREW_PREFER_METRES]
        team = min(small or foot, key=lambda t: distance(t["pos"], base))
        self.crew = team["name"]
        self.holds.pop(self.crew, None)
        notes.append("%s mans the %d mortar%s at the base (%d m from it, %d men)" % (
            self.crew, mortars, "" if mortars == 1 else "s", round(distance(team["pos"], base)), team["men"]))
        return notes

    def update_air(self, state, teams):
        """Air response (version 32). Returns notes; those that start with AIR go to the model as changes."""
        notes = []
        self.air_buy = []
        if not AIR_RESPONSE or (state.get("layout") or 0) < 14:
            return notes
        minute = state["minute"]
        aircraft = [(item, pos) for item in state["seen"] if item["whose"] == "enemy" and item["class"] in AIR_THREAT_CLASSES
                    for pos in (item.get("positions") or [])]
        if self.air_hunter:
            team = next((t for t in teams if t["name"] == self.air_hunter), None)
            if not team or team["men"] < 1 or team["player_led"]:
                notes.append("%s is no longer the attack helicopter team: %s" % (self.air_hunter, "gone" if not team or team["men"] < 1 else "player-led"))
                self.air_hunter = None
        if not aircraft:
            return notes
        if self.air_wave_at is not None and minute - self.air_wave_at < AIR_REBUY_MINUTES:
            return notes
        self.air_wave_at = minute
        what, where = aircraft[0][0]["what"], aircraft[0][1]
        fit = [t for t in teams if "pos" in t and t["men"] >= 1 and not t["player_led"] and t["name"] != "Commander"]
        nearest = sorted(fit, key=lambda t: distance(t["pos"], where))[:AIR_TEAMS]
        bought = []
        for team in nearest:
            count = max(0, min(AIR_SOLDIERS_PER_TEAM, 11 - team["men"]))
            if count:
                self.air_buy.append([TEAM_NAMES.index(team["name"]), count])
                bought.append("%s %d m from it" % (team["name"], round(distance(team["pos"], where))))
        if "guards" in state and AIR_BASE_SOLDIERS:
            self.air_buy.append([0, AIR_BASE_SOLDIERS])
            bought.append("%d for the base" % AIR_BASE_SOLDIERS)
        notes.append("AIR THREAT: %s seen at %d, %d. Anti-air soldiers are being bought for %s; this is done for you."
                     % (what, where[0], where[1], ", ".join(bought) or "nobody"))
        if not self.air_hunter and "air factory" in state["buildings"]:
            base = state.get("base_pos")
            candidates = [t for t in fit if t["name"] != self.crew and t["name"] not in self.counter and self.is_ready(t)]
            if candidates and base is not None:
                team = min(candidates, key=lambda t: distance(t["pos"], base))
                self.air_hunter = team["name"]
                notes.append("AIR THREAT: %s becomes the attack helicopter team (role AIR) to hunt enemy aircraft." % team["name"])
        return notes

    def update_counter(self, state, teams):
        """Base defence. Finds out whether the base is under fire, picks the teams that counterattack and the
        point the mortars fire on. Returns notes; those that start with BASE also go to the model as changes.
        Must run after find_changes (it adds to self.again) and before update_holds."""
        minute = state["minute"]
        notes = []
        base = state.get("base_pos")
        active = BASE_DEFENCE and base is not None and (state.get("layout") or 0) >= 14
        by_name = {t["name"]: t for t in teams}
        evidence = []
        if active:
            for item in state["seen"]:
                if item["whose"] != "enemy":
                    continue
                for pos in item.get("positions") or []:
                    metres = distance(pos, base)
                    if metres <= BASE_THREAT_METRES:
                        evidence.append({"pos": pos, "metres": metres, "what": item["what"], "class": item["class"],
                                         "armoured": item["armoured"], "how": "seen"})
            for killer in state.get("killers", []):
                metres = distance(killer["pos"], base)
                if metres <= BASE_THREAT_METRES:
                    evidence.append({"pos": killer["pos"], "metres": metres, "what": killer["what"],
                                     "class": killer["class"], "armoured": killer["armoured"], "how": "killing our men"})
            for killer in state.get("resistance_killers", []):
                metres = distance(killer["pos"], base)
                if metres <= RESISTANCE_BASE_METRES:
                    evidence.append({"pos": killer["pos"], "metres": metres, "what": "resistance " + killer["what"],
                                     "class": killer["class"], "armoured": killer["armoured"],
                                     "how": "resistance killing our men at the base"})
            if TEST_THREAT_MINUTE is not None and TEST_THREAT_MINUTE <= minute < TEST_THREAT_MINUTE + TEST_THREAT_LENGTH:
                evidence.append(self.test_threat(state, base))
        ground = [e for e in evidence if e and e["class"] not in AIR_CLASSES]
        if ground:
            best = min(ground, key=lambda e: (e["how"] == "seen", e["metres"]))    # one that is killing, then the nearest
            if self.base_threat is None:
                self.base_threat = {"since": minute, "said": minute}
                notes.append("BASE UNDER FIRE: %s %d m from your base (%s). The mortars fire on it and the nearest fit "
                             "teams counterattack it; this is done for you." % (best["what"], best["metres"], best["how"]))
            elif minute - self.base_threat["said"] >= BASE_THREAT_REMIND_MINUTES:
                self.base_threat["said"] = minute
                notes.append("BASE STILL UNDER FIRE after %.0f minutes: %s %d m from your base. Counterattacking: %s." % (
                    minute - self.base_threat["since"], best["what"], best["metres"], ", ".join(sorted(self.counter)) or "nobody"))
            self.base_threat.update({"last": minute, "pos": best["pos"], "what": best["what"], "metres": round(best["metres"]),
                                     "how": best["how"], "armoured": best["armoured"]})
        elif self.base_threat is not None and (not active or minute - self.base_threat["last"] >= BASE_THREAT_CLEAR_MINUTES):
            notes.append("BASE no longer under fire: nothing of the enemy seen within %d m of it for %d minutes. "
                         "The counterattack is over; %s back to their own orders." % (
                             BASE_THREAT_METRES, BASE_THREAT_CLEAR_MINUTES, ", ".join(sorted(self.counter)) or "nobody goes"))
            self.base_threat = None
        if self.base_threat is None:
            self.counter, self.counter_point, self.fire_point = {}, None, None
            self.fire_lifted = False
            return notes
        point = self.base_threat["pos"]
        if self.counter_point is None or distance(point, self.counter_point) > COUNTER_RETARGET_METRES:
            if self.counter_point is not None:
                self.again |= set(self.counter)            # same order, new place: send it again
                notes.append("counterattack follows the attacker to %d, %d" % point)
            self.counter_point = point
        if state.get("mortars", 1) > 0:
            if self.fire_point is None or distance(point, self.fire_point) > FIRE_RETARGET_METRES:
                self.fire_point = point
                notes.append("mortars (%s) fire on %d, %d" % (state.get("mortars", "?"), point[0], point[1]))
        else:
            self.fire_point = None
        for name in list(self.counter):
            team = by_name.get(name)
            if not team or team["men"] < 1 or team["fleeing"] or team["player_led"] or not self.is_ready(team) or not self.fit(team):
                del self.counter[name]
                notes.append("%s leaves the counterattack: %s" % (name, "gone" if not team or team["men"] < 1 else "no longer fit"))
        need = COUNTER_TEAMS - len(self.counter)
        if need > 0:
            candidates = []
            for team in teams:
                if team["name"] in self.counter or team["name"] == self.crew or "pos" not in team or team["player_led"] \
                        or team["fleeing"] or team["men"] < 1:
                    continue
                if not self.is_ready(team) or not self.fit(team):
                    continue
                if (self.standing.get(team["name"]) or {}).get("order") == "RETURN_TO_BASE":
                    continue
                if self.base_threat["armoured"] and not team.get("can_fight_armour"):
                    continue
                metres = distance(team["pos"], point)
                if metres <= COUNTER_REACH_METRES:
                    candidates.append((0 if self.working_vehicles(team) else 1, metres, team))
            for _, metres, team in sorted(candidates, key=lambda c: (c[0], c[1]))[:need]:
                self.counter[team["name"]] = minute
                notes.append("%s counterattacks the %s at the base (%d m away, %s)" % (team["name"], self.base_threat["what"],
                                                                                     round(metres), team["has"][:40]))
        if self.fire_point:
            close = sorted(t["name"] for t in state["teams"] if "pos" in t and t["men"] > 0 and t["name"] != "Commander"
                           and distance(t["pos"], self.fire_point) <= DANGER_CLOSE_METRES)
            if base is not None and distance(base, self.fire_point) <= DANGER_CLOSE_METRES:
                close.append("the base")
            if close and not self.fire_lifted:
                notes.append("mortars lift fire: %s within %d m of the target" % (", ".join(close), DANGER_CLOSE_METRES))
            elif not close and self.fire_lifted:
                notes.append("mortars fire again: nothing of ours within %d m of the target" % DANGER_CLOSE_METRES)
            self.fire_lifted = bool(close)
        return notes

    @staticmethod
    def test_threat(state, base):
        """A made-up armoured attacker 800 m from the base, towards the nearest town (--test-threat)."""
        towns = [t for t in state["towns"] if t.get("pos")]
        if not towns:
            return None
        town = min(towns, key=lambda t: distance(t["pos"], base))
        dx, dy = town["pos"][0] - base[0], town["pos"][1] - base[1]
        length = max(1.0, (dx * dx + dy * dy) ** .5)
        step = min(800.0, length)
        pos = (round(base[0] + dx / length * step), round(base[1] + dy / length * step))
        return {"pos": pos, "metres": step, "what": "test target (tank)", "class": "tank", "armoured": True, "how": "test"}

    def watch_frozen(self, state, teams):
        """Finds formed teams that stand still although their order tells them to move, and decides which
        to kick with this reply. Returns notes for the log. In the trial of version 18 such teams had
        nothing wrong with them and ignored every group order, but moved when each member was ordered."""
        minute = state["minute"]
        self.kick = {}
        notes = []
        for team in teams:
            name, order = team["name"], self.standing.get(team["name"])
            goal = self.moving_goal(team, order, state)
            filling = self.at_base(team) and team["men"] < self.dispatch_men(team)
            if name in self.holds or name in self.counter or name == self.crew:   # holding, fighting at base, crewing
                goal = None
            if goal is None or team["men"] < 3 or team["fleeing"] or team["player_led"] or filling:
                self.freeze.pop(name, None)
                continue
            track = self.freeze.get(name)
            moved = distance(team["pos"], track["pos"]) if track else 0
            if not track or (track["kicks"] == 0 and moved > FROZEN_METRES) or moved > UNFROZEN_METRES \
                    or track["order"] != (order["order"], order.get("target")):
                if track and track["kicks"]:
                    notes.append("%s is moving again after %d kick%s (it stood still for %d minutes)" % (
                        name, track["kicks"], "" if track["kicks"] == 1 else "s", round(minute - track["began"])))
                self.freeze[name] = {"pos": team["pos"], "since": minute, "began": minute, "men": team["men"],
                                     "kicks": 0, "order": (order["order"], order.get("target")), "told": False}
                continue
            lost = sum(state["deaths"].get(name, {}).values())
            track["men"] = team["men"]
            # The signature of a leader who cannot hear his team's orders: he sits in a vehicle holding an order
            # of his own (a healthy mounted leader holds none: his team's orders go to its main body), at speed 0,
            # where he was on the last report. In the trial of version 19 this was every base freeze, 7 to 10
            # minutes each, and nothing else for longer than one report.
            still = distance(team["pos"], track.get("last_pos", track["pos"])) < 10
            track["last_pos"] = team["pos"]
            signature = (still and team.get("leader_seat", "on foot") != "on foot" and team.get("leader_ready") is False
                         and team.get("speed") == 0)
            track["signature"] = track.get("signature", 0) + 1 if signature else 0
            if lost:
                track["since"] = minute          # it is fighting
                continue
            at_town = (goal == "towns" and team["metres_from_it"] < 150
                       and any(t["name"] == team["near"] and t["owner"] != "us" for t in state["towns"]))
            limit = FROZEN_AT_TOWN_MINUTES if at_town else FROZEN_MINUTES
            if track["kicks"] >= MAX_KICKS:
                limit = SLOW_KICK_MINUTES
            elif track["signature"] >= SIGNATURE_REPORTS:
                limit = SIGNATURE_KICK_MINUTES
            if minute - track["since"] < limit:
                continue
            track["kicks"] += 1
            track["since"] = minute
            self.kick[name] = 3 if track["kicks"] >= MAX_KICKS and not self.at_base(team) else 2
            if "leader_seat" in team:
                seen = "Leader %s, speed %d, %s, %d left behind, %d without a driver" % (
                    team["leader_seat"], team["speed"],
                    "holds no order of his own" if team["leader_ready"] else "holds an order of his own",
                    team["left_behind"], team["no_driver"])
                if "leader_height" in team:
                    seen += ", his vehicle %.1f m off the ground and %d%% damaged" % (
                        team["leader_height"], round(100 * team["leader_vehicle_damage"]))
                seen += vehicle_diagnosis(team)
                if track.get("signature", 0) >= SIGNATURE_REPORTS:
                    seen += ". Frozen-leader signature"
            else:
                seen = "The mission's report script is older than version 9 and says no more"
            notes.append("%s: kick %d%s. Stood still %d minutes %d m from base (%s) with the order %s. %s%s" % (
                name, track["kicks"], " with the bump" if self.kick[name] == 3 else "",
                round(minute - track["began"]), team.get("base_dist", -1), team["has"], order["order"], seen,
                engine_diagnosis(team)))
        for name in [n for n in self.freeze if n not in {t["name"] for t in teams}]:
            del self.freeze[name]
        return notes

    def frozen_minutes(self, name, minute):
        """Minutes a team has stood still, once it has been kicked at least once. None otherwise."""
        track = self.freeze.get(name)
        return round(minute - track["began"]) if track and track["kicks"] else None

    @classmethod
    def guns_all_out(cls, team, state):
        """In the field with every vehicle unable to fire, and a repair depot to fix them at."""
        return (cls.can_fight(team) and not cls.at_base(team) and team["vehicles"] > 0
                and team["gun_out"] >= team["vehicles"] and "repair depot" in state["buildings"])

    @staticmethod
    def strength(team):
        """How well the team fights armour: strong, weak or none."""
        if team.get("gun_vehicles", 0) >= 1 or team.get("at_soldiers", 0) >= STRONG_AT_SOLDIERS:
            return "strong"
        return "weak" if team["can_fight_armour"] else "none"

    def key_terrain(self, state):
        """Key terrain (not landing zones) the enemy side has been seen near lately, with the mission maker's note."""
        minute = state["minute"]
        town_pos = {t["name"]: t["pos"] for t in state["towns"] if "pos" in t}
        seen_at = [town_pos[name] for name, when in self.enemy_at.items()
                   if name in town_pos and minute - when <= POINT_ENEMY_MINUTES]
        result = []
        for point in state.get("points", []):
            note = KEY_TERRAIN.get(point["name"].lower(), {})
            if note.get("type") == "landing zone" or point["name"].lower().startswith("hlz"):
                continue
            if not any(distance(point["pos"], spot) <= POINT_NEAR_METRES for spot in seen_at):
                continue          # no enemy near it: holding it would achieve nothing
            near = min(((distance(point["pos"], t["pos"]), t) for t in state["towns"] if "pos" in t),
                       key=lambda pair: pair[0], default=None)
            entry = {"name": point["name"], "type": note.get("type", "key terrain"),
                     "note": note.get("text", "no description yet")}
            if near:
                entry["near"] = "%d m from %s (%s)" % (round(near[0], -1), near[1]["name"],
                                                       {"us": "yours", "enemy": "enemy-held"}.get(near[1]["owner"], "unclaimed"))
            if note.get("infantry_only"):
                entry["infantry_only"] = True
            result.append(entry)
        return result

    def air_recent(self, minute, within=AA_MEMORY_MINUTES):
        return self.air_seen_minute is not None and minute - self.air_seen_minute <= within

    def defenders_allowed(self, state):
        """How many ready teams may sit on DEFEND_BASE right now. It follows the threat."""
        minute = state["minute"]
        near = self.enemy_near_minute is not None and minute - self.enemy_near_minute <= 15
        if near or self.air_recent(minute, 15):
            return MAX_BASE_DEFENDERS
        return 0 if minute < QUIET_OPENING_MINUTES else 1

    def threatened(self, town, minute):
        """Minutes since anything hostile was seen at this town, or None if longer ago than counts."""
        when = self.hostile_at.get(town)
        if when is None or minute - when > DEFEND_MEMORY_MINUTES:
            return None
        return round(minute - when)

    # ----- the exceptions to TAKE_TOWNS ---------------------------------------------------
    def refused(self, wanted, state, teams):
        """wanted is {team name: (order, target)}. Returns {team name: reason} for every team whose exception
        to TAKE_TOWNS has no grounds right now. The same test is applied to a new plan from the model and,
        on every report, to the orders already standing, so an exception ends when its grounds do."""
        minute = state["minute"]
        towns = {t["name"]: t for t in state["towns"]}
        offered = {k["name"] for k in self.key_terrain(state)}
        points = {p["name"]: p for p in state.get("points", [])}
        allowed = self.defenders_allowed(state)
        reasons, defenders, guards, holders = {}, [], {}, []
        for team in teams:
            name = team["name"]
            order, target = wanted.get(name, ("TAKE_TOWNS", None))
            ready = self.can_fight(team)
            if order == "DEFEND_TOWN":
                town = towns.get(target)
                if not town or town["owner"] != "us":
                    reasons[name] = "%s is not one of your towns" % (target or "no town named")
                elif self.threatened(target, minute) is None:
                    reasons[name] = "nothing hostile seen at %s in the last %d minutes" % (target, DEFEND_MEMORY_MINUTES)
                elif ready:
                    guards.setdefault(target, []).append(team)
            elif order == "HOLD_POINT":
                point = points.get(target)
                if not point or target not in offered:
                    reasons[name] = "no enemy has been seen near %s lately" % (target or "any key terrain")
                elif "pos" in team and distance(team["pos"], point["pos"]) > POINT_REACH_METRES:
                    reasons[name] = "it is more than %d m from %s" % (POINT_REACH_METRES, target)
                elif KEY_TERRAIN.get(target.lower(), {}).get("infantry_only") and team["vehicles"] > 0:
                    reasons[name] = "%s is for infantry on foot only" % target
                else:
                    holders.append(team)
            elif order == "ATTACK_BASE":
                if not state["enemy_base"]:
                    reasons[name] = "the enemy base has not been found"
            elif order == "RETURN_TO_BASE":
                home = self.base_since.get(name)
                if not ready:
                    reasons[name] = "it is re-forming, which the mission does at base by itself"
                elif self.at_base(team) and home is not None and minute - home >= REFIT_DONE_MINUTES \
                        and (self.damaged(team) == 0 or minute - home >= REFIT_MINUTES):
                    reasons[name] = "it has been at base %d minutes and is repaired" % round(minute - home)
                elif not self.at_base(team) and self.fit(team):
                    reasons[name] = "it is fit to fight"
            elif order == "DEFEND_BASE" and ready:
                if allowed < MAX_BASE_DEFENDERS and team.get("gun_vehicles", 0) > 0:
                    reasons[name] = "it has tanks and nothing threatens the base"
                else:
                    defenders.append(team)
        # Limits on how many. Gun crews keep the base first; the guard nearest a town keeps the town.
        defenders.sort(key=lambda t: (-t["guns_manned"], t.get("gun_vehicles", 0), t["name"]))
        for team in defenders[allowed:]:
            reasons[team["name"]] = "only %d team%s may defend the base right now" % (allowed, "" if allowed == 1 else "s")
        for town, guarding in guards.items():
            guarding.sort(key=lambda t: (distance(t["pos"], towns[town]["pos"]) if "pos" in t and "pos" in towns[town] else 0,
                                         t["name"]))
            for team in guarding[1:]:
                reasons[team["name"]] = "%s already guards %s" % (guarding[0]["name"], town)
        holders.sort(key=lambda t: t["name"])
        for team in holders[MAX_POINT_TEAMS:]:
            reasons[team["name"]] = "%s already holds key terrain" % holders[0]["name"]
        return reasons

    def expire(self, state, teams):
        """Puts a team back on TAKE_TOWNS when the grounds for its exception have gone, and sends a team
        home when every gun it has is out. Neither needs the commander: there is only one right answer."""
        minute = state["minute"]
        wanted = {name: (o["order"], o.get("target")) for name, o in self.standing.items()}
        notes = []
        for name, reason in self.refused(wanted, state, teams).items():
            order = self.standing[name]
            notes.append("%s: %s%s -> TAKE_TOWNS (%s)" % (
                name, order["order"], (" " + order["target"]) if order.get("target") else "", reason))
            self.standing[name] = dict(order, order="TAKE_TOWNS", target=None, since=minute)
        for team in teams:
            order = self.standing.get(team["name"])
            if order and order["order"] in ATTACK_ORDERS and self.guns_all_out(team, state):
                notes.append("%s: %s -> RETURN_TO_BASE (every vehicle it has cannot fire)" % (team["name"], order["order"]))
                self.standing[team["name"]] = dict(order, order="RETURN_TO_BASE", target=None, since=minute)
        return notes

    def enforce(self, plan, state, teams):
        """The same two corrections applied to a plan the model has just given. Returns what was changed."""
        entries = {norm(name): entry for name, entry in plan["teams"].items() if isinstance(entry, dict)}
        town_names = {norm(t["name"]): t["name"] for t in state["towns"]}
        point_names = {norm(p["name"]): p["name"] for p in state.get("points", [])}
        wanted = {}
        for team in teams:
            entry = entries.get(norm(team["name"]))
            if entry and entry.get("order") in MFCTI_ORDER_NOTES:
                key = norm(entry.get("target")) if entry.get("target") else None
                wanted[team["name"]] = (entry["order"], town_names.get(key) or point_names.get(key))
        notes = []
        for name, reason in self.refused(wanted, state, teams).items():
            entry = entries[norm(name)]
            notes.append("%s: %s%s -> TAKE_TOWNS (%s)" % (
                name, entry["order"], (" " + str(entry["target"])) if entry.get("target") else "", reason))
            entry.update(order="TAKE_TOWNS", target=None)
        for team in teams:
            entry = entries.get(norm(team["name"]))
            if entry and entry.get("order") in ATTACK_ORDERS and self.guns_all_out(team, state):
                notes.append("%s: %s -> RETURN_TO_BASE (every vehicle it has cannot fire)" % (team["name"], entry["order"]))
                entry.update(order="RETURN_TO_BASE", target=None)
        return notes

    # ----- what changed ---------------------------------------------------------------
    def find_changes(self, state, teams):
        minute = state["minute"]
        changes, released = [], set()
        self.again = set()
        owner = {t["name"]: t["owner"] for t in state["towns"]}
        for item in state["seen"]:
            if item.get("near"):
                self.hostile_at[item["near"]] = minute

        if not self.standing:
            changes.append("First report. No orders have been given yet.")

        for team in teams:                       # how long each team has been inside the base
            if self.at_base(team):
                self.base_since.setdefault(team["name"], minute)
            else:
                self.base_since.pop(team["name"], None)

        built = set(state["buildings"])
        if self.factory_minute is None and "heavy factory" in built:
            self.factory_minute = minute
            changes.append("Your base now has a HEAVY factory. Set team roles NOW: at least %d teams must be "
                           "ARMOUR or ARMOUR_HEAVY." % MIN_TANK_TEAMS)
        if "light factory" in built and "light factory" not in self.last_buildings:
            changes.append("Your base now has a light factory. It builds light vehicles only. "
                           "ARMOUR still needs a heavy factory, which you %s." % (
                               "also have" if "heavy factory" in built else "do not have yet"))
        for name in ("barracks", "air factory", "repair depot"):
            if name in built and name not in self.last_buildings:
                changes.append("Your base now has a %s." % name)
        self.last_buildings = built
        if not self.opening_closed and minute >= OPENING_MINUTES and "heavy factory" not in built:
            self.opening_closed = True
            if any(o["role"] in NEEDS_HEAVY_FACTORY for o in self.standing.values()):
                changes.append("There is still no heavy factory after %d minutes. The teams waiting as ARMOUR cannot "
                               "form: give them infantry roles now. ARMOUR is refused until a heavy factory is built."
                               % OPENING_MINUTES)

        for town in state["towns"]:
            before = self.last_owner.get(town["name"])
            if before is None or before == town["owner"]:
                continue
            if town["owner"] == "us":
                changes.append("You captured %s (value %d)." % (town["name"], town["value"]))
            elif before == "us":
                changes.append("You LOST %s (value %d). It is now held by %s." % (
                    town["name"], town["value"], "the enemy" if town["owner"] == "enemy" else "nobody"))
            # A town passing between the enemy and nobody is not news; it shows in the town lists.

        if state["enemy_base"] and not self.base_was_found:
            changes.append("The enemy base has been found near %s. ATTACK_BASE is now allowed." % state["enemy_base"])
        self.base_was_found = bool(state["enemy_base"])

        for kill in state["kills"]:
            if not kill["near"]:
                continue
            is_man = kill["what"] in INFANTRY_LABELS
            if not is_man and kill["by"]:        # only what our own teams destroyed is worth a decision
                changes.append("%s destroyed a %s near %s." % (kill["by"], kill["what"], kill["near"]))
            entry = self.record.setdefault(kill["near"], {"lost": 0, "to": {}, "destroyed": {}})
            entry["destroyed"][kill["what"]] = entry["destroyed"].get(kill["what"], 0) + 1

        for team in teams:
            name = team["name"]
            before = self.last_men.get(name)
            killers = state["deaths"].get(name, {})
            lost_to_enemy = sum(killers.values())
            # Where the fight was: where the team stood on the last report. By now a dead leader
            # may already have reappeared at base, and the base is not where he died.
            where = self.prev_near.get(name) or team["near"] or "unknown"
            if lost_to_enemy:
                entry = self.record.setdefault(where, {"lost": 0, "to": {}, "destroyed": {}})
                entry["lost"] += lost_to_enemy
                for label, number in killers.items():
                    entry["to"][label] = entry["to"].get(label, 0) + number
            if before is not None and before > 0 and team["men"] == 0:
                changes.append("%s was wiped out near %s%s. It will reappear at base and form up again." % (
                    name, where, (" by %s" % count_text(killers)) if killers else ""))
                released.add(name)
            elif lost_to_enemy >= 2:
                changes.append("%s lost %d near %s to %s and has %d left." % (
                    name, lost_to_enemy, where, count_text(killers), team["men"]))
                released.add(name)
            self.last_men[name] = team["men"]

            ready = self.is_ready(team)
            if team["men"] > 0 and ready and self.was_ready.get(name) is False:
                changes.append("%s has formed up at base (%s)." % (name, team["has"]))
                released.add(name)
            self.was_ready[name] = ready if team["men"] > 0 else False

            faults = (team["immobile"], team["gun_out"])
            old = self.last_faults.get(name, (0, 0))
            if team["men"] > 0 and not self.at_base(team) and (faults[0] > old[0] or faults[1] > old[1]):
                changes.append("%s has damaged vehicles: %s" % (name, team["has"]))
                released.add(name)
            self.last_faults[name] = faults

            order = self.standing.get(name)
            if order and team["men"] > 0 and order["order"] == "DEFEND_TOWN" and owner.get(order.get("target")) != "us":
                changes.append("%s was defending %s, which is no longer yours." % (name, order["target"]))
                released.add(name)

        fleeing = {t["name"] for t in teams if t["fleeing"] and t["men"] > 0}
        for name in sorted(fleeing - self.last_fleeing):
            if not any(t["name"] == name and self.at_base(t) for t in teams):
                changes.append("%s has broken and is fleeing. It will ignore orders until it recovers." % name)
        for name in sorted(self.last_fleeing - fleeing):
            self.again.add(name)
        self.last_fleeing = fleeing

        # Sightings. Aircraft wake the model at most once per AIR_ALERT_MINUTES.
        # The enemy's ground forces matter at our towns, at our base, and where a team is.
        watched = {t["name"] for t in state["towns"] if t["owner"] == "us"} | {state["mhq"]["near"]}
        watched |= {team["near"] for team in teams}
        aircraft = []
        for item in state["seen"]:
            key = (item["raw"], item["near"], item["whose"])
            last = self.sighting_seen.get(key)
            fresh = last is None or minute - last > SIGHTING_MEMORY_MINUTES
            self.sighting_seen[key] = minute
            in_air = "helicopter" in item["class"] or "plane" in item["class"]
            if item["whose"] != "enemy":
                continue
            if in_air:
                aircraft.append("%d x %s near %s" % (item["count"], item["what"], item["near"]))
                continue
            self.enemy_at[item["near"]] = minute
            if item["near"] in watched:
                self.enemy_near_minute = minute
                if fresh:
                    changes.append("ENEMY SIGHTED: %d x %s near %s." % (item["count"], item["what"], item["near"]))
        if aircraft:
            self.air_seen_minute = minute
            if self.air_alert_minute is None or minute - self.air_alert_minute >= AIR_ALERT_MINUTES:
                self.air_alert_minute = minute
                changes.append("Enemy aircraft are active: %s. Anti-air roles counter this; pulling teams home does not."
                               % "; ".join(aircraft[:3]))

        # A team sent to one place (a town to defend, a point to hold, the base) is given a single move
        # order by the mission. Check that it is getting there, and send the order again if it is not.
        # A team on TAKE_TOWNS has no such place: the mission's own team script keeps it moving.
        town_pos = {t["name"]: t.get("pos") for t in state["towns"]}
        for team in teams:
            name, order = team["name"], self.standing.get(team["name"])
            goal = None
            if order and team["men"] > 0 and "pos" in team and not team["fleeing"]:
                if order["order"] == "DEFEND_TOWN":
                    goal = town_pos.get(order["target"])
                elif order["order"] in ("RETURN_TO_BASE", "DEFEND_BASE"):
                    goal = state["base_pos"]
                elif order["order"] == "HOLD_POINT":
                    goal = next((p["pos"] for p in state.get("points", []) if p["name"] == order.get("target")), None)
            refitting = name in self.base_since and minute - self.base_since[name] < REFIT_MINUTES
            if not goal or not self.is_ready(team) or refitting or distance(team["pos"], goal) < 200:
                self.progress.pop(name, None)
                self.stuck.pop(name, None)
            else:
                to_go = distance(team["pos"], goal)
                track = self.progress.get(name)
                if not track or track["goal"] != goal:
                    self.progress[name] = {"goal": goal, "best": to_go, "since": minute}
                    self.stuck.pop(name, None)
                elif to_go < track["best"] - 100:
                    track["best"], track["since"] = to_go, minute
                    self.stuck.pop(name, None)
                elif minute - track["since"] >= STUCK_MINUTES:
                    if name not in self.stuck:
                        changes.append("%s has not got any closer to its goal for %d minutes. It is stuck or fighting near %s."
                                       % (name, round(minute - track["since"]), team["near"]))
                        released.add(name)
                    if minute - track.get("nudged", -99) >= STUCK_MINUTES:
                        track["nudged"] = minute
                        self.again.add(name)
                    self.stuck[name] = round(minute - track["since"])
            # MFCTI drops a move order given while a team is refilling. Keep re-sending it until the team leaves.
            if (order and order["order"] in ("DEFEND_TOWN", "HOLD_POINT") and self.at_base(team) and self.is_ready(team)
                    and minute - self.last_resend.get(name, -99) >= RESEND_AT_BASE_MINUTES):
                self.last_resend[name] = minute
                self.again.add(name)

        for team in teams:
            if team["men"] > 0 and team["near"]:
                self.prev_near[team["name"]] = team["near"]

        # A team that stays below dispatch size at base without growing. Usually it is waiting its turn at the one
        # heavy factory, which nothing here can speed up, so it is only logged. Near the vehicle limit a tank team
        # cannot form at all, and that the commander must know: an infantry role forms at the barracks.
        self.form_notes = []
        if "barracks" in built and minute >= OPENING_MINUTES:
            side_vehicles = sum(t["vehicles"] for t in teams)
            for team in teams:
                name = team["name"]
                small = 0 < team["men"] < self.dispatch_men(team) and self.at_base(team) and not team["player_led"]
                track = self.forming.get(name)
                if not small:
                    self.forming.pop(name, None)
                    continue
                if not track or team["men"] > track["men"]:
                    self.forming[name] = {"since": minute, "men": team["men"], "logged": False, "told": False}
                    continue
                waited = minute - track["since"]
                order = self.standing.get(name)
                role = order["role"] if order else team["role"]
                near_limit = role in VEHICLE_ROLES and side_vehicles >= VEHICLE_LIMIT - NEAR_VEHICLE_LIMIT
                if waited >= FORMATION_STALL_MINUTES and not track["logged"]:
                    track["logged"] = True
                    self.form_notes.append("%s (%s) has had %d men at base for %d minutes without growing. The teams have %d "
                                           "vehicles of the %d the side may own: %s" % (
                                               name, role, team["men"], round(waited), side_vehicles, VEHICLE_LIMIT,
                                               "near the limit" if near_limit else "probably the factory queue"))
                if waited >= FORMATION_STALL_MINUTES and near_limit and not track["told"]:
                    track["told"] = True
                    changes.append("%s (%s) has waited %d minutes at base with %d men and cannot get vehicles: your teams "
                                   "already have %d and the side may own %d. Give it an infantry role so it forms at the "
                                   "barracks, or leave it waiting for losses to free a place." % (
                                       name, role, round(waited), team["men"], side_vehicles, VEHICLE_LIMIT))
                    released.add(name)
        else:
            self.forming = {}

        # A team that three kicks could not move is news once: the commander must stop counting on it.
        for team in teams:
            track = self.freeze.get(team["name"])
            if track and track["kicks"] >= MAX_KICKS and not track["told"] and minute - track["since"] >= FROZEN_MINUTES:
                track["told"] = True
                changes.append("%s has stood still near %s for %d minutes and %d attempts to get it moving have "
                               "failed. Do not count on it." % (team["name"], team["near"], round(minute - track["began"]), track["kicks"]))

        if not changes and self.last_plan_minute is not None and minute - self.last_plan_minute >= REVIEW_MINUTES:
            changes.append("Nothing new for %d minutes. Review the plan; keep it if it still makes sense." % REVIEW_MINUTES)
        return changes, released

    # ----- asking the model -----------------------------------------------------------
    def build_messages(self, state, teams, changes):
        roles = "\n".join("  %s: %s" % (name, note) for name, note in MFCTI_ROLE_NOTES.items())
        orders = "\n".join("  %s: %s" % (name, note) for name, note in MFCTI_ORDER_NOTES.items())
        system = MFCTI_SYSTEM.format(side=state["side"].upper(), roles=roles, orders=orders,
                                     tank_teams=MIN_TANK_TEAMS, vehicle_teams=MAX_VEHICLE_TEAMS,
                                     vehicle_limit=VEHICLE_LIMIT, opening=OPENING_MINUTES)
        minute = state["minute"]
        team_list = []
        for team in teams:
            order = self.standing.get(team["name"])
            entry = {"name": team["name"], "role": order["role"] if order else team["role"]}
            if team["men"] < 1:
                entry["status"] = "wiped out; it will reappear at base and form up again"
            else:
                entry.update({"men": team["men"], "has": team["has"],
                              "strength_vs_armour": self.strength(team),
                              "can_fight_aircraft": team["can_fight_aircraft"],
                              "near": team["near"], "metres_from_base": team.get("base_dist")})
                if team["fleeing"]:
                    entry["status"] = "fleeing"
                elif not self.is_ready(team):
                    waiting = self.forming.get(team["name"])
                    entry["status"] = "forming at base" if not waiting or minute - waiting["since"] < FORMATION_STALL_MINUTES \
                        else "forming at base, no growth for %d minutes" % round(minute - waiting["since"])
                elif self.frozen_minutes(team["name"], minute) is not None:
                    entry["status"] = "standing still for %d minutes, not answering orders" % self.frozen_minutes(team["name"], minute)
                elif team["name"] in self.stuck:
                    entry["status"] = "stuck for %d minutes" % self.stuck[team["name"]]
                elif team["guns_manned"]:
                    entry["status"] = "ready, manning %d static guns at base" % team["guns_manned"]
                elif self.at_base(team):
                    entry["status"] = "ready, at base" if self.fit(team) else "at base, refitting"
                elif self.fit(team):
                    entry["status"] = "ready, in the field"
                else:
                    entry["status"] = "in the field, not fit to fight (%s)" % self.unfit_reason(team)
            entry["current_order"] = ({"order": order["order"], "target": order.get("target")} if order else None)
            team_list.append(entry)

        def own_town(t):
            line = {"town": t["name"], "value": t["value"]}
            ago = self.threatened(t["name"], minute)
            if ago is not None:
                line["hostile_seen_minutes_ago"] = ago
            return line
        ready = [t for t in teams if self.can_fight(t) and not self.guns_all_out(t, state)]
        not_ours = [t for t in state["towns"] if t["owner"] != "us"]
        situation = {
            "minute": minute,
            "ready_teams": len(ready),
            "teams_that_must_attack": -(-len(ready) // 2) if not_ours else 0,
            "base_defenders_allowed": self.defenders_allowed(state),
            "enemy_aircraft_seen_recently": self.air_recent(minute),
            "heavy_factory": "heavy factory" in state["buildings"],
            "opening_tank_teams_may_be_named": self.opening(state),
            "vehicles_your_teams_have": sum(t["vehicles"] for t in teams),
            "vehicle_limit": VEHICLE_LIMIT,
            "base": {"buildings": state["buildings"], "near_town": state["mhq"]["near"],
                     "mobile_hq": "alive" if state["mhq"]["alive"] else "DESTROYED"},
            "enemy_base": ("found near %s" % state["enemy_base"]) if state["enemy_base"] else "not found yet",
            "your_towns": [own_town(t) for t in state["towns"] if t["owner"] == "us"],
            "enemy_towns": [{"town": t["name"], "value": t["value"]} for t in state["towns"] if t["owner"] == "enemy"],
            "unclaimed_towns": sum(1 for t in state["towns"] if t["owner"] == "nobody"),
            "your_teams": team_list,
            "enemy_ground_seen_now": [{"what": i["what"], "count": i["count"], "near": i["near"]}
                                      for i in state["seen"] if i["whose"] == "enemy"
                                      and "helicopter" not in i["class"] and "plane" not in i["class"]],
            "enemy_aircraft_seen_now": [{"what": i["what"], "count": i["count"], "near": i["near"]}
                                        for i in state["seen"] if i["whose"] == "enemy"
                                        and ("helicopter" in i["class"] or "plane" in i["class"])],
            "key_terrain": self.key_terrain(state),
            "base_under_fire": ({"attacker": self.base_threat["what"], "metres_from_base": self.base_threat["metres"],
                                 "how_we_know": self.base_threat["how"],
                                 "for_minutes": round(minute - self.base_threat["since"], 1),
                                 "counterattacking": sorted(self.counter),
                                 "mortars": state.get("mortars"), "mortars_firing": bool(self.fire_point) and not self.fire_lifted,
                                 "mortar_crew": self.crew,
                                 "he_stations": state.get("he_stations"), "he_stations_manned": state.get("he_manned"),
                                 "commanders_guard": state.get("guards")}
                                if self.base_threat else "no"),
            "battle_record": [{"town": point, "your_men_lost_there": e["lost"],
                               "lost_to": count_text(e["to"]) or "unknown",
                               "destroyed_there": count_text(e["destroyed"]) or "nothing"}
                              for point, e in self.record.items() if point and e["lost"] >= 4],
        }
        user = ""
        if self.standing_intent:
            user += "YOUR STANDING PLAN (written before the changes below): " + self.standing_intent + "\n\n"
        user += "WHAT CHANGED:\n" + "\n".join("- " + c for c in changes) + "\n\n"
        user += "CURRENT SITUATION:\n" + json.dumps(situation, indent=1) + "\n\nGive your orders now."
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]

    @staticmethod
    def tidy(plan):
        """Spell every order the standard way. The model may still call the normal order TAKE_TOWN or AUTO."""
        if not isinstance(plan, dict) or not isinstance(plan.get("teams"), dict):
            return plan
        for entry in plan["teams"].values():
            if isinstance(entry, dict):
                for key in ("role", "order"):
                    entry[key] = norm(entry[key]) if isinstance(entry.get(key), str) else ""
                entry["order"] = ORDER_ALIASES.get(entry["order"], entry["order"])
                if entry["order"] not in ("DEFEND_TOWN", "HOLD_POINT") or not isinstance(entry.get("target"), str):
                    entry["target"] = None
        return plan

    def validate(self, plan, state, teams):
        """What is still wrong with a plan after enforce() has dealt with the exceptions: names that do not
        exist, and the force mix, which is the commander's own decision and is sent back to him."""
        problems = []
        orders = plan.get("teams")
        if not isinstance(orders, dict):
            return ['"teams" is missing or is not an object']
        by_name = {norm(name): value for name, value in orders.items()}
        built = set(state["buildings"])
        minute = state["minute"]
        has_factory = bool({"light factory", "heavy factory"} & built)
        has_heavy = "heavy factory" in built
        opening = self.opening(state)
        chosen, wanted = {}, {}
        town_names = {norm(t["name"]): t["name"] for t in state["towns"]}
        point_names = {norm(p["name"]): p["name"] for p in state.get("points", [])}
        for team in teams:
            name = team["name"]
            entry = by_name.get(norm(name))
            if not isinstance(entry, dict):
                problems.append("no order for team %s" % name)
                continue
            role, order = norm(entry.get("role")), norm(entry.get("order"))
            if role not in MFCTI_ROLE_NOTES:
                problems.append("team %s: %r is not a role. Use one of: %s" % (
                    name, entry.get("role"), ", ".join(MFCTI_ROLE_NOTES)))
                continue
            if order not in MFCTI_ORDER_NOTES:
                problems.append("team %s: %r is not an order. Use one of: %s" % (
                    name, entry.get("order"), ", ".join(MFCTI_ORDER_NOTES)))
                continue
            chosen[name] = (role, order)
            key = norm(entry.get("target")) if entry.get("target") else None
            wanted[name] = (order, town_names.get(key) or point_names.get(key))
            if role == "AIR" and "air factory" not in built:
                problems.append("team %s cannot have role AIR: you have no air factory" % name)
            if role in NEEDS_HEAVY_FACTORY and not has_heavy and not opening:
                problems.append("team %s cannot have role %s: you have no heavy factory after %d minutes, and without "
                                "one that team cannot form. Use INFANTRY_AT or INFANTRY" % (name, role, OPENING_MINUTES))
            elif role in NEEDS_HEAVY_FACTORY:
                pass
            elif role in NEEDS_VEHICLE_FACTORY and not has_factory:
                problems.append("team %s cannot have role %s yet: you have no vehicle factory. "
                                "Use an INFANTRY role for now" % (name, role))
            if role in AA_ROLES and not self.air_recent(minute):
                problems.append("team %s cannot have role %s: no enemy aircraft have been seen, and anti-air does "
                                "nothing against tanks or infantry. Use INFANTRY_AT or INFANTRY" % (name, role))

        for name, reason in self.refused(wanted, state, teams).items():
            problems.append("team %s may not have %s: %s. Give it TAKE_TOWNS" % (name, wanted[name][0], reason))
        for team in teams:
            if team["name"] in chosen and chosen[team["name"]][1] in ATTACK_ORDERS and self.guns_all_out(team, state):
                problems.append("team %s: every vehicle it has is damaged and cannot fire. "
                                "Order RETURN_TO_BASE so the repair depot can fix them" % team["name"])

        # Posture: at least half the ready teams must be out taking towns.
        ready_names = [t["name"] for t in teams if self.can_fight(t) and t["name"] in chosen
                       and not self.guns_all_out(t, state)]
        attackers = [n for n in ready_names if chosen[n][1] in ATTACK_ORDERS]
        need = -(-len(ready_names) // 2)
        if any(t["owner"] != "us" for t in state["towns"]) and len(attackers) < need:
            problems.append("only %d of your %d ready teams are on TAKE_TOWNS or ATTACK_BASE. At least %d must be. "
                            "You cannot win from inside the base" % (len(attackers), len(ready_names), need))

        # Force mix: the heavy factory must be used, the vehicle limit respected, aircraft answered.
        if chosen:
            tank_teams = [n for n, (role, _) in chosen.items() if role in TANK_ROLES]
            vehicle_teams = [n for n, (role, _) in chosen.items() if role in VEHICLE_ROLES]
            need = min(MIN_TANK_TEAMS, max(1, len(chosen) // 2))
            if has_heavy and len(tank_teams) < need:
                problems.append("only %d teams are ARMOUR or ARMOUR_HEAVY. You have a heavy factory, and tank teams "
                                "are what take towns: at least %d teams must be ARMOUR or ARMOUR_HEAVY" % (
                                    len(tank_teams), need))
            elif opening and len(tank_teams) < need:
                problems.append("only %d teams are ARMOUR or ARMOUR_HEAVY. This is the opening: name your %d tank "
                                "teams now, before the heavy factory is built. They wait for it and buy nothing; a team "
                                "with any other role fills up with infantry first and has room for fewer tanks" % (
                                    len(tank_teams), need))
            if len(vehicle_teams) > MAX_VEHICLE_TEAMS:
                problems.append("%d teams have a vehicle role. Your side may own only %d vehicles, so no more than %d "
                                "teams may be MECHANIZED, MECHANIZED_AA, ARMOUR, ARMOUR_HEAVY or AIR; give the "
                                "others INFANTRY_AT or INFANTRY" % (len(vehicle_teams), VEHICLE_LIMIT, MAX_VEHICLE_TEAMS))
            if sum(1 for role, _ in chosen.values() if role == "AIR") > 1:
                problems.append("more than one team has role AIR. At most one")
            if self.air_recent(minute, 20) and not any(role in AA_ROLES for role, _ in chosen.values()):
                problems.append("enemy aircraft are active and no team has an anti-air role. Give at least one team "
                                "INFANTRY_AA%s" % (" or MECHANIZED_AA" if has_factory else ""))
        return problems

    def ask(self, state, teams, changes):
        """One plan from the model. All attempts share one deadline; past it ask_model raises and the caller
        falls back to the rules."""
        global MODEL_DEADLINE_AT
        MODEL_DEADLINE_AT = clock() + MODEL_DEADLINE
        try:
            return self.ask_within_deadline(state, teams, changes)
        finally:
            MODEL_DEADLINE_AT = None

    def ask_within_deadline(self, state, teams, changes):
        if self.rules_only():              # the control run: the same relay, rules and scripts, with no model
            self.last_decision = {"rules_only": True}
            return self.fallback_plan(state, teams), [], []
        messages = self.build_messages(state, teams, changes)
        think = THINK
        plan, problems = None, ["the model was never asked"]
        self.last_decision = {"prompt": messages[1]["content"], "attempts": []}
        if self.model_calls == 0:
            self.last_decision["system_prompt"] = messages[0]["content"]
        for attempt in range(1, MAX_ATTEMPTS + 1):
            LAST_MODEL_STATS.clear()
            asked = time.time()
            answer, capped = ask_model(messages, think)
            self.last_decision["attempts"].append({"think": think, "seconds": round(time.time() - asked, 1),
                                                   "answer": answer, "cut_short": capped, "model": dict(LAST_MODEL_STATS)})
            try:
                plan = self.tidy(extract_json(answer))
                if isinstance(plan.get("teams"), dict):
                    mentioned = {norm(k) for k in plan["teams"]}
                    for team in teams:
                        standing = self.standing.get(team["name"])
                        if norm(team["name"]) not in mentioned and standing:
                            plan["teams"][team["name"]] = {"role": standing["role"], "order": standing["order"],
                                                           "target": standing.get("target"), "why": "(not mentioned: kept)"}
                    corrected = self.enforce(plan, state, teams)
                else:
                    corrected = []
                problems = self.validate(plan, state, teams)
            except ValueError as error:
                plan, problems, corrected = None, ["answer was not valid JSON: %s" % error], []
            self.last_decision["attempts"][-1].update({"problems": list(problems), "corrections": list(corrected)})
            if not problems:
                return plan, [], corrected
            print("   attempt %d rejected: %s" % (attempt, "; ".join(problems)))
            if capped:
                think = LOWER_THINK[think]
            elif attempt < MAX_ATTEMPTS:
                messages = messages + [
                    {"role": "assistant", "content": answer},
                    {"role": "user", "content": "Your answer was rejected for these reasons:\n- "
                     + "\n- ".join(problems) + "\nSend the corrected JSON only."},
                ]
        return plan, problems, []

    def fallback_plan(self, state, teams):
        """A plain plan that obeys every rule, used only when the model fails to give a legal one.
        Roles: keep what stands where it is legal, else a fixed mix. Orders: every team takes towns."""
        built = set(state["buildings"])
        has_heavy = "heavy factory" in built
        has_factory = bool({"light factory", "heavy factory"} & built)
        minute = state["minute"]
        with_heavy = ["ARMOUR", "ARMOUR", "ARMOUR", "ARMOUR", "MECHANIZED", "INFANTRY_AT", "INFANTRY_AT", "INFANTRY"]
        on_foot = ["INFANTRY_AT", "INFANTRY", "INFANTRY_AT", "INFANTRY", "INFANTRY_AT", "INFANTRY", "INFANTRY_AT", "INFANTRY"]
        opening_mix = ["ARMOUR", "ARMOUR", "ARMOUR", "ARMOUR", "INFANTRY_AT", "INFANTRY", "INFANTRY_AT", "INFANTRY"]

        opening = self.opening(state)

        def legal(role):
            if role in NEEDS_HEAVY_FACTORY:
                return has_heavy or opening
            if role in NEEDS_VEHICLE_FACTORY and not has_factory:
                return False
            if role in AA_ROLES and not self.air_recent(minute):
                return False
            return role != "AIR" or "air factory" in built

        def count(roles, kinds):
            return sum(1 for r in roles.values() if r in kinds)

        roles = {}
        for i, team in enumerate(teams):
            standing = self.standing.get(team["name"])
            role = standing["role"] if standing else on_foot[i % 8]
            if role == "AIR" and "AIR" in roles.values():
                role = on_foot[i % 8]
            roles[team["name"]] = role if legal(role) else on_foot[i % 8]
        need = min(MIN_TANK_TEAMS, max(1, len(teams) // 2))
        if ((has_heavy or opening) and count(roles, TANK_ROLES) < need) or count(roles, VEHICLE_ROLES) > MAX_VEHICLE_TEAMS:
            roles = {team["name"]: opening_mix[i % 8] if opening else with_heavy[i % 8] if has_heavy else on_foot[i % 8]
                     for i, team in enumerate(teams)}
        if self.air_recent(minute, 20) and not any(r in AA_ROLES for r in roles.values()):
            spare = [t["name"] for t in teams if roles[t["name"]] not in TANK_ROLES]
            roles[(spare or [teams[-1]["name"]])[-1]] = "INFANTRY_AA"

        plan = {}
        for team in teams:
            order = "RETURN_TO_BASE" if self.guns_all_out(team, state) else "TAKE_TOWNS"
            plan[team["name"]] = {"role": roles[team["name"]], "order": order, "target": None,
                                  "why": "rule-based fallback"}
        return {"situation": "The model gave no legal plan; this is the rule-based fallback.",
                "teams": plan, "intent": "Every team takes the nearest towns."}

    # ----- the reply the game's script reads ---------------------------------------------
    def reply(self, state):
        """[1, [[role, order, town, again] x 9, team number 0 to 8], "intent", places, fire, crew]
        order: 1 go to a town (to base when town is -2, to key terrain point n when town is 100 + n),
               2 attack the enemy base, 3 take towns by itself, 4 defend where it stands.
               -1 means leave the team alone.
        again: 1 send the order again, 2 kick a team that stands still, 3 kick it and bump its vehicles."""
        town_index = {t["name"]: i for i, t in enumerate(state["towns"])}
        town_pos = {t["name"]: t.get("pos") for t in state["towns"]}
        by_name = {t["name"]: t for t in state["teams"]}
        has_barracks = "barracks" in state["buildings"]
        layout14 = (state.get("layout") or 0) >= 14
        parts = []
        for name in TEAM_NAMES:
            team, order = by_name.get(name), self.standing.get(name)
            if not team or not order or team["player_led"] or name == "Commander":
                parts.append("[-1,-1,-1,0]")
                continue
            role = MFCTI_ROLE_NUMBER[order["role"]]
            if name == self.air_hunter:
                role = MFCTI_ROLE_NUMBER["AIR"]           # air response: this team hunts enemy aircraft
            again = self.kick.get(name) or (1 if name in self.again else 0)
            kind, target = order["order"], order.get("target")
            hold = self.holds.get(name)
            if name == self.crew and layout14 and team["men"] >= 1:
                code, town = (4, -1) if self.at_base(team) else (1, -2)     # mortar crew: defend the base, man the guns
            elif name in self.counter and self.counter_point and layout14 and self.is_ready(team):
                code, town = 1, 200                              # counterattack: go to place 0, the attacker
            elif kind == "TAKE_TOWNS" and has_barracks and hold and hold["town"] in town_index:
                code, town = 1, town_index[hold["town"]]        # hold what you took: go to that flag and stay
            elif kind == "TAKE_TOWNS":
                # The mission's own team script forms the team up at base and then keeps it taking towns.
                # Before there is a barracks a lone leader would only walk off and die, so he waits.
                code, town = (3, -1) if has_barracks else (1, -2)
            elif not self.is_ready(team):
                code, town = 1, -2              # any other order: a lone leader stays at base until his team has formed
            elif kind == "DEFEND_TOWN" and target in town_index:
                arrived = "pos" in team and town_pos.get(target) and distance(team["pos"], town_pos[target]) < 200
                code, town = (4, -1) if arrived else (1, town_index[target])
            elif kind == "DEFEND_BASE":
                code, town = (4, -1) if self.at_base(team) else (1, -2)
            elif kind == "RETURN_TO_BASE":
                code, town = 1, -2
            elif kind == "HOLD_POINT":
                index = next((i for i, p in enumerate(state.get("points", [])) if p["name"] == target), None)
                code, town = (1, 100 + index) if index is not None else (1, -2)
            elif kind == "ATTACK_BASE":
                code, town = 2, -1
            else:
                code, town = 3, -1
            parts.append("[%d,%d,%d,%d]" % (role, code, town, again))
        if not layout14:
            return '[1,[%s],"%s"]' % (",".join(parts), clean_text(self.standing_intent))
        places = "[[%d,%d]]" % self.counter_point if (self.counter and self.counter_point) else "[]"
        fire = "[%d,%d]" % self.fire_point if (self.fire_point and not self.fire_lifted) else "[]"
        crew = TEAM_NAMES.index(self.crew) if self.crew in TEAM_NAMES else -1
        air = "[%s]" % ",".join("[%d,%d]" % (t, n) for t, n in self.air_buy)
        return '[1,[%s],"%s",%s,%s,%d,%s]' % (",".join(parts), clean_text(self.standing_intent), places, fire, crew, air)

    # ----- one report -----------------------------------------------------------------------
    def handle(self, state):
        self.cycle += 1
        started = time.time()
        minute = state["minute"]
        if minute < self.last_minute:
            print("\n=== %s: the game clock went backwards: new game, memory of the last one cleared ===" % self.side)
            self.new_game()
        self.last_minute = minute

        teams = self.commanded(state)
        changes, released = self.find_changes(state, teams)
        expired = self.expire(state, teams)
        defence_notes = self.update_crew(state, teams) + self.update_counter(state, teams) + self.update_air(state, teams)
        changes += [note for note in defence_notes if note.startswith("BASE") or note.startswith("AIR")]
        hold_notes = self.update_holds(state, teams)
        kicks = self.watch_frozen(state, teams)
        print_mfcti_board(self.side, "MFCTI commander, cycle %d" % self.cycle, state, self.last_owner, self.standing)
        for note in expired:
            print("   RULE  %s" % note)
        for note in defence_notes:
            print("   BASE  %s" % note)
        for note in hold_notes:
            print("   HOLD  %s" % note)
        for note in kicks:
            print("   KICK  %s" % note)
        for note in self.form_notes:
            print("   FORM  %s" % note)
        if state.get("mortars_off") and not getattr(self, "mortars_noted", False):
            self.mortars_noted = True
            print("   NOTE: mortars are switched off in this game (addon setting MFCTI116NoMortars, or a public server): no fire missions")
        if not self.diag_noted and engine_note(state):
            self.diag_noted = True
            print("   " + engine_note(state))
        if state.get("recounts") is not None and state["recounts"] != self.recounts_seen:
            self.recounts_seen = dict(state["recounts"])
            print("   COUNT the capture-circle recount has so far handed %d towns to East, %d to West, %d to the resistance"
                  % (state["recounts"]["east"], state["recounts"]["west"], state["recounts"]["resistance"]))
        if not self.layout_warned and state.get("layout") != REPORT_LAYOUT:
            self.layout_warned = True
            print("   NOTE: the mission sends report layout %s and this relay expects %d. It is read as far as it goes, but "
                  "install the mission scripts that came with this relay." % (state.get("layout") or "older than 10", REPORT_LAYOUT))
        if self.rules_only() and self.cycle == 1:
            print("   RULES ONLY: the model is not asked in this game. Every plan is the rule-based fallback.")
        if self.cycle == 1 or minute < 1.5:
            names = [p["name"] for p in state.get("points", [])]
            terrain = [n for n in names if not n.lower().startswith("hlz")]
            if not state.get("points_sent"):
                print("   key terrain: the mission sent no list. It is running a report script older than version 5.")
            elif not names:
                print("   key terrain: report script version 5 is running but found no kt or hlz objects in the mission.")
            else:
                print("   key terrain in this mission: %s | landing zones: %d" % (", ".join(terrain), len(names) - len(terrain)))
        for t in state["towns"]:
            self.last_owner[t["name"]] = t["owner"]

        if not teams:
            print("   no AI teams to command on this side")
            return '[1,[%s],""]' % ",".join(["[-1,-1,-1,0]"] * len(TEAM_NAMES))
        if not changes:
            note = ("   (order re-sent to %s)" % ", ".join(sorted(self.again))) if self.again else ""
            print("   no change: standing orders kept, model not asked%s" % note)
            reply = self.reply(state)
            self.log({"cycle": self.cycle, "state": state, "result": "no change", "reply": reply,
                      "standing": self.standing, "rule_changes": expired, "kicks": kicks, "forming": self.form_notes,
                      "holds": hold_notes, "defence": defence_notes})
            return reply

        for change in changes:
            print("   CHANGE: %s" % change)
        # The model may not cost the commander his tempo. If it does not answer in time, or is resting after
        # failing, there is no plan from it and the rule-based plan below is used, as in a --rules game.
        model_failed = None
        if not self.rules_only() and clock() < self.model_rest_until:
            model_failed = "resting after %d failures in a row" % self.model_fail_run
            self.last_decision = {"model_resting": True}
            plan, problems, corrected = None, ["the model is " + model_failed], []
            print("   MODEL  resting for another %d seconds. The rules decide." % max(1, round(self.model_rest_until - clock())))
        else:
            try:
                plan, problems, corrected = self.ask(state, teams, changes)
            except (urllib.error.URLError, OSError) as error:
                model_failed = clean_text(error, 120) or "no answer"
                self.model_fail_run += 1
                self.model_failed_total += 1
                plan, problems, corrected = None, ["the model did not answer: " + model_failed], []
                print("   MODEL  no answer within %d seconds (%s). The rules decide this time." % (MODEL_DEADLINE, model_failed))
                if self.model_fail_run >= MODEL_FAILS_TO_REST:
                    self.model_rest_until = clock() + MODEL_REST_SECONDS
                    print("   MODEL  DOWN: %d failures in a row. It is not asked again for %d seconds; the rules command until then."
                          % (self.model_fail_run, MODEL_REST_SECONDS))
            else:
                if self.model_fail_run:
                    print("   MODEL  answering again after %d failures in a row." % self.model_fail_run)
                self.model_fail_run = 0
                self.model_calls += 1
        seconds = round(time.time() - started, 1)
        used_fallback = False
        if self.rules_only():
            released = {t["name"] for t in teams}          # the rule-based plan is not held back by the commit rule
        if problems or not plan:
            fallback = self.fallback_plan(state, teams)
            still_wrong = self.validate(fallback, state, teams)
            if still_wrong:
                print("   NO LEGAL PLAN after %d attempts (%ss), and the fallback failed too: %s. Standing orders are kept."
                      % (MAX_ATTEMPTS, seconds, "; ".join(still_wrong)[:200]))
                record = {"cycle": self.cycle, "state": state, "changes": changes, "plan": plan, "problems": problems,
                          "fallback_problems": still_wrong}
                if model_failed:
                    record["model_failed"] = model_failed
                self.log(record)
                return self.reply(state) if self.standing else game_error("no legal plan")
            if model_failed:
                print("   FALLBACK: no plan from the model (%ss). Using the rule-based plan." % seconds)
            else:
                print("   FALLBACK: the model gave no legal plan in %d attempts (%ss). Using the rule-based plan." % (MAX_ATTEMPTS, seconds))
            rejected, plan, used_fallback = plan, fallback, True
            released = {t["name"] for t in teams}          # the fallback is not held back by the commit rule

        for note in corrected:
            print("   RULE  %s   (the plan asked otherwise)" % note)
        towns = {norm(t["name"]): t["name"] for t in state["towns"]}
        by_name = {norm(name): value for name, value in plan["teams"].items()}
        print("   sees: %s" % clean_text(plan.get("situation", ""), 220))
        for team in teams:
            name = team["name"]
            entry = by_name[norm(name)]
            wanted = {"role": norm(entry["role"]), "order": norm(entry["order"]), "target": None}
            if wanted["order"] == "DEFEND_TOWN":
                wanted["target"] = towns.get(norm(entry.get("target")))
            elif wanted["order"] == "HOLD_POINT":
                wanted["target"] = next((p["name"] for p in state.get("points", [])
                                         if norm(p["name"]) == norm(entry.get("target"))), None)
            why = clean_text(entry.get("why", ""), 70)
            current = self.standing.get(name)
            label = "%s%s" % (wanted["order"], (" " + wanted["target"]) if wanted["target"] else "")
            if current is None:
                self.standing[name] = dict(wanted, since=minute, role_since=minute)
                print("   ORDER %-8s %-13s %-26s %s" % (name, wanted["role"], label, why))
                continue
            free = name in released or team["men"] < 1
            same_order = current["order"] == wanted["order"] and current.get("target") == wanted["target"]
            if not same_order and not free and minute - current["since"] < COMMIT_MINUTES:
                print("   HELD  %-8s keeps %s%s (ordered %.1f min ago; model wanted %s)" % (
                    name, current["order"], (" " + current["target"]) if current.get("target") else "",
                    minute - current["since"], label))
                wanted["order"], wanted["target"] = current["order"], current.get("target")
                label = "%s%s" % (wanted["order"], (" " + wanted["target"]) if wanted["target"] else "")
                why = "(held)"
                same_order = True
            pre_factory = self.factory_minute is not None and current["role_since"] <= self.factory_minute
            impossible = (current["role"] in NEEDS_HEAVY_FACTORY and "heavy factory" not in state["buildings"]
                          and not self.opening(state)) or self.forming.get(name, {}).get("told", False)
            if wanted["role"] != current["role"] and not free and not pre_factory and not impossible \
                    and minute - current["role_since"] < ROLE_COMMIT_MINUTES:
                wanted["role"] = current["role"]
            if same_order and wanted["role"] == current["role"]:
                print("   KEEP  %-8s %-13s %-26s %s" % (name, current["role"], label, why))
                continue
            self.standing[name] = {"role": wanted["role"], "order": wanted["order"], "target": wanted["target"],
                                   "since": current["since"] if same_order else minute,
                                   "role_since": current["role_since"] if wanted["role"] == current["role"] else minute}
            print("   ORDER %-8s %-13s %-26s %s" % (name, wanted["role"], label, why))
        self.standing_intent = clean_text(plan.get("intent", ""))
        self.last_plan_minute = minute
        print("   intent: %s   (%ss, model call %d)" % (self.standing_intent, seconds, self.model_calls))
        # A team whose order has just changed is not kicked on the old one.
        for name in list(self.kick):
            track, order = self.freeze.get(name), self.standing.get(name)
            if not track or not order or track["order"] != (order["order"], order.get("target")):
                self.kick.pop(name)
                self.freeze.pop(name, None)
        reply = self.reply(state)
        record = {"cycle": self.cycle, "state": state, "changes": changes, "plan": plan,
                  "standing": self.standing, "reply": reply, "seconds": seconds,
                  "rule_changes": expired, "plan_corrections": corrected, "kicks": kicks, "forming": self.form_notes,
                  "holds": hold_notes, "defence": defence_notes, "decision": self.last_decision}
        if used_fallback:
            record.update({"fallback": True, "rejected_plan": rejected, "problems": problems})
        if model_failed:
            record["model_failed"] = model_failed
        self.log(record)
        return reply


# ----------------------------------------------------------------------------
# The relay: one Commander per side
# ----------------------------------------------------------------------------
class Relay:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.log_path = os.path.join(LOG_DIR, time.strftime("session_%Y%m%d_%H%M%S.jsonl"))
        self.commanders = {}
        self.observers = {}
        self.mfcti = {}

    def handle(self, text):
        if not text.startswith("["):
            print("game said:", text)
            return "relay got: " + text
        try:
            try:
                message = json.loads(text)
            except ValueError:
                # An object that vanished mid-report prints as bare words. Blank them and read the rest.
                repaired = re.sub(r"scalar bool array string 0x[0-9a-fA-F]+", "null", text)
                repaired = re.sub(r"(?<=[\[,])(string|scalar|bool|array|object)(?=[,\]])", "null", repaired)
                message = json.loads(repaired)
                print("   (one unreadable entry in the report was dropped)")
            if isinstance(message, list) and message and message[0] == "MFCTI":
                state = parse_mfcti(message)
                if state["mode"] >= 1:
                    commander = self.mfcti.get(state["side"])
                    if commander is None:
                        commander = self.mfcti[state["side"]] = MfctiCommander(state["side"], self.log_path)
                    return commander.handle(state)
                observer = self.observers.get(state["side"])
                if observer is None:
                    observer = self.observers[state["side"]] = MfctiObserver(state["side"], self.log_path)
                return observer.handle(state)
            state = parse_state(message)
        except (ValueError, TypeError, IndexError, KeyError) as error:
            print("could not read the game's message: %s" % error)
            position = getattr(error, "pos", None)
            if position is not None:        # show the part of the message that would not parse
                print("   the message around that point:  ...%s  >>>HERE>>>  %s..." % (
                    text[max(0, position - 60):position], text[position:position + 80]))
                if "scalar bool array string" in text:
                    print("   (that odd text is how the game prints a variable that was never set)")
            self.note_failure(text, error)
            return game_error("relay could not read the message: %s" % error)
        commander = self.commanders.get(state["side"])
        if commander is None:
            commander = self.commanders[state["side"]] = Commander(state["side"], self.log_path)
        return commander.handle(state, text)

    def note_failure(self, text, error):
        """Every failure goes into the session log with its cause, so a silent stop can be explained afterwards."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"relay": VERSION, "raw": text, "error": "%s: %s" % (type(error).__name__, error),
                                         "trace": traceback.format_exc()}) + "\n")
        except OSError:
            pass


RELAY = Relay()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        text = self.rfile.read(length).decode("utf-8", "replace")
        try:
            reply = RELAY.handle(text)
        except Exception as error:      # never let one bad cycle stop the relay
            print("   relay error:", repr(error))
            RELAY.note_failure(text, error)
            reply = game_error("relay error: %s" % error)
        data = reply.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def deadline_option(arguments, default):
    """--deadline=N: the real seconds the model has for one plan. Anything unreadable or below 5 leaves the default."""
    for argument in arguments:
        if argument.startswith("--deadline="):
            try:
                value = int(argument.split("=", 1)[1])
            except ValueError:
                continue
            if value >= 5:
                return value
    return default


if __name__ == "__main__":
    arguments = [a for a in sys.argv[1:] if not a.startswith("--")]
    RULES_ONLY = "--rules" in sys.argv[1:]
    for option in sys.argv[1:]:
        if option.startswith("--rules-side="):
            RULES_SIDES |= {s.strip().capitalize() for s in option.split("=", 1)[1].split(",") if s.strip()}
    MODEL_DEADLINE = deadline_option(sys.argv[1:], MODEL_DEADLINE)
    if "--no-hold" in sys.argv[1:]:
        HOLD_TAKEN_TOWNS = False
    if "--no-defence" in sys.argv[1:]:
        BASE_DEFENCE = False
    for option in sys.argv[1:]:
        if option.startswith("--test-threat="):
            try:
                TEST_THREAT_MINUTE = float(option.split("=", 1)[1])
            except ValueError:
                pass
    if arguments:                                     # unattended: write to a file, not to a window
        sys.stdout = sys.stderr = open(arguments[0], "a", encoding="utf-8", errors="replace", buffering=1)
    for stream in (sys.stdout, sys.stderr):           # whatever the model writes must not stop the relay
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    print("relay version %d   model %s   think=%s   review every %d min, commit %d min%s" % (
        VERSION, MODEL, THINK, REVIEW_MINUTES, COMMIT_MINUTES,
        "   RULES ONLY: the model is not asked" if RULES_ONLY else "   the model has %d seconds for a plan" % MODEL_DEADLINE))
    if RULES_SIDES and not RULES_ONLY:
        print("rules only for: %s (the model commands any other side)" % ", ".join(sorted(RULES_SIDES)))
    print("teams hold a town they have just taken: %s" % (
        "at least %d minutes at the flag, at most %d" % (HOLD_MIN_MINUTES, HOLD_MAX_MINUTES) if HOLD_TAKEN_TOWNS else "NO (--no-hold)"))
    print("base defence (counterattack and mortar fire when the base is under fire): %s%s" % (
        "on" if BASE_DEFENCE else "OFF (--no-defence)",
        ("   TEST: a made-up attacker at game minute %g" % TEST_THREAT_MINUTE) if TEST_THREAT_MINUTE is not None else ""))
    print("listening on http://%s:%d/   log: %s" % (HOST, PORT, RELAY.log_path))
    print("Ctrl+C to stop")
    try:
        HTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nrelay stopped")
