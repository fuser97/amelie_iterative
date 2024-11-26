import matplotlib

matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io

import json
import os
import numpy as np


# Path to the JSON file
data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

case_studies_file = os.path.join(data_dir, "case_studies.json")

# Load case studies into session state on app start
if "case_studies" not in st.session_state:
    if os.path.exists(case_studies_file):
        with open(case_studies_file, "r") as file:
            try:
                loaded_data = json.load(file)
                # Verifica che ogni case study sia un dizionario
                if isinstance(loaded_data, dict):
                    for case_study_name, case_study in loaded_data.items():
                        # Assicura che il valore sia un dizionario
                        if not isinstance(case_study, dict):
                            # Sostituisci con una struttura vuota valida
                            loaded_data[case_study_name] = {
                                "assumptions": [],
                                "capex": {},
                                "opex": {},
                                "energy_cost": 0.12,
                                "energy_consumption": {}
                            }
                        else:
                            # Aggiungi chiavi mancanti con valori di default
                            case_study.setdefault("assumptions", [])
                            case_study.setdefault("capex", {})
                            case_study.setdefault("opex", {})
                            case_study.setdefault("energy_cost", 0.12)
                            case_study.setdefault("energy_consumption", {})
                    st.session_state.case_studies = loaded_data
                else:
                    # Se i dati non sono un dizionario, inizializza vuoto
                    st.session_state.case_studies = {}
            except json.JSONDecodeError:
                st.warning("Case studies file is invalid. Starting with an empty state.")
                st.session_state.case_studies = {}
    else:
        st.session_state.case_studies = {}



class AmelieEconomicModel:
    def __init__(self):
        self.capex = get_default_capex()  # Usa la funzione per i valori di default
        self.opex = get_default_opex()    # Usa la funzione per i valori di default
        self.energy_consumption = {
            "Leaching Reactor": 5,
            "Press Filter": 3,
            "Precipitation Reactor": 4,
            "Solvent Extraction Unit": 6,
            "Microwave Thermal Treatment": 2.5
        }
        self.energy_cost = st.session_state.get("amelie_energy_cost", 0.12)  # Default 0.12 EUR per kWh
        self.black_mass = 10


    def calculate_totals(self):
        capex_total = sum(self.capex.values())
        opex_total = sum(self.opex.values()) + self.calculate_total_energy_cost()
        return capex_total, opex_total

    def calculate_total_energy_cost(self):
        total_kWh = sum(self.energy_consumption.values())
        return total_kWh * self.energy_cost

    def generate_pie_chart(self, data, title):
        fig, ax = plt.subplots(figsize=(12, 10))
        explode = [0.1 if key in ["Reagents", "Energy", "Labor"] else 0 for key in data.keys()]
        wedges, texts, autotexts = ax.pie(
            data.values(),
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode
        )
        ax.set_title(title, fontsize=16)
        ax.legend(
            loc="upper left",
            labels=[f"{key} ({value} EUR)" for key, value in data.items()],
            fontsize=12,
            bbox_to_anchor=(1, 0.5),
            frameon=False
        )
        for text in autotexts:
            text.set_fontsize(14)
            text.set_color('black')

        buf = io.BytesIO()
        try:
            plt.savefig(buf, format='png', bbox_inches="tight")
        except ValueError as e:
            plt.close(fig)
            raise ValueError(f"Error generating pie chart: {e}")
        finally:
            plt.close(fig)

        buf.seek(0)
        return buf

    def generate_table(self, data):
        df = pd.DataFrame(list(data.items()), columns=['Category', 'Cost (EUR)'])
        total = df['Cost (EUR)'].sum()
        df.loc[len(df)] = ['Total', total]
        return df

def get_default_capex():
    return {
        'Leaching Reactor': 20000,
        'Press Filter': 15000,
        'Precipitation Reactor': 18000,
        'Solvent Extraction Unit': 30000,
        'Microwave Thermal Treatment Unit': 25000,
        'Pre-treatment Dryer': 15000,
        'Secondary Dryer': 12000,
        'Wastewater Treatment Unit': 18000
    }

def get_default_opex():
    return {
        'Reagents': 90,
        'Labor': 80,
        'Maintenance': 20,
        'Disposal': 12.5,
        'Malic Acid': 8.0,
        'Hydrogen Peroxide': 4.0,
        'Lithium Precipitation Reagents': 5.0,
        'Co/Ni/Mn Precipitation Reagents': 7.0,
        'Wastewater Treatment Chemicals': 6.0
    }

def get_default_scenario():
    return {
        "capex": get_default_capex(),
        "opex": get_default_opex(),
        "energy_cost": 0.12,
        "energy_consumption": {
            "Leaching Reactor": 5,
            "Press Filter": 3,
            "Precipitation Reactor": 4,
            "Solvent Extraction Unit": 6,
            "Microwave Thermal Treatment": 2.5
        },
        "assumptions": [
            "Batch Size (10 kg)",
            "1 Operator per Batch",
            "Process Includes: Pre-treatment, microwave thermal treatment, leaching in water, precipitation, secondary drying, leaching in acid, and wastewater treatment"
        ],
        "technical_kpis": {
            "composition": {
                "Li": 7.0,  # Default percentages
                "Co": 15.0,
                "Ni": 10.0,
                "Mn": 8.0
            },
            "recovered_masses": {},
            "efficiency": 0.0,
            "phases": {}
        }
    }



# Initialize Model
model = AmelieEconomicModel()

amelie_scenarios_file = os.path.join(data_dir, "amelie_scenarios.json")

# Inizializzazione di st.session_state.amelie_scenarios se non esiste
if "amelie_scenarios" not in st.session_state:
    # Usa il file di configurazione o crea un valore di default
    amelie_scenarios_file = os.path.join(data_dir, "amelie_scenarios.json")
    if os.path.exists(amelie_scenarios_file):
        with open(amelie_scenarios_file, "r") as file:
            try:
                # Carica gli scenari da file
                st.session_state.amelie_scenarios = json.load(file)
                # Assicura che ogni scenario abbia i valori di default
                for scenario_name, scenario_data in st.session_state.amelie_scenarios.items():
                    default_scenario = get_default_scenario()
                    for key, default_value in default_scenario.items():
                        if key not in scenario_data:
                            scenario_data[key] = default_value
            except json.JSONDecodeError:
                # Se il file è corrotto, usa il default
                st.warning("File 'amelie_scenarios.json' non valido. Uso del valore di default.")
                st.session_state.amelie_scenarios = {"default": get_default_scenario()}
    else:
        # Nessun file trovato, inizializza con il default
        st.session_state.amelie_scenarios = {"default": get_default_scenario()}





def save_amelie_config():
    try:
        with open("amelie_config.json", "w") as file:
            json.dump({"amelie_energy_cost": st.session_state.amelie_energy_cost}, file)
        st.success("Amelie energy cost saved successfully.")
    except Exception as e:
        st.error(f"Failed to save Amelie config: {e}")


