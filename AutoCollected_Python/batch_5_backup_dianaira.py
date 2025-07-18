import os
import zipfile
import datetime
from pathlib import Path

def backup_dianaira():
    # 백업 대상 디렉토리
    source_dir = Path(r'd:\백업폴더\mcp_system')
    
    # 백업 파일명 (날짜-시간 포함)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_zip = f'd:\\dianaira_backup_{timestamp}.zip'
    
    # 백업 대상 파일 패턴
    patterns = [
        'dianaira_*',
        'run_dianaira.py',
        'logs/dianaira*',
        'logs/dianaira/*',
        '*.log'
    ]
    
    # ZIP 파일 생성
    with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pattern in patterns:
            for file_path in source_dir.rglob(pattern):
                if file_path.is_file():
                    # 상대 경로로 저장
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
                    print(f'백업 완료: {file_path}')
    
    print(f'\n백업이 완료되었습니다: {backup_zip}')

if __name__ == '__main__':
    try:
        print('데이아네이라 백업을 시작합니다...')
        backup_dianaira()
    except Exception as e:
        print(f'백업 중 오류가 발생했습니다: {e}')
