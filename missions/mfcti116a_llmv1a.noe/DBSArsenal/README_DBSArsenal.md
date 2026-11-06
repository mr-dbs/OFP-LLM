# DBS Arsenal for MFCTI 1.16A (mfcti116a_llmv1a.Noe)

## Where it lives

| What | Where |
|---|---|
| Arsenal in MFCTI | `Documents\Cold War Assault\missions\mfcti116a_llmv1a.Noe\DBSArsenal` |
| Test mission (Everon) | `Documents\DBS_OFP\Projects\ArsenalTest\DBS_ArsenalTest.Eden` (editor copy in `Documents\Cold War Assault\missions\DBS_ArsenalTest.Eden`) |
| Test launcher | `Documents\DBS_OFP\Projects\ArsenalTest\Launch_ArsenalTest.cmd` |
| Test logs | `Documents\DBS_OFP\Logs\ArsenalTest` |

Arsenal-style loadout screen. Camera orbits the selected unit; skin, weapons and items change on the live unit as you click. Edits the player or any AI in the player's group. Presets save/load/delete and can be pushed to the whole squad.

## Use

Action menu -> **Arsenal** (available anywhere, on foot).

- SQUAD list: pick YOU or an AI. AI being edited is held in place (`stop true`) until you pick someone else or close.
- Tabs SKIN / PRIM / LAUN / SIDE / ITEM. Selecting a weapon equips it at once with its default magazines. `<none>` removes it.
- SKIN applies 0.6 s after the selection settles (so scrolling the list does not spawn a unit per row).
- ITEM tab: Add / Remove one at a time (grenades, smoke, flares, GL rounds, spare mags, binoculars, NVG).
- `+ mag` / `- mag`: one primary magazine.
- PRESETS: type a name, Save current. Same name overwrites. Load to unit applies gear then skin. Apply to squad AI runs the preset on every AI in your group.
- CAMERA: rotate, zoom, height.
- ESC or CLOSE exits.

## Settings (top of `Init.sqs`)

| Setting | Default | Meaning |
|---|---|---|
| `dbsArsEngineBody` | `false` | `true` once CWR has the `dbsSetBody` command; enables player skin change |
| `dbsArsPersist` | `true` | Save presets to disk with `saveConfig` / `loadConfig` |
| `dbsArsPresetFile` | `DBSArsenal_Presets.cfg` | Preset file name in the CWR user `Config` folder |
| `dbsArsOwnSideFirst` | `true` | Skin list starts filtered to the unit's own side |

Standalone mode (no MFCTI menus or bounty scripts): `[1] Exec "DBSArsenal\Init.sqs"`. Any argument switches it on.

## Files

| File | Role |
|---|---|
| `Init.sqs` | Settings block at the top, function loading, catalog build, preset load |
| `Catalog.sqf` | Skins, GR/BAS/RHS weapons, items. Edit to add/remove entries. MFCTI stock weapons from `Stats.sqs` are appended automatically |
| `Dialog.hpp` | Dialog, included at the end of `Description.ext` |
| `Arsenal.sqs` | Main loop |
| `SetSkin.sqs` / `SetSkinEngine.sqs` | Skin change (script path for AI / engine path for anyone) |
| `Rebind.sqs` | Re-attaches MFCTI player menus after a player body swap |
| `ApplySquad.sqs`, `Presets*.sqs`, `fn_*.sqf` | Helpers |
| `ENGINE_dbsSetBody.patch` | CWR engine patch for player skin change |
| `_backup_original/` | The four MFCTI files before the hooks were added |

## Hooks added to MFCTI (4 files, originals in `_backup_original/`)

- `Description.ext`: `#include "DBSArsenal\Dialog.hpp"` at the end.
- `Main\InitPlayer.sqs`: `[] Exec "DBSArsenal\Init.sqs"` after `@ (statsStarted)`.
- `Main\UpdatePlayer.sqs`: adds the Arsenal action after the menu scripts start; one line in each side's loop so a body swap is not treated as a death (`dbsArsSwapped`).
- `Main\ResetUnit.sqs`: re-adds the Arsenal action after respawn.

## Player skin change needs one engine command

OFP/CWA cannot change the model of the unit you are controlling from script, and CWR has no `selectPlayer`. AI skins work without it (the AI is replaced by a new unit of the new class in the same group and spot, gear copied).

`ENGINE_dbsSetBody.patch` adds `unit dbsSetBody "Class"` to CWR. It moves the unit's brain into a new body of the given class, the same way `NetworkClient::DoRespawn` builds a respawn body, so the group slot, leader status, player control, identity and variable name carry over. It returns the new unit, or objNull if the unit is dead, in a vehicle, or the class is not a soldier.

1. From `C:\dev\CWR`: `git apply DBSArsenal\ENGINE_dbsSetBody.patch` (touches `GameStateExt.cpp` and `GameStateExtWorld.cpp` in `engine\Poseidon\Game\Commands`).
2. Rebuild `PoseidonGame` (`cmake --build build/win-x64-clang-rwdi`).
3. In `DBSArsenal\Init.sqs` set `dbsArsEngineBody = true`.

With the flag on, AI skin changes also use the engine path (no unit replacement, keeps group order and rank).

Status: the patched `GameStateExtWorld.cpp` passes a clang C++20 syntax/semantic check against upstream CWR headers. It has not been run in game. The multiplayer branch (co-op client switching body) is best effort and untested.

## Presets on disk

`dbsArsPersist = true` uses CWR's `newConfig` / `saveConfig` / `loadConfig` to write `<CWR user dir>\Config\DBSArsenal_Presets.cfg`. Presets survive restarts and are shared by every mission that includes the arsenal. Set it false on an engine without those commands; presets then last for the session.

## Known limits

- Script-path AI skin change: the new AI joins at the end of the group order, comes back at default rank, and gets a fresh MFCTI cleanup/bounty script (bounty 50).
- If the group is full (12), the old AI is deleted before the new one is created; a bad class name in that case loses the unit. Catalog classes come from the GR config, so this only matters if you edit the catalog.
- OFP has 10 magazine slots. Adding past that fails silently in the engine.
- GR pistol and launcher hand fit is still unfinished in the mod (r009/r012 notes); those weapons equip but may look off.
- Skin list is filtered to the unit's side by default; the "Skins: own side / all sides" button toggles it. A cross-side skin still fights for the group's side.

## Test mission

`Launch_ArsenalTest.cmd` runs CWR (`PoseidonGame.exe`) with `@DBS_GR_DEV` straight into the test mission, windowed, logs to `Documents\DBS_OFP\Logs\ArsenalTest`, and prints any errors from the log when the game closes.

In the mission:

- Action menu "Arsenal", or radio 0-0-1.
- You: GR rifleman (sergeant). Squad: 5 GR AI to re-skin and re-equip.
- East GR squad 25 m north, captive, for looking at East skins.
- Crate beside you with the r012 BAS/RHS/GR weapon set.
- Stock OFP weapons are listed too (marked MFCTI).

The test mission's `DBSArsenal` folder is a copy of the MFCTI one running in standalone mode. Player skin change stays off in both copies until the engine patch is built and `dbsArsEngineBody = true`.

## Status

- The `ENGINE_dbsSetBody.patch` has not been applied or built yet.
- Scripts pass syntax checks; the arsenal has been run in the test mission.
