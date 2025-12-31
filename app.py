import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import streamlit.components.v1 as components

# 1. [절대 원칙] 페이지 설정이 가장 먼저 와야 함
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# 2. [사용자 식별] 로그인 없는 기기 기반 식별 (localStorage + URL 파라미터)
# 설명: 로그인 창 없음. 접속 즉시 기기 고유 ID로 식별. 주소창에 ID 고정.
js_code = """
<script>
    const urlParams = new URLSearchParams(window.location.search);
    let deviceId = urlParams.get('device_id');
    
    // URL에 ID가 없으면 로컬 스토리지 확인 (재접속 대응)
    if (!deviceId) {
        deviceId = localStorage.getItem('mog_device_id');
        
        // 로컬 스토리지에도 없으면 신규 생성 (최초 접속)
        if (!deviceId) {
            deviceId = 'mog_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('mog_device_id', deviceId);
        }
        
        // URL에 ID 박아넣고 리로드 (주소 즐겨찾기용)
        urlParams.set('device_id', deviceId);
        window.location.search = urlParams.toString();
    } else {
        // URL에 있으면 로컬 스토리지 동기화 (기기 유지)
        localStorage.setItem('mog_device_id', deviceId);
    }
</script>
"""
components.html(js_code, height=0, width=0)

# Streamlit 세션에서 ID 확인
try:
    query_params = st.query_params
    device_id = query_params.get("device_id", None)
except:
    st.stop()

if not device_id:
    st.stop()  # JS 리로드 대기

# 3. [데이터 영속성] Firebase Firestore 연결
# 설명: 세션(휘발성)이 아닌 DB(영속성)를 유일한 진실로 취급.
if not firebase_admin._apps:
    try:
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("데이터베이스 연결 중 오류가 발생했습니다.")
        st.stop()

db = firestore.client()

# --- DB 함수 (자동 저장 핵심) ---
def save_to_db(work_id, data):
    """입력 즉시 Firestore에 저장 (버튼 없음)"""
    doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
    final_data = {
        "device_id": device_id,
        "work_id": work_id,
        "updated_at": datetime.datetime.now(),
        **data
    }
    doc_ref.set(final_data) # merge=True 대신 set으로 덮어써서 데이터 정합성 유지

def load_works():
    """기기 ID에 해당하는 작품만 로드"""
    docs = db.collection("works").where("device_id", "==", device_id).stream()
    works_list = []
    for doc in docs:
        works_list.append(doc.to_dict())
    return sorted(works_list, key=lambda x: x.get('updated_at', datetime.datetime.min), reverse=True)

def delete_work(work_id):
    """작품 단위 삭제"""
    db.collection("works").document(f"{device_id}_{work_id}").delete()

# --- AI 로직 (프롬프트 분리 원칙 준수) ---
def generate_copy(platform, name, material, point):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    # 공통 페르소나: 따뜻하고 다정한 작가님
    base_style = "[절대 규칙: 1인칭 작가 시점] 당신은 핸드메이드 작가 '모그(Mog)' 본인입니다. 말투: ~이지요^^, ~해요, ~했답니다 등 다정하고 따뜻하게. 특수기호(*, **) 사용 금지."
    
    if platform == "인스타":
        prompt = f"{base_style} [📸 인스타그램] 감성 문구, 제작 과정 서술, 해시태그 포함. 문단은 짧게."
    elif platform == "아이디어스":
        prompt = f"{base_style} [🎨 아이디어스] 4가지 필수 포맷 준수: \n💡상세설명 \n🍀Add info.(구매팁) \n🔉안내(배송/주의) \n👍🏻작가보증"
    elif platform == "스토어":
        prompt = f"{base_style} [🛍️ 스마트스토어] 7가지 필수 포맷 준수: \n💐상품명 \n🌸디자인 \n👜기능성 \n📏사이즈 \n📦소재 \n🧼관리 \n📍추천"
    else:
        return "알 수 없는 플랫폼입니다."

    user_msg = f"작품명: {name}\n소재: {material}\n포인트: {point}"
    
    try:
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":prompt}, {"role":"user","content":user_msg}]
        )
        return res.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except Exception:
        return "글쓰기 서버가 잠시 바쁜가 봐요. 잠시 후 다시 시도해주세요."

