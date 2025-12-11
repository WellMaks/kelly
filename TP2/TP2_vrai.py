import simpy
import random
import matplotlib.pyplot as plt

# --- CONFIGURATION GLOBALE ---
RANDOM_SEED = 48
INTER_ARRIVAL_MEAN = 2.0  # Moyenne de temps entre arrivées
FACTOR_DURATION = 0.5     # Durée = Taille * 0.5

# Définition des 3 Scénarios (Zones)
SCENARIOS = {
    "Zone 1 (Hybride)": [
        {"id": 1, "apps": ["A", "B"], "quota": 10, "res": 1000},
        {"id": 2, "apps": ["A", "C"], "quota": 20, "res": 2500}
    ],
    "Zone 2 (Spécialisée)": [
        {"id": 1, "apps": ["A"], "quota": 10, "res": 1000},
        {"id": 2, "apps": ["B"], "quota": 10, "res": 1000},
        {"id": 3, "apps": ["C"], "quota": 10, "res": 1000}
    ],
    "Zone 3 (Centralisée)": [
        {"id": 1, "apps": ["A", "B", "C"], "quota": 30, "res": 3000}
    ]
}

# --- CLASSES DU SYSTÈME ---

class Flow:
    def __init__(self, flow_id, time):
        self.id = flow_id
        self.arrival_time = time
        # Génération Classe (33% A, 33% B, 33% C)
        r = random.random()
        if r < 0.33: self.app_class = "A"
        elif r < 0.66: self.app_class = "B"
        else: self.app_class = "C"
        
        self.size = random.randint(10, 300)
        self.duration = self.size * FACTOR_DURATION

class Server:
    def __init__(self, env, config, check_stop_callback):
        self.env = env
        self.id = config["id"]
        self.apps = config["apps"]
        self.quota_limit = config["quota"]
        self.initial_res = config["res"]
        self.check_stop_callback = check_stop_callback
        
        # Gestion Mono-tâche
        self.processor = simpy.Resource(env, capacity=1)
        
        # Gestion Ressources
        self.current_res = self.initial_res
        self.admitted_count = 0
        
        # Logs pour console et graphes
        self.admitted_logs = []
        
        self.history_time = [0]
        self.history_res = [self.initial_res]
        self.history_admitted = [0]
        self.rejections = {"A": 0, "B": 0, "C": 0}

    def is_alive(self):
        if self.admitted_count >= self.quota_limit: return False
        if self.current_res < 10: return False
        return True

    def process_flow(self, flow):
        # 1. Check App
        if flow.app_class not in self.apps:
            self.rejections[flow.app_class] += 1
            return False
        
        # 2. Check Busy
        if self.processor.count == self.processor.capacity:
            self.rejections[flow.app_class] += 1
            return False
        
        # 3. Check Resources
        if self.current_res < flow.size:
            self.rejections[flow.app_class] += 1
            return False
            
        # 4. Check Quota
        if self.admitted_count >= self.quota_limit:
            self.rejections[flow.app_class] += 1
            return False

        # --- ADMISSION ---
        self.env.process(self._execute(flow))
        return True

    def _execute(self, flow):
        with self.processor.request() as req:
            yield req
            
            # Consommation immédiate
            self.current_res -= flow.size
            self.admitted_count += 1
            
            # LOGGING pour le tableau
            self.admitted_logs.append({
                "id": flow.id,
                "class": flow.app_class,
                "size": flow.size,
                "arrival": flow.arrival_time,
                "res_after": self.current_res
            })
            
            self.record_stats()
            
            # Temps de traitement
            yield self.env.timeout(flow.duration)
            
            self.record_stats()
            self.check_stop_callback()

    def record_stats(self):
        self.history_time.append(self.env.now)
        self.history_res.append(self.current_res)
        self.history_admitted.append(self.admitted_count)

# --- MOTEUR DE SIMULATION ---

def traffic_generator(env, servers, stop_event):
    flow_id = 0
    while not stop_event.triggered:
        yield env.timeout(random.expovariate(1.0 / INTER_ARRIVAL_MEAN))
        flow_id += 1
        flow = Flow(flow_id, env.now)
        
        target = random.choice(servers)
        target.process_flow(flow)
        
        if all(not s.is_alive() for s in servers) and not stop_event.triggered:
            stop_event.succeed()

