# app.py — Corrección de Writings EOI
# Light theme, minimalista. Selector de nivel B1-C2. Análisis estilo Cambridge.
# TODO(security): Considerar OAuth2 para uso multi-profesor en producción.
# TODO(security): Implementar rate limiting por sesión.

import hmac
import html as html_module
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from api_client import evaluate_exam, get_balance, validate_image_bytes
from rubric import (
    CEFR_LEVELS,
    RUBRIC_BANDS,
    SCORING_FORMULA,
    calculate_final_score,
    get_grade_label,
)

# ── Security: password ─────────────────────────────────────────────────────────
_APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
MAX_LOGIN_ATTEMPTS = 5

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_FILES = 6
LEVELS = ["B1", "B2", "C1", "C2"]

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Corrección de Writings — EOI",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": "Corrección de Writings — EOI Castilla y León"},
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
# CSS Block 1: Fonts, layout, login, sidebar
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
.login-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 20px; padding: 2.75rem 2.25rem 2.25rem; max-width: 400px; width: 100%; box-shadow: 0 8px 40px rgba(0,0,0,0.06); text-align: center; margin: 0 auto; }
.login-logo { font-size: 2.8rem; margin-bottom: 0.4rem; display: block; }
.login-title { font-size: 1.45rem; font-weight: 800; color: #1e293b; margin: 0 0 0.2rem; }
.login-sub { font-size: 0.78rem; color: #94a3b8; margin: 0 0 1.8rem; }
section[data-testid="stSidebar"] { background: #f8fafc !important; border-right: 1px solid #e2e8f0; }
.sidebar-title { font-size: 1rem; font-weight: 800; color: #1e293b; margin: 0 0 0.15rem; }
.sidebar-sub { font-size: 0.7rem; color: #94a3b8; }
.level-badge { display: inline-flex; align-items: center; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 99px; letter-spacing: 0.05em; color: white; }
.credits-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.75rem 1rem; margin: 0.5rem 0; font-size: 0.8rem; }
.credits-label { color: #64748b; font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
.credits-value { color: #1e293b; font-size: 1.05rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# CSS Block 2: Scores, cards, tabs, content boxes
st.markdown("""
<style>
.page-title { font-size: 1.55rem; font-weight: 800; color: #1e293b; margin: 0 0 0.2rem; }
.page-sub { font-size: 0.82rem; color: #64748b; margin: 0; }
.score-hero { border-radius: 16px; padding: 1.75rem 2rem; color: white; display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; box-shadow: 0 4px 24px rgba(0,0,0,0.15); }
.score-number { font-size: 3.8rem; font-weight: 900; line-height: 1; }
.score-denom { font-size: 1.5rem; font-weight: 400; opacity: 0.65; }
.score-meta { font-size: 0.8rem; opacity: 0.75; margin-top: 0.3rem; }
.score-grade { background: rgba(255,255,255,0.2); border-radius: 99px; padding: 0.5rem 1.2rem; font-size: 1rem; font-weight: 700; }
.crit-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 0.85rem; text-align: center; }
.crit-emoji { font-size: 1.5rem; display: block; margin-bottom: 0.25rem; }
.crit-name { font-size: 0.62rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.35rem; }
.crit-score { font-size: 1.7rem; font-weight: 900; color: #1e293b; line-height: 1; }
.crit-max { font-size: 0.68rem; color: #94a3b8; }
.bar-bg { background: #f1f5f9; border-radius: 99px; height: 5px; margin: 0.3rem 0 0.5rem; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 99px; }
.stTabs [data-baseweb="tab-list"] { background: #f8fafc; border-radius: 10px; padding: 4px; gap: 2px; border: 1px solid #e2e8f0; }
.stTabs [data-baseweb="tab"] { border-radius: 7px !important; font-size: 0.78rem !important; font-weight: 500 !important; color: #64748b !important; padding: 0.4rem 0.9rem !important; }
.stTabs [aria-selected="true"] { background: #fff !important; color: #1e293b !important; font-weight: 700 !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# CSS Block 3: Content boxes, logs, alerts, buttons
st.markdown("""
<style>
.transcript-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1.25rem 1.5rem; font-family: 'Courier New', monospace; font-size: 0.84rem; line-height: 1.9; color: #334155; white-space: pre-wrap; word-break: break-word; }
.examiner-box { background: #fafafa; border: 1px solid #e2e8f0; border-left: 4px solid #2563eb; border-radius: 0 10px 10px 0; padding: 1.5rem; font-size: 0.88rem; line-height: 1.85; color: #1e293b; }
.feedback-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 1.25rem 1.5rem; font-size: 0.9rem; line-height: 1.75; color: #1e293b; }
.rubric-row { display: grid; grid-template-columns: 140px 1fr; gap: 1.25rem; padding: 1rem 0; border-bottom: 1px solid #f1f5f9; align-items: start; }
.rubric-row:last-child { border-bottom: none; }
.rubric-score-center { text-align: center; }
.rubric-desc { font-size: 0.82rem; color: #475569; line-height: 1.65; }
.rubric-justif { display: block; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; font-size: 0.78rem; padding: 0.5rem 0.85rem; border-radius: 7px; margin-top: 0.6rem; font-style: italic; line-height: 1.6; }
.log-ok { background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; border-radius: 0 8px 8px 0; padding: 0.85rem 1rem; font-size: 0.82rem; }
.log-warn { background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; padding: 0.85rem 1rem; font-size: 0.82rem; margin-bottom: 0.5rem; }
.log-crit { background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; padding: 0.85rem 1rem; font-size: 0.82rem; margin-bottom: 0.5rem; }
.log-type { font-weight: 700; font-size: 0.7rem; letter-spacing: 0.05em; text-transform: uppercase; }
.log-loc { color: #94a3b8; font-size: 0.72rem; margin-top: 3px; }
.info-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 0.7rem 1rem; font-size: 0.82rem; color: #1e40af; margin-bottom: 0.75rem; }
.warn-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 0.7rem 1rem; font-size: 0.82rem; color: #92400e; margin-bottom: 0.75rem; }
.error-box { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 0.7rem 1rem; font-size: 0.82rem; color: #991b1b; margin-bottom: 0.75rem; }
.stButton > button[kind="primary"] { background: #2563eb !important; border: none !important; color: white !important; font-weight: 700 !important; font-size: 0.95rem !important; padding: 0.65rem 1.5rem !important; border-radius: 9px !important; transition: background 0.2s, transform 0.1s !important; width: 100%; }
.stButton > button[kind="primary"]:hover { background: #1d4ed8 !important; transform: translateY(-1px) !important; }
.stButton > button:disabled { opacity: 0.4 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("authenticated", False), ("result", None), ("last_error", None), ("level", "B2"), ("login_attempts", 0),
             ("session_cost", 0.0), ("session_count", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def render_login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div style="padding: 3rem 0 1rem;">
          <div class="login-card">
            <span class="login-logo">✍️</span>
            <h1 class="login-title">Corrección de Writings</h1>
            <p class="login-sub">Escuelas Oficiales de Idiomas · Castilla y León</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            pwd = st.text_input("Contraseña", type="password", placeholder="Contraseña de acceso...", label_visibility="collapsed")
            submitted = st.form_submit_button("Acceder →", use_container_width=True, type="primary")
        if submitted:
            if len(_APP_PASSWORD) < 8:
                st.markdown('<div class="error-box">⛔ APP_PASSWORD no está configurada (mínimo 8 caracteres). Revisa el .env.</div>', unsafe_allow_html=True)
            elif st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                st.markdown('<div class="error-box">⛔ Demasiados intentos. Recarga la página.</div>', unsafe_allow_html=True)
            elif hmac.compare_digest(pwd.encode(), _APP_PASSWORD.encode()):
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.markdown('<div class="error-box">⛔ Contraseña incorrecta.</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;font-size:0.68rem;color:#cbd5e1;margin-top:1rem;'>PYCE B1 · B2 · C1 · C2</p>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        level = st.session_state.get("level", "B2")
        lvl_color = CEFR_LEVELS[level]["color"]

        st.markdown(f"""
        <div style="padding-bottom:1rem;border-bottom:1px solid #e2e8f0;margin-bottom:1rem;">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">
            <span style="font-size:1.2rem;">✍️</span>
            <span class="sidebar-title">Corrección de Writings</span>
          </div>
          <span class="level-badge" style="background:{lvl_color};">{CEFR_LEVELS[level]['label']}</span>
        </div>
        """, unsafe_allow_html=True)

        # Level selector
        st.markdown("**Nivel del examen**")
        selected_level = st.selectbox(
            "Nivel del examen",
            options=LEVELS,
            index=LEVELS.index(st.session_state.level),
            format_func=lambda x: f"{x} — {CEFR_LEVELS[x]['label'].split('—')[1].strip()}",
            label_visibility="collapsed",
            key="level_select",
        )
        if selected_level != st.session_state.level:
            st.session_state.level = selected_level
            st.session_state.result = None
            st.rerun()

        # Level descriptor preview
        with st.expander(f"📋 Qué se espera en {level}", expanded=False):
            lvl = CEFR_LEVELS[level]
            st.markdown(f"""
**Eficacia Comunicativa**
{lvl['comunicativa'][:180]}...

**Corrección**
{lvl['correccion'][:150]}...
""")

        st.divider()

        # Credits
        st.markdown("**💳 Créditos OpenRouter**")
        balance = get_balance()
        if balance:
            used = balance.get("usage") or 0
            limit = balance.get("limit")
            remaining = balance.get("limit_remaining")
            if limit and remaining is not None:
                pct = max(0, min(100, (remaining / limit) * 100))
                color = "#16a34a" if pct > 30 else "#d97706" if pct > 10 else "#dc2626"
                st.markdown(f"""
                <div class="credits-card">
                  <div class="credits-label">Disponible</div>
                  <div class="credits-value" style="color:{color}">${remaining:.4f}</div>
                  <div style="font-size:0.68rem;color:#94a3b8;">de ${limit:.4f} · Usado: ${used:.4f}</div>
                  <div class="bar-bg" style="margin-top:6px;"><div class="bar-fill" style="width:{pct:.0f}%;background:{color};"></div></div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="credits-card">
                  <div class="credits-label">Consumido</div>
                  <div class="credits-value">${used:.4f}</div>
                  <div style="font-size:0.68rem;color:#94a3b8;">Sin límite definido</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="credits-card"><div class="credits-label">Estado</div><div style="color:#d97706;font-size:0.82rem;font-weight:600;">No disponible</div></div>', unsafe_allow_html=True)

        if st.session_state.result:
            usage = st.session_state.result.get("_usage", {})
            if usage.get("total_tokens"):
                st.markdown(f"""
                <div class="credits-card" style="margin-top:0.4rem;">
                  <div class="credits-label">Última corrección</div>
                  <div style="font-size:0.95rem;font-weight:800;color:#1e293b;">${usage['estimated_cost_usd']:.4f}</div>
                  <div style="font-size:0.68rem;color:#94a3b8;">{usage['total_tokens']:,} tokens · {html_module.escape(usage.get('model', ''))}</div>
                </div>""", unsafe_allow_html=True)
        if st.session_state.session_count:
            st.markdown(f"""
            <div class="credits-card" style="margin-top:0.4rem;">
              <div class="credits-label">Esta sesión</div>
              <div style="font-size:0.8rem;font-weight:700;color:#1e293b;">{st.session_state.session_count} corrección(es) · ${st.session_state.session_cost:.4f}</div>
            </div>""", unsafe_allow_html=True)

        st.divider()
        if st.button("🔒 Cerrar sesión", use_container_width=True):
            for k in ["authenticated", "result", "last_error"]:
                st.session_state[k] = False if k == "authenticated" else None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def score_bar(score: int, max_s: int = 3) -> str:
    pct = int((score / max_s) * 100)
    c = "#16a34a" if score == 3 else "#2563eb" if score == 2 else "#d97706" if score == 1 else "#dc2626"
    return f'<div class="bar-bg"><div class="bar-fill" style="width:{pct}%;background:{c};"></div></div>'


BAND_LABELS = {3: "Excelente / Supera el nivel", 2: "Estándar del nivel", 1: "Por debajo del nivel", 0: "Muy deficiente"}


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
def render_results(result: dict, level: str):
    scores = result.get("scores", {})
    final = calculate_final_score(scores)
    grade_label, _ = get_grade_label(final)
    text_type_label = result.get("text_type_label", "Texto")
    word_count = result.get("word_count_estimate", "—")
    vision_log = result.get("vision_log", [])
    lvl_color = CEFR_LEVELS[level]["color"]
    usage = result.get("_usage", {})
    cost = usage.get("estimated_cost_usd") or 0.0
    model_used = usage.get("model", "")

    # ── Score Hero ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="score-hero" style="background:linear-gradient(135deg,{lvl_color}dd,{lvl_color});">
      <div>
        <div style="font-size:0.78rem;opacity:0.8;margin-bottom:0.4rem;">
          Nivel {level} · {text_type_label} · {word_count} palabras
        </div>
        <div>
          <span class="score-number">{final}</span>
          <span class="score-denom"> / 10</span>
        </div>
        <div class="score-meta">Nota Final PYCE — Rúbrica {level}</div>
        <div style="font-size:0.72rem;opacity:0.85;margin-top:0.4rem;">💰 Coste de esta corrección: <strong>${cost:.4f}</strong> · {html_module.escape(model_used)}</div>
      </div>
      <div style="text-align:right;">
        <div class="score-grade">{grade_label}</div>
        {'<div style="font-size:0.7rem;opacity:0.7;margin-top:0.5rem;">⚠️ Ver Log del Sistema</div>' if vision_log else ''}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Criterion cards ───────────────────────────────────────────────────────
    cols = st.columns(4)
    for i, key in enumerate(["comunicativa", "coherencia", "correccion", "alcance"]):
        info = RUBRIC_BANDS[key]
        sv = scores.get(key, {}).get("score", 0)
        with cols[i]:
            st.markdown(f"""
            <div class="crit-card">
              <span class="crit-emoji">{info['emoji']}</span>
              <div class="crit-name">{info['name']}</div>
              {score_bar(sv)}
              <div><span class="crit-score">{sv}</span><span class="crit-max"> / 3</span></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    log_icon = "⚠️" if vision_log else "✅"
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Transcripción",
        "🔬 Análisis del Examinador",
        "📊 Criterios y Rúbrica",
        "💬 Feedback al Alumno",
        f"🔍 Log del Sistema {log_icon}",
    ])

    # Tab 1 — Transcripción
    with tab1:
        transcription = result.get("transcription", "")
        st.markdown("**Transcripción literal** — errores del alumno conservados exactamente")
        if any(m in transcription for m in ["[¿", "[ILEGIBLE]", "[TACHÓN"]):
            st.markdown('<div class="warn-box">⚠️ Contiene marcadores de ilegibilidad. Consulta el Log del Sistema.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="transcript-box">{html_module.escape(transcription)}</div>', unsafe_allow_html=True)

    # Tab 2 — Análisis del Examinador (Cambridge-style)
    with tab2:
        commentary = result.get("examiner_commentary", "")
        st.markdown(f"**Análisis del Examinador** — Nivel {level} · Estilo Cambridge")
        st.markdown('<div class="info-box">📋 Este análisis es para uso de la profesora. Cita frases literales del texto del alumno y evalúa cada dimensión con profundidad.</div>', unsafe_allow_html=True)
        # Render as paragraphs with preserved formatting
        if commentary:
            paragraphs = commentary.split("\n")
            formatted = ""
            for p in paragraphs:
                p = p.strip()
                if not p:
                    continue
                safe_p = html_module.escape(p)
                # Bold numbered sections if present
                if p[:1].isdigit() and "." in p[:3]:
                    safe_p = f"<strong>{safe_p}</strong>"
                formatted += f"<p style='margin:0 0 0.75rem;'>{safe_p}</p>"
            st.markdown(f'<div class="examiner-box">{formatted}</div>', unsafe_allow_html=True)
        else:
            st.info("No se generó comentario de examinador.")

    # Tab 3 — Evaluación por criterios
    with tab3:
        st.markdown(f"**Rúbrica PYCE** — Detalle por criterio (calibrada a nivel {level})")
        for key in ["comunicativa", "coherencia", "correccion", "alcance"]:
            info = RUBRIC_BANDS[key]
            sd = scores.get(key, {})
            sv = sd.get("score", 0)
            justif = sd.get("justification", "")
            descriptor = info["bands"][sv]
            band_label = BAND_LABELS[sv]

            st.markdown(f"""
            <div class="rubric-row">
              <div class="rubric-score-center">
                <div style="font-size:1.6rem;">{info['emoji']}</div>
                <div style="font-size:0.6rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;margin:4px 0;">{info['name']}</div>
                {score_bar(sv)}
                <div style="font-size:1.5rem;font-weight:900;color:#1e293b;">{sv}<span style="font-size:0.72rem;color:#94a3b8;font-weight:400;"> / 3</span></div>
                <div style="font-size:0.62rem;color:#64748b;margin-top:2px;">{band_label}</div>
              </div>
              <div class="rubric-desc">
                <div style="font-size:0.7rem;font-weight:700;color:{CEFR_LEVELS[level]['color']};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.4rem;">
                  Banda {sv} — {band_label}
                </div>
                <div>{html_module.escape(descriptor)}</div>
                <div class="rubric-justif">🤖 {html_module.escape(justif)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 4 — Feedback para el alumno
    with tab4:
        feedback = result.get("student_feedback", "")
        st.markdown("**Feedback para el alumno** — listo para copiar y enviar")
        st.markdown(f'<div class="feedback-box">💬 {html_module.escape(feedback)}</div>', unsafe_allow_html=True)
        st.code(feedback, language=None)

    # Tab 5 — Log del Sistema de Visión
    with tab5:
        st.markdown("**Log del Sistema de Visión** — anomalías detectadas en la lectura")
        if not vision_log:
            st.markdown('<div class="log-ok"><span class="log-type" style="color:#16a34a;">✅ Sin incidencias</span><br>El sistema procesó el texto sin detectar anomalías. Transcripción considerada completa y fiable.</div>', unsafe_allow_html=True)
        else:
            critical_types = {"ILEGIBLE", "CORTE"}
            st.markdown(f'<div class="warn-box">⚠️ <strong>{len(vision_log)}</strong> incidencia(s) detectadas. Revisa manualmente las zonas indicadas antes de confirmar la nota.</div>', unsafe_allow_html=True)
            for e in vision_log:
                t = e.get("type", "ANOMALIA")
                desc = html_module.escape(e.get("description", ""))
                loc = html_module.escape(e.get("location", "Ubicación no especificada"))
                is_crit = t in critical_types
                icon = "🔴" if is_crit else "🟡"
                css = "log-crit" if is_crit else "log-warn"
                color = "#dc2626" if is_crit else "#d97706"
                st.markdown(f"""
                <div class="{css}">
                  <div style="display:flex;gap:0.6rem;align-items:flex-start;">
                    <span style="font-size:1.2rem;">{icon}</span>
                    <div>
                      <div class="log-type" style="color:{color};">{t}</div>
                      <div style="color:#475569;">{desc}</div>
                      <div class="log-loc">📍 {loc}</div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def render_main():
    render_sidebar()
    level = st.session_state.get("level", "B2")
    lvl_color = CEFR_LEVELS[level]["color"]

    st.markdown(f"""
    <div style="margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #f1f5f9;">
      <h1 class="page-title">✍️ Corrección de Writings</h1>
      <p class="page-sub">Nivel seleccionado: <strong style="color:{lvl_color};">{CEFR_LEVELS[level]['label']}</strong> · Sube la foto o escaneo del examen</p>
    </div>
    """, unsafe_allow_html=True)

    # File uploader
    uploaded_files = st.file_uploader(
        "Arrastra las imágenes del examen aquí",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help=f"Hasta {MAX_FILES} páginas · Máximo 10 MB · JPG o PNG",
        label_visibility="collapsed",
    )

    valid_images = []
    errors = []

    if uploaded_files:
        if len(uploaded_files) > MAX_FILES:
            errors.append(f"Máximo {MAX_FILES} imágenes. Has subido {len(uploaded_files)}.")
        else:
            cols = st.columns(min(len(uploaded_files), 4))
            for i, f in enumerate(uploaded_files):
                data = f.read()
                f.seek(0)
                ok, mime, err = validate_image_bytes(data, f.name)
                if not ok:
                    errors.append(f"❌ {err}")
                    continue
                if len(data) > MAX_FILE_SIZE_BYTES:
                    errors.append(f"❌ '{f.name}' supera 10 MB.")
                    continue
                valid_images.append({"data": data, "mime_type": mime, "filename": f.name})
                with cols[i % 4]:
                    st.image(f, use_container_width=True, caption=f"Pág. {i+1}")

    for err in errors:
        st.markdown(f'<div class="error-box">{err}</div>', unsafe_allow_html=True)

    st.markdown("")
    can_go = len(valid_images) > 0 and not errors
    task_prompt = st.text_area(
        "Enunciado de la tarea (opcional, recomendado)",
        placeholder="Pega aquí el enunciado: tipo de texto, puntos que hay que tratar y número de palabras. Ej.: Write an email to your friend (180-200 words) telling them about...",
        height=110,
        max_chars=3000,
        key="task_prompt",
    )

    st.caption("💰 Cada corrección cuesta unos 3–5 céntimos de dólar con Claude Sonnet (más páginas = algo más). El coste exacto aparece junto a la nota.")

    btn_label = f"🚀 Corregir Writing — Nivel {level}" + (f" ({len(valid_images)} pág.)" if valid_images else "")
    go = st.button(btn_label, type="primary", use_container_width=True, disabled=not can_go)

    if st.session_state.last_error:
        st.markdown(f'<div class="error-box">⛔ {st.session_state.last_error}</div>', unsafe_allow_html=True)

    if go and can_go:
        st.session_state.result = None
        st.session_state.last_error = None
        with st.spinner(f"🔍 Analizando el examen (nivel {level})... puede tardar 30-90 segundos"):
            try:
                result = evaluate_exam(valid_images, target_level=level, task_prompt=task_prompt.strip())
                st.session_state.result = result
                st.session_state.session_cost += result.get("_usage", {}).get("estimated_cost_usd") or 0.0
                st.session_state.session_count += 1
            except Exception as e:
                st.session_state.last_error = str(e)
                st.rerun()
        st.rerun()

    if st.session_state.result:
        st.divider()
        render_results(st.session_state.result, level)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    render_login()
else:
    render_main()
