import matplotlib

matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io

import json
import os

# Path to the JSON file
case_studies_file = "case_studies.json"

# Function to save case studies to the JSON file
def save_case_studies():
    with open(case_studies_file, "w") as file:
        json.dump(st.session_state.case_studies, file, indent=4)



# Configure the page layout
st.set_page_config(
    page_title="Amelie KPI Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page:", ["Economic KPIs", "Technical KPIs", "Literature"])

# Initialize session state for case studies
if "case_studies" not in st.session_state:
    st.session_state.case_studies = {}


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
            'Labor': 80,
            'Maintenance': 20,
            'Disposal': 12.5,
            'Malic Acid': 8.0,
            'Hydrogen Peroxide': 4.0,
            'Lithium Precipitation Reagents': 5.0,
            'Co/Ni/Mn Precipitation Reagents': 7.0,
            'Wastewater Treatment Chemicals': 6.0
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


# Initialize Model
model = AmelieEconomicModel()

# Streamlit App
st.title("Amelie Economic Model Configurator")


def economic_kpis():
    st.title("Economic KPIs")

    # Initialize session state
    if "capex_data" not in st.session_state:
        st.session_state.capex_data = model.capex.copy()
    if "opex_data" not in st.session_state:
        st.session_state.opex_data = model.opex.copy()
    if "energy_data" not in st.session_state:
        st.session_state.energy_data = model.energy_consumption.copy()
    if "energy_cost" not in st.session_state:
        st.session_state.energy_cost = 0.12  # Default value if not set

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

    # CapEx Configuration Section
    elif selected_section == "CapEx Configuration":
        st.subheader("CapEx Configuration")
        capex_to_delete = []
        for key, value in st.session_state.capex_data.items():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"capex_name_{key}")
            with col2:
                new_cost = st.number_input(f"Edit Cost (EUR):", value=float(value), min_value=0.0,
                                           key=f"capex_cost_{key}")
            with col3:
                if st.button("Remove", key=f"remove_capex_{key}"):
                    capex_to_delete.append(key)
            if new_name != key:
                st.session_state.capex_data[new_name] = st.session_state.capex_data.pop(key)
            st.session_state.capex_data[new_name] = new_cost
        for item in capex_to_delete:
            del st.session_state.capex_data[item]

        new_name = st.text_input("New CapEx Name:", key="new_capex_name")
        new_cost = st.number_input("New CapEx Cost (EUR):", min_value=0.0, key="new_capex_cost")
        if st.button("Add CapEx"):
            if new_name and new_name not in st.session_state.capex_data:
                st.session_state.capex_data[new_name] = new_cost
                st.success(f"Added new CapEx item: {new_name}")
            else:
                st.error("CapEx item already exists or name is invalid!")

        model.capex = st.session_state.capex_data

        # OpEx Configuration Section
    elif selected_section == "OpEx Configuration":
        st.subheader("OpEx Configuration")

        # Temporary variables
        energy_data_temp = st.session_state.energy_data.copy()
        opex_data_temp = st.session_state.opex_data.copy()

        # Energy Configuration
        st.markdown("### Energy Configuration")

        # Update energy cost
        energy_cost = st.number_input(
            "Cost per kWh (EUR):",
            value=st.session_state.get("energy_cost", 0.12),
            min_value=0.0,
            key="energy_cost_input"  # Unique key for the energy cost input
        )
        st.session_state.energy_cost = energy_cost  # Update session state

        # Add, edit, and delete energy equipment
        energy_to_delete = []
        for key, value in energy_data_temp.items():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(
                    f"Edit Energy Equipment ({key}):",
                    value=key,
                    key=f"energy_name_{key}"
                )
            with col2:
                new_consumption = st.number_input(
                    f"Energy Consumption (kWh) for {key}:",
                    value=float(value),
                    min_value=0.0,
                    key=f"energy_value_{key}"
                )
            with col3:
                if st.button(f"Remove {key}", key=f"remove_energy_{key}"):
                    energy_to_delete.append(key)

            # Update temporary energy data
            if new_name != key:
                energy_data_temp[new_name] = energy_data_temp.pop(key)
            energy_data_temp[new_name] = new_consumption

        # Remove deleted energy items
        for item in energy_to_delete:
            del energy_data_temp[item]

        # Add new energy equipment
        st.markdown("**Add New Energy Equipment**")
        new_energy_name = st.text_input("New Equipment Name:", key="new_energy_name_input")
        new_energy_value = st.number_input("Energy Consumption (kWh):", min_value=0.0, key="new_energy_value_input")
        if st.button("Add Energy Equipment", key="add_energy_input"):
            if new_energy_name and new_energy_name not in energy_data_temp:
                energy_data_temp[new_energy_name] = new_energy_value
                st.success(f"Added new energy equipment: {new_energy_name}")
            else:
                st.error("Energy equipment already exists or name is invalid!")

        # Calculate total energy cost dynamically
        total_energy_consumption = sum(energy_data_temp.values())
        total_energy_cost = total_energy_consumption * energy_cost
        opex_data_temp["Energy"] = total_energy_cost

        # Display total energy cost
        st.markdown(f"**Total Energy Cost:** {total_energy_cost:.2f} EUR")

        # General OpEx Configuration
        st.markdown("### General OpEx Configuration")
        opex_to_delete = []
        for key, value in opex_data_temp.items():
            if key != "Energy":  # Skip energy as it is dynamically calculated
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    new_name = st.text_input(
                        f"Edit Name ({key}):",
                        value=key,
                        key=f"opex_name_{key}"
                    )
                with col2:
                    new_cost = st.number_input(
                        f"Edit Cost (EUR) for {key}:",
                        value=float(value),
                        min_value=0.0,
                        key=f"opex_cost_{key}"
                    )
                with col3:
                    if st.button(f"Remove {key}", key=f"remove_opex_{key}"):
                        opex_to_delete.append(key)

                # Update temporary OpEx data
                if new_name != key:
                    opex_data_temp[new_name] = opex_data_temp.pop(key)
                opex_data_temp[new_name] = new_cost

        # Remove deleted OpEx items
        for item in opex_to_delete:
            del opex_data_temp[item]

        # Add new OpEx item
        st.markdown("**Add New OpEx Item**")
        new_opex_name = st.text_input("New OpEx Name:", key="new_opex_name_input")
        new_opex_cost = st.number_input("New OpEx Cost (EUR):", min_value=0.0, key="new_opex_cost_input")
        if st.button("Add OpEx", key="add_opex_input"):
            if new_opex_name and new_opex_name not in opex_data_temp:
                opex_data_temp[new_opex_name] = new_opex_cost
                st.success(f"Added new OpEx item: {new_opex_name}")
            else:
                st.error("OpEx item already exists or name is invalid!")

        # Update session state in bulk
        st.session_state.energy_data = energy_data_temp
        st.session_state.opex_data = opex_data_temp
        st.session_state.energy_cost = energy_cost

        # Update the model
        model.opex = st.session_state.opex_data
        model.energy_consumption = st.session_state.energy_data


    # Results Section
    elif selected_section == "Results":
        st.subheader("Results")
        capex_total, opex_total = model.calculate_totals()
        st.write(f"**Total CapEx:** {capex_total} EUR")
        st.write(f"**Total OpEx (including energy):** {opex_total} EUR")

        capex_chart = model.generate_pie_chart(st.session_state.capex_data, "CapEx Breakdown")
        st.image(capex_chart, caption="CapEx Breakdown", use_column_width=True)

        capex_table = model.generate_table(st.session_state.capex_data)
        st.table(capex_table)

        opex_chart = model.generate_pie_chart(st.session_state.opex_data, "OpEx Breakdown")
        st.image(opex_chart, caption="OpEx Breakdown", use_column_width=True)

        opex_table = model.generate_table(st.session_state.opex_data)
        st.table(opex_table)


