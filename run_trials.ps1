# run_trials.ps1 (version 19)
# Runs headless MFCTI games back to back and packs the logs into one zip to upload.
# Each game gets its own relay, so their logs never mix. Nothing needs watching.
#
# There are three kinds of game:
#   stock   the stock MFCTI commander. The relay only logs.
#   rules   the relay commands East with its fixed rules and never asks the model. This is the control.
#   model   the relay commands East and asks the model.
#
# The matched comparison (9 games, about 3 hours): the same three pairs of start positions for each kind.
#   powershell -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only all -Rounds 3 -Matched
# Rules against model only (6 games, about 2 hours):
#   powershell -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only control -Rounds 3 -Matched
# Three model games from random starts, as before (about 1 hour):
#   powershell -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only model -Rounds 3
#
# To finish a trial that was cut short, run only the rounds that are missing. Round 3 for rules and model:
#   powershell -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only control -Rounds 3 -FirstRound 3 -Matched
#
# The diagnostic trial (6 games, about 2 hours): what is a team doing when it stands still?
#   powershell -ExecutionPolicy Bypass -File C:\ofp-llm\run_trials.ps1 -Only all -Rounds 2 -Matched
#
# New in version 19:
#   - needs relay.py version 32 and LLM\Report.sqs version 19 (the air response, 22 October)
#
# Version 18:
#   - both sides under the relay. -Only duel: the model commands both sides. -Only head: two games a round with
#     the model against the rules, once with the model on East and once on West ("versus" and "versusflip")
#   - -Funds "200000,50000": the same funds for both sides (side, then each team) in every game of the trial
#   - East's towns are read from East's own reports, and West's towns from the same reports, so a log that
#     holds both sides is read right
#   - needs relay.py version 31 and LLM\Init.sqs version 11 (19 October)
#
# Version 17:
#   - needs relay.py version 30, LLM\Report.sqs version 18 and LLM\Init.sqs version 10 (18 October)
#
# Version 16:
#   - -Island nogova (the default) or everon. Everon runs mfcti116a_stock.Eden and mfcti116a_llmv1a.Eden, with
#     four start pairs of its own (18 October)
#
# Version 15:
#   - needs relay.py version 29, LLM\Report.sqs version 17, LLM\Init.sqs version 9 and the crew cap in
#     Main\UpdateIndependentAI.sqs (18 October)
#
# Version 14:
#   - needs relay.py version 28 and LLM\Report.sqs version 16 (17 October)
#
# Version 13:
#   - needs relay.py version 27 and LLM\Report.sqs version 15 (15 October)
#
# Version 12:
#   - needs relay.py version 26 and LLM\Report.sqs version 14 (base defence pack of 12 October)
#   - -RelayOptions "--test-threat=20" passes options to the relay in rules and model games (not stock games).
#     --test-threat=N makes up an attacker 800 m from East's base at game minute N, so the counterattack and the
#     fire mission run in a headless game. The manifest records the options ("relay_options")
#
# Version 11:
#   - -ExtraMods "@ECP;@new" loads more mod folders from Documents\Cold War Assault\Workshop after @MFCTI, in the
#     start check and in every game. Each folder must exist or the trial does not start. The manifest records the
#     full mod list ("mods"), so trials with and without addons are never mixed up
#
# Version 10:
#   - the speed check loads the model with the same context size as relay.py does (CONTEXT_TOKENS). Version 9
#     asked with Ollama's default (4096 in the trial of 10 October, where the relay uses 8192), so Ollama
#     loaded the model twice, and the check measured a smaller load than the game puts on the graphics card
#
# Version 9 (the model games of the trial of 10 October were lost to a slow model: 7 tokens a second
# where it writes 110 to 140, one to two minutes for each answer):
#   - needs relay.py version 24
#   - before a trial with model games, and again before every model game, the model is asked for a short text
#     and timed. Below -MinModelSpeed tokens a second (60) it is tried twice more a minute apart; if it is
#     still slow that model game is skipped and the trial goes on with the others. -NoModelCheck runs anyway
#   - each check keeps what "ollama ps" and "nvidia-smi" said, so a slow model can be traced to what took
#     the graphics card. It is printed when the model is slow and stored in the manifest
#   - the results table gives each model game's speed and how many plans the model did not give in time
#
# Version 8:
#   - needs relay.py version 23 and the mission scripts of 9 October, fifth pack (report script 13, Init 8)
#   - needs the game rebuilt with apply_llm_engine.py (engine level 2: the diagnostics and the fix for a driver
#     left with a dead commander's driving order). With -Matched the one-minute check game confirms it and
#     stops if the game is below that. -NoEngineCheck runs anyway
#   - the results table and the manifest give each game's engine level
#
# Version 7:
#   - needs relay.py version 22 and the mission scripts of 9 October, fourth pack (report script 12, Init 7)
#   - needs the game rebuilt with apply_llm_diag.py. With -Matched the one-minute check game confirms that the
#     game has the diagnostic commands and stops if it does not. -NoEngineCheck runs anyway
#   - the results table and the manifest say for each game whether it carried engine diagnostics
#
# Version 6:
#   - -FirstRound N starts at round N instead of round 1, so the missing rounds of an interrupted trial can
#     be run with the same start positions they would have had
#
# Version 5:
#   - needs relay.py version 21 and the mission scripts of 9 October, third pack, and checks for both
#     (report script 11, LLM\Init.sqs 6, and the new LLM\TownWatch.sqs that recounts the capture circles)
#   - the results table and the manifest say how many towns the recount handed to each side in each game
#
# Version 4:
#   - relay.py version 20 and the mission scripts of 9 October, second pack
#   - -Only rules, control (rules and model) and all (stock, rules and model)
#   - -Matched: round 1 uses the first pair of start positions for every kind, round 2 the second, and so on
#     (four pairs, then they repeat). Without it both sides start at random, as in a normal game
#     Before the first game a one-minute check game confirms that the mission really takes the fixed start,
#     and every game's log is checked again afterwards
#   - a manifest in the zip: what ran, from where, with which versions and file hashes
#
# Version 3: prints the towns held at the end of each game.
# Version 2: the relay writes to a file; checks before starting; warns if a log stops early.

