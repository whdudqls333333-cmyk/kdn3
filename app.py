import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

CONFIG_FILE = "config.json"

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
]

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 1.0,
    "system_prompt": "You are a helpful assistant.",
}


def load_config() -> dict:
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def test_connection(api_key: str, model: str) -> tuple[bool, str]:
    if not OPENAI_AVAILABLE:
        return False, "openai 패키지가 설치되지 않았습니다. `pip install openai`를 실행하세요."
    if not api_key:
        return False, "API 키를 입력하세요."
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' in one word."}],
            max_tokens=5,
        )
        reply = response.choices[0].message.content.strip()
        return True, f"연결 성공! 모델 응답: {reply}"
    except Exception as e:
        return False, f"연결 실패: {str(e)}"


def send_message(api_key: str, config: dict, messages: list) -> str:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "system", "content": config["system_prompt"]}] + messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
    )
    return response.choices[0].message.content


MESSENGER_CSS = """
<style>
/* ── 메신저 전체 컨테이너 ── */
.chat-wrapper {
    background: #abc1d1;
    border-radius: 16px;
    padding: 0;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    max-width: 480px;
    margin: 0 auto;
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
}

/* ── 헤더 ── */
.chat-header {
    background: #3c1e1e;
    color: white;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.chat-header .bot-avatar {
    width: 38px; height: 38px;
    background: #fee500;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.chat-header .bot-name { font-weight: 700; font-size: 15px; }
.chat-header .bot-status { font-size: 11px; color: #aaa; }

/* ── 메시지 스크롤 영역 ── */
.chat-body {
    background: #abc1d1;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 420px;
    max-height: 520px;
    overflow-y: auto;
}

/* ── 날짜 구분선 ── */
.date-divider {
    text-align: center;
    font-size: 11px;
    color: #fff;
    background: rgba(0,0,0,0.2);
    border-radius: 10px;
    padding: 3px 10px;
    width: fit-content;
    margin: 4px auto;
}

/* ── 메시지 행 공통 ── */
.msg-row {
    display: flex;
    align-items: flex-end;
    gap: 6px;
}
.msg-row.user  { justify-content: flex-end; }
.msg-row.bot   { justify-content: flex-start; }

/* ── 아바타 ── */
.avatar {
    width: 36px; height: 36px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    align-self: flex-start;
}
.avatar.bot-av { background: #fee500; }

/* ── 말풍선 그룹 ── */
.bubble-group { display: flex; flex-direction: column; gap: 3px; max-width: 72%; }
.bubble-group.user { align-items: flex-end; }
.bubble-group.bot  { align-items: flex-start; }

.sender-name { font-size: 11px; color: #444; margin-bottom: 2px; padding-left: 2px; }

/* ── 말풍선 ── */
.bubble {
    padding: 9px 13px;
    border-radius: 18px;
    font-size: 13.5px;
    line-height: 1.5;
    word-break: break-word;
    white-space: pre-wrap;
}
.bubble.user {
    background: #fee500;
    color: #111;
    border-radius: 18px 18px 4px 18px;
}
.bubble.bot {
    background: #ffffff;
    color: #111;
    border-radius: 4px 18px 18px 18px;
}

/* ── 시간 + 읽음 ── */
.meta {
    font-size: 10px;
    color: rgba(0,0,0,0.45);
    flex-shrink: 0;
    margin-bottom: 2px;
}
.meta.user { text-align: right; }

/* ── 입력창 영역 ── */
.chat-footer {
    background: #f0f0f0;
    padding: 8px 10px;
    display: flex;
    gap: 8px;
    border-top: 1px solid #ddd;
    align-items: center;
    font-size: 12px;
    color: #888;
}

/* Streamlit chat_input 위치 조정 */
section[data-testid="stBottom"] { background: transparent !important; }
</style>
"""


