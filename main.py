import calendar
from datetime import date
import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="우리 학교 급식 달력", layout="wide")

st.title("🍱 우리 학교 이달의 급식 달력")

# 연도 및 월 선택
today = date.today()
col_y, col_m = st.columns(2)
with col_y:
    year = st.number_input(
        "연도 선택", min_value=2020, max_value=2030, value=today.year
    )
with col_m:
    month = st.number_input(
        "월 선택", min_value=1, max_value=12, value=today.month
    )


# [데모용] 날짜별 샘플 급식 데이터 생성 함수 (실제 데이터 연동 시 API로 대체)
def get_sample_menu(day_num):
    sample_menus = [
        ["현미밥", "돈까스", "쫄면무침", "배추김치", "바나나"],
        ["비빔밥", "팽이버섯된장국", "계란후라이", "열무김치", "요구르트"],
        ["자장밥", "짬뽕국", "탕수육", "단무지", "사과"],
        ["차조밥", "쇠고기미역국", "제육볶음", "상추쌈", "포도"],
        ["카레라이스", "가쓰오장국", "치킨너겟", "깍두기", "오렌지주스"],
    ]
    return sample_menus[day_num % len(sample_menus)]


# 요일 헤더 표시
days_of_week = ["월", "화", "수", "목", "금", "토", "일"]
cols = st.columns(7)
for idx, day_name in enumerate(days_of_week):
    # 주말 구분 색상 처리
    if idx >= 5:
        cols[idx].markdown(
            f"<h4 style='text-align: center; color: gray;'>{day_name}</h4>",
            unsafe_allow_html=True,
        )
    else:
        cols[idx].markdown(
            f"<h4 style='text-align: center;'>{day_name}</h4>",
            unsafe_allow_html=True,
        )

# 달력 그리드 생성
cal = calendar.monthcalendar(year, month)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day != 0:
                with st.container(border=True):
                    # 오늘 날짜 강조 표시
                    is_today = (
                        day == today.day
                        and year == today.year
                        and month == today.month
                    )
                    if is_today:
                        st.markdown(f"### 🌟 {day}일")
                    else:
                        st.markdown(f"### {day}일")

                    # 주말 예외 처리
                    if i in [5, 6]:
                        st.caption("주말 (급식 없음)")
                    else:
                        # 급식 메뉴 출력
                        menu_list = get_sample_menu(day)
                        for item in menu_list:
                            st.write(f"• {item}")
            else:
                # 월 시작 전/후 빈 영역 처리
                st.write("")
