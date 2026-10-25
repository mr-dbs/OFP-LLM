// [class] call dbsArsFnIndex -> index in dbsArsWpnClasses or -1
private ["_c","_i","_r"];
_c = _this select 0;
_r = -1;
_i = 0;
while {(_i < count dbsArsWpnClasses) and (_r < 0)} do
{
	if ((dbsArsWpnClasses select _i) == _c) then {_r = _i};
	_i = _i + 1;
};
_r
