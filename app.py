import streamlit as st
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import io
import openai
import base64
import json
from streamlit_drawable_canvas import st_canvas  # 🖌️ 직접 그리기 도구 추가

# 1. 페이지 설정
st.set_page_config(page_title="모그 AI 비서", layout="centered")

# --- CSS: 다크모드 및 모바일 시인성 ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] { color: inherit; }
    h1, h2, h3 { color: #D4A373 !important; font-weight: bold !important; margin-bottom: 12px; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.8em;
        background-color: #7d6e63; color: white !important;
        font-weight: bold; font-size: 18px !important;
        border: none; margin-bottom: 8px;
    }
    .stTextArea textarea {
        font-size: 17px !important;
        line-height: 1.6 !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: inherit !important;
        border: 1px solid #7d6e63 !important;
    }
    hr { border-top: 1px solid #7d6e63; opacity: 0.3; }
    </style>
    """, unsafe_allow_html=True)

# --- API 키 설정 ---
api_key = st.secrets.get("OPENAI_API_KEY")

st.title("🕯️ 모그(Mog) 작가 전용 비서")
st.write("<p style='text-align: center;'>작가님의 따뜻한 진심이 글에 그대로 담기도록 도와드려요🌸</p>", unsafe_allow_html=True)

# --- [1단계: 정보 입력] ---
st.header("1️⃣ 작품 정보 입력")
with st.expander("📝 이곳을 눌러 내용을 작성해주세요", expanded=True):
    name = st.text_input("📦 작품 이름", placeholder="예: 빈티지 튤립 뜨개 파우치")
    c1, c2 = st.columns(2)
    with c1:
        mat = st.text_input("🧵 소재", placeholder="코튼 100%")
        size = st.text_input("📏 크기", placeholder="20*15cm")
    with c2:
        period = st.text_input("⏳ 제작 기간", placeholder="주문 후 3일")
        care = st.text_input("💡 세탁 방법", placeholder="미온수 손세탁 권장")
    keys = st.text_area("🔑 작품 특징", placeholder="색감이 화사해서 포인트 아이템으로 좋아요.")
    process = st.text_area("🛠️ 제작 포인트", placeholder="안감까지 꼼꼼히 제작했습니다.")

st.divider()

# --- AI 처리 함수 (어투 지침 강화) ---
def process_mog_ai(platform_guide):
    if not api_key: return None
    client = openai.OpenAI(api_key=api_key)
    
    # [핵심 어투 프롬프트]
    mog_tone_prompt = f"""
    당신은 핸드메이드 브랜드 '모그(Mog)'를 운영하는 작가입니다. 
    다음 지침을 반드시 지켜서 [{platform_guide['name']}] 판매글을 작성하세요.

    [어투 지침 - 가장 중요]
    - 말투: 50대 여성 작가의 다정하고 따뜻한 말투를 사용하세요.
    - 어미: '~이지요^^', '~해요', '~좋아요', '~보내드려요'를 주로 사용하세요.
    - 금지 사항: 절대로 별표(*)나 볼드체(**) 같은 특수 기호를 사용하지 마세요. 
    - 이모지: 꽃(🌸,🌻), 구름(☁️), 반짝이(✨)를 적절히 섞어주세요.

    [플랫폼 지침]
    - {platform_guide['desc']}

    [작품 정보]
    이름: {name} / 소재: {mat} / 크기: {size} / 기간: {period} / 관리: {care}
    특징: {keys} / 포인트: {process}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": mog_tone_prompt}]
        )
        return response.choices[0].message.content.replace("**", "").replace("*", "").strip()
    except:
        return "오류가 발생했습니다. 다시 시도해 주세요."

# --- [2단계: 작업실 선택] ---
st.header("2️⃣ 작업실 선택")
tabs = st.tabs(["✍️ 판매글 쓰기", "📸 사진보정", "💡 캔바 & 에픽", "💬 고민 상담소"])

