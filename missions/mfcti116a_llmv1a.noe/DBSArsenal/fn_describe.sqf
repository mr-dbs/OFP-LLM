// [unit] call dbsArsFnDescribe -> array of text lines for the loadout panel
private ["_u","_r","_ms","_uniq","_cnt","_i","_j","_other"];
_u = _this select 0;
_r = [];
_r = _r + [format ["Skin: %1", [typeOf _u] call dbsArsFnName]];
_r = _r + [format ["Primary: %1", [primaryWeapon _u] call dbsArsFnName]];
_r = _r + [format ["Launcher: %1", [secondaryWeapon _u] call dbsArsFnName]];
_r = _r + [format ["Sidearm: %1", [[_u] call dbsArsFnSidearm] call dbsArsFnName]];

_other = (weapons _u) - [primaryWeapon _u, secondaryWeapon _u, [_u] call dbsArsFnSidearm, "Throw", "Put"];
{_r = _r + [format ["Item: %1", [_x] call dbsArsFnName]]} forEach _other;

_r = _r + ["--- Magazines ---"];
_ms = magazines _u;
_uniq = [];
_cnt = [];
{
	_i = -1;
	_j = 0;
	while {_j < count _uniq} do
	{
		if ((_uniq select _j) == _x) then {_i = _j};
		_j = _j + 1;
	};
	if (_i < 0) then
	{
		_uniq = _uniq + [_x];
		_cnt = _cnt + [1];
	}
	else
	{
		_cnt set [_i, (_cnt select _i) + 1];
	};
} forEach _ms;

_j = 0;
while {_j < count _uniq} do
{
	_r = _r + [format ["%1 x%2", [_uniq select _j] call dbsArsFnName, _cnt select _j]];
	_j = _j + 1;
};
_r
