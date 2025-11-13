"""
Configuration File
------------------
Contains all parameters for the simulation.
This makes it easy to tweak parameters without touching the core logic.
"""

# 1. Simulation Scenarios
# Defines the different scenarios to run and compare.
SIMULATION_CONFIGS = {
    # Alpha: {Config Dict}
    0: { "ALPHA": 0, "LABEL": "α=0 (Efficiency)" },
    1: { "ALPHA": 1, "LABEL": "α=1 (Proportional Fair)" },
    2: { "ALPHA": 2, "LABEL": "α=2 (Min-Potential Delay)" },
}

# 2. Base Configuration
# These settings are shared by all simulation scenarios.
BASE_CONFIG = {
    # --- World Parameters ---
    "PLAYER_ARRIVAL_RATE": 1.0,         # (A) Avg. 1 player arrives per second
    "PLAYER_MEAN_STAY_TIME": 20.0,        # (B) Avg. player stays for 20 seconds
    "PLAYER_DEPARTURE_RATE": 1.0 / 20.0,
    "SIM_MAX_TIME": 1000.0,             # Run for 1000 simulated seconds
    "SEED": 42,                         # For repeatable, comparable results
    "VERBOSE": False,                   # Set to True to see all event logs

    # --- Player Parameters ---
    "A_MIN": 100.0,                     # Min player valuation
    "A_MAX": 400.0,                     # Max player valuation
    "BUDGET": 4000.0,                   # Max bid = BUDGET / price
    "BID_REVISION_DELAY_MIN": 0.1,      # Min time for a player to "think"
    "BID_REVISION_DELAY_MAX": 0.5,      # Max time for a player to "think"

    # --- Kelly Mechanism Parameters ---
    "DELTA": 0.1,                       # System reservation parameter
    "EPSILON": 1e-3,                    # Min bid to avoid log(0) errors

    # --- Dynamic Pricing Parameters ---
    "DYNAMIC_PRICING": True,
    "PRICE_ADJUST_INTERVAL": 5.0,       # Adjust price every 5 seconds
    "INITIAL_PRICE": 1.0,
    "TARGET_UTILIZATION": 0.75,         # Target 75% utilization (from original main.py)
    "K_PRICE": 0.25,                    # Price adjustment "aggressiveness"
    "MIN_PRICE": 0.05,                  # Price floor
    "MAX_PRICE": 50.0                   # Price ceiling (uncapped from v7)
}