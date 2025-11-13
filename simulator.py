"""
Event-Driven Simulator File
---------------------------
Contains the main EventDrivenSimulator class.
This class manages the event queue, system state, and all event logic.
"""

import math
import random
import heapq
import statistics
import pandas as pd # Required for per-player summary table

# Import our custom modules
from config import BASE_CONFIG
from core_logic import best_response, utility

class EventDrivenSimulator:
    """
    Implements the main event-driven simulator (Component 4).
    Manages the event queue and system state.
    """
    def __init__(self, config):
        self.config = config
        self.event_queue = []       # Priority queue: (time, type, data)
        self.current_time = 0.0
        self.next_pid = 0
        self.players = {}           # Dict of active players: {pid: player_dict}
        
        # --- System State ---
        self.current_price = config['INITIAL_PRICE']
        
        # --- Statistics Collection ---
        # For time-series plots
        self.stats_player_count = []
        self.stats_utilization = []
        self.stats_avg_bid = []
        self.stats_social_welfare = []
        self.stats_avg_utility_timeseries = []
        self.stats_price = []
        
        # For final summary
        self.departed_player_data = [] # Stores dicts of departed players
        
        # For calculating time-weighted averages
        self.last_stats_update_time = 0.0
        self.integral_player_count = 0.0
        self.integral_utilization = 0.0
        self.integral_avg_bid = 0.0
        self.integral_social_welfare = 0.0
        self.integral_avg_utility = 0.0
        self.completed_player_count = 0

    def schedule_event(self, event_time, event_type, data=None):
        """Adds an event to the priority queue."""
        if data is None: data = {}
        heapq.heappush(self.event_queue, (event_time, event_type, data))

    # --- State Helper Functions ---

    def get_total_bid(self):
        """Returns the sum of all active bids."""
        return sum(p['bid'] for p in self.players.values())

    def get_utilization(self, total_bid):
        """Calculates resource utilization based on total bid."""
        if total_bid + self.config['DELTA'] <= 0: return 0.0
        # Allocation = B / (B + delta)
        return total_bid / (total_bid + self.config['DELTA'])

    # --- Event Handlers ---

    def handle_player_arrival(self, data):
        """Event: A new player enters the system."""
        pid = self.next_pid
        self.next_pid += 1
        a_val = random.uniform(self.config['A_MIN'], self.config['A_MAX'])
        
        # Create player and add to system
        self.players[pid] = {
            'a': a_val, 'bid': 0.0,
            'arrival_time': self.current_time,
            'integral_cost': 0.0,
            'integral_allocation': 0.0,
            'last_update_time': self.current_time
        }
        
        if self.config['VERBOSE']:
            print(f"[T={self.current_time:.2f}] Player {pid} ARRIVED (a={a_val:.2f})")

        # Schedule this player's departure
        stay_duration = random.expovariate(self.config['PLAYER_DEPARTURE_RATE'])
        self.schedule_event(self.current_time + stay_duration, "PLAYER_DEPARTURE", {'pid': pid})
        
        # Schedule the *next* player's arrival
        next_arrival_time = self.current_time + random.expovariate(self.config['PLAYER_ARRIVAL_RATE'])
        self.schedule_event(next_arrival_time, "PLAYER_ARRIVAL", {})
        
        # Notify all players to re-evaluate their bids
        self.notify_all_players_to_revise()

    def handle_player_departure(self, data):
        """Event: An active player leaves the system."""
        pid = data['pid']
        if pid not in self.players: return # Player already left

        player = self.players[pid]
        
        # Update integrals one last time before departing
        self.update_player_integrals()
        
        # Calculate final utility for this player
        final_utility = 0.0
        # Check if player ever made a non-zero bid
        if player['bid'] >= self.config['EPSILON']:
            current_total_bid = self.get_total_bid()
            s_total = current_total_bid + self.config['DELTA']
            if s_total > 0:
                allocation = player['bid'] / s_total
                final_utility = utility(
                    player['a'], allocation, 
                    self.current_price, player['bid'], self.config['ALPHA']
                )
        
        time_in_system = self.current_time - player['arrival_time']
        avg_allocation = (player['integral_allocation'] / time_in_system) if time_in_system > 0 else 0
        
        # Save all stats for this player
        self.departed_player_data.append({
            'pid': pid,
            'a_val': player['a'],
            'time_in_system': time_in_system,
            'total_cost': player['integral_cost'],
            'avg_allocation_pct': avg_allocation * 100,
            'final_utility': final_utility
        })
        self.completed_player_count += 1

        # Remove player from active system
        self.players.pop(pid)
        
        if self.config['VERBOSE']:
            print(f"[T={self.current_time:.2f}] Player {pid} DEPARTED")

        # Notify remaining players to re-evaluate bids
        self.notify_all_players_to_revise()

    def handle_player_bid_revision(self, data):
        """Event: A player re-calculates their best-response bid."""
        pid = data['pid']
        if pid not in self.players: return # Player left before revising

        # Update player integrals *before* the bid changes
        self.update_player_integrals()

        player = self.players[pid]
        current_total_bid = self.get_total_bid()
        
        # Calculate sum of *other* bids
        s_minus = current_total_bid - player['bid'] + self.config['DELTA']
        
        # Get the new optimal bid using the core logic
        new_bid = best_response(
            player['a'], s_minus,
            self.current_price, self.config['ALPHA']
        )
        
        # Apply budget constraint
        new_bid = min(new_bid, self.config['BUDGET'] / self.current_price)
        player['bid'] = new_bid
        
        if self.config['VERBOSE']:
            print(f"[T={self.current_time:.2f}] Player {pid} REVISED bid to {new_bid:.2f}")

    def handle_price_adjustment(self, data):
        """Event: The Resource Owner updates the price (lambda)."""
        
        # 1. Get current utilization
        current_total_bid = self.get_total_bid()
        util_now = self.get_utilization(current_total_bid)
        
        # 2. Calculate error from target
        err = util_now - self.config['TARGET_UTILIZATION']
        k = self.config['K_PRICE']
        
        # 3. Adjust price using feedback formula
        new_price = self.current_price * (1 + k * err)
        
        # 4. Clamp price to min/max
        self.current_price = max(self.config['MIN_PRICE'], min(self.config['MAX_PRICE'], new_price))
        
        if self.config['VERBOSE']:
            print(f"[T={self.current_time:.2f}] PRICE ADJUSTMENT: Util={util_now*100:.1f}%, New Price={self.current_price:.4f}")
        
        # Price changed, so *everyone* needs to reconsider their bids
        self.notify_all_players_to_revise()
        
        # 5. Schedule the next adjustment event
        self.schedule_event(self.current_time + self.config['PRICE_ADJUST_INTERVAL'], "PRICE_ADJUSTMENT", {})

    def notify_all_players_to_revise(self):
        """Schedules a bid revision for all active players."""
        for pid in self.players.keys():
            # Schedule revision after a short "thinking" delay
            revision_time = self.current_time + random.uniform(
                self.config['BID_REVISION_DELAY_MIN'],
                self.config['BID_REVISION_DELAY_MAX']
            )
            self.schedule_event(revision_time, "PLAYER_BID_REVISION", {'pid': pid})

    # --- Statistics & Simulation Loop ---

    def update_player_integrals(self):
        """Update cost/allocation integrals for all active players."""
        time_delta = self.current_time - self.last_stats_update_time
        if time_delta <= 0: return
        
        current_total_bid = self.get_total_bid()
        s_total = current_total_bid + self.config['DELTA']

        for pid, player in self.players.items():
            # Add cost: bid * price * time
            cost_this_interval = player['bid'] * self.current_price * time_delta
            player['integral_cost'] += cost_this_interval
            
            # Add allocation: (bid / total_bid) * time
            allocation_this_interval = 0
            if s_total > 0 and player['bid'] > 0:
                allocation_this_interval = (player['bid'] / s_total) * time_delta
            player['integral_allocation'] += allocation_this_interval
            
            player['last_update_time'] = self.current_time

    def update_stats(self):
        """Update all time-series stats for plotting."""
        time_delta = self.current_time - self.last_stats_update_time
        if time_delta <= 0: return
            
        player_count = len(self.players)
        current_total_bid = self.get_total_bid()
        current_utilization = self.get_utilization(current_total_bid)
        current_avg_bid = (current_total_bid / player_count) if player_count > 0 else 0.0
        
        # Calculate current Social Welfare and Avg. Satisfaction
        current_social_welfare = 0.0
        s_total = current_total_bid + self.config['DELTA']
        
        if player_count > 0 and s_total > 0:
            for pid, player in self.players.items():
                # **BUGFIX**: If bid is 0, utility is 0.
                if player['bid'] < self.config['EPSILON']:
                    player_utility = 0.0
                else:
                    allocation = player['bid'] / s_total
                    player_utility = utility(
                        player['a'], allocation,
                        self.current_price, player['bid'], self.config['ALPHA']
                    )
                current_social_welfare += player_utility
        
        current_avg_utility = (current_social_welfare / player_count) if player_count > 0 else 0.0

        # Update integrals (for time-weighted averages)
        self.integral_player_count += player_count * time_delta
        self.integral_utilization += current_utilization * time_delta
        self.integral_avg_bid += current_avg_bid * time_delta
        self.integral_social_welfare += current_social_welfare * time_delta
        self.integral_avg_utility += current_avg_utility * time_delta
        
        # Store data points for plotting
        self.stats_player_count.append((self.current_time, player_count))
        self.stats_utilization.append((self.current_time, current_utilization))
        self.stats_avg_bid.append((self.current_time, current_avg_bid))
        self.stats_social_welfare.append((self.current_time, current_social_welfare))
        self.stats_avg_utility_timeseries.append((self.current_time, current_avg_utility))
        self.stats_price.append((self.current_time, self.current_price))
        
        self.last_stats_update_time = self.current_time

    def run(self):
        """Main simulation event loop."""
        print(f"--- Simulation Starting for {self.config['LABEL']} ---")
        random.seed(self.config['SEED']) # Use common random numbers
        
        # Schedule the first events
        self.schedule_event(0.0, "PLAYER_ARRIVAL", {})
        if self.config['DYNAMIC_PRICING']:
            self.schedule_event(self.config['PRICE_ADJUST_INTERVAL'], "PRICE_ADJUSTMENT", {})
        
        # === MAIN EVENT LOOP ===
        while self.event_queue:
            # 1. Get next event
            event_time, event_type, data = heapq.heappop(self.event_queue)
            
            # 2. Check for simulation end
            if event_time > self.config['SIM_MAX_TIME']:
                print(f"--- Simulation End at T={self.current_time:.2f} ---")
                break
            
            # 3. Update all stats *before* changing state
            self.update_player_integrals()
            self.update_stats()
            
            # 4. Advance time
            self.current_time = event_time
            
            # 5. Process the event
            if event_type == "PLAYER_ARRIVAL": self.handle_player_arrival(data)
            elif event_type == "PLAYER_DEPARTURE": self.handle_player_departure(data)
            elif event_type == "PLAYER_BID_REVISION": self.handle_player_bid_revision(data)
            elif event_type == "PRICE_ADJUSTMENT": self.handle_price_adjustment(data)
        
        # Final update to capture stats from last event to end time
        self.update_stats()
        print(f"Processed {self.next_pid} arrivals and {self.completed_player_count} departures.")

    def get_summary_stats(self):
        """Calculates and returns final performance metrics."""
        if self.current_time == 0: return {}
        
        # Get stats from the *full* list of departed players
        final_utilities = [p['final_utility'] for p in self.departed_player_data]
        avg_utility_final = 0.0
        std_dev_utility = 0.0
        
        if final_utilities:
            avg_utility_final = statistics.mean(final_utilities)
        if len(final_utilities) > 1:
            std_dev_utility = statistics.stdev(final_utilities)

        # Return time-weighted averages
        return {
            "avg_player_count": self.integral_player_count / self.current_time,
            "avg_utilization": self.integral_utilization / self.current_time,
            "avg_bid": self.integral_avg_bid / self.current_time,
            "avg_social_welfare": self.integral_social_welfare / self.current_time,
            "avg_satisfaction": self.integral_avg_utility / self.current_time,
            "avg_utility_final": avg_utility_final,
            "std_dev_utility": std_dev_utility
        }

    def print_results(self):
        """Prints the final summary statistics to the console."""
        stats = self.get_summary_stats()
        print(f"\n--- Performance Evaluation for {self.config['LABEL']} ---")
        print(f"Average Players in System: {stats['avg_player_count']:.2f}")
        print(f"Average Resource Utilization: {stats['avg_utilization'] * 100:.1f}%")
        print(f"Average Player Utility:      {stats['avg_utility_final']:.2f} (for departed players)")
        print(f"Std Dev of Utility (Fairness): {stats['std_dev_utility']:.2f}")
        print(f"Average Bid per Player:      {stats['avg_bid']:.2f}")
        print(f"Average Social Welfare (Active): {stats['avg_social_welfare']:.2f}")
        print(f"Average Satisfaction (Active): {stats['avg_satisfaction']:.2f}")

    def print_player_summary(self):
        """Prints the detailed table of all departed players."""
        print(f"\n--- Departed Player Summary for {self.config['LABEL']} ---")
        if not self.departed_player_data:
            print("No players departed.")
            return

        # Use pandas for nice formatting
        df = pd.DataFrame(self.departed_player_data)
        df = df.set_index('pid')
        
        # Format columns for readability
        df['a_val'] = df['a_val'].map('{:,.2f}'.format)
        df['time_in_system'] = df['time_in_system'].map('{:,.2f}s'.format)
        df['total_cost'] = df['total_cost'].map('${:,.2f}'.format)
        df['avg_allocation_pct'] = df['avg_allocation_pct'].map('{:,.2f}%'.format)
        df['final_utility'] = df['final_utility'].map('{:,.2f}'.format)
        
        pd.set_option('display.max_rows', 50) # Show up to 50 players
        print(df.to_string(max_rows=50))