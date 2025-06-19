import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self, file):
        self.df = pd.read_csv(file)
        self.clean_data()

    def clean_data(self):
        self.df.replace('-', 0, inplace=True)
        self.df[['인구', '출생아수(명)', '사망자수(명)']] = self.df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)
        self.df.fillna(0, inplace=True)

    def show(self):
        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        with tabs[0]:
            st.subheader("📊 기본 통계 및 구조")
            st.write("데이터프레임 정보:")
            buffer = self.df.info(buf=None)
            st.text(str(buffer))
            st.write("기술 통계:")
            st.write(self.df.describe())

        with tabs[1]:
            st.subheader("📈 전체 인구 연도별 추이")
            national = self.df[self.df['지역'] == '전국']
            fig, ax = plt.subplots()
            ax.plot(national['연도'], national['인구'], marker='o', label='Actual')

            # 미래 인구 예측 (단순 선형 추정)
            recent = national.tail(3)
            mean_births = recent['출생아수(명)'].mean()
            mean_deaths = recent['사망자수(명)'].mean()
            projected_growth = mean_births - mean_deaths
            pop_2035 = national['인구'].iloc[-1] + projected_growth * (2035 - national['연도'].iloc[-1])
            ax.plot(list(national['연도']) + [2035], list(national['인구']) + [pop_2035], linestyle='--', marker='x', color='red', label='Projected')

            ax.set_title('Population Trend')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend()
            st.pyplot(fig)

        with tabs[2]:
            st.subheader("📍 최근 5년간 지역별 인구 변화")
            latest_year = self.df['연도'].max()
            past_year = latest_year - 5

            pop_change = self.df[self.df['연도'].isin([past_year, latest_year])]
            pivot = pop_change.pivot(index='지역', columns='연도', values='인구')
            pivot['Change'] = pivot[latest_year] - pivot[past_year]
            pivot['Rate'] = ((pivot['Change'] / pivot[past_year]) * 100).round(2)
            pivot = pivot.drop(index='전국').sort_values('Change', ascending=False)

            # 지역명을 영어로 변환 (예시용 매핑)
            region_map = {region: f"Region_{i}" for i, region in enumerate(pivot.index)}
            pivot['Region'] = pivot.index.map(region_map)

            fig, ax = plt.subplots(figsize=(8, 6))
            sns.barplot(y='Region', x='Change', data=pivot, ax=ax, palette='viridis')
            ax.set_title('Population Change (5 years)')
            ax.set_xlabel('Change (in thousands)')
            ax.set_ylabel('')
            for i, v in enumerate(pivot['Change']):
                ax.text(v, i, f'{int(v / 1000)}K', color='black', va='center')
            st.pyplot(fig)

            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(y='Region', x='Rate', data=pivot, ax=ax2, palette='coolwarm')
            ax2.set_title('Population Growth Rate (%)')
            ax2.set_xlabel('Growth Rate')
            ax2.set_ylabel('')
            for i, v in enumerate(pivot['Rate']):
                ax2.text(v, i, f'{v:.1f}%', color='black', va='center')
            st.pyplot(fig2)

            st.markdown("**Interpretation:** These graphs show the absolute and percentage population changes by region over the past 5 years.")

        with tabs[3]:
            st.subheader("📈 연도별 지역 인구 증감 Top 100")
            df_diff = self.df.copy()
            df_diff['Change'] = df_diff.sort_values(['지역', '연도']).groupby('지역')['인구'].diff()
            top100 = df_diff[df_diff['지역'] != '전국'].sort_values('Change', ascending=False).head(100)
            top100_display = top100[['연도', '지역', 'Change']].copy()
            top100_display['Change'] = top100_display['Change'].apply(lambda x: f"{int(x):,}")
            st.dataframe(
                top100_display.style.background_gradient(
                    subset=['Change'], cmap='RdBu', axis=0
                )
            )

        with tabs[4]:
            st.subheader("📊 누적 영역 그래프 (지역별 연도별 인구)")
            pivot_area = self.df.pivot(index='연도', columns='지역', values='인구').fillna(0)
            pivot_area = pivot_area.drop(columns='전국', errors='ignore')
            region_map = {region: f"Region_{i}" for i, region in enumerate(pivot_area.columns)}
            pivot_area.rename(columns=region_map, inplace=True)

            fig, ax = plt.subplots(figsize=(10, 6))
            pivot_area.div(1000).plot.area(ax=ax, cmap='tab20')
            ax.set_title('Population by Region (Cumulative)')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population (Thousands)')
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()