import pandas as pd
import streamlit as st


def technical_kpis():
    st.title("Technical KPIs: Efficiency and Solid/Liquid Ratios")

    # Add a section dropdown
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
                new_material = st.text_input(f"Edit Material Name ({material})", value=material,
                                             key=f"edit_material_{material}")
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
        new_material_percentage = st.number_input("New Material Percentage (%)", min_value=0.0, max_value=100.0,
                                                  key="new_material_percentage")
        if st.button("Add Material"):
            if new_material_name and new_material_name not in updated_composition:
                updated_composition[new_material_name] = new_material_percentage
                st.success(f"Added new material: {new_material_name}")
            elif new_material_name in updated_composition:
                st.error(f"Material {new_material_name} already exists!")

        st.session_state.composition = updated_composition

        if total_percentage > 100:
            st.warning(
                f"Total material composition exceeds 100% (currently {total_percentage:.2f}%). Adjust values accordingly.")
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
        total_black_mass = st.sidebar.number_input("Total Black Mass (kg):", min_value=0.1, value=10.0, step=0.1,
                                                   key="total_black_mass")
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

def literature():
    st.title("Literature: Case Studies")

    # Add, remove, or edit case studies
    # Path to the JSON file
    case_studies_file = "case_studies.json"

    # Load case studies from the file if not already loaded
    if "case_studies" not in st.session_state:
        if os.path.exists(case_studies_file):
            with open(case_studies_file, "r") as file:
                st.session_state.case_studies = json.load(file)
        else:
            st.session_state.case_studies = {}

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
                    new_cost = st.number_input(f"CapEx Cost ({key}):", value=value, min_value=0.0,
                                               key=f"capex_cost_{case_study_name}_{key}")
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
                    st.success("New CapEx item added!")
                else:
                    st.error("CapEx item already exists or name is invalid!")

            # OpEx Section
            st.markdown("#### OpEx")
            opex_to_delete = []
            for key, value in case_study["opex"].items():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    new_name = st.text_input(f"OpEx Name ({key}):", value=key, key=f"opex_name_{case_study_name}_{key}")
                with col2:
                    new_cost = st.number_input(f"OpEx Cost ({key}):", value=value, min_value=0.0,
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
                    st.success("New OpEx item added!")
                else:
                    st.error("OpEx item already exists or name is invalid!")

            # Generate Pie Charts and Tables
            st.markdown("#### Visualization")
            if case_study["capex"]:
                capex_data = {k: v for k, v in case_study["capex"].items() if v > 0}
            else:
                capex_data = {"Direct Entry": float(case_study.get("capex_total", 0.0))}

            # Ensure capex_data is not empty
            if not capex_data:
                capex_data = {"Placeholder": 1.0}

            st.markdown("#### CapEx Breakdown")
            # Fallback for empty CapEx data
            if not any(capex_data.values()):
                capex_data = {"Fallback": 1.0}

            capex_chart = model.generate_pie_chart(capex_data, f"CapEx Breakdown for {case_study_name}")
            st.image(capex_chart, caption="CapEx Breakdown", use_container_width=True)

            capex_table = model.generate_table(capex_data)
            st.table(capex_table)

            if case_study["opex"]:
                opex_data = {k: v for k, v in case_study["opex"].items() if v > 0}
            else:
                opex_data = {"Direct Entry": float(case_study.get("opex_total", 0.0))}

            # Ensure opex_data is not empty
            if not opex_data:
                opex_data = {"Placeholder": 1.0}

            st.markdown("#### OpEx Breakdown")
            # Fallback for empty OpEx data
            if not any(opex_data.values()):
                opex_data = {"Fallback": 1.0}

            opex_chart = model.generate_pie_chart(opex_data, f"OpEx Breakdown for {case_study_name}")
            st.image(opex_chart, caption="OpEx Breakdown", use_container_width=True)

            opex_table = model.generate_table(opex_data)
            st.table(opex_table)

            # Energy Cost Section
            st.markdown("#### Energy Cost")
            case_study["energy_cost"] = st.number_input(
                f"Energy Cost (EUR per kWh) for {case_study_name}:",
                value=case_study.get("energy_cost", 0.0),
                min_value=0.0,
                key=f"energy_cost_{case_study_name}"
            )

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
                    st.success(f"Added new machine: {new_machine_name}")
                else:
                    st.error("Machine name is invalid or already exists!")

            # Energy Cost Section (calculated as part of OpEx)
            total_energy_consumption = sum(case_study["energy_consumption"].values())
            energy_cost = total_energy_consumption * case_study.get("energy_cost", 0.0)

            # Add energy cost to OpEx
            case_study["opex"]["Energy"] = energy_cost

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
                st.success("Total CapEx and OpEx updated!")



# Render the selected page
if page == "Economic KPIs":
    economic_kpis()
elif page == "Technical KPIs":
    technical_kpis()
elif page == "Literature":
    literature()
