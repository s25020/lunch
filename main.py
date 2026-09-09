import calendar
import datetime
import re
import urllib.parse
import requests
import streamlit as st

# 1. 페이지 설정
st.set_page_config(
    page_title="월간 학교 급식 달력", page_icon="📅", layout="wide"
)
st.title("📅 우리 학교 월간 급식 달력")
st.caption(
    "메뉴를 클릭하면 상세 조리법과 레시피를 확인하고, 하단에서 상세 영양정보를 확인하실 수 있습니다."
)

# 2. 알레르기 식품 매핑 정보
ALLERGY_MAP = {
    1: "난류",
    2: "우유",
    3: "메밀",
    4: "땅콩",
    5: "대두",
    6: "밀",
    7: "고등어",
    8: "게",
    9: "새우",
    10: "돼지고기",
    11: "복숭아",
    12: "토마토",
    13: "아황산류",
    14: "호두",
    15: "닭고기",
    16: "쇠고기",
    17: "오징어",
    18: "조개류(굴/전복/홍합 포함)",
    19: "잣",
}


def get_clean_dish_name(dish_text):
  """알레르기 번호 및 특수문자를 제거한 순수 요리명 추출"""
  cleaned = re.sub(r"\(?(\d+\.)+\)?", "", dish_text)
  return cleaned.strip()


def replace_allergy_codes(dish_text, convert_to_text=True):
  """메뉴명 뒤의 알레르기 번호를 한글 식재료명으로 치환"""
  if not convert_to_text or not dish_text:
    return dish_text

  def convert_match(match):
    raw = match.group(0)
    nums = re.findall(r"\d+", raw)
    allergens = [ALLERGY_MAP[int(n)] for n in nums if int(n) in ALLERGY_MAP]
    if allergens:
      return f" <span style='color: #e65100; font-size: 0.82em; font-weight: 600;'>[{', '.join(allergens)}]</span>"
    return raw

  pattern = r"\(?(\d+\.)+\)?"
  return re.sub(pattern, convert_match, dish_text)


# 3. 사이드바 설정
st.sidebar.header("⚙️ 학교 정보 설정")
office_code = st.sidebar.text_input(
    "시도교육청코드",
    value="T10",
    help="기본값: 제주특별자치도교육청(T10)",
)
school_code = st.sidebar.text_input(
    "표준학교코드",
    value="9290088",
    help="기본값: 제주중앙고등학교(9290088)",
)

st.sidebar.markdown("---")
st.sidebar.subheader("🍽️ 알레르기 표시 설정")
show_allergen_names = st.sidebar.toggle(
    "알레르기 식품명으로 변환", value=True
)

# 4. 상단 필터 옵션
today = datetime.date.today()
col_y, col_m, col_filter = st.columns([1, 1, 2])
with col_y:
  year = st.selectbox(
      "연도 선택",
      options=list(range(today.year - 1, today.year + 2)),
      index=1,
  )
with col_m:
  month = st.selectbox(
      "월 선택", options=list(range(1, 13)), index=today.month - 1
  )
with col_filter:
  meal_filter = st.radio(
      "급식 종류 선택",
      options=["전체 보기", "중식만 보기", "석식만 보기"],
      index=0,
      horizontal=True,
  )


# 5. API 조회 함수 (@st.cache_data 사용)
@st.cache_data(ttl=3600)
def fetch_monthly_meals(key, ofcdc_code, schul_code, yr, mo):
  _, last_day = calendar.monthrange(yr, mo)
  from_ymd = f"{yr}{mo:02d}01"
  to_ymd = f"{yr}{mo:02d}{last_day:02d}"

  url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
  params = {
      "KEY": key,
      "Type": "json",
      "pIndex": 1,
      "pSize": 100,
      "ATPT_OFCDC_SC_CODE": ofcdc_code,
      "SD_SCHUL_CODE": schul_code,
      "MLSV_FROM_YMD": from_ymd,
      "MLSV_TO_YMD": to_ymd,
  }
  response = requests.get(url, params=params, timeout=7)
  return response.json()


if "NEIS_KEY" not in st.secrets:
  st.error("⚠️ Streamlit Secrets에 `NEIS_KEY`가 설정되어 있지 않습니다.")
  st.stop()

neis_key = st.secrets["NEIS_KEY"]


# 6. 개별 메뉴 팝오버 렌더링 함수
def render_dish_popover(dish_raw):
  clean_name = get_clean_dish_name(dish_raw)
  formatted_dish = replace_allergy_codes(
      dish_raw, convert_to_text=show_allergen_names
  )

  with st.popover(f"• {clean_name}", use_container_width=True):
    st.markdown(f"### 🍳 **{clean_name}**")
    st.caption(f"원문 명칭: {formatted_dish}")
    st.markdown("---")

    encoded_query = urllib.parse.quote(f"{clean_name} 레시피 만드는 법")
    yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    naver_url = f"https://search.naver.com/search.naver?query={encoded_query}"

    st.markdown("**🔍 상세 조리법 검색하기**")
    st.link_button(
        "📺 유튜브 영상 레시피 보기", yt_url, use_container_width=True
    )
    st.link_button(
        "🟢 네이버 블로그 레시피 보기", naver_url, use_container_width=True
    )

    st.markdown("---")
    st.markdown("**💡 기본 조리 가이드**")
    st.markdown(
        f"1. **재료 준비**: {clean_name}의 주재료를 세척 및 손질합니다.\n"
        "2. **양념/육수 준비**: 메뉴에 맞는 양념장이나 육수를 베이스로 준비합니다.\n"
        "3. **가열 조리**: 대용량 급식 기준 조리법을 가정용으로 비율 조정하여 조리합니다."
    )


