import streamlit as st
import json
import os
import locale
from datetime import datetime, date
from pathlib import Path

# ─── Data persistence ───────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "workouts.json"


def load_workouts():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_workouts(workouts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(workouts, f, ensure_ascii=False, indent=2)


# ─── Helpers ────────────────────────────────────────────────────────
DIAS_SEMANA = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}

MESES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


def format_date_pt(d):
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    dia_semana = DIAS_SEMANA[d.weekday()]
    return f"{dia_semana}, {d.day} de {MESES[d.month]}"


def get_all_exercise_names(workouts):
    names = set()
    for w in workouts:
        for ex in w.get("exercises", []):
            names.add(ex["name"].strip().lower())
    return sorted(names)


def get_exercise_history(workouts, exercise_name):
    """Return list of (date, max_weight, total_volume) for an exercise."""
    history = []
    for w in sorted(workouts, key=lambda x: x["date"]):
        for ex in w.get("exercises", []):
            if ex["name"].strip().lower() == exercise_name.lower():
                sets = ex.get("sets", [])
                if not sets:
                    continue
                max_w = max(s["weight"] for s in sets)
                volume = sum(s["weight"] * s["reps"] for s in sets)
                history.append({
                    "date": w["date"],
                    "max_weight": max_w,
                    "volume": volume,
                })
    return history


# ─── Custom CSS (dark theme matching the design) ───────────────────
CUSTOM_CSS = """
<style>
    /* Hide Streamlit defaults */
    #MainMenu, footer, header {visibility: hidden;}
    .stApp > header {display: none;}

    /* Dark background */
    .stApp {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }

    /* Top bar */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-bottom: 16px;
    }
    .top-bar .logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
    }
    .top-bar .logo span {
        color: #2ecc71;
        margin-right: 6px;
    }

    /* Workout card */
    .workout-card {
        background: #16213e;
        border: 1px solid #2ecc71;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        cursor: pointer;
    }
    .workout-card .wdate {
        font-size: 1.05rem;
        font-weight: 600;
        color: #fff;
    }
    .workout-card .wcount {
        font-size: 0.85rem;
        color: #aaa;
        margin-top: 2px;
    }

    /* Exercise detail inside expanded card */
    .exercise-detail {
        background: #0f3460;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 8px;
    }
    .exercise-detail .ex-name {
        font-weight: 600;
        color: #2ecc71;
        margin-bottom: 6px;
    }
    .set-row {
        color: #ccc;
        font-size: 0.9rem;
        padding: 2px 0;
    }

    /* Progress comparison badge */
    .comparison-card {
        background: #16213e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .comparison-icon-up {
        width: 44px; height: 44px;
        border-radius: 50%;
        background: rgba(46,204,113,0.15);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
    }
    .comparison-icon-down {
        width: 44px; height: 44px;
        border-radius: 50%;
        background: rgba(231,76,60,0.15);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
    }
    .comparison-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #fff;
    }
    .comparison-label {
        font-size: 0.82rem;
        color: #aaa;
    }

    /* Chart container */
    .chart-container {
        background: #16213e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .chart-title {
        font-size: 0.95rem;
        color: #ccc;
        margin-bottom: 10px;
    }

    /* Bottom nav */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #1a1a2e;
        border-top: 1px solid #333;
        display: flex;
        justify-content: center;
        gap: 120px;
        padding: 10px 0 14px;
        z-index: 999;
    }
    .nav-item {
        text-align: center;
        cursor: pointer;
        color: #888;
        font-size: 0.8rem;
    }
    .nav-item.active {
        color: #2ecc71;
    }
    .nav-item .nav-icon {
        font-size: 1.3rem;
        margin-bottom: 2px;
    }

    /* Notes */
    .notes-text {
        color: #aaa;
        font-style: italic;
        font-size: 0.85rem;
        margin-top: 6px;
    }

    /* Form section header */
    .form-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1.3rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 16px;
    }
    .form-header span {
        color: #2ecc71;
    }

    /* Pill buttons for exercise filter */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        border-radius: 20px !important;
    }

    /* Make bottom padding so content doesn't hide behind nav */
    .main .block-container {
        padding-bottom: 80px;
    }

    /* Style tabs to look like bottom nav */
    .stTabs [data-baseweb="tab-list"] {
        gap: 80px;
        justify-content: center;
        background: #1a1a2e;
        border-top: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        color: #2ecc71 !important;
        border-bottom-color: #2ecc71 !important;
    }

    /* Green button styling */
    .stButton > button[kind="primary"] {
        background-color: #2ecc71 !important;
        color: #000 !important;
        font-weight: 700;
        border: none;
        border-radius: 10px;
    }

    /* Dialog styling */
    div[data-testid="stDialog"] {
        background-color: #1a1a2e !important;
    }
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] {
        background-color: #1a1a2e;
    }
</style>
"""


