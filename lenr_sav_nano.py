import numpy as np
from scipy.integrate import odeint
from scipy.optimize import fsolve
import matplotlib.pyplot as plt

# =============================================
# Physical constants and parameters
# =============================================
r_dd = 2.75e-10          # Fixed D-D separation in SAV (m)
lambda_b = 0.577e-10     # Bulk Thomas-Fermi screening length (m)
E_th = 0.0388            # Thermal energy at 300K (eV = 38.8 meV)
x_0 = 0.1e-10            # Scaling length for oscillation amplitude (m)
omega_0 = 1e14           # Approximate vibration frequency (rad/s)

# =============================================
# Resonance ODE model (coupled oscillators)
# =============================================
def resonance_ode(y, tau, detune, g, k, A, om_d):
    X1, V1, X2, V2 = y
    dX1 = V1
    dV1 = -X1 - g * V1 - k * (X1 - X2)
    dX2 = V2
    dV2 = -detune**2 * X2 - g * V2 - k * (X2 - X1) + A * np.sin(om_d * tau)
    return [dX1, dV1, dX2, dV2]

# =============================================
# Run resonance simulation
# =============================================
def run_resonance(surface_factor=1.0, detune=1.05, g=0.01, k=0.1, A=0.1, om_d=None, plot=False):
    lambda_TF = lambda_b / np.sqrt(surface_factor)
    if om_d is None:
        om_d = (1 + detune) / 2
    
    tau = np.linspace(0, 200, 20000)  # Dimensionless time
    y0 = [1.0, 0.0, 0.0, 0.0]        # Initial conditions
    
    sol = odeint(resonance_ode, y0, tau, args=(detune, g, k, A, om_d), rtol=1e-6)
    
    dd_dist = np.abs(sol[:, 0] - sol[:, 2]) * x_0
    peak_amp = np.max(np.abs(sol[:, 0])) * x_0
    min_dd = np.min(dd_dist)
    
    # Avoid unphysical zero separation
    effective_min = max(min_dd, 0.1e-10)  # Minimum physical separation ~0.1 Å
    delta_r = r_dd - effective_min
    rate_boost = np.exp(delta_r / lambda_TF)
    
    if plot:
        t_ps = tau / omega_0 * 1e12  # Convert to picoseconds
        plt.figure(figsize=(10, 6))
        plt.plot(t_ps, sol[:, 0] * x_0 * 1e10, label='D1 position (Å)')
        plt.plot(t_ps, sol[:, 2] * x_0 * 1e10, label='D2 position (Å)')
        plt.xlabel('Time (ps)')
        plt.ylabel('Position deviation (Å)')
        plt.title(f'Resonance Trajectory (detune={detune:.2f}, boost={rate_boost:.1e})')
        plt.legend()
        plt.grid(True)
        plt.savefig('resonance_trajectory.png')
        plt.close()
    
    return peak_amp * 1e10, effective_min * 1e10, rate_boost

# =============================================
# Bundle-inspired topological boost (proxy)
# =============================================
def bundle_alpha_boost(base_alpha, fiber_dim=14, base_dim=4):
    alpha_vals = [base_alpha] * base_dim + [1 / base_alpha] * (fiber_dim - base_dim)
    M = np.diag(alpha_vals)
    tr_M = np.trace(M)
    M_tl = M - (tr_M / fiber_dim) * np.eye(fiber_dim)
    det_tl = np.linalg.det(M_tl)
    boost = max(1.0, np.abs(det_tl)**(1 / fiber_dim))
    return boost

# =============================================
# Barrier elimination equation
# =============================================
def barrier_eq(alpha, surface_factor=1.0, bundle_boost=1.0):
    eff_alpha = alpha * surface_factor * bundle_boost
    V_scr = (1.44e-9 / r_dd) * np.exp(-r_dd * np.sqrt(eff_alpha) / lambda_b)  # eV
    return V_scr - E_th

# =============================================
# Main demonstration run (nano case)
# =============================================
if __name__ == "__main__":
    surface_factor = 10.0    # Nano-enhancement
    base_alpha = 1.5         # Conservative base
    bundle_boost = bundle_alpha_boost(base_alpha)
    
    alpha_min = fsolve(barrier_eq, 1.0, args=(surface_factor, bundle_boost))[0]
    
    print(f"Nano-boosted alpha_min for barrier elimination: {alpha_min:.2f}")
    print(f"Bundle boost factor: {bundle_boost:.2f}")
    
    # Resonance sweep
    detunes = np.linspace(0.95, 1.05, 20)
    boosts = []
    for d in detunes:
        _, _, boost = run_resonance(surface_factor=surface_factor, detune=d)
        boosts.append(boost)
    
    max_boost = max(boosts)
    print(f"Maximum resonance rate boost (nano): {max_boost:.1e}")
    
    # Optional: Generate example plot
    run_resonance(surface_factor=surface_factor, detune=1.00, plot=True)
    print("Example plot saved as 'resonance_trajectory.png'")
