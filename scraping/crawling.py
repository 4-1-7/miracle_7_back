import requests
import json
import csv
from datetime import datetime
import codecs
import time
import pandas as pd
from bs4 import BeautifulSoup 
import streamlit as st

@st.cache_data

def coords(query):
    api_key = '61a75fb04f4dce476cc883a26c87c312'
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": query}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors
        res = response.json()
        if res["documents"]:
            doc = res["documents"][0]
            return doc["y"], doc["x"]  # 위도, 경도
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates from Kakao: {e}")
        return None, None

def get_real_estate_data(cortar_no, rP_M, rP_m, p_M, p_m, page=1):

    cookies = {
        'page_uid': 'j4DEOdqo1awss5k5NJ8sssssscN-065567',
        'NNB': 'YPBLFJKGM2EWQ',
        'BUC': 'pmQb6a3t8kgwgak2eQVn-NKGXIxPS71gSAysRtmDeFs=',
        'SRT30': '1753837875',
        'NAC': 'PZScBsglQCk4',
        'NACT': '1',
        'nhn.realestate.article.rlet_type_cd': 'A01',
        'nhn.realestate.article.trade_type_cd': '',
        'nhn.realestate.article.ipaddress_city': '1100000000',
        '_fwb': '200xigIMu2x4HrfpI76qOJG.1753852167020',
        'landHomeFlashUseYn': 'Y',
        'REALESTATE': 'Wed%20Jul%2030%202025%2015%3A10%3A27%20GMT%2B0900%20(Korean%20Standard%20Time)',
        'PROP_TEST_KEY': '1753855827492.46a3db9aa221b8841f121e27e5ea75e313732f378b5832688b77bf72632d4a58',
        'PROP_TEST_ID': 'bd8d94ad55e64024075d59e5ee55fd4d11089b1f6cb954c3ef606df755fb9fb3',
        'SRT5': '1753854953',
        'SHOW_FIN_BADGE': 'Y',
        'bnb_tooltip_shown_finance_v1': 'true',
    }

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NTM4NjMxOTEsImV4cCI6MTc1Mzg3Mzk5MX0.RXS5sM5j0p9Ybi46zxMsoQ6efVVJVbqW5Y0dcMIMcJE', # Placeholder: This token is dynamic. You might need to capture it from a live session or implement a way to generate/extract it.
        'priority': 'u=1, i',
        'referer': 'https://new.land.naver.com/articles?ms=37.4871026,127.0645068,17&a=APT:OPST:ABYG:OBYG:GM:OR:DDDGG:JWJT:SGJT:HOJT:VL:YR:DSD&e=RETAIL&g=1000&aa=SMALLSPCRENT&ae=ONEROOM', # Example referer, can be dynamic
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    url = "https://new.land.naver.com/api/articles"

    params = {
        'cortarNo': str(cortar_no),
        'order': 'rank',
        'realEstateType': 'APT:OPST:ABYG:OBYG:GM:OR:DDDGG:JWJT:SGJT:HOJT:VL:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD:YR:DSD',
        'tradeType': '', 
        'tag': ':::::::SMALLSPCRENT:ONEROOM', 
        'rentPriceMin': str(rP_m),  #최소 월세
        'rentPriceMax': str(rP_M), #최대 월세
        'priceMin': str(p_m), #최소 보증금
        'priceMax': str(p_M),  #최대 보증금
        'areaMin': '0',
        'areaMax': '900000000',
        'oldBuildYears': '',
        'recentlyBuildYears': '',
        'minHouseHoldCount': '',
        'maxHouseHoldCount': '',
        'showArticle': 'false',
        'sameAddressGroup': 'false',
        'minMaintenanceCost': '',
        'maxMaintenanceCost': '',
        'priceType': 'RETAIL',
        'directions': '',
        'page': str(page),
        'articleState': '',
    }

    try:
        response = requests.get(url, params=params, cookies=cookies, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

def save_to_json(all_data, filename_j):
    if not filename_j.endswith('.json'):
        filename_j = filename_j.split('.')[0] + '.json'
    try:

        with codecs.open(f'./data/{filename_j}', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        print(f"데이터가 '{filename_j}'에 JSON 형식으로 저장되었습니다.")
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생: {e}")
def save_to_csv(all_data, filename_c):
    if not filename_c.endswith('.csv'):
        filename_c = filename_c.split('.')[0] + '.csv'
    try:
        df = pd.DataFrame(all_data)
        df.to_csv(f'./data/{filename_c}', index=False, encoding='utf-8-sig')  # Excel 호환 위해 utf-8-sig 사용
        print(f"데이터가 '{filename_c}'에 CSV 형식으로 저장되었습니다.")
    except Exception as e:
        print(f"CSV 파일 저장 중 오류 발생: {e}")

@st.cache_data
def crawling(key,rP_M,rP_m,p_M,p_m):
    with open('./data/cortar.json','r',encoding='utf-8') as file:
        co_data = json.load(file)

    # #임의로 넣은 값이며 구현 때 파라미터로 메인에서 받아올 값들입니다!
    # key='서울특별시 종로구 낙원동'  #동
    # rP_M ='90'                  #최대 월세
    # rP_m = '0'                  #최소 월세
    # p_M = '500'                 #최대 보증금
    # p_m ='0'                    #최소 보증금

    cortar_no = (co_data.get(key,None)) #메인에서 받은 Key의 지역코드 반환

    filename_j = f'land_data.json'
    filename_c = f'land_data.csv'

    try:
        all_articles = []  # 전체 페이지의 데이터를 저장할 리스트

        for page in range(1, 101): # Increased page range, but will stop if no more articles
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {page}페이지 데이터 수집 중...")

            # API에서 데이터 가져오기
            data = get_real_estate_data(cortar_no,rP_M,rP_m,p_M,p_m,page)

            if data is None:
                print(f"데이터를 가져오는 데 실패했습니다. {page}페이지에서 중단합니다.")
                break

            # 페이지의 매물 목록 가져오기
            articles = data.get('articleList', [])

            # 매물이 없으면 반복 중단
            if not articles:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {page-1}페이지까지 수집 완료 (더 이상 데이터가 없습니다)")
                break

            # 전체 리스트에 추가
            all_articles.extend(articles)

            # 서버 부하를 줄이기 위한 딜레이
            time.sleep(1) # Be mindful of rate limits

        # 전체 데이터를 json로 저장
        if all_articles:
            save_to_json(all_articles, filename_j)
            save_to_csv(all_articles, filename_c)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 전체 {len(all_articles)}개의 매물 데이터가 {filename_j}, {filename_c}에 저장되었습니다.")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 수집할 매물 데이터가 없습니다.")
        return all_articles
    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")

# if __name__ == "__main__":
#     main()