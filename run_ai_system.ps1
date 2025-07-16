# AI Agent System + LLM Chat Integration Script (English Version)

# Environment setup
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host ""
Write-Host "[START] === AI Agent System + LLM Chat Integration === [START]" -ForegroundColor Green
Write-Host ""

# --- Virtual Environment Setup ---
$pythonExec = Join-Path $PWD ".venv/Scripts/python.exe"
if (-not (Test-Path $pythonExec)) {
    Write-Host "[VENV] Python virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[VENV] Virtual environment created. Please re-run the script." -ForegroundColor Green
    exit
}
Write-Host "[VENV] Using Python from: $pythonExec" -ForegroundColor Cyan
# ---

# Environment Variables Setup Function
function Set-EnvironmentVariables {
    Write-Host "[CONFIG] Setting up Environment Variables..." -ForegroundColor Yellow
    
    # Check and set API keys
    $envVars = @{
        "OPENAI_API_KEY" = "OpenAI API Key"
        "ANTHROPIC_API_KEY" = "Anthropic API Key" 
        "GEMINI_API_KEY" = "Google Gemini API Key"
        "HUGGINGFACE_TOKEN" = "HuggingFace Token"
    }
    
    foreach ($envVar in $envVars.Keys) {
        $currentValue = [Environment]::GetEnvironmentVariable($envVar)
        if (-not $currentValue) {
            Write-Host "   [WARN] $($envVars[$envVar]) not found" -ForegroundColor Yellow
            
            # Try to set default/demo values for development
            switch ($envVar) {
                "OPENAI_API_KEY" { 
                    [Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-demo-key-for-development", "Process")
                    Write-Host "   [SET] Set demo OpenAI key for development" -ForegroundColor Cyan
                }
                "ANTHROPIC_API_KEY" { 
                    [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-demo-key-for-development", "Process")
                    Write-Host "   [SET] Set demo Anthropic key for development" -ForegroundColor Cyan
                }
                "GEMINI_API_KEY" { 
                    [Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "demo-gemini-key-for-development", "Process")
                    Write-Host "   [SET] Set demo Gemini key for development" -ForegroundColor Cyan
                }
                "HUGGINGFACE_TOKEN" { 
                    [Environment]::SetEnvironmentVariable("HUGGINGFACE_TOKEN", "hf_demo_token_for_development", "Process")
                    Write-Host "   [SET] Set demo HuggingFace token for development" -ForegroundColor Cyan
                }
            }
        } else {
            $maskedKey = $currentValue.Substring(0, [Math]::Min(8, $currentValue.Length)) + "..."
            Write-Host "   [OK] $($envVars[$envVar]): $maskedKey" -ForegroundColor Green
        }
    }
    
    # Set additional environment variables
    $env:PYTHONPATH = "$PWD;$PWD\src;$PWD\code_nation\argonaute\src"
    $env:FLASK_ENV = "development"
    $env:FASTAPI_ENV = "development" 
    
    Write-Host "   [OK] Python path configured" -ForegroundColor Green
    Write-Host "   [OK] Development environment set" -ForegroundColor Green
    Write-Host ""
}

# Function to create environment file
function New-EnvironmentFile {
    Write-Host "[FILE] Creating .env file for persistent storage..." -ForegroundColor Cyan
    
    $envContent = @"
# AI Agent System Environment Variables
# Generated on $(Get-Date)

# API Keys (Replace with your actual keys)
OPENAI_API_KEY=sk-demo-key-for-development
ANTHROPIC_API_KEY=sk-ant-demo-key-for-development
GEMINI_API_KEY=demo-gemini-key-for-development
HUGGINGFACE_TOKEN=hf_demo_token_for_development

# Development Settings
FLASK_ENV=development
FASTAPI_ENV=development
PYTHONIOENCODING=utf-8

# Server Configuration
DEFAULT_PORT=8000
DEBUG_MODE=true

# Instructions:
# 1. Replace demo keys with your actual API keys
# 2. Restart the script after updating keys
# 3. Keep this file secure and don't commit to version control
"@

    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "   [OK] .env file created successfully" -ForegroundColor Green
    Write-Host "   [INFO] Edit .env file to add your actual API keys" -ForegroundColor Yellow
    Write-Host ""
}

# Function to load environment from .env file
function Import-EnvironmentFile {
    if (Test-Path ".env") {
        Write-Host "[LOAD] Loading environment from .env file..." -ForegroundColor Cyan
        
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Only set if not already set
                if (-not (Get-Item "env:$name" -ErrorAction SilentlyContinue)) {
                    Set-Item -Path "env:$name" -Value $value
                    Write-Host "   [OK] Loaded: $name" -ForegroundColor Green
                }
            }
        }
        Write-Host ""
    } else {
        Write-Host "[INFO] .env file not found, creating one..." -ForegroundColor Yellow
        New-EnvironmentFile
    }
}

