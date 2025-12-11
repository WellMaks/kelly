"""
Configuration File
------------------
Contains parameters for the Hybrid Event-Driven simulation.
"""

# 1. Simulation Scenarios
SIMULATION_CONFIGS = {
    0: { "ALPHA": 0, "LABEL": "α=0 (Efficiency)" },
    1: { "ALPHA": 1, "LABEL": "α=1 (Proportional Fair)" },
    2: { "ALPHA": 2, "LABEL": "α=2 (Min-Potential Delay)" },
}

# 2. Base Configuration
BASE_CONFIG = {
    # --- World Parameters ---
    "PLAYER_ARRIVAL_RATE": 0.5,         # Random background players / sec
    "PLAYER_MEAN_STAY_TIME": 40.0,
    "PLAYER_DEPARTURE_RATE": 1.0 / 40.0,
    "SIM_MAX_TIME": 500.0,
    "SEED": 42,
    "VERBOSE": False,

    # --- The 10 Immortal Test Subjects (IDs 0-9) ---
    # These players will be spawned at T=0 and never leave.
    "TEST_SUBJECTS": [
        {"id": 0, "label": "Pauper 1", "a": 10.0},
        {"id": 1, "label": "Pauper 2", "a": 20.0},
        {"id": 2, "label": "Poor 1",   "a": 40.0},
        {"id": 3, "label": "Poor 2",   "a": 60.0},
        {"id": 4, "label": "Avg 1",    "a": 80.0},
        {"id": 5, "label": "Avg 2",    "a": 100.0},
        {"id": 6, "label": "Rich 1",   "a": 130.0},
        {"id": 7, "label": "Rich 2",   "a": 160.0},
        {"id": 8, "label": "Whale 1",  "a": 190.0},
        {"id": 9, "label": "Whale 2",  "a": 250.0},
    ],

    # --- Player Parameters (For background players) ---
    "A_MIN": 10.0,
    "A_MAX": 100.0,
    "BUDGET": 500.0,
    "BID_REVISION_DELAY_MIN": 0.1,
    "BID_REVISION_DELAY_MAX": 0.3,

    # --- Kelly Mechanism ---
    "DELTA": 0.1,
    "EPSILON": 1e-4,

    # --- Strategy ---
    "STRATEGY": "BEST_RESPONSE",        # Options: "BEST_RESPONSE", "GRADIENT"
    "LEARNING_RATE": 2.0,

    # --- Pricing ---
    "DYNAMIC_PRICING": True,
    "PRICE_ADJUST_INTERVAL": 1.0,
    "INITIAL_PRICE": 0.1,
    "TARGET_UTILIZATION": 0.80,
    "K_PRICE": 0.05,
    "MIN_PRICE": 0.01,
    "MAX_PRICE": 1000.0
}