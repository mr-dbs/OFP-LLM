// [unit, slot, newClass] call dbsArsFnSetWeapon
// slot 1 primary, 2 launcher, 3 sidearm. newClass "" just removes.
// Removes the old weapon in that slot plus its catalog magazines, then adds the new one with magazines.
private ["_u","_slot","_new","_old","_i","_mags","_n","_k"];
_u = _this select 0;
_slot = _this select 1;
_new = _this select 2;

_old = "";
if (_slot == 1) then {_old = primaryWeapon _u};
if (_slot == 2) then {_old = secondaryWeapon _u};
if (_slot == 3) then {_old = [_u] call dbsArsFnSidearm};

if (_old != "") then
{
	_i = [_old] call dbsArsFnIndex;
	if (_i >= 0) then
	{
		{_u removeMagazines _x} forEach (dbsArsWpnMags select _i);
	}
	else
	{
		_u removeMagazines _old;
	};
	_u removeWeapon _old;
};

if (_new != "") then
{
	_i = [_new] call dbsArsFnIndex;
	_mags = [_new];
	_n = 4;
	if (_i >= 0) then {_mags = dbsArsWpnMags select _i; _n = dbsArsWpnCount select _i};
	_k = 0;
	while {_k < _n} do {_u addMagazine (_mags select 0); _k = _k + 1};
	if ((count _mags) > 1) then
	{
		_k = 0;
		while {_k < 3} do {_u addMagazine (_mags select 1); _k = _k + 1};
	};
	_u addWeapon _new;
	if (_slot == 1) then {_u selectWeapon _new};
};
true
