# 성능 팁: list comprehension 사용 고려

#!/usr/bin/env python3
"""
🚀 실시간 자기진화 AI 모니터링 대시보드
실시간으로 AI의 진화 과정을 시각화하고 모니터링
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sqlite3
import threading
import time
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class RealTimeEvolutionMonitor:
    """실시간 진화 모니터링 대시보드"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧠 AI 자기진화 실시간 모니터")
        self.root.geometry("1200x800")
        
        # 데이터베이스 연결
        self.db_connection = sqlite3.connect('self_evolution.db', check_same_thread=False)
        
        # 모니터링 상태
        self.monitoring_active = True
        
        # GUI 초기화
        self.setup_gui()
        
        # 실시간 업데이트 스레드 시작
        self.update_thread = threading.Thread(target=self.real_time_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def setup_gui(self):
        """GUI 구성"""
        # 메인 프레임 구성
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단: 현재 상태 표시
        status_frame = ttk.LabelFrame(main_frame, text="🚀 현재 진화 상태")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_labels = {}
        status_info = [
            ("generation", "세대"),
            ("intelligence", "지능 레벨"),
            ("performance", "성능 점수"),
            ("creativity", "창의성 지수"),
            ("uniqueness", "고유성 점수")
        ]
        
        for i, (key, label) in enumerate(status_info):
            ttk.Label(status_frame, text=f"{label}:").grid(row=0, column=i*2, padx=5, pady=5)
            self.status_labels[key] = ttk.Label(status_frame, text="0", font=("Arial", 12, "bold"))
            self.status_labels[key].grid(row=0, column=i*2+1, padx=5, pady=5)
        
        # 중앙: 그래프 영역
        graph_frame = ttk.LabelFrame(main_frame, text="📈 진화 그래프")
        graph_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # matplotlib 그래프 설정
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 하단: 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="📋 진화 로그")
        log_frame.pack(fill=tk.X, pady=(0, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # 제어 버튼
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="🔄 새로고침", command=self.manual_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📊 통계 보기", command=self.show_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 데이터 내보내기", command=self.export_data).pack(side=tk.LEFT, padx=5)
    
    def real_time_update_loop(self):
        """실시간 업데이트 루프"""
        while self.monitoring_active:
            try:
                self.update_dashboard()
                time.sleep(2)  # 2초마다 업데이트
            except Exception as e:
                print(f"모니터링 업데이트 오류: {e}")
                time.sleep(5)
    
    def update_dashboard(self):
        """대시보드 업데이트"""
        try:
            # 최신 진화 데이터 조회
            cursor = self.db_connection.cursor()
            
            # 현재 상태 업데이트
            cursor.execute('''SELECT generation, intelligence_level, performance_gain 
                            FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT 1''')
            latest = cursor.fetchone()
            
            if latest:
                self.status_labels['generation'].config(text=str(latest[0]))
                self.status_labels['intelligence'].config(text=f"{latest[1]:.1f}")
                self.status_labels['performance'].config(text=f"{latest[2]:.1f}")
            
            # 최근 진화 기록 조회 (그래프용)
            cursor.execute('''SELECT generation, intelligence_level, performance_gain, timestamp 
                            FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT 20''')
            records = cursor.fetchall()
            
            if records:
                self.update_graphs(records)
            
            # 최근 로그 업데이트
            cursor.execute('''SELECT timestamp, generation, performance_gain 
                            FROM evolution_log 
                            ORDER BY timestamp DESC LIMIT 5''')
            recent_logs = cursor.fetchall()
            
            self.update_log_display(recent_logs)
            
        except Exception as e:
            print(f"대시보드 업데이트 오류: {e}")
    
    def update_graphs(self, records):
        """그래프 업데이트"""
        try:
            # 데이터 추출
            generations = [r[0] for r in reversed(records)]
            intelligence_levels = [r[1] for r in reversed(records)]
            performance_gains = [r[2] for r in reversed(records)]
            
            # 지능 레벨 그래프
            self.ax1.clear()
            self.ax1.plot(generations, intelligence_levels, 'b-o', linewidth=2, markersize=4)
            self.ax1.set_title('🧠 지능 레벨 진화', fontsize=12, fontweight='bold')
            self.ax1.set_xlabel('세대')
            self.ax1.set_ylabel('지능 레벨')
            self.ax1.grid(True, alpha=0.3)
            
            # 성능 향상 그래프
            self.ax2.clear()
            colors = ['red' if x < 0 else 'green' for x in performance_gains]
            self.ax2.bar(generations, performance_gains, color=colors, alpha=0.7)
            self.ax2.set_title('📈 성능 향상도', fontsize=12, fontweight='bold')
            self.ax2.set_xlabel('세대')
            self.ax2.set_ylabel('성능 향상')
            self.ax2.grid(True, alpha=0.3)
            self.ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # 그래프 새로고침
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            print(f"그래프 업데이트 오류: {e}")
    
    def update_log_display(self, logs):
        """로그 디스플레이 업데이트"""
        try:
            # 기존 로그 지우기
            self.log_text.delete(1.0, tk.END)
            
            # 새 로그 추가
            for log in logs:
                timestamp = log[0]
                generation = log[1]
                performance = log[2]
                
                # 시간 포맷팅
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except Exception:
                    time_str = timestamp
                
                # 로그 항목 생성
                log_entry = f"[{time_str}] Gen {generation}: 성능 {performance:+.1f}\n"
                self.log_text.insert(tk.END, log_entry)
            
            # 자동 스크롤
            self.log_text.see(tk.END)
            
        except Exception as e:
            print(f"로그 업데이트 오류: {e}")
    
    def manual_refresh(self):
        """수동 새로고침"""
        self.update_dashboard()
        print("대시보드 수동 새로고침 완료")
    
    def show_statistics(self):
        """통계 창 표시"""
        try:
            cursor = self.db_connection.cursor()
            
            # 통계 데이터 조회
            cursor.execute('''SELECT 
                            COUNT(*) as total_generations,
                            AVG(performance_gain) as avg_performance,
                            MAX(intelligence_level) as max_intelligence,
                            MIN(intelligence_level) as min_intelligence
                            FROM evolution_log''')
            stats = cursor.fetchone()
            
            # 통계 창 생성
            stats_window = tk.Toplevel(self.root)
            stats_window.title("📊 진화 통계")
            stats_window.geometry("400x300")
            
            stats_text = f"""
🧠 자기진화 AI 통계

📈 총 진화 세대: {stats[0]}
📊 평균 성능 향상: {stats[1]:.2f}
🚀 최고 지능 레벨: {stats[2]:.1f}
📉 최저 지능 레벨: {stats[3]:.1f}

🎯 진화 효율성: {(stats[2] - stats[3]) / max(1, stats[0]):.2f} (세대당 향상)
            """
            
            ttk.Label(stats_window, text=stats_text, justify=tk.LEFT).pack(padx=20, pady=20)
            
        except Exception as e:
            print(f"통계 표시 오류: {e}")
    
    def export_data(self):
        """데이터 내보내기"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''SELECT * FROM evolution_log ORDER BY timestamp''')
            data = cursor.fetchall()
            
            # JSON 파일로 내보내기
            export_file = f"evolution_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            export_data = []
            for row in data:
                export_data.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'generation': row[2],
                    'intelligence_level': row[3],
                    'code_analysis': row[4],
                    'improvement_suggestion': row[5],
                    'implementation_result': row[6],
                    'performance_gain': row[7]
                })
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"데이터 내보내기 완료: {export_file}")
            
        except Exception as e:
            print(f"데이터 내보내기 오류: {e}")
    
    def run(self):
        """모니터 실행"""
        try:
            print("🚀 실시간 진화 모니터 시작")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("모니터 종료")
        finally:
            self.monitoring_active = False
            self.db_connection.close()

if __name__ == "__main__":
    monitor = RealTimeEvolutionMonitor()
    monitor.run()
