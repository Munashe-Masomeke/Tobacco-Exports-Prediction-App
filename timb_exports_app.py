import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# --- App Theme Colors (TIMB branding) ---
TIMB_GREEN = "#0B6623"
TIMB_GOLD = "#DAA520"

# --- Load Trend (from Jupyter-prepared file) ---
trend = pd.read_excel("Export_Trend_2022_2024.xlsx")
trend_dict = dict(zip(trend["Category"], trend["Pct_of_Crop"]))

# --- Load Production & Exports Data ---
df_prod = pd.read_excel("Exports_data.xlsx")[["Year", "Mass Produced"]]
df_exports = pd.read_excel("EXPORTS HISTORY.xlsx")
exp_yearly = df_exports.groupby("YEAR")["MASS EXPORTED"].sum().reset_index()
exp_yearly.rename(columns={"YEAR": "Year", "MASS EXPORTED": "Exports"}, inplace=True)

# --- Streamlit Setup ---
st.set_page_config(page_title="TIMB Tobacco Exports Prediction", page_icon="🌿", layout="wide")

# --- Header ---
st.markdown(
    f"""
    <div style="background-color:{TIMB_GREEN};padding:10px;border-radius:8px;">
        <h2 style="color:white;text-align:center;">Tobacco Industry and Marketing Board (TIMB)</h2>
        <h4 style="color:{TIMB_GOLD};text-align:center;">For Livelihoods. For Sustainability.</h4>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# --- User Input ---
st.subheader("🌿 Enter 2025 Production")
prod_2025 = st.number_input("Mass Produced (kg):", value=0, step=1_000_000)

# --- Compute Predictions for 2022–2024 ---
predictions = []
for year in range(2022, 2025):
    prod_current = df_prod.loc[df_prod["Year"] == year, "Mass Produced"].values[0] if year in df_prod["Year"].values else 0
    prod_prev1 = df_prod.loc[df_prod["Year"] == year-1, "Mass Produced"].values[0] if (year-1) in df_prod["Year"].values else 0
    prod_prev2 = df_prod.loc[df_prod["Year"] == year-2, "Mass Produced"].values[0] if (year-2) in df_prod["Year"].values else 0
    prod_prev3 = df_prod.loc[df_prod["Year"] == year-3, "Mass Produced"].values[0] if (year-3) in df_prod["Year"].values else 0

    pred = (
        prod_current * trend_dict.get("Current Crop", 0) / 100 +
        prod_prev1 * trend_dict.get("Prev-1 Crop", 0) / 100 +
        prod_prev2 * trend_dict.get("Prev-2 Crop", 0) / 100 +
        prod_prev3 * trend_dict.get("Prev-3 Crop", 0) / 100
    )
    predictions.append((year, pred))

df_pred = pd.DataFrame(predictions, columns=["Year", "Predicted"])
df_compare = exp_yearly.merge(df_pred, on="Year", how="left")

# --- Add 2025 Prediction ---
if prod_2025 > 0:
    prod_2024 = df_prod.loc[df_prod["Year"] == 2024, "Mass Produced"].values[0]
    prod_2023 = df_prod.loc[df_prod["Year"] == 2023, "Mass Produced"].values[0]
    prod_2022 = df_prod.loc[df_prod["Year"] == 2022, "Mass Produced"].values[0]

    pred_2025 = (
        prod_2025 * trend_dict.get("Current Crop", 0) / 100 +
        prod_2024 * trend_dict.get("Prev-1 Crop", 0) / 100 +
        prod_2023 * trend_dict.get("Prev-2 Crop", 0) / 100 +
        prod_2022 * trend_dict.get("Prev-3 Crop", 0) / 100
    )

    df_compare = pd.concat([
        df_compare,
        pd.DataFrame({"Year": [2025], "Exports": [None], "Predicted": [pred_2025]})
    ])

    # Highlight KPI card for 2025
    st.markdown(
        f"""
        <div style="background-color:{TIMB_GOLD};padding:10px;border-radius:8px;">
            <h3 style="color:black;text-align:center;">Predicted 2025 Exports</h3>
            <h2 style="color:{TIMB_GREEN};text-align:center;">{pred_2025:,.0f} kg</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Two-column layout for chart + notes ---
st.subheader("📈 Actual vs Predicted Tobacco Exports (2022–2025)")
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(5,3))

    # Actual exports scatter
    df_actual = df_compare[df_compare["Year"] >= 2022]
    ax.scatter(df_actual["Year"], df_actual["Exports"], color="teal", s=25, label="Actual Exports")

    # Predicted exports line
    ax.plot(df_compare["Year"], df_compare["Predicted"], color=TIMB_GREEN, linewidth=1.8, label="Pattern-Based Prediction")

    # Highlight 2025 prediction
    if prod_2025 > 0:
        ax.scatter(2025, pred_2025, color=TIMB_GOLD, s=60, marker="X", label="2025 Prediction")

    # Annotate % differences
    for _, row in df_actual.iterrows():
        if pd.notna(row["Exports"]) and pd.notna(row["Predicted"]):
            diff = ((row["Predicted"] - row["Exports"]) / row["Exports"]) * 100
            txt = f"{diff:+.1f}%"
            ax.text(row["Year"], row["Exports"], txt, fontsize=7, ha="center", va="bottom", color="black")

    # Labels
    ax.set_title("Actual vs Predicted Exports", fontsize=10, fontweight="bold")
    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Exports (kg)", fontsize=8)
    ax.tick_params(axis="both", which="major", labelsize=8)
    ax.set_xticks([2022, 2023, 2024, 2025])
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=7)

    st.pyplot(fig)

with col2:
    st.markdown("### ℹ️ Insights")
    st.markdown("- **Green line**: Pattern-based prediction.")
    st.markdown("- **Teal dots**: Actual exports (2022–2024).")
    st.markdown("- **Gold X**: Predicted 2025 exports.")
    st.markdown("- **% labels**: Gap between actual & predicted.")

    # --- Summary Table ---
    st.markdown("#### 📊 Export Summary")
    summary_rows = []
    for _, row in df_compare[df_compare["Year"] >= 2022].iterrows():
        year = int(row["Year"])
        pred = row["Predicted"]
        act = row["Exports"]
        if pd.notna(act):
            diff = ((pred - act) / act) * 100
            summary_rows.append(f"- {year}: Pred {pred:,.0f} vs Actual {act:,.0f} (**{diff:+.1f}%**)")
        else:
            summary_rows.append(f"- {year}: Pred {pred:,.0f} (no actual yet)")

    for row in summary_rows:
        st.markdown(row)
