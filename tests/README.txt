OFP LLM Commander: tests and analysis tools
============================================

Unzip into C:\ofp-llm so that you have C:\ofp-llm\tests and C:\ofp-llm\tools next to relay.py.

Run every check (about half a minute, no game and no model needed):

    cd C:\ofp-llm
    python tests\run_tests.py

What it runs
  test_rules_v18.py     45 checks: force mix, exceptions and their grounds, repair, replies, fallback
  test_rules_v19.py     38 checks: the kick for teams that stand still, the opening, the report
                        fields added in report script 9
  test_rules_v20.py     29 checks: fit to fight by platform, the frozen-leader signature, teams
                        that do not form, rules-only mode, the report layout number, the
                        decision log
  test_rules_v21.py     29 checks: report layout 11 (what the game says about the vehicle a leader
                        sits in), the capture-circle recount totals, older and newer layouts
  test_rules_v22.py     30 checks: report layout 12 (the texts from the engine's diagnostic
                        commands), the kick line, the note when the game was not rebuilt
  test_rules_v23.py     32 checks: report layout 13 (which of the project's engine changes the
                        game has), the note when it is below level 2, and that the same game
                        reported in layout 12 and in layout 13 gets the same orders
  test_rules_v24.py     27 checks: a model that is slow or down. One deadline for a plan, the
                        rule-based plan when it is missed, the rest after two failures in a
                        row, the mark in the log, and the real call against a stand-in server
  test_rules_v25.py     57 checks: hold what you take. Who is sent back to the flag of a town just
                        taken, the order it gets, two minutes at the flag, longer while it
                        fights or the town is taken back, five at most, no kick while it
                        holds, what ends a hold, --no-hold, and the same on top of a model's plan
  test_rules_v26.py     48 checks: base defence. Report layout 14 (positions of what is seen, where a
                        killer stood, mortars), when the base counts as under fire and when not,
                        which teams counterattack, place 0 and the fire mission in the reply, the
                        attacker moving, the threat ending, --no-defence, --test-threat, and the
                        model being told and not able to undo it
  test_rules_v27.py     7 checks: Report.sqs 15 sends the killer's side; only the enemy side's
                        killers count as an attack on the base; the mortars-off flag
  test_rules_v28.py     11 checks: the mortar crew: who is picked, order 1 home then order 4, not
                        sent to counterattack, never kicked, replaced, released
  test_rules_v29.py     13 checks: the crew team number in the reply, a small team preferred as
                        crew, the mortars lifting fire while one of ours is near their target or
                        the target is near the base, and the rounds fired read from Report.sqs 17
  test_rules_v30.py     12 checks: Report.sqs 18 (HE stations, how many manned, the commander's
                        guard), no field crew when the guard is reported, resistance killing our
                        men near the base as an attack, a crew kept down to 2 men
  test_rules_v31.py     7 checks: --rules-side, one side on the rules and the other on the model
  test_rules_v32.py     11 checks: the air response: anti-air soldiers for the 3 teams nearest an enemy
                        attack aircraft and for the base, waves 5 minutes apart, the attack helicopter team
  test_end_to_end.py    11 checks: raw game text in, reply out, including a damaged report, a closed
                        console and a crash inside the relay
  test_replays.py       replays logged games through the relay with stand-in models; any error,
                        malformed reply or missing order is a failure. A team on TAKE_TOWNS must
                        be sent to take towns, to the flag of the town it holds, or against an attacker at the base
  sqs_check.py          static checks on the mission scripts in Documents\Cold War Assault\Missions:
                        line ends, duplicate labels, goto without a label, brackets and quotes

fixtures\               one damaged report exactly as the game sent it, the three relay 18 games
                        of 8 October 2026 (9, 5 and 4 towns), the three relay 19 games
                        (16, 14 and 15 towns), two relay 20 games of 9 October: rules only,
                        round 3 (seven teams round one flag for 36 minutes) and model, round 3
                        (18 towns, one tank team frozen in the field), and one relay 22 game with
                        the engine's diagnostic texts: rules only, round 2 (a tank driver holding
                        his dead commander's driving order for 17 minutes)

The tests are written against relay version 28. When the relay's rules change, the tests that describe
the old rule must change with it, in the same delivery.

Analysis tools (they read session logs and print a report; they change nothing)

    python tools\trial_summary.py logs      towns, captures, losses and, for model games, how fast
                                            the model wrote and how many plans it gave too late
    python tools\holds.py logs             relay 25: every hold, how it ended, and how many towns
                                            were lost within three minutes of the holder leaving.
                                            Add a text to read only some logs: holds.py logs 20261010
    python tools\at_town.py logs            time spent at towns that were not taken; reads the
                                            manifest of a trial if the folder holds one
    python tools\frozen_diag.py logs        what the engine says about every team that stood
                                            still, and a count of the three causes found on
                                            9 October (needs the engine patch apply_llm_engine.py)
    python tools\standing_still.py logs\session_20261008_21*.jsonl
    python tools\vehicle_teams.py logs\session_20261008_21*.jsonl
