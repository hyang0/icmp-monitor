# ICMP监控脚本
# 使用PowerShell监控ICMP活动

Write-Host "ICMP Ping 监控脚本" -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green
Write-Host "开始监控ICMP活动..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Yellow
Write-Host ""

# 存储已知的ping源IP
$knownIps = @{}

try {
    while ($true) {
        # 获取ICMP相关的网络事件
        $events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=5156} -MaxEvents 10 -ErrorAction SilentlyContinue | 
                  Where-Object { $_.Message -like "*ICMP*" }
        
        if ($events) {
            foreach ($event in $events) {
                # 提取源IP
                $message = $event.Message
                if ($message -match '源地址:\s*((?:\d{1,3}\.){3}\d{1,3})') {
                    $srcIp = $matches[1]
                    
                    # 排除本地地址
                    if ($srcIp -notlike "127.*" -and $srcIp -ne "0.0.0.0") {
                        if (-not $knownIps.ContainsKey($srcIp)) {
                            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                            Write-Host "[${timestamp}] ${srcIp} 开始ping本机" -ForegroundColor Cyan
                            $knownIps[$srcIp] = $timestamp
                        }
                    }
                }
            }
        }
        
        # 检查是否有IP停止ping（简单实现）
        # 这里简化处理，实际应用中需要更复杂的逻辑
        
        Start-Sleep -Seconds 3
    }
}
catch {
    Write-Host "监控已停止或发生错误: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "监控结束" -ForegroundColor Green