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

# 2. 데이터 처리 함수들
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

# [기능] 이미지 분석 (Vision API)
def analyze_image_features(uploaded_file):
    if "OPENAI_API_KEY" not in st.secrets: return "API 키 오류"
    try:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 핸드메이드 작품 분석가입니다. 사진의 색감, 분위기, 재질감, 시각적 특징을 3줄 이내로 간략히 요약하세요. 감탄사 생략, 핵심만 서술."
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

# [기능] 글 생성 (플랫폼별 어투 강제 적용 - 시스템 프롬프트 분리)
def generate_copy(platform, name, material, size, duration, point, img_desc):
    if "OPENAI_API_KEY" not in st.secrets: return "🚨 API 키 설정을 확인해주세요."
    try:
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # [System Prompt] 플랫폼별 절대 규칙 정의
        if platform == "인스타":
            # [수정 지시서 100% 반영] 인스타 전용 감성 프롬프트
            system_message = """
            [Role]
            당신은 핸드메이드 작가 '모그(Mog)'입니다.
            판매자가 아닌, 작업실에서 조용히 독백하듯 이야기를 건네는 작가입니다.

            [절대 금지 사항]
            - "구매하세요", "주문 가능", "가격 문의", "옵션 선택" 등 상업적 키워드 사용 절대 금지.
            - 딱딱한 설명문, 스펙 나열(사이즈: 20cm X), 설명서 같은 말투 금지.
            - 특수기호(*, **) 사용 금지.

            [어투 및 형식]
            - 1인칭 '모그' 시점의 감성 에세이 스타일.
            - 말끝: ~죠?, ~해요, ~랍니다, ~같아요, ~했어요. (다정하고 여운 있게)
            - 문장은 짧게 끊고, 1~2문장마다 반드시 줄바꿈하여 여백을 둡니다.
            - "조물조물", "사부작", "하나하나", "조금씩 다르지만" 같은 핸드메이드 감성 단어 사용.

            [작성 구조 가이드]
            1. [도입] 소소한 생각, 날씨, 작업실 풍경, 또는 가벼운 말장난으로 시작. (예: "토끼같은... 이란 말 뒤엔 나쁜 단어가 잘 안 붙죠^^")
            2. [본문] 왜 이 소재를 썼는지, 만들 때의 마음, 손맛에 대한 이야기.
               - 작품의 종류나 버전이 있다면 1. 2. 3. 번호를 붙여 이야기하듯 묘사.
            3. [정보] 사이즈나 소재는 문장 속에 자연스럽게 녹여서 언급 (예: "손바닥에 쏙 들어오는 크기라..."). 절대 항목형으로 나열하지 마세요.
            4. [마무리] 읽고 나면 잔잔한 여운이 남는 끝인사.
            5. [해시태그] 글 맨 하단에 자연스럽게 5~10개.
            """
        
        elif platform == "아이디어스":
            # [기존 유지] 아이디어스 정보형 프롬프트
            system_message = """
            [Role]
            당신은 핸드메이드 마켓 '아이디어스(Idus)'의 전문 판매 작가입니다.
            감성보다는 '정확한 정보 전달'과 '가독성'을 최우선으로 하는 판매글을 작성합니다.

            [절대 금지 사항]
            - 혼잣말, 일기체, 감성 독백 금지.
            - 이모티콘(^^, ㅎㅎ, ㅠㅠ) 사용 절대 금지.
            - 과도한 미사여구 및 불필요한 인사/마무리 멘트 금지.

            [어투 및 형식]
            - "~에요", "~입니다" 형태의 친절하고 명확한 설명체.
            - 문단 사이에는 반드시 빈 줄을 넣어 가독성 확보.
            - 〰️, ➖ 구분선을 지시된 위치에 정확히 사용 (단독 줄).

            [필수 작성 구조 (순서 엄수)]
            1. [첫 문단] 색감+분위기+제품 정의 (한 문단 요약).
            2. [사이즈 요약] S/M 여부 언급 + "하단 상세사이즈 참고" 문구.
            3. (구분선) 〰️ (반드시 줄바꿈 후 단독 사용)
            4. [활용/포인트] 📌 이모지 사용. 옵션, 선물용, 활용도 강조.
            5. (구분선) ➖ (반드시 줄바꿈 후 단독 사용)
            6. [컨셉] 꺼낼 때 기분 좋아지는 제품 강조 (질문형 허용).
            7. [작가 소개] 과장 없는 담백한 브랜드 방향성.
            8. [소재 설명] ㅣ겉감ㅣ, ㅣ안감ㅣ 구분, 특성 및 주의사항.
            9. [사이즈 상세] ✔️S사이즈, ✔️M사이즈 항목 분리, 수납 예시 포함.
            10. [구성] 기본 구성 및 옵션(괄호 표기).
            11. [제작/배송] 미리 제작 여부, 사이즈 변경 가능/불가 여부.
            12. [세탁 방법] 손세탁, 물 온도, 건조, 다림질 등 항목형 안내.
            """
            
        else:
            # [기존 유지] 스토어 신뢰형 프롬프트
            system_message = """
            [Role] 당신은 스마트스토어 판매자입니다. 신뢰감 있는 정보 전달 위주로 작성하세요.
            [구조] 💐상품명, 🌸디자인, 👜기능성, 📏사이즈, 📦소재, 🧼관리법, 📍추천 7단락 구조 준수.
            """

        # [User Prompt] 오직 데이터만 전달 (어투 지시 포함 금지)
        user_input = f"""
        [Data]
        - Name: {name}
        - Material: {material}
        - Size: {size}
        - Duration: {duration}
        - Point: {point}
        - Image Feature: {img_desc}
        
        [지시사항]
        1. 작가가 입력한 정보를 최우선으로 반영하세요.
        2. 사진 정보가 입력 정보와 다르면 무시하세요.
        """
        
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content": system_message}, 
                {"role":"user","content": user_input}
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
        # 신규 필드 포함 초기화
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
            # Key 유일성 보장
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

