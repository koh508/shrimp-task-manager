import json, os, sys
from collections import Counter
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

db_path = r'C:\Users\User\Documents\Obsidian Vault\SYSTEM\onew_pure_db.json'
vault = r'C:\Users\User\Documents\Obsidian Vault'

if not os.path.exists(db_path):
    print('DB 없음')
    sys.exit()

data = json.load(open(db_path, encoding='utf-8'))
print(f'[온유 DB 동기화 상태]')
print(f'총 임베딩 문서: {len(data)}개')

# 최근 업데이트
items = sorted(data.items(), key=lambda x: x[1].get('updated',''), reverse=True)
if items:
    print(f'최근 동기화: {items[0][1].get("updated","?")}')
    print(f'최근 파일: {os.path.basename(items[0][0])}')

# DB 파일 크기
db_size = os.path.getsize(db_path) / 1024 / 1024
print(f'DB 파일 크기: {db_size:.1f} MB')

# Vault 전체 md 파일 수
total_md = sum(
    len([f for f in files if f.endswith('.md')])
    for _, _, files in os.walk(vault)
    if '.obsidian' not in _ and 'SYSTEM' not in _
)
print(f'\nVault 총 MD 파일: {total_md}개')
print(f'DB 미포함 가능성: {total_md - len(data)}개')

# 폴더별 통계
folders = Counter()
for path in data.keys():
    parts = path.replace(vault, '').strip('\\').split('\\')
    folder = parts[0] if parts else 'root'
    folders[folder] += 1

print('\n폴더별 임베딩 현황:')
for f, c in folders.most_common(15):
    print(f'  {f}: {c}개')
