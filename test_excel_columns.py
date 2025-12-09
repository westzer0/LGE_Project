import pandas as pd

df = pd.read_excel('data/스타일분석 메세지.xls', nrows=5)
print('컬럼명:')
for i, col in enumerate(df.columns):
    print(f'{i}: {repr(col)}')

print('\n\n첫 번째 행의 스타일 분석 결과:')
result = df.iloc[0]['스타일 분석 결과']
print(result)
print(f'\n타입: {type(result)}')

