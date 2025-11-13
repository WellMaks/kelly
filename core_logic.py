"""
Core Logic File
---------------
Contains the core mathematical functions from the research paper.
This separates the "math" from the "simulation engineering".
"""

import math
from config import BASE_CONFIG # Import for EPSILON

def best_response(a, s_minus, lam, alpha):
    """
    Compute best response bid for player with value 'a' given others' sum s_minus.
    Uses the correct formulas from the user's original main.py and the
    Best-Response Kelly Mechanism.pdf paper (Lemma 1).
    """
    # Ensure price (lambda) is not zero
    if lam <= 0: lam = BASE_CONFIG['EPSILON']
    
    if alpha == 0:
        z = math.sqrt(max(a * s_minus / lam, 0.0)) - s_minus
    elif alpha == 1:
        # Solves quadratic equation: z^2 + s_minus*z - (a*s_minus/lam) = 0
        disc = s_minus**2 + 4.0 * a * s_minus / lam
        z = (-s_minus + math.sqrt(disc)) / 2.0
    elif alpha == 2:
        z = math.sqrt(max(a * s_minus / lam, 0.0))
    else:
        raise ValueError(f"Unsupported alpha: {alpha}")
    
    # Return bid, clamped at a minimum value
    return max(BASE_CONFIG['EPSILON'], z)

def utility(a, x, lam, z, alpha):
    """
    Compute α-fair payoff (utility) for one player.
    Utility = Value - Cost
    """
    
    # --- Calculate Value ---
    # Handle the x=0 case to avoid math errors
    if x < 1e-9:
        if alpha == 1:
            val = a * math.log(1e-9) # Large penalty for log(0)
        else:
            # val = a * (x^(1-alpha)) / (1-alpha)
            val = a * (1e-9 ** (1 - alpha)) / (1 - alpha)
            val = max(val, -1e9) # Cap the penalty for alpha > 1
    else:
        # Standard utility formula
        if alpha == 1:
            val = a * math.log(x)
        else:
            val = a * (x ** (1 - alpha)) / (1 - alpha)
    
    # --- Return Utility (Value - Cost) ---
    cost = lam * z
    return val - cost