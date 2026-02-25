import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import time
import os
from datetime import datetime

st.set_page_config(page_title="MRC Flight Tracker", layout="wide")

# ၁။ မှတ်တမ်းသိမ်းမည့် ဖိုင်အမည်
HISTORY_FILE = "flight_history.csv"

# ၂။ Siren အသံပေးမည့် Function
def trigger_alarm():
    siren_url = "https://actions.google.com/sounds/v1/emergency/ambulance_siren.ogg"
    st.components.v1.html(
        f"""
        <div style="display:none;">
            <audio autoplay loop id="siren">
                <source src="{siren_url}" type="audio/ogg">
            </audio>
            <script>
                var audio = document.getElementById('siren');
                audio.volume = 1.0;
                audio.play();
            </script>
        </div>
        """,
        height=0,
    )

st.title("🛡️ MRC ၏ လီကြောင်း Live အချက်ပီးစနစ်")

# ၃။ ဒေတာဆွဲယူခြင်း
def get_flight_data():
    url = "https://opensky-network.org/api/states/all"
    bounds = {'lamin': 17.2, 'lamax': 21.4, 'lomin': 92.2, 'lomax': 95.0}
    try:
        response = requests.get(url, params=bounds, timeout=10)
        data = response.json()
        if data and 'states' in data and data['states'] is not None:
            df = pd.DataFrame(data['states'], columns=[
                'icao24', 'callsign', 'origin_country', 'time_position', 
                'last_contact', 'longitude', 'latitude', 'baro_altitude', 
                'on_ground', 'velocity', 'true_track', 'vertical_rate', 
                'sensors', 'geo_altitude', 'squawk', 'spi', 'position_source'
            ])
            df['callsign'] = df['callsign'].str.strip()
            df['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = get_flight_data()

# ၄။ ပင်မ Dashboard Logic
if not df.empty:
    count = len(df)
    st.markdown(f"""
        <div style="background-color:#ff4b4b; padding:15px; border-radius:10px; text-align:center;">
            <h1 style="color:white; margin:0;">⚠️ လေယာဉ် {count} စီး တွိ့ထားပါရေ။ သတိထားကတ်ပါ။ </h1>
        </div>
    """, unsafe_allow_html=True)
    
    trigger_alarm()
    
    # --- မှတ်တမ်းသိမ်းခြင်း Logic ---
    if not os.path.isfile(HISTORY_FILE):
        df[['timestamp', 'callsign', 'origin_country', 'baro_altitude']].to_csv(HISTORY_FILE, index=False)
    else:
        # လက်ရှိမိတဲ့ လေယာဉ်တွေကို မှတ်တမ်းဟောင်းထဲ ပေါင်းထည့်ခြင်း
        df[['timestamp', 'callsign', 'origin_country', 'baro_altitude']].to_csv(HISTORY_FILE, mode='a', header=False, index=False)

    # မြေပုံပြသခြင်း
    view_state = pdk.ViewState(latitude=19.5, longitude=93.5, zoom=6.5)
    layer = pdk.Layer("ScatterplotLayer", data=df, get_position='[longitude, latitude]',
                      get_color='[255, 255, 0]', get_radius=6000)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
    
    st.write("📋 လက်ရှိပျံသန်းနေသည့် အသေးစိတ်စာရင်း:")
    st.dataframe(df[['callsign', 'origin_country', 'baro_altitude']], use_container_width=True)
else:
    st.success("✅ လက်ဟိတွင် ရခိုင်ပြည်နယ်အတွင်း လေယာဉ်ပျံလို့မဟိပါ။")

# ၅။ --- လေယာဉ်မှတ်တမ်းများကို ပြန်ကြည့်ရန် အပိုင်း ---
st.divider()
st.subheader("📊 ပျံသန်းသွားခဲ့သည့် လေယာဉ်မှတ်တမ်း (History)")

if os.path.isfile(HISTORY_FILE):
    history_df = pd.read_csv(HISTORY_FILE)
    # နောက်ဆုံးမိတဲ့လေယာဉ်ကို အပေါ်ဆုံးမှာပြရန် (Sort by time)
    history_df = history_df.drop_duplicates(subset=['callsign'], keep='last') # ဒေတာမထပ်အောင် စစ်ထုတ်ခြင်း
    st.dataframe(history_df.iloc[::-1], use_container_width=True)
    
    # မှတ်တမ်းဖျက်ရန် ခလုတ် (Option)
    if st.button("မှတ်တမ်းအားလုံး ဖျက်ပစ်မည်"):
        os.remove(HISTORY_FILE)
        st.rerun()
else:
    st.info("မှတ်တမ်း မရှိသေးပါ။")

# ၆။ အလိုအလျောက် Refresh လုပ်ခြင်း
st.caption(f"နောက်ဆုံးစစ်ဆေးသည့်အချိန်: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(60)
st.rerun()