param(
    [ValidateRange(1, 20)]
    [int]$Rounds = 1,                                      # how many times to run each kind of game
    [ValidateRange(1, 20)]
    [int]$FirstRound = 1,                                  # start at this round (to finish a trial that was cut short)
    [switch]$NoEngineCheck,                                # run even if the game lacks this project's engine changes
    [switch]$NoModelCheck,                                 # run model games even if the model is slow
    [int]$MinModelSpeed = 60,                              # tokens a second the model must write. It writes 110 to 140 when well
    [ValidateSet("both", "stock", "model", "rules", "control", "all", "duel", "head", "versus", "versusflip")]
    [string]$Only = "both",                                # both = stock and model, control = rules and model, all = all three
    [switch]$Matched,                                      # fixed start positions, the same for every kind in a round
    [int]$Scale = 4,                                       # game speed. 4 is the fastest that still judges the model fairly
    [int]$GameMinutes = 80,                                # length of each game in game minutes
    [string]$ExtraMods = "",                               # more Workshop mod folders after @MFCTI, e.g. "@ECP;@new"
    [string]$RelayOptions = "",                            # passed to the relay in rules and model games, e.g. "--test-threat=20"
    [ValidateSet("nogova", "everon")]
    [string]$Island = "nogova",                            # which island's missions to run
    [string]$Funds = ""                                    # "side,team" funds for both sides, e.g. "200000,50000"
)

