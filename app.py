import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from supabase import create_client, Client
import json

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
st.write("🔄 *Attempting to download restricted land data from the State of Maryland...*")

@st.cache_data(ttl=3600) 
def get_malpf_data():
    # Using the official active MD iMAP endpoint (mdgeodata)
    malpf_url = "https://mdgeodata.md.gov/imap/rest/services/Environment/MD_ProtectedLands/FeatureServer/4/query"
    
    # We use 'LIKE' to avoid apostrophe syntax errors with "Prince George's"
    params = {
        "where": "County LIKE '%Prince George%'", 
        "outFields": "*", 
        "outSR": "4326", 
        "f": "geojson"
    }
    
    try:
        # Increased timeout to 30 seconds for state servers
        response = requests.get(malpf_url, params=params, timeout=30)
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
            st.success(f"✅ Success! Painted {len(features)} restricted agricultural zones (MALPF) on the map.")
            folium.GeoJson(
                malpf_geojson, 
                name="MALPF Easements (No Solar)",
                style_function=lambda x: {
                    'fillColor': '#ff0000', # Red for restricted
                    'color': '#ff0000',
                    'weight': 1,
                    'fillOpacity': 0.4
                }
            ).add_to(m)
        else:
            st.warning("⚠️ Connected to Maryland servers, but found 0 restricted zones for this query.")
    except Exception as e:
        st.error(f"❌ Downloaded the data, but it was corrupted. Error: {e}")
        with st.expander("See raw response from Maryland"):
            st.write(response_text[:1000])
else:
    st.error(f"❌ Failed to reach Maryland State Servers. Error Code: {status_code}")
    with st.expander("See technical error"):
        st.write(response_text)

# 7. Display the map
st_folium(m, width=1200, height=600)

# 8. Sidebar Controls
with st.sidebar:
    st.header("⚙️ Filtering Logic")
    
    st.checkbox("Show Parcels > 15 Acres", disabled=True, help="Will activate in Phase 3")
    st.checkbox("Show MALPF Easements (Red)", value=True)
    st.checkbox("Hide Restricted BGE Circuits", disabled=True, help="Will activate in Phase 3")
    
    st.divider()
    st.button("Find Viable Land", disabled=True, use_container_width=True)
