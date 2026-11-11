$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*omni*watch*" }
if ($procs) {
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force
        Write-Host "Stopped OmniContext daemon (PID: $($p.ProcessId))"
    }
} else {
    Write-Host "No active OmniContext daemon found."
}
