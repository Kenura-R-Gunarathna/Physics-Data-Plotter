# app/data_processing.py
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter


FIT_MODELS = ["None", "Exponential", "Linear", "Polynomial", "Logarithmic", "Power", "Moving Average", "Logistic"]

# --- Define Model Functions ---
def linear_model(x, m, c):
    return m * x + c

def polynomial_model(x, *coeffs):
    """coeffs are [a0, a1, a2, ...] for a0 + a1*x + a2*x^2 + ..."""
    y = np.zeros_like(x)
    for i, coeff in enumerate(coeffs):
        y += coeff * (x ** i)
    return y

def logarithmic_model(x, a, b, c):
    """y = a * ln(b*x) + c  or y = a * ln(x+b) + c"""
    return a * np.log(x + 1e-9) + b

def power_model(x, a, b, c):
    """y = a * x^b + c"""
    return a * (x ** b) + c

def logistic_model(x, l, k, x0, b):
    """
    l: maximum value (carrying capacity)

    k: growth rate

    x0: midpoint

    b: affects asymmetry, often set to 1 or related to L for simpler forms

    A common simpler form: l / (1 + exp(-k*(x-x0)))
    """
    return l / (1 + np.exp(-k * (x - x0)))

def moving_average_model(y_data, window_size, poly_order=2):
    """
    Applies a Savitzky-Golay filter, which is a type of moving average
    that can also fit a polynomial to the window.
    window_size must be odd and > poly_order.
    """
    if window_size <= poly_order:
        print(f"Warning: Moving average window_size ({window_size}) must be > poly_order ({poly_order}). Setting to poly_order+1 or +2.")
        window_size = poly_order + 1 if (poly_order + 1) % 2 != 0 else poly_order + 2
    if window_size % 2 == 0:  # Ensure odd
        window_size += 1
    if len(y_data) < window_size:
        print(f"Warning: Data length ({len(y_data)}) is less than window size ({window_size}). Returning original data.")
        return y_data
    return savgol_filter(y_data, window_size, poly_order)

def exponential_model(x, a, b):
    return a * np.exp(b * x)


