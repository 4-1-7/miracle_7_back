import streamlit as st
import requests
import re
import pandas as pd
from streamlit_folium import st_folium
from scraping.crawling import crawling
from ui.sidebar.sidebar import init_finding_path
import time
from geopy.geocoders import Nominatim
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# kakao API 키
kakao_api_key = "fb1bd569e343b2b3821ea18ec1694b74"
# TMAP API 키
tmap_api_key = "KXgnElYbnf9P4rPyZzanN91cHMyScabF1ZY4ifZR"

region_map = {
    "서울": "서울특별시",
    "경기": "경기도",
    "부산": "부산광역시",
    "인천": "인천광역시",
    "대구": "대구광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도"
}

st.set_page_config(
    page_title = "🚦 길찾기",
    layout = "wide"
)

def update_region_name(address_name):
    parts = address_name.split()
    if not parts:
        return address_name  # 비어있는 경우 그대로 반환
    region_key = parts[0]
    full_region = region_map.get(region_key)
    if full_region:
        parts[0] = full_region  # 변환된 명칭으로 교체
        return " ".join(parts)
    return address_name  # 변환 대상 아님

def get_route(startX, startY, endX, endY, appKey, method):
    if method == "🚶‍♂️ 도보":
        tmp = get_walk_route(startX, startY, endX, endY, tmap_api_key)
    elif method == "🚌 버스":
        tmp = get_car_route(startX, startY, endX, endY, tmap_api_key)

    return convert_distance_time(tmp)

