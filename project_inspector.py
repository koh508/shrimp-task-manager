#!/usr/bin/env python3
"""
Python Project Inspector - 파이썬 프로젝트 통합 분석 도구
"""
import os
import sys
import ast
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
import argparse


@dataclass
class FileInfo:
    """파일 정보 클래스"""

    path: str
    size: int
    lines: int
    functions: int
    classes: int
    imports: List[str]
    complexity: int
    last_modified: str


@dataclass
class ProjectSummary:
    """프로젝트 요약 정보"""

    total_files: int
    total_size: int
    total_lines: int
    total_functions: int
    total_classes: int
    languages: Dict[str, int]
    largest_files: List[Tuple[str, int]]
    most_complex: List[Tuple[str, int]]
    dependency_map: Dict[str, List[str]]


class ProjectInspector:
    """프로젝트 분석기"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.files_info: List[FileInfo] = []
        self.summary: Optional[ProjectSummary] = None

    def analyze_file(self, file_path: Path) -> Optional[FileInfo]:
        """개별 파일 분석"""
        try:
            content = None
            for encoding in ["utf-8", "cp949", "latin-1"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break  # 성공하면 루프 탈출
                except (UnicodeDecodeError, PermissionError):
                    continue

            if content is None:
                print(f"⚠️  파일 읽기 실패 (모든 인코딩 시도 실패): {file_path}")
                return None

            # 기본 정보
            size = file_path.stat().st_size
            lines = len(content.splitlines())
            last_modified = time.ctime(file_path.stat().st_mtime)

            # Python 파일인 경우 AST 분석
            functions = 0
            classes = 0
            imports = []
            complexity = 0

            if file_path.suffix == ".py":
                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions += 1
                            complexity += self._calculate_complexity(node)
                        elif isinstance(node, ast.ClassDef):
                            classes += 1
                        elif isinstance(node, (ast.Import, ast.ImportFrom)):
                            imports.extend(self._extract_imports(node))

                except SyntaxError:
                    pass  # 문법 오류가 있는 파일은 건너뛰기

            return FileInfo(
                path=str(file_path.relative_to(self.project_path)),
                size=size,
                lines=lines,
                functions=functions,
                classes=classes,
                imports=imports,
                complexity=complexity,
                last_modified=last_modified,
            )

        except Exception as e:
            print(f"⚠️  파일 분석 실패: {file_path} - {e}")
            return None

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """순환복잡도 계산 (간단한 버전)"""
        complexity = 1  # 기본 복잡도

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _extract_imports(self, node) -> List[str]:
        """임포트 추출"""
        imports = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)

        return imports

    def scan_project(self, exclude_dirs: List[str] = None) -> None:
        """프로젝트 전체 스캔"""
        if exclude_dirs is None:
            exclude_dirs = [
                ".git",
                "__pycache__",
                ".pytest_cache",
                "venv",
                "env",
                "node_modules",
                ".venv",
            ]

        print(f"🔍 프로젝트 스캔 시작: {self.project_path}")

        for root, dirs, files in os.walk(self.project_path):
            # 제외 디렉토리 필터링
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in [".py", ".txt", ".md", ".json", ".yml", ".yaml"]:
                    file_info = self.analyze_file(file_path)
                    if file_info:
                        self.files_info.append(file_info)

        print(f"✅ 스캔 완료: {len(self.files_info)}개 파일 분석")
        self._generate_summary()

    def _generate_summary(self) -> None:
        """프로젝트 요약 생성"""
        if not self.files_info:
            return

        # 기본 통계
        total_files = len(self.files_info)
        total_size = sum(f.size for f in self.files_info)
        total_lines = sum(f.lines for f in self.files_info)
        total_functions = sum(f.functions for f in self.files_info)
        total_classes = sum(f.classes for f in self.files_info)

        # 언어별 분포
        languages = defaultdict(int)
        for file_info in self.files_info:
            ext = Path(file_info.path).suffix or "no_extension"
            languages[ext] += 1

        # 가장 큰 파일들 (상위 10개)
        largest_files = sorted(
            [(f.path, f.size) for f in self.files_info], key=lambda x: x[1], reverse=True
        )[:10]

        # 가장 복잡한 파일들 (상위 10개)
        most_complex = sorted(
            [(f.path, f.complexity) for f in self.files_info if f.complexity > 0],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # 의존성 맵
        dependency_map = {}
        for file_info in self.files_info:
            if file_info.imports:
                dependency_map[file_info.path] = file_info.imports

        self.summary = ProjectSummary(
            total_files=total_files,
            total_size=total_size,
            total_lines=total_lines,
            total_functions=total_functions,
            total_classes=total_classes,
            languages=dict(languages),
            largest_files=largest_files,
            most_complex=most_complex,
            dependency_map=dependency_map,
        )

    def generate_report(self) -> str:
        """상세 리포트 생성"""
        if not self.summary:
            return "❌ 프로젝트가 스캔되지 않았습니다."

        report = []

        # 헤더
        report.append("🚀 Python Project Inspector Report")
        report.append("=" * 50)
        report.append(f"📁 프로젝트: {self.project_path.name}")
        report.append(f"📅 분석 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 기본 통계
        report.append("📊 기본 통계")
        report.append("-" * 30)
        report.append(f"📄 총 파일 수: {self.summary.total_files:,}")
        report.append(f"💾 총 용량: {self._format_size(self.summary.total_size)}")
        report.append(f"📝 총 코드 라인: {self.summary.total_lines:,}")
        report.append(f"⚙️  총 함수 수: {self.summary.total_functions:,}")
        report.append(f"🏗️  총 클래스 수: {self.summary.total_classes:,}")
        report.append("")

        # 언어별 분포
        report.append("🌍 파일 형식별 분포")
        report.append("-" * 30)
        for ext, count in sorted(self.summary.languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / self.summary.total_files) * 100
            report.append(f"{ext:>8}: {count:>3}개 ({percentage:5.1f}%)")
        report.append("")

        # 용량이 큰 파일들
        report.append("📈 용량이 큰 파일 (상위 10개)")
        report.append("-" * 30)
        for i, (path, size) in enumerate(self.summary.largest_files, 1):
            report.append(f"{i:2}. {path}")
        report.append("")

        # 복잡도가 높은 파일들
        if self.summary.most_complex:
            report.append("🧠 복잡도가 높은 파일 (상위 10개)")
            report.append("-" * 30)
            for i, (path, complexity) in enumerate(self.summary.most_complex, 1):
                report.append(f"{i:2}. {path}")
            report.append("")

        # 최적화 제안
        report.append("💡 최적화 제안")
        report.append("-" * 30)
        report.extend(self._generate_optimization_suggestions())

        return "\n".join(report)

    def _format_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes == 0:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _generate_optimization_suggestions(self) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []

        # 큰 파일 체크
        large_files = [f for f in self.files_info if f.size > 1024 * 100]  # 100KB 이상
        if large_files:
            suggestions.append(f"📄 큰 파일 {len(large_files)}개 발견 - 리팩토링 고려")

        # 복잡한 함수 체크
        complex_files = [f for f in self.files_info if f.complexity > 10]
        if complex_files:
            suggestions.append(f"🧠 복잡한 파일 {len(complex_files)}개 발견 - 함수 분리 고려")

        # 중복 임포트 체크
        all_imports = []
        for file_info in self.files_info:
            all_imports.extend(file_info.imports)

        import_counts = defaultdict(int)
        for imp in all_imports:
            import_counts[imp] += 1

        frequently_used = [imp for imp, count in import_counts.items() if count > 5]
        if frequently_used:
            suggestions.append(f"🔗 자주 사용되는 모듈 {len(frequently_used)}개 - 공통 모듈화 고려")

        if not suggestions:
            suggestions.append("✅ 특별한 최적화가 필요하지 않습니다.")

        return suggestions

    def generate_navigation_map(self) -> Dict[str, Any]:
        """프로젝트 네비게이션 맵 생성"""
        nav_map = {
            "structure": self._build_directory_tree(),
            "quick_access": self._identify_important_files(),
            "search_index": self._build_search_index(),
        }
        return nav_map

    def _build_directory_tree(self) -> Dict[str, Any]:
        """디렉토리 트리 구조 생성"""
        tree = {}

        for file_info in self.files_info:
            parts = Path(file_info.path).parts
            current = tree

            for part in parts[:-1]:  # 디렉토리 부분
                if part not in current:
                    current[part] = {}
                current = current[part]

            # 파일 추가
            filename = parts[-1]
            current[filename] = {
                "type": "file",
                "size": file_info.size,
                "lines": file_info.lines,
                "functions": file_info.functions,
                "classes": file_info.classes,
            }

        return tree

    def _identify_important_files(self) -> Dict[str, List[str]]:
        """중요한 파일들 식별"""
        important = {"entry_points": [], "large_modules": [], "config_files": [], "test_files": []}

        for file_info in self.files_info:
            path = file_info.path

            # 엔트리 포인트 (main.py, __main__.py, app.py 등)
            if any(
                name in path.lower() for name in ["main.py", "__main__.py", "app.py", "run.py"]
            ):
                important["entry_points"].append(path)

            # 큰 모듈들
            if file_info.size > 10240:  # 10KB 이상
                important["large_modules"].append(path)

            # 설정 파일들
            if any(ext in path.lower() for ext in [".json", ".yml", ".yaml", ".ini", ".cfg"]):
                important["config_files"].append(path)

            # 테스트 파일들
            if "test" in path.lower() or path.startswith("tests/"):
                important["test_files"].append(path)

        return important

    def _build_search_index(self) -> Dict[str, List[str]]:
        """검색 인덱스 구축"""
        index = defaultdict(list)

        for file_info in self.files_info:
            # 파일명으로 인덱싱
            filename = Path(file_info.path).name
            index[filename.lower()].append(file_info.path)

            # 임포트로 인덱싱
            for imp in file_info.imports:
                index[imp.lower()].append(file_info.path)

        return dict(index)

    def export_results(self, output_file: str = "project_analysis.json") -> None:
        """분석 결과 내보내기"""
        data = {
            "summary": asdict(self.summary) if self.summary else None,
            "files": [asdict(f) for f in self.files_info],
            "navigation": self.generate_navigation_map(),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"📄 분석 결과 저장: {output_file}")


class InteractiveNavigator:
    """대화형 프로젝트 네비게이터"""

    def __init__(self, inspector: ProjectInspector):
        self.inspector = inspector
        self.nav_map = inspector.generate_navigation_map()

    def start(self):
        """대화형 네비게이션 시작"""
        print("\n🧭 대화형 프로젝트 네비게이터")
        print("=" * 40)
        print("명령어:")
        print("  tree - 프로젝트 구조 보기")
        print("  find <검색어> - 파일/모듈 검색")
        print("  goto <파일경로> - 파일 정보 보기")
        print("  large - 큰 파일들 보기")
        print("  complex - 복잡한 파일들 보기")
        print("  deps <파일경로> - 의존성 보기")
        print("  help - 도움말")
        print("  exit - 종료")
        print()

        while True:
            try:
                command = input("📍 > ").strip().split()
                if not command:
                    continue

                cmd = command[0].lower()

                if cmd == "exit":
                    break
                elif cmd == "tree":
                    self._show_tree()
                elif cmd.startswith("find") and len(command) > 1:
                    self._find_file(command[1])
                elif cmd.startswith("goto") and len(command) > 1:
                    self._goto_file(" ".join(command[1:]))
                elif cmd == "large":
                    self._show_large_files()
                elif cmd == "complex":
                    self._show_complex_files()
                elif cmd.startswith("deps") and len(command) > 1:
                    self._show_dependencies(" ".join(command[1:]))
                elif cmd == "help":
                    self._show_help()
                else:
                    print("❌ 알 수 없는 명령어. 'help'를 입력하세요.")

            except KeyboardInterrupt:
                print("\n👋 네비게이터 종료")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")

        print("👋 네비게이터 종료")

    def _show_tree(self, tree: Dict = None, prefix: str = "", depth: int = 0):
        """트리 구조 표시"""
        if tree is None:
            tree = self.nav_map["structure"]
            print("📁 프로젝트 구조:")

        if depth > 5:  # 최대 깊이 제한
            print(f"{prefix}└── ... (더 보려면 깊이 조정)")
            return

        items = sorted(tree.items())
        for i, (name, content) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "

            if isinstance(content, dict) and "type" in content:
                # 파일
                size = self.inspector._format_size(content["size"])
                print(f"{prefix}{current_prefix}📄 {name} ({size})")
            else:
                # 디렉토리
                print(f"{prefix}{current_prefix}📁 {name}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                self._show_tree(content, next_prefix, depth + 1)

    def _find_file(self, query: str):
        """파일 검색"""
        results = []
        search_index = self.nav_map["search_index"]

        for key, paths in search_index.items():
            if query.lower() in key:
                results.extend(paths)

        if results:
            print(f"🔍 '{query}' 검색 결과:")
            for i, path in enumerate(sorted(list(set(results))), 1):
                print(f"  {i}. {path}")
        else:
            print(f"❌ '{query}'에 대한 검색 결과가 없습니다.")

    def _goto_file(self, file_path: str):
        """파일 정보 표시"""
        file_info = None
        # 정확한 경로 또는 가장 근접한 경로를 찾습니다.
        for f in self.inspector.files_info:
            if f.path == file_path or file_path in f.path:
                file_info = f
                break

        if file_info:
            print(f"📄 파일 정보: {file_info.path}")
            print(f"   💾 크기: {self.inspector._format_size(file_info.size)}")
            print(f"   📝 라인 수: {file_info.lines:,}")
            print(f"   ⚙️ 함수 수: {file_info.functions}")
            print(f"   🏗️ 클래스 수: {file_info.classes}")
            print(f"   🧠 복잡도: {file_info.complexity}")
            print(f"   📅 수정일: {file_info.last_modified}")
            if file_info.imports:
                print(f"   🔗 임포트: {', '.join(file_info.imports[:5])}")
                if len(file_info.imports) > 5:
                    print(f"        ... 및 {len(file_info.imports) - 5}개 더")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")

    def _show_large_files(self):
        """큰 파일들 표시"""
        if self.inspector.summary and self.inspector.summary.largest_files:
            print("📈 용량이 큰 파일들:")
            for i, (path, size) in enumerate(self.inspector.summary.largest_files, 1):
                print(f"  {i:2}. {path} ({self.inspector._format_size(size)})")

    def _show_complex_files(self):
        """복잡한 파일들 표시"""
        if self.inspector.summary and self.inspector.summary.most_complex:
            print("🧠 복잡도가 높은 파일들:")
            for i, (path, complexity) in enumerate(self.inspector.summary.most_complex, 1):
                print(f"  {i:2}. {path} (복잡도: {complexity})")
        else:
            print("ℹ️ 복잡도 정보가 없습니다.")

    def _show_dependencies(self, file_path: str):
        """의존성 표시"""
        file_info = None
        for f in self.inspector.files_info:
            if f.path == file_path or file_path in f.path:
                file_info = f
                break

        if file_info and file_info.imports:
            print(f"🔗 {file_info.path}의 의존성:")
            for dep in sorted(file_info.imports):
                print(f"  - {dep}")
        else:
            print(f"❌ {file_path}의 의존성 정보가 없거나 파일을 찾을 수 없습니다.")

    def _show_help(self):
        """도움말 표시"""
        print(
            """