# Initialize environment
Import-EnvironmentFile
Set-EnvironmentVariables

# Port configuration
$heroicSimplePort = 8001      # Changed from 8005 to 8001
$deianeiraSimplePort = 8002   # Changed from 8006 to 8002
$heroicFullPort = 8007
$deianeiraFullPort = 8008
$simpleChatPort = 8011

Write-Host "[PORTS] Port Configuration Complete:" -ForegroundColor Yellow
Write-Host "   [HERO] HeroicAge Simple: $heroicSimplePort" -ForegroundColor Cyan
Write-Host "   [DEIA] Deianeira Simple: $deianeiraSimplePort" -ForegroundColor Cyan  
Write-Host "   [HERO+] HeroicAge Full+MCP: $heroicFullPort" -ForegroundColor Green
Write-Host "   [DEIA+] Deianeira Full+MCP: $deianeiraFullPort" -ForegroundColor Green
Write-Host "   [CHAT] Simple AI Chat: $simpleChatPort" -ForegroundColor Magenta
Write-Host ""

# Function to check Python dependencies
function Test-PythonDependencies {
    param($pythonExec)
    Write-Host "[DEPS] Checking Python Dependencies..." -ForegroundColor Cyan
    
    $requiredPackages = @("fastapi", "uvicorn", "aiohttp", "python-dotenv")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        try {
            $result = & $pythonExec -c "import $package; print('OK')" 2>$null
            if ($result -eq "OK") {
                Write-Host "   [OK] $package" -ForegroundColor Green
            } else {
                Write-Host "   [MISS] $package (missing)" -ForegroundColor Red
                $missingPackages += $package
            }
        } catch {
            Write-Host "   [ERR] $package (error)" -ForegroundColor Red
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "   [INSTALL] Installing missing packages..." -ForegroundColor Yellow
        try {
            & $pythonExec -m pip install $missingPackages -q
            Write-Host "   [OK] Package installation completed" -ForegroundColor Green
        } catch {
            Write-Host "   [ERR] Package installation failed" -ForegroundColor Red
            Write-Host "   [TIP] Try: & $pythonExec -m pip install fastapi uvicorn aiohttp python-dotenv" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Check dependencies
Test-PythonDependencies -pythonExec $pythonExec

# 1. Start Simple AI Chat Server (Fixed syntax)
Write-Host "[START] Starting Simple AI Chat Server..." -ForegroundColor Magenta
$chatJob = Start-Job -ScriptBlock {
    param($WorkDir, $Port, $pythonExec)
    Set-Location $WorkDir
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = $Port
    
    # Copy environment variables to job
    $env:OPENAI_API_KEY = $using:env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY = $using:env:ANTHROPIC_API_KEY
    $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
    $env:HUGGINGFACE_TOKEN = $using:env:HUGGINGFACE_TOKEN
    
    & $pythonExec simple_chat.py
} -ArgumentList @($PWD.Path, $simpleChatPort, $pythonExec)

Start-Sleep -Seconds 3

# 2. Start HeroicAge Simple (Fixed syntax)
Write-Host "[START] Starting HeroicAge Simple Agent..." -ForegroundColor Blue
$heroicSimpleJob = Start-Job -ScriptBlock {
    param($WorkDir, $Port, $pythonExec)
    Set-Location $WorkDir
    Set-Location HeroicAge
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = $Port
    
    # Copy environment variables to job
    $env:OPENAI_API_KEY = $using:env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY = $using:env:ANTHROPIC_API_KEY
    $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
    $env:HUGGINGFACE_TOKEN = $using:env:HUGGINGFACE_TOKEN
    
    & $pythonExec main_simple.py
} -ArgumentList @($PWD.Path, $heroicSimplePort, $pythonExec)

Start-Sleep -Seconds 2

# 3. Start Deianeira Simple (Fixed syntax)
Write-Host "[START] Starting Deianeira Simple System..." -ForegroundColor Red
$deianeiraSimpleJob = Start-Job -ScriptBlock {
    param($WorkDir, $Port, $pythonExec)
    Set-Location $WorkDir
    Set-Location GeminiAnalysis
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = $Port
    
    # Copy environment variables to job
    $env:OPENAI_API_KEY = $using:env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY = $using:env:ANTHROPIC_API_KEY
    $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
    $env:HUGGINGFACE_TOKEN = $using:env:HUGGINGFACE_TOKEN
    
    & $pythonExec main_simple.py
} -ArgumentList @($PWD.Path, $deianeiraSimplePort, $pythonExec)

Start-Sleep -Seconds 2

# 4. Start HeroicAge Full (with MCP) (Fixed syntax)
Write-Host "[START] Starting HeroicAge Full Agent (with MCP)..." -ForegroundColor Green
$heroicFullJob = Start-Job -ScriptBlock {
    param($WorkDir, $Port, $pythonExec)
    Set-Location $WorkDir
    Set-Location HeroicAge
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = $Port
    
    # Copy environment variables to job
    $env:OPENAI_API_KEY = $using:env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY = $using:env:ANTHROPIC_API_KEY
    $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
    $env:HUGGINGFACE_TOKEN = $using:env:HUGGINGFACE_TOKEN
    
    & $pythonExec main.py
} -ArgumentList @($PWD.Path, $heroicFullPort, $pythonExec)

Start-Sleep -Seconds 3

# 5. Start Deianeira Full (with MCP) (Fixed syntax)
Write-Host "[START] Starting Deianeira Full System (with MCP)..." -ForegroundColor DarkGreen
$deianeiraFullJob = Start-Job -ScriptBlock {
    param($WorkDir, $Port, $pythonExec)
    Set-Location $WorkDir
    Set-Location GeminiAnalysis
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = $Port
    
    # Copy environment variables to job
    $env:OPENAI_API_KEY = $using:env:OPENAI_API_KEY
    $env:ANTHROPIC_API_KEY = $using:env:ANTHROPIC_API_KEY
    $env:GEMINI_API_KEY = $using:env:GEMINI_API_KEY
    $env:HUGGINGFACE_TOKEN = $using:env:HUGGINGFACE_TOKEN
    
    & $pythonExec main.py
} -ArgumentList @($PWD.Path, $deianeiraFullPort, $pythonExec)

Write-Host ""
Write-Host "[WAIT] Starting all services... (30 seconds wait)" -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "[CHECK] === Service Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Status check function
function Test-Service {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Icon
    )
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 5
        Write-Host "$Icon $Name`: [OK] Running normally ($Url)" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "$Icon $Name`: [FAIL] Connection failed ($Url)" -ForegroundColor Red
        return $false
    }
}

# Check each service status
$services = @(
    @{ Name = "Simple AI Chat"; Url = "http://localhost:$simpleChatPort/health"; Icon = "[CHAT]" };
    @{ Name = "HeroicAge Simple"; Url = "http://localhost:$heroicSimplePort/health"; Icon = "[HERO]" };
    @{ Name = "Deianeira Simple"; Url = "http://localhost:$deianeiraSimplePort/health"; Icon = "[DEIA]" };
    @{ Name = "HeroicAge Full MCP"; Url = "http://localhost:$heroicFullPort/health"; Icon = "[HERO+]" };
    @{ Name = "Deianeira Full MCP"; Url = "http://localhost:$deianeiraFullPort/health"; Icon = "[DEIA+]" }
)

$activeServices = 0
foreach ($service in $services) {
    if (Test-Service -Name $service.Name -Url $service.Url -Icon $service.Icon) {
        $activeServices++
    }
}

Write-Host ""
Write-Host "[SUMMARY] === Service Summary ===" -ForegroundColor Yellow
Write-Host "   Active Services: $activeServices/5" -ForegroundColor Cyan
Write-Host ""

# Access URL guide
Write-Host "[URLS] === Access URLs ===" -ForegroundColor Green
Write-Host ""
Write-Host "[CHAT] Chat Interface:" -ForegroundColor Magenta
Write-Host "   [CHAT] Simple AI Chat: http://localhost:$simpleChatPort/chat/interface" -ForegroundColor White

Write-Host ""
Write-Host "[DOCS] API Documentation:" -ForegroundColor Blue  
Write-Host "   [HERO] HeroicAge Simple: http://localhost:$heroicSimplePort/docs" -ForegroundColor White
Write-Host "   [DEIA] Deianeira Simple: http://localhost:$deianeiraSimplePort/docs" -ForegroundColor White
Write-Host "   [HERO+] HeroicAge Full: http://localhost:$heroicFullPort/docs" -ForegroundColor White
Write-Host "   [DEIA+] Deianeira Full: http://localhost:$deianeiraFullPort/docs" -ForegroundColor White

Write-Host ""
Write-Host "[TEST] === Chat Test ===" -ForegroundColor Yellow

# Simple chat test
try {
    Write-Host "[TEST] Testing Simple AI Chat..." -ForegroundColor Cyan
    $chatTest = Invoke-RestMethod -Uri "http://localhost:$simpleChatPort/chat" -Method POST -Body "message=Hello! This is a test." -ContentType "application/x-www-form-urlencoded"
    
    if ($chatTest.success) {
        Write-Host "   [OK] Chat Response: $($chatTest.response)" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Chat Failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERR] Chat Test Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "[READY] === System Ready! ===" -ForegroundColor Green
Write-Host ""
Write-Host "[INFO] Usage Instructions:" -ForegroundColor Yellow
Write-Host "   1. Access http://localhost:$simpleChatPort/chat/interface in web browser" -ForegroundColor White
Write-Host "   2. Start chatting with AI" -ForegroundColor White
Write-Host "   3. Check advanced features in API documentation" -ForegroundColor White
Write-Host "   4. Edit .env file to add real API keys for full functionality" -ForegroundColor White
Write-Host ""
Write-Host "[STOP] Stop System: Get-Job | Stop-Job | Remove-Job" -ForegroundColor Gray
Write-Host ""

# Display running jobs
$runningJobs = Get-Job | Where-Object { $_.State -eq "Running" }
Write-Host "[JOBS] Running Services: $($runningJobs.Count) services" -ForegroundColor Cyan
foreach ($job in $runningJobs) {
    Write-Host "   - Job ID: $($job.Id) | Name: $($job.Name)" -ForegroundColor White
}

# Environment summary
Write-Host ""
Write-Host "[ENV] === Environment Summary ===" -ForegroundColor Yellow
Write-Host "   [FILE] .env file: $(if (Test-Path '.env') { 'Created' } else { 'Missing' })" -ForegroundColor $(if (Test-Path '.env') { 'Green' } else { 'Red' })
Write-Host "   [KEYS] API Keys: Set (using demo keys - replace with real ones)" -ForegroundColor Yellow
Write-Host "   [PATH] Python Path: Configured" -ForegroundColor Green

# Auto-open chat page in browser
try {
    Write-Host ""
    Write-Host "[BROWSER] Opening chat page in browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:$simpleChatPort/chat/interface"
} catch {
    Write-Host "   Cannot open browser automatically. Please access manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")