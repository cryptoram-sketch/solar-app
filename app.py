import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Set up the page layout and title
st.set_page_config(page_title="Solar Site Selector MVP", layout="wide")

# 2. Build the App Header
st.title("☀️ Maryland Solar Farm Site Selector")
st.markdown("### Phase 1 MVP: Prince George's County Base Map")
st.write("Welcome to your live application! Right now, this is our foundation map. Next week, we will inject the BGE Grid Constraints and MALPF Easement data here.")

# 3. Create a base map centered on Prince George's County, MD
# Coordinates: Latitude 38.8298, Longitude -76.8483
m = folium.Map(location=[38.8298, -76.8483], zoom_start=10, tiles="CartoDB positron")

# Add a marker for Prince George's County to prove the map is working
folium.Marker(
    [38.8298, -76.8483],
    popup="Prince George's County Center",
    tooltip="MVP Target Area"
).add_to(m)

# 4. Display the map in the main section of the app
st_folium(m, width=1200, height=600)

# 5. Build a placeholder Sidebar for our future filtering logic
with st.sidebar:
    st.header("⚙️ Filtering Logic")
    st.write("*(These controls will activate in Phase 2)*")
    
    # These are disabled for now until we connect the database
    st.checkbox("Show Parcels > 15 Acres", disabled=True)
    st.checkbox("Hide MALPF Easements", disabled=True)
    st.checkbox("Hide Restricted BGE Circuits", disabled=True)
    
    st.divider()
    
    st.button("Find Viable Land", disabled=True, use_container_width=True)
