import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 접속 및 기기 식별 (Streamlit 네이티브 방식)
# ==========================================

# 1. URL 파라미터 확인 (버전 호환성 확보)
try:
    # Streamlit 최신 버전
    query_params = st.query_params
    # 딕셔너리처럼 동작하지만 객체일 수 있어 안전하게 접근
    device_id_val = query_params.get("device_id")
    if isinstance(device_id_val, list): # 구버전 호환
        device_id = device_id_val[0] if device_id_val else None
    else:
        device_id = device_id_val
except:
    # 아주 구버전일 경우
    try:
        qp = st.experimental_get_query_params()
        device_id = qp["device_id"][0] if "device_id" in qp else None
    except:
        device_id = None

# 2. device_id가 없는 경우 -> '시작하기' 화면 (렌더링 정지)
if not device_id:
    # 여기서 ID를 미리 생성해둡니다.
    if 'temp_new_id' not in st.session_state:
        st.session_state.temp_new_id = f"mog_{str(uuid.uuid4())[:8]}"

    # --- 랜딩 페이지 UI ---
    st.markdown("""
    <div style='text-align: center; padding-top: 50px; padding-bottom: 20px;'>
        <h1 style='color: #FF4B4B;'>🌸 모그 작가님 AI 비서</h1>
        <p style='font-size: 1.2em; color: #555;'>
            작가님, 환영합니다.<br>
            아래 버튼을 누르면 작업을 시작하실 수 있어요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 중앙 정렬을 위한 컬럼 배치
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # [핵심 수정] Streamlit 네이티브 버튼 사용
        # 이 버튼은 iframe이 아니라 앱 자체에서 작동하므로 무조건 클릭됩니다.
        if st.button("🚀 작가님, 여기를 눌러 시작해주세요", use_container_width=True, type="primary"):
            # 1. URL에 device_id 박아넣기
            new_id = st.session_state.temp_new_id
            
            try:
                # 최신 버전
                st.query_params["device_id"] = new_id
            except:
                # 구버전
                st.experimental_set_query_params(device_id=new_id)
            
            # 2. 즉시 새로고침 (이때 URL 파라미터를 물고 다시 시작함)
            st.rerun()

    # 안내 문구
    st.markdown("""
    <div style='text-align: center; margin-top: 30px; font-size: 0.9em; color: #888;'>
        * 버튼을 누르시면 작가님만의 작업 공간이 생성됩니다.<br>
        * 생성된 주소를 <b>[즐겨찾기]</b> 해두시면 내용을 계속 이어서 쓰실 수 있어요.
    </div>
    """, unsafe_allow_html=True)
    
    # ID가 없으므로 여기서 코드 실행을 멈춥니다. (흰 화면 방지용 UI가 위에 있으므로 OK)
    st.stop()


# ==========================================
# [섹션 B] 여기서부터는 device_id가 있는 상태 (메인 앱)
# ==========================================

# Firebase 연결
db = None
try:
    if not firebase_admin._apps:
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            st.error("🚨 설정(Secrets) 확인이 필요합니다.")
            st.stop()
            
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"서버 연결 중 오류가 발생했습니다: {e}")
    # DB 없이도 UI는 뜨도록 pass

# --- CRUD 함수 ---
def save_to_db(work_id, data):
    if not db: return
    try:
        doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
        doc_ref.set({
            "device_id": device_id,
            "work_id": work_id,
            "updated_at": datetime.datetime.now(),
            **data
        })
    except: pass

def load_works():
    if not db: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        return sorted([doc.to_dict() for doc in docs], key=lambda x: x.get('updated_at', datetime.datetime.min), reverse=True)
    except: return []

def delete_work(work_id):
    if not db: return
    try: db.collection("works").document(f"{device_id}_{work_id}").delete()
    except: pass

def generate_copy(platform, name, material, point):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키가 없습니다."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        base = "[규칙: 1인칭 '모그' 작가 시점] 말투: ~이지요^^, ~해요. 특수기호(*, **) 금지."
        prompts = {
            "인스타": f"{base} [인스타] 감성, 일기투, 해시태그.",
            "아이디어스": f"{base} [아이디어스] 💡상세, 🍀Info, 🔉안내, 👍🏻보증 4단락.",
            "스토어": f"{base} [스토어] 💐이름, 🌸디자인, 👜기능, 📏사이즈, 📦소재, 🧼관리, 📍추천 7단락."
        }
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":prompts.get(platform, base)}, {"role":"user","content":f"이름:{name}, 소재:{material}, 특징:{point}"}]
        )
        return res.choices[0].message.content.replace("**", "").strip()
    except Exception as e: return f"오류: {str(e)}"

# --- 메인 UI 구성 ---
if 'current_work' not in st.session_state: st.session_state.current_work = None
my_works = load_works()

with st.sidebar:
    st.title("📂 내 작품 목록")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        uid = str(uuid.uuid4())
        empty = {"name": "", "material": "", "point": "", "texts": {}}
        st.session_state.current_work = {"work_id": uid, **empty}
        save_to_db(uid, empty)
        st.rerun()
    st.divider()
    for w in my_works:
        if st.button(f"📦 {w.get('name') or '이름 없음'}", key=w['work_id'], use_container_width=True):
            st.session_state.current_work = w
            st.rerun()

st.title("🌸 모그 작가님 AI 비서")

if not st.session_state.current_work:
    if my_works: st.session_state.current_work = my_works[0]; st.rerun()
    else: st.info("👈 왼쪽 버튼을 눌러 새 작품을 만들어주세요!"); st.stop()

curr = st.session_state.current_work
c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 정보 입력")
    nn = st.text_input("작품 이름", curr.get('name',''))
    nm = st.text_input("소재", curr.get('material',''))
    np = st.text_area("특징", curr.get('point',''), height=150)
    if nn!=curr.get('name') or nm!=curr.get('material') or np!=curr.get('point'):
        curr.update({'name':nn, 'material':nm, 'point':np})
        save_to_db(curr['work_id'], curr)
    st.caption("자동 저장됨")
    if st.button("🗑️ 삭제"):
        delete_work(curr['work_id'])
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    for i, (k, n) in enumerate([("insta","인스타"), ("idus","아이디어스"), ("store","스토어")]):
        with tabs[i]:
            if st.button(f"{n} 생성", key=f"b_{k}"):
                if not nn: st.warning("이름 필요")
                else:
                    with st.spinner("작성 중..."):
                        texts[k] = generate_copy(k, nn, nm, np)
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr)
                        st.rerun()
            st.text_area("결과", texts.get(k,""), height=400)
