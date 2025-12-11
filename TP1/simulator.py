"""
Event-Driven Simulator (Hybrid & Robust)
----------------------------------------
1. Spawns 10 specific 'Test Subject' players who stay forever.
2. Spawns random 'Background' players.
3. Fixes heapq crash using tie-breaker counter.
"""
import math
import random
import heapq
import statistics
import itertools
from config import BASE_CONFIG
from core_logic import best_response, utility, gradient_descent_bid

class EventDrivenSimulator:
    def __init__(self, config):
        self.config = config
        self.event_queue = []
        self.event_counter = itertools.count() # TIE-BREAKER for priority queue
        
        self.current_time = 0.0
        self.next_pid = 0
        self.players = {}
        self.test_subjects = [] 
        
        # System State
        self.current_price = config['INITIAL_PRICE']
        
        # Stats
        self.stats_player_count = []
        self.stats_utilization = []
        self.stats_avg_bid = []
        self.stats_social_welfare = []
        self.stats_avg_utility_timeseries = []
        self.stats_price = []
        self.departed_player_data = [] 
        
        self.last_stats_update_time = 0.0
        self.integral_player_count = 0.0
        self.integral_utilization = 0.0
        self.integral_avg_bid = 0.0
        self.integral_social_welfare = 0.0
        self.integral_avg_utility = 0.0
        self.completed_player_count = 0

    def schedule_event(self, event_time, event_type, data=None):
        """Adds event with unique ID to prevent heap comparison crash."""
        if data is None: data = {}
        count = next(self.event_counter)
        heapq.heappush(self.event_queue, (event_time, count, event_type, data))

    def get_total_bid(self):
        return sum(p['bid'] for p in self.players.values())

    def get_utilization(self, total_bid):
        if total_bid + self.config['DELTA'] <= 0: return 0.0
        return total_bid / (total_bid + self.config['DELTA'])

    def spawn_test_subjects(self):
        """Creates the 10 fixed players defined in config."""
        subjects = self.config.get('TEST_SUBJECTS', [])
        
        for p_conf in subjects:
            pid = p_conf['id'] 
            if pid >= self.next_pid: self.next_pid = pid + 1
            
            self.players[pid] = {
                'a': float(p_conf['a']), 
                'bid': 0.1, 
                'arrival_time': 0.0,
                'integral_cost': 0.0,
                'integral_allocation': 0.0,
                'last_update_time': 0.0,
                'history_time': [0.0], 
                'history_bid': [0.1],
                'history_alloc': [0.0],
                'is_test_subject': True 
            }
            self.test_subjects.append(pid)
            # Wake them up immediately so they start bidding at T=0.1
            self.schedule_event(0.1, "PLAYER_BID_REVISION", {'pid': pid})

    def handle_player_arrival(self, data):
        pid = self.next_pid
        self.next_pid += 1
        a_val = random.uniform(self.config['A_MIN'], self.config['A_MAX'])
        
        self.players[pid] = {
            'a': a_val, 'bid': 0.0,
            'arrival_time': self.current_time,
            'integral_cost': 0.0,
            'integral_allocation': 0.0,
            'last_update_time': self.current_time,
            'history_time': [],
            'history_bid': [],
            'history_alloc': [],
            'is_test_subject': False
        }
        
        stay_duration = random.expovariate(self.config['PLAYER_DEPARTURE_RATE'])
        self.schedule_event(self.current_time + stay_duration, "PLAYER_DEPARTURE", {'pid': pid})
        
        next_arrival_time = self.current_time + random.expovariate(self.config['PLAYER_ARRIVAL_RATE'])
        if next_arrival_time < self.config['SIM_MAX_TIME']:
            self.schedule_event(next_arrival_time, "PLAYER_ARRIVAL", {})
        
        self.notify_all_players_to_revise()

    def handle_player_departure(self, data):
        pid = data['pid']
        if pid not in self.players: return

        # PROTECT TEST SUBJECTS
        if self.players[pid].get('is_test_subject') and not data.get('force', False):
            return 

        player = self.players[pid]
        self.update_player_integrals()
        
        final_utility = 0.0
        if player['bid'] >= self.config['EPSILON']:
            current_total_bid = self.get_total_bid()
            s_total = current_total_bid + self.config['DELTA']
            if s_total > 0:
                allocation = player['bid'] / s_total
                final_utility = utility(player['a'], allocation, self.current_price, player['bid'], self.config['ALPHA'])
        
        time_in_system = self.current_time - player['arrival_time']
        avg_allocation = (player['integral_allocation'] / time_in_system) if time_in_system > 0 else 0
        
        self.departed_player_data.append({
            'pid': pid,
            'a_val': player['a'],
            'arrival_time': player['arrival_time'],
            'time_in_system': time_in_system,
            'total_cost': player['integral_cost'],
            'avg_allocation_pct': avg_allocation * 100,
            'final_utility': final_utility,
            'history_time': player['history_time'],
            'history_bid': player['history_bid'],
            'history_alloc': player['history_alloc']
        })
        self.completed_player_count += 1
        self.players.pop(pid)
        self.notify_all_players_to_revise()

    def handle_player_bid_revision(self, data):
        pid = data['pid']
        if pid not in self.players: return

        self.update_player_integrals()
        player = self.players[pid]
        
        current_total_bid = self.get_total_bid()
        s_minus = current_total_bid - player['bid'] + self.config['DELTA']
        # Floating point safety
        s_minus = max(self.config['DELTA'], s_minus)
        
        strategy = self.config.get('STRATEGY', 'BEST_RESPONSE')
        
        if strategy == 'GRADIENT':
             new_bid = gradient_descent_bid(
                 player['bid'], player['a'], s_minus, self.current_price, 
                 self.config['ALPHA'],
                 step_size=self.config.get('LEARNING_RATE', 0.5), 
                 budget=self.config['BUDGET']
             )
        else:
            new_bid = best_response(player['a'], s_minus, self.current_price, self.config['ALPHA'])
        
        if self.current_price > 1e-9:
             max_bid = self.config['BUDGET'] / self.current_price
             new_bid = min(new_bid, max_bid)
        
        player['bid'] = new_bid

    def handle_price_adjustment(self, data):
        current_total_bid = self.get_total_bid()
        util_now = self.get_utilization(current_total_bid)
        err = util_now - self.config['TARGET_UTILIZATION']
        new_price = self.current_price * (1 + self.config['K_PRICE'] * err)
        self.current_price = max(self.config['MIN_PRICE'], min(self.config['MAX_PRICE'], new_price))
        
        self.notify_all_players_to_revise()
        
        next_adjust = self.current_time + self.config['PRICE_ADJUST_INTERVAL']
        if next_adjust < self.config['SIM_MAX_TIME']:
            self.schedule_event(next_adjust, "PRICE_ADJUSTMENT", {})

    def notify_all_players_to_revise(self):
        for pid in self.players.keys():
            delay = random.uniform(self.config['BID_REVISION_DELAY_MIN'], self.config['BID_REVISION_DELAY_MAX'])
            rev_time = self.current_time + delay
            if rev_time < self.config['SIM_MAX_TIME']:
                self.schedule_event(rev_time, "PLAYER_BID_REVISION", {'pid': pid})

    def update_player_integrals(self):
        time_delta = self.current_time - self.last_stats_update_time
        if time_delta <= 0: return
        
        current_total_bid = self.get_total_bid()
        s_total = current_total_bid + self.config['DELTA']

        for pid, player in self.players.items():
            cost_this_interval = player['bid'] * self.current_price * time_delta
            player['integral_cost'] += cost_this_interval
            
            current_alloc = 0
            if s_total > 0 and player['bid'] > 0:
                current_alloc = player['bid'] / s_total
            
            player['integral_allocation'] += current_alloc * time_delta
            player['last_update_time'] = self.current_time

            # RECORD HISTORY: Force record if test subject to get smooth plots
            if player.get('is_test_subject') or (self.current_time - player['history_time'][-1] > 1.0 if player['history_time'] else True):
                player['history_time'].append(self.current_time)
                player['history_bid'].append(player['bid'])
                player['history_alloc'].append(current_alloc)

    def update_stats(self):
        time_delta = self.current_time - self.last_stats_update_time
        if time_delta <= 0: return
            
        player_count = len(self.players)
        current_total_bid = self.get_total_bid()
        current_utilization = self.get_utilization(current_total_bid)
        current_avg_bid = (current_total_bid / player_count) if player_count > 0 else 0.0
        
        current_social_welfare = 0.0
        s_total = current_total_bid + self.config['DELTA']
        
        if player_count > 0 and s_total > 0:
            for pid, player in self.players.items():
                if player['bid'] < self.config['EPSILON']:
                    player_utility = 0.0
                else:
                    allocation = player['bid'] / s_total
                    player_utility = utility(player['a'], allocation, self.current_price, player['bid'], self.config['ALPHA'])
                current_social_welfare += player_utility
        
        current_avg_utility = (current_social_welfare / player_count) if player_count > 0 else 0.0

        self.integral_player_count += player_count * time_delta
        self.integral_utilization += current_utilization * time_delta
        self.integral_avg_bid += current_avg_bid * time_delta
        self.integral_social_welfare += current_social_welfare * time_delta
        self.integral_avg_utility += current_avg_utility * time_delta
        
        self.stats_player_count.append((self.current_time, player_count))
        self.stats_utilization.append((self.current_time, current_utilization))
        self.stats_avg_bid.append((self.current_time, current_avg_bid))
        self.stats_social_welfare.append((self.current_time, current_social_welfare))
        self.stats_avg_utility_timeseries.append((self.current_time, current_avg_utility))
        self.stats_price.append((self.current_time, self.current_price))
        
        self.last_stats_update_time = self.current_time

    def run(self):
        print(f"--- Simulation Starting for {self.config['LABEL']} ---")
        random.seed(self.config['SEED'])
        
        # 1. Spawn Immortals (Test Subjects)
        self.spawn_test_subjects()
        
        # 2. Start Randoms
        self.schedule_event(0.0, "PLAYER_ARRIVAL", {})
        if self.config['DYNAMIC_PRICING']:
            self.schedule_event(self.config['PRICE_ADJUST_INTERVAL'], "PRICE_ADJUSTMENT", {})
        
        while self.event_queue:
            # FIX: Unpack 4 values (Time, UniqueID, Type, Data)
            event_time, _, event_type, data = heapq.heappop(self.event_queue)
            
            if event_time > self.config['SIM_MAX_TIME']:
                print(f"--- Simulation End at T={self.current_time:.2f} ---")
                break
            
            self.update_player_integrals()
            self.update_stats()
            self.current_time = event_time
            
            if event_type == "PLAYER_ARRIVAL": self.handle_player_arrival(data)
            elif event_type == "PLAYER_DEPARTURE": self.handle_player_departure(data)
            elif event_type == "PLAYER_BID_REVISION": self.handle_player_bid_revision(data)
            elif event_type == "PRICE_ADJUSTMENT": self.handle_price_adjustment(data)
        
        # 3. Force Depart Immortals to save their data
        for pid in self.test_subjects:
            self.handle_player_departure({'pid': pid, 'force': True})
            
        self.update_stats()
        print(f"Processed {self.next_pid} arrivals and {self.completed_player_count} departures.")

    def get_summary_stats(self):
        if self.current_time == 0: return {}
        final_utilities = [p['final_utility'] for p in self.departed_player_data]
        avg_utility_final = statistics.mean(final_utilities) if final_utilities else 0.0
        std_dev_utility = statistics.stdev(final_utilities) if len(final_utilities) > 1 else 0.0

        return {
            "avg_player_count": self.integral_player_count / self.current_time,
            "avg_utilization": self.integral_utilization / self.current_time,
            "avg_bid": self.integral_avg_bid / self.current_time,
            "avg_social_welfare": self.integral_social_welfare / self.current_time,
            "avg_satisfaction": self.integral_avg_utility / self.current_time,
            "avg_utility_final": avg_utility_final,
            "std_dev_utility": std_dev_utility
        }