# ─── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="GymLog",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Session state init ────────────────────────────────────────────
if "workouts" not in st.session_state:
    st.session_state.workouts = load_workouts()

if "show_form" not in st.session_state:
    st.session_state.show_form = False


# ─── New Workout Dialog ────────────────────────────────────────────
@st.dialog("Novo Treino", width="large")
def new_workout_dialog():
    st.markdown(
        '<div class="form-header"><span>🏋️</span> Novo Treino</div>',
        unsafe_allow_html=True,
    )

    workout_date = st.date_input(
        "Data",
        value=date.today(),
        format="DD/MM/YYYY",
    )

    # Manage exercises in dialog via session state
    if "dialog_exercises" not in st.session_state:
        st.session_state.dialog_exercises = [
            {"name": "", "sets": [{"weight": 0.0, "reps": 0}]}
        ]

    exercises_to_remove = []
    for i, ex in enumerate(st.session_state.dialog_exercises):
        with st.container(border=True):
            ex["name"] = st.text_input(
                "Nome do exercício",
                value=ex["name"],
                key=f"ex_name_{i}",
                placeholder="Nome do exercício",
            )

            sets_to_remove = []
            for j, s in enumerate(ex["sets"]):
                cols = st.columns([3, 3, 1])
                with cols[0]:
                    ex["sets"][j]["weight"] = st.number_input(
                        "Peso (kg)",
                        min_value=0.0,
                        step=0.5,
                        value=float(s["weight"]),
                        key=f"weight_{i}_{j}",
                    )
                with cols[1]:
                    ex["sets"][j]["reps"] = st.number_input(
                        "Reps",
                        min_value=0,
                        step=1,
                        value=int(s["reps"]),
                        key=f"reps_{i}_{j}",
                    )
                with cols[2]:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✕", key=f"rm_set_{i}_{j}"):
                        sets_to_remove.append(j)

            for j in reversed(sets_to_remove):
                if len(ex["sets"]) > 1:
                    ex["sets"].pop(j)
                    st.rerun()

            if st.button("＋ Série", key=f"add_set_{i}"):
                ex["sets"].append({"weight": 0.0, "reps": 0})
                st.rerun()

    # Add exercise button
    if st.button("＋ Adicionar Exercício", use_container_width=True):
        st.session_state.dialog_exercises.append(
            {"name": "", "sets": [{"weight": 0.0, "reps": 0}]}
        )
        st.rerun()

    notes = st.text_input("Notas (opcional)", placeholder="Notas (opcional)")

    if st.button("Salvar Treino", type="primary", use_container_width=True):
        # Validate
        valid_exercises = [
            ex for ex in st.session_state.dialog_exercises
            if ex["name"].strip()
        ]
        if not valid_exercises:
            st.error("Adicione pelo menos um exercício com nome.")
            return

        workout = {
            "date": workout_date.isoformat(),
            "exercises": valid_exercises,
            "notes": notes,
        }
        st.session_state.workouts.append(workout)
        save_workouts(st.session_state.workouts)
        del st.session_state.dialog_exercises
        st.rerun()


# ─── Top bar ────────────────────────────────────────────────────────
top_cols = st.columns([6, 1])
with top_cols[0]:
    st.markdown(
        '<div class="top-bar"><div class="logo"><span>🏋️</span> GymLog</div></div>',
        unsafe_allow_html=True,
    )
