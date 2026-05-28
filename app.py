import streamlit as st
import json
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

CONFIG_FILE = "config.json"

AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]

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
        return False, "openai 패키지가 설치되지 않았습니다."
    if not api_key:
        return False, "API 키를 입력하세요."
    try:
        client = OpenAI(api_key=api_key)
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' in one word."}],
            max_tokens=5,
        )
        return True, f"연결 성공! 응답: {r.choices[0].message.content.strip()}"
    except Exception as e:
        return False, f"연결 실패: {e}"


def send_message(api_key: str, config: dict, messages: list) -> str:
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "system", "content": config["system_prompt"]}] + messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
    )
    return r.choices[0].message.content


# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI 챗봇", page_icon="🤖", layout="wide")

st.markdown("""
<style>
/* ── 상단 헤더 배너 ── */
.top-header {
    width: 100%;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    color: white;
    padding: 18px 32px;
    border-radius: 12px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.top-header .main-title { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
.top-header .sub-title  { font-size: 12px; color: rgba(255,255,255,0.55); margin-top: 3px; }
.top-header .badge {
    background: #fee500; color: #111;
    font-size: 11px; font-weight: 600;
    padding: 4px 10px; border-radius: 20px;
}

/* ── 대시보드 카드 ── */
.dash-card {
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.dash-card h4 { margin: 0 0 6px; font-size: 14px; color: #888; font-weight: 500; }
.dash-card .val { font-size: 26px; font-weight: 700; color: #1a1a2e; }

/* ── 사이드바 메뉴 버튼 ── */
[data-testid="stSidebar"] .menu-btn button {
    background: transparent !important;
    border: none !important;
    text-align: left !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    width: 100% !important;
    font-size: 13px !important;
    color: #333 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .menu-btn button:hover {
    background: #f0f0f0 !important;
}
.menu-active button {
    background: #1a1a2e !important;
    color: white !important;
}

/* ── Streamlit 기본 UI 요소 숨김 ── */
[data-testid="stDeployButton"]   { display: none !important; }
[data-testid="stStarButton"]     { display: none !important; }
[data-testid="stMainMenuButton"] { display: none !important; }
[data-testid="stDecoration"]     { display: none !important; }
#MainMenu { display: none !important; }
.block-container { padding-top: 1rem !important; }

/* ── 사이드바 폰트 축소 ── */
[data-testid="stSidebar"] { font-size: 12px !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { font-size: 12px !important; }
[data-testid="stSidebar"] h1 { font-size: 16px !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { font-size: 13px !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select { font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] { font-size: 14px !important; }
[data-testid="stSidebar"] [data-testid="stMetricLabel"] { font-size: 11px !important; }
[data-testid="stSidebar"] button { font-size: 12px !important; white-space: nowrap !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "config" not in st.session_state:
    st.session_state.config = load_config()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = st.session_state.config["api_key"]
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 메뉴")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 대시보드", use_container_width=True,
                     type="primary" if st.session_state.page == "dashboard" else "secondary"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col2:
        if st.button("💬 챗봇", use_container_width=True,
                     type="primary" if st.session_state.page == "chatbot" else "secondary"):
            st.session_state.page = "chatbot"
            st.rerun()

    st.divider()

    with st.expander("⚙️ 시스템 설정", expanded=False):
        tab_cfg, tab_status = st.tabs(["🔧 설정", "📊 현재 상태"])

    with tab_cfg:
        st.subheader("🔑 API 설정")
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key_input,
            type="password",
            placeholder="sk-...",
        )
        st.divider()
        st.subheader("🤖 모델 설정")
        model = st.selectbox(
            "모델 선택",
            options=AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.config["model"])
            if st.session_state.config["model"] in AVAILABLE_MODELS else 0,
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
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 저장", use_container_width=True):
                nc = {"api_key": api_key, "model": model, "temperature": temperature,
                      "max_tokens": max_tokens, "top_p": top_p, "system_prompt": system_prompt}
                st.session_state.config = nc
                st.session_state.api_key_input = api_key
                save_config(nc)
                st.success("저장 완료!")
        with c2:
            if st.button("🔗 테스트", use_container_width=True):
                with st.spinner("테스트 중..."):
                    ok, msg = test_connection(api_key, model)
                (st.success if ok else st.error)(msg)

    with tab_status:
        cfg = st.session_state.config
        key = cfg["api_key"]
        masked = key[:7] + "..." + key[-4:] if len(key) > 11 else ("(미입력)" if not key else key)
        st.subheader("현재 적용된 설정")
        st.metric("API Key", masked)
        st.metric("모델", cfg["model"])
        st.metric("Temperature", cfg["temperature"])
        st.metric("Max Tokens", cfg["max_tokens"])
        st.metric("Top P", cfg["top_p"])
        st.markdown("**System Prompt**")
        st.info(cfg["system_prompt"])
        if Path(CONFIG_FILE).exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if raw.get("api_key"):
                raw["api_key"] = masked
            st.markdown("**config.json**")
            st.json(raw)

# ── 상단 배너 (공통) ──────────────────────────────────────────────────────────
st.markdown("""
<div class="top-header">
    <div>
        <div class="main-title">서비스 타이틀</div>
        <div class="sub-title">부제목 또는 설명 문구를 입력하세요</div>
    </div>
    <div class="badge">OpenAI GPT</div>
</div>
""", unsafe_allow_html=True)

# ── 대시보드 페이지 ───────────────────────────────────────────────────────────
if st.session_state.page == "dashboard":
    cfg = st.session_state.config
    key = cfg["api_key"]
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else ("(미입력)" if not key else key)
    chat_count = len(st.session_state.chat_history)
    user_turns = sum(1 for m in st.session_state.chat_history if m["role"] == "user")

    # 요약 카드
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("사용 모델", cfg["model"])
    with c2:
        st.metric("API Key", masked)
    with c3:
        st.metric("총 메시지 수", chat_count)
    with c4:
        st.metric("내 질문 수", user_turns)

    st.divider()

    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("모델 파라미터")
        with st.container(border=True):
            st.markdown(f"**Temperature** : `{cfg['temperature']}`")
            st.markdown(f"**Max Tokens** : `{cfg['max_tokens']}`")
            st.markdown(f"**Top P** : `{cfg['top_p']}`")
            st.markdown(f"**System Prompt**")
            st.info(cfg["system_prompt"])

    with col_r:
        st.subheader("이용 안내")
        with st.container(border=True):
            st.markdown("""
**1. 시스템 설정**
왼쪽 사이드바 ▸ ⚙️ 시스템 설정을 열어 API Key와 모델을 설정하세요.

**2. 챗봇 사용**
사이드바 메뉴 ▸ 💬 챗봇을 클릭하면 대화를 시작할 수 있습니다.

**3. 연결 테스트**
설정 저장 후 🔗 테스트 버튼으로 API 연결 상태를 확인하세요.
""")

    if st.button("💬 챗봇 시작하기", type="primary"):
        st.session_state.page = "chatbot"
        st.rerun()

# ── 챗봇 페이지 ───────────────────────────────────────────────────────────────
elif st.session_state.page == "chatbot":
    if not st.session_state.config["api_key"]:
        st.warning("왼쪽 사이드바 **⚙️ 시스템 설정 > 🔧 설정** 탭에서 API 키를 입력하고 저장하세요.")
    elif not OPENAI_AVAILABLE:
        st.error("openai 패키지가 필요합니다: `pip install openai`")
    else:
        with st.container(border=True):
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            if not st.session_state.chat_history:
                st.caption("대화를 시작해보세요.")

        if st.session_state.chat_history:
            if st.button("🗑️ 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()

        if prompt := st.chat_input("메시지를 입력하세요..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("답변 생성 중..."):
                    try:
                        api_msgs = [{"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.chat_history]
                        reply = send_message(
                            st.session_state.config["api_key"],
                            st.session_state.config,
                            api_msgs,
                        )
                        st.write(reply)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": reply})
                    except Exception as e:
                        err = f"오류: {e}"
                        st.error(err)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": err})
