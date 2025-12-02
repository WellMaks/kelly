"""
Core Logic File
---------------
Mathematical implementation of the Kelly Mechanism and Best Response.
"""
import math
from config import BASE_CONFIG

def best_response(a, s_minus, lam, alpha):
    if lam <= 1e-6: lam = 1e-6 
    
    if alpha == 0:
        term = (a * s_minus) / lam
        if term < 0: term = 0
        z = math.sqrt(term) - s_minus
    elif alpha == 1:
        discriminant = s_minus**2 + 4.0 * (a * s_minus / lam)
        z = (-s_minus + math.sqrt(discriminant)) / 2.0
    elif alpha == 2:
        term = (a * s_minus) / lam
        if term < 0: term = 0
        z = math.sqrt(term) 
    else:
        z = 0.1 # Fallback
        
    return max(BASE_CONFIG['EPSILON'], z)

def gradient_descent_bid(current_bid, a, s_minus, lam, alpha, step_size=0.1, budget=4000):
    if lam <= 0: lam = BASE_CONFIG['EPSILON']
    s_total = current_bid + s_minus
    if s_total <= 0: return max(current_bid, BASE_CONFIG['EPSILON'])
    
    x = current_bid / s_total
    
    if x <= 1e-9: marginal_val = 1e6
    else: marginal_val = a * (x ** (-alpha))
    
    dx_dz = s_minus / (s_total**2)
    gradient = (marginal_val * dx_dz) - lam
    new_bid = current_bid + (step_size * gradient)
    
    max_bid = budget / lam
    return max(BASE_CONFIG['EPSILON'], min(new_bid, max_bid))

def utility(a, x, lam, z, alpha):
    if x <= 1e-9: return -100.0
    if alpha == 1: val = a * math.log(x)
    else: val = a * (x**(1-alpha)) / (1-alpha)
    return val - (lam * z)