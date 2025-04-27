import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Drug Release Data Tool", layout="wide")

st.title("💊 Drug Release Profile Entry and Plotting")

st.markdown("""
### 🧪 Welcome!
In this app, you will:
- Enter drug release data for multiple samples.
- Visualize how the drug is released over time.

You might have **6 to 10 different drug release profiles**, and each profile might have **10 to 15 time points**. Don't worry if the exact timing varies slightly between profiles.
""")

st.markdown("---")

st.header("📋 Step 1: Enter Your Drug Release Data")

st.markdown("""
Each column should represent one drug release profile. You can rename the columns with sample names if you like.
- **Time (hours)** should be your first column.
- **Release (%)** values go into the other columns.

Start with some default empty data and adjust as needed:
""")

# Default template for students
default_data = {
    "Time (h)": list(range(0, 10)),
    "Sample 1": ["" for _ in range(10)],
    "Sample 2": ["" for _ in range(10)],
    "Sample 3": ["" for _ in range(10)]
}

release_df = pd.DataFrame(default_data)
release_df = st.data_editor(release_df, num_rows="dynamic", key="release_data")

st.markdown("---")

st.header("📈 Step 2: Visualize Your Release Profiles")

# Only plot if 'Time (h)' is provided and at least one sample has data
try:
    time_points = release_df["Time (h)"].astype(float)
    fig, ax = plt.subplots()
    
    for col in release_df.columns:
        if col != "Time (h)":
            try:
                ax.plot(time_points, pd.to_numeric(release_df[col], errors='coerce'), marker='o', label=col)
            except:
                pass
    
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("% Drug Released")
    ax.set_title("Drug Release Profiles")
    ax.legend()
    st.pyplot(fig)
except Exception as e:
    st.warning("Please make sure 'Time (h)' column has valid numeric values.")

st.markdown("---")

st.header("📝 Reflection")

st.text_area("1. Which sample released drug the fastest? How can you tell?")
st.text_area("2. Did any sample show a burst release (very fast early release)?")
st.text_area("3. What differences or patterns do you notice between the samples?")

st.success("Great job visualizing your experimental data!")
