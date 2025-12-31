import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import streamlit.components.v1 as components
import time

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 흰 화면 방지용 기기 식별 로직
# ==========================================

# 1. 안전하게 query_params 가져오기 (버전 호환성 확보)
try:
    # Streamlit 최신 버전
    query_params = st.query_params
except AttributeError:
    # 구버전 호환
    try:
        query_params = st.experimental_get_query_params()
    except:
        query_params = {}

# 2. device_id 추출 (리스트/문자열/None 모든 케이스 대응)
device_id = None
if "device_id" in query_params:
    p_val = query_params["device_id"]
    if isinstance(p_val, list) and len(p_val) > 0:
        device_id = p_val[0]
    elif isinstance(p_val, str) and p_val.strip():
        device_id = p_val

# 3. 자바스크립트 주입 (기기가 식별되지 않았을 때만 실행)
# 주의: 이미 device_id가 있어도, 로컬스토리지 동기화를 위해 JS는 항상 렌더링하되 리로드는 조건부로 함
js_code = """
<script>
    try {
        const urlParams = new URLSearchParams(window.location.search);
        let urlDeviceId = urlParams.get('device_id');
        let localDeviceId = localStorage.getItem('mog_device_id');
        
        // 1. URL에 ID가 없고, 로컬스토리지에도 없는 경우 -> 신규 생성
        if (!urlDeviceId && !localDeviceId) {
            const newId = 'mog_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mog_device_id', newId);
            urlParams.set('device_id', newId);
            window.location.search = urlParams.toString(); // 리로드 발생
        }
        // 2. URL엔 없는데 로컬스토리지엔 있는 경우 -> URL에 붙여서 복구
        else if (!urlDeviceId && localDeviceId) {
            urlParams.set('device_id', localDeviceId);
            window.location.search = urlParams.toString(); // 리로드 발생
        }
        // 3. URL엔 있는데 로컬스토리지랑 다른 경우 (혹은 로컬에 없는 경우) -> 로컬 동기화
        else if (urlDeviceId && (urlDeviceId !== localDeviceId)) {
            localStorage.setItem('mog_device_id', urlDeviceId);
        }
    } catch(e) {
        console.error("Device ID Logic Error:", e);
    }
</script>
"""
components.html(js_code, height=0, width=0)

# 4. [중요] Python단에서의 실행 제어 (흰 화면 방지 핵심)
if not device_id:
    # 아직 URL에 id가 안 붙은 찰나의 순간
    # 바로 st.stop()을 하면 흰 화면이 뜨므로, 안내 메시지를 먼저 띄움
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h3>🌸 작가님을 확인하고 있어요...</h3>
        <p>잠시만 기다려주세요. 화면이 깜빡일 수 있습니다 ^^</p>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(1) # JS가 돌 시간을 1초 벌어줌
    st.stop() # 이후 실행 중단 (JS가 곧 리로드함)

# ==========================================
# [섹션 B] Firebase & Backend 안전 연결
# ==========================================

db = None
try:
    if not firebase_admin._apps:
        # secrets가 존재하는지 먼저 확인
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            raise ValueError("Secrets에 'FIREBASE_SERVICE_ACCOUNT' 정보가 없습니다.")
            
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
except Exception as e:
    # DB 연결 실패 시에도 흰 화면 대신 에러 메시지 출력
    st.error(f"🚨 시스템 연결 중 문제가 발생했어요.")
    st.code(str(e))
    st.info("따님께 'Secrets 설정'을 확인해달라고 말씀해주세요.")
    st.stop()

# ==========================================
# [섹션 C] 데이터 관리 함수 (CRUD)
# ==========================================

def save_to_db(work_id, data):
    """안전한 저장 함수"""
    if not db: return
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
        st.error(f"저장 중 오류가 났어요: {e}")

def load_works():
    """안전한 불러오기 함수"""
    if not db: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        works_list = []
        for doc in docs:
            works_list.append(doc.to_dict())
        return sorted(works_list, key=lambda x: x.get('updated_at', datetime.datetime.min), reverse=True)
    except Exception as e:
        st.warning(f"데이터를 불러오는데 실패했어요: {e}")
        return []

def delete_work(work_id):
    if not db: return
    db.collection("works").document(f"{device_id}_{work_id}").delete()

