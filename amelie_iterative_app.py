import matplotlib
matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io
import sqlite3
import json

# Initialize Streamlit page
st.set_page_config(
    page_title="Amelie KPI Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page:", ["Economic KPIs", "Technical KPIs", "Scenario Management"])

# Database setup
def init_db():
    conn = sqlite3.connect("scenarios.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scenarios (
                    username TEXT,
                    scenario_name TEXT,
                    data TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# Functions to save and load scenarios
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

# Save current scenario
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

# Load scenario
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

# Economic Model Class
class AmelieEconomicModel:
    def __init__(self):
        self.capex = {
            'Leaching Reactor': 20000,
            'Press Filter': 15000,
            'Precipitation Reactor': 18000,
            'Solvent Extraction Unit': 30000,
            'Microwave Thermal Treatment Unit': 25000,
            'Pre-treatment Dryer': 15000,
            'Secondary Dryer': 12000,
            'Wastewater Treatment Unit': 18000
        }
        self.opex = {
            'Reagents': 90,
            'Energy': 44,
            'Labor': 80,
            'Maintenance': 20,
            'Disposal': 12.5
        }
        self.energy_consumption = {
            'Leaching Reactor': 5,
            'Press Filter': 3,
            'Precipitation Reactor': 4,
            'Solvent Extraction Unit': 6,
            'Microwave Thermal Treatment': 2.5
        }
        self.energy_cost = 0.12  # EUR per kWh
        self.black_mass = 10

    def calculate_totals(self):
        capex_total = sum(self.capex.values())
        opex_total = sum(self.opex.values()) + self.calculate_total_energy_cost()
        return capex_total, opex_total

    def calculate_total_energy_cost(self):
        total_kWh = sum(self.energy_consumption.values())
        return total_kWh * self.energy_cost

model = AmelieEconomicModel()

# Economic KPIs Page
def economic_kpis():
    st.title("Economic KPIs")

    st.subheader("General Assumptions")
    if "general_assumptions" not in st.session_state:
        st.session_state.general_assumptions = [
            "Pilot project sized for 10 kg BM per batch.",
            "No infrastructure costs.",
            "Energy cost calculated dynamically based on kWh per machine."
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

    st.subheader("Results")
    capex_total, opex_total = model.calculate_totals()
    st.write(f"**Total CapEx:** {capex_total} EUR")
    st.write(f"**Total OpEx (including energy):** {opex_total} EUR/batch")

# Technical KPIs Page
def technical_kpis():
    st.title("Technical KPIs")

    st.subheader("Material Composition")
    if "composition" not in st.session_state:
        st.session_state.composition = {'Li': 7.0, 'Co': 15.0, 'Ni': 10.0, 'Mn': 8.0}

    updated_composition = {}
    for material, percentage in st.session_state.composition.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            updated_name = st.text_input(f"{material} Name:", value=material)
        with col2:
            updated_percentage = st.number_input(f"{material} %:", value=percentage, min_value=0.0, max_value=100.0)
        updated_composition[updated_name] = updated_percentage
    st.session_state.composition = updated_composition

    st.subheader("Efficiency Results")
    total_black_mass = st.number_input("Total Black Mass (kg):", value=10.0, min_value=0.1)
    st.write("Efficiency calculations based on black mass and recovered materials.")

# Scenario Management Page
if page == "Scenario Management":
    st.title("Scenario Management")
    save_current_scenario()
    load_scenario()

elif page == "Economic KPIs":
    economic_kpis()

elif page == "Technical KPIs":
    technical_kpis()
