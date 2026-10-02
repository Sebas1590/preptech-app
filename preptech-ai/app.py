"""Coach PrepTech — módulo de IA (Streamlit).  Ejecutar:  streamlit run app.py"""
import json
from datetime import date, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

from prompts import (FEW_SHOT_EXAMPLES, ONE_SHOT_EXAMPLE, SYSTEM_PROMPT, TECHNIQUES,  # noqa: E402
                     ZERO_SHOT_PROMPT)
from services.guardrails import InputError, RateLimiter, validate_input  # noqa: E402
from services.llm_service import (LLMError, LLMService, Usage, get_model, render_star,  # noqa: E402
                                  NOMBRES_STAR)
from services.tools import _banco  # noqa: E402

st.set_page_config(page_title="Coach PrepTech", page_icon="🎯", layout="wide")

AREAS = {"Algoritmos": "algoritmos", "System Design": "sistemas", "Behavioral": "comportamiento"}
EJEMPLO = ("En mi proyecto tuvimos un problema con la base de datos que se caía cuando había "
           "muchos usuarios. Me encargué de investigarlo. Revisé los logs, encontré que faltaba "
           "un índice y lo creé. Las consultas se volvieron mucho más rápidas.")
ATAJOS = {"🎯 Recomiéndame preguntas": "Recomiéndame preguntas para practicar según mi empresa objetivo.",
          "📊 Mi progreso": "Muéstrame mi progreso de las últimas semanas.",
          "⏳ Cuenta regresiva": "¿Cuántos días me faltan para mi entrevista y qué ritmo debo llevar?"}


# ---------------- Estado de sesión ----------------
def init_state():
    ss = st.session_state
    ss.setdefault("messages", [])      # lo que se muestra
    ss.setdefault("history", [])       # lo que se envía a la API (solo texto, sin tool calls)
    ss.setdefault("usage", Usage())
    ss.setdefault("limiter", RateLimiter(int(__import__("os").getenv("MAX_REQUESTS_PER_HOUR", "40"))))
    ss.setdefault("progreso_real", None)
    ss.setdefault("pending", None)
    ss.setdefault("compare", None)


def get_service():
    try:
        return LLMService(), None
    except LLMError as e:
        return None, str(e)


def sidebar():
    with st.sidebar:
        st.title("🎯 Coach PrepTech")
        st.caption("Práctica orientativa: la nota del coach no predice una contratación.")
        area = st.radio("Tipo de práctica", list(AREAS), key="area")
        tecnica = st.radio("Técnica de prompting (análisis STAR)", list(TECHNIQUES), index=2, key="tecnica",
                           help="Zero-shot: sin ejemplos · One-shot: 1 ejemplo · Few-shot: 3 ejemplos")
        st.checkbox("En Behavioral, analizar con STAR las respuestas largas", value=True, key="auto_star")
        with st.expander("Perfil", expanded=False):
            st.text_input("Nombre", "Postulante", key="nombre")
            st.selectbox("Empresa objetivo", ["Google", "Amazon", "Meta", "Anthropic", "Microsoft"], key="empresa")
            st.date_input("Fecha de entrevista", date.today() + timedelta(days=21), key="fecha")
            st.number_input("Meta semanal (intentos)", 1, 100, 15, key="meta")
        with st.expander("Progreso del usuario"):
            up = st.file_uploader("JSON de tu progreso real", type="json",
                                  help="En la app web, consola del navegador: copy(localStorage['preptech:v1'])")
            if up is not None:
                try:
                    data = json.load(up)
                    if not isinstance(data.get("intentos"), list):
                        raise ValueError
                    st.session_state.progreso_real = data
                except (ValueError, AttributeError):
                    st.error("Archivo inválido: debe ser el export de PrepTech con la clave 'intentos'.")
            elif st.session_state.progreso_real is not None:
                st.session_state.progreso_real = None
            real = st.session_state.progreso_real is not None
            st.caption("✅ Usando tu progreso real" if real else "⚠️ Sin archivo: se usan **datos de DEMOSTRACIÓN** (mock).")
        st.divider()
        u = st.session_state.usage
        st.caption(f"Modelo: `{get_model()}`")
        st.caption(f"Tokens de la sesión: {u.total} (entrada {u.prompt} / salida {u.completion})")
        if st.button("🗑️ Nueva conversación"):
            st.session_state.messages, st.session_state.history = [], []
            st.rerun()
    return AREAS[area], tecnica


def ctx_y_perfil():
    ss = st.session_state
    ctx = {"user_id": "usuario-demo", "empresa": ss.empresa, "fecha_entrevista": ss.fecha.isoformat(),
           "meta_semanal": ss.meta, "progreso_real": ss.progreso_real}
    return ctx, {"nombre": ss.nombre, "empresa": ss.empresa}


