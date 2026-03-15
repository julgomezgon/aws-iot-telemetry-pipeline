import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import time
from decimal import Decimal

# --- CONFIGURATION ---
st.set_page_config(page_title="AWS Sentinel Pro", layout="wide", page_icon="📡")

# Initialize history in session memory
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['timestamp', 'cpu_usage', 'ram_usage', 'disk_usage'])

# CSS styling
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 AWS IoT Sentinel: Mission Control")
st.markdown("---")

# --- CONNECTION ---
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('iot-device-status')

def fetch_data():
    try:
        response = table.scan()
        items = response.get('Items', [])
        for item in items:
            for k, v in item.items():
                if isinstance(v, Decimal): item[k] = float(v)
        return items
    except:
        return []

# --- UPDATE LOGIC ---
data = fetch_data()

if data:
    latest = data[0]
    # Update local history (keep last 20 points)
    new_entry = {
        'timestamp': latest['timestamp'][-12:-7], # Only min:sec for the X axis
        'cpu_usage': latest['cpu_usage'],
        'ram_usage': latest['ram_usage'],
        'disk_usage': latest['disk_usage']
    }
    
    # Avoid duplicates by timestamp
    if st.session_state.history.empty or new_entry['timestamp'] != st.session_state.history.iloc[-1]['timestamp']:
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_entry])]).tail(20)

    # --- UI: TOP METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    
    # Visual alert if CPU usage is high
    cpu_color = "normal" if latest['cpu_usage'] < 80 else "inverse"
    
    c1.metric("💻 Device ID", latest['device_id'])
    c2.metric("🔥 CPU Load", f"{latest['cpu_usage']}%", delta=None, delta_color=cpu_color)
    c3.metric("🧠 RAM Usage", f"{latest['ram_usage']}%")
    c4.metric("💾 Disk space", f"{latest['disk_usage']}%")

    st.markdown("---")

    # --- UI: CHARTS ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Real-Time Performance History")
        fig_line = px.line(st.session_state.history, x='timestamp', y=['cpu_usage', 'ram_usage'],
                           template="plotly_dark", color_discrete_sequence=['#00d4ff', '#7000ff'])
        fig_line.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig_line, use_container_width=True, key=f"line_{time.time()}")

    with col_right:
        st.subheader("📊 Current Distribution")
        # Pie chart or bar chart for comparison
        fig_bar = px.bar(st.session_state.history.tail(1), y=['cpu_usage', 'ram_usage', 'disk_usage'],
                         barmode='group', template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{time.time()}")

    st.caption(f"Last heartbeat: {latest['timestamp']} | Auto-refreshing every second")
    
else:
    st.warning("📡 Waiting for Kinesis data stream...")


time.sleep(1)
st.rerun()