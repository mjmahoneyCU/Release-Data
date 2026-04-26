import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# --- CONFIG ---
st.set_page_config(page_title="Release Curve Analyzer", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
h2, h3 {
    color: #1a1a1a;
    border-bottom: 2px solid #CFB87C;
    padding-bottom: 0.25rem;
}
.stButton > button {
    background-color: #CFB87C;
    color: #000000;
    border: none;
    font-weight: 600;
}
.stButton > button:hover {
    background-color: #b8a269;
    color: #000000;
}
</style>
""", unsafe_allow_html=True)

# --- DEPARTMENT BANNER ---
import base64
with open("CBEN.png", "rb") as _banner_file:
    _banner_b64 = base64.b64encode(_banner_file.read()).decode()
st.markdown(
    f"""
    <div style="background-color: #000000; padding: 0.5rem 1.5rem; margin-bottom: 1rem; border-radius: 4px;">
        <img src="data:image/png;base64,{_banner_b64}" style="height: 80px; display: block;" />
    </div>
    """,
    unsafe_allow_html=True,
)

# --- PAGE TITLE ---
st.title("Release Curve Analyzer")


# --- STEP 1: STANDARD CURVE EQUATION ---
st.header("Step 1: Enter Your Standard Curve Equation")

st.markdown("""
Your standard curve from Monday gives you the equation to convert absorbance into concentration. Enter the slope and y-intercept from your Standard Curve Tool here.
""")

with st.expander("Where do I find these numbers?", expanded=False):
    st.markdown("""
Look at the Step 3 results in your **Standard Curve Tool** (the app you used Monday). You'll see three metric cards: **Slope (m)**, **Y-intercept (b)**, and **R²**. Copy the values into the boxes below.

The equation your curve gave you is:
""")
    st.latex(r"A = m \times C + b")
    st.markdown("""
The app will use this equation to convert each of your absorbance readings into a concentration:
""")
    st.latex(r"C = \frac{A - b}{m}")

curve_cols = st.columns(2)
slope = curve_cols[0].number_input(
    "Slope (m)",
    value=0.001,
    format="%.5f",
    step=0.0001,
    help="From Monday's Standard Curve Tool. Should be a small positive number (roughly 0.0001 to 0.01)."
)
intercept = curve_cols[1].number_input(
    "Y-intercept (b)",
    value=0.0,
    format="%.4f",
    step=0.001,
    help="From Monday's Standard Curve Tool. Should be a small number near zero."
)

if slope <= 0:
    st.error("Slope must be positive. Check your Standard Curve Tool results.")
    st.stop()

st.markdown("---")


# --- STEP 2: EXPERIMENT TYPE ---
st.header("Step 2: Choose Your Experiment Type")

experiment_type = st.radio(
    "Which experiment are you analyzing?",
    [
        "Tuesday — Franz Cell (sample returned to receptor; receptor volume stays constant)",
        "Wednesday — Patch Mimic (patch moves to fresh compartment each time point)"
    ],
    key="experiment_type"
)

is_tuesday = experiment_type.startswith("Tuesday")

with st.expander("Why does this matter?", expanded=False):
    st.markdown("""
The math for cumulative release depends on how you sampled.

**Tuesday (Franz cell):** You sampled 1 mL, measured absorbance, then returned the sample to the receptor. The receptor volume stays constant, so the concentration you measure at each time point directly reflects how much dye has accumulated in the receptor since t = 0. Cumulative release = concentration × receptor volume.

**Wednesday (Patch mimic):** The patch moved to a fresh water compartment at each time point. Each measurement represents release during that single interval, not the total. Cumulative release = sum of (concentration × compartment volume) across all intervals.
""")

volume_label = "Receptor volume (mL)" if is_tuesday else "Compartment volume (mL)"
default_volume = 30.0 if is_tuesday else 60.0
sample_volume = st.number_input(
    volume_label,
    value=default_volume,
    min_value=1.0,
    step=1.0,
    help=f"The volume of water in each {'Franz cell receptor' if is_tuesday else 'patch compartment'}. Check your protocol."
)

st.markdown("---")


# --- STEP 3: SAMPLE SETUP ---
st.header("Step 3: Set Up Your Samples")

num_samples = st.selectbox(
    "How many samples (chambers) are you analyzing?",
    list(range(1, 7)),
    index=5  # default to 6
)

st.markdown(f"Enter each sample's name and time-absorbance data below. Leave unused time rows blank.")

all_samples = []

sample_tabs = st.tabs([f"Sample {i+1}" for i in range(num_samples)])

for i, tab in enumerate(sample_tabs):
    with tab:
        sample_name = st.text_input(
            "Sample name (from your experimental design):",
            value=f"Chamber {i+1}",
            key=f"name_{i}"
        )

        df_data = pd.DataFrame({
            "Time (min)": [np.nan] * 15,
            "Absorbance": [np.nan] * 15
        })

        edited = st.data_editor(
            df_data,
            num_rows="dynamic",
            key=f"data_{i}",
            use_container_width=True
        )

        # Clean data
        edited["Time (min)"] = pd.to_numeric(edited["Time (min)"], errors='coerce')
        edited["Absorbance"] = pd.to_numeric(edited["Absorbance"], errors='coerce')
        clean = edited.dropna(subset=["Time (min)", "Absorbance"]).sort_values("Time (min)").reset_index(drop=True)

        if len(clean) == 0:
            st.info("Enter time and absorbance values above to see your release curve.")
            all_samples.append({"name": sample_name, "data": None})
            continue

        # Calculate concentration
        clean["Concentration (µg/mL)"] = ((clean["Absorbance"] - intercept) / slope).clip(lower=0)

        # Calculate cumulative release based on experiment type
        if is_tuesday:
            # Concentration in receptor reflects accumulated dye directly
            clean["Cumulative release (µg)"] = clean["Concentration (µg/mL)"] * sample_volume
        else:
            # Each point is release during an interval; sum them
            clean["Interval release (µg)"] = clean["Concentration (µg/mL)"] * sample_volume
            clean["Cumulative release (µg)"] = clean["Interval release (µg)"].cumsum()

        st.dataframe(clean.round(3), use_container_width=True, hide_index=True)

        all_samples.append({"name": sample_name, "data": clean})

st.markdown("---")


# --- STEP 4: COMPARATIVE PLOT ---
valid_samples = [s for s in all_samples if s["data"] is not None and len(s["data"]) > 1]

if len(valid_samples) == 0:
    st.info("Enter data for at least one sample to see the release curve.")
    st.stop()

st.header("Step 4: Compare Your Release Curves")

colors = ["#4A90E2", "#CFB87C", "#D62728", "#2CA02C", "#9467BD", "#8C564B"]

fig, ax = plt.subplots(figsize=(10, 5))
for i, sample in enumerate(valid_samples):
    df = sample["data"]
    ax.plot(df["Time (min)"], df["Cumulative release (µg)"],
            marker='o', linewidth=2, markersize=6,
            color=colors[i % len(colors)], label=sample["name"])

ax.set_xlabel("Time (min)", fontsize=11)
ax.set_ylabel("Cumulative release (µg)", fontsize=11)
ax.grid(True, linestyle=':', alpha=0.4)
ax.legend(loc='best', fontsize=9, framealpha=0.95)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
st.pyplot(fig)
plt.close(fig)


# --- STEP 5: RELEASE RATE ANALYSIS ---
st.header("Step 5: Calculate Release Rate")

st.markdown("""
Every release curve typically has three phases:

- **Lag phase** — flat or slow release at the start, while the drug loads into the membrane
- **Steady-state release** — linear climb, the drug is moving through at a constant rate
- **Depletion or saturation** — flattening at the end, the reservoir is running out or the receptor is saturating

The **release rate** (µg/min) is the slope of the steady-state portion of the curve. For each sample, pick the time window where your curve looks most linear.
""")

rate_results = []

for i, sample in enumerate(valid_samples):
    df = sample["data"]
    st.subheader(sample["name"])

    times = df["Time (min)"].values
    cum_release = df["Cumulative release (µg)"].values

    if len(times) < 3:
        st.info("Need at least 3 time points to fit a release rate.")
        continue

    time_options = sorted(times.tolist())

    rate_cols = st.columns(2)
    start_time = rate_cols[0].selectbox(
        "Start of steady-state (min):",
        options=time_options,
        index=0,
        key=f"rate_start_{i}"
    )
    end_time = rate_cols[1].selectbox(
        "End of steady-state (min):",
        options=time_options,
        index=len(time_options) - 1,
        key=f"rate_end_{i}"
    )

    if end_time <= start_time:
        st.warning("End time must be after start time.")
        continue

    mask = (times >= start_time) & (times <= end_time)
    x_fit = times[mask]
    y_fit = cum_release[mask]

    if len(x_fit) < 2:
        st.warning("Select a window with at least 2 time points.")
        continue

    m, b, r, _, _ = linregress(x_fit, y_fit)
    r_squared = r ** 2

    metric_cols = st.columns(3)
    metric_cols[0].metric("Release rate", f"{m:.2f} µg/min")
    metric_cols[1].metric("R² of fit", f"{r_squared:.3f}")
    metric_cols[2].metric("Window", f"{int(start_time)}–{int(end_time)} min")

    if r_squared < 0.9:
        st.warning(f"R² = {r_squared:.3f} is low. Your selected window may not be in steady-state. Try narrowing the window.")
    else:
        st.success(f"R² = {r_squared:.3f} — clean linear fit. The release rate for this window is reliable.")

    # Plot this sample with fit overlay
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(times, cum_release, 'o-', color=colors[i % len(colors)],
            markersize=6, linewidth=1.5, alpha=0.5, label='All data')
    ax.plot(x_fit, y_fit, 'o', color=colors[i % len(colors)],
            markersize=9, label='Steady-state window')
    fit_line_x = np.array([start_time, end_time])
    fit_line_y = m * fit_line_x + b
    ax.plot(fit_line_x, fit_line_y, '--', color='#000000', linewidth=2,
            label=f'Fit: {m:.2f} µg/min')
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Cumulative release (µg)")
    ax.set_title(sample["name"])
    ax.legend(loc='best', fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    st.pyplot(fig)
    plt.close(fig)

    rate_results.append({
        "Sample": sample["name"],
        "Release rate (µg/min)": round(m, 2),
        "R²": round(r_squared, 3),
        "Window start (min)": int(start_time),
        "Window end (min)": int(end_time)
    })

    st.markdown("---")


# --- STEP 6: COMPARISON SUMMARY ---
if len(rate_results) > 0:
    st.header("Step 6: Compare Release Rates Across Samples")

    summary_df = pd.DataFrame(rate_results)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    if len(rate_results) > 1:
        # Identify fastest and slowest
        sorted_rates = sorted(rate_results, key=lambda x: x["Release rate (µg/min)"], reverse=True)
        fastest = sorted_rates[0]
        slowest = sorted_rates[-1]

        rate_ratio = fastest["Release rate (µg/min)"] / slowest["Release rate (µg/min)"] if slowest["Release rate (µg/min)"] > 0 else float('inf')

        st.markdown(f"""
- **Fastest release:** {fastest['Sample']} at **{fastest['Release rate (µg/min)']} µg/min**
- **Slowest release:** {slowest['Sample']} at **{slowest['Release rate (µg/min)']} µg/min**
- **Ratio:** Fastest is **{rate_ratio:.1f}×** faster than slowest
""")

        if rate_ratio > 2:
            st.info("Release rates differ by more than 2×. The design changes you made had a significant effect on how fast the 'drug' crosses the membrane.")


# --- STEP 7: DOWNLOAD ---
st.markdown("---")
st.subheader("Download Your Results")

def generate_csv():
    lines = []
    lines.append(f"Release Curve Analysis")
    lines.append(f"Experiment type: {'Tuesday Franz Cell' if is_tuesday else 'Wednesday Patch Mimic'}")
    lines.append(f"Standard curve: A = {slope} * C + {intercept}")
    lines.append(f"{'Receptor' if is_tuesday else 'Compartment'} volume: {sample_volume} mL")
    lines.append("")

    for sample in valid_samples:
        lines.append(f"Sample: {sample['name']}")
        lines.append(sample["data"].round(3).to_csv(index=False))
        lines.append("")

    if len(rate_results) > 0:
        lines.append("Release Rate Summary:")
        lines.append(pd.DataFrame(rate_results).to_csv(index=False))

    return "\n".join(lines).encode("utf-8")

st.download_button(
    label="Download all data as CSV",
    data=generate_csv(),
    file_name="release_curve_analysis.csv",
    mime="text/csv"
)
