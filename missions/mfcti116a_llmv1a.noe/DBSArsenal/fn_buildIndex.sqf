// Appends MFCTI stock weapons from Stats.sqs and builds lookup tables.
private ["_known","_lists","_w","_a","_n","_sp","_slot","_i","_cnt","_e","_c"];

_known = [];
{_known = _known + [_x select 0]} forEach (dbsArsPrimary + dbsArsLauncher + dbsArsSidearm);

_lists = [
	[westPrimaryWeapons,westPrimaryAmmo,westPrimaryNames,westPrimaryAmmoSpaces,1],
	[eastPrimaryWeapons,eastPrimaryAmmo,eastPrimaryNames,eastPrimaryAmmoSpaces,1],
	[westSecondaryWeapons,westSecondaryAmmo,westSecondaryNames,[],2],
	[eastSecondaryWeapons,eastSecondaryAmmo,eastSecondaryNames,[],2],
	[westSidearms,westSidearmAmmo,westSidearmNames,[],3],
	[eastSidearms,eastSidearmAmmo,eastSidearmNames,[],3]
];

{
	_w = _x select 0;
	_a = _x select 1;
	_n = _x select 2;
	_sp = _x select 3;
	_slot = _x select 4;
	_i = 1;
	while {_i < count _w} do
	{
		_c = _w select _i;
		if (not (_c in _known)) then
		{
			_cnt = 6;
			if (_slot == 1) then
			{
				if (_i < count _sp) then
				{
					if ((_sp select _i) > 1) then {_cnt = (8 - (8 mod (_sp select _i))) / (_sp select _i)};
				};
			};
			if (_slot == 2) then {_cnt = 1};
			if (_slot == 3) then {_cnt = 4};
			_e = [_c, format ["%1 (MFCTI)", _n select _i], [_a select _i], _cnt];
			if (_slot == 1) then {dbsArsPrimary = dbsArsPrimary + [_e]};
			if (_slot == 2) then {dbsArsLauncher = dbsArsLauncher + [_e]};
			if (_slot == 3) then {dbsArsSidearm = dbsArsSidearm + [_e]};
			_known = _known + [_c];
		};
		_i = _i + 1;
	};
} forEach _lists;

dbsArsWpnClasses = [];
dbsArsWpnMags = [];
dbsArsWpnCount = [];
{
	dbsArsWpnClasses = dbsArsWpnClasses + [_x select 0];
	dbsArsWpnMags = dbsArsWpnMags + [_x select 2];
	dbsArsWpnCount = dbsArsWpnCount + [_x select 3];
} forEach (dbsArsPrimary + dbsArsLauncher + dbsArsSidearm);

dbsArsSidearmClasses = [];
{dbsArsSidearmClasses = dbsArsSidearmClasses + [_x select 0]} forEach dbsArsSidearm;

dbsArsNameKeys = [];
dbsArsNameVals = [];
{
	dbsArsNameKeys = dbsArsNameKeys + [_x select 0];
	dbsArsNameVals = dbsArsNameVals + [_x select 1];
} forEach (dbsArsSkins + dbsArsPrimary + dbsArsLauncher + dbsArsSidearm + dbsArsItems);

true