def process_data(x_values, y_values, num_samples, fit_model_name="Exponential", fit_params=None):
    if fit_params is None:
        fit_params = {}

    # ... (data cleaning and interpolation - unchanged) ...
    x_values_orig = np.array(x_values, dtype=float)
    y_values_orig = np.array(y_values, dtype=float)
    mask = ~np.isnan(x_values_orig) & ~np.isnan(y_values_orig)
    x_values_clean = x_values_orig[mask]
    y_values_clean = y_values_orig[mask]
    if len(x_values_clean) < 2:
        return (x_values_orig, y_values_orig), (None, None), (None, None), "Fit Failed: Insufficient data"
    min_v, max_v = np.min(x_values_clean), np.max(x_values_clean)
    if min_v == max_v:
        if len(x_values_clean) >= 1:
            x_uniform = np.array([min_v] * num_samples)
            y_uniform = np.array([y_values_clean[0]] * num_samples)
        else:
            return (x_values_orig, y_values_orig), (None, None), (None, None), "Fit Failed: Insufficient data after cleaning"
    else:
        f_interp = interp1d(x_values_clean, y_values_clean, kind='linear', fill_value="extrapolate")
        x_uniform = np.linspace(min_v, max_v, num_samples)
        y_uniform = f_interp(x_uniform)

    y_fit = None
    label_fit = "Fit Failed"
    params_out = {}

    # --- Get p0 and maxfev from fit_params if available ---
    user_p0 = fit_params.get('p0', None)
    user_maxfev = fit_params.get('maxfev', None)  # SciPy's default will be used if None

    try:
        if fit_model_name == "Exponential":
            default_p0_exp = (1e-9, 10)
            p0_to_use = user_p0 if user_p0 is not None else default_p0_exp

            curve_fit_kwargs = {'p0': p0_to_use}
            if user_maxfev is not None and user_maxfev > 0:  # 0 might mean "SciPy default"
                curve_fit_kwargs['maxfev'] = user_maxfev
            else:  # Use a reasonable default if not specified or invalid
                curve_fit_kwargs['maxfev'] = 5000

            popt, pcov = curve_fit(exponential_model, x_uniform, y_uniform, **curve_fit_kwargs)
            y_fit = exponential_model(x_uniform, *popt)
            params_out = {'a': popt[0], 'b': popt[1]}
            label_fit = f'Exp: I = {popt[0]:.2e}·e^({popt[1]:.2f}·V)'

        elif fit_model_name == "Linear":
            curve_fit_kwargs = {}
            if user_p0 is not None:
                curve_fit_kwargs['p0'] = user_p0
            if user_maxfev is not None and user_maxfev > 0:
                curve_fit_kwargs['maxfev'] = user_maxfev

            popt, pcov = curve_fit(linear_model, x_uniform, y_uniform, **curve_fit_kwargs)
            y_fit = linear_model(x_uniform, *popt)
            params_out = {'m': popt[0], 'c': popt[1]}
            label_fit = f'Lin: I = {popt[0]:.2f}·V + {popt[1]:.2f}'

        elif fit_model_name == "Polynomial":  # Uses np.polyfit, p0/maxfev not directly applicable
            order = fit_params.get('poly_order', 2)
            if len(x_uniform) <= order:
                raise RuntimeError(f"Not enough data points ({len(x_uniform)}) for polynomial order {order}.")
            coeffs = np.polyfit(x_uniform, y_uniform, order)
            y_fit = np.polyval(coeffs, x_uniform)
            coeffs_display = coeffs[::-1]
            params_out = {f'a{i}': c for i, c in enumerate(coeffs_display)}
            terms = [f"{c:.2e}·V^{i}" for i, c in enumerate(coeffs_display)]
            label_fit = f'Poly (Ord {order}): I = {" + ".join(terms)}'.replace('V^0', '').replace('·V^1 ', '·V ')

        elif fit_model_name == "Logarithmic":
            v_shifted = x_uniform - np.min(x_uniform) + 1e-6
            default_p0_log = (np.mean(y_uniform), 1.0)  # a, b for a*log(x)+b
            p0_to_use = user_p0 if user_p0 is not None else default_p0_log

            curve_fit_kwargs = {'p0': p0_to_use}
            if user_maxfev is not None and user_maxfev > 0:
                curve_fit_kwargs['maxfev'] = user_maxfev
            else:
                curve_fit_kwargs['maxfev'] = 5000

            try:  # Attempt with shifted x first for stability if x starts near 0
                popt, pcov = curve_fit(lambda x, a, b: a * np.log(x) + b, v_shifted, y_uniform, **curve_fit_kwargs)
                y_fit = popt[0] * np.log(v_shifted) + popt[1]
            except RuntimeError:  # Fallback to original x if shifted fails or if user prefers direct fit
                popt, pcov = curve_fit(lambda x, a, b: a * np.log(x - np.min(x) + 1e-9) + b, x_uniform, y_uniform, **curve_fit_kwargs)
                y_fit = popt[0] * np.log(x_uniform - np.min(x_uniform) + 1e-9) + popt[1]

            params_out = {'a': popt[0], 'b': popt[1]}
            label_fit = f'Log: I = {popt[0]:.2f}·ln(V\') + {popt[1]:.2f}'  # V' indicates shifted V might be used

        elif fit_model_name == "Power":
            mask_pos = (x_uniform > 0) & (y_uniform > 0)
            if np.sum(mask_pos) > 2:
                log_v = np.log(x_uniform[mask_pos])
                log_i = np.log(y_uniform[mask_pos])
                coeffs_log = np.polyfit(log_v, log_i, 1)
                a_est, b_est = np.exp(coeffs_log[1]), coeffs_log[0]
                default_p0_power = (a_est, b_est, np.min(y_uniform))
            else:
                default_p0_power = (1.0, 1.0, 0.0)
            p0_to_use = user_p0 if user_p0 is not None else default_p0_power

            curve_fit_kwargs = {'p0': p0_to_use}
            if user_maxfev is not None and user_maxfev > 0:
                curve_fit_kwargs['maxfev'] = user_maxfev
            else:
                curve_fit_kwargs['maxfev'] = 5000

            popt, pcov = curve_fit(power_model, x_uniform, y_uniform, **curve_fit_kwargs)
            y_fit = power_model(x_uniform, *popt)
            params_out = {'a': popt[0], 'b': popt[1], 'c': popt[2]}
            label_fit = f'Pow: I = {popt[0]:.2e}·V^{{{popt[1]:.2f}}} + {popt[2]:.2e}'

        elif fit_model_name == "Logistic":
            L_guess = np.max(y_uniform)
            k_guess = 1.0 if y_uniform[0] < y_uniform[-1] else -1.0
            x0_guess = x_uniform[len(x_uniform) // 2]
            default_p0_logistic = (L_guess, k_guess, x0_guess)
            p0_to_use = user_p0 if user_p0 is not None else default_p0_logistic

            curve_fit_kwargs = {'p0': p0_to_use}
            if user_maxfev is not None and user_maxfev > 0:
                curve_fit_kwargs['maxfev'] = user_maxfev
            else:
                curve_fit_kwargs['maxfev'] = 8000  # Logistic often needs more

            popt, pcov = curve_fit(lambda x, L, k, x0: L / (1 + np.exp(-k * (x - x0))), x_uniform, y_uniform, **curve_fit_kwargs)
            y_fit = popt[0] / (1 + np.exp(-popt[1] * (x_uniform - popt[2])))
            params_out = {'L': popt[0], 'k': popt[1], 'x0': popt[2]}
            label_fit = f'Logis: L={popt[0]:.2e}, k={popt[1]:.2f}, V₀={popt[2]:.2f}'


        elif fit_model_name == "Moving Average":  # p0/maxfev not applicable
            period = fit_params.get('mov_avg_period', 5)
            poly_order_ma = fit_params.get('mov_avg_poly_order', 2)
            y_fit = moving_average_model(y_uniform, period, poly_order_ma)
            label_fit = f'MovAvg (P:{period}, O:{poly_order_ma})'

        elif fit_model_name == "None":
            y_fit = np.zeros_like(x_uniform)  # Or y_fit = None
            label_fit = "No Fit"

        else:
            label_fit = f"Unknown Model: {fit_model_name}"
            y_fit = np.zeros_like(x_uniform)  # Or y_fit = None

    # ... (exception handling - unchanged) ...
    except RuntimeError as e:
        print(f"RuntimeError during {fit_model_name} fit: {e}")
        label_fit = f'{fit_model_name} Fit Failed (Runtime)'
        y_fit = np.zeros_like(x_uniform)
    except TypeError as e:
        print(f"TypeError during {fit_model_name} fit (often bad p0 or data): {e}")
        label_fit = f'{fit_model_name} Fit Failed (Type)'
        y_fit = np.zeros_like(x_uniform)
    except Exception as e:  # Catch any other fitting error
        print(f"Unexpected error during {fit_model_name} fit: {e}")
        label_fit = f'{fit_model_name} Fit Failed (Error: {type(e).__name__})'
        y_fit = np.zeros_like(x_uniform)

    return (x_values_clean, y_values_clean), (x_uniform, y_uniform), (x_uniform, y_fit), label_fit