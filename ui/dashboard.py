import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 상위 디렉토리 경로 등록
from data.database import init_db, get_connection
import streamlit as st
import pandas as pd
from ui.sidebar.sidebar import init_sidebar
import html
import folium
from streamlit.components.v1 import html
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from geopy.geocoders import Nominatim
import math
from ui.sidebar.page_of_distance_per_method import format_address, convert_distance_time, get_car_route, get_walk_route, get_coords, get_route
# kakao API 키
kakao_api_key = "fb1bd569e343b2b3821ea18ec1694b74"
# TMAP API 키
tmap_api_key = "KXgnElYbnf9P4rPyZzanN91cHMyScabF1ZY4ifZR"

def haversine_distance(addr1_x, addr1_y, addr2_x, addr2_y, articleNo, articleName, tagList):
    r = 6371
    # 라디안 변환
    dlat = math.radians(addr2_x - addr1_x)
    dlon = math.radians(addr2_y - addr1_y)

    # 거리 계산 공식
    val = math.sin(dlat/2)**2 + math.cos(math.radians(addr1_x)) * math.cos(math.radians(addr2_x)) * math.sin(dlon/2)**2
    result = 2 * r * math.atan2(math.sqrt(val), math.sqrt(1 - val))


    return {"article_no": articleNo, "distance": result, "articleName": articleName, "tagList": tagList}