# Configure the page layout
st.set_page_config(
    page_title="Amelie KPI Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.sidebar.title("Amelie Scenarios")
scenario_names = list(st.session_state.amelie_scenarios.keys())

selected_scenario = st.sidebar.selectbox("Select Amelie Scenario:", scenario_names + ["Create New Scenario"])

if selected_scenario == "Create New Scenario":
    new_scenario_name = st.sidebar.text_input("New Scenario Name:")
    if st.sidebar.button("Create Scenario"):
        if new_scenario_name and new_scenario_name not in st.session_state.amelie_scenarios:
            st.session_state.amelie_scenarios[new_scenario_name] = get_default_scenario()
            st.success(f"Scenario '{new_scenario_name}' created.")
            selected_scenario = new_scenario_name
        else:
            st.error("Invalid or duplicate scenario name!")


# Pulsante per resettare la sessione
if st.sidebar.button("Reset Session"):
    st.session_state.clear()
    st.success("Session reset successfully. Reload the page.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page:", ["Economic KPIs", "Technical KPIs", "Literature", "Benchmarking"])

# Initialize session state for case studies
if "case_studies" not in st.session_state:
    st.session_state.case_studies = {}

# Initialize session state for case studies
if "case_studies" not in st.session_state:
    st.session_state.case_studies = {}

# Carica il valore di amelie_energy_cost se il file esiste
if os.path.exists("amelie_config.json"):
    with open("amelie_config.json", "r") as file:
        try:
            config_data = json.load(file)
            st.session_state.amelie_energy_cost = config_data.get("amelie_energy_cost", 0.12)
        except json.JSONDecodeError:
            st.session_state.amelie_energy_cost = 0.12  # Valore predefinito in caso di errore

# Inizializza il valore se non è stato caricato
if "amelie_energy_cost" not in st.session_state:
    st.session_state.amelie_energy_cost = 0.12  # Valore predefinito

# Streamlit App
st.title("Amelie Economic Model Configurator")


def economic_kpis():
    st.title("Economic KPIs")

    # Verifica se il selected_scenario è valido
    if selected_scenario == "Create New Scenario":
        st.warning("Please create a new scenario before proceeding.")
        return  # Ferma l'esecuzione della funzione

    # Recupera lo scenario selezionato o usa il default
    if selected_scenario not in st.session_state.amelie_scenarios:
        st.session_state.amelie_scenarios[selected_scenario] = get_default_scenario()

    # Recupera i dati dello scenario corrente
    current_scenario = st.session_state.amelie_scenarios[selected_scenario]

    # Assicurati che lo scenario abbia tutti i valori di default
    default_scenario = get_default_scenario()
    for key, default_value in default_scenario.items():
        if key not in current_scenario:
            current_scenario[key] = default_value

    # Inizializza le chiavi nello stato di sessione se non esistono
    if "capex_data" not in st.session_state:
        st.session_state.capex_data = get_default_capex()
    if "opex_data" not in st.session_state:
        st.session_state.opex_data = get_default_opex()

    if "energy_data" not in st.session_state:
        st.session_state.energy_data = {}
    if "assumptions" not in st.session_state:
        st.session_state.assumptions = [
            "Batch Size (10 kg)",
            "1 Operator per Batch",
            "Process Includes: Pre-treatment, microwave thermal treatment, leaching in water, precipitation, secondary drying, leaching in acid, and wastewater treatment"
        ]
    if "energy_cost" not in st.session_state:
        st.session_state.energy_cost = 0.12  # Valore di default

    # Aggiorna i dati del modello con lo scenario corrente
    model.capex = current_scenario["capex"]
    model.opex = current_scenario["opex"]
    model.energy_cost = current_scenario["energy_cost"]
    model.energy_consumption = current_scenario["energy_consumption"]

    # Add a section dropdown
    sections = ["General Assumptions", "CapEx Configuration", "OpEx Configuration", "Results"]
    selected_section = st.selectbox("Jump to Section:", sections)

    # General Assumptions Section
    if selected_section == "General Assumptions":
        st.subheader("General Assumptions")
        if "assumptions" not in st.session_state:
            st.session_state.assumptions = [
                "Batch Size (10 kg)",
                "1 Operator per Batch",
                "Process Includes: Pre-treatment, microwave thermal treatment, leaching in water, precipitation, secondary drying, leaching in acid, and wastewater treatment"
            ]

        # Display assumptions
        assumptions_to_delete = []
        for idx, assumption in enumerate(st.session_state.assumptions):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_input(f"Edit Assumption {idx + 1}:", value=assumption, key=f"assumption_{idx}")
            with col2:
                if st.button("Remove", key=f"remove_assumption_{idx}"):
                    assumptions_to_delete.append(idx)

        for idx in sorted(assumptions_to_delete, reverse=True):
            st.session_state.assumptions.pop(idx)

        # Add new assumption
        new_assumption = st.text_input("New Assumption:", key="new_assumption")
        if st.button("Add Assumption", key="add_assumption"):
            if new_assumption:
                st.session_state.assumptions.append(new_assumption)
                st.success(f"Added new assumption: {new_assumption}")
            else:
                st.error("Assumption cannot be empty!")

        st.markdown("### Current Assumptions")
        for idx, assumption in enumerate(st.session_state.assumptions, 1):
            st.write(f"{idx}. {assumption}")

    elif selected_section == "CapEx Configuration":
        st.subheader("CapEx Configuration")
        # Verifica che "capex" esista nello scenario corrente
        if "capex" not in current_scenario:
            current_scenario["capex"] = {}

        capex_to_delete = []
        for key, value in current_scenario["capex"].items():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(f"Edit CapEx Name ({key}):", value=key,
                                         key=f"capex_name_{selected_scenario}_{key}")
            with col2:
                new_cost = st.number_input(
                    f"CapEx Cost ({key}):", value=float(value), min_value=0.0,
                    key=f"capex_cost_{selected_scenario}_{key}"
                )
            with col3:
                if st.button(f"Remove CapEx ({key})", key=f"remove_capex_{selected_scenario}_{key}"):
                    capex_to_delete.append(key)

            # Se il nome o il costo sono cambiati, aggiorna
            if new_name != key:
                current_scenario["capex"][new_name] = current_scenario["capex"].pop(key)
            current_scenario["capex"][new_name] = new_cost

        # Rimuovi i CapEx eliminati
        for item in capex_to_delete:
            del current_scenario["capex"][item]

        # Salva lo scenario
        st.session_state.amelie_scenarios[selected_scenario] = current_scenario
        save_amelie_scenarios()

        # Grafici e tabelle aggiornati
        st.subheader("Updated CapEx Breakdown")
        capex_chart = model.generate_pie_chart(current_scenario["capex"], "CapEx Breakdown")
        st.image(capex_chart, caption="CapEx Breakdown", use_container_width=True)

        capex_table = model.generate_table(current_scenario["capex"])
        st.table(capex_table)

        # Aggiungi nuovi elementi
        new_name = st.text_input("New CapEx Name:", key="new_capex_name")
        new_cost = st.number_input("New CapEx Cost (EUR):", min_value=0.0, key="new_capex_cost")
        if st.button("Add CapEx"):
            if new_name and new_name not in current_scenario["capex"]:
                current_scenario["capex"][new_name] = new_cost
                st.success(f"Added new CapEx item: {new_name}")
            else:
                st.error("CapEx item already exists or name is invalid!")

            # Salva lo scenario e aggiorna
            st.session_state.amelie_scenarios[selected_scenario] = current_scenario
            save_amelie_scenarios()

            # Rigenera i grafici e le tabelle
            capex_chart = model.generate_pie_chart(current_scenario["capex"], "CapEx Breakdown")
            st.image(capex_chart, caption="CapEx Breakdown", use_container_width=True)

            capex_table = model.generate_table(current_scenario["capex"])
            st.table(capex_table)





    elif selected_section == "OpEx Configuration":

        st.subheader("OpEx Configuration")

        # Recupera l'OpEx dallo scenario corrente o usa i valori di default

        current_opex = current_scenario.get("opex", {})

        if "energy_consumption" not in current_scenario:
            current_scenario["energy_consumption"] = model.energy_consumption.copy()

        # --- Configurazione Energia ---

        st.markdown("### Energy Configuration")

        energy_cost = st.number_input(

            "Energy Cost (EUR/kWh):",

            value=float(current_scenario.get("energy_cost", 0.12)),  # Forza a float

            min_value=0.0,

            key=f"energy_cost_{selected_scenario}"

        )

        current_scenario["energy_cost"] = energy_cost

        # Modifica delle apparecchiature di consumo energetico

        energy_to_delete = []

        for machine, consumption in current_scenario["energy_consumption"].items():

            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:

                new_machine = st.text_input(

                    f"Machine Name ({machine}):",

                    value=machine,

                    key=f"machine_name_{selected_scenario}_{machine}"

                )

            with col2:

                new_consumption = st.number_input(

                    f"Consumption (kWh) for {machine}:",

                    value=float(consumption),  # Forza a float

                    min_value=0.0,

                    key=f"machine_consumption_{selected_scenario}_{machine}"

                )

            with col3:

                if st.button(f"Remove {machine}", key=f"remove_machine_{selected_scenario}_{machine}"):
                    energy_to_delete.append(machine)

            # Aggiorna il dizionario se il nome è stato modificato

            if new_machine != machine:
                current_scenario["energy_consumption"][new_machine] = current_scenario["energy_consumption"].pop(
                    machine)

            current_scenario["energy_consumption"][new_machine] = new_consumption

        # Rimuovi le apparecchiature eliminate

        for machine in energy_to_delete:
            del current_scenario["energy_consumption"][machine]

        # Aggiungi una nuova apparecchiatura

        new_machine_name = st.text_input("New Machine Name:", key=f"new_machine_name_{selected_scenario}")

        new_machine_consumption = st.number_input(

            "New Machine Consumption (kWh):",

            min_value=0.0,

            key=f"new_machine_consumption_{selected_scenario}"

        )

        if st.button("Add Machine", key=f"add_machine_{selected_scenario}"):

            if new_machine_name and new_machine_name not in current_scenario["energy_consumption"]:

                current_scenario["energy_consumption"][new_machine_name] = float(new_machine_consumption)

                st.success(f"Added new machine: {new_machine_name}")

            else:

                st.error("Invalid or duplicate machine name!")

        # Calcola il costo totale dell'energia

        total_energy_consumption = sum(current_scenario["energy_consumption"].values())

        total_energy_cost = total_energy_consumption * energy_cost

        current_opex["Energy"] = total_energy_cost

        st.markdown(f"**Total Energy Cost:** {total_energy_cost:.2f} EUR")

        # --- Configurazione OpEx Generale ---

        st.markdown("### General OpEx Configuration")

        opex_to_delete = []

        for key, value in current_opex.items():

            if key != "Energy":  # Non permettere modifiche dirette al costo energia

                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:

                    new_name = st.text_input(

                        f"OpEx Name ({key}):",

                        value=key,

                        key=f"opex_name_{selected_scenario}_{key}"

                    )

                with col2:

                    new_cost = st.number_input(

                        f"OpEx Cost (EUR) for {key}:",

                        value=float(value),  # Forza a float

                        min_value=0.0,

                        key=f"opex_cost_{selected_scenario}_{key}"

                    )

                with col3:

                    if st.button(f"Remove {key}", key=f"remove_opex_{selected_scenario}_{key}"):
                        opex_to_delete.append(key)

                # Aggiorna il dizionario se il nome è stato modificato

                if new_name != key:
                    current_opex[new_name] = current_opex.pop(key)

                current_opex[new_name] = new_cost

        # Rimuovi gli elementi OpEx eliminati

        for item in opex_to_delete:
            del current_opex[item]

        # Aggiungi un nuovo elemento OpEx

        new_opex_name = st.text_input("New OpEx Name:", key=f"new_opex_name_{selected_scenario}")

        new_opex_cost = st.number_input(

            "New OpEx Cost (EUR):",

            min_value=0.0,

            key=f"new_opex_cost_{selected_scenario}"

        )

        if st.button("Add OpEx", key=f"add_opex_{selected_scenario}"):

            if new_opex_name and new_opex_name not in current_opex:

                current_opex[new_opex_name] = float(new_opex_cost)  # Forza a float

                st.success(f"Added new OpEx item: {new_opex_name}")

            else:

                st.error("Invalid or duplicate OpEx name!")

        # Salva le modifiche nello scenario

        current_scenario["opex"] = current_opex

        st.session_state.amelie_scenarios[selected_scenario] = current_scenario

        save_amelie_scenarios()

        # --- Visualizza grafico e tabella OpEx ---

        opex_chart = model.generate_pie_chart(current_opex, "OpEx Breakdown")

        st.image(opex_chart, caption="OpEx Breakdown", use_column_width=True)

        opex_table = model.generate_table(current_opex)

        st.table(opex_table)







    # Results Section
    elif selected_section == "Results":
        st.subheader("Results")
        capex_total, opex_total = model.calculate_totals()
        st.write(f"**Total CapEx:** {capex_total} EUR")
        st.write(f"**Total OpEx (including energy):** {opex_total} EUR")

        capex_chart = model.generate_pie_chart(current_scenario["capex"], "CapEx Breakdown")
        st.image(capex_chart, caption="CapEx Breakdown", use_container_width=True)

        capex_table = model.generate_table(current_scenario["capex"])
        st.table(capex_table)

        opex_chart = model.generate_pie_chart(current_scenario["opex"], "OpEx Breakdown")
        st.image(opex_chart, caption="OpEx Breakdown", use_container_width=True)

        opex_table = model.generate_table(current_scenario["opex"])
        st.table(opex_table)


import pandas as pd
import streamlit as st


def technical_kpis():
    st.title("Technical KPIs")

    # Dropdown per selezionare la sezione
    sections = ["Material Composition & Efficiency", "Solid/Liquid Ratios"]
    selected_section = st.selectbox("Select Section:", sections)

    # Recupera lo scenario selezionato
    if selected_scenario not in st.session_state.amelie_scenarios:
        st.session_state.amelie_scenarios[selected_scenario] = get_default_scenario()

    # Ottieni i dati dello scenario corrente
    current_scenario = st.session_state.amelie_scenarios[selected_scenario]

    # Inizializza la struttura per i Technical KPIs se non esiste
    if "technical_kpis" not in current_scenario:
        current_scenario["technical_kpis"] = {
            "composition": {
                "Li": 7.0,  # Default percentages
                "Co": 15.0,
                "Ni": 10.0,
                "Mn": 8.0
            },
            "recovered_masses": {},
            "efficiency": 0.0,
            "phases": {}  # Per la sezione Solid/Liquid Ratios
        }

    # Verifica e imposta valori di default per la composizione
    if not current_scenario["technical_kpis"].get("composition"):
        current_scenario["technical_kpis"]["composition"] = {
            "Li": 7.0,
            "Co": 15.0,
            "Ni": 10.0,
            "Mn": 8.0
        }

    # Resto del codice della funzione...


    # Sezione "Material Composition & Efficiency"
    if selected_section == "Material Composition & Efficiency":
        st.subheader("Material Composition & Efficiency")
        composition = current_scenario["technical_kpis"].get("composition", {})
        recovered_masses = current_scenario["technical_kpis"].get("recovered_masses", {})

        total_percentage = 0
        updated_composition = {}

        for material, percentage in list(composition.items()):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                new_material = st.text_input(
                    f"Material ({material}):", value=material,
                    key=f"edit_material_{selected_scenario}_{material}"
                )
            with col2:
                new_percentage = st.number_input(
                    f"Percentage of {material} in BM (%)", min_value=0.0, max_value=100.0,
                    value=percentage, key=f"edit_percentage_{selected_scenario}_{material}"
                )
            with col3:
                recovered_mass = st.number_input(
                    f"Recovered Mass of {material} (kg):",
                    min_value=0.0, value=recovered_masses.get(material, 0.0),
                    key=f"recovered_mass_{selected_scenario}_{material}"
                )
                recovered_masses[material] = recovered_mass
            with col4:
                if st.button(f"Remove {material}", key=f"remove_material_{selected_scenario}_{material}"):
                    continue

            updated_composition[new_material] = new_percentage
            total_percentage += new_percentage

        # Aggiungi nuovo materiale
        new_material_name = st.text_input("New Material Name:", key=f"new_material_name_{selected_scenario}")
        new_material_percentage = st.number_input(
            "New Material Percentage (%):", min_value=0.0, max_value=100.0,
            key=f"new_material_percentage_{selected_scenario}"
        )
        new_recovered_mass = st.number_input(
            "New Material Recovered Mass (kg):", min_value=0.0,
            key=f"new_material_recovered_mass_{selected_scenario}"
        )
        if st.button("Add Material", key=f"add_material_{selected_scenario}"):
            if new_material_name and new_material_name not in updated_composition:
                updated_composition[new_material_name] = new_material_percentage
                recovered_masses[new_material_name] = new_recovered_mass
                st.success(f"Added new material: {new_material_name}")
            else:
                st.error(f"Material {new_material_name} already exists!")

        # Verifica totale percentuale
        if total_percentage > 100:
            st.warning(f"Total material composition exceeds 100% ({total_percentage:.2f}%). Adjust values.")
        elif total_percentage < 100:
            st.info(f"Total material composition is below 100% ({total_percentage:.2f}%).")

        # Calcolo Efficienza complessiva
        total_black_mass = st.number_input(
            "Total Black Mass (kg):", min_value=0.1, value=10.0,
            key=f"total_black_mass_{selected_scenario}"
        )
        efficiencies = {}
        total_recovered_mass = 0.0

        for material, percentage in updated_composition.items():
            initial_mass = total_black_mass * (percentage / 100)
            recovered_mass = recovered_masses.get(material, 0.0)
            efficiency = (recovered_mass / initial_mass) * 100 if initial_mass > 0 else 0.0
            efficiencies[material] = efficiency
            total_recovered_mass += recovered_mass

        overall_efficiency = (total_recovered_mass / total_black_mass) * 100

        # Mostra i risultati in una tabella
        st.write(f"**Overall Process Efficiency:** {overall_efficiency:.2f}%")
        result_df = pd.DataFrame({
            "Material": list(updated_composition.keys()),
            "Initial Mass in BM (kg)": [total_black_mass * (p / 100) for p in updated_composition.values()],
            "Recovered Mass (kg)": [recovered_masses.get(m, 0.0) for m in updated_composition.keys()],
            "Efficiency (%)": [efficiencies.get(m, 0.0) for m in updated_composition.keys()]
        })
        st.table(result_df)

        # Salva i dati aggiornati nello scenario corrente
        current_scenario["technical_kpis"]["composition"] = updated_composition
        current_scenario["technical_kpis"]["recovered_masses"] = recovered_masses
        current_scenario["technical_kpis"]["efficiency"] = overall_efficiency

        # Aggiorna lo stato della sessione
        st.session_state.amelie_scenarios[selected_scenario] = current_scenario

        # Persisti i dati su disco
        save_amelie_scenarios()
        st.success("Material and Efficiency data saved successfully!")

    # Solid/Liquid Ratios Section
    elif selected_section == "Solid/Liquid Ratios":
        st.subheader("Solid/Liquid Ratios for Each Phase")

        if "phases" not in st.session_state:
            st.session_state.phases = {
                "Leaching in Water": {"liquids": [{"type": "Water", "volume": 20.0}], "mass": 5.0},
                "Leaching in Acid": {
                    "liquids": [{"type": "Malic Acid", "volume": 5.0}, {"type": "Water", "volume": 2.0}], "mass": 5.0}
            }

        phases = st.session_state.phases
        updated_phases = {}

        for phase_name, phase_data in phases.items():
            st.subheader(f"Phase: {phase_name}")
            liquids = phase_data.get("liquids", [])
            updated_liquids = []

            phase_mass = st.number_input(
                f"Mass for {phase_name} (kg):", min_value=0.0, value=phase_data.get("mass", 0.0), step=0.1,
                key=f"mass_{phase_name}"
            )

            for idx, liquid in enumerate(liquids):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    liquid_type = st.text_input(
                        f"Liquid Type ({liquid['type']}):", value=liquid["type"], key=f"liquid_type_{phase_name}_{idx}"
                    )
                with col2:
                    liquid_volume = st.number_input(
                        f"Volume ({liquid['type']}, L):", min_value=0.0, value=liquid["volume"], step=0.1,
                        key=f"volume_{phase_name}_{idx}"
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

        # Salva i dati aggiornati nello scenario corrente
        current_scenario["technical_kpis"]["phases"] = st.session_state.phases

        # Aggiorna lo stato della sessione
        st.session_state.amelie_scenarios[selected_scenario] = current_scenario

        # Salva su disco
        save_amelie_scenarios()
        st.success("Solid/Liquid Ratios saved successfully!")


def save_case_studies():
    try:
        for case_study_name, case_study in st.session_state.case_studies.items():
            if not isinstance(case_study, dict):
                st.session_state.case_studies[case_study_name] = {
                    "assumptions": [],
                    "capex": {},
                    "opex": {},
                    "energy_cost": 0.12,
                    "energy_consumption": {},
                    "technical_kpis": {}  # Aggiunta dei KPI tecnici
                }
            else:
                case_study.setdefault("assumptions", [])
                case_study.setdefault("capex", {})
                case_study.setdefault("opex", {})
                case_study.setdefault("energy_cost", 0.12)
                case_study.setdefault("energy_consumption", {})
                case_study.setdefault("technical_kpis", {})  # Aggiunta dei KPI tecnici

        with open(case_studies_file, "w") as file:
            json.dump(st.session_state.case_studies, file, indent=4)
        st.info(f"Case studies saved to {case_studies_file}")
    except Exception as e:
        st.error(f"Failed to save case studies: {e}")



def save_amelie_scenarios():
    try:
        with open(amelie_scenarios_file, "w") as file:
            json.dump(st.session_state.amelie_scenarios, file, indent=4)
        st.success("Amelie scenarios saved successfully.")
    except Exception as e:
        st.error(f"Failed to save Amelie scenarios: {e}")



def literature():
    st.title("Literature: Case Studies")

    # Add, remove, or edit case studies
    # Path to the JSON file
    case_studies_file = "case_studies.json"



    case_study_names = list(st.session_state.case_studies.keys())

    col1, col2 = st.columns([4, 1])
    with col1:
        selected_case_study = st.selectbox("Select or Add a Case Study:", case_study_names + ["Add New Case Study"],
                                           key="selected_case_study")
    with col2:
        if selected_case_study != "Add New Case Study" and st.button("Remove Case Study", key="remove_case_study"):
            del st.session_state.case_studies[selected_case_study]
            save_case_studies()
            st.success(f"Case Study '{selected_case_study}' removed.")
            return

    if selected_case_study == "Add New Case Study":
        new_case_study_name = st.text_input("New Case Study Name:")
        if st.button("Create Case Study"):
            if new_case_study_name and new_case_study_name not in st.session_state.case_studies:
                st.session_state.case_studies[new_case_study_name] = {
                    "assumptions": [],
                    "capex": {},
                    "opex": {},
                    "energy_cost": 0.0,
                    "energy_consumption": {}
                }
                save_case_studies()
                st.success(f"Case Study '{new_case_study_name}' created.")

            else:
                st.error("Invalid or duplicate case study name!")
        return

    st.markdown("### Case Studies")

    for case_study_name in st.session_state.case_studies.keys():
        with st.expander(f"Case Study: {case_study_name}", expanded=False):
            case_study = st.session_state.case_studies[case_study_name]

            # Ensure all keys are present
            if "assumptions" not in case_study:
                case_study["assumptions"] = []
            if "capex" not in case_study:
                case_study["capex"] = {}
            if "opex" not in case_study:
                case_study["opex"] = {}
            if "energy_cost" not in case_study:
                case_study["energy_cost"] = 0.12  # Default value

            # Assumptions Section
            st.markdown("#### Assumptions")
            assumptions_to_delete = []
            for idx, assumption in enumerate(case_study["assumptions"]):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text_input(f"Edit Assumption {idx + 1}:", value=assumption,
                                  key=f"assumption_{case_study_name}_{idx}")
                with col2:
                    if st.button("Remove", key=f"remove_assumption_{case_study_name}_{idx}"):
                        assumptions_to_delete.append(idx)

            for idx in sorted(assumptions_to_delete, reverse=True):
                case_study["assumptions"].pop(idx)

            new_assumption = st.text_input(f"New Assumption for {case_study_name}:",
                                           key=f"new_assumption_{case_study_name}")
            if st.button(f"Add Assumption", key=f"add_assumption_{case_study_name}"):
                if new_assumption:
                    case_study["assumptions"].append(new_assumption)
                    save_case_studies()  # Salva le modifiche
                    st.success("New assumption added!")
                else:
                    st.error("Assumption cannot be empty!")

            # CapEx Section
            st.markdown("#### CapEx")
            capex_to_delete = []
            for key, value in case_study["capex"].items():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    new_name = st.text_input(f"CapEx Name ({key}):", value=key,
                                             key=f"capex_name_{case_study_name}_{key}")
                with col2:
                    new_cost = st.number_input(
                        f"CapEx Cost ({key}):",
                        value=float(value),  # Converti sempre in float
                        min_value=0.0,
                        key=f"capex_cost_{selected_scenario}_{key}"
                    )

                with col3:
                    if st.button(f"Remove CapEx ({key})", key=f"remove_capex_{case_study_name}_{key}"):
                        capex_to_delete.append(key)
                if new_name != key:
                    case_study["capex"][new_name] = case_study["capex"].pop(key)
                case_study["capex"][new_name] = new_cost

            for item in capex_to_delete:
                del case_study["capex"][item]

            new_capex_name = st.text_input(f"New CapEx Name for {case_study_name}:",
                                           key=f"new_capex_name_{case_study_name}")
            new_capex_cost = st.number_input(f"New CapEx Cost for {case_study_name}:", min_value=0.0,
                                             key=f"new_capex_cost_{case_study_name}")
            if st.button(f"Add CapEx for {case_study_name}"):
                if new_capex_name and new_capex_name not in case_study["capex"]:
                    case_study["capex"][new_capex_name] = new_capex_cost
                    save_case_studies()  # Salva le modifiche
                    st.success("New CapEx item added!")
                else:
                    st.error("CapEx item already exists or name is invalid!")

            # OpEx Section
            st.markdown("#### OpEx")
            opex_to_delete = []
            for key, value in case_study["opex"].items():
                if key != "Energy":  # Escludi il costo dell'energia dai campi modificabili
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        new_name = st.text_input(f"OpEx Name ({key}):", value=key,
                                                 key=f"opex_name_{case_study_name}_{key}")
                    with col2:
                        new_cost = st.number_input(f"OpEx Cost ({key}):", value=float(value), min_value=0.0,
                                                   key=f"opex_cost_{case_study_name}_{key}")
                    with col3:
                        if st.button(f"Remove OpEx ({key})", key=f"remove_opex_{case_study_name}_{key}"):
                            opex_to_delete.append(key)
                    if new_name != key:
                        case_study["opex"][new_name] = case_study["opex"].pop(key)
                    case_study["opex"][new_name] = new_cost

            for item in opex_to_delete:
                del case_study["opex"][item]

            new_opex_name = st.text_input(f"New OpEx Name for {case_study_name}:",
                                          key=f"new_opex_name_{case_study_name}")
            new_opex_cost = st.number_input(f"New OpEx Cost for {case_study_name}:", min_value=0.0,
                                            key=f"new_opex_cost_{case_study_name}")
            if st.button(f"Add OpEx for {case_study_name}"):
                if new_opex_name and new_opex_name not in case_study["opex"]:
                    case_study["opex"][new_opex_name] = new_opex_cost
                    save_case_studies()  # Salva le modifiche
                    st.success("New OpEx item added!")
                else:
                    st.error("OpEx item already exists or name is invalid!")

            # Generate Pie Charts and Tables
            st.markdown("#### Visualization")
            if case_study["capex"]:
                capex_data = {k: v for k, v in case_study["capex"].items() if v > 0}
            else:
                # Usa il valore diretto di CapEx se specificato
                direct_capex = case_study.get("capex_total", 0.0)
                capex_data = {"Total CapEx (Direct)": float(direct_capex) if direct_capex > 0 else 1.0}

            # Ensure capex_data is not empty
            if not capex_data:
                capex_data = {"Placeholder": 1.0}

            st.markdown("#### CapEx Breakdown")
            # Fallback for empty CapEx data
            if not any(capex_data.values()):
                capex_data = {"Fallback": 1.0}

            if case_study["opex"]:
                opex_data = {k: v for k, v in case_study["opex"].items() if v > 0}
            else:
                # Usa il valore diretto di OpEx se specificato
                direct_opex = case_study.get("opex_total", 0.0)
                opex_data = {"Total OpEx (Direct)": float(direct_opex) if direct_opex > 0 else 1.0}

            # Ensure opex_data is not empty
            if not opex_data:
                opex_data = {"Placeholder": 1.0}

            st.markdown("#### OpEx Breakdown")
            # Fallback for empty OpEx data
            if not any(opex_data.values()):
                opex_data = {"Fallback": 1.0}



            # Energy Cost Section
            st.markdown("#### Energy Cost")
            case_study["energy_cost"] = st.number_input(
                f"Energy Cost (EUR per kWh) for {case_study_name}:",
                value=case_study.get("energy_cost", 0.12),  # Default value if missing
                min_value=0.0,
                key=f"energy_cost_{case_study_name}"
            )
            save_case_studies()  # Salva automaticamente al cambio del valore

            # Energy Consumption Section
            st.markdown("#### Energy Consumption per Machine")
            energy_to_delete = []
            for machine, consumption in case_study["energy_consumption"].items():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    new_machine = st.text_input(
                        f"Machine Name ({machine}):",
                        value=machine,
                        key=f"machine_name_{case_study_name}_{machine}"
                    )
                with col2:
                    new_consumption = st.number_input(
                        f"Consumption (kWh) for {machine}:",
                        value=consumption,
                        min_value=0.0,
                        key=f"machine_consumption_{case_study_name}_{machine}"
                    )
                with col3:
                    if st.button(f"Remove {machine}", key=f"remove_machine_{case_study_name}_{machine}"):
                        energy_to_delete.append(machine)

                # Update the dictionary
                if new_machine != machine:
                    case_study["energy_consumption"][new_machine] = case_study["energy_consumption"].pop(machine)
                case_study["energy_consumption"][new_machine] = new_consumption

            for machine in energy_to_delete:
                del case_study["energy_consumption"][machine]

            # Add a new machine
            new_machine_name = st.text_input(f"New Machine Name for {case_study_name}:",
                                             key=f"new_machine_name_{case_study_name}")
            new_machine_consumption = st.number_input(f"New Machine Consumption (kWh) for {case_study_name}:",
                                                      min_value=0.0, key=f"new_machine_consumption_{case_study_name}")
            if st.button(f"Add Machine for {case_study_name}", key=f"add_machine_{case_study_name}"):
                if new_machine_name and new_machine_name not in case_study["energy_consumption"]:
                    case_study["energy_consumption"][new_machine_name] = new_machine_consumption
                    save_case_studies()  # Salva le modifiche
                    st.success(f"Added new machine: {new_machine_name}")
                else:
                    st.error("Machine name is invalid or already exists!")

            # Energy Cost Section (calculated as part of OpEx)
            total_energy_consumption = sum(case_study["energy_consumption"].values())
            energy_cost = total_energy_consumption * case_study.get("energy_cost", 0.0)

            # Add energy cost to OpEx
            case_study["opex"]["Energy"] = energy_cost
            save_case_studies()  # Salva il costo dell'energia aggiornato

            st.markdown(f"**Total Energy Cost (EUR):** {energy_cost:.2f}")

            # Direct Input for CapEx and OpEx
            st.markdown("#### Direct Input for Total CapEx and OpEx")
            direct_capex = st.number_input(
                f"Total CapEx (EUR) for {case_study_name}:",
                value=float(sum(case_study["capex"].values())),
                min_value=0.0,
                key=f"direct_capex_{case_study_name}"
            )
            direct_opex = st.number_input(
                f"Total OpEx (EUR) for {case_study_name}:",
                value=float(sum(case_study["opex"].values())),
                min_value=0.0,
                key=f"direct_opex_{case_study_name}"
            )

            if st.button(f"Update Total CapEx and OpEx for {case_study_name}", key=f"update_totals_{case_study_name}"):
                case_study["capex"] = {"Total CapEx": float(direct_capex)}
                case_study["opex"]["Direct OpEx"] = float(direct_opex)  # Keep other OpEx like energy
                save_case_studies()  # Salva i dati aggiornati
                st.success("Total CapEx and OpEx updated!")

            capex_chart = model.generate_pie_chart(capex_data, f"CapEx Breakdown for {case_study_name}")
            st.image(capex_chart, caption="CapEx Breakdown", use_container_width=True)

            capex_table = model.generate_table(capex_data)
            st.table(capex_table)

            opex_chart = model.generate_pie_chart(opex_data, f"OpEx Breakdown for {case_study_name}")
            st.image(opex_chart, caption="OpEx Breakdown", use_container_width=True)

            opex_table = model.generate_table(opex_data)
            st.table(opex_table)

            # Technical KPIs Section in Literature
            st.markdown("#### Technical KPIs")

            # Caricamento dei KPI tecnici dallo scenario selezionato
            technical_kpis = case_study.setdefault("technical_kpis", {
                "composition": {},
                "recovered_masses": {},
                "phases": {},
                "custom_kpis": {}
            })

            # Sezioni per KPI Tecnici
            sections = ["Material Composition & Efficiency", "Solid/Liquid Ratios", "Add/Modify Custom KPIs"]
            selected_section = st.selectbox("Select Technical KPI Section:", sections)

            # === Material Composition & Efficiency ===
            if selected_section == "Material Composition & Efficiency":
                st.subheader("Material Composition in Black Mass")
                composition = technical_kpis.get("composition", {})
                updated_composition = {}
                total_percentage = 0

                for material, percentage in composition.items():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        new_material = st.text_input(f"Edit Material Name ({material})", value=material,
                                                     key=f"edit_material_{case_study_name}_{material}")
                    with col2:
                        new_percentage = st.number_input(
                            f"Percentage of {material} in BM (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=percentage,
                            key=f"edit_percentage_{case_study_name}_{material}"
                        )
                    with col3:
                        if st.button(f"Remove {material}", key=f"remove_material_{case_study_name}_{material}"):
                            continue

                    updated_composition[new_material] = new_percentage
                    total_percentage += new_percentage

                # Aggiungi nuovo materiale
                new_material_name = st.text_input("New Material Name", key=f"new_material_name_{case_study_name}")
                new_material_percentage = st.number_input("New Material Percentage (%)", min_value=0.0, max_value=100.0,
                                                          key=f"new_material_percentage_{case_study_name}")
                if st.button("Add Material", key=f"add_material_{case_study_name}"):
                    if new_material_name and new_material_name not in updated_composition:
                        updated_composition[new_material_name] = new_material_percentage
                        st.success(f"Added new material: {new_material_name}")
                    else:
                        st.error(f"Material {new_material_name} already exists!")

                technical_kpis["composition"] = updated_composition

                # Verifica totale percentuale
                if total_percentage > 100:
                    st.warning(f"Total material composition exceeds 100% ({total_percentage:.2f}%). Adjust values.")
                elif total_percentage < 100:
                    st.info(f"Total material composition is below 100% ({total_percentage:.2f}%).")

                st.subheader("Efficiency Calculation")
                total_black_mass = st.number_input("Total Black Mass (kg):", min_value=0.1, value=10.0,
                                                   key=f"total_black_mass_{case_study_name}")
                recovered_masses = technical_kpis.get("recovered_masses", {})
                efficiencies = {}
                total_recovered_mass = 0

                for material, percentage in updated_composition.items():
                    initial_mass = total_black_mass * (percentage / 100)
                    recovered_mass = st.number_input(
                        f"Recovered Mass of {material} (kg):",
                        min_value=0.0,
                        value=recovered_masses.get(material, 0.0),
                        key=f"recovered_mass_{case_study_name}_{material}"
                    )
                    recovered_masses[material] = recovered_mass
                    efficiency = (recovered_mass / initial_mass) * 100 if initial_mass > 0 else 0.0
                    efficiencies[material] = efficiency
                    total_recovered_mass += recovered_mass

                overall_efficiency = (total_recovered_mass / total_black_mass) * 100
                technical_kpis["recovered_masses"] = recovered_masses
                technical_kpis["efficiency"] = overall_efficiency

                st.write(f"**Overall Process Efficiency:** {overall_efficiency:.2f}%")
                st.write("**Efficiency and Recovered Mass per Material:**")
                result_df = pd.DataFrame({
                    "Material": list(updated_composition.keys()),
                    "Initial Mass in BM (kg)": [total_black_mass * (p / 100) for p in updated_composition.values()],
                    "Recovered Mass (kg)": [recovered_masses.get(m, 0.0) for m in updated_composition.keys()],
                    "Efficiency (%)": [efficiencies.get(m, 0.0) for m in updated_composition.keys()]
                })
                st.table(result_df)

            # === Solid/Liquid Ratios ===
            if selected_section == "Solid/Liquid Ratios":
                st.subheader("Solid/Liquid Ratios for Each Phase")
                phases = technical_kpis.get("phases", {})
                updated_phases = {}

                for phase_name, phase_data in phases.items():
                    st.subheader(f"Phase: {phase_name}")

                    # Massa per la fase
                    masses = phase_data.get("masses", {})
                    updated_masses = {}

                    st.markdown("##### Mass Types")
                    for mass_type, mass_value in masses.items():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            new_mass_type = st.text_input(
                                f"Mass Type ({mass_type})", value=mass_type,
                                key=f"mass_type_{case_study_name}_{phase_name}_{mass_type}"
                            )
                        with col2:
                            new_mass_value = st.number_input(
                                f"Mass (kg) for {mass_type}:", min_value=0.0,
                                value=mass_value, step=0.1,
                                key=f"mass_value_{case_study_name}_{phase_name}_{mass_type}"
                            )
                        with col3:
                            if st.button(f"Remove Mass ({mass_type})",
                                         key=f"remove_mass_{case_study_name}_{phase_name}_{mass_type}"):
                                continue

                        updated_masses[new_mass_type] = new_mass_value

                    # Aggiungi nuovo tipo di massa
                    new_mass_type = st.text_input(f"New Mass Type for {phase_name}:",
                                                  key=f"new_mass_type_{case_study_name}_{phase_name}")
                    new_mass_value = st.number_input(
                        f"New Mass Value (kg):", min_value=0.0, step=0.1,
                        key=f"new_mass_value_{case_study_name}_{phase_name}"
                    )
                    if st.button(f"Add Mass for {phase_name}", key=f"add_mass_{case_study_name}_{phase_name}"):
                        if new_mass_type and new_mass_type not in updated_masses:
                            updated_masses[new_mass_type] = new_mass_value
                            st.success(f"Added new mass type: {new_mass_type}")
                        else:
                            st.error("Invalid or duplicate mass type!")

                    # Aggiorna le masse della fase
                    masses = updated_masses

                    # Liquidi per la fase
                    liquids = phase_data.get("liquids", {})
                    updated_liquids = {}

                    st.markdown("##### Liquid Types")
                    # Verifica che `liquids` sia un dizionario
                    if isinstance(liquids, list):
                        liquids = {f"Liquid {i + 1}": vol for i, vol in enumerate(liquids)}
                    elif not isinstance(liquids, dict):
                        liquids = {}

                    # Iterazione sicura
                    for liquid_type, liquid_volume in liquids.items():

                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            new_liquid_type = st.text_input(
                                f"Liquid Type ({liquid_type})", value=liquid_type,
                                key=f"liquid_type_{case_study_name}_{phase_name}_{liquid_type}"
                            )
                        with col2:
                            new_liquid_volume = st.number_input(
                                f"Volume (L) for {liquid_type}:", min_value=0.0,
                                value=liquid_volume, step=0.1,
                                key=f"liquid_volume_{case_study_name}_{phase_name}_{liquid_type}"
                            )
                        with col3:
                            if st.button(f"Remove Liquid ({liquid_type})",
                                         key=f"remove_liquid_{case_study_name}_{phase_name}_{liquid_type}"):
                                continue

                        updated_liquids[new_liquid_type] = new_liquid_volume

                    # Aggiungi nuovo tipo di liquido
                    new_liquid_type = st.text_input(f"New Liquid Type for {phase_name}:",
                                                    key=f"new_liquid_type_{case_study_name}_{phase_name}")
                    new_liquid_volume = st.number_input(
                        f"New Liquid Volume (L):", min_value=0.0, step=0.1,
                        key=f"new_liquid_volume_{case_study_name}_{phase_name}"
                    )
                    if st.button(f"Add Liquid for {phase_name}", key=f"add_liquid_{case_study_name}_{phase_name}"):
                        if new_liquid_type and new_liquid_type not in updated_liquids:
                            updated_liquids[new_liquid_type] = new_liquid_volume
                            st.success(f"Added new liquid type: {new_liquid_type}")
                        else:
                            st.error("Invalid or duplicate liquid type!")

                    # Aggiorna i liquidi della fase
                    liquids = updated_liquids

                    # Calcolo rapporti massa/liquido
                    st.markdown("##### Solid/Liquid Ratios")
                    sl_results = []

                    # Assicura che `liquids` sia un dizionario
                    # Assicura che `liquids` sia un dizionario
                    if isinstance(liquids, list):
                        # Converti lista in dizionario, usando l'indice come chiave
                        st.warning(f"'liquids' was a list. Converting to dictionary with indexed keys.")
                        liquids = {f"Liquid {i + 1}": vol for i, vol in enumerate(liquids)}
                    elif not isinstance(liquids, dict):
                        # Inizializza come dizionario vuoto se non è valido
                        st.warning(f"'liquids' was of type {type(liquids)}. Resetting to empty dictionary.")
                        liquids = {}

                    # Iterazione su masse e liquidi
                    for mass_type, mass_value in masses.items():
                        # Verifica che `liquids` sia un dizionario
                        if isinstance(liquids, list):
                            liquids = {f"Liquid {i + 1}": vol for i, vol in enumerate(liquids)}
                        elif not isinstance(liquids, dict):
                            liquids = {}

                        # Iterazione sicura
                        for liquid_type, liquid_volume in liquids.items():

                            # Verifica che `liquid_volume` sia numerico
                            if not isinstance(liquid_volume, (int, float)):
                                st.warning(
                                    f"Invalid liquid volume for '{liquid_type}' in phase '{phase_name}'. Resetting to 0.")
                                liquid_volume = 0  # Imposta un valore predefinito se non è numerico

                            # Calcola il rapporto massa/liquido
                            ratio = mass_value / liquid_volume if liquid_volume > 0 else 0
                            sl_results.append({
                                "Phase": phase_name,
                                "Mass Type": mass_type,
                                "Liquid Type": liquid_type,
                                "Mass (kg)": mass_value,
                                "Liquid Volume (L)": liquid_volume,
                                "S/L Ratio": ratio
                            })

                    # Calcolo rapporto complessivo
                    total_mass = sum(masses.values())
                    total_volume = sum(liquids.values()) if liquids else 0
                    overall_ratio = total_mass / total_volume if total_volume > 0 else 0
                    sl_results.append({
                        "Phase": phase_name,
                        "Mass Type": "Overall",
                        "Liquid Type": "Overall",
                        "Mass (kg)": total_mass,
                        "Liquid Volume (L)": total_volume,
                        "S/L Ratio": overall_ratio
                    })

                    # Mostra risultati in tabella
                    sl_df = pd.DataFrame(sl_results)
                    st.table(sl_df)

                # Aggiungi nuova fase
                new_phase_name = st.text_input("New Phase Name:", key=f"new_phase_name_{case_study_name}")
                if st.button("Add Phase", key=f"add_phase_{case_study_name}"):
                    if new_phase_name and new_phase_name not in updated_phases:
                        updated_phases[new_phase_name] = {"masses": {}, "liquids": {}}
                        st.success(f"Added new phase: {new_phase_name}")
                    else:
                        st.error("Phase already exists or name is invalid!")

                # Salva le modifiche alle fasi
                technical_kpis["phases"] = updated_phases
                save_case_studies()


            # === Add/Modify Custom KPIs ===
            elif selected_section == "Add/Modify Custom KPIs":
                st.subheader("Add or Modify Custom KPIs")
                custom_kpis = technical_kpis.get("custom_kpis", {})

                # Visualizza KPI personalizzati esistenti
                for kpi_name, kpi_value in list(custom_kpis.items()):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        new_kpi_name = st.text_input(f"Edit KPI Name ({kpi_name}):", value=kpi_name,
                                                     key=f"custom_kpi_name_{case_study_name}_{kpi_name}")
                    with col2:
                        new_kpi_value = st.number_input(
                            f"Value for {kpi_name}:",
                            value=kpi_value,
                            min_value=0.0,
                            key=f"custom_kpi_value_{case_study_name}_{kpi_name}"
                        )
                    with col3:
                        if st.button(f"Remove KPI ({kpi_name})", key=f"remove_custom_kpi_{case_study_name}_{kpi_name}"):
                            del custom_kpis[kpi_name]

                    # Aggiorna KPI personalizzati se modificati
                    if new_kpi_name != kpi_name:
                        custom_kpis[new_kpi_name] = custom_kpis.pop(kpi_name)
                    custom_kpis[new_kpi_name] = new_kpi_value

                # Aggiungi nuovi KPI personalizzati
                new_custom_kpi_name = st.text_input("New KPI Name:", key=f"new_custom_kpi_name_{case_study_name}")
                new_custom_kpi_value = st.number_input("New KPI Value:", min_value=0.0,
                                                       key=f"new_custom_kpi_value_{case_study_name}")
                if st.button("Add Custom KPI", key=f"add_custom_kpi_{case_study_name}"):
                    if new_custom_kpi_name and new_custom_kpi_name not in custom_kpis:
                        custom_kpis[new_custom_kpi_name] = new_custom_kpi_value
                        st.success(f"Added new custom KPI: {new_custom_kpi_name}")
                    else:
                        st.error("KPI name is invalid or already exists!")

                # Salva i KPI personalizzati
                technical_kpis["custom_kpis"] = custom_kpis

            # Salva modifiche ai KPI tecnici
            case_study["technical_kpis"] = technical_kpis
            save_case_studies()


st.sidebar.title("Compare Scenarios")
compare_scenarios = st.sidebar.multiselect(
    "Select Scenarios to Compare:",
    [name for name in scenario_names if name != "Create New Scenario"],  # Escludi "Create New Scenario"
    default=["default"]
)

if len(compare_scenarios) > 1:
    st.subheader("Comparison of Selected Scenarios")
    comparison_data = {
        "Scenario": compare_scenarios,
        "Energy Cost": [st.session_state.amelie_scenarios[sc]["energy_cost"] for sc in compare_scenarios],
        "Total CapEx": [sum(st.session_state.amelie_scenarios[sc]["capex"].values()) for sc in compare_scenarios],
        "Total OpEx": [sum(st.session_state.amelie_scenarios[sc]["opex"].values()) for sc in compare_scenarios]
    }
    comparison_df = pd.DataFrame(comparison_data)
    st.table(comparison_df)


def benchmarking():
    st.title("Benchmarking: Unified Comparison Across Scenarios and Literature")

    # Selezione delle fonti (scenari e letteratura)
    selected_scenarios = st.multiselect(
        "Select Scenarios to Compare:",
        list(st.session_state.amelie_scenarios.keys()),
        default=["default"],
        key="benchmarking_scenarios"
    )
    selected_case_studies = st.multiselect(
        "Select Literature Case Studies to Compare:",
        list(st.session_state.case_studies.keys()),
        key="benchmarking_case_studies"
    )

    # Unifica scenari e letteratura in un'unica lista
    sources = []

    # Aggiungi gli scenari
    for scenario_name in selected_scenarios:
        scenario_data = st.session_state.amelie_scenarios.get(scenario_name, {})
        sources.append({
            "name": scenario_name,
            "type": "Scenario",
            "data": scenario_data
        })

    # Aggiungi i casi di letteratura
    for case_study_name in selected_case_studies:
        case_study_data = st.session_state.case_studies.get(case_study_name, {})
        sources.append({
            "name": case_study_name,
            "type": "Literature",
            "data": case_study_data
        })

    # Aggregazione dei dati
    capex_opex_data = []
    mass_volume_ratios = []  # Per rapporto massa/volume

    for source in sources:
        source_name = source["name"]
        source_type = source["type"]
        source_data = source["data"]

        # Assicurati che i dati di CapEx e OpEx siano inizializzati
        capex = sum(source_data.get("capex", {}).values())
        opex = sum(source_data.get("opex", {}).values())

        # Aggiungi i dati di CapEx e OpEx alla lista
        capex_opex_data.append({
            "Source": f"{source_type}: {source_name}",
            "CapEx (EUR)": capex,
            "OpEx (EUR)": opex
        })

        # Processa i dati relativi al rapporto massa/volume
        process_source(source)  # Usa la funzione pre-esistente

    def process_source(source):
        source_name = source["name"]
        source_type = source["type"]
        source_data = source["data"]

        # Assicurati che i dati tecnici siano inizializzati
        source_data.setdefault("technical_kpis", {})
        source_data["technical_kpis"].setdefault("phases", {})

        # Recupera le fasi
        phases = source_data["technical_kpis"]["phases"]

        # Processa i dati relativi al rapporto massa/volume per ogni fase
        for phase_name, phase_data in phases.items():
            # Recupera la massa totale per la fase
            total_mass = phase_data.get("mass", 0)

            # Recupera i dati sui liquidi
            liquids = phase_data.get("liquids", [])
            if not isinstance(liquids, list):  # Gestisce eventuali errori di formato
                st.warning(f"Invalid data format for liquids in phase '{phase_name}' from source '{source_name}'.")
                liquids = []

            # Itera sui liquidi per calcolare il rapporto massa/volume
            for liquid in liquids:
                liquid_type = liquid.get("type", "Unknown")
                liquid_volume = liquid.get("volume", 0)

                # Calcolo del rapporto massa/volume
                sl_ratio = total_mass / liquid_volume if liquid_volume > 0 else 0

                # Aggiungi i dati raccolti
                mass_volume_ratios.append({
                    "Source": f"{source_type}: {source_name}",
                    "Phase": phase_name,
                    "Liquid Type": liquid_type,
                    "Phase Mass (kg)": total_mass,
                    "Liquid Volume (L)": liquid_volume,
                    "S/L Ratio": sl_ratio,
                })

            # Calcolo complessivo per la fase
            total_volume = sum(liquid.get("volume", 0) for liquid in liquids)
            overall_ratio = total_mass / total_volume if total_volume > 0 else 0

            # Aggiungi i dati complessivi della fase
            mass_volume_ratios.append({
                "Source": f"{source_type}: {source_name}",
                "Phase": phase_name,
                "Liquid Type": "Overall",
                "Phase Mass (kg)": total_mass,
                "Liquid Volume (L)": total_volume,
                "S/L Ratio": overall_ratio,
            })

    # Processa i dati relativi al rapporto massa/volume
    process_source(source)  # Usa la funzione pre-esistente

        # Processa tutte le fonti

    for source in sources:
        process_source(source)

    # Visualizzazione dei dati di CapEx e OpEx
    st.markdown("### Comparison of CapEx and OpEx")

    # Converte i dati in DataFrame per il confronto
    capex_opex_df = pd.DataFrame(capex_opex_data)

    # Mostra i dati in formato tabellare
    st.table(capex_opex_df)

    # Grafico a barre per CapEx e OpEx
    st.markdown("#### Bar Chart for CapEx and OpEx")
    fig, ax = plt.subplots(figsize=(10, 6))
    width = 0.4  # Larghezza delle barre
    x = np.arange(len(capex_opex_df["Source"]))

    # Barre per CapEx e OpEx
    ax.bar(x - width / 2, capex_opex_df["CapEx (EUR)"], width=width, label="CapEx")
    ax.bar(x + width / 2, capex_opex_df["OpEx (EUR)"], width=width, label="OpEx")

    # Configurazione grafico
    ax.set_title("Comparison of CapEx and OpEx")
    ax.set_xlabel("Sources")
    ax.set_ylabel("Cost (EUR)")
    ax.set_xticks(x)
    ax.set_xticklabels(capex_opex_df["Source"], rotation=45, ha="right")
    ax.legend()

    # Visualizza il grafico
    st.pyplot(fig)

    # Visualizzazione dei rapporti massa/volume
    st.markdown("### Comparison of Mass/Volume Ratios")

    if mass_volume_ratios:
        # Converte i dati in DataFrame per il confronto
        mass_volume_df = pd.DataFrame(mass_volume_ratios)
        st.dataframe(mass_volume_df)

        # Identifica tutte le combinazioni uniche di fasi e liquidi per garantire uniformità
        unique_phases_liquids = mass_volume_df[["Phase", "Liquid Type"]].drop_duplicates()

        # Pivot per organizzare i dati
        pivot_df = mass_volume_df.pivot(
            index="Source",
            columns=["Phase", "Liquid Type"],
            values="S/L Ratio"
        ).fillna(0)  # Riempie i valori mancanti con 0

        st.markdown("### Pivot Table for Mass/Volume Ratios")
        st.dataframe(pivot_df)

        # Visualizzazione Grafica
        st.markdown("### Graphical Representation of Mass/Volume Ratios")

        # Opzione 1: Grafico a Ragnatela
        st.markdown("#### Radar Chart (Spider Plot) for Phases and Liquids")
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        # Preparazione degli angoli per il grafico radar
        phases_liquids = pivot_df.columns
        num_vars = len(phases_liquids)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Chiudi il cerchio

        # Traccia ogni scenario
        for source, values in pivot_df.iterrows():
            data = values.tolist()
            data += data[:1]  # Chiudi il cerchio
            ax.plot(angles, data, label=source, linewidth=2)
            ax.fill(angles, data, alpha=0.25)

        ax.set_yticks([])
        ax.set_xticks(angles[:-1])
        # Crea etichette leggibili per ogni combinazione fase/liquido
        labels = [f"{phase}\n({liquid})" for phase, liquid in phases_liquids]

        # Imposta le etichette sui vertici del grafico a ragnatela
        ax.set_xticks(angles[:-1])  # Gli angoli corrispondenti ai vertici
        ax.set_xticklabels(labels, fontsize=10)

        ax.set_title("Mass/Volume Ratios by Phase and Liquid")
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1))
        st.pyplot(fig)

        # Opzione 2: Grafico a Barre
        st.markdown("#### Bar Chart for Mass/Volume Ratios")
        # Assicurati che "Source" sia una colonna e non un indice
        if "Source" not in pivot_df.columns:
            st.error("Column 'Source' not found in the DataFrame. Please check the pivot table.")
        else:
            pivot_df = pivot_df.reset_index()  # Assicura che "Source" sia una colonna
            melted_df = pivot_df.melt(id_vars="Source", var_name="Phase & Liquid", value_name="S/L Ratio")

        pivot_df = pivot_df.reset_index()  # Rendi l'indice una colonna
        melted_df = pivot_df.melt(id_vars="Source", var_name="Phase & Liquid", value_name="S/L Ratio")

        fig, ax = plt.subplots(figsize=(12, 6))
        for phase_liquid in melted_df["Phase & Liquid"].unique():
            phase_liquid_data = melted_df[melted_df["Phase & Liquid"] == phase_liquid]
            ax.bar(
                phase_liquid_data["Source"],
                phase_liquid_data["S/L Ratio"],
                label=phase_liquid,
                alpha=0.7
            )
        ax.set_title("Mass/Volume Ratio Comparison")
        ax.set_ylabel("S/L Ratio")
        ax.set_xticklabels(pivot_df.index, rotation=45, ha="right")
        ax.legend(title="Phase & Liquid", bbox_to_anchor=(1.05, 1), loc="upper left")
        st.pyplot(fig)
    else:
        st.warning("No mass/volume ratio data available for comparison.")


if page == "Economic KPIs":
    economic_kpis()
elif page == "Technical KPIs":
    technical_kpis()
elif page == "Literature":
    literature()
elif page == "Benchmarking":
    benchmarking()





