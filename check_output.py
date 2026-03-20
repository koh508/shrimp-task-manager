import sys, re
sys.stdout.reconfigure(encoding='utf-8')
path = r'C:\Users\User\Documents\Obsidian Vault\OCU\공조냉동기계기사\실기기출_25년1-3회.md'
md = open(path, encoding='utf-8').read()

# 탭문자 확인
tabs = md.count('\t')
print(f'탭문자 총 개수: {tabs}')

# 수식 샘플 (repr로 탭 확인)
lines_with_dollar = [l for l in md.split('\n') if '$' in l][:5]
print('\n수식 포함 라인 (repr):')
for l in lines_with_dollar:
    print(' ', repr(l[:80]))

# 표 샘플
idx = md.find('|')
print('\n표 샘플:')
print(md[idx:idx+400])

# 이미지 목록
imgs = re.findall(r'!\[\[(.+?)\]\]', md)
print(f'\n이미지 {len(imgs)}개:')
for i in imgs[:8]:
    print(' ', i)