def render_messenger(messages: list, model_name: str):
    now_date = datetime.now().strftime("%Y년 %m월 %d일")

    bubbles_html = ""
    for msg in messages:
        ts = msg.get("time", "")
        content = msg["content"].replace("<", "&lt;").replace(">", "&gt;")

        if msg["role"] == "user":
            bubbles_html += f"""
            <div class="msg-row user">
                <div class="meta user">{ts}</div>
                <div class="bubble-group user">
                    <div class="bubble user">{content}</div>
                </div>
            </div>"""
        else:
            bubbles_html += f"""
            <div class="msg-row bot">
                <div class="avatar bot-av">🤖</div>
                <div class="bubble-group bot">
                    <span class="sender-name">{model_name}</span>
                    <div class="bubble bot">{content}</div>
                </div>
                <div class="meta">{ts}</div>
            </div>"""

    html = f"""
    <div class="chat-wrapper">
        <div class="chat-header">
            <div class="bot-avatar">🤖</div>
            <div>
                <div class="bot-name">{model_name}</div>
                <div class="bot-status">Online</div>
            </div>
        </div>
        <div class="chat-body" id="chat-body">
            <div class="date-divider">{now_date}</div>
            {bubbles_html if bubbles_html else '<div style="text-align:center;color:#fff;font-size:13px;margin-top:30px;">대화를 시작해보세요 👋</div>'}
        </div>
    </div>
    <script>
        var el = document.getElementById('chat-body');
        if(el) el.scrollTop = el.scrollHeight;
    </script>
    """
    return html


# ── Page setup ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI 설정 관리", page_icon="⚙️", layout="wide")
st.markdown(MESSENGER_CSS, unsafe_allow_html=True)
st.title("⚙️ OpenAI API 설정 관리")

if "config" not in st.session_state:
    st.session_state.config = load_config()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = st.session_state.config["api_key"]

# ── Sidebar: settings ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 API 설정")

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.api_key_input,
        type="password",
        placeholder="sk-...",
        help="OpenAI 대시보드에서 발급받은 API 키를 입력하세요.",
    )

    st.divider()
    st.header("🤖 모델 설정")

    model = st.selectbox(
        "모델 선택",
        options=AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state.config["model"])
        if st.session_state.config["model"] in AVAILABLE_MODELS
        else 0,
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=float(st.session_state.config["temperature"]),
        step=0.05,
        help="높을수록 창의적, 낮을수록 일관된 응답",
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=64,
        max_value=4096,
        value=int(st.session_state.config["max_tokens"]),
        step=64,
        help="생성할 최대 토큰 수",
    )

    top_p = st.slider(
        "Top P",
        min_value=0.0,
        max_value=1.0,
        value=float(st.session_state.config["top_p"]),
        step=0.05,
        help="누클리어스 샘플링 확률",
    )

    system_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.config["system_prompt"],
        height=100,
        help="모델의 기본 역할을 정의합니다.",
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 저장", use_container_width=True):
            new_config = {
                "api_key": api_key,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "system_prompt": system_prompt,
            }
            st.session_state.config = new_config
            st.session_state.api_key_input = api_key
            save_config(new_config)
            st.success("저장 완료!")

    with col2:
        if st.button("🔗 연결 테스트", use_container_width=True):
            with st.spinner("테스트 중..."):
                ok, msg = test_connection(api_key, model)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

# ── Main area: two tabs ──────────────────────────────────────────────────────
tab_status, tab_chat = st.tabs(["📊 현재 설정", "💬 채팅 테스트"])

with tab_status:
    st.subheader("현재 적용된 설정")

    cfg = st.session_state.config
    masked_key = (
        cfg["api_key"][:7] + "..." + cfg["api_key"][-4:]
        if len(cfg["api_key"]) > 11
        else ("(미입력)" if not cfg["api_key"] else cfg["api_key"])
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("API Key", masked_key)
        st.metric("모델", cfg["model"])
        st.metric("Temperature", cfg["temperature"])
    with col_b:
        st.metric("Max Tokens", cfg["max_tokens"])
        st.metric("Top P", cfg["top_p"])

    st.markdown("**System Prompt**")
    st.info(cfg["system_prompt"])

    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if raw.get("api_key"):
            raw["api_key"] = masked_key
        st.markdown("**저장된 config.json**")
        st.json(raw)

with tab_chat:
    if not st.session_state.config["api_key"]:
        st.warning("사이드바에서 API 키를 입력하고 저장하세요.")
    elif not OPENAI_AVAILABLE:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
    else:
        current_model = st.session_state.config["model"]

        # 메신저 UI 렌더링
        st.markdown(
            render_messenger(st.session_state.chat_history, current_model),
            unsafe_allow_html=True,
        )

        # 초기화 버튼
        if st.session_state.chat_history:
            if st.button("🗑️ 대화 초기화", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

        # 메시지 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            now_str = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt, "time": now_str}
            )

            with st.spinner(""):
                try:
                    api_messages = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ]
                    reply = send_message(
                        st.session_state.config["api_key"],
                        st.session_state.config,
                        api_messages,
                    )
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": reply, "time": datetime.now().strftime("%H:%M")}
                    )
                except Exception as e:
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"오류가 발생했습니다: {e}", "time": datetime.now().strftime("%H:%M")}
                    )
            st.rerun()
