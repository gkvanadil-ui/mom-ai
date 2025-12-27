import streamlit as st
import openai
from PIL import Image, ImageEnhance
import io
import base64

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 엄마를 위한 다정하고 큼직한 디자인 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    label p { font-size: 22px !important; font-weight: bold !important; color: #8D6E63 !important; }
    .stTextInput input, .stTextArea textarea { font-size: 20px !important; border-radius: 12px !important; border: 2px solid #D7CCC8 !important; padding: 15px !important; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; background-color: #8D6E63 !important; color: white !important; font-weight: bold; font-size: 20px !important; }
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] button { font-size: 22px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정
api_key = st.secrets.get("OPENAI_API_KEY")

# 세션 상태 초기화
for key in ['texts', 'chat_log', 'm_name', 'm_mat', 'm_per', 'm_size', 'm_det']:
    if key not in st.session_state:
        if key == 'texts': st.session_state[key] = {"인스타": "", "아이디어스": "", "스토어": ""}
        elif key == 'chat_log': st.session_state[key] = []
        else: st.session_state[key] = ""

# --- [로직 1: AI 자동 사진 보정 엔진] ---
def ai_auto_enhance(img_file):
    client = openai.OpenAI(api_key=api_key)
    img = Image.open(img_file)
    # 3단계 실제 이미지 보정 프로세스
    img = ImageEnhance.Brightness(img).enhance(1.3)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.2)
    return img

# --- [로직 2: 모그 작가님 전용 1인칭 글쓰기 로직] ---
def ask_mog_ai(platform, user_in="", feedback=""):
    client = openai.OpenAI(api_key=api_key)
    
    # 💡 따님, "비서인 척 금지" 지시사항을 최상단에 박았습니다.
    base_style = """
    [절대 규칙: 1인칭 본인 시점]
    - 당신은 AI 비서가 아니라, 핸드메이드 작가 '모그(Mog)' 본인입니다.
    - "작가님의 이야기를 들려드릴게요" 혹은 "정보를 바탕으로 작성합니다" 같은 서두를 절대 쓰지 마세요.
    - 글의 첫 마디부터 바로 작가님의 다정한 인사로 시작하세요.
    - 모든 문장은 "내가", "나의 마음은" 등 작가 본인의 시점에서 1인칭으로 서술하세요.
    
    [어투 규칙]
    - 정체성: 50대 여성 핸드메이드 작가의 다정하고 따뜻한 마음.
    - 대표 어미: ~이지요^^, ~해요, ~좋아요, ~보내드려요 등 부드러운 말투.
    - 특수기호 금지: 별표(*)나 볼드체(**) 같은 마크다운 기호는 절대 사용 금지.
    - 감성 이모지: 꽃(🌸, 🌻), 구름(☁️), 반짝이(✨)를 과하지 않게 섞어서 사용.
    """
    
    if platform == "인스타그램":
        system_p = f"{base_style} [📸 인스타그램] 지침: 첫 줄 감성 문구, 나의 제작 일기, 상세 정보, 해시태그 10개 내외. 줄바꿈 넉넉히."
    elif platform == "아이디어스":
        system_p = f"{base_style} [🎨 아이디어스 (에세이 모드)] 지침: 작가인 '나'의 정성이 깊게 전달되도록 긴 호흡으로 작성. '한 땀 한 땀', '밤새 고민하며' 등 나의 노력을 상세하게 서술. 절대 내용을 축약하지 말 것."
    elif platform == "스마트스토어":
        system_p = f"{base_style} [🛍️ 스마트스토어 (상세 양식)] 지침: 작가 본인이 직접 설명하듯 다정하고 길게 작성.
        구성 형식:
        💐 [상품명]
        ⸻
        [작가 본인의 감성적인 소개글]
        ⸻
        🌸 디자인 & 특징 (나의 정성이 담긴 포인트 설명)
        👜 기능성 & 내구성 (내가 어떻게 튼튼하게 만들었는지 설명)
        📏 사이즈 (±1~2cm 오차)
        📦 소재 (내가 고른 따뜻한 소재 설명)
        🧼 관리 방법 (오래 써주길 바라는 나의 마음을 담은 가이드)
        ⸻
        📍 이런 분께 추천 (나의 작품이 어울릴 것 같은 분들)
        ⸻
        #[해시태그]"
    elif platform == "상담":
        system_p = f"{base_style} [💬 상담소] 든든한 선배 작가 본인이 되어 동료에게 공감하고 실질적인 조언을 건네주세요."

    if feedback:
        u_content = f"내가 쓴 기존 글: {user_in}\n\n나의 수정 요청: {feedback}\n\n위 요청을 반영해서 내용을 더 풍성하고 다정하게 다시 써주셔요🌸"
    else:
        info = f"작품명:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 사이즈:{st.session_state.m_size}, 나의 정성 포인트:{st.session_state.m_det}"
        u_content = f"정보: {info} / {user_in}"

    res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":system_p},{"role":"user","content":u_content}])
    return res.choices[0].message.content.replace("**", "").replace("*", "").strip()

# --- 3. 메인 화면 ---
st.title("🌸 모그 작가님 AI 비서 🌸")
st.header("1️⃣ 작품 정보를 입력해주세요")

c1, c2 = st.columns(2)
with c1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name)
    st.session_state.m_mat = st.text_input("🧵 소재", value=st.session_state.m_mat)
