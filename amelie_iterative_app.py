import matplotlib
matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io

# Configure the page layout
st.set_page_config(
    page_title="Amelie KPI Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page:", ["Economic KPIs", "Technical KPIs"])


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
            'Disposal': 12.5,
            'Microwave Energy': 6.0,
            'Drying Energy (Pre-treatment)': 3.5,
            'Drying Energy (Secondary)': 2.5,
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
        self.scenarios = {}

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
        plt.savefig(buf, format='png', bbox_inches="tight")
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

    # Add a section dropdown
    sections = ["General Assumptions", "CapEx Configuration", "OpEx Configuration", "Energy Consumption", "Results"]
    selected_section = st.selectbox("Jump to Section:", sections)

    # General Assumptions Section
    if selected_section == "General Assumptions":
        st.subheader("General Assumptions")
        st.markdown("""
        - Pilot project sized for 10 kg BM per batch.
        - No infrastructure costs.
        - Process includes BM pre-treatment, microwave-assisted thermal treatment, leaching in water, precipitation for lithium recovery, secondary drying, leaching in acid (malic acid and hydrogen peroxide), and wastewater treatment.
        - Energy cost calculated dynamically based on kWh per machine.
        - Labor includes one operator per batch.
        - Maintenance and disposal are estimated.
        """)
        flowchart_path = "processo.png"
        st.image(flowchart_path, caption="Recycling Process Flowchart (UNIBS) (from Rallo thesis)", use_column_width=True)

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

    # Energy Consumption Section
    elif selected_section == "Energy Consumption":
        st.subheader("Energy Consumption Configuration")
        if "energy_data" not in st.session_state:
            st.session_state.energy_data = model.energy_consumption.copy()

        energy_to_delete = []
        for key in list(st.session_state.energy_data.keys()):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"energy_name_{key}")
            with col2:
                new_consumption = st.number_input(
                    f"Edit Consumption for {key} (kWh):",
                    value=float(st.session_state.energy_data[key]),
                    min_value=0.0,
                    key=f"energy_consumption_{key}"
                )
            with col3:
                if st.button("Remove", key=f"remove_energy_{key}"):
                    energy_to_delete.append(key)
            if new_name != key:
                st.session_state.energy_data[new_name] = st.session_state.energy_data.pop(key)
            st.session_state.energy_data[new_name] = new_consumption

        for item in energy_to_delete:
            del st.session_state.energy_data[item]

        st.markdown("**Add New Energy Equipment**")
        new_energy_name = st.text_input("New Equipment Name for Energy Consumption:", key="new_energy_name")
        new_energy_consumption = st.number_input(
            "New Equipment Energy Consumption (kWh):",
            min_value=0.0,
            key="new_energy_consumption"
        )
        if st.button("Add Energy Equipment", key="add_energy"):
            if new_energy_name and new_energy_name not in st.session_state.energy_data:
                st.session_state.energy_data[new_energy_name] = new_energy_consumption
                st.success(f"Added new energy equipment: {new_energy_name}")
            elif new_energy_name in st.session_state.energy_data:
                st.error(f"The energy equipment '{new_energy_name}' already exists!")

        model.energy_consumption = st.session_state.energy_data

    # Results Section
    elif selected_section == "Results":
        st.subheader("Results")
        capex_total, opex_total = model.calculate_totals()
        st.write(f"**Total CapEx:** {capex_total} EUR")
        st.write(f"**Total OpEx (including energy):** {opex_total} EUR/batch")

        st.subheader("CapEx Breakdown")
        capex_chart_buf = model.generate_pie_chart(model.capex, "CapEx Breakdown")
        st.image(capex_chart_buf, caption="CapEx Pie Chart", use_column_width=True)

        st.subheader("OpEx Breakdown")
        opex_chart_buf = model.generate_pie_chart(model.opex, "OpEx Breakdown")
        st.image(opex_chart_buf, caption="OpEx Pie Chart", use_column_width=True)

        st.subheader("CapEx Table")
        capex_table = model.generate_table(model.capex)
        st.table(capex_table)

        st.subheader("OpEx Table")
        opex_table = model.generate_table(model.opex)
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

# Render the selected page
if page == "Economic KPIs":
    economic_kpis()
elif page == "Technical KPIs":
    technical_kpis()






