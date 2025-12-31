import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import streamlit.components.v1 as components

# ==========================================
# [섹션 0] 무조건 렌더링 (흰 화면 방지 최우선)
# ==========================================
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# 제목은 무슨 일이 있어도 먼저 보여줍니다.
st.title("🌸 모그 작가님 AI 비서")

# ==========================================
# [섹션 A] 안전한 기기 식별 (2단계 진입 방식)
# ==========================================

# 1. Query Params 안전하게 가져오기 (버전 호환성)
try:
    # Streamlit 최신 버전
    query_params = st.query_params
except AttributeError:
    try:
        # 구버전
        query_params = st.experimental_get_query_params()
    except:
        query_params = {}

# 2. device_id 추출 및 검증 (문자열만 허용)
device_id = None
raw_id = query_params.get("device_id", None)

if raw_id:
    if isinstance(raw_id, list) and len(raw_id) > 0:
        device_id = raw_id[0] # 리스트인 경우 첫 번째
    elif isinstance(raw_id, str) and raw_id.strip() != "":
        device_id = raw_id    # 문자열인 경우 그대로

# 3. ID가 없을 경우: 절대 자동 리로드 하지 않음 -> 안내 UI 출력 후 사용자 클릭 유도
if not device_id:
    st.info("작가님의 작업 환경을 확인하고 있습니다... 아래 버튼을 눌러주세요.")
    
    # JS: 로컬스토리지에서 ID를 찾거나 만들어서 -> '버튼'의 링크에 심어줌 (자동 리로드 X)
    # 이 방식은 무한 루프를 원천 차단합니다.
    manual_entry_html = """
    <div id="entry_area" style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; text-align: center; background-color: #f9f9f9;">
        <p style="margin-bottom: 15px; font-weight: bold; color: #555;">이전에 쓰시던 기록을 불러옵니다.</p>
        <a id="connect_btn" href="#" target="_self" style="
            display: inline-block; 
            text-decoration: none;
            background-color: #FF4B4B; 
            color: white; 
            padding: 15px 30px; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: background-color 0.3s;">
            🚀 작가님, 여기를 눌러 시작해주세요
        </a>
    </div>

    <script>
        try {
            // 1. 로컬 스토리지 확인
            let myId = localStorage.getItem('mog_device_id');
            
            // 2. 없으면 새로 생성 (하지만 아직 이동 안함)
            if (!myId) {
                myId = 'mog_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('mog_device_id', myId);
            }
            
            // 3. 현재 URL에 ID를 붙여서 버튼 링크 완성
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('device_id', myId);
            
            const btn = document.getElementById('connect_btn');
            btn.href = currentUrl.toString();
            
        } catch(e) {
            console.error("ID Setup Error:", e);
            document.getElementById('entry_area').innerText = "브라우저 오류가 발생했습니다. 새로고침 해주세요.";
        }
    </script>
    """
    components.html(manual_entry_html, height=200)
    
    # [중요] UI가 다 그려진 후에 stop을 겁니다. 흰 화면 방지.
    st.stop()

# ==========================================
# [섹션 B] Firebase & Backend 안전 연결
# ==========================================

db = None
try:
    if not firebase_admin._apps:
        # Secrets 확인
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            st.error("🚨 설정(Secrets)에 'FIREBASE_SERVICE_ACCOUNT'가 없습니다.")
            st.stop()
            
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
except Exception as e:
    # DB 실패해도 앱 전체가 죽지 않도록 방어
    st.error(f"⚠️ 데이터베이스 연결에 실패했습니다. 하지만 앱은 계속 켜둡니다.")
    st.code(str(e))
    # db가 None인 상태로 아래 로직이 흘러가게 둠 (CRUD 함수에서 방어)

# ==========================================
# [섹션 C] 데이터 관리 함수 (방어 코드 적용)
# ==========================================

def save_to_db(work_id, data):
    if db is None: return # DB 없으면 조용히 리턴
    try:
        doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
        final_data = {
            "device_id": device_id,
            "work_id": work_id,
            "updated_at": datetime.datetime.now(),
            **data
        }
        doc_ref.set(final_data)
    except Exception as e:
        st.toast(f"저장 실패: {e}") # 사용자 흐름 방해 안 함

def load_works():
    if db is None: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        works_list = []
        for doc in docs:
            works_list.append(doc.to_dict())
        return sorted(works_list, key=lambda x: x.get('updated_at', datetime.datetime.min), reverse=True)
    except Exception as e:
        st.error(f"목록 불러오기 실패: {e}")
        return []