# --- Tab 1: 판매글 쓰기 ---
with tabs[0]:
    if 'texts' not in st.session_state:
        st.session_state.texts = {"인스타그램": "", "아이디어스": "", "네이버 스마트스토어": ""}

    st.write("💡 아래 버튼을 누르면 작가님 말투로 글이 써집니다.")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    # 1. 인스타그램: 작가님 샘플의 '감성 일기' 스타일
    if btn_col1.button("📸 인스타그램"):
        insta_guide = {
            "name": "인스타그램",
            "desc": """
            - 분위기: 친구에게 편지를 쓰듯, 혹은 일기장에 기록하듯 다정하고 포근한 느낌
            - 문장 지침: 
                * "오늘 창가로 들어오는 햇살이 참 좋아서 한 컷 찍어봤어요🌸" 같은 계절감 있는 인사로 시작하세요.
                * "요 작은 아이가 누구에게 가서 행복을 줄지 상상만 해도 설레요✨" 같은 작가님의 마음을 담아주세요.
            - 구성: [날씨/일상 인사] + [제작 비하인드] + [다정한 상세정보] + [해시태그]
            - 가이드: 줄바꿈을 아주 넉넉히 하고, 기호(*) 대신 반짝이와 구름 이모지를 사용해 주세요.
            """
        }
        st.session_state.texts["인스타그램"] = process_mog_ai(insta_guide)
        
    # 2. 아이디어스: 작가님 샘플의 '느리지만 정직한' 스타일
    if btn_col2.button("🎨 아이디어스"):
        idus_guide = {
            "name": "아이디어스",
            "desc": """
            - 분위기: 서두르지 않고 차분하게, 작품에 담긴 온기를 조곤조곤 설명하는 느낌
            - 문장 지침: 
                * "작가인 제가 직접 써보고 좋아서 만들기 시작했어요"라는 진솔함을 담아주세요.
                * "기다려주시는 마음을 알기에 포장 하나도 허투루 하지 않아요"라는 문구를 녹여주세요.
            - 핵심 단어: '느리지만 정직하게', '따스한 선물', '마음을 담아', '한 코 한 코'
            - 가이드: 매우 잦은 줄바꿈을 사용하여 정성스럽게 쓴 느낌을 주고, 꽃(🌸)과 잎새(🌿) 이모지를 적절히 섞어주세요.
            """
        }
        st.session_state.texts["아이디어스"] = process_mog_ai(idus_guide)
        
    # 3. 스마트스토어: 작가님 샘플의 '친절한 안부' 스타일
    if btn_col3.button("🛍️ 스마트스토어"):
        store_guide = {
            "name": "네이버 스마트스토어",
            "desc": """
            - 분위기: 멀리 있는 지인에게 작품을 소개하듯 다정하고 신뢰감 있는 느낌
            - 문장 지침: 
                * "작가인 제가 꼼꼼하게 골라온 소재들이에요"라며 품질에 대한 다정한 확신을 주세요.
                * "세탁은 이렇게 하시면 오래오래 예쁘게 쓰실 수 있답니다^^" 같은 친절한 가이드를 포함하세요.
            - 구성: 구분선(⸻)을 활용하여 [작가 인삿말] - [소재/사이즈] - [세탁/관리] 순서로 정리
            """
        }
        st.session_state.texts["네이버 스마트스토어"] = process_mog_ai(store_guide)

# 결과물 출력 및 수정 로직
    for p_key in ["인스타그램", "아이디어스", "네이버 스마트스토어"]:
        if st.session_state.texts[p_key]:
            st.write(f"---")
            st.write(f"**✅ {p_key} 결과물이에요!**")
            
            # 입력창 (사용자가 여기서 직접 수정도 가능)
            # value를 session_state와 직접 연결합니다.
            st.session_state.texts[p_key] = st.text_area(
                f"{p_key} 내용", 
                value=st.session_state.texts[p_key], 
                height=350, 
                key=f"area_{p_key}"
            )
            
            # 수정 요청 칸
            with st.expander(f"✨ {p_key} 글을 AI에게 다시 부탁하기"):
                # 폼 없이 버튼 클릭 시 바로 변수를 참조하도록 함
                new_feedback = st.text_input("어떻게 고쳐드릴까요?", placeholder="예: 조금 더 짧게, 더 다정하게", key=f"feed_{p_key}")
                
                if st.button("♻️ 다시 정성껏 쓰기", key=f"btn_re_{p_key}"):
                    if not new_feedback:
                        st.warning("고칠 내용을 적어주셔요🌸")
                    else:
                        with st.spinner("작가님 마음을 담아 다시 고쳐 쓰는 중..."):
                            # 현재 창에 떠있는 글(st.session_state.texts[p_key])을 바탕으로 다시 씁니다.
                            refine_prompt = {
                                "name": p_key,
                                "desc": f"원래 쓴 글: {st.session_state.texts[p_key]}\n\n요청사항: {new_feedback}\n\n위 내용을 반영해서 작가님 말투로 다시 써주세요."
                            }
                            # 결과 업데이트
                            st.session_state.texts[p_key] = process_mog_ai(refine_prompt)
                            # 페이지 강제 새로고침 (수정된 글을 보여주기 위함)
                            st.rerun()



