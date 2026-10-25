// [unit] call dbsArsFnGet -> [skinClass, weapons, magazines]
private ["_u"];
_u = _this select 0;
[typeOf _u, weapons _u, magazines _u]
