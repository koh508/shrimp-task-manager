# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
from pathlib import Path
import time
from datetime import datetime

class GitKrakenAutomator:
    def __init__(self, source_drive="D:\\", target_repo="D:\\my workspace\\OneDrive NEW\\GNY"):
        self.source_drive = source_drive
        self.target_repo = target_repo
        self.python_files = []
        
    def find_python_files(self, extensions=['.py', '.pyw', '.ipynb']):
        """D:\ 드라이브에서 파이썬 파일 검색"""
        print(f"🔍 {self.source_drive}에서 파이썬 파일 검색 중...")
        
        for root, dirs, files in os.walk(self.source_drive):
            # 시스템 폴더 제외
            dirs[:] = [d for d in dirs if not d.startswith(('.', '$', 'System', 'Windows', 'ProgramData'))]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 0:
                            self.python_files.append({
                                'path': file_path,
                                'name': file,
                                'size': file_size,
                                'relative_path': os.path.relpath(file_path, self.source_drive)
                            })
                    except (OSError, PermissionError):
                        continue
        
        print(f"✅ 총 {len(self.python_files)}개의 파이썬 파일 발견")
        return self.python_files
    
    def copy_files_to_repo(self, batch_size=30):
        """파일들을 Git 저장소로 복사"""
        target_python_dir = os.path.join(self.target_repo, "Python_Files")
        os.makedirs(target_python_dir, exist_ok=True)
        
        if not self.python_files:
            print("❌ 복사할 파일이 없습니다.")
            return
            
        batches = [self.python_files[i:i + batch_size] for i in range(0, len(self.python_files), batch_size)]
        print(f"📦 {len(batches)}개 배치로 처리합니다")
        
        for batch_num, batch in enumerate(batches, 1):
            print(f"\n🔄 배치 {batch_num}/{len(batches)} 처리 중...")
            
            copied_count = 0
            for file_info in batch:
                source_path = file_info['path']
                relative_dir = os.path.dirname(file_info['relative_path'])
                
                # 경로 길이 제한
                if len(relative_dir) > 100:
                    relative_dir = relative_dir[:100] + "..."
                
                target_dir = os.path.join(target_python_dir, relative_dir)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file_info['name'])
                
                try:
                    shutil.copy2(source_path, target_path)
                    print(f"  ✅ {file_info['name']} ({file_info['size']/1024:.1f}KB)")
                    copied_count += 1
                except Exception as e:
                    print(f"  ❌ {file_info['name']} - {str(e)[:50]}...")
            
            if copied_count > 0:
                self.process_batch_with_gitkraken(batch_num, len(batches))
    
    def process_batch_with_gitkraken(self, batch_num, total_batches):
        """GitKraken CLI로 배치 처리"""
        work_item_name = f"python-batch-{batch_num}"
        
        try:
            os.chdir(self.target_repo)
            print(f"  🔧 GitKraken 처리 중...")
            
            # GitKraken Work 시작
            subprocess.run(["gk", "work", "start", work_item_name], check=True, capture_output=True, text=True)
            subprocess.run(["gk", "work", "add"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            
            commit_message = f"D:\\ 파이썬 파일 배치 {batch_num}/{total_batches} 자동 추가"
            subprocess.run(["gk", "work", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
            subprocess.run(["gk", "work", "push"], check=True, capture_output=True, text=True)
            subprocess.run(["gk", "work", "end"], input="y\n", text=True, capture_output=True)
            
            print(f"  🎉 GitKraken 처리 완료!")
            time.sleep(1)
            
        except subprocess.CalledProcessError:
            print(f"  ⚠️ GitKraken 오류 - 수동 Git 사용")
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", f"배치 {batch_num} 자동 추가"], check=True)
                subprocess.run(["git", "push"], check=True)
                print(f"  ✅ 수동 Git 처리 완료")
            except:
                print(f"  ❌ Git 처리 실패")
        except Exception as e:
            print(f"  ❌ 예상치 못한 오류: {str(e)[:50]}...")

    def generate_report(self):
        """보고서 생성"""
        if not self.python_files:
            return
        
        self.python_files.sort(key=lambda x: x['size'], reverse=True)
        report_path = os.path.join(self.target_repo, "Python_Files_Report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🐍 D:\\ 파이썬 파일 수집 보고서\n\n")
            f.write(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**총 파일 수**: {len(self.python_files)}개\n")
            f.write(f"**총 용량**: {sum(f['size'] for f in self.python_files) / 1024 / 1024:.2f} MB\n\n")
            
            # 확장자별 통계
            f.write("## 📊 파일 유형별 통계\n\n")
            extensions = {}
            for file_info in self.python_files:
                ext = os.path.splitext(file_info['name'])[1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1
            
            for ext, count in sorted(extensions.items()):
                f.write(f"- **{ext}**: {count}개\n")
            
            # 대용량 파일 목록
            f.write("\n## 📁 상위 10개 대용량 파일\n\n")
            f.write("| 순위 | 파일명 | 크기 | 경로 |\n")
            f.write("|------|--------|------|------|\n")
            
            for i, file_info in enumerate(self.python_files[:10], 1):
                size_mb = file_info['size'] / 1024 / 1024
                path = file_info['relative_path'][:50] + "..." if len(file_info['relative_path']) > 50 else file_info['relative_path']
                f.write(f"| {i} | {file_info['name']} | {size_mb:.2f} MB | {path} |\n")
        
        print(f"📄 보고서 생성: {report_path}")

def main():
    print("🐍 GitKraken 파이썬 파일 자동 수집기")
    print("=" * 50)
    
    automator = GitKrakenAutomator()
    
    # 파일 검색
    python_files = automator.find_python_files()
    
    if not python_files:
        print("❌ 파이썬 파일을 찾을 수 없습니다.")
        return
    
    # 정보 표시
    total_size_mb = sum(f['size'] for f in python_files) / 1024 / 1024
    print(f"\n📊 발견된 파일:")
    print(f"   - 파일 수: {len(python_files)}개")
    print(f"   - 총 용량: {total_size_mb:.2f} MB")
    
    # 사용자 확인
    confirm = input("\n계속 진행하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ 작업이 취소되었습니다.")
        return
    
    # 파일 처리
    automator.copy_files_to_repo()
    automator.generate_report()
    
    print("\n🎉 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()
