// [unit, weapons, magazines] call dbsArsFnApplyGear
// Magazines go in first so weapons load on add.
private ["_u","_w","_m"];
_u = _this select 0;
_w = _this select 1;
_m = _this select 2;
removeAllWeapons _u;
{_u addMagazine _x} forEach _m;
{_u addWeapon _x} forEach _w;
if (primaryWeapon _u != "") then {_u selectWeapon (primaryWeapon _u)};
true