$server   = "C:\dev\CWR\dist\x64-win-rwdi\PoseidonServer.exe"
$gameDir  = "E:\steam\steamapps\common\ARMA Cold War Assault\Remastered"
$workshop = "C:\Users\tumbl\Documents\Cold War Assault\Workshop"
$modDir   = Join-Path $workshop "@MFCTI"
foreach ($extra in ($ExtraMods -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
    $extraPath = if ([System.IO.Path]::IsPathRooted($extra)) { $extra } else { Join-Path $workshop $extra }
    if (-not (Test-Path $extraPath)) { Write-Host "Mod folder not found: $extraPath" -ForegroundColor Red; exit 1 }
    $modDir = "$modDir;$extraPath"
}
Write-Host "Mods: $modDir" -ForegroundColor Cyan
$missions = "C:\Users\tumbl\Documents\Cold War Assault\Missions"
$relay    = "C:\ofp-llm\relay.py"
$logs     = "C:\ofp-llm\logs"

# What each kind of game runs.
$suffix = if ($Island -eq "everon") { ".Eden" } else { ".noe" }
Write-Host "Island: $Island" -ForegroundColor Cyan
$kindTable = @{
    stock = @{ Mission = "mfcti116a_stock$suffix";  RelayArgument = "" }
    rules = @{ Mission = "mfcti116a_llmv1a$suffix"; RelayArgument = " --rules" }
    model = @{ Mission = "mfcti116a_llmv1a$suffix"; RelayArgument = "" }
    duel       = @{ Mission = "mfcti116a_llmv1a$suffix"; RelayArgument = "";                    BothSides = $true }
    versus     = @{ Mission = "mfcti116a_llmv1a$suffix"; RelayArgument = " --rules-side=West";  BothSides = $true }
    versusflip = @{ Mission = "mfcti116a_llmv1a$suffix"; RelayArgument = " --rules-side=East";  BothSides = $true }
}
$modelKinds = @("model", "duel", "versus", "versusflip")
$fundsText = ""
if ($Funds) {
    $fundsParts = @($Funds -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' })
    if ($fundsParts.Count -ne 2) { Write-Host "-Funds must be two whole numbers, side then team, e.g. 200000,50000" -ForegroundColor Red; exit 1 }
    $fundsText = "; llmTestFunds = [{0},{1}]" -f $fundsParts[0], $fundsParts[1]
    Write-Host "Funds for both sides: $($fundsParts[0]) a side, $($fundsParts[1]) a team" -ForegroundColor Cyan
}
$kinds = @(switch ($Only) {
    "both"    { "stock", "model" }
    "control" { "rules", "model" }
    "all"     { "stock", "rules", "model" }
    "head"    { "versus", "versusflip" }
    default   { $Only }
})
if ($FirstRound -gt $Rounds) {
    Write-Host "-FirstRound $FirstRound is past -Rounds $Rounds. Nothing to run." -ForegroundColor Red
    exit 1
}

# Start positions for -Matched: map coordinates of West's start, then East's. Each side starts at the
# starting location nearest its point. All eight points are starts seen in earlier trial games.
$startPairs = @(
    @{ Name = "East Mirov east, West Lany";    West = "11098,3903"; East = "4649,7397"  },
    @{ Name = "East Lany, West Mokropsy";      West = "4675,10142"; East = "11098,3903" },
    @{ Name = "East Petrovice, West Loukov";   West = "10384,8494"; East = "4105,4393"  },
    @{ Name = "East Loukov, West far west";    West = "1420,4512";  East = "10384,8494" }
)
# Everon: two pairs of opposite ends of the island, each played both ways round.
if ($Island -eq "everon") {
    $startPairs = @(
        @{ Name = "East Saint Phillippe, West Durras";  West = "8985,2452";  East = "5062,10293" },
        @{ Name = "East Durras, West Saint Phillippe";  West = "5062,10293"; East = "8985,2452"  },
        @{ Name = "East Le Moule, West Laruns";         West = "7290,5267";  East = "2580,6162"  },
        @{ Name = "East Laruns, West Le Moule";         West = "2580,6162";  East = "7290,5267"  }
    )
}

$seconds = [int]($GameMinutes * 60 / $Scale)
$missionNames = @($kinds | ForEach-Object { $kindTable[$_].Mission } | Select-Object -Unique)

function Set-TestStart($missionName, $text) {
    # The mission reads this file when it places the two sides. An empty list means the stock random placement.
    Set-Content -Path (Join-Path (Join-Path $missions $missionName) "LLM\TestStart.sqf") -Value $text -NoNewline -Encoding ASCII
}

function Test-StartApplied($sessionPath, $pair) {
    # True if East's base in the first report is at the pair's East point, False if it is somewhere else,
    # $null if the log has no first report with a base position.
    try {
        $line = Select-String -Path $sessionPath -Pattern '"side": "East"' | Select-Object -First 1
        if (-not $line) { return $null }
        $first = ($line.Line | ConvertFrom-Json).state
        if (-not $first -or -not $first.base_pos) { return $null }
        $want = @($pair.East -split "," | ForEach-Object { [double]$_ })
        $dx = [double]$first.base_pos[0] - $want[0]
        $dy = [double]$first.base_pos[1] - $want[1]
        return ([math]::Sqrt($dx * $dx + $dy * $dy) -lt 400)
    } catch { return $null }
}

function Get-ModelName {
    $line = Select-String -Path $relay -Pattern '^MODEL = "([^"]+)"' | Select-Object -First 1
    if ($line) { return $line.Matches[0].Groups[1].Value }
    return "gpt-oss:20b"
}

function Get-ModelContext {
    $line = Select-String -Path $relay -Pattern '^CONTEXT_TOKENS = (\d+)' | Select-Object -First 1
    if ($line) { return [int]$line.Matches[0].Groups[1].Value }
    return 8192
}

function Test-ModelSpeed {
    # Asks the model for a short text. Returns how fast it wrote (tokens a second, as Ollama measured it,
    # so the time to load the model is not counted) and what Ollama and the graphics card report.
    $result = [ordered]@{ tokens_per_second = 0; seconds = 0; error = ""; ollama_ps = ""; gpu = "" }
    $body = @{ model = (Get-ModelName); stream = $false; think = "low";
               messages = @(@{ role = "user"; content = "Write the numbers from 1 to 120, separated by spaces. Nothing else." });
               options = @{ num_predict = 300; temperature = 0; num_ctx = (Get-ModelContext) } } | ConvertTo-Json -Depth 5
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $answer = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 240
        if ($answer.eval_count -and $answer.eval_duration) {
            $result.tokens_per_second = [math]::Round([double]$answer.eval_count / ([double]$answer.eval_duration / 1000000000), 1)
        } else {
            $result.error = "the model answered without its timing"
        }
    } catch {
        $result.error = "$($_.Exception.Message)"
    }
    $result.seconds = [math]::Round($watch.Elapsed.TotalSeconds, 1)
    try { $result.ollama_ps = ((& ollama ps 2>&1) | Out-String).Trim() } catch { $result.ollama_ps = "ollama ps could not be run" }
    try {
        $card = ((& nvidia-smi "--query-gpu=name,memory.used,memory.total,utilization.gpu" "--format=csv,noheader" 2>&1) | Out-String).Trim()
        $apps = ((& nvidia-smi "--query-compute-apps=process_name,used_memory" "--format=csv,noheader" 2>&1) | Out-String).Trim()
        $result.gpu = "$card`n$apps"
    } catch { $result.gpu = "nvidia-smi could not be run" }
    return $result
}

function Wait-ModelSpeed($label) {
    # Up to three checks a minute apart. Returns the last check; .ok says whether the model is fast enough.
    $check = $null
    foreach ($try in 1..3) {
        $check = Test-ModelSpeed
        $check.ok = ($check.tokens_per_second -ge $MinModelSpeed)
        $check.when = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        $check.label = $label
        if ($check.ok) {
            Write-Host "   the model writes $($check.tokens_per_second) tokens a second"
            break
        }
        Write-Host ("   the model writes {0} tokens a second and needs {1}{2} (check {3} of 3)" -f $check.tokens_per_second, $MinModelSpeed,
            $(if ($check.error) { ": " + $check.error } else { "" }), $try) -ForegroundColor Yellow
        if ($try -lt 3) { Start-Sleep -Seconds 60 }
    }
    if (-not $check.ok) {
        Write-Host "   What Ollama says (it should read 100% GPU):" -ForegroundColor Yellow
        Write-Host $check.ollama_ps
        Write-Host "   What the graphics card says (memory used, and the programs using it):" -ForegroundColor Yellow
        Write-Host $check.gpu
    }
    return $check
}

function Get-EngineLevel($sessionPath) {
    # The engine level the mission reported in this game's log: 0 = none of the project's changes,
    # 1 = the diagnostic commands, 2 = also the driver fix. A log from older scripts says only whether
    # the diagnostics were there, which counts as 1. A log that says neither counts as 0.
    $found = Select-String -Path $sessionPath -Pattern '"engine_level": (\d+)' | Select-Object -First 1
    if ($found) { return [int]$found.Matches[0].Groups[1].Value }
    if (Select-String -Path $sessionPath -Pattern '"has_diag": true' -Quiet) { return 1 }
    return 0
}

# ---- checks before starting ----
foreach ($path in @($server, $gameDir, (Join-Path $workshop "@MFCTI"), $relay) + ($missionNames | ForEach-Object { Join-Path $missions $_ })) {
    if (-not (Test-Path $path)) { Write-Host "Missing: $path" -ForegroundColor Red; exit 1 }
}
New-Item -ItemType Directory -Force -Path $logs | Out-Null

$versionLine = Select-String -Path $relay -Pattern "^VERSION = (\d+)" | Select-Object -First 1
$relayVersion = 0
if ($versionLine) { $relayVersion = [int]$versionLine.Matches[0].Groups[1].Value }
Write-Host "relay.py is version $relayVersion"
if ($relayVersion -lt 32) {
    Write-Host "This script needs relay.py version 32 or later. Save the new relay.py into C:\ofp-llm first." -ForegroundColor Red
    exit 1
}
$scriptChecks = @(
    @{ File = "LLM\Report.sqs";               Pattern = "\(version 19\)" },
    @{ File = "LLM\Init.sqs";                 Pattern = "\(version 11\)" },
    @{ File = "LLM\TownWatch.sqs";            Pattern = "\(version 1\)" },
    @{ File = "Main\UpdateIndependentAI.sqs"; Pattern = "llmCrewMax" },
    @{ File = "Main\UpdateCommanderAI.sqs";   Pattern = "tank team is given tanks only" },
    @{ File = "Main\PlaceSides.sqs";          Pattern = "llmTestStart" },
    @{ File = "LLM\TestStart.sqf";            Pattern = "llmTestStart" }
)
foreach ($name in $missionNames) {
    $folder = Join-Path $missions $name
    foreach ($check in $scriptChecks) {
        $file = Join-Path $folder $check.File
        $current = (Test-Path $file) -and (Select-String -Path $file -Pattern $check.Pattern -Quiet)
        if (-not $current) {
            Write-Host "$name has an old or missing $($check.File). Run the latest install_*.cmd in C:\ofp-llm first." -ForegroundColor Red
            exit 1
        }
    }
}
Write-Host "mission scripts are current"

if ($kinds -contains "model") {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 | Out-Null
        Write-Host "Ollama is running"
    } catch {
        Write-Host "Ollama is not answering on http://localhost:11434. Start it, then run this again." -ForegroundColor Red
        exit 1
    }
}
if (Get-NetTCPConnection -LocalPort 8777 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "Something is already listening on port 8777. Close any open relay window, then run this again." -ForegroundColor Red
    exit 1
}

