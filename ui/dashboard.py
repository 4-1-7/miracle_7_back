import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 상위 디렉토리 경로 등록
from data.database import init_db, get_connection
import streamlit as st
import pandas as pd
from ui.sidebar.sidebar import init_sidebar
import folium
from streamlit.components.v1 import html
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import json


def show_homepage(df, selected_location):
    # TODO: 이제 로그인 시 사용자마다 값을 저장할수있게 로직을 처리해보자! 20250731 백두현현
    #init_db()

    # ---------------------
    # 지도 기반 시각화
    # ---------------------
    st.subheader("🗺️ 지도 기반 매물 시각화")


    center_longitude = float(df[0]["longitude"])
    center_latitude  = float(df[0]["latitude"])
    map_center = [center_latitude, center_longitude]

    with open("./data/late.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    location_dict = {
        entry["행정구역"]: (entry["위도"], entry["경도"])
        for entry in data
    }
    center_latitude, center_longitude = location_dict[selected_location]
    
    map_center = [center_latitude, center_longitude]
    marker_locations = [[listing["latitude"], listing["longitude"]] for listing in df]

    # 지도 표출
    map = folium.Map(location=map_center, zoom_start=13)


    # 크롤링된 매물들 처리
    for listing in df:
        popup_html = f"""
                    <div style="width:auto">
                        <br>
                        <h4>매물 정보</h4>
                        {listing["tradeTypeName"]} {listing["sameAddrMaxPrc"]}<br><br>
                        <h4>매물 특징</h4>
                        {listing["tagList"]}
                    </div>
                    """
        folium.Marker([listing["latitude"], listing["longitude"]], popup=folium.Popup(popup_html, max_width=500), tooltip="클릭해서 매물보기").add_to(map)
    if marker_locations:
        map.fit_bounds(marker_locations)
    m_html = map._repr_html_() 
    html(m_html, height=500)

    st.subheader("📋 매물 리스트")

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


    if isinstance(selected_data, pd.DataFrame):
        if not selected_data.empty:
            selected_row = selected_data.iloc[0].to_dict()
            st.markdown("### 🏠 매물 상세 정보")
            
            st.write(f"**매물명**: {selected_row.get('articleName', '정보 없음')}")
            st.write(f"**매물유형**: {selected_row.get('realEstateTypeName', '정보 없음')}")
            st.write(f"**거래유형**: {selected_row.get('tradeTypeName', '정보 없음')}")
            st.write(f"**보증금/월세**: {selected_row.get('sameAddrMaxPrc', '정보 없음')}")
            st.write(f"**공급/전용면적**: {selected_row.get('area1', '정보 없음')}㎡/{selected_row.get('area2', '정보 없음')}㎡")
            st.write(f"**방향**: {selected_row.get('direction', '정보 없음')}")
            st.write(f"**층수**: {selected_row.get('floorInfo', '정보 없음')}")
            st.write(f"**매물특징**: {selected_row.get('articleFeatureDesc', '정보 없음')}")
            
            tag_list = selected_row.get('tagList', [])
            tags = ", ".join(tag_list) if tag_list else "정보 없음"
            st.write(f"**태그**: {tags}")
            
            st.write(f"**확인일자**: {selected_row.get('articleConfirmYmd', '정보 없음')}")
            st.write(f"**중개사무소**: {selected_row.get('realtorName', '정보 없음')}")
            st.write(f"**매물링크**: {selected_row.get('cpPcArticleUrl', '정보 없음')}")
        else:
            st.write("📌 선택된 행이 없습니다.")
    else:
        st.info("위쪽 리스트에서 매물을 선택해주세요.")