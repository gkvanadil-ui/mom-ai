import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import openai

# 1. 페이지 설정 (가장 먼저 실행되어야 합니다)
st.set_page_config(page_title="모그 AI 비서", layout="centered", page_icon="🌸")

# --- ✨ UI/UX: 엄마를 위한 따뜻하고 큰 글씨 스타일 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FCF9F6;
        font-family: 'Noto Sans KR', sans-serif;
        color: #4A3E3E;
    }
    h1, h2, h3 { color: #8D6E63 !important; font-weight: 700 !important; }
    .stButton>button {
        width: 100%; border-radius: 20px; height: 3.5em;
        background-color: #8D6E63 !important; color: white !important;
        font-weight: bold; font-size: 18px !important; border: none;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .stTextInput input, .stTextArea textarea {
        font-size: 18px !important; border-radius: 12px !important;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 연결 설정
api_key = st.secrets.get("OPENAI_API_KEY")
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 보관함(세션 상태) 초기화
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'refined' not in st.session_state: st.session_state.refined = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'name' not in st.session_state: st.session_state.name = ""
if 'keys' not in st.session_state: st.session_state.keys = ""

# --- [도우미 함수들] ---
def process_mog_ai(guide):
    if not api_key: return "API 키를 확인해주세요🌸"
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""
    당신은 핸드메이드 브랜드 '모그(Mog)' 작가입니다. 50대 여성 작가의 다정하고 따뜻한 말투(~이지요^^, ~해요)로 작성하세요.
    별표(*)나 볼드체(**)는 절대 쓰지 마세요.
    [플랫폼] {guide['name']} 
    [지침] {guide['desc']}
    [정보] 작품명: {st.session_state.name} / 특징: {st.session_state.keys}
    """
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "잠시 오류가 생겼어요🌸"

def load_gs_data():
    try: return conn.read(ttl=0)
    except: return pd.DataFrame(columns=["name", "keys"])

# --- 4. 메인 화면 구성 ---
st.title("🌸 모그 작가님 AI 비서")
st.write("### 오늘도 정성 가득한 하루 보내셔요 작가님! ✨")

# [1구역] 정보 입력 (공통 정보)
with st.container():
    st.header("1️⃣ 어떤 작품인가요?")
    st.session_state.name = st.text_input("📦 작품 이름", value=st.session_state.name, placeholder="예: 빈티지 튤립 파우치")
    st.session_state.keys = st.text_area("🔑 정성 포인트", value=st.session_state.keys, placeholder="예: 직접 뜬 꽃무늬가 화사해요.")

st.divider()

# ⭐⭐⭐ [핵심] 탭을 여기서 먼저 정의합니다! ⭐⭐⭐
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 영구 작품 창고"])

# --- Tab 1: 판매글 쓰기 ---
with tabs[0]:
    st.write("#### 💡 버튼을 누르면 작가님 말투로 글이 써집니다.")
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"):
        st.session_state.texts["인스타"] = process_mog_ai({"name": "인스타그램", "desc": "감성 일기 스타일, 해시태그 포함"})
        st.session_state.refined["인스타"] = ""
    if c2.button("🎨 아이디어스"):
        st.session_state.texts["아이디어스"] = process_mog_ai({"name": "아이디어스", "desc": "정성을 강조하는 스타일"})
        st.session_state.refined["아이디어스"] = ""
    if c3.button("🛍️ 스토어"):
        st.session_state.texts["스토어"] = process_mog_ai({"name": "스마트스토어", "desc": "다정한 정보 안내"})
        st.session_state.refined["스토어"] = ""

    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.info(f"📍 {k} 첫 번째 글")
            st.text_area(f"{k} 원본", value=st.session_state.texts[k], height=200, key=f"orig_{k}")
            with st.expander("✨ 글을 다르게 고쳐볼까요?"):
                feed = st.text_input("요청사항", key=f"f_{k}")
                if st.button("♻️ 다시 정성껏 쓰기", key=f"re_{k}"):
                    st.session_state.refined[k] = process_mog_ai({"name": k, "desc": f"원래 글: {st.session_state.texts[k]}\n요청: {feed}"})
                    st.rerun()
            if st.session_state.refined.get(k):
                st.success("✨ 새로 작성한 글입니다!")
                st.text_area(f"{k} 수정본", value=st.session_state.refined[k], height=250, key=f"new_{k}")

# --- Tab 2: 사진 보정법 ---
with tabs[1]:
    st.header("📸 사진 보정, 이것만 기억하세요!")
    st.info("엄마! 버튼 하나로 사진이 화사해지는 방법이에요🌸")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 💚 네이버 편집기\n- 상품 올릴 때 **[편집]** 클릭\n- **[자동보정]**만 누르세요!")
    with col_b:
        st.markdown("#### 🪄 포토(Fotor) AI\n- 조명을 알아서 켜줘요.\n- **[AI 원클릭 보정]** 클릭!")
        st.link_button("👉 포토 사이트 바로가기", "https://www.fotor.com/kr/photo-editor-app/editor/basic")

# --- Tab 3: 고민 상담소 ---
with tabs[2]:
    st.header("💬 모그 작가님 전용 상담소")
    for m in st.session_state.chat_history:
        avatar = "🌸" if m["role"] == "user" else "🕯️"
        with st.chat_message(m["role"], avatar=avatar):
            st.write(m["content"])

    if pr := st.chat_input("작가님, 어떤 고민이 있으셔요?"):
        st.session_state.chat_history.append({"role": "user", "content": pr})
        with st.chat_message("user", avatar="🌸"):
            st.write(pr)
        with st.chat_message("assistant", avatar="🕯️"):
            with st.spinner("생각 중이지요..."):
                ans = process_mog_ai({"name": "상담소", "desc": f"이전 대화 맥락을 기억하고 현실적인 조언 제공. 질문: {pr}"})
                st.write(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
    if st.button("♻️ 대화 지우기"):
        st.session_state.chat_history = []
        st.rerun()

# --- Tab 4: 영구 작품 창고 (구글 시트 연동) ---
with tabs[3]:
    st.header("📂 나의 영구 작품 창고")
    st.write("여기 저장하면 컴퓨터를 꺼도 정보가 남아요 🕯️")
    df = load_gs_data()

    if st.button("✨ 지금 정보를 구글 시트에 저장하기"):
        if st.session_state.name:
            new_row = pd.DataFrame([{"name": st.session_state.name, "keys": st.session_state.keys}])
            if st.session_state.name in df['name'].values:
                df.loc[df['name'] == st.session_state.name, 'keys'] = st.session_state.keys
                up_df = df
            else:
                up_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=up_df)
            st.success("창고에 저장되었습니다! 🌸")
            st.rerun()
        else:
            st.warning("이름을 적어주세요.")

    st.divider()
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"📦 {row['name']}"):
                st.write(row['keys'])
                c1, c2 = st.columns(2)
                if c1.button("📥 불러오기", key=f"gs_l_{i}"):
                    st.session_state.name = row['name']
                    st.session_state.keys = row['keys']
                    st.rerun()
                if c2.button("🗑️ 삭제", key=f"gs_d_{i}"):
                    conn.update(data=df.drop(i))
                    st.rerun()
