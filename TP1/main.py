"""
Main Simulation Runner
"""
import config
from simulator import EventDrivenSimulator
import plotting
import numpy as np
import pandas as pd

def run_main_fairness_experiment():
    print("\n=== 1. Running Fairness Experiment (Alpha 0, 1, 2) ===")
    sims = {}
    all_stats = {}

    for alpha_val, config_data in config.SIMULATION_CONFIGS.items():
        run_config = config.BASE_CONFIG.copy()
        run_config.update(config_data)
        
        sim = EventDrivenSimulator(run_config)
        sim.run()
        sims[alpha_val] = sim
        
        stats = sim.get_summary_stats()
        stats['avg_price'] = np.mean([p[1] for p in sim.stats_price]) if sim.stats_price else 0.0
        all_stats[alpha_val] = stats

    # --- Generate Plots ---
    # Only calling functions present in your plotting.py
    
    plotting.plot_distribution_comparison(sims)
    plotting.plot_welfare_satisfaction(sims)
    plotting.plot_player_load(sims) 
    plotting.plot_heatmap_dashboard(all_stats)
    
    # NEW: Overlay Plots for Test Subjects
    plotting.plot_player_overlays(sims)
        
    # NOTE: 'plot_fairness_scatter', 'plot_bid_convergence', and 
    # 'plot_jains_fairness_index' were removed to match your plotting file.
    
    print(">> Fairness plots & Overlay Player Graphs generated.")

def run_strategy_comparison():
    print("\n=== 2. Running Strategy Comparison ===")
    sims = {}
    base_conf = config.BASE_CONFIG.copy()
    base_conf.update(config.SIMULATION_CONFIGS[1])
    
    for strat in ['BEST_RESPONSE', 'GRADIENT']:
        conf = base_conf.copy()
        conf['STRATEGY'] = strat
        if strat == 'GRADIENT': conf['LEARNING_RATE'] = 2.0
        sim = EventDrivenSimulator(conf)
        sim.run()
        sims[strat] = sim
    plotting.plot_strategy_comparison(sims)

def run_pricing_comparison():
    print("\n=== 3. Running Pricing Comparison ===")
    sims = {}
    base_conf = config.BASE_CONFIG.copy()
    base_conf.update(config.SIMULATION_CONFIGS[1])
    
    conf_dyn = base_conf.copy(); conf_dyn['DYNAMIC_PRICING'] = True
    sim_dyn = EventDrivenSimulator(conf_dyn); sim_dyn.run(); sims['Dynamic'] = sim_dyn
    
    conf_stat = base_conf.copy(); conf_stat['DYNAMIC_PRICING'] = False; conf_stat['INITIAL_PRICE'] = 2.0
    sim_stat = EventDrivenSimulator(conf_stat); sim_stat.run(); sims['Static'] = sim_stat
    plotting.plot_pricing_comparison(sims)

if __name__ == "__main__":
    run_main_fairness_experiment()
    # Scalability analysis removed as plot_sensitivity_analysis is missing from plotting.py
    run_strategy_comparison()
    run_pricing_comparison()
    print("\n✅ ALL EXPERIMENTS COMPLETE.")