# ---- with -Matched: one short game to confirm the mission takes the fixed start position ----
if ($Matched) {
    Write-Host "Checking that the mission takes a fixed start position (about one minute)..."
    $checkStamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $checkStarted = Get-Date
    $checkMission = $missionNames[0]
    Set-TestStart $checkMission ("llmTestStart = [[{0}],[{1}]]" -f $startPairs[0].West, $startPairs[0].East)
    $checkOut = Join-Path $logs "relay_startcheck_$checkStamp.log"
    $checkRelay = Start-Process python -ArgumentList "`"$relay`" `"$checkOut`" --rules" -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 4
    & $server --simulate (Join-Path $missions $checkMission) --time-scale $Scale --duration 60 --stats 60 `
        --log-file (Join-Path $logs "server_startcheck_$checkStamp.log") -C $gameDir --mod $modDir
    Start-Sleep -Seconds 3
    if (-not $checkRelay.HasExited) { Stop-Process -Id $checkRelay.Id -Force }
    Start-Sleep -Seconds 3
    Set-TestStart $checkMission "llmTestStart = []"
    $checkSession = Get-ChildItem $logs -Filter "session_*.jsonl" | Where-Object { $_.LastWriteTime -ge $checkStarted } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $applied = $null
    if ($checkSession) { $applied = Test-StartApplied $checkSession.FullName $startPairs[0] }
    if ($applied -eq $true) {
        Write-Host "the mission takes the fixed start position"
        # Which of the project's engine changes does the game have? The mission asks the game and reports it.
        $engineLevel = Get-EngineLevel $checkSession.FullName
        if ($engineLevel -ge 2) {
            Write-Host "the game has the engine changes (level $engineLevel)"
        } elseif ($NoEngineCheck) {
            Write-Host "the game's engine is at level $engineLevel, not 2. Continuing because of -NoEngineCheck." -ForegroundColor Yellow
        } else {
            Write-Host "The game's engine is at level $engineLevel and this trial needs level 2 (0 = no changes, 1 = diagnostics only, 2 = diagnostics and the driver fix). Nothing was run." -ForegroundColor Red
            Write-Host "Close the game, then:" -ForegroundColor Red
            Write-Host "   python C:\ofp-llm\apply_llm_engine.py C:\dev\CWR" -ForegroundColor Red
            Write-Host "   cd C:\dev\CWR" -ForegroundColor Red
            Write-Host "   cmake --build build/win-x64-clang-rwdi" -ForegroundColor Red
            Write-Host "and run this again. To run without it, add -NoEngineCheck." -ForegroundColor Red
            exit 1
        }
    } elseif ($applied -eq $false) {
        Write-Host "The mission ignored the fixed start position: East started somewhere else. Nothing was run." -ForegroundColor Red
        Write-Host "Run without -Matched for random starts, and send me $($checkSession.FullName)" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "The check game sent no report, so the start position could not be confirmed. Nothing was run." -ForegroundColor Red
        Write-Host "See $checkOut" -ForegroundColor Red
        exit 1
    }
    if (Get-NetTCPConnection -LocalPort 8777 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "The relay from the check game is still running and could not be stopped. Nothing was run." -ForegroundColor Red
        exit 1
    }
}

$modelChecks = @()
if (($kinds -contains "model") -and -not $NoModelCheck) {
    Write-Host "Checking the model's speed..."
    $check = Wait-ModelSpeed "before the trial"
    $modelChecks += $check
    if (-not $check.ok) {
        # Nobody may be watching, so the trial goes on: the other kinds run, and each model game is checked
        # again when its turn comes and skipped if the model is still slow then.
        Write-Host "The model is too slow to command a game: a model game now would only measure the slow model." -ForegroundColor Red
        Write-Host "Something else is using the graphics card, or Ollama has loaded the model onto the processor." -ForegroundColor Red
        Write-Host "The trial goes on. Each model game is checked again when its turn comes and is skipped if the model is still slow." -ForegroundColor Red
        Write-Host "To free the card: close what uses it, then   ollama stop $(Get-ModelName)   . To run model games anyway, add -NoModelCheck." -ForegroundColor Red
    }
}

$total = ($Rounds - $FirstRound + 1) * $kinds.Count
Write-Host ("{0} games ({1}), about {2} minutes in all{3}" -f $total, ($kinds -join ", "), [int]($total * ($seconds + 15) / 60),
    $(if ($Matched) { ", matched start positions" } else { ", random start positions" }))

# ---- the games ----
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$produced = @()
$games = @()
$done = 0
$abort = $false
try {
    foreach ($round in $FirstRound..$Rounds) {
        if ($abort) { break }
        $pair = $null
        if ($Matched) { $pair = $startPairs[($round - 1) % $startPairs.Count] }
        foreach ($kind in $kinds) {
            $done++
            $name = $kindTable[$kind].Mission
            $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $started = Get-Date
            Write-Host ""
            Write-Host ("=== Game {0} of {1} : {2} (round {3}{4}), about {5} minutes ===" -f $done, $total, $kind, $round,
                $(if ($pair) { ", " + $pair.Name } else { "" }), [int]($seconds / 60)) -ForegroundColor Cyan

            $modelSpeed = ""
            if (($modelKinds -contains $kind) -and -not $NoModelCheck) {
                $check = Wait-ModelSpeed ("before game {0}: model, round {1}" -f $done, $round)
                $modelChecks += $check
                $modelSpeed = $check.tokens_per_second
                if (-not $check.ok) {
                    Write-Host "   The model is too slow. This game is skipped." -ForegroundColor Red
                    $games += [ordered]@{ kind = $kind; mission = $name; round = $round; start = $(if ($pair) { $pair.Name } else { "random" });
                                          session = ""; relay_log = ""; server_log = ""; last_minute = 0; east_towns = "skipped"; west_towns = ""; start_applied = "";
                                          recount = ""; engine_level = 0; model_speed = $modelSpeed; model_failed = 0; skipped = "model too slow" }
                    continue
                }
            }

            $startText = if ($pair) { "llmTestStart = [[{0}],[{1}]]" -f $pair.West, $pair.East } else { "llmTestStart = []" }
            if ($kindTable[$kind].BothSides) { $startText += "; llmTestSides = [east, west]" }
            Set-TestStart $name ($startText + $fundsText)

            $relayOut  = Join-Path $logs "relay_${kind}_$stamp.log"
            $serverLog = Join-Path $logs "server_${kind}_$stamp.log"
            $relayArguments = "`"$relay`" `"$relayOut`"" + $kindTable[$kind].RelayArgument
            if ($RelayOptions -and $kind -ne "stock") { $relayArguments += " " + $RelayOptions }
            $relayProcess = Start-Process python -ArgumentList $relayArguments -PassThru -WindowStyle Minimized
            Start-Sleep -Seconds 4

            & $server --simulate (Join-Path $missions $name) --time-scale $Scale --duration $seconds --stats 60 `
                --log-file $serverLog -C $gameDir --mod $modDir

            Start-Sleep -Seconds 3
            if (-not $relayProcess.HasExited) { Stop-Process -Id $relayProcess.Id -Force }
            Start-Sleep -Seconds 3
            Set-TestStart $name "llmTestStart = []"
            if (Get-NetTCPConnection -LocalPort 8777 -State Listen -ErrorAction SilentlyContinue) {
                # A relay that is still running would take the next game's reports into this game's log.
                Write-Host "   The relay from this game is still running and could not be stopped. Stopping here." -ForegroundColor Red
                $abort = $true
            }

            # How far did the relay's own log get, and how did the game end?
            $game = [ordered]@{ kind = $kind; mission = $name; round = $round; start = $(if ($pair) { $pair.Name } else { "random" });
                                session = ""; relay_log = (Split-Path $relayOut -Leaf); server_log = (Split-Path $serverLog -Leaf);
                                last_minute = 0; east_towns = "?"; west_towns = "?"; start_applied = ""; recount = ""; engine_level = 0;
                                model_speed = $modelSpeed; model_failed = 0; skipped = "" }
            $session = Get-ChildItem $logs -Filter "session_*.jsonl" | Where-Object { $_.LastWriteTime -ge $started } |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if (-not $session) {
                Write-Host "   WARNING: the relay wrote no log for this game. See $relayOut" -ForegroundColor Yellow
            } else {
                $reports = (Get-Content $session.FullName | Measure-Object -Line).Lines
                $game.engine_level = Get-EngineLevel $session.FullName
                # Reports for which the model gave no plan in time (the relay marks them and the rules decided).
                $game.model_failed = @(Select-String -Path $session.FullName -Pattern '"model_failed": "').Count
                if ($game.model_failed -ge 5) {
                    Write-Host "   WARNING: the model gave no plan in time for $($game.model_failed) reports. The rules commanded then. This is not a clean model game." -ForegroundColor Yellow
                }
                try {
                    $lastEast = Select-String -Path $session.FullName -Pattern '"side": "East"' | Select-Object -Last 1
                    $lastState = $null
                    if ($lastEast) { $lastState = ($lastEast.Line | ConvertFrom-Json).state }
                    if ($lastState) {
                        $game.last_minute = [double]$lastState.minute
                        $game.east_towns = @($lastState.towns | Where-Object { $_.owner -eq "us" }).Count
                        $game.west_towns = @($lastState.towns | Where-Object { $_.owner -eq "enemy" }).Count
                        if ($lastState.recounts) {
                            $game.recount = "{0} to East, {1} to West, {2} to the resistance" -f $lastState.recounts.east, $lastState.recounts.west, $lastState.recounts.resistance
                        }
                    }
                } catch { }
                $game.session = $session.Name
                if ($pair) {
                    $applied = Test-StartApplied $session.FullName $pair
                    $game.start_applied = $(if ($applied -eq $true) { "yes" } elseif ($applied -eq $false) { "NO" } else { "not checked" })
                    if ($applied -eq $false) {
                        Write-Host "   WARNING: this game did NOT start from the fixed position. It is not a matched game." -ForegroundColor Yellow
                    }
                }
                Write-Host ("   {0}: {1} reports, the last at game minute {2:N0}. East held {3} towns at the end, West {4}" -f $session.Name, $reports, $game.last_minute, $game.east_towns, $game.west_towns)
                if ($game.last_minute -lt ($GameMinutes * 0.85)) {
                    Write-Host "   WARNING: the log stops early (expected about minute $GameMinutes). See $relayOut" -ForegroundColor Yellow
                }
                $produced += $session.FullName
            }
            foreach ($file in @($relayOut, $serverLog)) { if (Test-Path $file) { $produced += $file } }
            $games += $game
            if ($abort) { break }
        }
    }
} finally {
    # Whatever happened, leave both missions on the stock random placement.
    foreach ($name in $missionNames) { Set-TestStart $name "llmTestStart = []" }
}

# ---- the results, and one zip to upload ----
Write-Host ""
if ($games.Count -gt 0) {
    Write-Host "East towns at the end:" -ForegroundColor Green
    foreach ($game in $games) {
        if ($game.skipped) {
            Write-Host ("   round {0}  {1,-6} SKIPPED: {2} ({3} tokens a second)" -f $game.round, $game.kind, $game.skipped, $game.model_speed) -ForegroundColor Yellow
            continue
        }
        Write-Host ("   round {0}  {1,-10} East {2,3}  West {8,3}   {3}{4}{5}{6}{7}" -f $game.round, $game.kind, $game.east_towns, $game.start,
            $(if ($game.start_applied -eq "NO") { "   (start NOT applied)" } else { "" }),
            $(if ($game.recount) { "   recount: " + $game.recount } else { "   (no recount reported)" }),
            $(if ($game.engine_level -ge 2) { "" } else { "   (engine level $($game.engine_level), NOT 2)" }),
            $(if ($modelKinds -notcontains $game.kind) { "" } else {
                "   model " + $(if ("$($game.model_speed)" -ne "") { "$($game.model_speed) tokens a second" } else { "speed not checked" }) +
                $(if ($game.model_failed -gt 0) { ", NO PLAN IN TIME for $($game.model_failed) reports" } else { "" }) }), $game.west_towns)
    }
}
if ($produced.Count -gt 0) {
    $hashes = [ordered]@{ "relay.py" = (Get-FileHash $relay -Algorithm SHA256).Hash }
    foreach ($name in $missionNames) {
        foreach ($file in @("mission.sqm") + ($scriptChecks | ForEach-Object { $_.File })) {
            $full = Join-Path (Join-Path $missions $name) $file
            if (Test-Path $full) { $hashes["$name\$file"] = (Get-FileHash $full -Algorithm SHA256).Hash }
        }
    }
    $manifest = [ordered]@{ run = $runStamp; run_trials_version = 19; funds = $Funds; island = $Island; relay_version = $relayVersion; mods = $modDir; relay_options = $RelayOptions; scale = $Scale;
                            game_minutes = $GameMinutes; matched = [bool]$Matched; kinds = $kinds; games = $games;
                            model_checks = $modelChecks; sha256 = $hashes }
    $manifestFile = Join-Path $logs "manifest_$runStamp.json"
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $manifestFile -Encoding ASCII
    $produced += $manifestFile

    $zip = Join-Path $logs "trials_$runStamp.zip"
    Compress-Archive -Path $produced -DestinationPath $zip -Force
    Write-Host ""
    $skippedGames = @($games | Where-Object { $_.skipped }).Count
    Write-Host ("{0} of {1} games ran{2}. Upload this one file:" -f ($games.Count - $skippedGames), $total,
        $(if ($skippedGames -gt 0) { ", $skippedGames skipped" } else { "" })) -ForegroundColor Green
    Write-Host "   $zip"
} else {
    Write-Host "The games ran but no logs were produced." -ForegroundColor Yellow
}
