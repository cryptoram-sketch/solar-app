import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from supabase import create_client, Client

# 1. Set up the page layout and title
st.set_page_config(page_title="Solar Site Selector MVP", layout="wide")

# 2. Connect to our new Supabase Database
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        return None

supabase = init_connection()

# 3. Build the App Header
st.title("☀️ Maryland Solar Farm Site Selector")
st.markdown("### Phase 2: Live State Data & Database Connection")

if supabase:
    st.success("✅ Successfully connected to Supabase Database!")
else:
    st.error("❌ Database not connected. Check Streamlit secrets.")

# 4. Create a base map centered on Prince George's County
m = folium.Map(location=[38.8298, -76.8483], zoom_start=10, tiles="CartoDB positron")

# 5. FETCH LIVE DATA: Pull MALPF Easements directly from the State of Maryland
@st.cache_data(ttl=3600) # Cache the data so it doesn't download on every single click
def get_malpf_data():
    malpf_url = "https://mdgeodata.md.gov/imap/rest/services/Environment/MD_ProtectedLands/FeatureServer/4/query"
    # Query specifically for Prince George's County
    params = {
        "where": "County='Prince George''s'", 
        "outFields": "*", 
        "outSR": "4326", 
        "f": "geojson"
    }
    response = requests.get(malpf_url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

malpf_geojson = get_malpf_data()

# 6. Add the "No-Go" zones to the map
if malpf_geojson and 'features' in malpf_geojson and len(malpf_geojson['features']) > 0:
    st.write(f"🗺️ Loaded {len(malpf_geojson['features'])} restricted agricultural easements in PG County.")
    folium.GeoJson(
        malpf_geojson, 
        name="MALPF Easements (No Solar)",
        style_function=lambda x: {
            'fillColor': '#ff0000', # Red for restricted
            'color': '#ff0000',
            'weight': 1,
            'fillOpacity': 0.4
        },
        tooltip=folium.GeoJsonTooltip(fields=['Local_Name'], aliases=['Easement Name:'])
    ).add_to(m)

# 7. Display the map
st_folium(m, width=1200, height=600)

# 8. Sidebar Controls
with st.sidebar:
    st.header("⚙️ Filtering Logic")
    
    st.checkbox("Show Parcels > 15 Acres", disabled=True, help="Will activate in Phase 3")
    malpf_toggle = st.checkbox("Show MALPF Easements (Red)", value=True)
    st.checkbox("Hide Restricted BGE Circuits", disabled=True, help="Will activate in Phase 3")
    
    st.divider()
    st.button("Find Viable Land", disabled=True, use_container_width=True)
