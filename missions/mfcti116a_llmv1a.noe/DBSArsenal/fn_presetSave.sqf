// [name, unit] call dbsArsFnPresetSave - adds or overwrites a preset by name
// Preset = [name, skinClass, weapons, magazines]
private ["_name","_u","_lo","_p","_i","_found"];
_name = _this select 0;
_u = _this select 1;
_lo = [_u] call dbsArsFnGet;
_p = [_name, _lo select 0, _lo select 1, _lo select 2];
_found = -1;
_i = 0;
while {_i < count dbsArsPresets} do
{
	if (((dbsArsPresets select _i) select 0) == _name) then {_found = _i};
	_i = _i + 1;
};
if (_found >= 0) then
{
	dbsArsPresets set [_found, _p];
}
else
{
	dbsArsPresets = dbsArsPresets + [_p];
};
true
