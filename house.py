import streamlit as st
import pandas as pd
# 샘플 매물 데이터 (실제 API 연동 필요)
df = pd.DataFrame({
    '지역': ['서울 강남', '서울 마포', '서울 송파'],
    '가격': [80000, 55000, 72000],
    '면적': [30, 20, 25],
    '위도': [37.4979, 37.5407, 37.5065],
    '경도': [127.0276, 126.9469, 127.1060],
    '주소': ['강남역 근처', '홍대입구역 근처', '잠실역 근처'],
    '층': [10, 5, 7],
    '방수': [2, 1, 3],
    '엘리베이터': ['있음', '없음', '있음'],
    '난방': ['중앙난방', '개별난방', '지역난방']
})

# ---------------------
# 1. 대시보드 UI 구성
# ---------------------
st.set_page_config(page_title="부동산 대시보드", layout="wide")

st.title("🏡 7번방의 기적")
st.sidebar.header("🔍 필터링 검색")

# 필터 옵션
지역옵션 = st.sidebar.multiselect("지역 선택", options=df['지역'].unique(), default=df['지역'].unique())
가격범위 = st.sidebar.slider("가격 범위 (만원)", min_value=0, max_value=100000, value=(0, 100000))
면적범위 = st.sidebar.slider("면적 범위 (㎡)", min_value=10, max_value=60, value=(10, 60))

# 필터링 적용
filtered_df = df[
    df['지역'].isin(지역옵션) &
    df['가격'].between(가격범위[0], 가격범위[1]) &
    df['면적'].between(면적범위[0], 면적범위[1])
]


# ---------------------
# 2. 지도 기반 시각화
# ---------------------
st.subheader("🗺️ 지도 기반 매물 시각화")


st.markdown("""
<div style='
    border: 2px dashed #999;
    height: 400px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f9f9f9;
    font-size: 20px;
    font-weight: bold;
    color: #555;
'>
지도 기반 매물 시각화 영역 (추후 KakaoMap 삽입 예정)
</div>
""", unsafe_allow_html=True)


# st.subheader("🗺️ 지도 기반 매물 시각화")
# m = folium.Map(location=[37.5, 127], zoom_start=11)

# for i, row in filtered_df.iterrows():
#     popup_text = f"{row['지역']}<br>{row['가격']}만원<br>{row['주소']}"
#     folium.Marker([row['위도'], row['경도']], popup=popup_text).add_to(m)

# st_data = st_folium(m, width=700, height=500)

# ---------------------
# 3. 매물 리스트 및 정렬
# ---------------------
st.subheader("📋 매물 리스트")

정렬기준 = st.selectbox("정렬 기준", ['가격', '면적'])
정렬방식 = st.radio("정렬 방식", ['오름차순', '내림차순'])

ascending = True if 정렬방식 == '오름차순' else False
sorted_df = filtered_df.sort_values(by=정렬기준, ascending=ascending)

st.dataframe(sorted_df[['지역', '가격', '면적', '주소']])

# ---------------------
# 4. 매물 상세 정보 모달 구성 (예시)
# ---------------------
st.subheader("🏠 매물 상세 보기")

선택매물 = st.selectbox("매물 선택", sorted_df['주소'].tolist())
매물정보 = sorted_df[sorted_df['주소'] == 선택매물].iloc[0]

with st.expander(f"{매물정보['주소']} 상세 정보 보기"):
    st.write(f"📍 위치: {매물정보['지역']} - {매물정보['주소']}")
    st.write(f"💰 가격: {매물정보['가격']}만원")
    st.write(f"📐 면적: {매물정보['면적']}㎡")
    st.write(f"🚪 방수: {매물정보['방수']} / 층수: {매물정보['층']}")
    st.write(f"🔥 난방: {매물정보['난방']} / 🛗 엘리베이터: {매물정보['엘리베이터']}")
    st.image("https://via.placeholder.com/300x200.png?text=매물+이미지", caption="샘플 이미지")
    st.write("📞 주변 공인중개사: 02-1234-5678")

# ---------------------
# 5. 사용자 맞춤형 요약 정보 배치
# ---------------------
st.sidebar.subheader("🚀 요약 정보")
st.sidebar.write(f"필터링 결과 매물 수: {len(filtered_df)}건")
st.sidebar.write(f"최저가: {filtered_df['가격'].min()}만원 / 최고가: {filtered_df['가격'].max()}만원")
