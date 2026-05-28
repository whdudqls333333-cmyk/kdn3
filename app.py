import streamlit as st
import json
import os
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


# ── Page setup ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI 설정 관리", page_icon="⚙️", layout="wide")
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
    st.subheader("💬 채팅 테스트")

    if not st.session_state.config["api_key"]:
        st.warning("사이드바에서 API 키를 입력하고 저장하세요.")
    elif not OPENAI_AVAILABLE:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("메시지를 입력하세요..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("응답 생성 중..."):
                    try:
                        reply = send_message(
                            st.session_state.config["api_key"],
                            st.session_state.config,
                            st.session_state.chat_history,
                        )
                        st.write(reply)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": reply}
                        )
                    except Exception as e:
                        st.error(f"오류: {e}")

        if st.session_state.chat_history:
            if st.button("🗑️ 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()
