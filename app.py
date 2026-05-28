import streamlit as st
import json
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
/* ── 상단 헤더 ── */
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
.top-header .main-title {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
}
.top-header .sub-title {
    font-size: 12px;
    color: rgba(255,255,255,0.55);
    margin-top: 3px;
}
.top-header .badge {
    background: #fee500;
    color: #111;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
}

/* ── 공유·배포·별표 버튼만 숨김 (사이드바 토글 유지) ── */
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
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { font-size: 12px !important; }
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

if "config" not in st.session_state:
    st.session_state.config = load_config()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = st.session_state.config["api_key"]
if "schedule" not in st.session_state:
    st.session_state.schedule = []  # [{"task": str, "done": bool}]

# ── Sidebar (탭: 설정 / 현재 상태) ──────────────────────────────────────────
with st.sidebar:
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

# ── 메인: 상단 헤더 + 챗봇 ───────────────────────────────────────────────────
st.markdown("""
<div class="top-header">
    <div>
        <div class="main-title">KDN 업무 지원 AI</div>
        <div class="sub-title">업무 질문부터 문서 작성까지, AI가 함께합니다</div>
    </div>
    <div class="badge">OpenAI GPT</div>
</div>
""", unsafe_allow_html=True)

col_chat, col_schedule = st.columns([3, 1])

# ── 좌측: 챗봇 ───────────────────────────────────────────────────────────────
with col_chat:
    if not st.session_state.config["api_key"]:
        st.warning("왼쪽 사이드바 **⚙️ 시스템 설정** 에서 API 키를 입력하고 저장하세요.")
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

# ── 우측: 오늘의 일정 ─────────────────────────────────────────────────────────
with col_schedule:
    from datetime import date
    today = date.today().strftime("%Y년 %m월 %d일")

    with st.container(border=True):
        st.markdown(f"#### 📅 오늘의 일정")
        st.caption(today)

        # 일정 추가
        with st.form("add_schedule", clear_on_submit=True):
            new_task = st.text_input("일정 입력", placeholder="일정을 입력하세요", label_visibility="collapsed")
            if st.form_submit_button("+ 추가", use_container_width=True):
                if new_task.strip():
                    st.session_state.schedule.append({"task": new_task.strip(), "done": False})
                    st.rerun()

        st.divider()

        # 일정 목록
        if not st.session_state.schedule:
            st.caption("등록된 일정이 없습니다.")
        else:
            done_count = sum(1 for s in st.session_state.schedule if s["done"])
            total = len(st.session_state.schedule)
            st.progress(done_count / total, text=f"{done_count}/{total} 완료")

            to_delete = []
            for i, item in enumerate(st.session_state.schedule):
                c1, c2 = st.columns([5, 1])
                with c1:
                    checked = st.checkbox(
                        item["task"] if not item["done"] else f"~~{item['task']}~~",
                        value=item["done"],
                        key=f"sched_{i}",
                    )
                    if checked != item["done"]:
                        st.session_state.schedule[i]["done"] = checked
                        st.rerun()
                with c2:
                    if st.button("✕", key=f"del_{i}", help="삭제"):
                        to_delete.append(i)

            if to_delete:
                st.session_state.schedule = [
                    s for j, s in enumerate(st.session_state.schedule)
                    if j not in to_delete
                ]
                st.rerun()

            if done_count == total:
                st.success("모든 일정을 완료했습니다! 🎉")

            if st.button("완료 항목 삭제", use_container_width=True):
                st.session_state.schedule = [s for s in st.session_state.schedule if not s["done"]]
                st.rerun()
