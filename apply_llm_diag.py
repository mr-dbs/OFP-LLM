"""
apply_llm_diag.py - adds two read-only diagnostic script commands to the engine source.

Usage:   python apply_llm_diag.py C:\\dev\\CWR

What it does (safe to run twice):
  1. writes the new file  engine/Poseidon/Game/Commands/GameStateExtLlmDiag.cpp
  2. adds four lines to   engine/Poseidon/Game/Commands/GameStateExt.cpp
     so the game knows the commands  llmUnitInfo  and  llmGroupInfo

Neither command changes anything in the game. They report which order a unit's subgroup is carrying
out and who issued it, which no existing script command can tell.

It needs the LLM bridge (apply_llm_bridge.py) to be in the source already. If it is not, nothing is changed.

Then rebuild (close the game first), from the source folder:
   cmake --build build/win-x64-clang-rwdi
"""

import os
import sys

COMMANDS_DIR = os.path.join("engine", "Poseidon", "Game", "Commands")

DECL_ANCHOR = "GameValue LlmResult(const GameState* state, GameValuePar oper1);"
DECL_LINES = [
    "GameValue LlmUnitInfo(const GameState* state, GameValuePar oper1);",
    "GameValue LlmGroupInfo(const GameState* state, GameValuePar oper1);",
]

TABLE_ANCHOR = '        GameFunction(GameString, "llmResult", LlmResult, GameScalar),'
TABLE_LINES = [
    '        GameFunction(GameString, "llmUnitInfo", LlmUnitInfo, GameObject),',
    '        GameFunction(GameString, "llmGroupInfo", LlmGroupInfo, GameObject),',
]