# --- UI 구성 (단순함 + 반복 안정성) ---

# 세션 초기화
if 'current_work' not in st.session_state:
    st.session_state.current_work = None

# [사이드바] 작품 목록 (직관적 선택)
with st.sidebar:
    st.header("📂 내 작품 목록")
    
    # 신규 생성
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        # 생성 즉시 DB 저장 (데이터 유실 방지 1원칙)
        empty_data = {"name": "", "material": "", "point": "", "texts": {"insta": "", "idus": "", "store": ""}}
        save_to_db(new_id, empty_data)
        st.session_state.current_work = {"work_id": new_id, **empty_data}
        st.rerun()
    
    st.divider()
    
    # 목록 로드
    my_works = load_works()
    for w in my_works:
        label = w.get('name') if w.get('name') else "(이름 없는 작품)"
        if st.button(f"📦 {label}", key=f"btn_{w['work_id']}", use_container_width=True):
            st.session_state.current_work = w
            st.rerun()

# [메인 화면]
st.title("🌸 모그 작가님 AI 비서")

# 선택된 작품이 없으면 안내 (UX 보호)
if st.session_state.current_work is None:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽의 '새 작품 만들기' 버튼을 눌러주세요^^")
        st.stop()

# 현재 작업 데이터
curr = st.session_state.current_work

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📝 작품 정보")
    st.caption("입력하면 자동으로 저장됩니다.")
    
    # [입력 폼] 값 변경 감지 -> 즉시 저장 (Debounce 없이 안전 제일)
    new_name = st.text_input("작품 이름", value=curr.get('name', ''))
    new_mat = st.text_input("소재", value=curr.get('material', ''))
    new_point = st.text_area("특징 / 포인트", value=curr.get('point', ''), height=200)
    
    # 변경 감지 로직
    is_changed = (
        new_name != curr.get('name') or 
        new_mat != curr.get('material') or 
        new_point != curr.get('point')
    )
    
    if is_changed:
        curr['name'] = new_name
        curr['material'] = new_mat
        curr['point'] = new_point
        save_to_db(curr['work_id'], curr) # Firestore 즉시 반영
        # 별도 알림 없이 조용히 저장 (UX 방해 금지)

    st.markdown("---")
    # 삭제 기능 (작품 단위만)
    if st.button("🗑️ 이 작품 삭제하기"):
        delete_work(curr['work_id'])
        st.session_state.current_work = None
        st.rerun()

with col_right:
    st.subheader("✨ 글쓰기")
    
    tab_list = ["📸 인스타", "🎨 아이디어스", "🛍️ 스토어"]
    tabs = st.tabs(tab_list)
    
    texts = curr.get('texts', {})
    
    # 탭 렌더링 함수
    def render_platform_tab(tab, p_key, p_name):
        with tab:
            # 생성 버튼
            if st.button(f"{p_name} 글 짓기", key=f"gen_{p_key}"):
                if not new_name:
                    st.warning("작품 이름을 먼저 적어주세요!")
                else:
                    with st.spinner("글을 짓고 있어요..."):
                        res = generate_copy(p_name, new_name, new_mat, new_point)
                        texts[p_key] = res
                        curr['texts'] = texts
                        save_to_db(curr['work_id'], curr) # 결과물도 즉시 저장
                        st.rerun()
            
            # 결과 출력 (읽기 전용에 가깝게)
            st.text_area("결과물", value=texts.get(p_key, ""), height=450, key=f"view_{p_key}")

    render_platform_tab(tabs[0], "insta", "인스타")
    render_platform_tab(tabs[1], "idus", "아이디어스")
    render_platform_tab(tabs[2], "store", "스토어")
