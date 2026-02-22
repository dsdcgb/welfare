import streamlit as st
from google import genai
from PyPDF2 import PdfReader
import os
import re

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

    /* 1. 상단 헤더(Fork, GitHub 아이콘, 메뉴 바) 숨기기 */
    header {visibility: hidden;}
    
    /* 2. 하단 'Made with Streamlit' 푸터 숨기기 */
    footer {visibility: hidden;}
    
    /* 3. 오른쪽 상단 삼점 메뉴(#MainMenu) 숨기기 */
    #MainMenu {visibility: hidden;}
    
    /* 4. 우측 하단 빨간색 배포(Deploy) 버튼 숨기기 */
    .stDeployButton {display:none;}
    
    /* 5. (선택사항) 상단 여백 조절 - 헤더가 사라진 자리를 메워줍니다. */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 클라이언트 설정
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 타이틀 표시
st.markdown('<p class="main-title">달서 AI 복지 도우미</p>', unsafe_allow_html=True)

# 3. PDF 자동 로드 (캐싱 적용)
PDF_FILE_PATH = "manual.pdf" 

@st.cache_data(show_spinner="잠시만 기다려주세요. 😊")
def get_pdf_text(path):
    if os.path.exists(path):
        reader = PdfReader(path)
        return "".join([page.extract_text() for page in reader.pages])
    return None

if "pdf_text" not in st.session_state:
    # 최초 실행 시에만 PDF를 읽어 메모리에 저장합니다.
    text = get_pdf_text(PDF_FILE_PATH)
    if text:
        st.session_state.pdf_text = text
    else:
        st.error(f"'{PDF_FILE_PATH}' 파일을 찾을 수 없습니다.")

# 세션 상태 관리
if "messages" not in st.session_state:
# 처음 접속 시 어시스턴트가 먼저 환영 인사를 건넵니다.
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": """안녕하세요! **달서 AI 복지 도우미**입니다. 
주민 여러분께 꼭 필요한 복지 정보를 빠르고 정확하게 안내해 드립니다. 궁금하신 내용을 아래와 같이 질문해 보세요!

**🔍 이렇게 물어보세요:**
* "65세 이상 어르신이 받을 수 있는 혜택은 뭐야?"
* "갑자기 소득이 줄었는데 긴급지원 받을 수 있어?"
* "아동수당 신청 방법이랑 준비물 알려줘."
---
⚠️ 생성형 AI 기반 챗봇으로 답변이 부정확할 수 있으니, 반드시 담당 부서를 통해 정확한 내용을 확인하시기 바랍니다."""
        }
    ]

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
        주민들의 질문에 대해 아래 지침을 받드시 지켜 답변하세요.

        ## 답변 원칙
        1. **자연스러운 답변**: 답변 시 "복지업무편람의 어느 부분에서 참고했다", "제공된 문서에 따르면"과 같은 **출처에 대한 언급을 절대 하지 마세요.**
	2. **전문가 페르소나**: 마치 모든 내용을 숙지하고 있는 복지 담당 공무원처럼 바로 핵심 내용을 안내하세요.
        3. **근거 기반**: 오직 [문서 내용]에 있는 정보만을 바탕으로 답변하되, 문장은 당신의 언어로 재구성하여 친절하게 설명하세요.
	3. 문서에 전화번호 뒷자리 네자리만 있을 때는 앞에 "053-667-"를 붙혀서 표시합니다.
        4. **정보 부재 시**: 문서에 내용이 없다면 지어내지 말고 "죄송합니다. 해당 정보가 확인되지 않아 답변을 할 수 없습니다."라고 안내하세요.

        ## 인터넷 주소(URL) 안내 지침
        1. 인터넷 주소를 안내할 때는 반드시 **[사이트명](URL)** 형식을 사용하세요. 
          - 예: [문화누리 홈페이지](https://www.mnuri.kr)
        2. `www.`으로 시작하는 주소라도 반드시 앞에 **https://**를 붙여서 전체 경로를 작성하세요.
        3. 주소 뒤에 마침표(.)나 괄호())가 바로 붙지 않도록 주소 앞뒤에 반드시 **공백**을 한 칸씩 두세요.

        ## 출력 형식
        1. 답변은 불렛포인트(•)나 번호(1, 2, 3)를 사용하여 가독성 있게 구성하세요.
        2. 서비스(사업)별로 담당부서와 전화번호도 안내하세요.

        [문서 내용]
        {st.session_state.pdf_text}
        """
        
        try:
            # ✅ 해결 포인트: generate_content_stream() 함수 사용
            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 20,
                }
            )

            # 스트리밍 텍스트를 하나씩 내보내는 제너레이터
            def stream_generator():
                for chunk in response_stream:
                    # chunk.text가 있는 경우에만 전달
                    if chunk.text:
                        text = chunk.text
            
                        # 1. 취소선 및 도메인 공백 보정 (기존 로직)
                        text = text.replace("~", "\\~").replace("or. kr", "or.kr").replace("go. kr", "go.kr")
            
                        # (?<!https://)와 (?<!http://)를 나란히 배치하여 각각 확인하게 합니다.
                        text = re.sub(r'(?<!https://)(?<!http://)www\.', r'https://www.', text)
            
                        # 3. URL 주변 공백 확보 (괄호 잠식 방지)
                        url_pattern = r'(https?://[^\s()<>]+)'
                        text = re.sub(url_pattern, r' \1 ', text)
            
                        yield text

            # st.write_stream을 이용해 화면에 타자 치듯 출력
            full_response = st.write_stream(stream_generator())
            
            # 최종 답변을 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")