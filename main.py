"""
Main Simulation Runner
----------------------
This is the main entry point for the project.
It imports the other modules and runs the simulation.
"""

# Check for required libraries
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("This script requires 'pandas', 'matplotlib', and 'numpy'.")
    print("Please install them by running:")
    print("pip install pandas matplotlib numpy")
    exit()

# Import our project files
import config
from simulator import EventDrivenSimulator
import plotting

def run_all_simulations():
    """
    Runs the simulation for each scenario defined in config.py
    and generates all plots.
    """
    sims = {}       # Stores the simulator object for each alpha
    all_stats = {}  # Stores the final summary stats for each alpha

    # --- Run all simulations ---
    for alpha_val, config_data in config.SIMULATION_CONFIGS.items():
        
        # Create a combined config dict for this run
        run_config = config.BASE_CONFIG.copy()
        run_config.update(config_data) # Add ALPHA and LABEL
        
        # Create and run the simulator
        sim = EventDrivenSimulator(run_config)
        sim.run()
        
        # Print results to console
        sim.print_results()
        sim.print_player_summary()
        
        # Store results for plotting
        sims[alpha_val] = sim
        all_stats[alpha_val] = sim.get_summary_stats()

    # --- Generate Comparative Plots ---
    if sims:
        plotting.plot_time_series_comparison(sims)
        plotting.plot_distribution_comparison(sims)
        plotting.plot_summary_barchart(all_stats)
        plotting.plot_welfare_satisfaction(sims)
        plotting.plot_price_over_time(sims)
        
        print("\n✅ All simulations and plots are complete.")
        print("Generated files:")
        print(" - performance_comparison.png")
        print(" - utility_distribution.png")
        print(" - summary_metrics.png")
        print(" - welfare_comparison.png")
        print(" - price_over_time.png")
    else:
        print("No simulations were run.")

# ===================================================================
# ==== Main Execution ====
# ===================================================================

if __name__ == "__main__":
    run_all_simulations()