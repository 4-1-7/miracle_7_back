#machinelearning.py

# https://www.youtube.com/watch?v=CkI7YvZWlCM

#다중선형회귀(Multiple Linear Regression) 기본 예제 - 월세예측

# machinelearning.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import pickle

# JSON 데이터 불러오기
rent_Data = pd.read_json("./data/land_data.json")  # VS Code 실행 시에는 상대경로로 사용

# 전처리
rent_Data['floor'] = rent_Data['floorInfo'].str.extract(r'(\d+)').astype(float)
rent_Data['rent'] = pd.to_numeric(rent_Data['rentPrc'], errors='coerce')

# 인코딩 맵 정의
house_type_map = {v: i for i, v in enumerate(rent_Data['realEstateTypeName'].dropna().unique())}
direction_map = {v: i for i, v in enumerate(rent_Data['direction'].dropna().unique())}
trade_type_map = {"월세": 0, "전세": 1}

# 인코딩 적용
rent_Data['house_type'] = rent_Data['realEstateTypeName'].map(house_type_map)
rent_Data['direction_code'] = rent_Data['direction'].map(direction_map)
rent_Data['trade_type_code'] = rent_Data['tradeTypeName'].map(trade_type_map)

# 결측치 제거
rent_Data = rent_Data.dropna(subset=['floor', 'house_type', 'direction_code', 'trade_type_code', 'rent'])

# 학습 데이터 준비
x = rent_Data[['floor', 'house_type', 'direction_code', 'trade_type_code']]
y = rent_Data[['rent']]

# 학습/테스트 분리
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8)

# 모델 학습
lr = LinearRegression()
lr.fit(x_train, y_train)

# 정확도 출력
print("모델 정확도:", lr.score(x_test, y_test))

# 모델 저장 (4개 인코딩 맵 포함)
with open("models/rent_model.pkl", "wb") as f:
    pickle.dump((lr, direction_map, house_type_map, trade_type_map), f)

# 시각화
y_predicted = lr.predict(x_test)
plt.scatter(y_test, y_predicted, alpha=0.5)
plt.xlabel("실제 월세")
plt.ylabel("예측 월세")
plt.title("실제 vs 예측")
plt.grid(True)
plt.tight_layout()
plt.show()
