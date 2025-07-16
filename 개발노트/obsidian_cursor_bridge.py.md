#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

class ObsidianCursorBridge:
    def __init__(self):
        self.obsidian_vault_path = None
        self.search_results = []
        self.config_file = Path.home() / ".obsidian_cursor_config.json"
        self.load_config()

    def load_config(self):
        """설정 파일에서 옵시디언 볼트 경로를 로드합니다."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.obsidian_vault_path = config.get('vault_path')
            except Exception as e:
                print(f"설정 파일 로드 중 오류 발생: {e}")

    def save_config(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'vault_path': self.obsidian_vault_path}, f)
        except Exception as e:
            print(f"설정 파일 저장 중 오류 발생: {e}")

    def set_vault_path(self, path=None):
        """옵시디언 볼트 경로를 설정합니다."""
        if not path:
            # GUI 대화상자를 통해 볼트 경로 선택
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askdirectory(title="옵시디언 볼트 폴더를 선택하세요")
            if not path:
                return False
        
        self.obsidian_vault_path = path
        self.save_config()
        return True

    def search_vault(self, query, max_results=10):
        """볼트 내 파일을 검색하고 결과를 반환합니다."""
        if not self.obsidian_vault_path:
            print("옵시디언 볼트 경로가 설정되지 않았습니다.")
            return []

        self.search_results = []
        vault_path = Path(self.obsidian_vault_path)
        
        # 마크다운 파일만 검색
        for md_file in vault_path.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 대소문자 구분 없이 검색
                    if re.search(query, content, re.IGNORECASE):
                        # 파일 상대 경로 및 검색어 주변 컨텍스트 저장
                        rel_path = md_file.relative_to(vault_path)
                        context = self.extract_context(content, query)
                        self.search_results.append({
                            'file': str(rel_path),
                            'path': str(md_file),
                            'context': context
                        })
                        
                        if len(self.search_results) >= max_results:
                            break
            except Exception as e:
                print(f"파일 {md_file} 읽기 오류: {e}")
        
        return self.search_results

    def extract_context(self, content, query, context_length=100):
        """검색어 주변의 컨텍스트를 추출합니다."""
        match = re.search(query, content, re.IGNORECASE)
        if not match:
            return ""
        
        start = max(0, match.start() - context_length)
        end = min(len(content), match.end() + context_length)
        
        # 컨텍스트 추출 및 검색어 강조
        context = content[start:end]
        highlighted = re.sub(f"({query})", r"**\1**", context, flags=re.IGNORECASE)
        return highlighted

    def copy_to_cursor(self, result_index=0):
        """선택한 검색 결과를 클립보드에 복사하고 커서에서 사용할 수 있게 합니다."""
        if not self.search_results or result_index >= len(self.search_results):
            print("유효한 검색 결과가 없습니다.")
            return
        
        result = self.search_results[result_index]
        
        # 마크다운 형식으로 결과 포맷팅
        formatted_result = f"""
# 옵시디언 노트: {result['file']}

{result['context']}