🧭 네비게이터 명령어:

  tree                 - 프로젝트 디렉토리 구조 표시
  find <검색어>        - 파일명이나 모듈명으로 검색
  goto <파일경로>      - 특정 파일의 상세 정보 표시
  large                - 용량이 큰 파일들 표시
  complex              - 복잡도가 높은 파일들 표시
  deps <파일경로>      - 파일의 의존성(import) 표시
  help                 - 이 도움말 표시
  exit                 - 네비게이터 종료

💡 팁:
  - 파일 경로는 부분적으로 입력해도 됩니다.
  - 검색은 대소문자를 구분하지 않습니다.
  - Ctrl+C로도 종료할 수 있습니다.
"""
        )


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Python Project Inspector")
    parser.add_argument("path", nargs="?", default=".", help="분석할 프로젝트 경로 (기본: 현재 디렉토리)")
    parser.add_argument("--output", "-o", help="결과를 저장할 JSON 파일명")
    parser.add_argument("--navigate", "-n", action="store_true", help="대화형 네비게이터 실행")
    parser.add_argument("--report-file", help="리포트를 저장할 텍스트 파일명")
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[".git", "__pycache__", ".pytest_cache", "venv", "env", ".venv"],
        help="제외할 디렉토리들",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"❌ 에러: 경로를 찾을 수 없습니다: {args.path}")
        sys.exit(1)

    # 프로젝트 분석
    inspector = ProjectInspector(args.path)
    inspector.scan_project(exclude_dirs=args.exclude)

    # 리포트 생성 및 출력
    report_content = inspector.generate_report()
    print(report_content)

    # 리포트 파일 저장
    if args.report_file:
        try:
            with open(args.report_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\n📄 리포트 저장 완료: {args.report_file}")
        except Exception as e:
            print(f"\n❌ 리포트 파일 저장 실패: {e}")

    # 결과 저장 (JSON)
    if args.output:
        inspector.export_results(args.output)

    # 대화형 네비게이터 실행
    if args.navigate:
        navigator = InteractiveNavigator(inspector)
        navigator.start()


if __name__ == "__main__":
    main()
