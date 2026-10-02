#Requires -RunAsAdministrator
# Run this yourself from an administrator PowerShell window.
# Only the official account/game services on LAN/Radmin are permitted.
$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$pythonExecutable = (Get-Command python -ErrorAction Stop).Source
$pythonBackgroundExecutable = (Get-Command pythonw -ErrorAction Stop).Source
$godotExecutable = 'A:\Installer\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe'
if (-not (Test-Path -LiteralPath $godotExecutable)) { throw 'The configured Godot executable is missing.' }
$interfaces = @(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -in @('Ethernet', 'Radmin VPN') } | Select-Object -ExpandProperty InterfaceAlias -Unique)
if ($interfaces.Count -eq 0) { throw 'No Ethernet or Radmin VPN interface was found.' }
$rules = @(
    @{ Name='BeyondHeroesOfficialAccounts'; Label='Beyond Heroes Official Accounts (LAN and Radmin)'; Protocol='TCP'; Port=8443; Program=$pythonExecutable },
    @{ Name='BeyondHeroesOfficialAccountsBackground'; Label='Beyond Heroes Official Accounts Background (LAN and Radmin)'; Protocol='TCP'; Port=8443; Program=$pythonBackgroundExecutable },
    @{ Name='BeyondHeroesOfficialGame'; Label='Beyond Heroes Official Game (LAN and Radmin)'; Protocol='UDP'; Port=24680; Program=$godotExecutable }
)
foreach ($rule in $rules) {
    if (Get-NetFirewallRule -Name $rule.Name -ErrorAction SilentlyContinue) {
        Write-Output ($rule.Label + ': rule already exists; inspect it if connectivity fails.')
        continue
    }
    New-NetFirewallRule -Name $rule.Name -DisplayName $rule.Label -Direction Inbound -Action Allow -Enabled True -Profile Any -InterfaceAlias $interfaces -RemoteAddress LocalSubnet -Protocol $rule.Protocol -LocalPort $rule.Port -Program $rule.Program | Out-Null
    Write-Output ($rule.Label + ': allowed on local Ethernet/Radmin networks.')
}
Write-Output 'Friends can now try the official address on your LAN or Radmin network. Router settings were not changed.'
