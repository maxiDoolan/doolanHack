import streamlit as st
import pandas as pd
import json
import os
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv
from datetime import date

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# ── HELPERS SUPABASE ─────────────────────────────────────────────────────────

def cargar_gastos():
    res = supabase.table("gastos").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "fecha", "descripcion", "monto", "categoria"])

def guardar_gasto(fecha, descripcion, monto, categoria):
    supabase.table("gastos").insert({
        "fecha": fecha, "descripcion": descripcion,
        "monto": monto, "categoria": categoria
    }).execute()

def cargar_gym():
    res = supabase.table("gym").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "fecha", "ejercicio", "peso_kg", "series", "reps"])

def guardar_ejercicio(fecha, ejercicio, peso_kg, series, reps):
    supabase.table("gym").insert({
        "fecha": fecha, "ejercicio": ejercicio,
        "peso_kg": peso_kg, "series": series, "reps": reps
    }).execute()

def borrar_ejercicio(id_row):
    supabase.table("gym").delete().eq("id", int(id_row)).execute()

def cargar_habitos():
    res = supabase.table("habitos").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["id", "fecha", "habito", "completado"])

def guardar_habitos_hoy(completados, hoy):
    # Borra los de hoy y reinserta
    supabase.table("habitos").delete().eq("fecha", hoy).execute()
    for h in completados:
        supabase.table("habitos").insert({
            "fecha": hoy, "habito": h["habito"], "completado": h["completado"]
        }).execute()

def cargar_lista():
    # Guardamos la lista de hábitos como un único registro especial
    res = supabase.table("habitos").select("habito").execute()
    if res.data:
        habitos = list(dict.fromkeys([r["habito"] for r in res.data]))
        return habitos if habitos else ["Gym", "Leer", "Programar"]
    return ["Gym", "Leer", "Programar"]

# ── GROQ HELPERS ─────────────────────────────────────────────────────────────