# --- Tab 2: 사진보정 ---
with tabs[1]:
    st.subheader("📸 AI 섬세한 사진 작업실")
    st.write("AI가 사진의 밝기, 색감, 질감을 아주 섬세하게 분석하여 원본보다 조금 더 화사하고 깔끔하게만 다듬어 드려요.")
    
    uploaded_files = st.file_uploader("작업할 사진 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files and api_key:
        c1, c2 = st.columns(2)
        
        # --- 기능 1: AI 섬세 자율 보정 ---
        if c1.button("✨ AI 섬세 보정 시작"):
            client = openai.OpenAI(api_key=api_key)
            def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')
            
            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                with st.spinner(f"{idx+1}번 사진을 조심스럽게 분석 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": """당신은 핸드메이드 작품 전문 사진가입니다. 
                                다음 가이드를 바탕으로 이 사진의 최적 보정 수치를 결정하세요. 
                                이미지가 하얗게 날아가거나(Overexposed) 인위적으로 보이지 않게 하는 것이 가장 중요합니다.

                                [보정 철학]
                                1. 자연스러움: 원본의 분위기를 최대한 유지하세요.
                                2. 밝기(brightness): 사진이 어두울 때만 '아주 미세하게' 높이세요 (최대 1.15). 충분히 밝다면 1.0을 유지하세요.
                                3. 대비(contrast): 상품이 흐릿할 때만 아주 살짝 높이세요 (최대 1.1).
                                4. 채도(saturation): 색감을 생기 있게 만들되 과하지 않게 (0.95~1.1).
                                5. 선명도(sharpness): 질감이 보일 정도로만 살짝 높이세요 (최대 1.3).

                                오직 JSON 형식으로만 답하세요: 
                                {"brightness": n, "contrast": n, "saturation": n, "sharpness": n}"""},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}
                            ]}],
                            response_format={ "type": "json_object" }
                        )
                        res = json.loads(response.choices[0].message.content)
                        img = Image.open(io.BytesIO(img_bytes))
                        img = ImageOps.exif_transpose(img)
                        if img.mode == 'RGBA': img = img.convert('RGB')
                        
                        img = ImageEnhance.Brightness(img).enhance(res.get('brightness', 1.0))
                        img = ImageEnhance.Contrast(img).enhance(res.get('contrast', 1.0))
                        img = ImageEnhance.Color(img).enhance(res.get('saturation', 1.0))
                        img = ImageEnhance.Sharpness(img).enhance(res.get('sharpness', 1.0))
                        
                        st.image(img, caption=f"✅ {idx+1}번 자연스러운 보정 완료")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=95)
                        st.download_button(f"📥 {idx+1}번 사진 저장", buf.getvalue(), f"mog_natural_{idx+1}.jpg", key=f"dl_{idx}")
                    except:
                        st.error(f"{idx+1}번 보정 실패🌸")

        # --- 기능 2: 얼굴 모자이크 (AI 정밀 감지) ---
        if c2.button("👤 정밀 얼굴 모자이크 시작"):
            client = openai.OpenAI(api_key=api_key)
            def encode_image(image_bytes): return base64.b64encode(image_bytes).decode('utf-8')

            for idx, file in enumerate(uploaded_files):
                img_bytes = file.getvalue()
                raw_img = Image.open(io.BytesIO(img_bytes))
                raw_img = ImageOps.exif_transpose(raw_img)
                w, h = raw_img.size

                with st.spinner(f"{idx+1}번 사진에서 얼굴 탐색 중..."):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": [
                                {"type": "text", "text": f"이 이미지(가로 {w}px, 세로 {h}px)에서 실제 사람의 얼굴만 찾아 [ymin, xmin, ymax, xmax] (0~1000 기준) 리스트로 답하세요. JSON 형식: {{'faces': [[...]]}}"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(img_bytes)}"}}
                            ]}],
                            response_format={ "type": "json_object" }
                        )
                        res = json.loads(response.choices[0].message.content)
                        faces = res.get('faces', [])
                        img = raw_img.copy()
                        if not faces:
                            st.info(f"💡 {idx+1}번 사진은 가릴 얼굴을 찾지 못했어요.")
                        else:
                            for face in faces:
                                ymin, xmin, ymax, xmax = face
                                left, top, right, bottom = (xmin/1000)*w, (ymin/1000)*h, (xmax/1000)*w, (ymax/1000)*h
                                # 영역 확장 및 모자이크
                                face_area = img.crop((int(left-10), int(top-10), int(right+10), int(bottom+10)))
                                mosaic = face_area.resize((15, 15), resample=Image.BILINEAR).resize(face_area.size, resample=Image.NEAREST)
                                img.paste(mosaic, (int(left-10), int(top-10)))
                            st.image(img, caption=f"👤 {idx+1}번 얼굴 보호 완료")
                            buf = io.BytesIO(); img.save(buf, format="JPEG", quality=95)
                            st.download_button(f"📥 {idx+1}번 저장하기", buf.getvalue(), f"mog_face_{idx+1}.jpg", key=f"btn_face_{idx}")
                    except:
                        st.error(f"{idx+1}번 처리 오류🌸")

