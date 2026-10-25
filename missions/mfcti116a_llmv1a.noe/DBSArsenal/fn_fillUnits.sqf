// [currentUnit] call dbsArsFnFillUnits -> [unitsArray, selectedIndex]
// Fills the squad list with the player and living members of the player's group.
private ["_cur","_us","_sel","_t","_i"];
_cur = _this select 0;
_us = [];
_sel = 0;
lbClear dbsArsIdcUnits;
{
	if (alive _x) then
	{
		_t = format ["AI %1", count _us];
		if (_x == player) then {_t = "YOU"};
		if (vehicle _x != _x) then {_t = _t + " (vehicle)"};
		_i = lbAdd [dbsArsIdcUnits, format ["%1 - %2", _t, [typeOf _x] call dbsArsFnName]];
		lbSetValue [dbsArsIdcUnits, _i, count _us];
		if (_x == _cur) then {_sel = count _us};
		_us = _us + [_x];
	};
} forEach (units group player);
lbSetCurSel [dbsArsIdcUnits, _sel];
[_us, _sel]