# ---------------- Pestaña 1: Chat ----------------
def tab_chat(svc, err, area, tecnica):
    ss = st.session_state
    if err:
        st.error(err)
    cols = st.columns(len(ATAJOS))
    for c, (label, texto) in zip(cols, ATAJOS.items()):
        if c.button(label, use_container_width=True, disabled=svc is None):
            ss.pending = texto
    if not ss.messages:
        st.info("Hola, soy tu Coach PrepTech. Pídeme un ejercicio, una pista o pega tu respuesta a una pregunta de comportamiento.")
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("tools"):
                with st.expander("🔧 Funciones consultadas"):
                    for t in m["tools"]:
                        st.code(f"{t['name']}({t['args']})\n→ source: {t['result'].get('source', '-')}", language="text")
    entrada = st.chat_input("Escribe tu mensaje…", disabled=svc is None)
    texto, ss.pending = entrada or ss.pending, None
    if texto is None:
        return
    try:
        texto = validate_input(texto)
        ss.limiter.check()
    except InputError as e:
        st.warning(str(e))
        return
    ss.messages.append({"role": "user", "content": texto})
    with st.chat_message("user"):
        st.markdown(texto)
    ctx, perfil = ctx_y_perfil()
    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            try:
                if area == "comportamiento" and ss.auto_star and len(texto.split()) >= 25:
                    d, u, _ = svc.analyze_star(tecnica, "Pregunta de comportamiento en práctica", texto)
                    respuesta, tools, flag = f"_Análisis STAR ({tecnica})_\n\n" + render_star(d), [], False
                else:
                    r = svc.chat(ss.history, texto, area, perfil, ctx)
                    respuesta, u, tools, flag = r.text, r.usage, r.tools_used, r.injection_flag
            except LLMError as e:
                st.error(str(e))
                ss.messages.pop()
                return
            except Exception:  # noqa: BLE001 - nunca mostrar traceback al usuario
                st.error("Ocurrió un error inesperado. Intenta de nuevo.")
                ss.messages.pop()
                return
        st.markdown(respuesta)
        if flag:
            st.caption("🛡️ Se detectó un intento de alterar las reglas internas; el coach las mantiene.")
    ss.usage.prompt += u.prompt
    ss.usage.completion += u.completion
    ss.history += [{"role": "user", "content": texto}, {"role": "assistant", "content": respuesta}]
    ss.messages.append({"role": "assistant", "content": respuesta, "tools": tools})
    st.rerun()


# ---------------- Pestaña 2: Analizador / comparador ----------------
def tab_analizador(svc, tecnica):
    ss = st.session_state
    st.subheader("Analizador STAR y comparación de técnicas")
    st.caption("La misma respuesta se evalúa con la misma rúbrica; solo cambia la técnica de prompting.")
    preguntas = {q["pregunta"]: q for q in _banco()["conductuales"]}
    pregunta = st.selectbox("Pregunta de comportamiento", list(preguntas))
    if st.button("Cargar respuesta de ejemplo"):
        ss.respuesta = EJEMPLO
    respuesta = st.text_area("Tu respuesta", key="respuesta", height=160, max_chars=2000)
    c1, c2 = st.columns(2)
    solo = c1.button(f"Analizar con {tecnica}", disabled=svc is None, type="primary")
    todas = c2.button("Comparar las 3 técnicas", disabled=svc is None)
    if solo or todas:
        try:
            validate_input(respuesta)
            tecnicas = list(TECHNIQUES) if todas else [tecnica]
            res = {}
            with st.spinner("Consultando al modelo…"):
                for t in tecnicas:
                    ss.limiter.check()
                    d, u, msgs = svc.analyze_star(t, pregunta, respuesta.strip())
                    ss.usage.prompt += u.prompt
                    ss.usage.completion += u.completion
                    res[t] = (d, u, msgs)
            ss.compare = res
        except (InputError, LLMError) as e:
            st.warning(str(e))
        except Exception:  # noqa: BLE001
            st.error("Ocurrió un error inesperado. Intenta de nuevo.")
    res = ss.compare
    if not res:
        return
    cols = st.columns(len(res))
    for col, (t, (d, u, msgs)) in zip(cols, res.items()):
        with col:
            st.markdown(f"### {t}")
            st.caption(f"{(len(msgs) - 2) // 2} ejemplo(s) en el prompt · {u.prompt} tokens de entrada")
            st.markdown(render_star(d))
            with st.expander("Ver prompt enviado"):
                st.code(json.dumps(msgs, ensure_ascii=False, indent=1)[:6000], language="json")
    if len(res) > 1:
        st.markdown("**Resumen comparativo**")
        filas = {"Técnica": list(res), "Nota": [r[0]["score"] for r in res.values()]}
        for k, nombre in NOMBRES_STAR.items():
            filas[nombre] = ["✅" if r[0][k]["present"] else "❌" for r in res.values()]
        filas["Tokens entrada"] = [r[1].prompt for r in res.values()]
        st.table(filas)


# ---------------- Pestaña 3: Biblioteca de prompts ----------------
def tab_biblioteca():
    st.subheader("Biblioteca de prompts (solo lectura)")
    st.caption("Los prompts internos están en `prompts/` y no se pueden editar desde la interfaz.")
    with st.expander("Prompt de sistema (system.py)"):
        st.code(SYSTEM_PROMPT, language="text")
    with st.expander("ZERO_SHOT_PROMPT — sin ejemplos (zero_shot.py)"):
        st.code(ZERO_SHOT_PROMPT, language="text")
    with st.expander("ONE_SHOT — 1 ejemplo (one_shot.py)"):
        st.json(ONE_SHOT_EXAMPLE)
    with st.expander("FEW_SHOT — 3 ejemplos (few_shot.py)"):
        st.json(FEW_SHOT_EXAMPLES)


def main():
    init_state()
    area, tecnica = sidebar()
    svc, err = get_service()
    t1, t2, t3 = st.tabs(["💬 Coach", "🧪 Analizador STAR / Comparador", "📚 Biblioteca de prompts"])
    with t1:
        tab_chat(svc, err, area, tecnica)
    with t2:
        if err:
            st.error(err)
        tab_analizador(svc, tecnica)
    with t3:
        tab_biblioteca()


main()