---
원본 경로: {result['path']}
        """
        
        # 클립보드에 복사 (플랫폼에 따라 다른 방법 사용)
        try:
            # GUI를 통해 결과 표시
            root = tk.Tk()
            root.title("옵시디언 검색 결과")
            
            frame = tk.Frame(root, padx=10, pady=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(frame, text=f"파일: {result['file']}", font=("Arial", 12, "bold")).pack(anchor="w")
            
            text_widget = tk.Text(frame, wrap=tk.WORD, height=15, width=80)
            text_widget.insert(tk.END, result['context'])
            text_widget.config(state=tk.DISABLED)
            text_widget.pack(fill=tk.BOTH, expand=True, pady=10)
            
            def copy_to_clipboard():
                root.clipboard_clear()
                root.clipboard_append(formatted_result)
                messagebox.showinfo("복사 완료", "검색 결과가 클립보드에 복사되었습니다.")
            
            def open_in_obsidian():
                # obsidian:// URI 스키마를 사용하여 옵시디언에서 파일 열기
                uri = f"obsidian://open?vault={os.path.basename(self.obsidian_vault_path)}&file={result['file']}"
                webbrowser.open(uri)
            
            button_frame = tk.Frame(frame)
            button_frame.pack(fill=tk.X)
            
            tk.Button(button_frame, text="클립보드에 복사", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="옵시디언에서 열기", command=open_in_obsidian).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="닫기", command=root.destroy).pack(side=tk.RIGHT, padx=5)
            
            root.mainloop()
            
        except Exception as e:
            print(f"결과 복사 중 오류 발생: {e}")

    def show_search_gui(self):
        """검색을 위한 GUI 인터페이스를 제공합니다."""
        root = tk.Tk()
        root.title("옵시디언 볼트 검색")
        root.geometry("600x500")
        
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 볼트 경로 표시
        path_frame = tk.Frame(frame)
        path_frame.pack(fill=tk.X, pady=(0, 20))
        
        vault_label = tk.Label(path_frame, text="볼트 경로: ")
        vault_label.pack(side=tk.LEFT)
        
        vault_path_var = tk.StringVar(value=self.obsidian_vault_path or "경로가 설정되지 않았습니다")
        vault_path = tk.Label(path_frame, textvariable=vault_path_var, wraplength=400)
        vault_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(path_frame, text="변경", command=lambda: self.set_vault_path() and vault_path_var.set(self.obsidian_vault_path)).pack(side=tk.RIGHT)
        
        # 검색 입력
        search_frame = tk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="검색어: ").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 결과 리스트
        result_frame = tk.Frame(frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(result_frame, text="검색 결과:").pack(anchor="w")
        
        result_list = tk.Listbox(result_frame, height=10)
        result_list.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 검색 함수
        def perform_search():
            query = search_var.get()
            if not query:
                messagebox.showwarning("경고", "검색어를 입력하세요")
                return
                
            results = self.search_vault(query)
            result_list.delete(0, tk.END)
            
            if not results:
                result_list.insert(tk.END, "검색 결과가 없습니다")
                return
                
            for i, result in enumerate(results):
                result_list.insert(tk.END, f"{i+1}. {result['file']}")
        
        # 결과 선택 함수
        def on_result_select(event):
            selection = result_list.curselection()
            if not selection:
                return
                
            index = selection[0]
            if index < len(self.search_results):
                self.copy_to_cursor(index)
        
        result_list.bind('<Double-1>', on_result_select)
        
        # 버튼 프레임
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(button_frame, text="검색", command=perform_search).pack(side=tk.LEFT)
        tk.Button(button_frame, text="닫기", command=root.destroy).pack(side=tk.RIGHT)
        
        # Enter 키로 검색 실행
        search_entry.bind('<Return>', lambda event: perform_search())
        
        # 초기 포커스
        search_entry.focus_set()
        
        root.mainloop()

def main():
    parser = argparse.ArgumentParser(description='옵시디언과 커서 IDE를 연결하는 브릿지')
    parser.add_argument('--search', '-s', help='옵시디언 볼트에서 검색할 쿼리')
    parser.add_argument('--set-vault', '-v', help='옵시디언 볼트 경로 설정')
    parser.add_argument('--gui', '-g', action='store_true', help='GUI 모드로 실행')
    
    args = parser.parse_args()
    bridge = ObsidianCursorBridge()
    
    if args.set_vault:
        success = bridge.set_vault_path(args.set_vault)
        if success:
            print(f"옵시디언 볼트 경로가 설정되었습니다: {args.set_vault}")
        else:
            print("옵시디언 볼트 경로 설정에 실패했습니다.")
    
    elif args.search:
        if not bridge.obsidian_vault_path:
            print("옵시디언 볼트 경로가 설정되지 않았습니다. --set-vault 옵션을 사용하여 설정하세요.")
            return
        
        results = bridge.search_vault(args.search)
        if not results:
            print("검색 결과가 없습니다.")
            return
            
        print(f"{len(results)}개의 결과를 찾았습니다:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result['file']}")
        
        choice = input("\n결과를 보려면 번호를 입력하세요 (기본값: 1): ")
        try:
            index = int(choice) - 1 if choice else 0
            bridge.copy_to_cursor(index)
        except ValueError:
            print("유효한 번호를 입력하세요.")
    
    elif args.gui or not (args.set_vault or args.search):
        # GUI 모드 또는 인자 없이 실행 시 GUI 표시
        bridge.show_search_gui()

if __name__ == "__main__":
    main()
    