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


def build_messenger_html(messages: list, model_name: str) -> str:
    date_str = datetime.now().strftime("%Y년 %m월 %d일")

    rows = ""
    for msg in messages:
        ts = msg.get("time", "")
        content = (
            msg["content"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        if msg["role"] == "user":
            rows += f"""
            <div class="msg-row user">
                <div class="ts">{ts}</div>
                <div class="bubble user">{content}</div>
            </div>"""
        else:
            rows += f"""
            <div class="msg-row bot">
                <div class="avatar">🤖</div>
                <div class="bubble-col">
                    <div class="sender">{model_name}</div>
                    <div class="bubble bot">{content}</div>
                </div>
                <div class="ts">{ts}</div>
            </div>"""

    body = rows if rows else '<p class="empty">대화를 시작해보세요 👋</p>'

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
    height: 100%;
    font-family: 'Apple SD Gothic Neo', 'Noto Sans KR', Arial, sans-serif;
    font-size: 14px;
    background: #b2c7d9;
}}
.wrap {{
    display: flex;
    flex-direction: column;
    height: 100vh;
}}

/* ── 헤더 ── */
.header {{
    background: #3c1e1e;
    color: #fff;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}}
.h-icon {{
    width: 38px; height: 38px;
    background: #fee500;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}}
.h-name {{ font-weight: 700; font-size: 15px; }}
.h-status {{ font-size: 11px; color: #aaa; margin-top: 1px; }}

/* ── 메시지 영역 ── */
.body {{
    flex: 1;
    overflow-y: auto;
    padding: 14px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: #b2c7d9;
}}
.date-chip {{
    font-size: 11px;
    color: #fff;
    background: rgba(0,0,0,.22);
    border-radius: 10px;
    padding: 3px 12px;
    text-align: center;
    width: fit-content;
    margin: 2px auto 6px;
}}
.empty {{
    text-align: center;
    color: rgba(255,255,255,.8);
    font-size: 13px;
    margin-top: 60px;
}}

/* ── 메시지 행 ── */
.msg-row {{
    display: flex;
    align-items: flex-end;
    gap: 6px;
}}
.msg-row.user {{ justify-content: flex-end; }}
.msg-row.bot  {{ justify-content: flex-start; }}

.avatar {{
    width: 36px; height: 36px;
    background: #fee500;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    align-self: flex-start;
}}
.bubble-col {{
    display: flex;
    flex-direction: column;
    gap: 2px;
    max-width: 68%;
}}
.sender {{
    font-size: 11px;
    color: #333;
    padding-left: 4px;
    margin-bottom: 2px;
}}
.bubble {{
    padding: 9px 13px;
    font-size: 13.5px;
    line-height: 1.55;
    word-break: break-word;
    white-space: pre-wrap;
    max-width: 68vw;
}}
.bubble.user {{
    background: #fee500;
    color: #111;
    border-radius: 18px 18px 4px 18px;
}}
.bubble.bot {{
    background: #fff;
    color: #111;
    border-radius: 4px 18px 18px 18px;
}}
.ts {{
    font-size: 10px;
    color: rgba(0,0,0,.38);
    flex-shrink: 0;
    margin-bottom: 3px;
}}

/* ── 입력창 ── */
.footer {{
    background: #f0f0f0;
    border-top: 1px solid #ddd;
    padding: 8px 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}}
.plus-btn {{
    width: 32px; height: 32px;
    border: 1.5px solid #aaa;
    border-radius: 50%;
    background: none;
    color: #888;
    font-size: 20px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    line-height: 1;
}}
.msg-input {{
    flex: 1;
    border: 1.5px solid #ddd;
    border-radius: 22px;
    padding: 9px 16px;
    font-size: 13.5px;
    font-family: inherit;
    outline: none;
    background: #fff;
    resize: none;
    min-height: 38px;
    max-height: 90px;
    line-height: 1.4;
    overflow-y: auto;
    transition: border-color .15s;
}}
.msg-input:focus {{ border-color: #aaa; }}
.send-btn {{
    width: 38px; height: 38px;
    background: #fee500;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    font-size: 18px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    transition: background .1s;
}}
.send-btn:hover {{ background: #f0d800; }}
.send-btn:active {{ background: #e0c800; transform: scale(.94); }}
</style>
</head>
<body>
<div class="wrap">

  <!-- 헤더 -->
  <div class="header">
    <div class="h-icon">🤖</div>
    <div>
      <div class="h-name">{model_name}</div>
      <div class="h-status">Online</div>
    </div>
  </div>

  <!-- 메시지 -->
  <div class="body" id="chatBody">
    <div class="date-chip">{date_str}</div>
    {body}
  </div>

  <!-- 입력창 -->
  <div class="footer">
    <button class="plus-btn" type="button" onclick="return false">+</button>
    <textarea id="msgInput" class="msg-input"
              placeholder="메시지를 입력하세요..." rows="1"></textarea>
    <button id="sendBtn" class="send-btn" type="button">&#10148;</button>
  </div>

</div>
<script>
(function () {{
  /* 자동 스크롤 */
  var chatBody = document.getElementById('chatBody');
  if (chatBody) chatBody.scrollTop = chatBody.scrollHeight;

  /* textarea 자동 높이 */
  var msgInput = document.getElementById('msgInput');
  msgInput.addEventListener('input', function () {{
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 90) + 'px';
  }});

  /* Streamlit form 브리지 — st.form(hidden) 을 타겟 */
  function triggerStreamlit(text) {{
    try {{
      var pd = window.parent.document;
      /* 숨겨진 st.form 안의 input 탐색 */
      var formWrap = pd.querySelector('[data-testid="stForm"]');
      if (!formWrap) {{ console.warn('[Bridge] stForm not found'); return false; }}

      var inp = formWrap.querySelector('input');
      if (!inp) {{ console.warn('[Bridge] input not found'); return false; }}

      /* React 내부 setter로 값 주입 */
      var setter = Object.getOwnPropertyDescriptor(
        window.parent.HTMLInputElement.prototype, 'value'
      ).set;
      setter.call(inp, text);
      inp.dispatchEvent(new window.parent.Event('input', {{ bubbles: true }}));
      inp.dispatchEvent(new window.parent.Event('change', {{ bubbles: true }}));

      /* 제출 버튼 클릭 */
      var btn = formWrap.querySelector('[data-testid="stFormSubmitButton"] button') ||
                formWrap.querySelector('button');
      if (btn) {{
        setTimeout(function () {{ btn.click(); }}, 100);
        return true;
      }}
    }} catch (e) {{
      console.warn('[Bridge] error:', e);
    }}
    return false;
  }}

  function send() {{
    var text = msgInput.value.trim();
    if (!text) return;
    var ok = triggerStreamlit(text);
    if (ok) {{
      msgInput.value = '';
      msgInput.style.height = 'auto';
      msgInput.focus();
    }}
  }}

  document.getElementById('sendBtn').addEventListener('click', send);
  msgInput.addEventListener('keydown', function (e) {{
    if (e.key === 'Enter' && !e.shiftKey) {{
      e.preventDefault();
      send();
    }}
  }});
}})();
</script>
</body>
</html>"""


# ── Page setup ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="OpenAI 설정 관리", page_icon="⚙️", layout="wide")
st.title("⚙️ OpenAI API 설정 관리")

# 브리지용 hidden form 을 완전히 숨김 (display:none 은 JS click 에도 동작함)
st.markdown("""
<style>
[data-testid="stForm"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

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

        # 메신저 UI (입력창 포함)
        components.html(
            build_messenger_html(st.session_state.chat_history, model_name),
            height=580,
            scrolling=False,
        )

        if st.session_state.chat_history:
            if st.button("🗑️ 대화 초기화"):
                st.session_state.chat_history = []
                st.rerun()

        # ── 숨겨진 브리지 form (iframe JS가 트리거, display:none이라 보이지 않음) ──
        with st.form("chat_bridge", clear_on_submit=True):
            bridge_text = st.text_input("_msg", label_visibility="hidden")
            bridge_submit = st.form_submit_button("전송")

        if bridge_submit and bridge_text:
            now = datetime.now().strftime("%H:%M")
            st.session_state.chat_history.append(
                {"role": "user", "content": bridge_text, "time": now}
            )
            try:
                api_msgs = [{"role": m["role"], "content": m["content"]}
                            for m in st.session_state.chat_history]
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
