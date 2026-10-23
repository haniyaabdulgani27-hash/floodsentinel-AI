import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FloodSentinel AI", page_icon="🌊", layout="wide")

st.title("🌊 FloodSentinel AI")
st.write("### Intelligent Flood Management Dashboard")
st.caption("Prototype | Flood monitoring and risk assessment")

st.warning(
    "Demo mode: the readings and thresholds below are illustrative, "
    "not actual flood warnings."
)

st.sidebar.header("Monitoring Inputs")

location = st.sidebar.selectbox("Select Location", ["Kolhapur", "Sangli", "Pune"])

rainfall = st.sidebar.number_input(
    "Rainfall (mm/day)", min_value=0.0, max_value=1000.0, value=35.0
)

river_level = st.sidebar.number_input(
    "River Level (m)", min_value=0.0, max_value=100.0, value=2.1
)

# Illustrative rules only; replace after validating data.
if rainfall >= 80 or river_level >= 4:
    risk = "HIGH"
elif rainfall >= 40 or river_level >= 3:
    risk = "MODERATE"
else:
    risk = "LOW"

st.subheader(f"Monitoring Overview — {location}")

c1, c2, c3 = st.columns(3)
c1.metric("Rainfall", f"{rainfall:.1f} mm/day")
c2.metric("River Level", f"{river_level:.2f} m")
c3.metric("Prototype Risk", risk)

if risk == "HIGH":
    st.error("HIGH: Review current official warnings and local conditions.")
elif risk == "MODERATE":
    st.warning("MODERATE: Continue monitoring readings and official advisories.")
else:
    st.success("LOW: Continue routine monitoring; this is not an all-clear.")

st.subheader("Rainfall Trend")

demo_data = pd.DataFrame(
    {
        "Day": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
        "Rainfall (mm)": [20, 35, 48, 65, 35],
    }
)

fig = px.line(
    demo_data,
    x="Day",
    y="Rainfall (mm)",
    markers=True,
    title="Illustrative Rainfall Data",
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Recommended Next Steps")

st.write("- Check official rainfall and river-gauge observations.")
st.write("- Compare readings with validated local thresholds.")
st.write("- Review official warnings before making response decisions.")

st.caption(
    "The graph uses sample values. Risk rules are temporary demo logic "
    "and must not be used for real-world emergency decisions."
)