def run_zone_simulation(zone_name, server_configs):
    print(f"Calcul en cours pour : {zone_name}...")
    random.seed(RANDOM_SEED)
    
    env = simpy.Environment()
    stop_event = env.event()
    
    def check_stop():
        if all(not s.is_alive() for s in servers) and not stop_event.triggered:
            stop_event.succeed()

    servers = [Server(env, cfg, check_stop) for cfg in server_configs]
    env.process(traffic_generator(env, servers, stop_event))
    
    env.run(until=stop_event)
    return servers

# --- AFFICHAGE TABLEAUX (LOGS) ---

def print_multi_zone_logs(all_results):
    for zone_name, servers in all_results.items():
        print(f"\n{'='*80}")
        print(f" RAPPORTS DÉTAILLÉS : {zone_name.upper()}")
        print(f"{'='*80}")
        
        for s in servers:
            print(f"\n -> SERVER {s.id} (Apps: {','.join(s.apps)}) | Admis: {s.admitted_count}/{s.quota_limit} | Res: {s.current_res}")
            print(f" {'-'*63}")
            print(f" | {'Flux ID':^8} | {'Classe':^6} | {'Taille':^8} | {'Arrivée':^8} | {'Res. Rest':^9} |")
            print(f" {'-'*63}")
            
            if not s.admitted_logs:
                print(f" | {'AUCUN FLUX ADMIS':^61} |")
            else:
                for log in s.admitted_logs:
                    print(f" | {log['id']:^8} | {log['class']:^6} | {log['size']:^8} | {log['arrival']:^8.2f} | {log['res_after']:^9} |")
            
            print(f" {'-'*63}")
            
            # Petit bilan des rejets pour ce serveur
            total_rejets = sum(s.rejections.values())
            print(f" [Stats Rejets] A: {s.rejections['A']}, B: {s.rejections['B']}, C: {s.rejections['C']} (Total: {total_rejets})")

# --- AFFICHAGE GRAPHIQUE ---

def plot_all_zones(results):
    cols = len(results)
    rows = 3
    fig, axs = plt.subplots(rows, cols, figsize=(18, 12), constrained_layout=True)
    
    zone_names = list(results.keys())

    for col_idx, zone_name in enumerate(zone_names):
        servers = results[zone_name]
        
        # Ligne 1 : Flux Admis
        ax1 = axs[0, col_idx]
        total_admitted = 0
        quota_total = 0
        for s in servers:
            ax1.plot(s.history_time, s.history_admitted, label=f"S{s.id}", drawstyle='steps-post')
            total_admitted += s.admitted_count
            quota_total += s.quota_limit
            
        ax1.set_title(f"{zone_name}\nFlux Admis (Total: {total_admitted}/{quota_total})", fontweight='bold')
        ax1.set_xlabel("Temps (s)")
        ax1.grid(True, alpha=0.3)
        if col_idx == 0: ax1.set_ylabel("Flux Admis")
        ax1.legend(fontsize=8)

        # Ligne 2 : Ressources
        ax2 = axs[1, col_idx]
        for s in servers:
            ax2.plot(s.history_time, s.history_res, label=f"S{s.id}", drawstyle='steps-post')
        
        ax2.set_title("Ressources Restantes")
        ax2.set_xlabel("Temps (s)")
        ax2.grid(True, alpha=0.3)
        if col_idx == 0: ax2.set_ylabel("Ressources")

        # Ligne 3 : Rejets
        ax3 = axs[2, col_idx]
        labels = ["A", "B", "C"]
        x = range(len(labels))
        width = 0.8 / len(servers)
        
        for i, s in enumerate(servers):
            rejets = [s.rejections["A"], s.rejections["B"], s.rejections["C"]]
            pos = [p + i * width - (len(servers)*width)/2 + width/2 for p in x]
            ax3.bar(pos, rejets, width, label=f"S{s.id}")
            
        ax3.set_title("Rejets par Classe")
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels)
        if col_idx == 0: ax3.set_ylabel("Nb Rejets")
        ax3.legend(fontsize=8)

    plt.suptitle("Simulation Multi-Zones : Hybride vs Spécialisée vs Centralisée", fontsize=16)
    plt.show()

# --- MAIN ---

if __name__ == "__main__":
    all_results = {}
    
    # Exécution des simulations
    for name, config in SCENARIOS.items():
        all_results[name] = run_zone_simulation(name, config)
    
    # 1. Affichage des tableaux dans le terminal
    print_multi_zone_logs(all_results)
    
    # 2. Affichage des graphiques
    plot_all_zones(all_results)