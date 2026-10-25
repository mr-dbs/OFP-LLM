// [class] call dbsArsFnName -> display name, class if unknown, "-" if empty
private ["_c","_i","_r"];
_c = _this select 0;
_r = _c;
if (_c == "") then {_r = "-"};
_i = 0;
while {_i < count dbsArsNameKeys} do
{
	if ((dbsArsNameKeys select _i) == _c) then {_r = dbsArsNameVals select _i; _i = count dbsArsNameKeys};
	_i = _i + 1;
};
_r
