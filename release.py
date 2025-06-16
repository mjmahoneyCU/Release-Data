import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

# --- CONFIG ---
st.set_page_config(page_title="Biotech Release Curve Analysis", layout="wide")
st.title("Standard Curve & Release Curve Analysis Tool")

st.markdown(r"""
Welcome to the Release Analysis Tool! This app will help you:
1. Build a **standard curve** from known concentrations and their absorbance.
2. Use your standard curve to calculate the concentration of **unknown release samples**.
3. Construct a **cumulative release curve** to visualize your experiment's results.
""")

st.markdown("---")

# --- SECTION 1: STANDARD CURVE ---
st.header("📈 Step 1: Build Your Standard Curve")
st.markdown(r"""
Enter the known concentrations of your standards and their corresponding absorbance values below.

### What is a Standard Curve?
A standard curve is a line that shows the relationship between how much substance is in your sample (concentration) and how much light it absorbs (absorbance).

**Standard Curve Equation:**
$$A = m \times C + b$$
Where:
- \( A \) is Absorbance (AU)
- \( C \) is Concentration (\mu g/mL)
- \( m \) is the slope of the line
- \( b \) is the y-intercept
""")

with st.expander("Enter your Standard Curve Data", expanded=True):
    df_std = pd.DataFrame({
        "Concentration (µg/mL)": [0.00, 10.00, 25.00, 50.00, 100.00, 200.00],
        "Absorbance (AU)": [0.00, 0.05, 0.12, 0.25, 0.50, 1.00]
    })
    edited_std_df = st.data_editor(df_std, num_rows="dynamic", key="std_editor")

x_std = pd.to_numeric(edited_std_df["Concentration (µg/mL)"], errors='coerce').dropna().values
y_std = pd.to_numeric(edited_std_df["Absorbance (AU)"], errors='coerce').dropna().values

if len(x_std) >= 2:
    slope, intercept, r_value, _, _ = linregress(x_std, y_std)
    st.success(f"**Standard Curve Equation:** A = {slope:.4f} × C + {intercept:.4f}")
    st.info(f"R-squared = {r_value**2:.4f}.")
    fig_std, ax_std = plt.subplots(figsize=(8, 4))
    ax_std.plot(x_std, y_std, 'o', label='Data')
    ax_std.plot(x_std, slope * x_std + intercept, 'r-', label='Fit')
    ax_std.set_xlabel("Concentration (µg/mL)")
    ax_std.set_ylabel("Absorbance (AU)")
    ax_std.set_title("Standard Curve")
    ax_std.legend()
    st.pyplot(fig_std)
else:
    st.warning("Please enter at least two valid data points to create the standard curve.")
    slope, intercept = 1.0, 0.0

st.markdown("---")

# --- SECTION 2: MULTI-SAMPLE RELEASE ANALYSIS ---
st.header("🧪 Step 2: Analyze Your Release Samples")

num_samples = st.selectbox("How many samples would you like to analyze?", list(range(1, 10)), index=2)
sample_tabs = st.tabs([f"Sample {i+1}" for i in range(num_samples)])

all_cumulative = []

for i in range(num_samples):
    with sample_tabs[i]:
        st.subheader(f"Sample {i+1} Release Data")
        df_release = pd.DataFrame({
            "Time (h)": [0, 1, 2, 4, 8, 12, 24],
            "Absorbance (AU)": [0.00]*7
        })
        df_edit = st.data_editor(df_release, key=f"release_{i}", num_rows="dynamic")

        # Convert to concentrations
        concs = (pd.to_numeric(df_edit["Absorbance (AU)"], errors='coerce') - intercept) / slope
        concs = concs.apply(lambda x: max(0.0, x))

        sample_volume = 25
        amount_released = concs * sample_volume
        cumulative_release = amount_released.cumsum()

        result_df = pd.DataFrame({
            "Time (h)": df_edit["Time (h)"],
            "Absorbance (AU)": df_edit["Absorbance (AU)"],
            "Concentration (µg/mL)": concs,
            "Amount Released (µg)": amount_released,
            "Cumulative Release (µg)": cumulative_release
        })

        st.dataframe(result_df.set_index("Time (h)"))
        all_cumulative.append((f"Sample {i+1}", result_df))

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            f"Download Sample {i+1} Data as CSV",
            csv,
            file_name=f"sample_{i+1}_release.csv",
            mime='text/csv'
        )

st.markdown("---")

# --- COMPARATIVE PLOT ---
st.subheader("📈 Comparative Plot: Cumulative Release")
if len(all_cumulative) > 1:
    fig, ax = plt.subplots(figsize=(10, 6))
    for label, df in all_cumulative:
        ax.plot(df["Time (h)"], df["Cumulative Release (µg)"], marker='o', label=label)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Cumulative Release (µg)")
    ax.set_title("Comparison of Cumulative Release Curves")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# --- REFLECTION ---
st.markdown("---")
st.header("🧠 Reflection")
st.text_area("1. What did you learn from comparing the release profiles?")
st.text_area("2. What do differences between samples suggest about release behavior?")
st.text_area("3. What steps could you take to improve the consistency or control the rate of release?")

st.success("Great job analyzing your multiple release samples!")
