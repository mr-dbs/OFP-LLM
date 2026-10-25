// [unit, category, showAllSides] call dbsArsFnFillItems -> index of the unit's current entry
// category 0 skin, 1 primary, 2 launcher, 3 sidearm, 4 items
private ["_u","_cat","_all","_list","_cur","_sel","_i","_side","_tag","_ok"];
_u = _this select 0;
_cat = _this select 1;
_all = _this select 2;
_sel = -1;
lbClear dbsArsIdcItems;

if (_cat == 0) then
{
	_side = 2;
	if (side _u == west) then {_side = 1};
	if (side _u == east) then {_side = 0};
	_cur = typeOf _u;
	{
		_ok = _all;
		if ((_x select 2) == _side) then {_ok = true};
		if ((_x select 2) == 2) then {_ok = true};
		if (_ok) then
		{
			_tag = "[E] ";
			if ((_x select 2) == 1) then {_tag = "[W] "};
			if ((_x select 2) == 2) then {_tag = ""};
			_i = lbAdd [dbsArsIdcItems, _tag + (_x select 1)];
			lbSetData [dbsArsIdcItems, _i, _x select 0];
			if ((_x select 0) == _cur) then {_sel = _i};
		};
	} forEach dbsArsSkins;
};

if ((_cat >= 1) and (_cat <= 3)) then
{
	_list = dbsArsPrimary;
	_cur = primaryWeapon _u;
	if (_cat == 2) then {_list = dbsArsLauncher; _cur = secondaryWeapon _u};
	if (_cat == 3) then {_list = dbsArsSidearm; _cur = [_u] call dbsArsFnSidearm};
	_i = lbAdd [dbsArsIdcItems, "<none>"];
	lbSetData [dbsArsIdcItems, _i, ""];
	if (_cur == "") then {_sel = _i};
	{
		_i = lbAdd [dbsArsIdcItems, _x select 1];
		lbSetData [dbsArsIdcItems, _i, _x select 0];
		if ((_x select 0) == _cur) then {_sel = _i};
	} forEach _list;
};

if (_cat == 4) then
{
	{
		_i = lbAdd [dbsArsIdcItems, _x select 1];
		lbSetData [dbsArsIdcItems, _i, _x select 0];
		lbSetValue [dbsArsIdcItems, _i, _x select 2];
	} forEach dbsArsItems;
	_sel = 0;
};

if (_sel >= 0) then {lbSetCurSel [dbsArsIdcItems, _sel]};
_sel
