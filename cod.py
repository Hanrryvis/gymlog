import streamlit as st
import json
import hashlib
from datetime import datetime, date
from pathlib import Path

# ─── Constants ──────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "workouts.json"
USERS_FILE = Path(__file__).parent / "users.json"
SALT = "gymlog_2026_salt"

DIAS_SEMANA = {
    0: "segunda-feira", 1: "terça-feira", 2: "quarta-feira",
    3: "quinta-feira", 4: "sexta-feira", 5: "sábado", 6: "domingo",
}
MESES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}


# ═══════════════════════════════════════════════════════════════════
#  DATA PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{SALT}{password}".encode("utf-8")).hexdigest()


# ─── Users ──────────────────────────────────────────────────────────
def load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": []}


def save_users(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_user(username: str):
    data = load_users()
    for u in data["users"]:
        if u["username"] == username.strip().lower():
            return u
    return None


def create_user(username: str, display_name: str, password: str):
    username_clean = username.strip().lower()
    if len(username_clean) < 3:
        return False, "Nome de usuário deve ter pelo menos 3 caracteres."
    if not username_clean.isalnum():
        return False, "Nome de usuário deve conter apenas letras e números."
    if find_user(username_clean):
        return False, "Este nome de usuário já está em uso."
    if len(password) < 4:
        return False, "A senha deve ter pelo menos 4 caracteres."

    data = load_users()
    data["users"].append({
        "username": username_clean,
        "display_name": display_name.strip(),
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(),
    })
    save_users(data)
    return True, ""


def authenticate(username: str, password: str):
    user = find_user(username)
    if user and user["password_hash"] == hash_password(password):
        return user
    return None


# ─── Workouts (multi-user) ──────────────────────────────────────────
def load_workouts(username: str) -> list:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data if username == "default" else []
        return data.get(username, [])
    return []


def save_workouts(username: str, workouts: list):
    all_data = {}
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            all_data["default"] = raw
        else:
            all_data = raw
    all_data[username] = workouts
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
#  CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp > header {display: none;}

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

    /* Exercise detail */
    .exercise-detail {
        background: #0f3460;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 8px;
        margin-bottom: 8px;
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

    .chart-title {
        font-size: 0.95rem;
        color: #ccc;
        margin-bottom: 10px;
    }

    .notes-text {
        color: #aaa;
        font-style: italic;
        font-size: 0.85rem;
        margin-top: 6px;
    }

    /* Make bottom padding */
    .main .block-container {
        padding-bottom: 80px;
    }

    /* Style tabs */
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

    /* Green primary button */
    .stButton > button[kind="primary"],
    button[data-testid="stFormSubmitButton"] > button {
        background-color: #2ecc71 !important;
        color: #000 !important;
        font-weight: 700;
        border: none;
        border-radius: 10px;
    }

    /* Subtle secondary button */
    .stButton > button:not([kind="primary"]) {
        background: transparent;
        border: 1px solid #444;
        color: #ccc;
        border-radius: 8px;
    }
    .stButton > button:not([kind="primary"]):hover {
        border-color: #2ecc71;
        color: #2ecc71;
    }

    /* Auth form styling */
    div[data-testid="stForm"] {
        background: #16213e;
        border: 1px solid #333;
        border-radius: 12px;
        padding: 24px;
    }

    /* Form header */
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

    /* Greeting text */
    .greeting {
        color: #aaa;
        font-size: 0.85rem;
        text-align: right;
        padding-top: 16px;
    }
    .greeting b {
        color: #2ecc71;
    }

    /* Logout button red hover */
    .logout-btn button {
        border-color: #555 !important;
    }
    .logout-btn button:hover {
        border-color: #e74c3c !important;
        color: #e74c3c !important;
    }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="GymLog",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════

defaults = {
    "authenticated": False,
    "current_user": None,
    "display_name": "",
    "auth_page": "login",
    "page": "main",          # "main" or "novo_treino"
    "workouts": None,
    "form_exercises": None,   # exercises being edited in the form
    "form_date": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ═══════════════════════════════════════════════════════════════════
#  AUTH PAGES
# ═══════════════════════════════════════════════════════════════════

def show_auth_page():
    _col1, col2, _col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<div style="text-align:center; margin-top:60px; margin-bottom:30px;">'
            '<span style="font-size:3rem;">🏋️</span><br>'
            '<span style="font-size:1.8rem; font-weight:700; color:#fff;">'
            '<span style="color:#2ecc71;">Gym</span>Log</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.session_state.auth_page == "login":
            _show_login_form()
        else:
            _show_register_form()


def _show_login_form():
    st.markdown(
        '<p style="text-align:center; color:#aaa; margin-bottom:20px;">Entre na sua conta</p>',
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        username = st.text_input("Nome de usuário", placeholder="seu_usuario")
        password = st.text_input("Senha", type="password", placeholder="Sua senha")
        submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Preencha todos os campos.")
        else:
            user = authenticate(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.current_user = user["username"]
                st.session_state.display_name = user["display_name"]
                st.session_state.workouts = load_workouts(user["username"])
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    if st.button("Não tem conta? **Cadastre-se**", use_container_width=True):
        st.session_state.auth_page = "register"
        st.rerun()


def _show_register_form():
    st.markdown(
        '<p style="text-align:center; color:#aaa; margin-bottom:20px;">Criar nova conta</p>',
        unsafe_allow_html=True,
    )
    with st.form("register_form"):
        display_name = st.text_input("Nome completo", placeholder="João Silva")
        username = st.text_input("Nome de usuário", placeholder="joao123")
        password = st.text_input("Senha", type="password", placeholder="Mínimo 4 caracteres")
        password_confirm = st.text_input("Confirmar senha", type="password", placeholder="Repita a senha")
        submitted = st.form_submit_button("Cadastrar", type="primary", use_container_width=True)

    if submitted:
        if not display_name or not username or not password:
            st.error("Preencha todos os campos.")
        elif password != password_confirm:
            st.error("As senhas não coincidem.")
        else:
            success, msg = create_user(username, display_name, password)
            if success:
                st.success("Conta criada com sucesso! Faça login.")
                st.session_state.auth_page = "login"
                st.rerun()
            else:
                st.error(msg)

    if st.button("Já tem conta? **Entrar**", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  AUTH GATE
# ═══════════════════════════════════════════════════════════════════

if not st.session_state.authenticated:
    show_auth_page()
    st.stop()

# Load workouts for current user if not loaded yet
if st.session_state.workouts is None:
    st.session_state.workouts = load_workouts(st.session_state.current_user)


# ═══════════════════════════════════════════════════════════════════
#  NOVO TREINO PAGE (full page form — replaces main view)
# ═══════════════════════════════════════════════════════════════════

def show_novo_treino():
    # Initialize form data
    if st.session_state.form_exercises is None:
        st.session_state.form_exercises = [
            {"name": "", "sets": [{"weight": 0.0, "reps": 0}]}
        ]
    if st.session_state.form_date is None:
        st.session_state.form_date = date.today()

    # Header
    col_title, col_close = st.columns([6, 1])
    with col_title:
        st.markdown(
            '<div class="top-bar"><div class="logo"><span>🏋️</span> GymLog</div></div>',
            unsafe_allow_html=True,
        )
    with col_close:
        if st.button("✕", key="close_form"):
            st.session_state.page = "main"
            st.session_state.form_exercises = None
            st.session_state.form_date = None
            st.rerun()

    st.divider()
    st.markdown(
        '<div class="form-header"><span>🏋️</span> Novo Treino</div>',
        unsafe_allow_html=True,
    )

    # Date picker
    st.session_state.form_date = st.date_input(
        "Data",
        value=st.session_state.form_date,
        format="DD/MM/YYYY",
    )

    # ─── Exercises ──────────────────────────────────────────────
    exercises = st.session_state.form_exercises

    for i, ex in enumerate(exercises):
        with st.container(border=True):
            exercises[i]["name"] = st.text_input(
                "Nome do exercício",
                value=ex["name"],
                key=f"exname_{i}",
                placeholder="Nome do exercício",
            )

            for j, s in enumerate(ex["sets"]):
                c1, c2, c3 = st.columns([3, 3, 1])
                with c1:
                    exercises[i]["sets"][j]["weight"] = st.number_input(
                        "Peso (kg)",
                        min_value=0.0,
                        step=0.5,
                        value=float(s["weight"]),
                        key=f"w_{i}_{j}",
                    )
                with c2:
                    exercises[i]["sets"][j]["reps"] = st.number_input(
                        "Reps",
                        min_value=0,
                        step=1,
                        value=int(s["reps"]),
                        key=f"r_{i}_{j}",
                    )
                with c3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if len(ex["sets"]) > 1:
                        if st.button("✕", key=f"rmset_{i}_{j}"):
                            exercises[i]["sets"].pop(j)
                            st.rerun()

            if st.button("＋ Série", key=f"addset_{i}"):
                exercises[i]["sets"].append({"weight": 0.0, "reps": 0})
                st.rerun()

    # Add exercise
    if st.button("＋ Adicionar Exercício", use_container_width=True):
        exercises.append({"name": "", "sets": [{"weight": 0.0, "reps": 0}]})
        st.rerun()

    st.markdown("---")

    # Notes
    notes = st.text_input("Notas (opcional)", placeholder="Notas (opcional)", key="form_notes")

    # Save button
    if st.button("Salvar Treino", type="primary", use_container_width=True):
        # Read values from widget keys (Streamlit updates on interaction)
        final_exercises = []
        for i, ex in enumerate(exercises):
            name = st.session_state.get(f"exname_{i}", ex["name"]).strip()
            if not name:
                continue
            final_sets = []
            for j, s in enumerate(ex["sets"]):
                w = st.session_state.get(f"w_{i}_{j}", s["weight"])
                r = st.session_state.get(f"r_{i}_{j}", s["reps"])
                final_sets.append({"weight": float(w), "reps": int(r)})
            final_exercises.append({"name": name, "sets": final_sets})

        if not final_exercises:
            st.error("Adicione pelo menos um exercício com nome.")
        else:
            workout = {
                "date": st.session_state.form_date.isoformat(),
                "exercises": final_exercises,
                "notes": notes,
            }
            st.session_state.workouts.append(workout)
            save_workouts(st.session_state.current_user, st.session_state.workouts)

            # Reset form and go back
            st.session_state.page = "main"
            st.session_state.form_exercises = None
            st.session_state.form_date = None
            st.success("Treino salvo!")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════
#  MAIN PAGE (Histórico + Progresso)
# ═══════════════════════════════════════════════════════════════════

def show_main():
    # Top bar: logo + greeting + logout
    c1, c2, c3 = st.columns([4, 3, 1])
    with c1:
        st.markdown(
            '<div class="top-bar"><div class="logo"><span>🏋️</span> GymLog</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="greeting">Olá, <b>{st.session_state.display_name}</b></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Sair", key="logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # New workout button (full width, below top bar)
    if st.button("＋  Novo Treino", type="primary", use_container_width=True):
        st.session_state.page = "novo_treino"
        st.session_state.form_exercises = None
        st.session_state.form_date = None
        st.rerun()

    st.divider()

    # Tabs
    tab_hist, tab_prog = st.tabs(["🕐  Histórico", "📊  Progresso"])

    # ─── Histórico ──────────────────────────────────────────────
    with tab_hist:
        workouts = st.session_state.workouts
        if not workouts:
            st.info("Nenhum treino registrado ainda. Clique em **＋ Novo Treino** para começar!")
        else:
            sorted_wk = sorted(workouts, key=lambda w: w["date"], reverse=True)
            for idx, w in enumerate(sorted_wk):
                d = datetime.strptime(w["date"], "%Y-%m-%d").date()
                n_ex = len(w.get("exercises", []))
                label = format_date_pt(d)

                with st.expander(f"**{label}**  \n{n_ex} exercício{'s' if n_ex != 1 else ''}"):
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

                    if st.button("🗑️ Excluir treino", key=f"del_{idx}"):
                        st.session_state.workouts.remove(w)
                        save_workouts(st.session_state.current_user, st.session_state.workouts)
                        st.rerun()

    # ─── Progresso ──────────────────────────────────────────────
    with tab_prog:
        workouts = st.session_state.workouts
        exercise_names = get_all_exercise_names(workouts)

        if not exercise_names:
            st.info("Registre treinos para ver seu progresso.")
        else:
            selected = st.radio(
                "Exercício",
                exercise_names,
                horizontal=True,
                label_visibility="collapsed",
            )

            history = get_exercise_history(workouts, selected)

            if len(history) < 1:
                st.info("Nenhum dado encontrado para este exercício.")
            else:
                # Comparison card
                if len(history) >= 2:
                    curr = history[-1]["max_weight"]
                    prev = history[-2]["max_weight"]
                    diff = curr - prev
                    sign = "+" if diff >= 0 else ""
                    icon_cls = "comparison-icon-up" if diff >= 0 else "comparison-icon-down"
                    icon = "📈" if diff >= 0 else "📉"

                    st.markdown(
                        f'<div class="comparison-card">'
                        f'<div class="{icon_cls}">{icon}</div>'
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
                st.line_chart(
                    {"Data": [h["date"] for h in history],
                     "Peso Máximo (kg)": [h["max_weight"] for h in history]},
                    x="Data", y="Peso Máximo (kg)", color="#2ecc71",
                )

                # Volume chart
                st.markdown(
                    '<div class="chart-title">Volume total por sessão</div>',
                    unsafe_allow_html=True,
                )
                st.line_chart(
                    {"Data": [h["date"] for h in history],
                     "Volume (kg)": [h["volume"] for h in history]},
                    x="Data", y="Volume (kg)", color="#3498db",
                )


# ═══════════════════════════════════════════════════════════════════
#  ROUTER — decide which page to show
# ═══════════════════════════════════════════════════════════════════

if st.session_state.page == "novo_treino":
    show_novo_treino()
else:
    show_main()