def delete_work(work_id):
    if db is None: return
    try:
        db.collection("works").document(f"{device_id}_{work_id}").delete()
    except:
        pass

def generate_copy(platform, name, material, point):
    if "OPENAI_API_KEY" not in st.secrets:
        return "⚠️ OpenAI API 키 설정이 필요합니다."
    
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 핸드메이드 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요, ~했답니다 등 다정하고 따뜻하게. 특수기호(*, **) 사용 금지."
        
        if platform == "인스타":
            system_p = f"{base_style} [📸 인스타그램] 감성 문구, 제작 과정, 일기장 스타일. 해시태그 필수."
        elif platform == "아이디어스":
            system_p = f"{base_style} [🎨 아이디어스] 4단락 필수: 💡상세설명, 🍀Add info, 🔉안내, 👍🏻작가보증."
        elif platform == "스토어":
            system_p = f"{base_style} [🛍️ 스마트스토어] 7단락 필수: 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리, 📍추천."
        else:
            system_p = base_style

        user_msg = f"작품명: {name}\n소재: {material}\n특징/포인트: {point}"
        
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":system_p},{"role":"user","content":user_msg}]
        )
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except Exception as e:
        return f"AI 연결 오류: {str(e)}"

# ==========================================
# [섹션 D] UI 렌더링 (안전 흐름)
# ==========================================

# 1. 세션 초기화
if 'current_work' not in st.session_state:
    st.session_state.current_work = None

# 2. 데이터 로드
my_works = load_works()

# 3. 사이드바 구성
with st.sidebar:
    st.header("📂 내 작품")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        empty_data = {"name": "", "material": "", "point": "", "texts": {}}
        st.session_state.current_work = {"work_id": new_id, **empty_data}
        save_to_db(new_id, empty_data)
        st.rerun()
    
    st.divider()
    
    if not my_works:
        st.caption("등록된 작품이 없습니다.")
    else:
        for w in my_works:
            label = w.get('name') or "(이름 없는 작품)"
            # 현재 선택된 항목 강조
            is_active = st.session_state.current_work and st.session_state.current_work['work_id'] == w['work_id']
            if st.button(f"{'👉' if is_active else '📦'} {label}", key=w['work_id'], use_container_width=True):
                st.session_state.current_work = w
                st.rerun()

# 4. 메인 콘텐츠
# Case: 선택된 작품 없음
if st.session_state.current_work is None:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽 [➕ 새 작품 만들기] 버튼을 눌러 시작하세요!")
        st.stop()

# Case: 작업 중
curr = st.session_state.current_work
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 작품 정보")
    
    n_name = st.text_input("작품 이름", value=curr.get('name', ''))
    n_mat = st.text_input("소재", value=curr.get('material', ''))
    n_point = st.text_area("특징 / 포인트", value=curr.get('point', ''), height=150)
    
    # 변경 감지 및 저장
    if (n_name != curr.get('name') or n_mat != curr.get('material') or n_point != curr.get('point')):
        curr.update({'name': n_name, 'material': n_mat, 'point': n_point})
        save_to_db(curr['work_id'], curr)
    
    st.caption("자동 저장 중...")
    
    st.divider()
    if st.button("🗑️ 삭제하기"):
        delete_work(curr['work_id'])
        st.session_state.current_work = None
        st.rerun()

with col2:
    st.subheader("✨ AI 글쓰기")
    
    tabs = st.tabs(["📸 인스타", "🎨 아이디어스", "🛍️ 스토어"])
    texts = curr.get('texts', {})
    if not isinstance(texts, dict): texts = {}

    def render_ai_tab(tab, key, p_name):
        with tab:
            if st.button(f"{p_name} 글 짓기", key=f"btn_{key}"):
                if not n_name.strip():
                    st.warning("이름을 먼저 입력해주세요!")
                else:
                    with st.spinner("작성 중..."):
                        res = generate_copy(p_name, n_name, n_mat, n_point)
                        texts[key] = res
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr)
                        st.rerun()
            st.text_area("결과", value=texts.get(key, ""), height=400)

    render_ai_tab(tabs[0], "insta", "인스타")
    render_ai_tab(tabs[1], "idus", "아이디어스")
    render_ai_tab(tabs[2], "store", "스토어")