with c2:
    st.session_state.m_per = st.text_input("⏳ 제작 기간", value=st.session_state.m_per)
    st.session_state.m_size = st.text_input("📏 사이즈", value=st.session_state.m_size)
st.session_state.m_det = st.text_area("✨ 정성 포인트와 설명", value=st.session_state.m_det, height=150)

st.divider()

# --- 4. 기능 탭 (저장 기능 완전 삭제) ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 AI 자동 사진 보정", "💬 고민 상담소"])

with tabs[0]: 
    sc1, sc2, sc3 = st.columns(3)
    if sc1.button("📸 인스타그램"): st.session_state.texts["인스타"] = ask_mog_ai("인스타그램")
    if sc2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = ask_mog_ai("아이디어스")
    if sc3.button("🛍️ 스마트스토어"): st.session_state.texts["스토어"] = ask_mog_ai("스마트스토어")
    
    for k, v in st.session_state.texts.items():
        if v:
            st.markdown(f"### ✨ 완성된 {k} 글")
            st.text_area(f"{k} 결과", value=v, height=600, key=f"area_{k}")
            feed = st.text_input(f"✍️ {k} 글에서 수정하고 싶은 부분이 있으신가요?", key=f"feed_{k}")
            if st.button(f"🚀 {k} 글 다시 수정하기", key=f"btn_{k}"):
                with st.spinner("작가님의 마음을 담아 다시 고치는 중이에요..."):
                    st.session_state.texts[k] = ask_mog_ai(k, user_in=v, feedback=feed)
                    st.rerun()

with tabs[1]: 
    st.header("📸 AI 자동 사진 보정")
    up_img = st.file_uploader("사진을 올려주시면 AI가 화사하게 직접 보정해드릴게요 🌸", type=["jpg", "png", "jpeg"])
    if up_img and st.button("✨ 보정 시작하기"):
        with st.spinner("작품을 화사하게 만드는 중이에요..."):
            e_img = ai_auto_enhance(up_img)
            col1, col2 = st.columns(2)
            col1.image(up_img, caption="보정 전")
            col2.image(e_img, caption="AI 보정 결과")
            buf = io.BytesIO(); e_img.save(buf, format="JPEG")
            st.download_button("📥 저장", buf.getvalue(), "mogs_fixed.jpg", "image/jpeg")

with tabs[2]: 
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_log:
        with st.chat_message(m["role"]): st.write(m["content"])
    if pr := st.chat_input("작가님, 어떤 고민이 있으신가요?"):
        st.session_state.chat_log.append({"role": "user", "content": pr})
        st.session_state.chat_log.append({"role": "assistant", "content": ask_mog_ai("상담", user_in=pr)})
        st.rerun()
