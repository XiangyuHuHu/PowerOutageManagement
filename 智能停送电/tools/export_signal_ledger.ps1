param(
    [Parameter(Mandatory = $true)]
    [string]$WorkbookPath,
    [string]$DeviceOutputPath = ".\data\signal_ledger_devices.json",
    [string]$SignalOutputPath = ".\data\signal_points_seed.json",
    [string]$SummaryOutputPath = ".\data\signal_ledger_summary.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Text($sheet, [int]$row, [int]$col) {
    return ($sheet.Cells.Item($row, $col).Text | ForEach-Object { "$_".Trim() })
}

function Is-Blank([string]$value) {
    return [string]::IsNullOrWhiteSpace($value)
}

function Looks-LikeDeviceId([string]$value) {
    if (Is-Blank $value) { return $false }
    return $value -match '^[A-Za-z0-9#][A-Za-z0-9_\-/#]*$'
}

$resolvedWorkbook = (Resolve-Path -LiteralPath $WorkbookPath).Path
$resolvedDeviceOutput = Join-Path (Get-Location) $DeviceOutputPath
$resolvedSignalOutput = Join-Path (Get-Location) $SignalOutputPath
$resolvedSummaryOutput = Join-Path (Get-Location) $SummaryOutputPath
$tempWorkbook = Join-Path $env:TEMP ("signal-ledger-" + [guid]::NewGuid().ToString() + ".xlsx")

$input = $null
$output = $null
try {
    $input = [System.IO.File]::Open($resolvedWorkbook, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $output = [System.IO.File]::Open($tempWorkbook, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $input.CopyTo($output)
}
finally {
    if ($output) { $output.Close() }
    if ($input) { $input.Close() }
}

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$workbook = $excel.Workbooks.Open($tempWorkbook, $null, $true)

$devices = New-Object System.Collections.Generic.List[object]
$signals = New-Object System.Collections.Generic.List[object]

try {
    foreach ($sheet in $workbook.Worksheets) {
        $rowCount = $sheet.UsedRange.Rows.Count

        for ($row = 1; $row -le $rowCount; $row++) {
            $col1 = Get-Text $sheet $row 1
            $col2 = Get-Text $sheet $row 2
            $col3 = Get-Text $sheet $row 3
            $col4 = Get-Text $sheet $row 4
            $col5 = Get-Text $sheet $row 5
            $col7 = Get-Text $sheet $row 7
            $col8 = Get-Text $sheet $row 8
            $col10 = Get-Text $sheet $row 10
            $col12 = Get-Text $sheet $row 12

            $deviceId = $null
            $deviceName = $null

            if ((Looks-LikeDeviceId $col2) -and -not (Is-Blank $col3)) {
                $deviceId = $col2
                $deviceName = $col3
            } elseif ((Looks-LikeDeviceId $col3) -and -not (Is-Blank $col4)) {
                $deviceId = $col3
                $deviceName = $col4
            }

            if ($deviceId) {
                $displayName = if (-not (Is-Blank $col5)) { $col5 } elseif (-not (Is-Blank $col1)) { $col1 } else { "$deviceId $deviceName" }

                $devices.Add([pscustomobject]@{
                    source_sheet = $sheet.Name
                    row_number = $row
                    sequence = $col1
                    device_id = $deviceId
                    device_name = $deviceName
                    display_name = $displayName
                    related_device_name = $col7
                    related_device_id = $col8
                    db_address = $col10
                    remote_local_input = $col12
                })

                if (-not (Is-Blank $col12)) {
                    $signals.Add([pscustomobject]@{
                        device_id = $deviceId
                        signal_type = "remote_local"
                        signal_name = "remote_local"
                        signal_address = $col12
                        data_type = "bool"
                        source_system = "plc"
                        source_sheet = $sheet.Name
                        description = if (-not (Is-Blank $col10)) { "linked register: $col10" } else { "" }
                        is_active = $true
                    })
                }
            }

            if ($col4 -like '*YCFHZ*' -and -not (Is-Blank $col5)) {
                $signals.Add([pscustomobject]@{
                    device_id = ($col5 -replace '_.*$', '')
                    signal_type = "remote_switch_binding"
                    signal_name = "remote_switch_binding"
                    signal_address = $col4
                    data_type = "binding"
                    source_system = "plc"
                    source_sheet = $sheet.Name
                    description = $col5
                    is_active = $true
                })
            }
        }
    }
}
finally {
    $workbook.Close($false)
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    if (Test-Path -LiteralPath $tempWorkbook) {
        Remove-Item -LiteralPath $tempWorkbook -Force -ErrorAction SilentlyContinue
    }
}

$devicesUnique = $devices | Sort-Object device_id, source_sheet, row_number -Unique
$signalsUnique = $signals | Sort-Object device_id, signal_type, signal_name, signal_address -Unique

$summary = [pscustomobject]@{
    workbook = $resolvedWorkbook
    exported_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    device_rows = @($devicesUnique).Count
    signal_rows = @($signalsUnique).Count
    unique_device_ids = (@($devicesUnique | Select-Object -ExpandProperty device_id -Unique)).Count
    signal_types = @($signalsUnique | Group-Object signal_type | ForEach-Object {
        [pscustomobject]@{
            signal_type = $_.Name
            count = $_.Count
        }
    })
}

$devicesUnique | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resolvedDeviceOutput -Encoding UTF8
$signalsUnique | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resolvedSignalOutput -Encoding UTF8
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resolvedSummaryOutput -Encoding UTF8

Write-Output "EXPORTED_DEVICES: $resolvedDeviceOutput"
Write-Output "EXPORTED_SIGNALS: $resolvedSignalOutput"
Write-Output "EXPORTED_SUMMARY: $resolvedSummaryOutput"
