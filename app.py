import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance
import io
import openai
import base64
import json

# 1. 앱 페이지 설정
st.set_page_config(page_title="핸드메이드 잡화점 모그 AI 비서", layout="wide")

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.sidebar.header("⚙️ AI 설정")
    api_key = st.sidebar.text_input("OpenAI API Key를 넣어주세요", type="password")
else:
    st.sidebar.success("✅ 작가님, 모그 AI 비서가 연결되었습니다.")

st.title("🕯️ 작가 '모그(Mog)' 전용 AI 통합 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 작가님의 진심을 기록합니다.")

st.divider()

# --- [공통 입력 구역] ---
with st.expander("📦 작업할 작품 정보 입력", expanded=True):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        name = st.text_input("📦 작품 이름", placeholder="예: 파스텔 플라워 모티브 숄더백")
        keys = st.text_area("🔑 핵심 특징/이야기", placeholder="예: 사탕처럼 사랑스러운 컬러, 계절에 상관없는 포인트")
        mat = st.text_input("🧵 원단/소재", placeholder="예: 코튼, 폴리 혼방 등")
    with col_in2:
        size = st.text_input("📏 사이즈/수납", placeholder="예: 가로 33, 세로 25, 바닥폭 9cm")
        period = st.text_input("⏳ 제작 기간", placeholder="예: 주문 후 제작, 평일 기준 3~5일 소요")
        process = st.text_area("🛠️ 제작 포인트", placeholder="예: 하나하나 직접 떠서 연결, 인조 가죽 스트랩으로 튼튼함")
        care = st.text_input("💡 관리 방법/포장", placeholder="예: 세탁기 불가, 오염 시 부분 손세탁")

# --- 메인 탭 구성 ---
tabs = st.tabs(["✍️ 글쓰기 센터", "🎨 이미지 & 상세페이지", "📱 영상 제작 팁"])

# --- [글 생성 및 수정 함수] ---
def process_ai_text(full_prompt):
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
        clean_text = response.choices[0].message.content.replace("**", "")
        return clean_text.strip()
    except Exception as e:
        st.error(f"오류가 발생했어요: {e}")
        return None

# --- [Tab 1: 글쓰기 센터] ---
with tabs[0]:
    st.header("✍️ 매체별 맞춤형 상세 글 생성")
    if 'generated_texts' not in st.session_state:
        st.session_state.generated_texts = {"인스타그램": "", "아이디어스": "", "스마트스토어": ""}
    sub_tabs = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])
    platforms = ["인스타그램", "아이디어스", "스마트스토어"]
    for i, platform in enumerate(platforms):
        with sub_tabs[i]:
            if st.button(f"🪄 {platform}용 글 만들기"):
                platform_prompts = {
                    "인스타그램": "해시태그 포함, 계절 인사 포함, 감성 일기 스타일.",
                    "아이디어스": "짧은 문장, 줄바꿈 매우 자주, 꽃 이모지 풍성하게.",
                    "스마트스토어": "구분선(⸻)과 카테고리 활용, 정보 꼼꼼히 정리, 마지막 태그 포함."
                }
                full_prompt = f"당신은 브랜드 '모그(Mog)' 작가입니다. [{platform}] 스타일로 작성하세요. [어투] ~이지요^^, ~해요, ~좋아요 / 별표 금지 / 이모지 활용. 이름:{name}, 특징:{keys}, 소재:{mat}, 사이즈:{size}, 제작:{process}, 관리:{care}, 기간:{period}. 지침: {platform_prompts[platform]}"
                st.session_state.generated_texts[platform] = process_ai_text(full_prompt)
            if st.session_state.generated_texts[platform]:
                current_text = st.text_area(f"📄 {platform} 결과", value=st.session_state.generated_texts[platform], height=400, key=f"text_{platform}")
                st.divider()
                st.subheader("💡 작가님, 수정하고 싶은 부분이 있으신가요?")
                feedback = st.text_input("수정 요청 (예: 조금 더 짧게 써줘, 원단의 부드러움을 더 강조해줘)", key=f"feed_{platform}")
                if st.button("♻️ 요청대로 다시 고쳐쓰기", key=f"btn_{platform}"):
                    refine_prompt = f"기존 글: {current_text} \n요청사항: {feedback} \n위 내용을 반영해 작가님 말투로 다시 작성하세요."
                    new_text = process_ai_text(refine_prompt)
                    if new_text:
                        st.session_state.generated_texts[platform] = new_text
                        st.rerun()

