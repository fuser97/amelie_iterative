import matplotlib
matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io
import sqlite3
import json
import bcrypt

# Database Initialization
def init_db():
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT
                )''')

    # Create scenarios table
    c.execute('''CREATE TABLE IF NOT EXISTS scenarios (
                    username TEXT,
                    scenario_name TEXT,
                    data TEXT,
                    FOREIGN KEY(username) REFERENCES users(username)
                )''')

    conn.commit()
    conn.close()

init_db()

# Password Hashing and Verification
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# User Registration
def register_user(username, password):
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return "Username already exists."

    hashed_password = hash_password(password)
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()
    return "User registered successfully."

# User Authentication
def authenticate_user(username, password):
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    if result and check_password(password, result[0]):
        return True
    return False

# Login/Registration UI
def login_or_register():
    st.sidebar.title("Login or Register")
    choice = st.sidebar.radio("Select an option:", ["Login", "Register"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if choice == "Login":
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.sidebar.success(f"Welcome, {username}!")
            else:
                st.sidebar.error("Invalid username or password.")
    elif choice == "Register":
        if st.sidebar.button("Register"):
            if username and password:
                message = register_user(username, password)
                if "successfully" in message:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)
            else:
                st.sidebar.error("Please provide a username and password.")

# Scenario Management
def save_scenario_to_db(username, scenario_name, scenario_data):
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scenarios WHERE username=? AND scenario_name=?", (username, scenario_name))
    exists = c.fetchone()[0]

    if exists:
        c.execute("UPDATE scenarios SET data=? WHERE username=? AND scenario_name=?",
                  (json.dumps(scenario_data), username, scenario_name))
    else:
        c.execute("INSERT INTO scenarios (username, scenario_name, data) VALUES (?, ?, ?)",
                  (username, scenario_name, json.dumps(scenario_data)))

    conn.commit()
    conn.close()
    return "Scenario saved successfully!" if not exists else "Scenario updated successfully!"

def load_scenarios_from_db(username):
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()
    c.execute("SELECT scenario_name, data FROM scenarios WHERE username=?", (username,))
    rows = c.fetchall()
    conn.close()
    return {row[0]: json.loads(row[1]) for row in rows}

def save_current_scenario():
    username = st.session_state.get("username", "guest")
    scenario_name = st.text_input("Enter Scenario Name:")
    if st.button("Save Scenario"):
        if scenario_name:
            scenario_data = {
                "economic_kpis": st.session_state.get("economic_kpis", {}),
                "technical_kpis": st.session_state.get("technical_kpis", {})
            }
            message = save_scenario_to_db(username, scenario_name, scenario_data)
            st.success(message)
        else:
            st.error("Please provide a scenario name.")

def load_scenario():
    username = st.session_state.get("username", "guest")
    scenarios = load_scenarios_from_db(username)
    st.markdown("### Load Scenario")
    scenario_list = list(scenarios.keys())
    if scenario_list:
        selected_scenario = st.selectbox("Select a scenario to load:", scenario_list)
        if st.button("Load Scenario"):
            scenario_data = scenarios[selected_scenario]
            for key, value in scenario_data.items():
                st.session_state[key] = value
            st.success(f"Scenario '{selected_scenario}' loaded!")
    else:
        st.info("No saved scenarios available.")

# App Layout
st.set_page_config(
    page_title="Amelie KPI Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login_or_register()
    st.stop()


def economic_kpis():
    st.title("Economic KPIs")

    # Section Dropdown for Navigation
    sections = ["General Assumptions", "CapEx Configuration", "OpEx Configuration", "Results"]
    selected_section = st.selectbox("Jump to Section:", sections)

    # General Assumptions Section
    if selected_section == "General Assumptions":
        st.subheader("General Assumptions")
        if "general_assumptions" not in st.session_state:
            st.session_state.general_assumptions = [
                "Pilot project sized for 10 kg BM per batch.",
                "No infrastructure costs.",
                "Energy cost calculated dynamically based on kWh per machine.",
                "Labor includes one operator per batch.",
                "Maintenance and disposal are estimated."
            ]

        updated_assumptions = []

        for idx, assumption in enumerate(st.session_state.general_assumptions):
            col1, col2 = st.columns([4, 1])
            with col1:
                new_assumption = st.text_area(f"Assumption {idx + 1}:", value=assumption, key=f"edit_assumption_{idx}")
            with col2:
                if st.button(f"Remove Assumption {idx + 1}", key=f"remove_assumption_{idx}"):
                    continue

            updated_assumptions.append(new_assumption)

        st.session_state.general_assumptions = updated_assumptions

        st.markdown("**Add New Assumption**")
        new_assumption = st.text_area("New Assumption:", key="new_assumption")
        if st.button("Add Assumption"):
            if new_assumption:
                st.session_state.general_assumptions.append(new_assumption)
                st.success("Added new assumption.")
            else:
                st.error("Assumption cannot be empty.")

        st.markdown("### Current Assumptions")
        for idx, assumption in enumerate(st.session_state.general_assumptions):
            st.write(f"{idx + 1}. {assumption}")

    # CapEx Configuration Section
    elif selected_section == "CapEx Configuration":
        st.subheader("CapEx Configuration")
        if "capex_data" not in st.session_state:
            st.session_state.capex_data = model.capex.copy()

        capex_to_delete = []
        for key in list(st.session_state.capex_data.keys()):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"capex_name_{key}")
            with col2:
                new_cost = st.number_input(
                    f"Edit Cost for {key} (EUR):",
                    value=float(st.session_state.capex_data[key]),
                    min_value=0.0,
                    key=f"capex_cost_{key}"
                )
            with col3:
                if st.button("Remove", key=f"remove_capex_{key}"):
                    capex_to_delete.append(key)
            if new_name != key:
                st.session_state.capex_data[new_name] = st.session_state.capex_data.pop(key)
            st.session_state.capex_data[new_name] = new_cost

        for item in capex_to_delete:
            del st.session_state.capex_data[item]

        st.markdown("**Add New CapEx Item**")
        new_capex_name = st.text_input("New CapEx Name:", key="new_capex_name")
        new_capex_cost = st.number_input("New CapEx Cost (EUR):", min_value=0.0, key="new_capex_cost")
        if st.button("Add CapEx", key="add_capex"):
            if new_capex_name and new_capex_name not in st.session_state.capex_data:
                st.session_state.capex_data[new_capex_name] = new_capex_cost
                st.success(f"Added new CapEx item: {new_capex_name}")
            elif new_capex_name in st.session_state.capex_data:
                st.error(f"The CapEx item '{new_capex_name}' already exists!")

        model.capex = st.session_state.capex_data

    # OpEx Configuration Section
    elif selected_section == "OpEx Configuration":
        st.subheader("OpEx Configuration")
        if "opex_data" not in st.session_state:
            st.session_state.opex_data = model.opex.copy()

        opex_to_delete = []
        for key in list(st.session_state.opex_data.keys()):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"opex_name_{key}")
            with col2:
                new_cost = st.number_input(
                    f"Edit Cost for {key} (EUR/batch):",
                    value=float(st.session_state.opex_data[key]),
                    min_value=0.0,
                    key=f"opex_cost_{key}"
                )
            with col3:
                if st.button("Remove", key=f"remove_opex_{key}"):
                    opex_to_delete.append(key)
            if new_name != key:
                st.session_state.opex_data[new_name] = st.session_state.opex_data.pop(key)
            st.session_state.opex_data[new_name] = new_cost

        for item in opex_to_delete:
            del st.session_state.opex_data[item]

        st.markdown("**Add New OpEx Item**")
        new_opex_name = st.text_input("New OpEx Name:", key="new_opex_name")
        new_opex_cost = st.number_input("New OpEx Cost (EUR/batch):", min_value=0.0, key="new_opex_cost")
        if st.button("Add OpEx", key="add_opex"):
            if new_opex_name and new_opex_name not in st.session_state.opex_data:
                st.session_state.opex_data[new_opex_name] = new_opex_cost
                st.success(f"Added new OpEx item: {new_opex_name}")
            elif new_opex_name in st.session_state.opex_data:
                st.error(f"The OpEx item '{new_opex_name}' already exists!")

        model.opex = st.session_state.opex_data

    # Results Section
    elif selected_section == "Results":
        st.subheader("Results")
        try:
            capex_total, opex_total = model.calculate_totals()
        except Exception as e:
            st.error(f"Error calculating totals: {e}")
            capex_total, opex_total = 0, 0

        st.write(f"**Total CapEx:** {capex_total} EUR")
        st.write(f"**Total OpEx (including energy):** {opex_total} EUR/batch")

    # Save the current economic KPIs into session state
    st.session_state["economic_kpis"] = {
        "general_assumptions": st.session_state.get("general_assumptions", []),
        "capex_data": st.session_state.get("capex_data", {}),
        "opex_data": st.session_state.get("opex_data", {}),
        "results": {
            "capex_total": capex_total,
            "opex_total": opex_total
        }
    }

    # Scenario Management
    st.sidebar.title("Scenario Management")
    if st.sidebar.button("Save Current Scenario"):
        save_current_scenario()
    if st.sidebar.button("Load Existing Scenario"):
        load_scenario()


# Technical KPIs Page
def technical_kpis():
    st.title("Technical KPIs: Efficiency and Solid/Liquid Ratios")

    # Section Dropdown for Navigation
    sections = ["Material Composition", "Efficiency Calculation", "Solid/Liquid Ratios"]
    selected_section = st.selectbox("Jump to Section:", sections)

    # Material Composition Section
    if selected_section == "Material Composition":
        st.subheader("Material Composition in Black Mass")
        if "composition" not in st.session_state:
            st.session_state.composition = {'Li': 7.0, 'Co': 15.0, 'Ni': 10.0, 'Mn': 8.0}  # Default percentages

        updated_composition = {}
        total_percentage = 0

        for material, percentage in list(st.session_state.composition.items()):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                new_material = st.text_input(f"Edit Material Name ({material})", value=material, key=f"edit_material_{material}")
            with col2:
                new_percentage = st.number_input(
                    f"Percentage of {material} in BM (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=percentage,
                    key=f"edit_percentage_{material}"
                )
            with col3:
                if st.button(f"Remove {material}", key=f"remove_material_{material}"):
                    st.session_state.composition.pop(material, None)

            updated_composition[new_material] = new_percentage
            total_percentage += new_percentage

        st.markdown("**Add New Material**")
        new_material_name = st.text_input("New Material Name", key="new_material_name")
        new_material_percentage = st.number_input("New Material Percentage (%)", min_value=0.0, max_value=100.0, key="new_material_percentage")
        if st.button("Add Material"):
            if new_material_name and new_material_name not in updated_composition:
                updated_composition[new_material_name] = new_material_percentage
                st.success(f"Added new material: {new_material_name}")
            elif new_material_name in updated_composition:
                st.error(f"Material {new_material_name} already exists!")

        st.session_state.composition = updated_composition

        if total_percentage > 100:
            st.warning(f"Total material composition exceeds 100% (currently {total_percentage:.2f}%). Adjust values accordingly.")
        elif total_percentage < 100:
            st.info(f"Total material composition is below 100% (currently {total_percentage:.2f}%).")

    # Efficiency Calculation Section
    elif selected_section == "Efficiency Calculation":
        st.subheader("Recovered Mass and Efficiency Calculation")
        recovered_masses = {}

        for material in st.session_state.composition:
            recovered_mass = st.number_input(
                f"Recovered Mass of {material} (kg):",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                key=f"recovered_mass_{material}"
            )
            recovered_masses[material] = recovered_mass

        efficiencies = {}
        total_black_mass = st.sidebar.number_input("Total Black Mass (kg):", min_value=0.1, value=10.0, step=0.1, key="total_black_mass")
        total_recovered_mass = 0

        for material, percentage in st.session_state.composition.items():
            initial_mass = total_black_mass * (percentage / 100)
            recovered_mass = recovered_masses.get(material, 0.0)
            efficiency = (recovered_mass / initial_mass) * 100 if initial_mass > 0 else 0.0
            efficiencies[material] = efficiency
            total_recovered_mass += recovered_mass

        overall_efficiency = (total_recovered_mass / total_black_mass) * 100

        st.write(f"**Overall Process Efficiency:** {overall_efficiency:.2f}%")
        st.write("**Efficiency and Recovered Mass per Material:**")
        result_df = pd.DataFrame({
            "Material": list(st.session_state.composition.keys()),
            "Initial Mass in BM (kg)": [total_black_mass * (p / 100) for p in st.session_state.composition.values()],
            "Recovered Mass (kg)": [recovered_masses.get(m, 0.0) for m in st.session_state.composition.keys()],
            "Efficiency (%)": [efficiencies.get(m, 0.0) for m in st.session_state.composition.keys()]
        })
        st.table(result_df)

    # Solid/Liquid Ratios Section
    elif selected_section == "Solid/Liquid Ratios":
        st.subheader("Solid/Liquid Ratios for Each Phase")

        if "phases" not in st.session_state:
            st.session_state.phases = {
                "Leaching in Water": {"liquids": [{"type": "Water", "volume": 20.0}], "mass": 5.0},
                "Leaching in Acid": {"liquids": [{"type": "Malic Acid", "volume": 5.0}, {"type": "Water", "volume": 2.0}], "mass": 5.0}
            }

        phases = st.session_state.phases
        updated_phases = {}

        for phase_name, phase_data in phases.items():
            st.subheader(f"Phase: {phase_name}")
            liquids = phase_data.get("liquids", [])
            updated_liquids = []

            phase_mass = st.number_input(
                f"Mass for {phase_name} (kg):", min_value=0.0, value=phase_data.get("mass", 0.0), step=0.1, key=f"mass_{phase_name}"
            )

            for idx, liquid in enumerate(liquids):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    liquid_type = st.text_input(
                        f"Liquid Type ({liquid['type']}):", value=liquid["type"], key=f"liquid_type_{phase_name}_{idx}"
                    )
                with col2:
                    liquid_volume = st.number_input(
                        f"Volume ({liquid['type']}, L):", min_value=0.0, value=liquid["volume"], step=0.1, key=f"volume_{phase_name}_{idx}"
                    )
                with col3:
                    if st.button(f"Remove {liquid['type']}", key=f"remove_{phase_name}_{idx}"):
                        continue

                updated_liquids.append({"type": liquid_type, "volume": liquid_volume})

            updated_phases[phase_name] = {"liquids": updated_liquids, "mass": phase_mass}

        st.session_state.phases = updated_phases

        sl_results = []
        for phase_name, phase_data in st.session_state.phases.items():
            phase_mass = phase_data["mass"]
            phase_liquids = phase_data["liquids"]
            total_liquid_volume = sum(liquid["volume"] for liquid in phase_liquids)

            for liquid in phase_liquids:
                liquid_ratio = phase_mass / liquid["volume"] if liquid["volume"] > 0 else 0
                sl_results.append({
                    "Phase": phase_name,
                    "Liquid Type": liquid["type"],
                    "Phase Mass (kg)": phase_mass,
                    "Liquid Volume (L)": liquid["volume"],
                    "S/L Ratio": liquid_ratio
                })

            overall_ratio = phase_mass / total_liquid_volume if total_liquid_volume > 0 else 0
            sl_results.append({
                "Phase": phase_name,
                "Liquid Type": "Overall",
                "Phase Mass (kg)": phase_mass,
                "Liquid Volume (L)": total_liquid_volume,
                "S/L Ratio": overall_ratio
            })

        sl_df = pd.DataFrame(sl_results)
        st.table(sl_df)

    # Save the current technical KPIs into session state
    st.session_state["technical_kpis"] = {
        "composition": st.session_state.get("composition", {}),
        "phases": st.session_state.get("phases", {}),
        "solid_liquid_ratios": sl_df.to_dict("records")
    }

    # Scenario Management
    st.sidebar.title("Scenario Management")
    if st.sidebar.button("Save Current Scenario"):
        save_current_scenario()
    if st.sidebar.button("Load Existing Scenario"):
        load_scenario()

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page:", ["Economic KPIs", "Technical KPIs"])

if page == "Economic KPIs":
    economic_kpis()
elif page == "Technical KPIs":
    technical_kpis()