def show_homepage(df, selected_location, start_longitude, start_latitude):
    # ---------------------
    # 지도 기반 시각화
    # ---------------------
    st.subheader("🗺️ 지도 기반 매물 시각화")

    map_center = [start_latitude, start_longitude]
    marker_locations = [[listing["latitude"], listing["longitude"]] for listing in df]

    # 지도 표출
    map = folium.Map(location=map_center, zoom_start=20)
    distance_info = []
    # 크롤링된 매물들 처리
    for listing in df:
        # 매물마다 직선거리 dict list
        distance_info.append(haversine_distance(float(start_longitude), float(start_latitude), float(listing["longitude"]), float(listing["latitude"]), listing["articleNo"], listing["articleName"], listing["tagList"]))
 
        popup_html = f"""
                    <div style="width:auto; font-family:Arial; font-size:13px">
                        <h4 style="margin-bottom:2px;">매물번호</h4>
                        {listing["articleNo"]}<br>
                        <h4 style="margin-bottom:2px;">매물명</h4> 
                        {listing["articleName"]}<br>
                        <h4 style="margin-bottom:2px;">매물 정보</h4>
                        {listing["tradeTypeName"]} {listing["sameAddrMaxPrc"]}<br>
                        <h4 ">매물 특징</h4>
                        {listing["tagList"]}
                
                    </div>
                    """
        folium.Marker([listing["latitude"], listing["longitude"]], popup=folium.Popup(popup_html, max_width=500), tooltip="클릭해서 매물보기").add_to(map)

    popup_html_start_loc = f"""
                    <div style="width:auto; font-family:Arial; font-size:13px">
                        <h4 style="margin-bottom:5px;">회사/사무실 위치</h4>
                    </div>
        """
    folium.Marker(
    location=[start_latitude, start_longitude],
    popup=folium.Popup(popup_html_start_loc, max_width=500), 
    tooltip="회사위치",
    icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(map)

    if marker_locations:
        map.fit_bounds(marker_locations)
    m_html = map._repr_html_() 
    html(m_html, height=500)

    st.subheader("📋 매물 리스트")
    top1 = 0.0
    if distance_info:
        sorted_items = sorted(distance_info, key=lambda x: x['distance'])
        top1 = sorted_items[0]
        article_name = top1.get("articleName", "이름 없음")
        tag_list = top1.get("tagList", "")
        top1_link = top1_link = next((item.get("cpPcArticleUrl") for item in df if item.get("articleNo") == top1.get("article_no")), "정보 없음")
        rent = next((item.get("sameAddrMaxPrc") for item in df if item.get("articleNo") == top1.get("article_no")), "정보 없음")        
        tag_elements = " ".join([f"<span style='background:#e0e0ff;padding:3px 8px;border-radius:6px;margin-right:4px;font-size:13px;'>{t}</span>"for t in tag_list])
    

        st.markdown(f"""
            <div style="
                background-color: #f5f5fa;
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 1px 1px 6px rgba(0,0,0,0.1);
                font-family: 'Segoe UI';
            ">
                <h4 style="margin-bottom: 5px;">📍가장 가까운 매물을 찾았어요! 🎉🙌</h4>
                <p><strong>🆔 매물 번호:</strong> {top1["article_no"]}<br>
                <strong>📏 거리:</strong> {top1["distance"]:.4f} km<br>
                <strong>🏷️ 이름:</strong> {article_name}<br>
                <strong>💬 특징:</strong> {tag_elements}</p>
                <strong>💬 보증금/월세:</strong> {rent}</p>
                <a href="{top1_link}" target="_blank" style="
                    text-decoration: none; 
                    background-color: #007bff; 
                    color: white; 
                    padding: 8px 16px; 
                    border-radius: 8px; 
                    display: inline-block;
                ">매물 상세 페이지 바로가기</a>
            </div>
            """, unsafe_allow_html=True)

    sort_options = {
        '건물명': 'articleName',
        '보증금/월세': 'sameAddrMaxPrc',
        '협의가능' : 'sameAddrMinPrc',
        '주거유형' : 'realEstateTypeName',
        '매물특징' : 'articleFeatureDesc'
    }

    selected_label = st.selectbox("정렬 기준", list(sort_options.keys()))
    standard_sort = sort_options[selected_label]

    type_sort = st.radio("정렬 방식", ['오름차순', '내림차순'])  # 정렬 방식

    ascending = True if type_sort == '오름차순' else False
    real_df = pd.DataFrame(df)
    sorted_df = real_df.sort_values(by=standard_sort, ascending=ascending).reset_index(drop=True)

    selected_columns_display = ['건물명', '보증금/월세', '협의가능', '주거유형', '매물특징']

    selected_columns = [sort_options[col] for col in selected_columns_display]

    grid_df = sorted_df[selected_columns]
    #st.dataframe(grid_df)

    # 빌드 설정
    builder = GridOptionsBuilder.from_dataframe(sorted_df)
    # 모든 컬럼 숨기기
    for col in sorted_df.columns:
        builder.configure_column(col, hide=True)
    builder.configure_pagination(enabled=True) # 페이징 처리
    builder.configure_selection(selection_mode='single', use_checkbox=True) 
    builder.configure_column(field='articleNo', header_name='NO', editable=False, hide=False)
    builder.configure_column(field='articleName', header_name='매물명', editable=False, hide=False) 
    builder.configure_column(field='sameAddrMaxPrc', header_name='보증금/월세',editable=False, hide=False)
    builder.configure_column(field='sameAddrMinPrc', header_name='협의가능', editable=False, hide=False)
    builder.configure_column(field='realEstateTypeName', header_name='매물유형', editable=False, hide=False)
    builder.configure_column(field='articleFeatureDesc', header_name='매물특징', editable=False, hide=False)


    grid_options = builder.build()

    grid_response = AgGrid(sorted_df, gridOptions=grid_options, update_mode='SELECTION_CHANGED')

    selected_data = grid_response.get('selected_rows', [])



    if isinstance(selected_data, pd.DataFrame) and not selected_data.empty:
        selected_row = selected_data.iloc[0].to_dict()

        # 로고와 타이틀을 한 줄에 배치
        col_title = st.columns(1)[0]
        with col_title:
            st.header("🏠 매물 상세 정보")

        # 좌표 변환
        geo = get_coords(selected_location, kakao_api_key)

        start_longitude = geo[0] # X축
        start_latitude = geo[1]  # Y축

        st.subheader("🚊 교통수단을 선택해주세요.")
        vehicles = {"🚶‍♂️ 도보":"WALK", "🚌 자동차":"BUS"}
        vehicle_input = st.selectbox("📍 교통수단", list(vehicles.keys()))
        records = []
        with st.spinner("경로 계산 중입니다...잠시만 기다려주세요!"):
                route = get_route(start_longitude, start_latitude, selected_row["longitude"], selected_row["latitude"], tmap_api_key, vehicle_input)

                geolocator = Nominatim(user_agent="do_reverse_geocoder")

                reverse_geo = geolocator.reverse((selected_row["latitude"], selected_row["longitude"]), language='ko')
                
                if reverse_geo:
                    target_address = format_address(reverse_geo.raw)

                records.append({
                    "articleName" : selected_row["articleName"],
                    "realEstateTypeName" : selected_row["realEstateTypeName"],
                    "tradeTypeName" : selected_row["tradeTypeName"],
                    "area1" : selected_row["area1"],
                    "area2" : selected_row["area2"],
                    "direction" : selected_row["direction"],
                    "floorInfo" : selected_row["floorInfo"],
                    "tagList" : selected_row["tagList"],
                    "dealOrWarrantPrc" : selected_row["dealOrWarrantPrc"],
                    "rentPrc" : selected_row["rentPrc"],
                    "buildingName" : selected_row["buildingName"],
                    "articleConfirmYmd" : selected_row["articleConfirmYmd"],
                    "realtorName" : selected_row["realtorName"],
                    "cpPcArticleUrl" : selected_row["cpPcArticleUrl"],
                    "출발지주소" : selected_location,
                    "도착지주소" : target_address,
                    "이동수단" : route[0],
                    "거리" : route[1],
                    "소요시간": route[2]
                })

        # 주요 정보를 2개의 열로 나누어 배치
        col1 = st.columns(1)[0]
        feature_string = selected_row.get('articleFeatureDesc', '')

        if records:
            거리 = records[0]["거리"]
            소요시간 = records[0]["소요시간"]
        else:
            거리 = "정보 없음"
            소요시간 = "정보 없음"

        tag_list = selected_row.get("tagList", "")
        tag_elements = " ".join([f"<span style='background:#e0f7fa;padding:3px 8px;border-radius:6px;margin-right:4px;font-size:13px;'>{t}</span>"for t in tag_list])

        with col1:
            st.markdown(
                    f"""
                    <div style="background-color: #f7f9fc; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); padding:20px;">
                        <h2>🏠 {selected_row["articleName"]}</h2>
                        <p>⭐ 건물 번호          <strong>{selected_row["articleNo"]}</strong></p> 
                        <p>🧭 채광 방향           <strong>{selected_row["direction"]}</strong></p>                                  
                        <p>🏢 층수(복층 여부)     <strong>{selected_row["floorInfo"]}  ({"복층" if "복층" in selected_row["tagList"] else "일반형"}) </strong></p>
                        <p>📐 매물의 면적         <strong>{selected_row["area1"]}㎡ / {selected_row["area2"]}㎡</strong></p>
                        <p>📍 매물까지의 거리      <strong>{거리}</strong></p>                                     
                        <p>⏱️ 매물까지 소요 시간   <strong>{소요시간} 소요</strong></p>
                        <p>📅 확인일자           <strong>{selected_row["articleConfirmYmd"][:4]}년 {selected_row["articleConfirmYmd"][4:6]}월 {selected_row["articleConfirmYmd"][6:]}일</strong></p>
                        <p>🧑‍💼 공인중개사         <strong>{selected_row["realtorName"]}</strong></p>
                        <p>✨<strong>{tag_elements}</strong></p> 
                        <p>🌟<strong>{feature_string}</strong></p>    
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("---")

        link = selected_row.get('cpPcArticleUrl', None)
        if link:

            col_empty1, col_btn, col_empty2 = st.columns([1, 2, 1])
            with col_btn:
                st.link_button("매물 상세 페이지 바로가기", link, type="primary", use_container_width=True)


    else:
        st.info("위쪽 리스트에서 매물을 선택해주세요.")
        st.image("./data/not_home.png", width=500)