# 🔥 7. 식사(중식/석식) 및 영양정보 출력 렌더링 함수
def render_meal_block(meal_type_name, meal_info, icon, color):
  dishes = meal_info.get("dishes", [])
  cal_info = meal_info.get("cal", "")
  ntr_info = meal_info.get("ntr", "")

  # 열량(칼로리) 표시 텍스트 생성
  cal_text = (
      f" <span style='font-size:0.82em; color:#666;'>({cal_info})</span>"
      if cal_info
      else ""
  )
  st.markdown(
      f":{color}[**{icon} {meal_type_name}**]{cal_text}", unsafe_allow_html=True
  )

  # 메뉴 목록 표시
  for dish in dishes:
    render_dish_popover(dish)

  # 상세 영양성분 표시 (Expander)
  if ntr_info:
    with st.expander(f"📊 {meal_type_name} 영양정보"):
      # 나이스 영양성분 텍스트 파싱 (<br/> 분리)
      ntr_items = [
          item.strip()
          for item in ntr_info.replace("<br/>", "\n").split("\n")
          if item.strip()
      ]
      for item in ntr_items:
        st.caption(f"• {item}")


# 8. 급식 데이터 파싱 및 출력
try:
  with st.spinner(f"{year}년 {month}월 급식 정보를 불러오는 중..."):
    res_data = fetch_monthly_meals(
        neis_key, office_code, school_code, year, month
    )

  meal_dict = {}

  if "mealServiceDietInfo" in res_data:
    rows = res_data["mealServiceDietInfo"][1]["row"]
    for row in rows:
      ymd = row.get("MLSV_YMD")
      meal_type = row.get("MMEAL_SC_NM", "급식")
      dish = row.get("DDISH_NM", "")
      cal = row.get("CAL_INFO", "")  # 열량 정보 (예: 750.5 Kcal)
      ntr = row.get("NTR_INFO", "")  # 영양성분 정보

      dish_lines = [
          d.strip()
          for d in dish.replace("<br/>", "\n").split("\n")
          if d.strip()
      ]

      # 🔥 메뉴, 칼로리, 영양정보를 딕셔너리로 저장
      meal_dict.setdefault(ymd, {})[meal_type] = {
          "dishes": dish_lines,
          "cal": cal,
          "ntr": ntr,
      }

  month_cal = calendar.monthcalendar(year, month)
  weekdays_kr = ["월", "화", "수", "목", "금"]

  st.markdown("---")

  # 요일 헤더
  header_cols = st.columns(5)
  for idx, w_name in enumerate(weekdays_kr):
    header_cols[idx].markdown(
        f"<h4 style='text-align: center;'>{w_name}</h4>", unsafe_allow_html=True
    )

  # 달력 출력
  for week in month_cal:
    if not any(week[:5]):
      continue

    cols = st.columns(5)

    for i in range(5):
      day = week[i]
      with cols[i]:
        if day == 0:
          st.empty()
        else:
          ymd_str = f"{year}{month:02d}{day:02d}"
          day_meals = meal_dict.get(ymd_str, {})
          is_today = (
              year == today.year and month == today.month and day == today.day
          )

          with st.container(border=True):
            if is_today:
              st.markdown(
                  f"**{month}월 {day}일 ({weekdays_kr[i]})**"
                  " :orange-background[**TODAY**]"
              )
            else:
              st.markdown(f"**{month}월 {day}일 ({weekdays_kr[i]})**")

            st.divider()

            if not day_meals:
              st.caption("급식 없음 (휴업/방학)")
            else:
              # 중식 출력
              if (
                  meal_filter in ["전체 보기", "중식만 보기"]
                  and "중식" in day_meals
              ):
                render_meal_block(
                    "중식", day_meals["중식"], icon="🍚", color="blue"
                )

              # 석식 출력
              if (
                  meal_filter in ["전체 보기", "석식만 보기"]
                  and "석식" in day_meals
              ):
                if meal_filter == "전체 보기" and "중식" in day_meals:
                  st.write("")
                render_meal_block(
                    "석식", day_meals["석식"], icon="🌙", color="red"
                )

              # 기타 식사(조식 등) 출력
              if meal_filter == "전체 보기":
                for m_type, m_info in day_meals.items():
                  if m_type not in ["중식", "석식"]:
                    st.write("")
                    render_meal_block(
                        m_type, m_info, icon="🍴", color="green"
                    )

except Exception as e:
  st.error(f"⚠️ 오류가 발생했습니다: {e}")
