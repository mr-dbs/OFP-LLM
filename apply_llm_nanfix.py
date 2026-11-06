"""
apply_llm_nanfix.py - 5 November 2026: the fix for the freeze in heavy rocket and HE fire.

Usage:   python apply_llm_nanfix.py C:\\dev\\CWR

The freeze (dumps of 24 October and 5 November 2026): a shell explodes at a position that is not a number
(NaN). Landscape::ExplosionDammage then asks Landscape::Visible how far the ground shields each nearby object.
With a NaN end point the second walk in Landscape::Visible, which has no step limit, runs about 2.1 billion
map cells, for each of hundreds of objects. The game hangs with its sound looping. The 24 October dump froze
in the next step of the same explosion (ExplosionDammageEffects > Disclose) for the same reason.

What it changes, in  engine/Poseidon/World/Simulation/Collisions.cpp  only:
  1. Landscape::ExplosionDammage        skips an explosion whose position is not a finite number (one log line)
  2. Landscape::ExplosionDammageEffects the same, for the path that clients take
  3. Landscape::Visible                 returns 0 (not visible) at once when an end point is not finite
  and a small helper, LlmFinite, that tests a number by its bits (safe under fast-math builds)
With valid numbers nothing changes. Safe to run twice: it does nothing if the fix is already there.

Then rebuild (close the game first):  rebuild_engine.cmd
"""

import os
import sys

PATH = os.path.join("engine", "Poseidon", "World", "Simulation", "Collisions.cpp")
MARK = "LLM project fix (5 November 2026)"

EDITS = [
    ("""#include <cmath>
""", """#include <cmath>
#include <cstdint>
#include <cstring>

// LLM project fix (5 November 2026): true when a float is a finite number. It reads the bits, so it still
// works if the build is ever made with fast-math options, under which std::isfinite may be optimised away.
static inline bool LlmFinite(float value)
{
    std::uint32_t bits;
    std::memcpy(&bits, &value, sizeof bits);
    return (bits & 0x7f800000u) != 0x7f800000u;
}
"""),
    ("""void Landscape::ExplosionDammage(EntityAI* owner, Shot* shot, Object* directHit, Vector3Par pos, Vector3Par dir,
                                 const AmmoType* type)
{
""", """void Landscape::ExplosionDammage(EntityAI* owner, Shot* shot, Object* directHit, Vector3Par pos, Vector3Par dir,
                                 const AmmoType* type)
{
    // LLM project fix (5 November 2026): an explosion whose position is not a finite number is skipped. With
    // such a position the shielding check in Landscape::Visible walks about 2 billion map cells for every
    // nearby object, and the game freezes with its sound looping (dumps of 24 October and 5 November 2026).
    if (!LlmFinite(pos.X()) || !LlmFinite(pos.Y()) || !LlmFinite(pos.Z()))
    {
        LOG_WARN(Physics, "Explosion at an invalid position skipped");
        return;
    }
"""),
    ("""void Landscape::ExplosionDammageEffects(EntityAI* owner, Shot* shot, Object* directHit, Vector3Par pos, Vector3Par dir,
                                        const AmmoType* type, bool enemyDammage)
{
""", """void Landscape::ExplosionDammageEffects(EntityAI* owner, Shot* shot, Object* directHit, Vector3Par pos, Vector3Par dir,
                                        const AmmoType* type, bool enemyDammage)
{
    // LLM project fix (5 November 2026): the same guard as in Landscape::ExplosionDammage, for clients.
    if (!LlmFinite(pos.X()) || !LlmFinite(pos.Y()) || !LlmFinite(pos.Z()))
    {
        return;
    }
"""),
    ("""float Landscape::Visible(Vector3Par from, Vector3Par to, float toRadius, const Object* skip1, const Object* target,
                         ObjIntersect isect) const
{
""", """float Landscape::Visible(Vector3Par from, Vector3Par to, float toRadius, const Object* skip1, const Object* target,
                         ObjIntersect isect) const
{
    // LLM project fix (5 November 2026): no walk through the map from or to a point that is not a finite
    // number; the second walk below has no step limit.
    if (!LlmFinite(from.X()) || !LlmFinite(from.Y()) || !LlmFinite(from.Z()) ||
        !LlmFinite(to.X()) || !LlmFinite(to.Y()) || !LlmFinite(to.Z()))
    {
        return 0;
    }
"""),
]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = os.path.join(sys.argv[1], PATH)
    if not os.path.exists(path):
        print("Not found: " + path)
        return 1
    with open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if MARK in text:
        print("The fix is already in " + path + ". Nothing changed.")
        return 0
    crlf = "\r\n" in text
    for old, new in EDITS:
        if crlf:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            print("A place to change was not found exactly once (%d times). Nothing changed:\n%s" % (text.count(old), old))
            return 1
        text = text.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("Fixed: " + path + " (3 guards and a helper added)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
