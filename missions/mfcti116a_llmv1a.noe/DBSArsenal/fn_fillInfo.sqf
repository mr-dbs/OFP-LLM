// [unit] call dbsArsFnFillInfo - refreshes the loadout panel and primary magazine counter
private ["_u","_i","_n","_m"];
_u = _this select 0;
lbClear dbsArsIdcInfo;
{lbAdd [dbsArsIdcInfo, _x]} forEach ([_u] call dbsArsFnDescribe);

_n = 0;
_m = "";
_i = [primaryWeapon _u] call dbsArsFnIndex;
if (_i >= 0) then {_m = (dbsArsWpnMags select _i) select 0};
if ((_m == "") and (primaryWeapon _u != "")) then {_m = primaryWeapon _u};
{if (_x == _m) then {_n = _n + 1}} forEach (magazines _u);
ctrlSetText [dbsArsIdcMag, format ["Primary mags: %1", _n]];
true
