#!/usr/bin/env python3
"""
클라우드 저장 및 메모리 관리 모니터
자기진화 AI 시스템의 저장공간과 메모리 사용량을 실시간 모니터링
"""

import os
import json
import sqlite3
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import glob

class CloudMemoryMonitor:
    def __init__(self):
        self.db_path = "d:/cloud_memory_monitor.db"
        self.workspace_path = "d:/"
        self.setup_database()
    
    def setup_database(self):
        """모니터링 데이터베이스 설정"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                memory_percent REAL,
                disk_used_gb REAL,
                disk_free_gb REAL,
                file_count INTEGER,
                largest_files TEXT,
                cloud_uploads INTEGER,
                compressed_files INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cloud_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action TEXT,
                file_path TEXT,
                file_size_mb REAL,
                service TEXT,
                status TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_system_stats(self):
        """시스템 통계 수집"""
        # 메모리 사용률
        memory = psutil.virtual_memory()
        
        # 디스크 사용률
        disk = psutil.disk_usage(self.workspace_path)
        
        # 파일 개수
        files = list(Path(self.workspace_path).glob("**/*"))
        file_count = len([f for f in files if f.is_file()])
        
        # 큰 파일들 찾기
        large_files = []
        for file_path in files:
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # 10MB 이상
                    large_files.append({
                        'path': str(file_path),
                        'size_mb': round(size_mb, 2)
                    })
        
        large_files.sort(key=lambda x: x['size_mb'], reverse=True)
        
        return {
            'memory_percent': memory.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'file_count': file_count,
            'largest_files': large_files[:10]  # 상위 10개
        }
    
    def count_cloud_activity(self):
        """클라우드 활동 통계"""
        # 압축 파일 개수
        zip_files = len(glob.glob(f"{self.workspace_path}/*.zip"))
        
        # 클라우드 업로드 로그 확인
        cloud_uploads = 0
        cloud_log_path = f"{self.workspace_path}/cloud_upload_log.json"
        if os.path.exists(cloud_log_path):
            try:
                with open(cloud_log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    cloud_uploads = len(logs)
            except:
                pass
        
        return {
            'cloud_uploads': cloud_uploads,
            'compressed_files': zip_files
        }
    
    def save_stats(self, stats, cloud_stats):
        """통계 데이터베이스에 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO memory_stats 
            (timestamp, memory_percent, disk_used_gb, disk_free_gb, file_count, 
             largest_files, cloud_uploads, compressed_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            stats['memory_percent'],
            stats['disk_used_gb'],
            stats['disk_free_gb'],
            stats['file_count'],
            json.dumps(stats['largest_files']),
            cloud_stats['cloud_uploads'],
            cloud_stats['compressed_files']
        ))
        
        conn.commit()
        conn.close()
    
    def get_memory_trend(self, hours=24):
        """메모리 사용 트렌드 분석"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT timestamp, memory_percent, disk_used_gb, file_count
            FROM memory_stats 
            WHERE timestamp > ?
            ORDER BY timestamp
        ''', (since.isoformat(),))
        
        data = cursor.fetchall()
        conn.close()
        
        if not data:
            return None
        
        return {
            'start_memory': data[0][1],
            'current_memory': data[-1][1],
            'memory_change': data[-1][1] - data[0][1],
            'start_disk': data[0][2],
            'current_disk': data[-1][2],
            'disk_growth': data[-1][2] - data[0][2],
            'start_files': data[0][3],
            'current_files': data[-1][3],
            'files_created': data[-1][3] - data[0][3]
        }
    
    def check_cleanup_needed(self):
        """정리 필요 여부 확인"""
        stats = self.get_system_stats()
        
        warnings = []
        
        # 메모리 사용률 80% 이상
        if stats['memory_percent'] > 80:
            warnings.append(f"⚠️ 메모리 사용률 높음: {stats['memory_percent']:.1f}%")
        
        # 디스크 여유공간 5GB 미만
        if stats['disk_free_gb'] < 5:
            warnings.append(f"⚠️ 디스크 여유공간 부족: {stats['disk_free_gb']:.1f}GB")
        
        # 파일 개수 5000개 이상
        if stats['file_count'] > 5000:
            warnings.append(f"⚠️ 파일 개수 과다: {stats['file_count']:,}개")
        
        return warnings
    
    def generate_report(self):
        """실시간 리포트 생성"""
        stats = self.get_system_stats()
        cloud_stats = self.count_cloud_activity()
        trend = self.get_memory_trend()
        warnings = self.check_cleanup_needed()
        
        # 통계 저장
        self.save_stats(stats, cloud_stats)
        
        print("=" * 80)
        print("🖥️  클라우드 저장 & 메모리 관리 모니터")
        print("=" * 80)
        print(f"⏰ 검사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 현재 상태
        print("📊 현재 시스템 상태:")
        print(f"   💾 메모리 사용률: {stats['memory_percent']:.1f}%")
        print(f"   💿 디스크 사용량: {stats['disk_used_gb']:.1f}GB")
        print(f"   📁 디스크 여유공간: {stats['disk_free_gb']:.1f}GB")
        print(f"   📄 총 파일 개수: {stats['file_count']:,}개")
        print()
        
        # 클라우드 활동
        print("☁️  클라우드 저장 활동:")
        print(f"   📤 업로드 횟수: {cloud_stats['cloud_uploads']}회")
        print(f"   🗜️  압축 파일: {cloud_stats['compressed_files']}개")
        print()
        
        # 큰 파일들
        if stats['largest_files']:
            print("📁 용량 큰 파일들 (상위 5개):")
            for i, file_info in enumerate(stats['largest_files'][:5], 1):
                print(f"   {i}. {file_info['size_mb']}MB - {Path(file_info['path']).name}")
            print()
        
        # 트렌드 분석
        if trend:
            print("📈 24시간 변화 추이:")
            print(f"   💾 메모리: {trend['memory_change']:+.1f}%")
            print(f"   💿 디스크: {trend['disk_growth']:+.1f}GB")
            print(f"   📄 파일: {trend['files_created']:+,}개")
            print()
        
        # 경고사항
        if warnings:
            print("⚠️  주의사항:")
            for warning in warnings:
                print(f"   {warning}")
            print()
        
        # 권장사항
        print("💡 권장사항:")
        if stats['memory_percent'] > 70:
            print("   🧹 메모리 정리 권장")
        if stats['disk_free_gb'] < 10:
            print("   ☁️ 클라우드 백업 권장")
        if stats['file_count'] > 3000:
            print("   🗜️ 파일 압축 권장")
        print()
        
        return {
            'stats': stats,
            'cloud_stats': cloud_stats,
            'trend': trend,
            'warnings': warnings
        }
    
    def run_continuous_monitoring(self, interval_minutes=5):
        """지속적 모니터링 실행"""
        print("🎯 클라우드 메모리 모니터 시작")
        print(f"📊 {interval_minutes}분마다 상태 확인")
        print("=" * 80)
        
        while True:
            try:
                self.generate_report()
                
                # 다음 검사까지 대기
                print(f"⏳ {interval_minutes}분 후 다음 검사...")
                print("=" * 80)
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n👋 모니터링 종료")
                break
            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")
                time.sleep(30)

def main():
    """메인 실행 함수"""
    import sys
    
    monitor = CloudMemoryMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor.run_continuous_monitoring(5)  # 5분마다
    else:
        # 단일 리포트
        monitor.generate_report()

if __name__ == "__main__":
    main()
