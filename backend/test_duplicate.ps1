$content = "This is a dummy test file for duplicate testing. " * 100
Set-Content -Path test_duplicate.txt -Value $content

Write-Host "--- Uploading file for the first time ---"
$resp1 = Invoke-RestMethod -Uri http://localhost:8000/upload -Method Post -Form @{ files = Get-Item test_duplicate.txt }
Write-Host ($resp1 | ConvertTo-Json -Depth 5)

Write-Host "`n--- Uploading identical file again ---"
$resp2 = Invoke-RestMethod -Uri http://localhost:8000/upload -Method Post -Form @{ files = Get-Item test_duplicate.txt }
Write-Host ($resp2 | ConvertTo-Json -Depth 5)

if ($resp2.documents[0].status -eq "already_exists") {
    Write-Host "SUCCESS: duplicate detected"
} else {
    Write-Host "FAILED: duplicate not detected"
}
