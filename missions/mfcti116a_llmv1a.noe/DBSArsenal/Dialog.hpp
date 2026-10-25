// DBS Arsenal dialog. Included at the end of Description.ext (uses its Gui* base classes and defines).
// Left and right panels only, so the camera view of the unit stays clear in the middle.
// IDCs 9001-9009 mirror the dbsArsIdc* globals in DBSArsenal\Init.sqs.

class DBSArsenalMenu
{
	idd = -1;
	movingEnable = false;
	objects[] = {};
	controlsBackground[] = {DBSArsBgLeft,DBSArsBgRight};
	controls[] = {Title,UnitLabel,UnitList,BtnSkin,BtnPrimary,BtnLauncher,BtnSidearm,BtnItems,CatLabel,ItemList,BtnSideFilter,BtnAdd,BtnRemove,MagLabel,BtnMagAdd,BtnMagSub,Status,Hint1,InfoLabel,InfoList,PresetLabel,PresetList,NameLabel,NameEdit,BtnSave,BtnLoad,BtnDelete,BtnSquad,CamLabel,BtnRotL,BtnRotR,BtnZoomIn,BtnZoomOut,BtnUp,BtnDown,BtnClose};

	class DBSArsBgLeft:GuiText
	{
		style = GUISTYLEHUD;
		colorBackground[] = {0.06,0.07,0.06,0.85};
		text = "";
		x = 0.005; y = 0.015; w = 0.34; h = 0.94;
	};

	class DBSArsBgRight:GuiText
	{
		style = GUISTYLEHUD;
		colorBackground[] = {0.06,0.07,0.06,0.85};
		text = "";
		x = 0.655; y = 0.015; w = 0.34; h = 0.94;
	};

	class Title:GuiText
	{
		idc = -1;
		style = GUICENTER;
		x = 0.015; y = 0.025; w = 0.32; h = 0.035;
		sizeEx = 0.03;
		text = "DBS ARSENAL";
	};

	class UnitLabel:GuiText
	{
		idc = -1;
		style = GUILEFT;
		x = 0.015; y = 0.065; w = 0.32; h = 0.035;
		sizeEx = 0.022;
		text = "SQUAD (pick who to edit)";
	};

	class UnitList:GuiListBox
	{
		idc = 9001;
		x = 0.015; y = 0.1; w = 0.32; h = 0.15;
		sizeEx = 0.021;
		rowHeight = 0.028;
	};

	class BtnSkin:GuiButton
	{
		x = 0.015; y = 0.26; w = 0.062; h = 0.035;
		sizeEx = 0.02;
		text = "SKIN";
		action = "dbsArsBtn = ""CAT0""";
	};

	class BtnPrimary:GuiButton
	{
		x = 0.079; y = 0.26; w = 0.062; h = 0.035;
		sizeEx = 0.02;
		text = "PRIM";
		action = "dbsArsBtn = ""CAT1""";
	};

	class BtnLauncher:GuiButton
	{
		x = 0.143; y = 0.26; w = 0.062; h = 0.035;
		sizeEx = 0.02;
		text = "LAUN";
		action = "dbsArsBtn = ""CAT2""";
	};

	class BtnSidearm:GuiButton
	{
		x = 0.207; y = 0.26; w = 0.062; h = 0.035;
		sizeEx = 0.02;
		text = "SIDE";
		action = "dbsArsBtn = ""CAT3""";
	};

	class BtnItems:GuiButton
	{
		x = 0.271; y = 0.26; w = 0.062; h = 0.035;
		sizeEx = 0.02;
		text = "ITEM";
		action = "dbsArsBtn = ""CAT4""";
	};

	class CatLabel:GuiText
	{
		idc = 9006;
		style = GUILEFT;
		x = 0.015; y = 0.3; w = 0.32; h = 0.035;
		sizeEx = 0.022;
		text = "PRIMARY";
	};

	class ItemList:GuiListBox
	{
		idc = 9002;
		x = 0.015; y = 0.335; w = 0.32; h = 0.44;
		sizeEx = 0.021;
		rowHeight = 0.028;
	};

	class BtnSideFilter:GuiButton
	{
		idc = 9009;
		x = 0.015; y = 0.785; w = 0.16; h = 0.035;
		sizeEx = 0.02;
		text = "Skins: own side";
		action = "dbsArsBtn = ""SIDE""";
	};

	class BtnAdd:GuiButton
	{
		x = 0.18; y = 0.785; w = 0.075; h = 0.035;
		sizeEx = 0.02;
		text = "Add";
		action = "dbsArsBtn = ""ADD""";
	};

	class BtnRemove:GuiButton
	{
		x = 0.26; y = 0.785; w = 0.075; h = 0.035;
		sizeEx = 0.02;
		text = "Remove";
		action = "dbsArsBtn = ""REM""";
	};

	class MagLabel:GuiText
	{
		idc = 9008;
		style = GUILEFT;
		x = 0.015; y = 0.83; w = 0.2; h = 0.035;
		sizeEx = 0.022;
		text = "Primary mags: 0";
	};