def get_walk_route(startX, startY, endX, endY, appKey):
    url = f"https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&format=json&appKey={appKey}"
    headers = {"Content-Type": "application/json"}
    body = {
        "startX": str(startX), "startY": str(startY),
        "endX": str(endX), "endY": str(endY),
        "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
        "startName": "출발지", "endName": "도착지"
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        try:
            props = response.json()["features"][0]["properties"]
            return ("도보", props["totalDistance"], props["totalTime"])
        except:
            return ("도보", None, None)
    return ("도보", None, None)

def get_car_route(startX, startY, endX, endY, appKey):
    url = f"https://apis.openapi.sk.com/tmap/routes?version=1&format=json&appKey={appKey}"
    headers = {"Content-Type": "application/json"}
    body = {
        "startX": str(startX), "startY": str(startY),
        "endX": str(endX), "endY": str(endY),
        "reqCoordType": "WGS84GEO", "resCoordType": "WGS84GEO",
        "startName": "출발지", "endName": "도착지",
        "searchOption": 0, "trafficInfo": "Y"
    }
    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        try:
            props = response.json()["features"][0]["properties"]
            return ("자동차", props["totalDistance"], props["totalTime"])
        except:
            return ("자동차", None, None)
    return ("자동차", None, None)
    
def get_coords(address, kakao_api_key):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    if result['documents']:
        x = result['documents'][0]['x']  # 경도
        y = result['documents'][0]['y']  # 위도
        return x, y, result
    else:
        return None, None
    
def convert_distance_time(tuple):
    method, distance_m, time_sec = tuple[0], tuple[1], tuple[2]

    if distance_m is None or time_sec is None:
        return st.warning("❌ 거리 또는 시간 정보가 부족합니다.")

    distance_km = round(distance_m / 1000, 1)
    minutes = time_sec // 60
    seconds = time_sec % 60
    expect_minutes = round(distance_km / 5 * 60)

    return (
        f"{method}",
        f"{distance_km}km ({distance_m}m)",
        f"{minutes}분 {seconds}초"
    )

# geocoding을 reverse로 할때 정상적인 format으로 주소명 변환
def format_address(addr_dict):
    addr = addr_dict.get('address', {})
    parts = [
        addr.get('city', ''),
        addr.get('borough', ''),
        addr.get('road', ''),
        addr.get('suburb', '')
    ]
    formatted = ' '.join(filter(None, parts))
    return formatted


st.title("🏃‍♂️ 직장 근처 매물 찾기")
office_info, deposit_range, rent_range, flag = init_finding_path()
print(f"시작주소: {office_info}")
st.subheader("🚊 교통수단을 선택해주세요.")
vehicles = {"🚶‍♂️ 도보":"WALK", "🚌 자동차":"BUS"}
vehicle_input = st.selectbox("📍 교통수단", list(vehicles.keys()))

# 좌표 변환
geo = get_coords(office_info, kakao_api_key)
start_longitude = geo[0] # X축
start_latitude = geo[1]  # Y축
if start_latitude and start_longitude:
    response = geo[2]

    name = f"{response["documents"][0]["address"]["region_1depth_name"]} {response["documents"][0]["address"]["region_2depth_name"]} {response["documents"][0]["address"]["region_3depth_name"]}"
    address_name = update_region_name(name)
    print(f"길찾기 지번주소 검색: {address_name}")

    # 크롤링 데이터 ON
    if flag:
        filtered_df = crawling(address_name, rent_range[1], rent_range[0], deposit_range[1], deposit_range[0])

        if not filtered_df:
            st.warning("매물 데이터가 존재하지 않습니다.")
        
        house_locations = [
            {
                    "articleName": item["articleName"],
                    "realEstateTypeName": item["realEstateTypeName"],
                    "tradeTypeName": item["tradeTypeName"],
                    "area1": item["area1"],
                    "area2": item["area2"],
                    "direction": item["direction"],
                    "floorInfo": item["floorInfo"],
                    "tagList": item["tagList"],
                    "dealOrWarrantPrc": item["dealOrWarrantPrc"],
                    "rentPrc": item["rentPrc"],
                    "buildingName": item["buildingName"],
                    "articleConfirmYmd": item["articleConfirmYmd"],
                    "realtorName": item["realtorName"],
                    "cpPcArticleUrl": item["cpPcArticleUrl"],
                    "longitude": item["longitude"],
                    "latitude": item["latitude"]
            } for item in filtered_df]
        
        
        # 매물 카드 5개 보여주기
        page_size = 5
        page_num = st.session_state.get('page_num', 0)
        start_idx = page_num * page_size
        end_idx = start_idx + page_size
        sliced_location = house_locations[start_idx:end_idx]

        records = []

        # 카드 5개 보여주기
        current_record = records[start_idx:end_idx]

        with st.spinner("경로 계산 중입니다...잠시만 기다려주세요!"):
            for i, row in enumerate(sliced_location):
                route = get_route(start_longitude, start_latitude, row["longitude"], row["latitude"], tmap_api_key, vehicle_input)

                geolocator = Nominatim(user_agent="do_reverse_geocoder")

                reverse_geo = geolocator.reverse((row["latitude"], row["longitude"]), language='ko')
                
                if reverse_geo:
                    target_address = format_address(reverse_geo.raw)

                records.append({
                    "articleName" : row["articleName"],
                    "realEstateTypeName" : row["realEstateTypeName"],
                    "tradeTypeName" : row["tradeTypeName"],
                    "area1" : row["area1"],
                    "area2" : row["area2"],
                    "direction" : row["direction"],
                    "floorInfo" : row["floorInfo"],
                    "tagList" : row["tagList"],
                    "dealOrWarrantPrc" : row["dealOrWarrantPrc"],
                    "rentPrc" : row["rentPrc"],
                    "buildingName" : row["buildingName"],
                    "articleConfirmYmd" : row["articleConfirmYmd"],
                    "realtorName" : row["realtorName"],
                    "cpPcArticleUrl" : row["cpPcArticleUrl"],
                    "출발지주소" : office_info,
                    "도착지주소" : target_address,
                    "이동수단" : route[0],
                    "거리" : route[1],
                    "소요시간": route[2]
                })
        st.subheader("📋 나의 매물 카드")

        if not records:
            st.info("표시할 매물이 없습니다 😢")

        for item in records:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color:#f5f5f5; padding:15px; border-radius:8px; box-shadow: 1px 1px 4px rgba(0,0,0,0.1);">
                        <h3>🏠 {item["articleName"]}</h3>
                        🔖 <strong>매물 타입:</strong> {item["realEstateTypeName"]}<br>
                        🤝 <strong>거래유형:</strong> {item["tradeTypeName"]}<br>
                        🔢 <strong>면적:</strong> {item["area1"]}㎡ / {item["area2"]}㎡<br>
                        ☀️ <strong>방향:</strong> {item["direction"]}<br>
                        🧭 <strong>층수:</strong> {item["floorInfo"]}  <strong>복층 여부:</strong> {"복층" if "복층" in item["tagList"] else "일반형"}<br>
                        💰 <strong>보증금/월세:</strong> {item["dealOrWarrantPrc"]} / {item["rentPrc"]}만원<br>
                        🏢 <strong>건물명:</strong> {item["buildingName"]}<br>
                        🗓️ <strong>확인일자:</strong> {item["articleConfirmYmd"][:4]}년 {item["articleConfirmYmd"][4:6]}월 {item["articleConfirmYmd"][6:]}일<br>
                        👤 <strong>공인중개사:</strong> {item["realtorName"]}<br>
                        🚗 <strong>{item["이동수단"]}</strong> → <strong>{item["거리"]}</strong>km<br>
                        ⏱️ 예상 소요시간: <strong>{item["소요시간"]}</strong><br><br>
                        👉 <a href="{item["cpPcArticleUrl"]}" target="_blank">매물 상세페이지 바로가기</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown("")  



        col1 = st.columns(1)
        with col1[0]: 
            if end_idx < len(house_locations) and st.button("더보기"):
                st.session_state.page_num = page_num + 1


