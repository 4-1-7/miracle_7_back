from selenium import webdriver
from bs4 import BeautifulSoup

# 전예진
def get_distance_duration(transportation, origin, destination):
    '''
    transportation: 이동수단(자동차, 도보, 대중교통, 자전거 중 택1)
    origin: 출발지(articleName, latitude, longitude) (ex)'송파파크하비오푸르지오', 37.481453, 127.123735
    destination: 목적지(articleName, latitude, longitude) (ex) ('카카오판교아지트',37.3952969470752,127.110449292622)
    '''

    o_name, o_x, o_y = origin
    d_name, d_x, d_y = destination

    url = f"https://map.kakao.com/link/by/{transportation}/{o_name},{o_x},{o_y}/{d_name},{d_x},{d_y}"
    driver = webdriver.Chrome()  # 드라이버 경로
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html,'html.parser')

    # 대중교통
    if transportation == 'traffic':
        li_tag = soup.select_one("ul li.TransitRouteItem")
        div_tag = li_tag.select_one("div.title") if li_tag else exit()
        if div_tag:
            # 시간
            duration = div_tag.select_one("span.time span.num").text.strip()
            time_unit = div_tag.select_one("span.time span.minitueTxt").text.strip()
            duration = f"{duration+time_unit}"
            # 거리
            span_tags = div_tag.select("span.walkTime span.num")
            distance = span_tags[-1].text.strip()
    # 자동차, 도보, 자전거
    elif transportation in ['car', 'walk', 'bicycle']:
        p_tag = soup.select("p.header")
        if p_tag:
        # 거리
            span_tag = p_tag[0].select_one("span.distance")
            distance = span_tag.text.strip()
            # 시간
            span_tag2 = p_tag[0].select_one("span.time")
            duration = span_tag2.text.strip()
    # 그외
    else:
        driver.quit()
        print('잘못된 이동수단입니다. 다시 입력해 주세요!')
        exit()

    driver.quit()

    return distance, duration