	class BtnMagAdd:GuiButton
	{
		x = 0.22; y = 0.83; w = 0.055; h = 0.035;
		sizeEx = 0.02;
		text = "+ mag";
		action = "dbsArsBtn = ""MAGADD""";
	};

	class BtnMagSub:GuiButton
	{
		x = 0.28; y = 0.83; w = 0.055; h = 0.035;
		sizeEx = 0.02;
		text = "- mag";
		action = "dbsArsBtn = ""MAGSUB""";
	};

	class Status:GuiText
	{
		idc = 9007;
		style = GUILEFT;
		x = 0.015; y = 0.875; w = 0.32; h = 0.035;
		sizeEx = 0.02;
		text = "";
	};

	class Hint1:GuiText
	{
		idc = -1;
		style = GUILEFT;
		x = 0.015; y = 0.91; w = 0.32; h = 0.035;
		sizeEx = 0.018;
		text = "Skin/weapon applies on select. ESC or Close to exit.";
	};

	class InfoLabel:GuiText
	{
		idc = -1;
		style = GUICENTER;
		x = 0.665; y = 0.025; w = 0.32; h = 0.035;
		sizeEx = 0.026;
		text = "CURRENT LOADOUT";
	};

	class InfoList:GuiListBox
	{
		idc = 9003;
		x = 0.665; y = 0.06; w = 0.32; h = 0.3;
		sizeEx = 0.021;
		rowHeight = 0.028;
	};

	class PresetLabel:GuiText
	{
		idc = -1;
		style = GUILEFT;
		x = 0.665; y = 0.37; w = 0.32; h = 0.035;
		sizeEx = 0.022;
		text = "PRESETS";
	};

	class PresetList:GuiListBox
	{
		idc = 9004;
		x = 0.665; y = 0.405; w = 0.32; h = 0.2;
		sizeEx = 0.021;
		rowHeight = 0.028;
	};

	class NameLabel:GuiText
	{
		idc = -1;
		style = GUILEFT;
		x = 0.665; y = 0.615; w = 0.09; h = 0.035;
		sizeEx = 0.022;
		text = "Name:";
	};

	class NameEdit:GuiEditableText
	{
		idc = 9005;
		x = 0.75; y = 0.615; w = 0.235; h = 0.035;
		sizeEx = 0.022;
		text = "";
	};

	class BtnSave:GuiButton
	{
		x = 0.665; y = 0.66; w = 0.155; h = 0.035;
		sizeEx = 0.02;
		text = "Save current";
		action = "dbsArsBtn = ""SAVE""";
	};

	class BtnLoad:GuiButton
	{
		x = 0.83; y = 0.66; w = 0.155; h = 0.035;
		sizeEx = 0.02;
		text = "Load to unit";
		action = "dbsArsBtn = ""LOAD""";
	};

	class BtnDelete:GuiButton
	{
		x = 0.665; y = 0.705; w = 0.155; h = 0.035;
		sizeEx = 0.02;
		text = "Delete preset";
		action = "dbsArsBtn = ""DEL""";
	};

	class BtnSquad:GuiButton
	{
		x = 0.83; y = 0.705; w = 0.155; h = 0.035;
		sizeEx = 0.02;
		text = "Apply to squad AI";
		action = "dbsArsBtn = ""SQUAD""";
	};

	class CamLabel:GuiText
	{
		idc = -1;
		style = GUILEFT;
		x = 0.665; y = 0.76; w = 0.32; h = 0.035;
		sizeEx = 0.022;
		text = "CAMERA";
	};

	class BtnRotL:GuiButton
	{
		x = 0.665; y = 0.795; w = 0.077; h = 0.035;
		sizeEx = 0.02;
		text = "< Rot";
		action = "dbsArsBtn = ""ROTL""";
	};

	class BtnRotR:GuiButton
	{
		x = 0.745; y = 0.795; w = 0.077; h = 0.035;
		sizeEx = 0.02;
		text = "Rot >";
		action = "dbsArsBtn = ""ROTR""";
	};

	class BtnZoomIn:GuiButton
	{
		x = 0.825; y = 0.795; w = 0.077; h = 0.035;
		sizeEx = 0.02;
		text = "Zoom +";
		action = "dbsArsBtn = ""ZIN""";
	};

	class BtnZoomOut:GuiButton
	{
		x = 0.905; y = 0.795; w = 0.077; h = 0.035;
		sizeEx = 0.02;
		text = "Zoom -";
		action = "dbsArsBtn = ""ZOUT""";
	};

	class BtnUp:GuiButton
	{
		x = 0.665; y = 0.84; w = 0.157; h = 0.035;
		sizeEx = 0.02;
		text = "Cam up";
		action = "dbsArsBtn = ""UP""";
	};

	class BtnDown:GuiButton
	{
		x = 0.828; y = 0.84; w = 0.157; h = 0.035;
		sizeEx = 0.02;
		text = "Cam down";
		action = "dbsArsBtn = ""DOWN""";
	};

	class BtnClose:GuiButton
	{
		x = 0.665; y = 0.91; w = 0.32; h = 0.045;
		sizeEx = 0.025;
		text = "CLOSE";
		action = "dbsArsBtn = ""CLOSE""";
	};
};
