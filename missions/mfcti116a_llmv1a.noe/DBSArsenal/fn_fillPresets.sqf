// [] call dbsArsFnFillPresets
private ["_i"];
lbClear dbsArsIdcPresets;
{
	_i = lbAdd [dbsArsIdcPresets, format ["%1  [%2]", _x select 0, [_x select 1] call dbsArsFnName]];
	lbSetData [dbsArsIdcPresets, _i, _x select 0];
} forEach dbsArsPresets;
true
