// [unit] call dbsArsFnSidearm -> current sidearm class or ""
private ["_u","_r"];
_u = _this select 0;
_r = "";
{if (_x in dbsArsSidearmClasses) then {_r = _x}} forEach (weapons _u);
_r