NEW_FILE_NAME = "GameStateExtLlmDiag.cpp"
NEW_FILE_TEXT = r'''// LLM commander diagnostics. Project addition - not part of upstream CWR.
//
//   _text = llmUnitInfo obj    -> string: what the unit that commands obj is doing
//   _text = llmGroupInfo obj   -> string: every subgroup of obj's group and the order it holds
//
// Both only read. They change nothing in the game.
//
// obj may be a soldier or a vehicle. For a vehicle, the unit is the crewman who commands it,
// which the engine picks by seat (commander, then gunner, then driver) and not by rank.
//
// Why these exist: a mission script can tell that a subgroup holds an order (unitReady) but not which
// order, nor who issued it. An order from a script goes to the back of the subgroup's queue
// (AISubgroup::ReceiveCommand, CtxMission: EnqueueTask). An order the engine issues by itself (attack,
// rearm, repair, heal, get out) goes to the front (CtxAuto: PushTask) and no script order removes it.
// A team that stands still with a script order pending is waiting behind one of those. These commands
// name it.
//
// The text is a list of key=value words separated by spaces. It never holds a quote or a bracket,
// so it can sit inside a script array that is printed with format.

#include <Poseidon/Core/Application.hpp>

#include <Poseidon/World/Scene/Object.hpp>
#include <Poseidon/Game/Commands/GameStateExt.hpp>
#include <Poseidon/Game/Commands/GameStateExtCommon.hpp>

#include <Poseidon/World/World.hpp>
#include <Poseidon/Core/Global.hpp>
#include <Poseidon/AI/VehicleAI.hpp>
#include <Poseidon/AI/AI.hpp>
#include <Poseidon/World/Entities/Vehicles/Transport.hpp>

#include <cstdio>
#include <string>

using namespace Poseidon;

namespace
{
const char* MessageName(Command::Message message)
{
    switch (message)
    {
        case Command::NoCommand:
            return "NONE";
        case Command::Wait:
            return "WAIT";
        case Command::Attack:
            return "ATTACK";
        case Command::Hide:
            return "HIDE";
        case Command::Move:
            return "MOVE";
        case Command::Heal:
            return "HEAL";
        case Command::Repair:
            return "REPAIR";
        case Command::Refuel:
            return "REFUEL";
        case Command::Rearm:
            return "REARM";
        case Command::Support:
            return "SUPPORT";
        case Command::Join:
            return "JOIN";
        case Command::GetIn:
            return "GETIN";
        case Command::Fire:
            return "FIRE";
        case Command::GetOut:
            return "GETOUT";
        case Command::Stop:
            return "STOP";
        case Command::Expect:
            return "EXPECT";
        case Command::Action:
            return "ACTION";
#if ENABLE_HOLDFIRE_FIX
        case Command::AttackAndFire:
            return "ATTACKFIRE";
#endif
        default:
            return "OTHER";
    }
}

const char* ContextName(Command::Context context)
{
    switch (context)
    {
        case Command::CtxUndefined:
            return "UNDEF";
        case Command::CtxAuto:
            return "AUTO";
        case Command::CtxAutoSilent:
            return "AUTOSILENT";
        case Command::CtxJoin:
            return "JOIN";
        case Command::CtxAutoJoin:
            return "AUTOJOIN";
        case Command::CtxEscape:
            return "ESCAPE";
        case Command::CtxMission:
            return "MISSION";
        case Command::CtxUI:
            return "UI";
        case Command::CtxUIWithJoin:
            return "UIJOIN";
        default:
            return "OTHER";
    }
}

const char* StateName(AIUnit::State state)
{
    switch (state)
    {
        case AIUnit::Wait:
            return "WAIT";
        case AIUnit::Init:
            return "INIT";
        case AIUnit::Busy:
            return "BUSY";
        case AIUnit::Completed:
            return "COMPLETED";
        case AIUnit::Delay:
            return "DELAY";
        case AIUnit::InCargo:
            return "INCARGO";
        case AIUnit::Stopping:
            return "STOPPING";
        case AIUnit::Replan:
            return "REPLAN";
        case AIUnit::Stopped:
            return "STOPPED";
        case AIUnit::Sending:
            return "SENDING";
        default:
            return "OTHER";
    }
}

const char* PlanName(AIUnit::PlanningMode mode)
{
    switch (mode)
    {
        case AIUnit::DoNotPlan:
            return "NONE";
        case AIUnit::LeaderPlanned:
            return "LEADERPLANNED";
        case AIUnit::LeaderDirect:
            return "LEADERDIRECT";
        case AIUnit::FormationPlanned:
            return "FORMATION";
        case AIUnit::VehiclePlanned:
            return "VEHICLE";
        default:
            return "OTHER";
    }
}

const char* SubgroupModeName(AISubgroup::Mode mode)
{
    switch (mode)
    {
        case AISubgroup::Wait:
            return "WAIT";
        case AISubgroup::PlanAndGo:
            return "PLANANDGO";
        case AISubgroup::DirectGo:
            return "DIRECTGO";
        default:
            return "OTHER";
    }
}

const char* SemaphoreName(AI::Semaphore semaphore)
{
    switch (semaphore)
    {
        case AI::SemaphoreBlue:
            return "BLUE";
        case AI::SemaphoreGreen:
            return "GREEN";
        case AI::SemaphoreWhite:
            return "WHITE";
        case AI::SemaphoreYellow:
            return "YELLOW";
        case AI::SemaphoreRed:
            return "RED";
        default:
            return "NONE";
    }
}

const char* ResourceName(AIUnit::ResourceState state)
{
    switch (state)
    {
        case AIUnit::RSNormal:
            return "N";
        case AIUnit::RSLow:
            return "L";
        case AIUnit::RSCritical:
            return "C";
        default:
            return "?";
    }
}

// Letters, digits and underscore only, so the text can never break the script array it is printed in.
std::string Plain(const char* text)
{
    std::string out;
    if (text != nullptr)
    {
        for (const char* p = text; *p != '\0' && out.size() < 32; ++p)
        {
            const char c = *p;
            const bool keep = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_';
            out.push_back(keep ? c : '_');
        }
    }
    return out.empty() ? std::string("-") : out;
}

void Add(std::string& out, const char* key, const char* value)
{
    if (!out.empty())
    {
        out.push_back(' ');
    }
    out.append(key);
    out.push_back('=');
    out.append(value);
}

void Add(std::string& out, const char* key, int value)
{
    char buffer[32];
    std::snprintf(buffer, sizeof(buffer), "%d", value);
    Add(out, key, buffer);
}

std::string TypeNameOf(EntityAI* entity)
{
    if (entity == nullptr)
    {
        return "-";
    }
    const EntityType* type = entity->GetNonAIType();
    if (type == nullptr)
    {
        return "-";
    }
    RString name = type->GetName();
    return Plain((const char*)name);
}

// The order at the front of a subgroup's queue, from where the unit `from` stands.
void AddCommand(std::string& out, AISubgroup* subgroup, AIUnit* from)
{
    Add(out, "stack", subgroup->StackSize());
    Add(out, "mode", SubgroupModeName(subgroup->GetMode()));
    const Command* command = subgroup->GetCommand();
    if (command == nullptr)
    {
        Add(out, "cmd", "NONE");
        return;
    }
    Add(out, "cmd", MessageName(command->_message));
    Add(out, "ctx", ContextName(command->_context));

    const auto* current = subgroup->GetCurrent();
    if (current != nullptr && current->_fsm && current->_fsm->GetState() >= 0)
    {
        Add(out, "step", Plain(current->_fsm->GetStateName()).c_str());
    }

    // Not every order has a place or a time limit; those are left at zero and at the earliest time.
    EntityAI* vehicle = (from != nullptr) ? from->GetVehicle() : nullptr;
    if (vehicle != nullptr && command->_destination.SquareSizeXZ() > 1.0f)
    {
        const float distance = vehicle->Position().DistanceXZ(command->_destination);
        if (distance >= 0.0f && distance < 100000.0f)
        {
            Add(out, "dist", static_cast<int>(distance));
        }
    }
    if (command->_time > TIME_MIN && command->_time < TIME_MAX)
    {
        const float left = command->_time - Glob.time;
        if (left > -100000.0f && left < 100000.0f)
        {
            Add(out, "left", static_cast<int>(left));
        }
    }

    Target* enemy = command->_targetE;
    EntityAI* exact = command->_target;
    if (enemy != nullptr)
    {
        EntityAI* enemyVehicle = enemy->idExact;
        Add(out, "tgt", TypeNameOf(enemyVehicle).c_str());
        Add(out, "tgtdead",
            (enemy->destroyed || enemyVehicle == nullptr || enemyVehicle->IsDammageDestroyed()) ? 1 : 0);
    }
    else if (exact != nullptr)
    {
        Add(out, "tgt", TypeNameOf(exact).c_str());
        Add(out, "tgtdead", exact->IsDammageDestroyed() ? 1 : 0);
    }
}

AIUnit* UnitOf(GameValuePar oper)
{
    Object* object = GetObject(oper);
    EntityAI* entity = dyn_cast<EntityAI>(object);
    if (entity == nullptr)
    {
        return nullptr;
    }
    return entity->CommanderUnit();
}
} // namespace

GameValue LlmUnitInfo(const GameState* /*state*/, GameValuePar oper1)
{
    AIUnit* unit = UnitOf(oper1);
    if (unit == nullptr || unit->GetPerson() == nullptr)
    {
        return GameValue("none");
    }
    AIGroup* group = unit->GetGroup();
    AISubgroup* subgroup = unit->GetSubgroup();
    if (group == nullptr || subgroup == nullptr)
    {
        return GameValue("nogroup");
    }

    std::string out;
    AIUnit* groupLeader = group->Leader();
    AIUnit* subgroupLeader = subgroup->Leader();
    Add(out, "id", unit->ID());
    Add(out, "gl", groupLeader != nullptr ? groupLeader->ID() : 0);
    Add(out, "sl", subgroupLeader != nullptr ? subgroupLeader->ID() : 0);
    Add(out, "main", subgroup == group->MainSubgroup() ? 1 : 0);
    Add(out, "n", subgroup->NUnits());
    Add(out, "subs", group->NSubgroups());
    AddCommand(out, subgroup, unit);

    Add(out, "state", StateName(unit->GetState()));
    Add(out, "plan", PlanName(unit->GetPlanningMode()));
    Add(out, "away", unit->IsAway() ? 1 : 0);
    Add(out, "sem", SemaphoreName(unit->GetSemaphore()));
    Add(out, "ammo", ResourceName(unit->GetAmmoState()));
    Add(out, "armor", ResourceName(unit->GetArmorState()));
    Add(out, "health", ResourceName(unit->GetHealthState()));
    Add(out, "fuel", ResourceName(unit->GetFuelState()));
    Add(out, "asg", unit->GetTargetAssigned() != nullptr ? 1 : 0);
    Add(out, "eng", unit->GetEngageTarget() != nullptr ? 1 : 0);
    Add(out, "noai", unit->GetAIDisabled());
    Add(out, "flee", group->GetFlee() ? 1 : 0);

    EntityAI* vehicle = unit->GetVehicle();
    if (vehicle != nullptr)
    {
        const float wanted = vehicle->Position().DistanceXZ(unit->GetWantedPosition());
        if (wanted >= 0.0f && wanted < 100000.0f)
        {
            Add(out, "want", static_cast<int>(wanted));
        }
        Add(out, "ustop", vehicle->IsUserStopped() ? 1 : 0);
        Add(out, "engine", vehicle->EngineIsOn() ? 1 : 0);
    }
    Transport* transport = unit->GetVehicleIn();
    if (transport != nullptr)
    {
        Person* driver = transport->Driver();
        Add(out, "drv", (driver != nullptr && driver->Brain() != nullptr) ? 1 : 0);
        AIUnit* pilot = transport->PilotUnit();
        Add(out, "pilot", pilot != nullptr ? pilot->ID() : 0);
    }
    return GameValue(out.c_str());
}

GameValue LlmGroupInfo(const GameState* /*state*/, GameValuePar oper1)
{
    AIUnit* unit = UnitOf(oper1);
    AIGroup* group = (unit != nullptr) ? unit->GetGroup() : nullptr;
    if (group == nullptr)
    {
        return GameValue("none");
    }

    std::string out;
    const int count = group->NSubgroups();
    int listed = 0;
    for (int i = 0; i < count && listed < 8; ++i)
    {
        AISubgroup* subgroup = group->GetSubgroup(i);
        if (subgroup == nullptr)
        {
            continue;
        }
        std::string one;
        AIUnit* leader = subgroup->Leader();
        Add(one, "sl", leader != nullptr ? leader->ID() : 0);
        Add(one, "main", subgroup == group->MainSubgroup() ? 1 : 0);
        Add(one, "n", subgroup->NUnits());
        AddCommand(one, subgroup, leader);
        if (leader != nullptr)
        {
            Add(one, "state", StateName(leader->GetState()));
        }
        if (!out.empty())
        {
            out.append(" / ");
        }
        out.append(one);
        ++listed;
    }
    if (out.empty())
    {
        out = "none";
    }
    return GameValue(out.c_str());
}
'''


