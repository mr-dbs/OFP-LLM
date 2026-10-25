// [index] call dbsArsFnPresetDelete
private ["_del","_n","_i"];
_del = _this select 0;
_n = [];
_i = 0;
while {_i < count dbsArsPresets} do
{
	if (_i != _del) then {_n = _n + [dbsArsPresets select _i]};
	_i = _i + 1;
};
dbsArsPresets = _n;
true
