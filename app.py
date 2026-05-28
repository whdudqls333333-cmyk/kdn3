import streamlit as st
import streamlit.components.v1 as components
import json
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

CHAT_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: #b2c7d9;
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', Arial, sans-serif;
    font-size: 14px;
}

.chat-wrapper {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 480px;
    margin: 0 auto;
    background: #b2c7d9;
}

/* 헤더 */
.chat-header {
    background: #3c1e1e;
    color: white;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.bot-icon {
    width: 38px; height: 38px;
    background: #fee500;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}
.bot-info .bot-name { font-weight: 700; font-size: 15px; }
.bot-info .bot-status { font-size: 11px; color: #aaa; margin-top: 1px; }

/* 메시지 영역 */
.chat-body {
    flex: 1;
    overflow-y: auto;
    padding: 14px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

/* 날짜 구분선 */
.date-chip {
    text-align: center;
    font-size: 11px;
    color: #fff;
    background: rgba(0,0,0,0.22);
    border-radius: 10px;
    padding: 3px 12px;
    width: fit-content;
    margin: 2px auto 6px;
}

/* 메시지 행 */
.msg-row {
    display: flex;
    align-items: flex-end;
    gap: 6px;
}
.msg-row.user { justify-content: flex-end; }
.msg-row.bot  { justify-content: flex-start; }

/* 아바타 */
.avatar {
    width: 36px; height: 36px;
    background: #fee500;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    align-self: flex-start;
}

/* 말풍선 그룹 */
.bubble-col {
    display: flex;
    flex-direction: column;
    gap: 2px;
    max-width: 68%;
}
.bubble-col.user { align-items: flex-end; }
.bubble-col.bot  { align-items: flex-start; }

.sender-name {
    font-size: 11px;
    color: #333;
    padding-left: 4px;
    margin-bottom: 2px;
}

/* 말풍선 */
.bubble {
    padding: 9px 13px;
    font-size: 13.5px;
    line-height: 1.55;
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

/* 시간 */
.ts {
    font-size: 10px;
    color: rgba(0,0,0,0.4);
    flex-shrink: 0;
    margin-bottom: 3px;
}

/* 빈 화면 안내 */
.empty-notice {
    text-align: center;
    color: rgba(255,255,255,0.85);
    font-size: 13px;
    margin-top: 60px;
}
"""


def build_messenger_html(messages: list, model_name: str) -> str:
    date_str = datetime.now().strftime("%Y년 %m월 %d일")

    rows = ""
    for msg in messages:
        ts = msg.get("time", "")
        raw = msg["content"]
        content = (
            raw.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
               .replace("\n", "<br>")
        )

        if msg["role"] == "user":
            rows += f"""
            <div class="msg-row user">
                <div class="ts">{ts}</div>
                <div class="bubble-col user">
                    <div class="bubble user">{content}</div>
                </div>
            </div>"""
        else:
            rows += f"""
            <div class="msg-row bot">
                <div class="avatar">🤖</div>
                <div class="bubble-col bot">
                    <div class="sender-name">{model_name}</div>
                    <div class="bubble bot">{content}</div>
                </div>
                <div class="ts">{ts}</div>
            </div>"""

    body_content = rows if rows else '<div class="empty-notice">대화를 시작해보세요 👋</div>'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>{CHAT_CSS}</style>
</head>
<body>
<div class="chat-wrapper">
    <div class="chat-header">
        <div class="bot-icon">🤖</div>
        <div class="bot-info">
            <div class="bot-name">{model_name}</div>
            <div class="bot-status">Online</div>
        </div>
    </div>
    <div class="chat-body" id="chatBody">
        <div class="date-chip">{date_str}</div>
        {body_content}
    </div>
</div>
<script>
  var el = document.getElementById('chatBody');
  if (el) el.scrollTop = el.scrollHeight;
</script>
</body>
</html>"""


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
        return False, "openai 패키지가 설치되지 않았습니다."
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
        return True, f"연결 성공! 응답: {reply}"
    except Exception as e:
        return False, f"연결 실패: {e}"


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


# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI 설정 관리", page_icon="⚙️", layout="wide")
st.title("⚙️ OpenAI API 설정 관리")

if "config" not in st.session_state:
    st.session_state.config = load_config()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = st.session_state.config["api_key"]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 API 설정")
    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.api_key_input,
        type="password",
        placeholder="sk-...",
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
    temperature = st.slider("Temperature", 0.0, 2.0,
                            float(st.session_state.config["temperature"]), 0.05)
    max_tokens  = st.slider("Max Tokens", 64, 4096,
                            int(st.session_state.config["max_tokens"]), 64)
    top_p       = st.slider("Top P", 0.0, 1.0,
                            float(st.session_state.config["top_p"]), 0.05)
    system_prompt = st.text_area("System Prompt",
                                 value=st.session_state.config["system_prompt"],
                                 height=100)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 저장", use_container_width=True):
            new_cfg = {
                "api_key": api_key, "model": model,
                "temperature": temperature, "max_tokens": max_tokens,
                "top_p": top_p, "system_prompt": system_prompt,
            }
            st.session_state.config = new_cfg
            st.session_state.api_key_input = api_key
            save_config(new_cfg)
            st.success("저장 완료!")
    with col2:
        if st.button("🔗 연결 테스트", use_container_width=True):
            with st.spinner("테스트 중..."):
                ok, msg = test_connection(api_key, model)
            (st.success if ok else st.error)(msg)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_status, tab_chat = st.tabs(["📊 현재 설정", "💬 채팅 테스트"])

with tab_status:
    st.subheader("현재 적용된 설정")
    cfg = st.session_state.config
    key = cfg["api_key"]
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else ("(미입력)" if not key else key)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("API Key", masked)
        st.metric("모델", cfg["model"])
        st.metric("Temperature", cfg["temperature"])
    with c2:
        st.metric("Max Tokens", cfg["max_tokens"])
        st.metric("Top P", cfg["top_p"])

    st.markdown("**System Prompt**")
    st.info(cfg["system_prompt"])

    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if raw.get("api_key"):
            raw["api_key"] = masked
        st.markdown("**저장된 config.json**")
        st.json(raw)

with tab_chat:
    if not st.session_state.config["api_key"]:
        st.warning("사이드바에서 API 키를 입력하고 저장하세요.")
    elif not OPENAI_AVAILABLE:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
    else:
        model_name = st.session_state.config["model"]

        # 메신저 UI (iframe 렌더링)
        components.html(
            build_messenger_html(st.session_state.chat_history, model_name),
            height=540,
            scrolling=False,
        )

        # 대화 초기화
        if st.session_state.chat_history:
            if st.button("🗑️ 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()

        # 메시지 입력
        if prompt := st.chat_input("메시지를 입력하세요..."):
            now = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt, "time": now}
            )
            try:
                api_msgs = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history
                ]
                with st.spinner("답변 생성 중..."):
                    reply = send_message(
                        st.session_state.config["api_key"],
                        st.session_state.config,
                        api_msgs,
                    )
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": reply,
                     "time": datetime.now().strftime("%H:%M")}
                )
            except Exception as e:
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": f"오류: {e}",
                     "time": datetime.now().strftime("%H:%M")}
                )
            st.rerun()