# --- ✨ 기능 3 대신: 에픽(EPIK)에서 직접 가리는 법 안내 ---
    st.divider()
    st.subheader("🎨 AI가 얼굴을 못 찾았다면? (에픽 앱 활용법)")
    st.write("스마트폰 앱 **'에픽(EPIK)'**을 쓰면 손가락으로 슥슥 문질러서 아주 예쁘게 얼굴을 가릴 수 있어요!")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info("""
        **1. 에픽 앱에서 사진 열기**
        * 앱 실행 후 **[편집]**을 누르고 보정한 사진을 선택하세요.
        
        **2. [도구] 메뉴 찾기**
        * 하단 메뉴를 옆으로 밀어서 **[도구]** 버튼을 찾아 누르세요.
        """)
    with col_info2:
        st.info("""
        **3. [모자이크] 선택**
        * **[모자이크]** 아이콘을 누르면 여러 가지 예쁜 무늬가 나와요.
        
        **4. 얼굴 슥슥 문지르기**
        * 가리고 싶은 얼굴 위를 손가락으로 문지르면 끝! 오른쪽 위 **[저장]**을 누르세요.
        """)
    
    st.success("💡 팁: 에픽에서는 모자이크 대신 귀여운 '스티커'를 얼굴에 붙여도 정말 예쁘답니다🌸")
                
                
