import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import datetime
import traceback
import base64

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

# [신규 기능] 이미지 분석 함수 (Vision API)
def analyze_image_features(uploaded_file):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 오류"
    try:
        # 이미지를 base64로 인코딩
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o", # Vision 기능이 있는 모델
            messages=[
                {
                    "role": "system",
                    "content": "당신은 핸드메이드 작품을 분석하는 전문가입니다. 사진을 보고 색감, 분위기, 재질감, 시각적 특징을 3줄 이내로 간략히 요약해서 한국어로 설명해주세요. 감탄사나 인사는 생략하고 핵심 특징만 서술하세요."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 작품의 시각적 특징을 분석해줘."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(사진 분석 실패: {str(e)})"

# [수정] 글 생성 함수 (필드 확장 반영)
def generate_copy(platform, name, material, size, duration, point, img_desc):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 기본 페르소나
        base = """[규칙: 1인칭 '모그' 작가 시점]
        말투: ~이지요^^, ~해요, ~했답니다. 다정하고 따뜻하게.
        금지: 특수기호(*, **) 사용 금지. 기계적인 느낌 금지.
        """
        
        # 플랫폼별 지침
        platform_rules = {
            "인스타": "[인스타] 감성적인 에세이 스타일. 제작 과정의 정성과 시각적 아름다움을 강조. 해시태그 10개 포함.",
            "아이디어스": "[아이디어스] 💡상세설명(감성 스토리), 🍀Add info(사이즈/소재/제작기간), 🔉안내(주의사항), 👍🏻작가보증 4단락 구조 준수.",
            "스토어": "[스토어] 💐상품명, 🌸디자인, 👜기능/특징, 📏사이즈/제작기간, 📦소재, 🧼관리법, 📍추천이유 7단락 구조 준수."
        }
        
        # 사용자 데이터 조합
        user_input = f"""
        [기본 정보]
        - 이름: {name}
        - 소재: {material}
        - 사이즈: {size}
        - 제작기간: {duration}
        - 특징/포인트: {point}
        
        [사진에서 분석된 특징 (참고용)]
        {img_desc}
        
        [지시사항]
        1. 사진 특징은 글을 풍성하게 만드는 양념으로만 사용하세요.
        2. 작가가 직접 입력한 [기본 정보]가 팩트이므로 가장 우선순위가 높습니다.
        3. 사진 특징이 기본 정보와 충돌하면 무시하세요.
        """
        
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":base + platform_rules.get(platform, base)}, 
                {"role":"user","content":user_input}
            ]
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
        # [수정] 빈 데이터 구조에 신규 필드 추가
        empty = {"name": "", "material": "", "size": "", "duration": "", "point": "", "image_analysis": "", "texts": {}}
        st.session_state.current_work = {"work_id": uid, **empty}
        save_to_db(uid, empty)
        st.rerun()
    
    st.divider()
    
    if not my_works:
        st.caption("목록이 비어있습니다.")
    else:
        for w in my_works:
            label = w.get('name') or "(이름 없는 작품)"
            is_active = st.session_state.current_work and st.session_state.current_work['work_id'] == w['work_id']
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
wid = curr['work_id']

# 데이터 안전 조회 (신규 필드 없을 경우 대비)
c_name = curr.get('name', '')
c_mat = curr.get('material', '')
c_size = curr.get('size', '')      # 신규
c_dur = curr.get('duration', '')   # 신규
c_point = curr.get('point', '')
c_img_anl = curr.get('image_analysis', '') # 신규

c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 기본 정보 입력")
    
    # [수정] 입력 필드 확장 (Key 충돌 방지 유지)
    nn = st.text_input("작품 이름", value=c_name, key=f"input_name_{wid}")
    
    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        nm = st.text_input("소재", value=c_mat, key=f"input_mat_{wid}")
    with col_sub2:
        ns = st.text_input("사이즈 (예: 20x30cm)", value=c_size, key=f"input_size_{wid}")
        
    nd = st.text_input("제작 소요 기간 (예: 3일)", value=c_dur, key=f"input_dur_{wid}")
    np = st.text_area("특징 / 포인트 (작가님 생각)", value=c_point, height=100, key=f"input_point_{wid}")

    st.markdown("---")
    st.subheader("📸 사진 보조 (선택)")
    
    # 사진 업로더 (DB 저장 X, 분석용 O)
    uploaded_img = st.file_uploader("작품 사진을 올리면 AI가 특징을 읽어줍니다", type=['png', 'jpg', 'jpeg'], key=f"uploader_{wid}")
    
    # 사진 분석 버튼 (토큰 절약을 위해 버튼 클릭 시 수행)
    if uploaded_img:
        if st.button("✨ 이 사진 특징 분석하기", key=f"btn_anal_{wid}"):
            with st.spinner("사진을 꼼꼼히 보고 있어요..."):
                analysis_result = analyze_image_features(uploaded_img)
                c_img_anl = analysis_result # 결과 업데이트
                # 즉시 저장
                curr.update({'image_analysis': c_img_anl})
                save_to_db(wid, curr)
                st.rerun()

    # 분석된 텍스트 표시 (수정 가능하게 text_area로 제공)
    n_img_anl = st.text_area("AI가 분석한 사진 특징 (수정 가능)", value=c_img_anl, height=80, key=f"input_img_anl_{wid}", placeholder="사진을 올리고 분석 버튼을 누르면 채워집니다.")

    # 전체 변경 감지 및 저장
    if (nn!=c_name or nm!=c_mat or ns!=c_size or nd!=c_dur or np!=c_point or n_img_anl!=c_img_anl):
        curr.update({
            'name': nn, 'material': nm, 'size': ns, 'duration': nd, 
            'point': np, 'image_analysis': n_img_anl
        })
        save_to_db(wid, curr)

    st.caption("모든 내용은 자동으로 저장됩니다.")
    
    if st.button("🗑️ 이 작품 삭제", key=f"btn_del_{wid}"):
        delete_work(wid)
        st.session_state.current_work = None
        st.rerun()

with c2:
    st.subheader("✨ 글쓰기")
    tabs = st.tabs(["인스타", "아이디어스", "스토어"])
    texts = curr.get('texts', {})
    
    def render_tab(tab, platform_key, platform_name):
        with tab:
            if st.button(f"{platform_name} 글 짓기", key=f"btn_gen_{platform_key}_{wid}"):
                if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                else:
                    with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                        # [수정] 확장된 필드 전달
                        res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl)
                        texts[platform_key] = res
                        curr['texts'] = texts
                        save_to_db(wid, curr)
                        st.rerun()
            
            st.text_area("결과물", value=texts.get(platform_key,""), height=500, key=f"result_{platform_key}_{wid}")

    render_tab(tabs[0], "insta", "인스타")
    render_tab(tabs[1], "idus", "아이디어스")
    render_tab(tabs[2], "store", "스토어")
