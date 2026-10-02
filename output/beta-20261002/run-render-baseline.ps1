param(
    [string]$Godot = 'A:\Installer\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe'
)

$ErrorActionPreference = 'Stop'
$betaRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$betaGame = Join-Path $betaRoot 'game'
$betaShots = Join-Path $PSScriptRoot 'gameplay-screenshots'
New-Item -ItemType Directory -Path $betaShots -Force | Out-Null
$betaCases = @(
    @{ Name='town-desktop'; Map='sanctuary'; Renderer='forward_plus'; Lite='0'; Touch='0' },
    @{ Name='town-mobile-renderer'; Map='sanctuary'; Renderer='gl_compatibility'; Lite='1'; Touch='1' },
    @{ Name='forest-desktop'; Map='ruined_forest'; Renderer='forward_plus'; Lite='0'; Touch='0' },
    @{ Name='forest-mobile-renderer'; Map='ruined_forest'; Renderer='gl_compatibility'; Lite='1'; Touch='1' },
    @{ Name='forest-combat-desktop'; Map='ruined_forest'; Renderer='forward_plus'; Lite='0'; Touch='0'; Stress='40' },
    @{ Name='forest-combat-mobile-renderer'; Map='ruined_forest'; Renderer='gl_compatibility'; Lite='1'; Touch='1'; Stress='40' }
)
$betaResults = @()
foreach ($betaCase in $betaCases) {
    $betaReport = Join-Path $PSScriptRoot ($betaCase.Name + '.json')
    if (Test-Path -LiteralPath $betaReport) { throw "Refusing to overwrite existing baseline: $betaReport" }
    $betaArgs = @('--path', $betaGame, '--rendering-method', $betaCase.Renderer,
        '--resolution', '1280x720', 'res://tests/tools/beta_release_perf.tscn', '--',
        '--class=knight', '--slot=97', ('--map=' + $betaCase.Map),
        ('--lite=' + $betaCase.Lite), ('--touch=' + $betaCase.Touch),
        '--spots=3', '--frames=300', ('--out=' + $betaReport))
    if ($betaCase.ContainsKey('Stress')) {
        $betaArgs += '--stress=' + $betaCase.Stress
    } else {
        $betaArgs += '--shots=' + $betaShots
    }
    $betaStart = Get-Date
    $betaProcess = Start-Process -FilePath $Godot -ArgumentList $betaArgs -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $PSScriptRoot ($betaCase.Name + '.stdout.log')) `
        -RedirectStandardError (Join-Path $PSScriptRoot ($betaCase.Name + '.stderr.log'))
    $betaFinished = $betaProcess.WaitForExit(180000)
    if (-not $betaFinished) {
        $betaProcess.Kill()
        throw "Render probe exceeded three minutes: $($betaCase.Name)"
    }
    $betaProcess.Refresh()
    $betaResults += @{name=$betaCase.Name; exit=$betaProcess.ExitCode; started=$betaStart.ToString('o'); report=$betaReport}
    $betaResults | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'render-runs.json')
    if ($betaProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $betaReport)) {
        throw "Render probe failed: $($betaCase.Name); inspect its logs."
    }
    $betaData = Get-Content -LiteralPath $betaReport -Raw | ConvertFrom-Json
    if ($betaData.window[0] -ne 1280 -or $betaData.window[1] -ne 720) {
        throw "Unexpected measured resolution for $($betaCase.Name): $($betaData.window)"
    }
    Write-Output "$($betaCase.Name): frame median=$($betaData.total.frame.median)ms p95=$($betaData.total.frame.p95)ms p99=$($betaData.total.frame.p99)ms"
}
