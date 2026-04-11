"""스킬: dev_docker — Dockerfile 생성기 + 모범사례 검증"""

def generate_dockerfile(
    base_image: str = "python:3.12-slim",
    app_user: str = "appuser",
    port: int = 8000,
    requirements_file: str = "requirements.txt",
    entrypoint: str = "main.py",
    healthcheck_path: str = "/health",
) -> str:
    return f"""FROM {base_image}

# 비루트 사용자 생성 (보안)
RUN useradd -m {app_user}

# 의존성 먼저 복사 (레이어 캐시 최적화)
WORKDIR /app
COPY {requirements_file} .
RUN pip install --no-cache-dir -r {requirements_file}

# 소스코드 복사
COPY --chown={app_user}:{app_user} . .
USER {app_user}

EXPOSE {port}

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
    CMD curl -f http://localhost:{port}{healthcheck_path} || exit 1

CMD ["python", "{entrypoint}"]
"""

def generate_dockerignore() -> str:
    return "\n".join([
        "__pycache__/", "*.pyc", "*.pyo",
        ".env", "*.db", "*.sqlite",
        ".git", ".gitignore",
        "tests/", "*.md",
    ])

def validate_dockerfile(content: str) -> list[str]:
    """Dockerfile 모범사례 준수 여부 체크"""
    warnings = []
    if "FROM" not in content:
        warnings.append("[CRITICAL] FROM 명령 없음")
    if "useradd" not in content and "USER" not in content:
        warnings.append("[WARN] 비루트 사용자 설정 없음 (보안 취약)")
    if "HEALTHCHECK" not in content:
        warnings.append("[WARN] HEALTHCHECK 없음")
    if "no-cache" not in content and "pip install" in content:
        warnings.append("[NIT] pip install에 --no-cache-dir 없음 (이미지 크기 증가)")
    if "COPY requirements" not in content and "COPY req" not in content:
        warnings.append("[NIT] 의존성 레이어 분리 없음 (캐시 비효율)")
    return warnings

# ── 검증 ─────────────────────────────────────────────────────────────────────
dockerfile = generate_dockerfile(port=8080, entrypoint="app.py")
warnings = validate_dockerfile(dockerfile)

assert "FROM python:3.12-slim" in dockerfile
assert "useradd" in dockerfile
assert "HEALTHCHECK" in dockerfile
assert "--no-cache-dir" in dockerfile
print(f"  [1] Dockerfile 생성 완료 ({len(dockerfile.splitlines())}줄)")
print(f"  [2] 모범사례 경고: {warnings if warnings else '없음'}")
assert len(warnings) == 0, f"경고 발생: {warnings}"

# 의도적으로 나쁜 Dockerfile 검증
bad_dockerfile = "FROM ubuntu:latest\nRUN pip install flask\nCMD python app.py"
bad_warnings = validate_dockerfile(bad_dockerfile)
assert len(bad_warnings) >= 2, f"나쁜 Dockerfile 경고 부족: {bad_warnings}"
print(f"  [3] 나쁜 Dockerfile 경고 {len(bad_warnings)}개 탐지: {[w.split(']')[0]+']' for w in bad_warnings]}")

dockerignore = generate_dockerignore()
assert ".env" in dockerignore
assert "__pycache__/" in dockerignore
print(f"  [4] .dockerignore 생성 ({len(dockerignore.splitlines())}줄)")

print("PASS")
