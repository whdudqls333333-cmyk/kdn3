import streamlit as st
import json
from datetime import date
from pathlib import Path

try:
    from streamlit_calendar import calendar as st_calendar
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False

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
.block-container { padding-top: 3rem !important; }

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

today_str = date.today().isoformat()  # "YYYY-MM-DD"

if "config" not in st.session_state:
    st.session_state.config = load_config()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key_input" not in st.session_state:
    st.session_state.api_key_input = st.session_state.config["api_key"]
if "schedule" not in st.session_state or isinstance(st.session_state.schedule, list):
    # dict keyed by "YYYY-MM-DD": [{"task": str, "detail": str, "done": bool}]
    st.session_state.schedule = {}
if "selected_date" not in st.session_state:
    st.session_state.selected_date = today_str

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

# ── 메인: 상단 헤더 ───────────────────────────────────────────────────────────
st.markdown("""
<div class="top-header">
    <div>
        <div class="main-title">KDN 업무 지원 AI</div>
        <div class="sub-title">업무 질문부터 문서 작성까지, AI가 함께합니다</div>
    </div>
    <div class="badge">OpenAI GPT</div>
</div>
""", unsafe_allow_html=True)

# ── 일정 상세 팝업 ────────────────────────────────────────────────────────────
@st.dialog("📋 일정 상세")
def show_detail(date_key: str, idx: int):
    item = st.session_state.schedule[date_key][idx]
    st.markdown(f"### {item['task']}")
    st.caption(date_key)
    st.divider()
    st.markdown(item["detail"] if item["detail"] else "_세부 내용이 없습니다._")
    st.divider()
    done_label = "✅ 완료 취소" if item["done"] else "☑️ 완료 처리"
    if st.button(done_label, use_container_width=True):
        st.session_state.schedule[date_key][idx]["done"] = not item["done"]
        st.rerun()

# ── 달력 + 일정 패널 (좌: 달력 / 우: 일정) ───────────────────────────────────
col_cal, col_schedule = st.columns([3, 1])

with col_cal:
    # 일정 데이터를 FullCalendar 이벤트 형식으로 변환
    calendar_events = []
    for d, items in st.session_state.schedule.items():
        for item in items:
            color = "#4CAF50" if item["done"] else "#E53935"
            calendar_events.append({
                "title": "",
                "start": d,
                "backgroundColor": color,
                "borderColor": color,
                "display": "list-item",
            })

    calendar_options = {
        "initialView": "dayGridMonth",
        "locale": "ko",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "",
        },
        "height": 480,
        "selectable": True,
        "dateClick": True,
    }

    custom_css = """
    .fc-day-today { background-color: rgba(25, 118, 210, 0.08) !important; }
    .fc-toolbar-title { font-size: 15px !important; font-weight: 700; }
    .fc-button { font-size: 11px !important; padding: 2px 7px !important; }
    .fc-col-header-cell { font-size: 12px !important; }
    .fc-daygrid-day-number { font-size: 12px !important; }
    .fc-daygrid-event-dot {
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        border-width: 4px !important;
        margin: 0 auto !important;
    }
    .fc-daygrid-event.fc-daygrid-dot-event {
        justify-content: center !important;
        padding: 1px 0 !important;
    }
    .fc-daygrid-event.fc-daygrid-dot-event .fc-event-title {
        display: none !important;
    }
    """

    if CALENDAR_AVAILABLE:
        cal_result = st_calendar(
            events=calendar_events,
            options=calendar_options,
            custom_css=custom_css,
            key="main_calendar",
        )
        if cal_result and cal_result.get("dateClick"):
            clicked = cal_result["dateClick"].get("date", "")[:10]
            if clicked:
                st.session_state.selected_date = clicked
                st.rerun()
    else:
        st.info("달력을 표시하려면 `pip install streamlit-calendar`를 실행하세요.")

# ── 우측: 선택된 날짜의 일정 ───────────────────────────────────────────────────
with col_schedule:
    sel = st.session_state.selected_date
    try:
        sel_date = date.fromisoformat(sel)
        display_date = sel_date.strftime("%Y년 %m월 %d일")
    except Exception:
        display_date = sel

    is_today = (sel == today_str)
    date_label = f"{'📅 오늘' if is_today else '📅'} {display_date}"

    with st.container(border=True):
        st.markdown(f"#### {date_label}")
        if not is_today:
            if st.button("오늘로 이동", use_container_width=True):
                st.session_state.selected_date = today_str
                st.rerun()

        # 일정 추가 폼
        with st.form("add_schedule", clear_on_submit=True):
            new_task = st.text_input("타이틀", placeholder="일정 제목을 입력하세요")
            new_detail = st.text_area("세부내용", placeholder="세부 내용을 입력하세요 (선택)", height=80)
            if st.form_submit_button("+ 추가", use_container_width=True):
                if new_task.strip():
                    if sel not in st.session_state.schedule:
                        st.session_state.schedule[sel] = []
                    st.session_state.schedule[sel].append({
                        "task": new_task.strip(),
                        "detail": new_detail.strip(),
                        "done": False,
                    })
                    st.rerun()

        st.divider()

        # 일정 목록
        items = st.session_state.schedule.get(sel, [])
        if not items:
            st.caption("등록된 일정이 없습니다.")
        else:
            done_count = sum(1 for s in items if s["done"])
            total = len(items)
            st.progress(done_count / total, text=f"{done_count}/{total} 완료")

            to_delete = []
            with st.container(height=240):
                for i, item in enumerate(items):
                    c_chk, c_title, c_del = st.columns([1, 5, 1])
                    with c_chk:
                        checked = st.checkbox("", value=item["done"], key=f"sched_{sel}_{i}",
                                             label_visibility="collapsed")
                        if checked != item["done"]:
                            st.session_state.schedule[sel][i]["done"] = checked
                            st.rerun()
                    with c_title:
                        label = f"~~{item['task']}~~" if item["done"] else item["task"]
                        if st.button(label, key=f"detail_{sel}_{i}", use_container_width=True,
                                     type="tertiary"):
                            show_detail(sel, i)
                    with c_del:
                        if st.button("✕", key=f"del_{sel}_{i}", help="삭제"):
                            to_delete.append(i)

            if to_delete:
                st.session_state.schedule[sel] = [
                    s for j, s in enumerate(items) if j not in to_delete
                ]
                if not st.session_state.schedule[sel]:
                    del st.session_state.schedule[sel]
                st.rerun()

            if done_count == total:
                st.success("모든 일정 완료! 🎉")

            if st.button("완료 항목 삭제", use_container_width=True):
                st.session_state.schedule[sel] = [
                    s for s in items if not s["done"]
                ]
                if not st.session_state.schedule[sel]:
                    del st.session_state.schedule[sel]
                st.rerun()

st.divider()

# ── 챗봇 (달력 아래 전체 너비) ────────────────────────────────────────────────
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
