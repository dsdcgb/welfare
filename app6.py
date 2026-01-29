import streamlit as st
from google import genai
from PyPDF2 import PdfReader
import os

# 1. 페이지 설정 및 디자인 (이전의 소프트 모던 스타일 유지)
st.set_page_config(page_title="Dalseo AI Manual", page_icon="✨", layout="wide")

# CSS 스타일 (가독성을 위해 핵심 부분만 유지)
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    /* 1. Pretendard 웹 폰트 불러오기 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* 2. 앱 전체 및 타이틀에 폰트 적용 */
    html, body, [class*="css"], .stApp, .main-title {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif !important;
    }
    .main-title {
        /* 1. 요청하신 글자 크기 및 두께 설정 */
        font-size: 2rem !important;
        font-weight: 700 !important;
        
        /* 2. 그라데이션 효과 (신뢰감 있는 블루 계열) */
        background: linear-gradient(90deg, #0d6efd 0%, #00d2ff 100%);
        -webkit-background-clip: text; /* 글자 모양대로 배경 자르기 */
        -webkit-text-fill-color: transparent !important; /* 글자 내부 색상을 투명하게 하여 배경 노출 */
        
        /* 3. 정렬 및 간격 조절 */
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 2rem;
        letter-spacing: -0.02em; /* 폰트를 더 세련되게 만드는 자간 조절 */
        
        /* 4. 애니메이션 효과 (선택 사항: 부드러운 느낌 추가) */
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 클라이언트 및 모델 설정 (Gemini 2.5 Flash)
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown('<p class="main-title">✨달서 복지서비스 도우미</p>', unsafe_allow_html=True)

# 3. PDF 자동 로드 로직
# 앱과 같은 폴더에 있는 'manual.pdf' 파일을 읽어옵니다.
PDF_FILE_PATH = "manual.pdf"  # ← 여기에 실제 파일 이름을 적어주세요.

if "pdf_text" not in st.session_state:
    if os.path.exists(PDF_FILE_PATH):
        with st.spinner("지정된 문서를 분석하는 중입니다..."):
            try:
                reader = PdfReader(PDF_FILE_PATH)
                text = "".join([page.extract_text() for page in reader.pages])
                st.session_state.pdf_text = text
                st.sidebar.success(f"✅ '{PDF_FILE_PATH}' 로드 완료!")
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    else:
        st.error(f"파일을 찾을 수 없습니다: '{PDF_FILE_PATH}' 파일이 소스 코드와 같은 폴더에 있는지 확인해주세요.")

# 세션 상태 관리 (메시지 기록)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 채팅 화면 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 처리
if prompt := st.chat_input("문서 내용에 대해 질문하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini 2.5 Flash 모델 호출
    system_instruction = f"당신은 문서 전문가입니다. 아래 내용을 바탕으로 친절하게 답하세요.\n\n{st.session_state.pdf_text}"
    
    with st.chat_message("assistant"):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": system_instruction}
        )
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})