# pages/월세예측기.py

import streamlit as st
import pandas as pd
import json
import pickle
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

st.set_page_config(page_title="월세 예측기", page_icon="image/miracle_7_logo.png", layout="wide")
st.title("💡 머신러닝 기반 월세 예측기")


# Helper: Haversine 거리 계산 (단위 km)
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # 지구 반지름 (km)
    return c * r


# JSON 데이터 로딩
@st.cache_data
def load_data():
    with open("./data/land_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# 전처리
df['floor'] = df['floorInfo'].str.extract(r'(\d+)').astype(float)
df['rent'] = pd.to_numeric(df['rentPrc'], errors='coerce')
df['deposit'] = pd.to_numeric(df['dealOrWarrantPrc'], errors='coerce')

# 인코딩 맵
house_type_map = {v: i for i, v in enumerate(df['realEstateTypeName'].dropna().unique())}
direction_map = {v: i for i, v in enumerate(df['direction'].dropna().unique())}
trade_type_map = {"월세": 0, "전세": 1}

# 인코딩 컬럼 추가
df['house_type'] = df['realEstateTypeName'].map(house_type_map)
df['direction_code'] = df['direction'].map(direction_map)
df['trade_type_code'] = df['tradeTypeName'].map(trade_type_map)

df = df.dropna(subset=['floor', 'house_type', 'direction_code', 'trade_type_code', 'rent', 'latitude', 'longitude'])

# st.session_state 초기화
if "predicted_result" not in st.session_state:
    st.session_state.predicted_result = None

# 👉 사이드바 입력 영역
st.sidebar.subheader("📋 예측 정보 입력")
floor = st.sidebar.number_input("층수", min_value=1, max_value=50, value=3)
direction = st.sidebar.selectbox("방향", list(direction_map.keys()))
house_type = st.sidebar.selectbox("집 종류", list(house_type_map.keys()))
trade_type = st.sidebar.selectbox("거래 유형", ["월세", "전세"])

predict_button = st.sidebar.button("📈 예측하기")

# 예측 실행
# ---------------------------
if predict_button:
    try:
        x_input = np.array([[floor, house_type_map[house_type], direction_map[direction], trade_type_map[trade_type]]])

        with open("models/rent_model.pkl", "rb") as f:
            model, direction_map, house_type_map, trade_type_map = pickle.load(f)

        y_pred = int(model.predict(x_input)[0][0])

        # 조건에 맞는 매물 필터링
        filtered = df[
            (df['house_type'] == house_type_map[house_type]) &
            (df['direction_code'] == direction_map[direction]) &
            (df['trade_type_code'] == trade_type_map[trade_type])
        ].copy()

        if not filtered.empty:
            # 중심점: 첫 매물 기준
            base_lat = filtered.iloc[0]['latitude']
            base_lon = filtered.iloc[0]['longitude']

            # 반경 1km 내 매물만 필터링
            filtered['distance_km'] = filtered.apply(
                lambda row: haversine(base_lat, base_lon, row['latitude'], row['longitude']), axis=1
            )
            nearby = filtered[filtered['distance_km'] <= 1]

        else:
            nearby = pd.DataFrame()

        st.session_state.predicted_result = {
            "y_pred": y_pred,
            "filtered": nearby,
            "compare_col": 'rent' if trade_type == "월세" else 'deposit',
            "trade_type": trade_type
        }

    except Exception as e:
        st.session_state.predicted_result = {"error": str(e)}



# 예측 결과 출력
# ---------------------------
result = st.session_state.predicted_result
if result:
    if "error" in result:
        st.error(f"❌ 예측 실패: {result['error']}")
    else:
        st.markdown(f"""
        <div style="background-color: #f7f9fc; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); padding:20px; margin-bottom:20px;">
        <h4>✅ 예측 결과</h4>
        <p>예측된 {result['trade_type']}는 <strong>{result['y_pred']:,}만원</strong>입니다.</p>
        </div>
        """, unsafe_allow_html=True)


        if not result["filtered"].empty:
            avg_price = int(result["filtered"][result["compare_col"]].mean())

            # 지도 표시
            st.subheader("📍 반경 1km 유사 매물 지도")
            m = folium.Map(location=[result["filtered"].iloc[0]['latitude'], result["filtered"].iloc[0]['longitude']], zoom_start=14)
            for _, row in result["filtered"].iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=f"{int(row[result['compare_col']])}만원",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            st_folium(m, width=1200, height=500)

            # 예측 vs 평균 비교
            st.metric("💡 예측값", f"{result['y_pred']}만원")
            st.metric("🏘 실제 매물 평균", f"{avg_price}만원")

            # bar chart 비교
            chart_data = pd.DataFrame({
                "항목": ["예측값", "평균값", "최저값", "최고값"],
                "금액": [
                    result["y_pred"],
                    avg_price,
                    int(result["filtered"][result["compare_col"]].min()),
                    int(result["filtered"][result["compare_col"]].max())
                ]
            })
            st.bar_chart(chart_data.set_index("항목"))


        else:
            st.info("❗ 주변 1km 내 유사 매물이 없습니다.")

