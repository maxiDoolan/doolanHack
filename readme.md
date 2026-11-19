# 🧠 doolanHack

App personal con IA para gestionar gastos, hábitos y entrenamiento. Deployada en Streamlit Cloud con base de datos PostgreSQL en Supabase.

🔗 **Demo live:** https://doolanhack-jvrfbpdakdolyyyujbccdi.streamlit.app/

---

## ✨ Features

### 💸 Gastos
- Registrá gastos en lenguaje natural ("gasté 5000 en el super y 2000 en nafta")
- La IA extrae automáticamente descripción, monto y categoría
- Gráfico de barras por categoría
- Asesor financiero IA personalizado con tus datos

### 🤝 Split de cuentas
- Contale quién pagó qué en lenguaje natural
- La IA calcula exactamente quién le debe cuánto a quién

### ✅ Hábitos
- Creá y eliminá hábitos personalizados
- Registrá tu progreso diario con checkboxes
- Visualización de los últimos 30 días (🟩🟥⬜)
- Racha actual por hábito
- Coach de hábitos IA con contexto de tu progreso

### 🏋️ Gym
- Registrá ejercicios en lenguaje natural ("sentadilla 80kg 4x8, press banca 60kg 3x10")
- Comparación automática con tu último registro (subiste / bajaste peso)
- Gráfico de progreso por ejercicio
- Coach de gym IA
- Borrar registros individuales

---

## 🛠 Stack

| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal |
| Streamlit | Frontend y deploy |
| Groq API | LLM (extracción de datos + coaches IA) |
| Supabase | Base de datos PostgreSQL en la nube |
| Pandas | Procesamiento de datos |
| python-dotenv | Variables de entorno |

---

## 🚀 Correr localmente

```bash
# 1. Clonar el repo
git clone https://github.com/maxiDoolan/doolanHack.git
cd doolanHack

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear archivo .env
GROQ_API_KEY=tu_groq_api_key
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key

# 4. Correr la app
python -m streamlit run app.py
```

### Base de datos (Supabase)

Crear las siguientes tablas en el SQL Editor de Supabase:

```sql
create table gastos (
  id bigint generated always as identity primary key,
  fecha text, descripcion text, monto numeric, categoria text
);

create table gym (
  id bigint generated always as identity primary key,
  fecha text, ejercicio text, peso_kg numeric, series int, reps int
);

create table habitos (
  id bigint generated always as identity primary key,
  fecha text, habito text, completado boolean
);
```

---

## 📁 Estructura

```
doolanHack/
├── app.py              # App principal
├── requirements.txt    # Dependencias
└── .gitignore          # Excluye .env
```

---

Desarrollado por [Maxi Doolan](https://github.com/maxiDoolan)