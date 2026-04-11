"""
onew_shared/config.py
기기 환경 자동 감지 — PC vs 태블릿 공통 설정
"""
import os
import platform
from pathlib import Path


def is_termux() -> bool:
    """Termux(Android) 환경인지 확인."""
    return os.path.exists("/data/data/com.termux")


def is_pc() -> bool:
    """Windows PC 환경인지 확인."""
    return platform.system() == "Windows"


def get_device_name() -> str:
    """현재 기기 이름 반환."""
    return "tablet" if is_termux() else "pc"


def get_vault_path() -> Path:
    """Obsidian Vault 경로 반환 (기기별 자동 감지)."""
    if is_termux():
        candidates = [
            Path("/data/data/com.termux/files/home/storage/shared/Documents/Obsidian Vault"),
            Path("/data/data/com.termux/files/home/storage/shared/Obsidian Vault"),
            Path("/data/data/com.termux/files/home/storage/shared/Ams_vault"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return Path.home() / "storage/shared/Documents/Obsidian Vault"
    else:
        return Path(r"C:\Users\User\Documents\Obsidian Vault")


def get_system_path() -> Path:
    """SYSTEM 폴더 경로."""
    return get_vault_path() / "SYSTEM"


def get_ollama_url() -> str:
    """Ollama API URL (환경변수 우선)."""
    return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_model() -> str:
    """사용할 Ollama 모델 (환경변수 우선)."""
    return os.environ.get("OLLAMA_MODEL", "gemma4:e4b")


def get_gemini_api_key() -> str:
    """Gemini API 키."""
    return os.environ.get("GEMINI_API_KEY", "")


def summary() -> dict:
    """현재 환경 요약."""
    return {
        "device": get_device_name(),
        "vault": str(get_vault_path()),
        "ollama_url": get_ollama_url(),
        "ollama_model": get_ollama_model(),
        "gemini_key_set": bool(get_gemini_api_key()),
    }