def generate_copy(platform, name, material, point):
    # OpenAI API 키 체크
    if "OPENAI_API_KEY" not in st.secrets:
        return "⚠️ OpenAI API 키가 설정되지 않았습니다."

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
    
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":system_p},{"role":"user","content":user_msg}]
        )
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except Exception as e:
        return f"글쓰기 중 오류가 났어요 ㅠㅠ: {str(e)}"

# ==========================================
# [섹션 D] UI 렌더링 (예외 없는 안전한 흐름)
# ==========================================

# 1. 세션 초기화
if 'current_work' not in st.session_state:
    st.session_state.current_work = None

# 2. 데이터 로드
my_works = load_works()

# 3. 사이드바 UI
with st.sidebar:
    st.title("📂 내 작품 목록")
    
    # 새 작품 만들기 버튼
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        empty_data = {"name": "", "material": "", "point": "", "texts": {"insta": "", "idus": "", "store": ""}}
        st.session_state.current_work = {"work_id": new_id, **empty_data}
        save_to_db(new_id, empty_data)
        st.rerun()
    
    st.divider()
    
    if not my_works:
        st.info("아직 등록된 작품이 없어요.\n위 버튼을 눌러 시작해보세요!")
    else:
        for w in my_works:
            label = w.get('name') or "(이름 없는 작품)"
            # 현재 선택된 작품 표시 (UX 강화)
            is_active = st.session_state.current_work and st.session_state.current_work['work_id'] == w['work_id']
            if st.button(f"{'👉' if is_active else '📦'} {label}", key=w['work_id'], use_container_width=True):
                st.session_state.current_work = w
                st.rerun()

# 4. 메인 화면 UI
st.title("🌸 모그 작가님 AI 비서")

# Case: 선택된 작품이 없음 (초기 상태 혹은 삭제 후)
if st.session_state.current_work is None:
    if my_works:
        # 목록은 있는데 선택이 안된 경우 -> 첫 번째 자동 선택
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        # 목록도 없는 경우 -> 안내 화면
        st.info("👈 왼쪽 사이드바의 [➕ 새 작품 만들기] 버튼을 눌러주세요^^")
        st.stop() # 여기서는 멈춰도 됨 (안내 문구가 있으므로)

# Case: 작업 중
curr = st.session_state.current_work

# 레이아웃
col_input, col_output = st.columns([1, 1])

with col_input:
    st.subheader("📝 작품 정보")
    
    # 텍스트 입력 위젯
    new_name = st.text_input("작품 이름", value=curr.get('name', ''))
    new_mat = st.text_input("소재", value=curr.get('material', ''))
    new_point = st.text_area("특징 / 포인트", value=curr.get('point', ''), height=150)
    
    # 변화 감지 및 저장
    has_changed = (
        new_name != curr.get('name') or 
        new_mat != curr.get('material') or 
        new_point != curr.get('point')
    )
    
    if has_changed:
        curr['name'] = new_name
        curr['material'] = new_mat
        curr['point'] = new_point
        save_to_db(curr['work_id'], curr)
        
    st.caption("입력하면 자동으로 저장됩니다.")

    st.divider()
    if st.button("🗑️ 이 작품 삭제하기"):
        delete_work(curr['work_id'])
        st.session_state.current_work = None # 초기화
        st.success("삭제되었습니다!")
        st.rerun()

with col_output:
    st.subheader("✨ AI 글쓰기")
    
    tabs = st.tabs(["📸 인스타", "🎨 아이디어스", "🛍️ 스토어"])
    texts = curr.get('texts', {})
    if not isinstance(texts, dict): texts = {} # 방어 코드

    def render_platform_tab(tab, key, name):
        with tab:
            if st.button(f"{name} 글 짓기", key=f"btn_{key}"):
                if not new_name.strip():
                    st.warning("작품 이름을 먼저 입력해주세요^^")
                else:
                    with st.spinner("글을 짓고 있습니다..."):
                        res = generate_copy(name, new_name, new_mat, new_point)
                        texts[key] = res
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr)
                        st.rerun()
            
            val = texts.get(key, "")
            st.text_area("결과물", value=val, height=400, key=f"res_{key}")

    render_platform_tab(tabs[0], "insta", "인스타")
    render_platform_tab(tabs[1], "idus", "아이디어스")
    render_platform_tab(tabs[2], "store", "스토어")