# --- Tab 3: 캔바 & 에픽 (더 자세하고 친절한 설명) ---
with tabs[2]:
    st.subheader("🎨 예쁜 상세페이지와 영상 만들기")
    st.write("작품 사진을 예쁜 배경에 넣거나, 음악이 흐르는 홍보 영상을 만드는 방법을 알려드릴게요. 🌸")
    
    # --- 캔바(Canva) 섹션 ---
    st.markdown("### 1️⃣ 사진을 잡지처럼! '캔바(Canva)'")
    st.write("""
    캔바는 **작품 사진을 넣기만 하면 멋진 잡지나 홍보지**처럼 만들어주는 앱이에요. 
    직접 디자인하기 어려우실 때 AI가 미리 짜주는 기획안을 참고해 보세요!
    """)
    
    if st.button("🪄 AI가 추천하는 페이지 구성 보기"):
        if not name: 
            st.warning("위쪽 '1️⃣ 작품 정보'를 먼저 입력해 주시면 더 정확하게 짜드려요🌸")
        else:
            with st.spinner("작가님을 위해 기획안을 작성 중입니다..."):
                # 상세페이지 기획용 프롬프트
                canva_prompt = {
                    "name": "상세페이지 기획",
                    "desc": f"""
                    당신은 핸드메이드 전문가입니다. 50대 작가님이 이해하기 쉽게 '{name}' 작품의 상세페이지 기획안을 짜주세요.
                    - 말투는 다정하게 (~이지요^^, ~해요)
                    - 1페이지: 첫인상 (어떤 느낌의 사진과 문구)
                    - 2페이지: 작품의 디테일 (소재, 정성)
                    - 3페이지: 크기 및 구성 정보
                    - 4페이지: 작가의 한마디 (브랜드 스토리)
                    - 5페이지: 구매 및 세탁 안내
                    - 복잡한 용어 없이 텍스트로만 친절히 설명하세요.
                    """
                }
                st.info(process_mog_ai(canva_prompt))

    st.link_button("✨ 캔바 앱 바로가기", "https://www.canva.com/templates/?query=상세페이지")
    st.caption("💡 팁: 캔바 앱 검색창에 '상세페이지'나 '핸드메이드'를 검색하면 예쁜 양식이 아주 많아요.")

    st.divider()

    # --- 에픽(EPIK) 섹션 ---
    st.markdown("### 2️⃣ 음악이 흐르는 영상 만들기! '에픽(EPIK)'")
    st.write("작품 사진 여러 장으로 **음악이 나오는 멋진 홍보 영상**을 1분 만에 만들 수 있어요.")
    
    with st.expander("📺 천천히 따라해보세요 (에픽 사용법)", expanded=True):
        st.markdown("""
        **1. 앱 실행 및 [템플릿] 누르기**
        * 스마트폰에서 **[EPIK]** 앱을 열고 하단 메뉴에서 **[템플릿]**을 누르세요.
        
        **2. 어울리는 분위기 검색**
        * 상단 검색창에 **'감성'**, **'봄'**, **'뜨개'** 또는 **'Handmade'**라고 검색해 보세요.
        
        **3. 사진 선택하기**
        * 맘에 드는 영상틀을 골라 **[사용하기]**를 누른 뒤, 아까 보정했던 예쁜 사진들을 순서대로 선택해 주세요.
        
        **4. 음악과 함께 저장**
        * 오른쪽 위 **[저장]** 버튼을 누르면 끝! 갤러리에 음악이 나오는 멋진 영상이 생깁니다. 🌸
        """)
        st.info("💡 이렇게 만든 영상은 인스타그램 '릴스'나 아이디어스 '작가소식'에 올리면 효과가 아주 좋아요!")

    st.divider()
    st.write("<p style='text-align: center; color: #7d6e63;'>오늘도 작가님의 따뜻한 손길을 응원합니다. 화이팅! 🕯️</p>", unsafe_allow_html=True)

# --- Tab 4: 무엇이든 물어보세요 (신설) ---
with tabs[3]:
    st.subheader("💬 모그 작가님 고민 상담소")
    st.write("작품 활동을 하시며 궁금한 점이나 고민이 있다면 무엇이든 물어보세요. 다정하게 대답해 드릴게요. 🌸")
    
    # 질문 입력창
    user_question = st.text_area("✍️ 궁금한 내용을 적어주세요", 
                                placeholder="예: 뜨개 파우치에 어울리는 예쁜 이름을 추천해줘.\n손님이 배송이 늦어진다고 문의했는데 어떻게 답장하면 좋을까?",
                                height=150)
    
    if st.button("🕯️ AI 작가에게 물어보기"):
        if not user_question:
            st.warning("질문을 먼저 입력해 주셔요🌸")
        elif not api_key:
            st.error("API 키가 설정되지 않았어요.")
        else:
            with st.spinner("작가님의 고민을 함께 나누는 중입니다..."):
                try:
                    client = openai.OpenAI(api_key=api_key)
                    
                    # 상담소 전용 다정한 프롬프트
                    advice_prompt = f"""
                    당신은 핸드메이드 작가들의 다정한 선배이자 동료인 '모그 AI'입니다. 
                    50대 여성 작가님의 고민에 대해 다음 규칙을 지켜 답변하세요.
                    
                    1. 말투: 매우 다정하고 따뜻하게 (~이지요^^, ~해요, ~보내드려요)
                    2. 내용: 구체적이고 실질적인 도움을 줄 것
                    3. 금지: 별표(*)나 볼드체(**) 같은 특수 기호는 절대 사용하지 말 것
                    4. 응원: 마지막에는 항상 작가님의 활동을 응원하는 따뜻한 말을 덧붙일 것
                    
                    질문 내용: {user_question}
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": advice_prompt}]
                    )
                    
                    answer = response.choices[0].message.content.replace("**", "").replace("*", "").strip()
                    
                    st.write("---")
                    st.write("### 🕯️ 모그 AI의 다정한 답변")
                    st.info(answer)
                    
                except:
                    st.error("답변을 가져오는 중에 작은 오류가 생겼어요. 잠시 후 다시 물어봐 주세요🌸")

    st.divider()
    st.caption("💡 팁: '작품 이름 추천', '인스타그램 댓글 답장', '계절 인사말' 등을 물어보시면 아주 좋아요.")
