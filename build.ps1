# LOL国际服聊天框翻译 (LoL International Server Chat Translator) - 打包脚本
# 用法：.venv\Scripts\python.exe -m PyInstaller 或直接运行本脚本
# PowerShell: powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "== 清理旧构建 ==" -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Host "== 构建 onedir 版本 ==" -ForegroundColor Cyan
& ".venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --name "LoLChatTranslator" `
    --paths "src" `
    --icon "src/lolchattranslator/resources/icons/app_icon.ico" `
    --add-data "config/default_config.json;config" `
    --add-data "src/lolchattranslator/resources;resources" `
    --hidden-import "keyboard" `
    --hidden-import "pystray._win32" `
    --windowed `
    main.py

Write-Host "== onedir 构建完成 ==" -ForegroundColor Green

Write-Host "== 构建 onefile 版本 ==" -ForegroundColor Cyan
& ".venv\Scripts\python.exe" -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name "LoLChatTranslator-onefile" `
    --paths "src" `
    --icon "src/lolchattranslator/resources/icons/app_icon.ico" `
    --add-data "config/default_config.json;config" `
    --add-data "src/lolchattranslator/resources;resources" `
    --hidden-import "keyboard" `
    --hidden-import "pystray._win32" `
    --windowed `
    main.py

Write-Host "== 全部构建完成 ==" -ForegroundColor Green
Write-Host "产物位置："
Write-Host "  onedir : dist/LoLChatTranslator/LoLChatTranslator.exe"
Write-Host "  onefile: dist/LoLChatTranslator-onefile.exe"
