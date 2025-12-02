"""
Plotting Functions - Master Suite
---------------------------------
Includes Overlay Charts for specific Test Subjects (PIDs 0-9).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import table
from matplotlib.colors import Normalize
from config import SIMULATION_CONFIGS

# --- MICRO: Individual Player Overlays ---
def plot_player_overlays(sims_dict):
    print("Generating individual player overlay charts...")
    test_subject_ids = range(10)
    colors_bid = {0: 'blue', 1: 'green', 2: 'purple'}
    
    for pid in test_subject_ids:
        p_ref_list = [p for p in sims_dict[0].departed_player_data if p['pid'] == pid]
        if not p_ref_list: continue
        p_ref = p_ref_list[0]
        
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()
        
        # Added config lookup to get label if available
        # But relying on data is safer
        
        plt.title(f"Test Subject {pid} (Valuation a={p_ref['a_val']:.1f})", fontsize=14, weight='bold')
        
        for alpha, sim in sims_dict.items():
            p_data_list = [p for p in sim.departed_player_data if p['pid'] == pid]
            if not p_data_list: continue
            player = p_data_list[0]
            
            times = np.array(player['history_time'])
            ax1.plot(times, player['history_bid'], label=f"Bid (α={alpha})", 
                     color=colors_bid[alpha], lw=2, alpha=0.8)
            ax2.plot(times, player['history_alloc'], label=f"Alloc (α={alpha})",
                     color=colors_bid[alpha], linestyle='--', lw=1.5, alpha=0.4)

        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Bid ($)", color='black')
        ax2.set_ylabel("Share", color='gray')
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper right', fontsize='small')
        ax1.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"overlay_test_subject_{pid}.png")
        plt.close()


def plot_distribution_comparison(sims_dict):
    print("Generating plot 'utility_distribution.png'...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=False)
    fig.suptitle("Distribution of Completed Player Utilities", fontsize=16)
    for i, (alpha, sim) in enumerate(sims_dict.items()):
        ax = axes[i]
        utils = [p['final_utility'] for p in sim.departed_player_data if p['time_in_system'] > 1.0]
        if not utils: continue
        lower = np.percentile(utils, 2); upper = np.percentile(utils, 98)
        filtered = [u for u in utils if lower <= u <= upper]
        ax.hist(filtered, bins=30, density=True, alpha=0.75, color='tab:blue')
        ax.set_title(sim.config['LABEL'])
        ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout(); plt.savefig("utility_distribution.png"); plt.close()

def plot_welfare_satisfaction(sims_dict):
    print("Generating plot 'welfare_comparison.png'...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    for alpha, sim in sims_dict.items():
        times, welfare = zip(*sim.stats_social_welfare)
        w_series = pd.Series(welfare).rolling(window=10).mean()
        ax1.plot(times, w_series, label=sim.config['LABEL'])
    ax1.set_title("Total Social Welfare"); ax1.legend(); ax1.grid(True, alpha=0.3)
    for alpha, sim in sims_dict.items():
        times, avg_util = zip(*sim.stats_avg_utility_timeseries)
        u_series = pd.Series(avg_util).rolling(window=10).mean()
        ax2.plot(times, u_series, label=sim.config['LABEL'])
    ax2.set_title("Avg Player Satisfaction"); ax2.legend(); ax2.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig("welfare_comparison.png"); plt.close()

# --- STABILITY & OPS ---
def plot_bid_convergence(sims_dict):
    print("Generating plot 'bid_convergence_volatility.png'...")
    plt.figure(figsize=(12, 6))
    for alpha, sim in sims_dict.items():
        times, avg_bid = zip(*sim.stats_avg_bid)
        series = pd.Series(avg_bid); volatility = series.rolling(window=40).std()
        plt.plot(times, volatility, label=sim.config['LABEL'], lw=2)
    plt.xlabel("Time"); plt.ylabel("Volatility"); plt.legend(); plt.grid(True, alpha=0.3)
    plt.savefig("bid_convergence_volatility.png", dpi=100); plt.close()

def plot_player_load(sims_dict):
    print("Generating plot 'system_load_players.png'...")
    plt.figure(figsize=(12, 5))
    sim = list(sims_dict.values())[0]
    times, counts = zip(*sim.stats_player_count)
    plt.step(times, counts, where='post', color='black', alpha=0.7, lw=1.5)
    plt.fill_between(times, counts, step='post', alpha=0.1, color='blue')
    plt.xlabel("Time (s)"); plt.ylabel("Active Players")
    plt.grid(True, alpha=0.3); plt.tight_layout()
    plt.savefig("system_load_players.png", dpi=100); plt.close()

def plot_jains_fairness_index(sims_dict):
    print("Generating plot 'jains_fairness_index.png'...")
    plt.figure(figsize=(12, 6))
    for alpha, sim in sims_dict.items():
        departed = sorted(sim.departed_player_data, key=lambda x: x['arrival_time'] + x['time_in_system'])
        if not departed: continue
        rolling_times = []; rolling_jain = []
        for i in range(len(departed) - 30):
            window = departed[i : i+30]
            allocs = [p['avg_allocation_pct'] for p in window]
            n = len(allocs); num = sum(allocs) ** 2; den = n * sum([x**2 for x in allocs])
            if den > 0:
                rolling_jain.append(num / den)
                rolling_times.append(window[-1]['arrival_time'] + window[-1]['time_in_system'])
        plt.plot(rolling_times, rolling_jain, label=sim.config['LABEL'], lw=2)
    plt.xlabel("Time"); plt.ylabel("Jain's Index"); plt.legend(); plt.grid(True, alpha=0.3)
    plt.savefig("jains_fairness_index.png", dpi=100); plt.close()

def plot_heatmap_dashboard(all_stats):
    print("Generating plot 'executive_heatmap_dashboard.png'...")
    metrics_map = {"avg_player_count": "Load", "avg_utilization": "Util", "avg_social_welfare": "Welfare", 
                   "avg_bid": "Avg Bid", "avg_price": "Price", "std_dev_utility": "Inequality"}
    rows = []; labels = []; data_matrix = []
    for alpha, stats in all_stats.items():
        labels.append(SIMULATION_CONFIGS[alpha]['LABEL'])
        row_vals = []; raw_row = []
        for key in metrics_map.keys():
            val = stats.get(key, 0.0); raw_row.append(val)
            row_vals.append(f"{val:.2f}")
        rows.append(row_vals); data_matrix.append(raw_row)
    cols = list(metrics_map.values())
    fig, ax = plt.subplots(figsize=(12, 3)); ax.axis('off')
    the_table = table(ax, pd.DataFrame(rows, columns=cols, index=labels), loc='center', cellLoc='center')
    the_table.scale(1.2, 2.5)
    data_np = np.array(data_matrix)
    for col_idx, col_name in enumerate(cols):
        col_values = data_np[:, col_idx]
        norm = Normalize(vmin=min(col_values), vmax=max(col_values))
        for row_idx in range(len(rows)):
            val = data_np[row_idx, col_idx]
            cell = the_table[row_idx + 1, col_idx]
            if "Welfare" in col_name: color = plt.cm.RdYlGn(norm(val))
            elif "Inequality" in col_name or "Price" in col_name: color = plt.cm.RdYlGn(1 - norm(val))
            else: color = plt.cm.Blues(0.2 + 0.5*norm(val))
            cell.set_facecolor(color)
    plt.savefig("executive_heatmap_dashboard.png", bbox_inches='tight'); plt.close()

def plot_strategy_comparison(sims_dict):
    print("Generating plot 'strategy_comparison.png'...")
    plt.figure(figsize=(12, 6))
    for label, sim in sims_dict.items():
        times, avg_bid = zip(*sim.stats_avg_bid)
        plt.plot(times, avg_bid, label=label)
    plt.legend(); plt.tight_layout(); plt.savefig("strategy_comparison.png", dpi=100); plt.close()

def plot_pricing_comparison(sims_dict):
    print("Generating plot 'pricing_mode_comparison.png'...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    target = list(sims_dict.values())[0].config['TARGET_UTILIZATION'] * 100
    ax1.axhline(target, color='r', linestyle='--'); ax1.legend()
    for label, sim in sims_dict.items():
        times, util = zip(*sim.stats_utilization)
        ax1.plot(times, util, label=label)
    for label, sim in sims_dict.items():
        times, welfare = zip(*sim.stats_social_welfare)
        ax2.plot(times, welfare, label=label)
    plt.tight_layout(); plt.savefig("pricing_mode_comparison.png", dpi=100); plt.close()