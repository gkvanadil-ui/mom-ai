import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import openai

# 1. 페이지 설정 (화면을 넓게 써서 칸이 깨지지 않게 합니다)
st.set_page_config(page_title="모그 AI 비서", layout="wide", page_icon="🌸")

# --- ✨ UI 스타일: 엄마를 위한 큰 글씨와 명확한 칸 분리 ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { background-color: #FCF9F6; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 입력창 제목(라벨) 크기 */
    label p { font-size: 20px !important; font-weight: bold !important; color: #8D6E63 !important; }
    
    /* 입력창 내부 디자인 */
    .stTextInput input, .stTextArea textarea { 
        font-size: 19px !important; 
        border-radius: 12px !important; 
        border: 2px solid #D7CCC8 !important; 
        padding: 15px !important; 
    }
    
    /* 버튼 스타일 */
    .stButton>button { 
        width: 100%; border-radius: 15px; height: 3.8em; 
        background-color: #8D6E63 !important; color: white !important; 
        font-weight: bold; font-size: 19px !important; 
    }
    
    h1 { color: #8D6E63 !important; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 필수 설정 및 연결
api_key = st.secrets.get("OPENAI_API_KEY")

# ⭐ 따님, 여기에 구글 시트 링크를 꼭 넣어주세요!
SHEET_URL = "https://docs.google.com/spreadsheets/d/1tz4pYbxyV8PojkzYtPz82OhiAGD2XoWVZqlTpwAebaA/edit?usp=sharing"

try:
    # 시트 연결 객체 생성
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("구글 시트 연결 설정에 문제가 있어요🌸")

# 데이터 보관함 초기화 (변수명 충돌 방지)
if 'texts' not in st.session_state: st.session_state.texts = {"인스타": "", "아이디어스": "", "스토어": ""}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'm_name' not in st.session_state: st.session_state.m_name = ""
if 'm_mat' not in st.session_state: st.session_state.m_mat = ""
if 'm_per' not in st.session_state: st.session_state.m_per = ""
if 'm_tar' not in st.session_state: st.session_state.m_tar = ""
if 'm_det' not in st.session_state: st.session_state.m_det = ""

# --- 3. 메인 화면: 상세 입력 섹션 (칸 분리) ---
st.title("🌸 모그 작가님 AI 비서")
st.header("1️⃣ 작품 정보를 채워주세요")

# 한 줄에 두 개씩, 큼직하게 나눕니다.
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.session_state.m_name = st.text_input("📦 작품 이름", value=st.session_state.m_name, placeholder="예: 빈티지 튤립 뜨개 파우치")
    st.session_state.m_mat = st.text_input("🧵 사용한 소재", value=st.session_state.m_mat, placeholder="예: 순면사, 린넨 안감")
with row1_col2:
    st.session_state.m_per = st.text_input("⏳ 제작 소요 기간", value=st.session_state.m_per, placeholder="예: 주문 확인 후 3일 이내")
    st.session_state.m_tar = st.text_input("🎁 추천 선물 대상", value=st.session_state.m_tar, placeholder="예: 생일 선물, 나를 위한 선물")

# 상세 설명은 아래에 넓게 배치
st.session_state.m_det = st.text_area("✨ 정성 포인트와 상세 설명", value=st.session_state.m_det, height=200, placeholder="작가님의 정성이 들어간 이야기를 자유롭게 적어주세요.")

st.divider()

# --- 4. 기능 탭 구역 ---
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진 보정법", "💬 고민 상담소", "📂 작품 창고"])

def process_ai(guide):
    if not api_key: return "API 키가 없어요🌸"
    client = openai.OpenAI(api_key=api_key)
    info = f"이름:{st.session_state.m_name}, 소재:{st.session_state.m_mat}, 기간:{st.session_state.m_per}, 대상:{st.session_state.m_tar}, 설명:{st.session_state.m_det}"
    prompt = f"당신은 작가 모그입니다. 다정하게 {guide['name']} 판매글을 작성하세요. 특수기호 ** 금지. [정보] {info} [지침] {guide['desc']}"
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except: return "연결이 잠시 끊겼어요🌸"

with tabs[0]: # 판매글 쓰기
    st.write("#### 💡 아래 버튼을 누르면 글이 완성됩니다.")
    c1, c2, c3 = st.columns(3)
    if c1.button("📸 인스타그램"): st.session_state.texts["인스타"] = process_ai({"name": "인스타그램", "desc": "감성 일기 스타일"})
    if c2.button("🎨 아이디어스"): st.session_state.texts["아이디어스"] = process_ai({"name": "아이디어스", "desc": "정성 강조 스타일"})
    if c3.button("🛍️ 스토어"): st.session_state.texts["스토어"] = process_ai({"name": "스마트스토어", "desc": "정보 안내 스타일"})
    
    for k in ["인스타", "아이디어스", "스토어"]:
        if st.session_state.texts.get(k):
            st.info(f"📍 {k} 글이 완성되었어요^^")
            st.text_area(f"{k} 내용", value=st.session_state.texts[k], height=250, key=f"t_{k}")

with tabs[1]: # 사진 보정
    st.markdown("### 📸 사진 보정법 가이드")
    st.success("**네이버 스마트스토어 편집기**: 사진 올리고 [편집] - [자동보정] 클릭!")
    st.info("**포토(Fotor)**: [AI 원클릭 보정] 버튼 하나로 밝기 조절 끝!")
    st.link_button("👉 포토(Fotor) 바로가기", "https://www.fotor.com/kr/photo-editor-app/editor/basic")

with tabs[2]: # 상담소
    st.header("💬 작가님 고민 상담소")
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"], avatar="🌸" if m["role"]=="user" else "🕯️"): st.write(m["content"])
    if pr := st.chat_input("작가님, 무엇이든 물어보세요..."):
        st.session_state.chat_history.append({"role": "user", "content": pr})
        st.rerun()

with tabs[3]: # 창고 (구글 시트 연동)
    st.header("📂 나의 영구 작품 창고")
    try:
        # SHEET_URL을 명시하여 Spreadsheet must be specified 오류 해결
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        
        if st.button("✨ 지금 입력한 정보 창고에 저장하기"):
            new_row = pd.DataFrame([{"name":st.session_state.m_name, "material":st.session_state.m_mat, "period":st.session_state.m_per, "target":st.session_state.m_tar, "keys":st.session_state.m_det}])
            conn.update(spreadsheet=SHEET_URL, data=pd.concat([df, new_row], ignore_index=True))
            st.success("안전하게 저장되었습니다! 🌸")
            st.rerun()
            
        st.divider()
        for i, r in df.iterrows():
            with st.expander(f"📦 {r['name']}"):
                st.write(f"소재: {r['material']} | 제작기간: {r['period']}")
                if st.button("📥 이 정보 다시 불러오기", key=f"l_{i}"):
                    st.session_state.m_name, st.session_state.m_mat = r['name'], r['material']
                    st.session_state.m_per, st.session_state.m_tar = r['period'], r['target']
                    st.session_state.m_det = r['keys']
                    st.rerun()
    except Exception:
        st.warning("구글 시트 설정을 확인해 주세요! 🌸")