def extraer_ejercicios(texto):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": f"""Extraé los ejercicios de este texto y devolvé SOLO un JSON así, sin explicaciones:
[{{"ejercicio": "sentadilla", "peso_kg": 80, "series": 4, "reps": 8}}]
Texto: {texto}"""}]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

def extraer_gastos(texto):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": f"""Extraé los gastos de este texto y devolvé SOLO un JSON así, sin explicaciones:
[{{"descripcion": "supermercado", "monto": 5000, "categoria": "Comida"}}]
Categorías posibles: Comida, Transporte, Entretenimiento, Salud, Educación, Servicios, Otro.
Texto: {texto}"""}]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

# ── APP ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="doolanHack", page_icon="🧠", layout="centered")
st.title("🧠 doolanHack")

tab1, tab2, tab3, tab4 = st.tabs(["💸 Gastos", "🤝 Split", "✅ Hábitos", "🏋️ Gym"])

# ── TAB 1: GASTOS ─────────────────────────────────────────────────────────────
with tab1:
    st.header("💸 Gastos")

    entrada_gastos = st.text_input("Contame tus gastos:",
                                    placeholder="ej: gasté 5000 en el super, 2000 en nafta y 1500 en Netflix")

    if st.button("Registrar", key="gastos"):
        with st.spinner("Analizando..."):
            gastos = extraer_gastos(entrada_gastos)
            hoy = str(date.today())
            for g in gastos:
                guardar_gasto(hoy, g["descripcion"], g["monto"], g["categoria"])
            st.success(f"✅ Registrados {len(gastos)} gastos")

    st.divider()
    st.subheader("📊 Resumen")

    df_gastos = cargar_gastos()
    if df_gastos.empty:
        st.info("Todavía no hay gastos registrados.")
    else:
        total_por_categoria = df_gastos.groupby("categoria")["monto"].sum()
        st.bar_chart(total_por_categoria)
        st.write(f"**Total gastado:** ${df_gastos['monto'].sum():,.0f}")

    st.subheader("📋 Detalle de gastos")
    df_gastos = cargar_gastos()
    if not df_gastos.empty:
        st.dataframe(df_gastos[["fecha","descripcion","monto","categoria"]].sort_values("fecha", ascending=False))

    st.divider()
    st.subheader("💡 Asesor Financiero IA")
    pregunta_finanzas = st.text_input("Preguntale al asesor:", placeholder="ej: ¿cómo puedo ahorrar más?")
    if st.button("Consultar", key="asesor"):
        with st.spinner("El asesor está analizando..."):
            df_gastos = cargar_gastos()
            resumen = ""
            if not df_gastos.empty:
                total_por_cat = df_gastos.groupby("categoria")["monto"].sum().to_dict()
                total = df_gastos["monto"].sum()
                resumen = f"El usuario tiene registrados estos gastos: {total_por_cat}. Total: ${total:,.0f}."
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "system", "content": f"""Sos un asesor financiero personal. Respondés en español, de forma clara y práctica. Ayudás con ahorro, metas financieras, presupuesto y planificación. {resumen}"""},
                          {"role": "user", "content": pregunta_finanzas}]
            )
            st.write(response.choices[0].message.content)

# ── TAB 2: SPLIT ──────────────────────────────────────────────────────────────
with tab2:
    st.header("🤝 Split de cuentas")
    entrada_split = st.text_area("Contame la cuenta:", placeholder="ej: fuimos 4 al restaurant. Yo pagué 8000, Juan pagó 3000, María no pagó nada y Pedro pagó 5000.")
    if st.button("Calcular", key="split"):
        with st.spinner("Calculando..."):
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "system", "content": "Sos un calculador de splits de cuentas. Analizás quién pagó qué, calculás cuánto debería pagar cada uno en partes iguales, y decís exactamente quién le debe cuánto a quién para saldar todo. Respondés en español, de forma clara con el detalle de cada transferencia necesaria."},
                          {"role": "user", "content": entrada_split}]
            )
            st.write(response.choices[0].message.content)

# ── TAB 3: HÁBITOS ────────────────────────────────────────────────────────────
with tab3:
    st.header("✅ Hábitos")

    # Administrar lista de hábitos (guardada en session_state + Supabase)
    if "lista_habitos" not in st.session_state:
        st.session_state.lista_habitos = cargar_lista()

    with st.expander("⚙️ Administrar hábitos"):
        nuevo = st.text_input("Nuevo hábito:", placeholder="ej: Meditar")
        if st.button("➕ Agregar", key="agregar_hab"):
            if nuevo and nuevo not in st.session_state.lista_habitos:
                st.session_state.lista_habitos.append(nuevo)
                st.rerun()

        st.write("**Tus hábitos:**")
        for h in st.session_state.lista_habitos:
            col1, col2 = st.columns([4, 1])
            col1.write(h)
            if col2.button("🗑️", key=f"del_{h}"):
                st.session_state.lista_habitos.remove(h)
                st.rerun()

    hoy = str(date.today())
    lista = st.session_state.lista_habitos
    df_habitos = cargar_habitos()

    st.subheader(f"📅 Hoy — {hoy}")
    completados = []
    for habito in lista:
        check = st.checkbox(habito, key=f"hab_{habito}")
        completados.append({"habito": habito, "completado": check})

    if st.button("Guardar hábitos", key="habitos"):
        with st.spinner("Guardando..."):
            guardar_habitos_hoy(completados, hoy)
            completados_hoy = sum(1 for h in completados if h["completado"])
            st.success(f"✅ {completados_hoy}/{len(lista)} hábitos completados hoy")

    st.divider()
    st.subheader("📈 Tu racha")
    df_habitos = cargar_habitos()

    if not df_habitos.empty:
        lista_actual = st.session_state.lista_habitos
        habito_sel = st.selectbox("Elegí un hábito:", lista_actual)

        df_hab = df_habitos[df_habitos["habito"] == habito_sel].copy()
        df_hab["fecha"] = pd.to_datetime(df_hab["fecha"])

        from datetime import timedelta
        hoy_dt = pd.Timestamp(date.today())
        fechas_30 = [hoy_dt - timedelta(days=i) for i in range(29, -1, -1)]

        celdas = []
        for f in fechas_30:
            fila = df_hab[df_hab["fecha"] == f]
            if not fila.empty and fila["completado"].values[0]:
                celdas.append("🟩")
            elif not fila.empty:
                celdas.append("🟥")
            else:
                celdas.append("⬜")

        st.write("**Últimos 30 días** (🟩 hecho · 🟥 no hecho · ⬜ sin registro)")
        for i in range(0, 30, 7):
            st.write(" ".join(celdas[i:i+7]))

        racha = 0
        for c in reversed(celdas):
            if c == "🟩":
                racha += 1
            else:
                break
        st.metric("🔥 Racha actual", f"{racha} días")
    else:
        st.info("Todavía no hay datos registrados.")

    st.divider()
    st.subheader("🧠 Coach de Hábitos")
    pregunta_habitos = st.text_input("Preguntale al coach:", placeholder="ej: ¿cómo puedo ser más constante?")
    if st.button("Consultar", key="coach_habitos"):
        with st.spinner("El coach está pensando..."):
            df_habitos = cargar_habitos()
            contexto = ""
            if not df_habitos.empty:
                lista_actual = st.session_state.lista_habitos
                contexto = f"El usuario está trackeando estos hábitos: {', '.join(lista_actual)}."
                completados_total = df_habitos[df_habitos["completado"] == True].shape[0]
                total = df_habitos.shape[0]
                if total > 0:
                    porcentaje = round(completados_total / total * 100)
                    contexto += f" Completó el {porcentaje}% de sus hábitos registrados."
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "system", "content": f"""Sos un coach de hábitos y productividad personal. Ayudás a las personas a construir hábitos duraderos, mantener constancia y empezar nuevas rutinas. Usás técnicas basadas en evidencia (habit stacking, implementación de intenciones, recompensas, etc.). Respondés en español, de forma motivadora, clara y práctica. Consejos concretos y accionables. {contexto}"""},
                          {"role": "user", "content": pregunta_habitos}]
            )
            st.write(response.choices[0].message.content)

# ── TAB 4: GYM ────────────────────────────────────────────────────────────────
with tab4:
    st.header("🏋️ Gym")

    hoy = str(date.today())
    df_gym = cargar_gym()
    entrenamientos_hoy = df_gym[df_gym["fecha"] == hoy] if not df_gym.empty else pd.DataFrame()

    if not entrenamientos_hoy.empty:
        st.success(f"✅ Ya registraste {len(entrenamientos_hoy)} ejercicios hoy")
        st.dataframe(entrenamientos_hoy[["ejercicio", "peso_kg", "series", "reps"]])
        st.divider()

    entrada_gym = st.text_input("¿Qué entrenaste hoy?", placeholder="ej: sentadilla 80kg 4x8, press banca 60kg 3x10")

    if st.button("Registrar", key="gym"):
        with st.spinner("Analizando..."):
            ejercicios = extraer_ejercicios(entrada_gym)
            for e in ejercicios:
                guardar_ejercicio(hoy, e["ejercicio"], e["peso_kg"], e["series"], e["reps"])
            df_gym = cargar_gym()
            st.success(f"✅ Registrados {len(ejercicios)} ejercicios")
            for e in ejercicios:
                nombre = e["ejercicio"]
                peso_hoy = e["peso_kg"]
                historial = df_gym[(df_gym["ejercicio"] == nombre) & (df_gym["fecha"] != hoy)]
                if not historial.empty:
                    ultimo_peso = historial.sort_values("fecha").iloc[-1]["peso_kg"]
                    diff = peso_hoy - ultimo_peso
                    if diff > 0:
                        st.write(f"💪 **{nombre}**: {peso_hoy}kg — subiste {diff}kg desde la última vez ({ultimo_peso}kg) 🔥")
                    elif diff < 0:
                        st.write(f"📉 **{nombre}**: {peso_hoy}kg — bajaste {abs(diff)}kg desde la última vez ({ultimo_peso}kg)")
                    else:
                        st.write(f"➡️ **{nombre}**: {peso_hoy}kg — igual que la última vez")
                else:
                    st.write(f"🆕 **{nombre}**: primer registro con {peso_hoy}kg")

    st.divider()
    df_gym = cargar_gym()
    if not df_gym.empty:
        with st.expander("🗑️ Borrar un ejercicio registrado"):
            fechas = df_gym["fecha"].unique()[::-1]
            fecha_sel = st.selectbox("Fecha:", fechas, key="fecha_borrar")
            df_fecha = df_gym[df_gym["fecha"] == fecha_sel]
            idx_sel = st.selectbox("Ejercicio:", df_fecha.index,
                                    format_func=lambda i: f"{df_fecha.loc[i,'ejercicio']} — {df_fecha.loc[i,'peso_kg']}kg {df_fecha.loc[i,'series']}x{df_fecha.loc[i,'reps']}")
            if st.button("Borrar", key="borrar_gym"):
                borrar_ejercicio(df_fecha.loc[idx_sel, "id"])
                st.success("✅ Ejercicio borrado")
                st.rerun()

    st.divider()
    st.subheader("🤖 Coach IA")
    pregunta_gym = st.text_input("Preguntale al coach:", placeholder="ej: ¿cómo hago bien una sentadilla?")
    if st.button("Preguntar", key="coach"):
        with st.spinner("El coach está pensando..."):
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "system", "content": "Sos un coach de gym experto. Respondés en español, de forma clara y práctica. Explicás técnica, músculos trabajados y consejos de seguridad. Respuestas cortas y directas."},
                          {"role": "user", "content": pregunta_gym}]
            )
            st.write(response.choices[0].message.content)

    st.divider()
    st.subheader("📈 Tu progreso")
    df_gym = cargar_gym()
    if df_gym.empty:
        st.info("Todavía no hay datos registrados.")
    else:
        ejercicio_sel = st.selectbox("Elegí un ejercicio:", df_gym["ejercicio"].unique())
        df_filtrado = df_gym[df_gym["ejercicio"] == ejercicio_sel]
        st.line_chart(df_filtrado.set_index("fecha")["peso_kg"])
        st.dataframe(df_filtrado[["fecha","ejercicio","peso_kg","series","reps"]])