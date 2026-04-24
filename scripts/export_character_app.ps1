$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $root "dist"
$appDir = Join-Path $dist "AutoPTUCharacter"
$zipPath = Join-Path $dist "AutoPTUCharacter.zip"
$staticDir = Join-Path $root "auto_ptu\\api\\static"

if (!(Test-Path $appDir)) {
  New-Item -ItemType Directory -Force $appDir | Out-Null
}
Get-ChildItem -Path $appDir -Force | Remove-Item -Recurse -Force

Copy-Item (Join-Path $staticDir "index.html") (Join-Path $appDir "index.html") -Force
Copy-Item (Join-Path $staticDir "create.html") (Join-Path $appDir "create.html") -Force
Copy-Item (Join-Path $staticDir "styles.css") (Join-Path $appDir "styles.css") -Force
Copy-Item (Join-Path $staticDir "app.js") (Join-Path $appDir "app.js") -Force
Copy-Item (Join-Path $staticDir "character_creation.json") (Join-Path $appDir "character_creation.json") -Force
Copy-Item (Join-Path $staticDir "master_dataset.embed.js") (Join-Path $appDir "master_dataset.embed.js") -Force
Copy-Item (Join-Path $staticDir "pokedex_learnset.embed.js") (Join-Path $appDir "pokedex_learnset.embed.js") -Force
Copy-Item (Join-Path $staticDir "pokemon_move_sources.embed.js") (Join-Path $appDir "pokemon_move_sources.embed.js") -Force
Copy-Item (Join-Path $staticDir "design-system") (Join-Path $appDir "design-system") -Recurse -Force
Copy-Item (Join-Path $staticDir "vendor") (Join-Path $appDir "vendor") -Recurse -Force
Copy-Item (Join-Path $staticDir "logic") (Join-Path $appDir "logic") -Recurse -Force
Copy-Item (Join-Path $staticDir "ui") (Join-Path $appDir "ui") -Recurse -Force

if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}

Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $zipPath

Write-Output "Exported: $zipPath"
