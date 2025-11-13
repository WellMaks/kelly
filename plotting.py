"""
Plotting Functions
------------------
Contains all functions for generating the final plots and graphs.
Separates analysis from the simulation logic.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import config to get labels
from config import SIMULATION_CONFIGS

def plot_time_series_comparison(sims_dict):
    """
    Plots Player Count, Utilization, and Average Bid over time.
    """
    print("Generating plot 'performance_comparison.png'...")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle("Time-Series Performance Comparison", fontsize=16)

    # Use any sim for player count (they are identical)
    sim_any = list(sims_dict.values())[0]

    # --- Plot 1: Player Count ---
    times, counts = zip(*sim_any.stats_player_count)
    ax1.plot(times, counts, drawstyle='steps-post', label='Player Count')
    ax1.set_ylabel("Active Players")
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.legend()
    ax1.set_title("Player Arrivals/Departures (Identical for all alphas)")

    # --- Plot 2: Utilization ---
    ax2.set_title("System Utilization (Dynamic Response)")
    for alpha, sim in sims_dict.items():
        times, utils = zip(*sim.stats_utilization)
        # Use smoothing to make the lines clearer
        util_series = pd.Series(utils, index=pd.Series(times, name="time"))
        util_smooth = util_series.rolling(window=50, min_periods=1).mean()
        ax2.plot(util_smooth.index, [u * 100 for u in util_smooth.values], label=sim.config['LABEL'], alpha=0.8)
    
    # Add target line
    target_util = sim_any.config['TARGET_UTILIZATION'] * 100
    ax2.axhline(y=target_util, color='r', linestyle='--', label=f'Target ({target_util}%)')
    
    ax2.set_ylabel("Resource Utilization (%)")
    ax2.set_ylim(0, 101)
    ax2.grid(True, linestyle=':', alpha=0.7)
    ax2.legend()

    # --- Plot 3: Average Bid ---
    ax3.set_title("Average Bid per Player (Behavioral Difference)")
    for alpha, sim in sims_dict.items():
        times, bids = zip(*sim.stats_avg_bid)
        bid_series = pd.Series(bids, index=pd.Series(times, name="time"))
        bid_smooth = bid_series.rolling(window=50, min_periods=1).mean()
        ax3.plot(bid_smooth.index, bid_smooth.values, label=sim.config['LABEL'])
        
    ax3.set_ylabel("Average Bid Amount")
    ax3.set_xlabel("Time (seconds)")
    ax3.grid(True, linestyle=':', alpha=0.7)
    ax3.legend()
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("performance_comparison.png", dpi=100)
    plt.close()

def plot_distribution_comparison(sims_dict):
    """
    Plots the "fairness" of each alpha value via histogram.
    """
    print("Generating plot 'utility_distribution.png'...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)
    fig.suptitle("Distribution of Completed Player Utilities (Fairness Comparison)", fontsize=16)

    # Get all utilities to find a common scale
    all_utils = []
    for sim in sims_dict.values():
        all_utils.extend([p['final_utility'] for p in sim.departed_player_data])
    
    if not all_utils:
        print("No utility data to plot.")
        plt.close()
        return

    # Use percentiles to find a good bin range (robust to outliers)
    min_util = np.percentile(all_utils, 1)
    max_util = np.percentile(all_utils, 99)
    if max_util <= min_util: max_util = min_util + 1
    bins = np.linspace(min_util, max_util, 40)

    # Create the 3 side-by-side histograms
    for i, (alpha, sim) in enumerate(sims_dict.items()):
        ax = axes[i]
        utils = [p['final_utility'] for p in sim.departed_player_data]
        ax.hist(utils, bins=bins, density=True, alpha=0.75, label=sim.config['LABEL'])
        ax.set_title(sim.config['LABEL'])
        ax.set_xlabel("Final Utility")
        ax.grid(True, linestyle=':', alpha=0.7)
        if i == 0:
            ax.set_ylabel("Probability Density")
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    plt.savefig("utility_distribution.png", dpi=100)
    plt.close()

def plot_summary_barchart(stats_dict):
    """
    Generates a final bar chart summarizing the key performance
    metrics for a direct comparison.
    """
    print("Generating plot 'summary_metrics.png'...")
    
    sorted_alphas = sorted(stats_dict.keys())
    labels = [SIMULATION_CONFIGS[alpha]['LABEL'] for alpha in sorted_alphas]
    
    # Get all the stats
    avg_social_welfare = [stats_dict[alpha]['avg_social_welfare'] for alpha in sorted_alphas]
    avg_utility_final = [stats_dict[alpha]['avg_utility_final'] for alpha in sorted_alphas]
    std_dev_utilities = [stats_dict[alpha]['std_dev_utility'] for alpha in sorted_alphas]
    avg_bids = [stats_dict[alpha]['avg_bid'] for alpha in sorted_alphas]
    
    x = np.arange(len(labels)) # the label locations
    width = 0.35 # the width of the bars
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Blue, Orange, Green

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Summary of Key Performance Metrics", fontsize=16)
    
    ax_list = axes.flatten()

    # Plot 1: Average Social Welfare (Active)
    ax_list[0].bar(x, avg_social_welfare, width, color=colors)
    ax_list[0].set_title("Average Social Welfare (Sum of active utilities)")
    ax_list[0].set_ylabel("Utility")
    ax_list[0].set_xticks(x); ax_list[0].set_xticklabels(labels, rotation=10)
    ax_list[0].grid(True, linestyle=':', axis='y')

    # Plot 2: Average Utility (Departed)
    ax_list[1].bar(x, avg_utility_final, width, color=colors)
    ax_list[1].set_title("Average Player Utility (Of departed players)")
    ax_list[1].set_ylabel("Utility")
    ax_list[1].set_xticks(x); ax_list[1].set_xticklabels(labels, rotation=10)
    ax_list[1].grid(True, linestyle=':', axis='y')

    # Plot 3: Std Dev of Utility (Fairness)
    ax_list[2].bar(x, std_dev_utilities, width, color=colors)
    ax_list[2].set_title("Utility Std. Deviation (Fairness of departed players)")
    ax_list[2].set_ylabel("Std. Deviation")
    ax_list[2].set_xticks(x); ax_list[2].set_xticklabels(labels, rotation=10)
    ax_list[2].grid(True, linestyle=':', axis='y')

    # Plot 4: Average Bid
    ax_list[3].bar(x, avg_bids, width, color=colors)
    ax_list[3].set_title("Average Bid per Player")
    ax_list[3].set_ylabel("Bid Amount")
    ax_list[3].set_xticks(x); ax_list[3].set_xticklabels(labels, rotation=10)
    ax_list[3].grid(True, linestyle=':', axis='y')

    plt.tight_layout(rect=[0, 0.03, 1, 0.93])
    plt.savefig("summary_metrics.png", dpi=100)
    plt.close()

def plot_welfare_satisfaction(sims_dict):
    """
    Plots Social Welfare and Average Satisfaction over time.
    """
    print("Generating plot 'welfare_comparison.png'...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Welfare and Satisfaction Comparison", fontsize=16)

    # Plot 1: Social Welfare
    ax1.set_title("Social Welfare (Sum of Active Player Utilities)")
    for alpha, sim in sims_dict.items():
        times, welfare = zip(*sim.stats_social_welfare)
        # Use pandas rolling average to smooth the noisy line
        welfare_series = pd.Series(welfare, index=pd.Series(times, name="time"))
        welfare_smooth = welfare_series.rolling(window=50, min_periods=1).mean()
        ax1.plot(welfare_smooth.index, welfare_smooth.values, label=sim.config['LABEL'])
    ax1.set_ylabel("Total Utility")
    ax1.grid(True, linestyle=':', alpha=0.7)
    ax1.legend()

    # Plot 2: Average Player Satisfaction
    ax2.set_title("Average Player 'Satisfaction' (Utility of Active Players)")
    for alpha, sim in sims_dict.items():
        times, avg_util = zip(*sim.stats_avg_utility_timeseries)
        # Use pandas rolling average to smooth the noisy line
        util_series = pd.Series(avg_util, index=pd.Series(times, name="time"))
        util_smooth = util_series.rolling(window=50, min_periods=1).mean()
        ax2.plot(util_smooth.index, util_smooth.values, label=sim.config['LABEL'])
    ax2.set_ylabel("Average Utility")
    ax2.set_xlabel("Time (seconds)")
    ax2.grid(True, linestyle=':', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("welfare_comparison.png", dpi=100)
    plt.close()
    
def plot_price_over_time(sims_dict):
    """
    Plots the dynamic price and utilization on a twin-axis chart.
    """
    print("Generating plot 'price_over_time.png'...")
    fig, ax1 = plt.subplots(figsize=(14, 6)) # Explicitly create fig and ax1
    
    target_util = list(sims_dict.values())[0].config['TARGET_UTILIZATION'] * 100
    plt.title(f"Dynamic Price vs. Utilization (Targeting {target_util}%)", fontsize=16)

    # Plot 1: Prices on ax1 (left y-axis)
    for alpha, sim in sims_dict.items():
        if not sim.config['DYNAMIC_PRICING']: continue
        times, prices = zip(*sim.stats_price)
        ax1.plot(times, prices, drawstyle='steps-post', label=sim.config['LABEL'])
    
    ax1.set_xlabel("Time (seconds)")
    ax1.set_ylabel("Price (Lambda)")
    
    # Plot 2: Utilization on ax2 (right y-axis)
    ax2 = ax1.twinx() # Create a second y-axis
    
    # Use alpha=0 for the reference utilization plot (they are all similar)
    sim_ref = sims_dict.get(0) 
    if sim_ref:
        times_u, utils = zip(*sim_ref.stats_utilization)
        ax2.plot(times_u, [u * 100 for u in utils], 'k:', alpha=0.3, label='Utilization (Ref, α=0)')
    
    # Plot the target line
    ax2.axhline(y=target_util, color='r', linestyle='--', label=f'Target Util ({target_util}%)')
    ax2.set_ylabel("Utilization (%)")
    ax2.set_ylim(0, 101)

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    plt.tight_layout()
    plt.savefig("price_over_time.png", dpi=100)
    plt.close()