import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from supabase import create_client, Client
import json
import time

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
st.markdown("### Phase 3: Real Database Queries")

if supabase:
    st.success("✅ Successfully connected to Supabase Database!")
else:
    st.error("❌ Database not connected. Check Streamlit secrets.")

# 4. Create a base map centered on the Central Maryland region
m = folium.Map(location=[38.8298, -76.8483], zoom_start=10, tiles="CartoDB positron")

# 5. FETCH LIVE DATA: Pull MALPF Easements
# We create a placeholder that disappears when it finishes loading
status_placeholder = st.empty()
status_placeholder.write("🔄 *Attempting to download restricted land data from the State of Maryland...*")

@st.cache_data(ttl=3600) 
def get_malpf_data():
    malpf_url = "https://mdgeodata.md.gov/imap/rest/services/Environment/MD_ProtectedLands/FeatureServer/4/query"
    params = {
        "where": "County LIKE '%Prince George%'", 
        "outFields": "*", 
        "outSR": "4326", 
        "f": "geojson",
        "resultRecordCount": 25 # Reduced from 1000 to 25 to prevent browser freezing!
    }
    try:
        response = requests.get(malpf_url, params=params, timeout=15)
        return response.status_code, response.text
    except Exception as e:
        return 500, str(e)

status_code, response_text = get_malpf_data()

# 6. Diagnostics & Drawing the Red Zones
if status_code == 200:
    try:
        malpf_geojson = json.loads(response_text)
        features = malpf_geojson.get('features', [])
        
        if len(features) > 0:
            status_placeholder.success(f"✅ Success! Painted {len(features)} restricted agricultural zones (MALPF) on the map.")
            folium.GeoJson(
                malpf_geojson, 
                name="MALPF Easements (No Solar)",
                style_function=lambda x: {
                    'fillColor': '#ff0000',
                    'color': '#ff0000',
                    'weight': 1,
                    'fillOpacity': 0.4
                }
            ).add_to(m)
        else:
            status_placeholder.warning("⚠️ Connected to Maryland servers, but found 0 restricted zones for this query.")
    except Exception as e:
        status_placeholder.error(f"❌ Downloaded the data, but it was corrupted. Error: {e}")
else:
    status_placeholder.error(f"❌ Failed to reach Maryland State Servers. Error Code: {status_code}")

# 7. PHASE 3: The Real Solar Logic Engine
if "search_run" not in st.session_state:
        st.session_state.search_run = False

# 8. Sidebar Controls 
with st.sidebar:
    st.header("⚙️ Filtering Logic")
    min_acreage = st.slider("Minimum Acreage", min_value=5, max_value=50, value=15)
    st.checkbox("Show MALPF Easements (Red)", value=True)
    st.checkbox("Hide Restricted BGE Circuits", value=True)
    st.divider()
    if st.button("Find Viable Land", type="primary", use_container_width=True):
        st.session_state.search_run = True

# 9. Process the real search and draw the results from Supabase
if st.session_state.search_run:
    with st.spinner("Querying Spatial Database..."):
        try:
            # Execute the real PostGIS RPC function we built in Supabase
            response = supabase.rpc("get_viable_parcels", {"min_acres": min_acreage}).execute()
            parcel_geojson = response.data
            
            if parcel_geojson and len(parcel_geojson.get("features", [])) > 0:
                count = len(parcel_geojson["features"])
                st.sidebar.success(f"✅ Found {count} High-Confidence Sites in Database!")
                
                folium.GeoJson(
                    parcel_geojson,
                    name="Viable Parcels",
                    style_function=lambda x: {
                        'fillColor': '#00ff00', 
                        'color': '#008000',
                        'weight': 2,
                        'fillOpacity': 0.5
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['address', 'acreage', 'zoning'], 
                        aliases=['Address:', 'Acreage:', 'Zoning:']
                    )
                ).add_to(m)
            else:
                st.sidebar.warning("No parcels found in database matching criteria.")
        except Exception as e:
            st.sidebar.error(f"Database query failed: {e}")

# 10. Display the map
st_folium(m, width=1200, height=600)
