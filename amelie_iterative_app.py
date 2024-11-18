import matplotlib
matplotlib.use('Agg')  # Required for Streamlit compatibility
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import io


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

# General Assumptions
st.subheader("General Assumptions")
st.markdown("""
- Pilot project sized for 10 kg BM per batch.
- No infrastructure costs.
- Process includes BM pre-treatment, microwave-assisted thermal treatment, leaching in water, precipitation for lithium recovery, secondary drying, leaching in acid (malic acid and hydrogen peroxide), and wastewater treatment.
- Energy cost calculated dynamically based on kWh per machine.
- Labor includes one operator per batch.
- Maintenance and disposal are estimated.
""")
# Add a section for the recycling process flowchart
st.subheader("Recycling Process Flowchart")

# Display the flowchart image
flowchart_path = "processo.png"  # Adjust the path if the image is in a subfolder
st.image(flowchart_path, caption="Recycling Process Flowchart (UNIBS)", use_column_width=True)

# Configure Black Mass
st.subheader("Configure Black Mass")
model.black_mass = st.number_input("Mass of Black Mass (kg)", min_value=1, value=model.black_mass)

# Manage CapEx
st.subheader("CapEx Configuration")

# Dynamic CapEx input form
if "capex_data" not in st.session_state:
    st.session_state.capex_data = model.capex.copy()

# Display existing CapEx items with editable inputs
capex_to_delete = []
for key in list(st.session_state.capex_data.keys()):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"capex_name_{key}")
    with col2:
        new_cost = st.number_input(
            f"Edit Cost for {key} (EUR):",
            value=float(st.session_state.capex_data[key]),  # Ensure value is float
            min_value=0.0,
            key=f"capex_cost_{key}"
        )
    with col3:
        if st.button("Remove", key=f"remove_capex_{key}"):
            capex_to_delete.append(key)
    if new_name != key:
        st.session_state.capex_data[new_name] = st.session_state.capex_data.pop(key)
    st.session_state.capex_data[new_name] = new_cost

# Remove items marked for deletion
for item in capex_to_delete:
    del st.session_state.capex_data[item]

# Add new CapEx item
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

# Manage OpEx
st.subheader("OpEx Configuration")

# Dynamic OpEx input form
if "opex_data" not in st.session_state:
    st.session_state.opex_data = model.opex.copy()

# Display existing OpEx items with editable inputs
opex_to_delete = []
for key in list(st.session_state.opex_data.keys()):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"opex_name_{key}")
    with col2:
        new_cost = st.number_input(
            f"Edit Cost for {key} (EUR/batch):",
            value=float(st.session_state.opex_data[key]),  # Ensure value is float
            min_value=0.0,
            key=f"opex_cost_{key}"
        )
    with col3:
        if st.button("Remove", key=f"remove_opex_{key}"):
            opex_to_delete.append(key)
    if new_name != key:
        st.session_state.opex_data[new_name] = st.session_state.opex_data.pop(key)
    st.session_state.opex_data[new_name] = new_cost

# Remove items marked for deletion
for item in opex_to_delete:
    del st.session_state.opex_data[item]

# Add new OpEx item
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




# Manage Energy Consumption
st.subheader("Energy Consumption Configuration")

# Dynamic Energy Consumption input form
if "energy_data" not in st.session_state:
    st.session_state.energy_data = model.energy_consumption.copy()

# Display existing energy consumption items with editable inputs
energy_to_delete = []
for key in list(st.session_state.energy_data.keys()):
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_name = st.text_input(f"Edit Name: {key}", value=key, key=f"energy_name_{key}")
    with col2:
        new_consumption = st.number_input(
            f"Edit Consumption for {key} (kWh):",
            value=float(st.session_state.energy_data[key]),  # Ensure value is float
            min_value=0.0,
            key=f"energy_consumption_{key}"
        )
    with col3:
        if st.button("Remove", key=f"remove_energy_{key}"):
            energy_to_delete.append(key)
    if new_name != key:
        st.session_state.energy_data[new_name] = st.session_state.energy_data.pop(key)
    st.session_state.energy_data[new_name] = new_consumption

