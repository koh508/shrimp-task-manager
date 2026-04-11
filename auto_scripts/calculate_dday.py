from datetime import date

today = date(2026, 3, 25)
exam_date = date(2026, 4, 18)
d_day = (exam_date - today).days

print(f'{d_day}일 남았습니다.')