# 데이터 안전 조회
c_name = curr.get('name', '')
c_mat = curr.get('material', '')
c_size = curr.get('size', '')
c_dur = curr.get('duration', '')
c_point = curr.get('point', '')
c_img_anl = curr.get('image_analysis', '')

c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 기본 정보 입력")
    
    # [입력 필드] 모든 위젯에 고유 Key 부여
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
    
    # 사진 업로더
    uploaded_img = st.file_uploader("작품 사진을 올리면 AI가 특징을 읽어줍니다", type=['png', 'jpg', 'jpeg'], key=f"uploader_{wid}")
    
    # 사진 분석 버튼
    if uploaded_img:
        if st.button("✨ 이 사진 특징 분석하기", key=f"btn_anal_{wid}"):
            with st.spinner("사진을 꼼꼼히 보고 있어요..."):
                analysis_result = analyze_image_features(uploaded_img)
                c_img_anl = analysis_result
                
                # 1. DB 저장
                curr.update({'image_analysis': c_img_anl})
                save_to_db(wid, curr)
                
                # 2. [필수] Session State 직접 갱신 (화면 출력 보장)
                st.session_state[f"input_img_anl_{wid}"] = analysis_result
                
                # 3. Rerun
                st.rerun()

    # 분석 결과 표시
    n_img_anl = st.text_area("AI가 분석한 사진 특징 (수정 가능)", value=c_img_anl, height=80, key=f"input_img_anl_{wid}", placeholder="사진을 올리고 분석 버튼을 누르면 채워집니다.")

    # 저장 로직
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
            # 생성 버튼
            if st.button(f"{platform_name} 글 짓기", key=f"btn_gen_{platform_key}_{wid}"):
                if not nn: st.toast("작품 이름을 먼저 입력해주세요! 😅")
                else:
                    with st.spinner(f"모그 작가님 말투로 {platform_name} 글을 쓰는 중..."):
                        # AI 생성
                        res = generate_copy(platform_name, nn, nm, ns, nd, np, n_img_anl)
                        
                        # 1. 변수 저장 및 DB 저장
                        texts[platform_key] = res
                        curr['texts'] = texts
                        save_to_db(wid, curr)
                        
                        # 2. [필수] Session State 직접 갱신 (화면 출력 보장)
                        st.session_state[f"result_{platform_key}_{wid}"] = res
                        
                        # 3. Rerun
                        st.rerun()
            
            # 결과 표시 (Key 충돌 방지 및 세션 상태 기반 출력)
            st.text_area("결과물", value=texts.get(platform_key,""), height=500, key=f"result_{platform_key}_{wid}")

    render_tab(tabs[0], "insta", "인스타")
    render_tab(tabs[1], "idus", "아이디어스")
    render_tab(tabs[2], "store", "스토어")
