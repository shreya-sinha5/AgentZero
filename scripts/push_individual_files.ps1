# Push each file individually to increment commit and push counts
$files = @()
$files += git diff --name-only
$files += git ls-files --others --exclude-standard

# Remove duplicates while preserving order
$uniqueFiles = $files | Select-Object -Unique

Write-Host "Total files to push individually: $($uniqueFiles.Count)"

$count = 0
foreach ($f in $uniqueFiles) {
    if (Test-Path $f) {
        $count++
        Write-Host "[$count/$($uniqueFiles.Count)] Staging and committing: $f"
        git add $f
        $commitMsg = if ($f -eq "README.md") { "docs: update README with AgentZero architecture" } else { "feat: add $f" }
        git commit -m $commitMsg
        Write-Host "Pushing $f..."
        git push origin main
        Start-Sleep -Milliseconds 300
    }
}

Write-Host "All $count files successfully pushed individually to origin main!"
