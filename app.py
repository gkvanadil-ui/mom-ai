import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import traceback

# 1. 페이지 설정
st.set_page_config(page_title="모그 작가님 AI 비서", layout="wide", page_icon="🌸")

# ==========================================
# [섹션 A] 진실의 원천 (ID 확정 로직)
# ==========================================

found_id = None
try:
    qp = st.query_params
    val = qp.get("device_id")
    if val: found_id = val if isinstance(val, str) else val[0]
except:
    try:
        qp = st.experimental_get_query_params()
        if "device_id" in qp: found_id = qp["device_id"][0]
    except:
        pass

if found_id and "device_id" not in st.session_state:
    st.session_state["device_id"] = found_id

# ==========================================
# [섹션 B] 화면 분기
# ==========================================

if "device_id" not in st.session_state:
    st.markdown("""
    <div style='text-align: center; padding-top: 50px; padding-bottom: 30px;'>
        <h1 style='color: #FF4B4B;'>🌸 모그 작가님 AI 비서</h1>
        <p style='font-size: 1.1em; color: #666;'>
            환영합니다, 작가님.<br>
            아래 버튼을 눌러 작업을 시작해주세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 작가님, 여기를 눌러 시작해주세요", use_container_width=True, type="primary"):
            new_id = f"mog_{str(uuid.uuid4())[:8]}"
            st.session_state["device_id"] = new_id
            try:
                st.experimental_set_query_params(device_id=new_id)
            except:
                pass
            st.rerun()
    
    st.markdown("""
    <div style='text-align: center; margin-top: 40px; font-size: 0.85em; color: #999;'>
        * 버튼을 누르면 작가님만의 고유 주소가 생성됩니다.<br>
        * 주소를 <b>즐겨찾기</b> 해두시면 언제든 이어서 작성하실 수 있어요.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# [섹션 C] 메인 앱
# ==========================================

device_id = st.session_state["device_id"]

# 1. Firebase 연결
db = None
try:
    if not firebase_admin._apps:
        if "FIREBASE_SERVICE_ACCOUNT" not in st.secrets:
            raise ValueError("Secrets 설정을 확인해주세요.")
        cred_dict = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error("🚨 서버와 연결할 수 없습니다.")
    with st.expander("상세 오류 보기"):
        st.code(traceback.format_exc())
    st.stop()

# 2. 데이터 처리 함수
def save_to_db(work_id, data):
    if not db: return
    try:
        doc_ref = db.collection("works").document(f"{device_id}_{work_id}")
        doc_ref.set({
            "device_id": device_id,
            "work_id": work_id,
            "updated_at": datetime.datetime.now(datetime.timezone.utc),
            **data
        })
    except Exception as e:
        st.toast("⚠️ 저장 중에 문제가 생겼어요.")

def load_works():
    if not db: return []
    try:
        docs = db.collection("works").where("device_id", "==", device_id).stream()
        return sorted(
            [doc.to_dict() for doc in docs], 
            key=lambda x: x.get('updated_at', datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)), 
            reverse=True
        )
    except Exception as e:
        st.toast("목록을 불러오지 못했습니다.")
        return []

def delete_work(work_id):
    if not db: return
    try:
        db.collection("works").document(f"{device_id}_{work_id}").delete()
        st.toast("작품이 삭제되었습니다.")
    except Exception as e:
        st.toast("삭제 실패: 잠시 후 다시 시도해주세요.")

def generate_copy(platform, name, material, point):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        base = "[규칙: 1인칭 '모그' 작가 시점] 말투: ~이지요^^, ~해요, ~했답니다. 특수기호(*, **) 금지."
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
    except Exception as e: return f"AI 오류: {str(e)}"

# 3. UI 렌더링
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
    
    if not my_works:
        st.caption("아직 등록된 작품이 없습니다.")
    else:
        for w in my_works:
            label = w.get('name') or "(이름 없는 작품)"
            is_active = st.session_state.current_work and st.session_state.current_work['work_id'] == w['work_id']
            # [수정] 사이드바 버튼 Key는 이미 work_id로 유니크함
            if st.button(f"{'👉' if is_active else '📦'} {label}", key=w['work_id'], use_container_width=True):
                st.session_state.current_work = w
                st.rerun()

st.title("🌸 모그 작가님 AI 비서")

if not st.session_state.current_work:
    if my_works:
        st.session_state.current_work = my_works[0]
        st.rerun()
    else:
        st.info("👈 왼쪽 사이드바의 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
        st.stop()

curr = st.session_state.current_work
wid = curr['work_id'] # Key 생성용 ID 확보

c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 정보 입력")
    # [핵심 수정] 모든 입력 위젯에 고유 Key 부여 (work_id 포함)
    nn = st.text_input("작품 이름", value=curr.get('name',''), key=f"input_name_{wid}")
    nm = st.text_input("소재", value=curr.get('material',''), key=f"input_mat_{wid}")
    np = st.text_area("특징 / 포인트", value=curr.get('point',''), height=150, key=f"input_point_{wid}")
    
    # 변경 감지
    if nn!=curr.get('name') or nm!=curr.get('material') or np!=curr.get('point'):
        curr.update({'name':nn, 'material':nm, 'point':np})
        save_to_db(wid, curr)
    
    st.caption("입력 내용은 자동으로 저장됩니다.")
    st.divider()
    
    # [핵심 수정] 삭제 버튼에도 고유 Key 부여
    if st.button("🗑️ 이 작품 삭제", key=f"btn_del_{wid}"):
        delete_work(wid)
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    
    # 탭 렌더링 로직 (ID 충돌 방지 적용)
    def render_tab(tab, platform_key, platform_name):
        with tab:
            # [핵심 수정] 생성 버튼 Key: btn + 플랫폼 + work_id
            if st.button(f"{platform_name} 글 짓기", key=f"btn_gen_{platform_key}_{wid}"):
                if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                else:
                    with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                        res = generate_copy(platform_name, nn, nm, np)
                        texts[platform_key] = res
                        curr['texts'] = texts
                        save_to_db(wid, curr)
                        st.rerun()
            
            # [핵심 수정] 결과 텍스트 영역 Key: result + 플랫폼 + work_id
            st.text_area("결과물", value=texts.get(platform_key,""), height=400, key=f"result_{platform_key}_{wid}")

    render_tab(tabs[0], "insta", "인스타")
    render_tab(tabs[1], "idus", "아이디어스")
    render_tab(tabs[2], "store", "스토어")
