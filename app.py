import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 기기 식별 로직 (우선순위 재정립)
# ==========================================
# 지침: session_state -> query_params -> 생성 순서 엄수

# 1단계: 세션 스테이트 확인 (가장 빠르고 확실함)
if "device_id" in st.session_state:
    device_id = st.session_state["device_id"]
else:
    # 2단계: 세션에 없으면 URL 파라미터 확인 (보조 수단)
    found_id = None
    try:
        # Streamlit 최신 버전 대응
        qp = st.query_params
        val = qp.get("device_id")
        if val:
            found_id = val if isinstance(val, str) else val[0]
    except:
        # 구버전 대응
        try:
            qp = st.experimental_get_query_params()
            if "device_id" in qp:
                found_id = qp["device_id"][0]
        except:
            pass
            
    if found_id:
        # URL에서 찾았으면 세션에 즉시 동기화
        st.session_state["device_id"] = found_id
        device_id = found_id
    else:
        # 3단계: 아무것도 없으면 아직 '시작 전' 상태
        device_id = None

# ==========================================
# [섹션 B] 시작 화면 (device_id가 없을 때만 진입)
# ==========================================
if device_id is None:
    st.markdown("""
    <div style='text-align: center; padding-top: 50px; padding-bottom: 20px;'>
        <h1 style='color: #FF4B4B;'>🌸 모그 작가님 AI 비서</h1>
        <p style='font-size: 1.2em; color: #555;'>
            작가님, 환영합니다.<br>
            아래 버튼을 한번만 눌러주세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # [핵심 수정] 버튼 클릭 시 로직 순서 강제
        if st.button("🚀 작가님, 여기를 눌러 시작해주세요", use_container_width=True, type="primary"):
            # 1. 고유 ID 생성
            new_id = f"mog_{str(uuid.uuid4())[:8]}"
            
            # 2. [절대 규칙] 세션 스테이트에 먼저 저장 (진실의 원천)
            st.session_state["device_id"] = new_id
            
            # 3. URL 파라미터 업데이트 (보조 - 즐겨찾기용)
            try:
                st.query_params["device_id"] = new_id
            except:
                try:
                    st.experimental_set_query_params(device_id=new_id)
                except:
                    pass
            
            # 4. 강제 리런 (이제 세션에 값이 있으므로 다음 실행 땐 이 화면을 건너뜀)
            st.rerun()

    st.markdown("""
    <div style='text-align: center; margin-top: 30px; font-size: 0.9em; color: #888;'>
        * 버튼을 누르시면 작가님만의 작업 주소가 생성됩니다.<br>
        * 생성된 주소를 <b>[즐겨찾기]</b> 해두시면 편해요.
    </div>
    """, unsafe_allow_html=True)
    
    # [중요] 안내 화면이 다 그려졌으므로 여기서 멈춤 (흰 화면 방지)
    st.stop()

# ==========================================
# [섹션 C] 메인 앱 로직 (device_id 확보 이후)
# ==========================================
# 여기 도달했다는 것은 st.session_state['device_id']가 확실히 있다는 뜻

# Firebase 연결 (ID 확보 후 안전하게 시도)
db = None
try:
    if not firebase_admin._apps:
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            st.error("🚨 Secrets 설정이 필요합니다.")
            st.stop()
        
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"서버 연결 오류: {e}")
    # DB 오류나도 UI는 띄움

# --- 데이터 처리 함수들 ---
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

# --- UI 렌더링 ---
if 'current_work' not in st.session_state: st.session_state.current_work = None
my_works = load_works()

# 사이드바
with st.sidebar:
    st.title("📂 내 작품 목록")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        uid = str(uuid.uuid4())
        empty = {"name": "", "material": "", "point": "", "texts": {}}
        st.session_state.current_work = {"work_id": uid, **empty}
        save_to_db(uid, empty)
        st.rerun()
    st.divider()
    if not my_works:
        st.caption("작품이 없습니다.")
    for w in my_works:
        if st.button(f"📦 {w.get('name') or '이름 없음'}", key=w['work_id'], use_container_width=True):
            st.session_state.current_work = w
            st.rerun()

# 메인 영역
st.title("🌸 모그 작가님 AI 비서")

if not st.session_state.current_work:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽의 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
        st.stop()

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
                if not nn: st.warning("이름을 입력해주세요")
                else:
                    with st.spinner("작성 중..."):
                        texts[k] = generate_copy(k, nn, nm, np)
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr)
                        st.rerun()
            st.text_area("결과", texts.get(k,""), height=400)