def find_anchor(lines, anchor, what):
    matches = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == anchor]
    if len(matches) != 1:
        print("STOPPED: expected exactly one line to anchor the %s, found %d." % (what, len(matches)))
        print("That line is added by apply_llm_bridge.py. Either the bridge is not in this source,")
        print("or the engine source differs from the version this script was written for (ffc6183).")
        print("Nothing was changed.")
        sys.exit(1)
    return matches[0]


def insert_after(lines, position, new_lines):
    newline = "\r\n" if lines[position].endswith("\r\n") else "\n"
    return lines[:position + 1] + [text + newline for text in new_lines] + lines[position + 1:]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    repo = sys.argv[1]
    commands = os.path.join(repo, COMMANDS_DIR)
    table_path = os.path.join(commands, "GameStateExt.cpp")
    if not os.path.isfile(table_path):
        print("STOPPED: could not find", table_path)
        print("Give the folder that contains the engine source, for example C:\\dev\\CWR")
        sys.exit(1)

    with open(table_path, "r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()
    text = "".join(lines)

    if "LlmUnitInfo" in text:
        print("GameStateExt.cpp already has the diagnostic lines - left as it is.")
    else:
        # Find both places before changing anything, so a failure leaves the file untouched.
        find_anchor(lines, DECL_ANCHOR, "declarations")
        find_anchor(lines, TABLE_ANCHOR, "command table entries")
        lines = insert_after(lines, find_anchor(lines, DECL_ANCHOR, "declarations"), DECL_LINES)
        lines = insert_after(lines, find_anchor(lines, TABLE_ANCHOR, "command table entries"), TABLE_LINES)
        with open(table_path, "w", encoding="utf-8", newline="") as handle:
            handle.writelines(lines)
        print("Added 4 lines to", table_path)

    new_path = os.path.join(commands, NEW_FILE_NAME)
    with open(new_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(NEW_FILE_TEXT)
    print("Wrote", new_path)
    print()
    print("Done. Close the game, then rebuild from the source folder:")
    print("   cmake --build build/win-x64-clang-rwdi")


if __name__ == "__main__":
    main()
