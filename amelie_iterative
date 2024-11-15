import streamlit as st
import matplotlib.pyplot as plt
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
        self.cost_fluctuations = {
            'Reagents': {'Lower': -20, 'Base': 0, 'Upper': 20},
            'Energy': {'Lower': -15, 'Base': 0, 'Upper': 25},
            'Labor': {'Lower': -5, 'Base': 0, 'Upper': 10},
            'Maintenance': {'Lower': -10, 'Base': 0, 'Upper': 15},
            'Disposal': {'Lower': -10, 'Base': 0, 'Upper': 10},
            'Microwave Energy': {'Lower': -10, 'Base': 0, 'Upper': 15},
            'Ascorbic Acid': {'Lower': -15, 'Base': 0, 'Upper': 20},
            'Wastewater Treatment': {'Lower': -5, 'Base': 0, 'Upper': 10}
        }
        self.black_mass = 10
        self.scenarios = {}

    def calculate_totals(self):
        capex_total = sum(self.capex.values())
        opex_total = sum(self.opex.values())
        return capex_total, opex_total

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

    def add_scenario(self, name, capex_changes, opex_percentage_changes, fluctuation_type):
        self.scenarios[name] = {
            'CapEx': capex_changes,
            'OpExPercentage': opex_percentage_changes,
            'FluctuationType': fluctuation_type
        }

    def apply_scenario(self, name):
        if name in self.scenarios:
            scenario = self.scenarios[name]
            for key, change in scenario['CapEx'].items():
                self.capex[key] = self.capex.get(key, 0) + change
            for key, percentage_change in scenario['OpExPercentage'].items():
                self.opex[key] *= (1 + percentage_change / 100)
            for cost, fluctuation in self.cost_fluctuations.items():
                fluctuation_percentage = fluctuation[scenario['FluctuationType']]
                if cost in self.opex:
                    self.opex[cost] *= (1 + fluctuation_percentage / 100)


# Streamlit App
model = AmelieEconomicModel()

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

# Configure Black Mass
st.subheader("Configure Black Mass")
model.black_mass = st.number_input("Mass of Black Mass (kg)", min_value=1, value=model.black_mass)

# Manage CapEx
st.subheader("CapEx Configuration")
for item, cost in model.capex.items():
    model.capex[item] = st.number_input(f"{item} Cost (EUR)", min_value=0, value=cost)

new_capex_name = st.text_input("Add a New CapEx Item")
new_capex_cost = st.number_input("New CapEx Item Cost (EUR)", min_value=0)
if st.button("Add CapEx Item"):
    if new_capex_name and new_capex_cost > 0:
        model.capex[new_capex_name] = new_capex_cost

# Manage OpEx
st.subheader("OpEx Configuration")
for item, cost in model.opex.items():
    model.opex[item] = st.number_input(f"{item} Cost (EUR/batch)", min_value=0.0, value=cost)

new_opex_name = st.text_input("Add a New OpEx Item")
new_opex_cost = st.number_input("New OpEx Item Cost (EUR/batch)", min_value=0.0)
if st.button("Add OpEx Item"):
    if new_opex_name and new_opex_cost > 0:
        model.opex[new_opex_name] = new_opex_cost

# Configure Cost Fluctuations
st.subheader("Scenario Cost Fluctuations")
for level in model.cost_fluctuations.keys():
    for cost in model.cost_fluctuations:
        model.cost_fluctuations[cost][level] = st.number_input(
            f"{cost} - {level} Fluctuation (%)", value=model.cost_fluctuations[cost][level]
        )

# Display Results
st.subheader("Results")
capex_total, opex_total = model.calculate_totals()
st.write(f"**Total CapEx:** {capex_total} EUR")
st.write(f"**Total OpEx:** {opex_total} EUR/batch")

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
