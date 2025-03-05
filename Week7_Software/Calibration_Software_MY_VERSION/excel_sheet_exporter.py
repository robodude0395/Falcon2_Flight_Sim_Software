import numpy as np
import pandas as pd
from fluidic_muscle import FluidicMuscle  # Import the FluidicMuscle class

# Initialize the fluidic muscle model
muscle = FluidicMuscle(max_extension=100.0, max_pressure=6000.0)  # 100cm max extension, 6000mbar max pressure

# Define pressure values for contraction (increasing) and relaxation (decreasing)
pressures_contract = list(range(0, 6001, 200))  
pressures_relax = list(range(6000, -1, -200))

# Define loads (kg)
loads = [10, 25, 40]

# Create a dictionary to store the data
data = {"Pressure": pressures_contract}  # First column: pressures for contraction

# Function to simulate muscle behavior under different loads
def simulate_muscle(pressures, is_contracting):
    results = {f"{load}kg_{'contract' if is_contracting else 'relax'} distance": [] for load in loads}

    for p in pressures:
        muscle.apply_pressure(p)  # Update contraction/relaxation state
        base_extension = muscle.apply_pressure(p)  # Get base extension
        
        for load in loads:
            load_factor = load * 0.05  # Simulated effect of load (adjust as needed)
            adjusted_extension = max(base_extension - load_factor, 0)  # Prevent negative extension
            results[f"{load}kg_{'contract' if is_contracting else 'relax'} distance"].append(adjusted_extension)
    
    return results

# Simulate contraction and relaxation
contract_data = simulate_muscle(pressures_contract, is_contracting=True)
relax_data = simulate_muscle(pressures_relax, is_contracting=False)

# Merge data into one dictionary
data.update(contract_data)
data.update(relax_data)

# Convert to Pandas DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel("fluidic_muscle_data.xlsx", index=False)
print("Excel file 'fluidic_muscle_data.xlsx' has been created.")