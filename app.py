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
    st.sidebar.success("✅ 작가님, 모그 AI 비서가 준비되었습니다.")

st.title("🕯️ 작가 '모그(Mog)' 전용 AI 통합 비서")
st.write("'세상에 단 하나뿐인 온기'를 전하는 작가님의 진심을 기록합니다.")

st.divider()

# --- [공통 입력 구역] ---
with st.expander("📦 작품 정보 입력 (글쓰기와 상세페이지에 사용됩니다)", expanded=True):
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        name = st.text_input("📦 작품 이름", placeholder="예: 파스텔 플라워 모티브 숄더백")
        keys = st.text_area("🔑 핵심 특징/이야기", placeholder="예: 사탕처럼 사랑스러운 컬러, 계절에 상관없는 포인트")
        mat = st.text_input("🧵 원단/소재", placeholder="예: 코튼, 폴리 혼방 등")
    with col_in2:
        size = st.text_input("📏 사이즈/수납", placeholder="예: 가로 33, 세로 25, 바닥폭 9cm")
        process = st.text_area("🛠️ 제작 포인트", placeholder="예: 하나하나 직접 떠서 연결, 인조 가죽 스트랩으로 튼튼함")
        care = st.text_input("💡 관리 방법/포장", placeholder="예: 세탁기 불가, 오염 시 부분 손세탁")

# --- 메인 탭 구성 ---
tabs = st.tabs(["✍️ 글쓰기 센터", "🎨 이미지 & 상세페이지", "📱 영상 제작 팁"])

# --- [Tab 1: 글쓰기 센터] (매체별 샘플 100% 반영) ---
with tabs[0]:
    st.header("✍️ 매체별 맞춤형 상세 글 생성")
    tab1, tab2, tab3 = st.tabs(["📸 인스타그램", "🎨 아이디어스", "🛍️ 스마트스토어"])

    def generate_text(platform_type, specific_prompt):
        if not api_key or not name:
            st.warning("작품 정보를 먼저 입력해주셔요.")
            return None

        client = openai.OpenAI(api_key=api_key)
        
        full_prompt = f"""
        당신은 핸드메이드 브랜드 '모그(Mog)'의 작가 본인입니다.
        제공된 플랫폼별 샘플 형식을 완벽하게 따라 [{platform_type}] 판매글을 작성하세요.

        [공통 어투]
        - 말투: 다정하고 조근조근한 어른의 말투 (~이지요^^, ~해요, ~좋아요).
        - 기호: 강조용 별표(**)는 절대 사용 금지. 이모지(🌻, 🌸, 🌷, 👜) 적극 활용.
        
        [플랫폼별 형식 지침]
        1. 인스타그램: 해시태그 먼저, 날씨/계절 인사를 포함한 감성 일기 스타일.
        2. 아이디어스: 짧은 문장 + 줄바꿈 매우 자주 + 꽃 이모지 풍성하게.
        3. 스마트스토어: 
           - 상단에 꽃다발(💐) 이모지와 제품명 배치.
           - 구분선(⸻)을 사용하여 섹션을 나눔.
           - '🌸 디자인 & 특징', '👜 기능성 & 내구성', '📏 사이즈', '📦 소재', '🧼 관리 방법', '📍 이런 분께 추천' 카테고리 필수 포함.
           - 불렛 포인트(•)를 사용하여 가독성 있게 정리.

        [제품 정보] 명칭:{name} / 특징:{keys} / 소재:{mat} / 사이즈:{size} / 제작진심:{process} / 관리:{care}

        {specific_prompt}
        """
        
        with st.spinner(f"작가님의 감성을 담아 글을 짓고 있어요..."):
            try:
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": full_prompt}])
                clean_text = response.choices[0].message.content.replace("**", "")
                return clean_text.strip()
            except Exception as e:
                st.error(f"오류가 발생했어요: {e}")
                return None

    with tab1:
        if st.button("🪄 인스타용 글 만들기"):
            instr = "인스타그램 게시물입니다. 해시태그와 함께 원단의 촉감, 계절의 온기를 느낄 수 있는 감성 일기 형식으로 작성하세요."
            result = generate_text("인스타그램", instr)
            if result: st.text_area("인스타 결과", value=result, height=450)

    with tab2:
        if st.button("🪄 아이디어스용 글 만들기"):
            instr = "아이디어스 판매글입니다. 한 줄에 한 문장만 나오도록 줄바꿈을 아주 많이 하고, 꽃 이모지로 정성을 표현하세요."
            result = generate_text("아이디어스", instr)
            if result: st.text_area("아이디어스 결과", value=result, height=600)

    with tab3:
        if st.button("🪄 스마트스토어용 글 만들기"):
            instr = "스마트스토어용입니다. 구분선(⸻)과 카테고리를 활용해 정보를 꼼꼼하고 가독성 있게 정리하세요. 마지막엔 태그 10개 이상 달아주세요."
            result = generate_text("스마트스토어", instr)
            if result: st.text_area("스토어 결과", value=result, height=700)

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
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": [{"type": "text", "text": "화사하고 빈티지한 느낌의 보정 수치 JSON."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}]}],
                        response_format={ "type": "json_object" }
                    )
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
        st.header("🎨 캔바(Canva) 제작")
        st.link_button("✨ 캔바 상세페이지 양식 열기", "https://www.canva.com/templates/?query=상세페이지", use_container_width=True)
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