with top_cols[1]:
    if st.button("＋ Treino", type="primary"):
        st.session_state.dialog_exercises = [
            {"name": "", "sets": [{"weight": 0.0, "reps": 0}]}
        ]
        new_workout_dialog()

st.divider()

# ─── Navigation tabs ───────────────────────────────────────────────
tab_historico, tab_progresso = st.tabs(["🕐  Histórico", "📊  Progresso"])

# ─── Histórico tab ─────────────────────────────────────────────────
with tab_historico:
    workouts = st.session_state.workouts
    if not workouts:
        st.info("Nenhum treino registrado ainda. Clique em **＋ Treino** para começar!")
    else:
        # Group by date, most recent first
        sorted_workouts = sorted(workouts, key=lambda w: w["date"], reverse=True)
        for idx, w in enumerate(sorted_workouts):
            d = datetime.strptime(w["date"], "%Y-%m-%d").date()
            n_exercises = len(w.get("exercises", []))
            label = format_date_pt(d)

            with st.expander(f"**{label}**  \n{n_exercises} exercício{'s' if n_exercises != 1 else ''}"):
                for ex in w.get("exercises", []):
                    st.markdown(
                        f'<div class="exercise-detail">'
                        f'<div class="ex-name">{ex["name"]}</div>',
                        unsafe_allow_html=True,
                    )
                    for j, s in enumerate(ex.get("sets", [])):
                        st.markdown(
                            f'<div class="set-row">Série {j+1}: {s["weight"]} kg × {s["reps"]} reps</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

                if w.get("notes"):
                    st.markdown(
                        f'<div class="notes-text">📝 {w["notes"]}</div>',
                        unsafe_allow_html=True,
                    )

                # Delete workout button
                if st.button("🗑️ Excluir treino", key=f"del_{idx}"):
                    st.session_state.workouts.remove(w)
                    save_workouts(st.session_state.workouts)
                    st.rerun()

# ─── Progresso tab ─────────────────────────────────────────────────
with tab_progresso:
    workouts = st.session_state.workouts
    exercise_names = get_all_exercise_names(workouts)

    if not exercise_names:
        st.info("Registre treinos para ver seu progresso.")
    else:
        # Exercise filter pills
        selected_exercise = st.radio(
            "Exercício",
            exercise_names,
            horizontal=True,
            label_visibility="collapsed",
        )

        history = get_exercise_history(workouts, selected_exercise)

        if len(history) < 1:
            st.info("Nenhum dado encontrado para este exercício.")
        else:
            # Comparison card
            if len(history) >= 2:
                current_max = history[-1]["max_weight"]
                previous_max = history[-2]["max_weight"]
                diff = current_max - previous_max
                sign = "+" if diff >= 0 else ""

                if diff >= 0:
                    icon_class = "comparison-icon-up"
                    icon = "📈"
                else:
                    icon_class = "comparison-icon-down"
                    icon = "📉"

                st.markdown(
                    f'<div class="comparison-card">'
                    f'<div class="{icon_class}">{icon}</div>'
                    f'<div>'
                    f'<div class="comparison-value">{sign}{diff:.1f} kg</div>'
                    f'<div class="comparison-label">vs. treino anterior (peso máximo)</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

            # Max weight chart
            st.markdown(
                '<div class="chart-title">Histórico de peso máximo</div>',
                unsafe_allow_html=True,
            )
            chart_data_weight = {
                "Data": [h["date"] for h in history],
                "Peso Máximo (kg)": [h["max_weight"] for h in history],
            }
            st.line_chart(
                chart_data_weight,
                x="Data",
                y="Peso Máximo (kg)",
                color="#2ecc71",
            )

            # Volume chart
            st.markdown(
                '<div class="chart-title">Volume total por sessão</div>',
                unsafe_allow_html=True,
            )
            chart_data_volume = {
                "Data": [h["date"] for h in history],
                "Volume (kg)": [h["volume"] for h in history],
            }
            st.line_chart(
                chart_data_volume,
                x="Data",
                y="Volume (kg)",
                color="#3498db",
            )