# --- [Tab 2: 이미지 & 상세페이지] ---
with tabs[1]:
    col_img1, col_img2 = st.columns([1, 1.2])
    with col_img1:
        st.header("📸 사진 자동 보정")
        uploaded_files = st.file_uploader("보정할 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')
        if uploaded_files and api_key and st.button("🚀 사진 일괄 보정"):
            client = openai.OpenAI(api_key=api_key)
            cols = st.columns(2)
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                try:
                    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": "화사한 보정 수치 JSON."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}], response_format={ "type": "json_object" })
                    res = json.loads(response.choices[0].message.content)
                    img = Image.open(io.BytesIO(img_bytes))
                    edited = ImageEnhance.Brightness(img).enhance(res.get('b', 1.15))
                    edited = ImageEnhance.Color(edited).enhance(res.get('c', 1.1))
                    with cols[idx % 2]:
                        st.image(edited, use_container_width=True)
                        buf = io.BytesIO()
                        edited.save(buf, format="JPEG")
                        st.download_button(f"📥 저장 {idx+1}", buf.getvalue(), f"img_{idx+1}.jpg")
                except Exception as e: st.error(f"오류: {e}")

    with col_img2:
        st.header("🎨 캔바(Canva) 상세페이지 제작")
        
        # --- 캔바 사용 안내 출력 ---
        st.info("""
        **🎨 작가님을 위한 캔바 작업실 사용법**
        1. **내용 만들기**: 아래 '🪄 캔바 대량 제작용 데이터 생성' 버튼을 누르세요.
        2. **파일 저장**: 생성된 표 아래 '📥 캔바 CSV 받기'를 눌러 컴퓨터에 저장하세요.
        3. **캔바 열기**: '✨ 캔바 양식 작업실 열기' 버튼을 눌러 마음에 드는 디자인을 고르세요.
        4. **대량 제작**: 캔바 왼쪽 메뉴 [앱] -> [대량 제작] -> [CSV 업로드]를 통해 방금 받은 파일을 넣으세요.
        5. **연결하기**: 디자인의 글자를 오른쪽 클릭하고 [데이터 연결]을 누르면 글이 자동으로 쏙 들어간답니다!
        """)
        
        st.link_button("✨ 캔바 상세페이지 양식 작업실 열기", "https://www.canva.com/templates/?query=상세페이지", use_container_width=True)
        
        st.divider()
        if st.button("🪄 캔바 대량 제작용 데이터 생성"):
            if not name: st.warning("정보를 먼저 입력해주셔요.")
            else:
                client = openai.OpenAI(api_key=api_key)
                prompt = f"모그 작가로서 {name} 상세페이지 5장 기획. JSON [{{'순서':'1','메인문구':'..','설명':'..','사진구도':'..'}}] 형식. 별표 금지."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type":"json_object"})
                data = json.loads(res.choices[0].message.content)
                df = pd.DataFrame(data[list(data.keys())[0]])
                st.table(df)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 캔바 CSV 받기", csv, f"moog_{name}.csv", "text/csv", use_container_width=True)

# --- [Tab 3: 영상 제작 팁] ---
with tabs[2]:
    st.header("📱 에픽(EPIK) 활용 팁")
    st.info("에픽 앱의 '핸드메이드' 템플릿을 활용해 보세요. 정성 들여 보정한 사진만 넣으면 모그만의 따뜻한 영상이 완성되지요🌸")
