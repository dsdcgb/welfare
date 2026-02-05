import streamlit as st
from google import genai
from PyPDF2 import PdfReader
import os

# 1. 페이지 설정 및 디자인 (Pretendard & 그라데이션 타이틀)
st.set_page_config(page_title="달서 복지 AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"], .stApp, .main-title {
        font-family: 'Pretendard', sans-serif !important;
    }
    .stApp { background-color: #f8f9fa; color: #212529; }
    .main-title {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #0d6efd 0%, #00d2ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent !important;
        text-align: center;
        margin-top: -1rem;
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
    }
    .stChatMessage {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #e9ecef !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 클라이언트 설정
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 타이틀 표시
st.markdown('<p class="main-title">✨ 달서 AI 복지 도우미</p>', unsafe_allow_html=True)

# 3. PDF 자동 로드 (캐싱 적용)
PDF_FILE_PATH = "manual.pdf" 

@st.cache_data
def get_pdf_text(path):
    if os.path.exists(path):
        reader = PdfReader(path)
        return "".join([page.extract_text() for page in reader.pages])
    return None

if "pdf_text" not in st.session_state:
    with st.spinner("복지 매뉴얼을 준비하는 중입니다..."):
        text = get_pdf_text(PDF_FILE_PATH)
        if text:
            st.session_state.pdf_text = text
        else:
            st.error(f"'{PDF_FILE_PATH}' 파일을 찾을 수 없습니다.")

# 세션 상태 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 처리 및 최신 스트리밍 방식 적용
if prompt := st.chat_input("복지 서비스에 대해 궁금한 점을 물어보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        system_instruction = f"""
        당신은 대구광역시 달서구의 사회복지업무 전문가입니다.
        1. 민원인의 질문에 제공된 [문서 내용]을 바탕으로 출처를 밝히지 않고 답변하세요.
        2. 문서에 없는 정보는 지어내지 말고 "죄송합니다. 정보가 없어 답변을 할 수 없습니다."라고 안내하세요.
        
        [문서 내용]
        {st.session_state.pdf_text}
        """
        
        try:
            # ✅ 해결 포인트: generate_content_stream() 함수 사용
            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": system_instruction}
            )

            # 스트리밍 텍스트를 하나씩 내보내는 제너레이터
            def stream_generator():
                for chunk in response_stream:
                    # chunk.text가 있는 경우에만 전달
                    if chunk.text:
                        yield chunk.text

            # st.write_stream을 이용해 화면에 타자 치듯 출력
            full_response = st.write_stream(stream_generator())
            
            # 최종 답변을 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")