# Remove items marked for deletion
for item in energy_to_delete:
    del st.session_state.energy_data[item]

# Add new energy consumption item
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

# Save the updated energy consumption configuration
model.energy_consumption = st.session_state.energy_data


# Display Results
st.subheader("Results")
capex_total, opex_total = model.calculate_totals()
st.write(f"**Total CapEx:** {capex_total} EUR")
st.write(f"**Total OpEx (including energy):** {opex_total} EUR/batch")

# CapEx Chart
st.subheader("CapEx Breakdown")
capex_chart_buf = model.generate_pie_chart(model.capex, "CapEx Breakdown")
st.image(capex_chart_buf, caption="CapEx Pie Chart", use_column_width=True)

# OpEx Chart
st.subheader("OpEx Breakdown")
opex_chart_buf = model.generate_pie_chart(model.opex, "OpEx Breakdown")
st.image(opex_chart_buf, caption="OpEx Pie Chart", use_column_width=True)

# Display tables
st.subheader("CapEx Table")
capex_table = model.generate_table(model.capex)
st.table(capex_table)

st.subheader("OpEx Table")
opex_table = model.generate_table(model.opex)
st.table(opex_table)

# Technical KPI: Efficiency
st.subheader("Technical KPI: Efficiency")

# Define default material composition
if "composition" not in st.session_state:
    st.session_state.composition = {'Li': 7.0, 'Co': 15.0, 'Ni': 10.0, 'Mn': 8.0}  # Default percentages

# Display and allow the user to edit default materials
st.markdown("### Material Composition")
total_percentage = 0  # Track the sum of percentages
updated_composition = {}

for material, percentage in list(st.session_state.composition.items()):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Allow editing of material names
        new_material = st.text_input(f"Edit Material Name ({material})", value=material, key=f"edit_material_{material}")
    with col2:
        # Allow editing of material percentages
        new_percentage = st.number_input(
            f"Percentage of {material} (%)",
            min_value=0.0,
            max_value=100.0,
            value=percentage,
            key=f"edit_percentage_{material}"
        )
    with col3:
        # Option to remove material
        if st.button(f"Remove {material}", key=f"remove_material_{material}"):
            st.session_state.composition.pop(material, None)

    # Save updated composition
    updated_composition[new_material] = new_percentage
    total_percentage += new_percentage

# Add a new material dynamically
st.markdown("**Add New Material**")
new_material_name = st.text_input("New Material Name", key="new_material_name")
new_material_percentage = st.number_input("New Material Percentage (%)", min_value=0.0, max_value=100.0, key="new_material_percentage")
if st.button("Add Material"):
    if new_material_name and new_material_name not in updated_composition:
        updated_composition[new_material_name] = new_material_percentage
        st.success(f"Added new material: {new_material_name}")
    elif new_material_name in updated_composition:
        st.error(f"Material {new_material_name} already exists!")

# Update session state with new composition
st.session_state.composition = updated_composition

# Warn if total percentage exceeds 100
if total_percentage > 100:
    st.warning(f"Total material composition exceeds 100% (currently {total_percentage:.2f}%). Adjust values accordingly.")
elif total_percentage < 100:
    st.info(f"Total material composition is below 100% (currently {total_percentage:.2f}%).")

# Efficiency Calculation
st.markdown("### Process Efficiency")
overall_efficiency = st.slider("Set Overall Process Efficiency (%)", min_value=0, max_value=100, value=85) / 100

# Calculate total recovered mass
total_black_mass = model.black_mass
total_recovered_mass = total_black_mass * overall_efficiency

# Calculate recovered mass per material based on user-defined composition
recovered_masses = {
    material: total_recovered_mass * (percentage / 100)
    for material, percentage in st.session_state.composition.items()
}

# Display Results
st.write(f"**Overall Process Efficiency:** {overall_efficiency * 100:.2f}%")
st.write(f"**Total Recovered Mass (kg):** {total_recovered_mass:.2f}")
st.write("**Recovered Mass by Material (kg):**")
st.table(pd.DataFrame(recovered_masses.items(), columns=["Material", "Recovered Mass (kg)"]))

