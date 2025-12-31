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
# [섹션 B] 화면 분기 (device_id 유무 기준)
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
# [섹션 C] 메인 앱 준비 (DB 연결 및 함수)
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

# 2. 데이터 처리 함수들 (기존 유지)
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

# 3. AI 기능 함수 (기존 유지 + 상담 함수 추가)

# [기존] 이미지 분석
def analyze_image_features(uploaded_file):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 오류"
    try:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 핸드메이드 작품 분석가입니다. 사진의 색감, 분위기, 재질감, 시각적 특징을 3줄 이내로 간략히 요약하세요. 감탄사 생략, 핵심만 서술."},
                {"role": "user", "content": [{"type": "text", "text": "이 작품의 시각적 특징을 분석해줘."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"(사진 분석 실패: {str(e)})"

# [기존] 글 생성
def generate_copy(platform, name, material, size, duration, point, img_desc):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # 기본 페르소나
        base_persona = """[역할 정의] 당신은 핸드메이드 작가 '모그(Mog)'입니다."""
        
        if platform == "인스타":
            system_message = """[인스타그램 규칙] 100% 감성 독백형 에세이. 상업적 키워드 금지. 말끝(~죠?, ~해요). 줄바꿈 자주.
            [구조] 도입(날씨/기분) -> 본문(감정/손맛) -> 정보(녹여서) -> 여운 남는 마무리."""
        elif platform == "아이디어스":
            system_message = """[아이디어스 규칙] 정보형 판매글. 명확한 설명체(~입니다). 문단 사이 빈 줄. 구분선(〰️, ➖) 사용.
            [구조] 요약 -> 사이즈안내 -> 〰️ -> 포인트(📌) -> ➖ -> 컨셉 -> 작가소개 -> 소재 -> 상세사이즈 -> 구성 -> 제작/배송 -> 세탁."""
        else:
            system_message = """[스토어 규칙] 신뢰감 있는 정보 전달. 3인칭 설명체.
            [구조] 요약 -> 디자인/핏 -> 스타일링 -> 추천대상 -> 소재 -> 사이즈 -> 촬영안내."""

        user_input = f"""
        [Data] Name: {name}, Material: {material}, Size: {size}, Duration: {duration}, Point: {point}, Image Feature: {img_desc}
        [지시] 작가 입력 정보 최우선. 플랫폼별 어투/구조 100% 준수.
        """
        
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content": base_persona + "\n" + system_message}, {"role":"user","content": user_input}]
        )
        return res.choices[0].message.content.replace("**", "").strip()
    except Exception as e: return f"AI 오류: {str(e)}"

# [신규] 고민상담소 AI 응답 생성 함수
def ask_consultant(history_messages):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        system_prompt = """
        [역할 정의]
        당신은 핸드메이드 작가를 돕는 '실전형 판매·마케팅 컨설턴트'입니다.
        작가의 고민에 대해 막연한 위로가 아닌, '매출과 브랜딩에 직결되는 현실적인 조언'을 제공합니다.

        [답변 스타일]
        - 말투: 차분하고 단정한 설명체 (~합니다, ~하세요).
        - 태도: 객관적이고 분석적이며, 실행 가능한 대안을 제시하는 전문가.
        - 금지: "힘내세요", "열심히 하면 됩니다" 같은 추상적인 위로 금지. 불필요한 이모지 남발 금지.

        [답변 구조 가이드]
        1. [문제 요약] 작가의 고민 핵심을 한 줄로 정리.
        2. [원인 분석] 왜 그런 문제가 발생하는지 실무적 관점에서 분석 (가격, 노출, 사진, 소구점 등).
        3. [실행 솔루션] 당장 시도해볼 수 있는 구체적인 해결책 2~4가지 (번호 매기기).
        4. [조언] 장단점 비교나 리스크가 있다면 명확히 언급.
        """
        
        messages = [{"role": "system", "content": system_prompt}] + history_messages
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e: return f"상담 중 오류가 발생했습니다: {str(e)}"


# ==========================================
# [섹션 D] UI 레이아웃 구성
# ==========================================

# 1. 사이드바 (공통 유지)
if 'current_work' not in st.session_state: st.session_state.current_work = None
my_works = load_works()

with st.sidebar:
    st.title("📂 내 작품 목록")
    if st.button("➕ 새 작품 만들기", use_container_width=True, type="primary"):
        uid = str(uuid.uuid4())
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

# 2. 메인 탭 구성 (글작성 / 고민상담소)
main_tab1, main_tab2 = st.tabs(["📝 글작성", "💬 고민상담소"])

# =========================================================
# [탭 1] 글작성 (기존 기능 100% 이식)
# =========================================================
with main_tab1:
    if not st.session_state.current_work:
        if my_works:
            st.session_state.current_work = my_works[0]
            st.rerun()
        else:
            st.info("👈 왼쪽 사이드바의 [➕ 새 작품 만들기] 버튼을 눌러주세요!")
            st.stop()

    curr = st.session_state.current_work
    wid = curr['work_id']

    # 데이터 로드
    c_name = curr.get('name', '')
    c_mat = curr.get('material', '')
    c_size = curr.get('size', '')
    c_dur = curr.get('duration', '')
    c_point = curr.get('point', '')
    c_img_anl = curr.get('image_analysis', '')

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📝 기본 정보 입력")
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
        
        uploaded_img = st.file_uploader("작품 사진을 올리면 AI가 특징을 읽어줍니다", type=['png', 'jpg', 'jpeg'], key=f"uploader_{wid}")
        
        if uploaded_img:
            if st.button("✨ 이 사진 특징 분석하기", key=f"btn_anal_{wid}"):
                with st.spinner("사진을 꼼꼼히 보고 있어요..."):
                    analysis_result = analyze_image_features(uploaded_img)
                    c_img_anl = analysis_result
                    curr.update({'image_analysis': c_img_anl})
                    save_to_db(wid, curr)
                    st.session_state[f"input_img_anl_{wid}"] = analysis_result
                    st.rerun()

        n_img_anl = st.text_area("AI가 분석한 사진 특징 (수정 가능)", value=c_img_anl, height=80, key=f"input_img_anl_{wid}", placeholder="사진을 올리고 분석 버튼을 누르면 채워집니다.")

        # 자동 저장
        if (nn!=c_name or nm!=c_mat or ns!=c_size or nd!=c_dur or np!=c_point or n_img_anl!=c_img_anl):
            curr.update({'name': nn, 'material': nm, 'size': ns, 'duration': nd, 'point': np, 'image_analysis': n_img_anl})
            save_to_db(wid, curr)

        st.caption("모든 내용은 자동으로 저장됩니다.")
        
        if st.button("🗑️ 이 작품 삭제", key=f"btn_del_{wid}"):
            delete_work(wid)
            st.session_state.current_work = None
            st.rerun()

    with c2:
        st.subheader("✨ 글쓰기")
        sub_tabs = st.tabs(["인스타", "아이디어스", "스토어"])
        texts = curr.get('texts', {})
        
        def render_sub_tab(tab, platform_key, platform_name):
            with tab:
                if st.button(f"{platform_name} 글 짓기", key=f"btn_gen_{platform_key}_{wid}"):
                    if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                    else:
                        with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                            res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl)
                            texts[platform_key] = res
                            curr['texts'] = texts
                            save_to_db(wid, curr)
                            st.session_state[f"result_{platform_key}_{wid}"] = res
                            st.rerun()
                st.text_area("결과물", value=texts.get(platform_key,""), height=500, key=f"result_{platform_key}_{wid}")

        render_sub_tab(sub_tabs[0], "insta", "인스타")
        render_sub_tab(sub_tabs[1], "idus", "아이디어스")
        render_sub_tab(sub_tabs[2], "store", "스토어")


# =========================================================
# [탭 2] 고민상담소 (신규 기능)
# =========================================================
with main_tab2:
    st.header("💬 핸드메이드 고민 상담소")
    st.caption("가격, 마케팅, 고객 대응... 혼자 고민하지 말고 물어보세요. 실전형 컨설턴트가 답변해드립니다.")
    
    # 1. 채팅 로그 세션 초기화
    if "consult_chat_log" not in st.session_state:
        st.session_state["consult_chat_log"] = []

    # 2. 이전 대화 기록 출력
    for msg in st.session_state["consult_chat_log"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. 사용자 입력 처리
    if user_question := st.chat_input("예: 이번 신상 가격을 어떻게 정해야 할지 모르겠어."):
        # 사용자 메시지 표시 및 저장
        st.session_state["consult_chat_log"].append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        # AI 답변 생성 및 표시
        with st.chat_message("assistant"):
            with st.spinner("전문가가 고민을 분석 중입니다..."):
                # API 호출용 히스토리 구성 (시스템 프롬프트는 함수 내에서 결합)
                history_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state["consult_chat_log"]]
                
                ai_advice = ask_consultant(history_for_api)
                st.markdown(ai_advice)
        
        # AI 답변 저장
        st.session_state["consult_chat_log"].append({"role": "assistant", "content": ai_advice})
    
