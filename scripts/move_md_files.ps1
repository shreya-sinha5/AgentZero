New-Item -ItemType Directory -Force -Path "Documents" | Out-Null
$mdFiles = (Get-ChildItem -Path . -Filter "*.md" -File).Name

foreach ($f in $mdFiles) {
    Write-Host "=== Moving $f into Documents ==="
    git mv $f "Documents/$f"
    git commit -m "refactor: move $f into Documents directory"
    Write-Host "Pushing move of $f to GitHub..."
    git push origin main
    Start-Sleep -Milliseconds 300
}

Write-Host "All markdown files moved and pushed individually!"
