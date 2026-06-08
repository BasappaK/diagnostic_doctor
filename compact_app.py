import streamlit as st
import pandas as pd
import numpy as np
import time
import threading
import os
import queue
from datetime import datetime
import plotly.express as px
import io

# Highly compact page setup layout profile
st.set_page_config(page_title="Diagnostics", layout="wide", initial_sidebar_state="collapsed")

# Inject Custom CSS injection matrix to aggressively minimize vertical padding and empty gaps
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 98%;}
        h1 {margin-top: -15px; margin-bottom: 2px; font-size: 1.8rem !important;}
        h2 {margin-top: 2px; margin-bottom: 2px; font-size: 1.3rem !important;}
        h3 {margin-top: 2px; margin-bottom: 2px; font-size: 1.05rem !important;}
        .stTabs [data-baseweb="tab-list"] {gap: 4px;}
        .stTabs [data-baseweb="tab"] {padding: 4px 10px; border-radius: 4px;}
        .element-container {margin-bottom: 0.4rem !important;}
        div[data-testid="stVerticalBlock"] > div {padding-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()

# -----------------------------------------------------------------------------
# 1. PARSER ENGINE
# -----------------------------------------------------------------------------
class DiagnosticParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        
    def parse_files(self, log_queue):
        log_queue.put({"message": f"Mapping: '{self.folder_path}'...", "level": "info", "time": datetime.now().strftime("%H:%M:%S")})
        time.sleep(0.3)
        if not os.path.exists(self.folder_path):
            log_queue.put({"message": f"Path '{self.folder_path}' missing.", "level": "error", "time": datetime.now().strftime("%H:%M:%S")})
            raise FileNotFoundError()
            
        simulated_files = [f"log_{i}.txt" for i in range(1, 6)]
        dtc_pool = {
            'P0101': 'MAF Sensor Range/Perf', 'P0300': 'Misfire Detected', 
            'P0420': 'Catalyst Efficiency Low', 'P0171': 'System Too Lean',
            'P0700': 'TCM Malfunction', 'U0100': 'ECM Comm Lost'
        }
        models = ['Model S', 'Model X', 'Truck A', 'Sedan Eco']
        modules = ['ECM (Engine)', 'TCM (Transmission)', 'BCM (Body)', 'ABS Module']
        statuses = ['Open', 'In Progress', 'Resolved', 'Under Investigation']
        
        rows = []
        for file in simulated_files:
            for _ in range(np.random.randint(15, 30)):
                chosen_code = np.random.choice(list(dtc_pool.keys()))
                rows.append({
                    "File Name": file, "Module": np.random.choice(modules),
                    "Code": chosen_code, "Description": dtc_pool[chosen_code],
                    "Status": np.random.choice(statuses), "Comments": "Auto-logged anomaly.",
                    "Reviewer": "Admin", "Vehicle Model Name": np.random.choice(models),
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        return pd.DataFrame(rows)

def background_worker(folder_path, log_queue, result_container):
    try:
        parser = DiagnosticParser(folder_path)
        result_container['dataframe'] = parser.parse_files(log_queue)
        result_container['status'] = 'done'
    except Exception:
        result_container['status'] = 'error'

# State Setup
if 'status_logs' not in st.session_state: st.session_state.status_logs = []
if 'processing_complete' not in st.session_state: st.session_state.processing_complete = False
if 'is_processing' not in st.session_state: st.session_state.is_processing = False
if 'dataframe' not in st.session_state: st.session_state.dataframe = None
if 'thread_result' not in st.session_state: st.session_state.thread_result = {'status': 'idle', 'dataframe': None}

st.title("⚡ Vehicle Diagnostic Parser")
tab1, tab2 = st.tabs(["📊 Summary & Insights", "📋 Detailed Data Report"])

# ==========================================
# --- TAB 1: INSIGHTS & CONTROLS ---
# ==========================================
with tab1:
    col_in1, col_in2 = st.columns([3, 1])
    with col_in1:
        folder_input = st.text_input("Folder Path:", placeholder="e.g., C:/DiagnosticLogs", label_visibility="collapsed", disabled=st.session_state.is_processing)
    with col_in2:
        if not st.session_state.is_processing and not st.session_state.processing_complete:
            if st.button("🚀 Run Parse Engine", type="primary", use_container_width=True):
                st.session_state.is_processing, st.session_state.processing_complete = True, False
                st.session_state.status_logs, st.session_state.thread_result = [], {'status': 'running', 'dataframe': None}
                threading.Thread(target=background_worker, args=(folder_input, st.session_state.log_queue, st.session_state.thread_result)).start()
                st.rerun()
        if st.session_state.processing_complete:
            if st.button("Clear / Reset Path", use_container_width=True):
                st.session_state.processing_complete = st.session_state.is_processing = False
                st.session_state.dataframe = None
                st.session_state.status_logs = []
                st.session_state.thread_result = {'status': 'idle', 'dataframe': None}
                st.rerun()

    # Log streaming block
    if st.session_state.is_processing:
        while not st.session_state.log_queue.empty():
            try: st.session_state.status_logs.append(st.session_state.log_queue.get_nowait())
            except queue.Empty: break
        if st.session_state.thread_result['status'] == 'done':
            st.session_state.dataframe = st.session_state.thread_result['dataframe']
            st.session_state.processing_complete, st.session_state.is_processing = True, False
            st.rerun()
        elif st.session_state.thread_result['status'] == 'error':
            st.session_state.processing_complete, st.session_state.is_processing = True, False
            st.error("Engine failure.")
            st.rerun()
        with st.container(border=True):
            st.caption("Parsing Log Activity stream...")
            for log in reversed(st.session_state.status_logs[-3:]):
                st.text(f"[{log['time']}] {log['message']}")
            time.sleep(0.5)
            st.rerun()

    if st.session_state.dataframe is not None:
        df = st.session_state.dataframe

        # --- COMPACT PERSPECTIVE SELECTOR ---
        st.write("---")
        perspective = st.selectbox("Root View Hierarchy Axis:", ["Code Perspective", "Vehicle Model Perspective"], label_visibility="visible")

        # Fixed to a clean, stable 2-layer drill down setup to eliminate visualization distortions
        active_hierarchy = ["Code", "Vehicle Model Name"] if perspective == "Code Perspective" else ["Vehicle Model Name", "Code"]

        # Side-by-Side Charts Configuration Matrix
        drilldown_col1, drilldown_col2 = st.columns(2)
        with drilldown_col1:
            fig_sunburst = px.sunburst(df, path=active_hierarchy, color_discrete_sequence=px.colors.qualitative.Safe)
            fig_sunburst.update_layout(margin=dict(t=25, l=5, r=5, b=5), height=280, title_text="Sunburst Breakdown", title_font_size=13)
            st.plotly_chart(fig_sunburst, use_container_width=True)
            
        with drilldown_col2:
            fig_treemap = px.treemap(df, path=active_hierarchy, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_treemap.update_layout(margin=dict(t=25, l=5, r=5, b=5), height=280, title_text="Nested Treemap Breakdown", title_font_size=13)
            st.plotly_chart(fig_treemap, use_container_width=True)

        # Baseline Distributions Hub
        st.write("---")
        c_1, c_2, c_3 = st.columns(3)
        with c_1:
            code_counts = df['Code'].value_counts().reset_index().head(10)
            code_counts.columns = ['Code', 'Count']
            fig_code = px.bar(code_counts, x='Code', y='Count', color_continuous_scale=px.colors.sequential.Viridis)
            fig_code.update_layout(margin=dict(t=20, b=5, l=5, r=5), height=220, title_text="Top Fault Codes", title_font_size=12)
            st.plotly_chart(fig_code, use_container_width=True)
            
        with c_2:
            module_counts = df['Module'].value_counts().reset_index()
            module_counts.columns = ['Module', 'Count']
            fig_module = px.bar(module_counts, x='Module', y='Count', color_continuous_scale=px.colors.sequential.Plasma)
            fig_module.update_layout(margin=dict(t=20, b=5, l=5, r=5), height=220, title_text="Module Metrics Distribution", title_font_size=12)
            st.plotly_chart(fig_module, use_container_width=True)
            
        with c_3:
            status_df = df.groupby(['Module', 'Status']).size().reset_index(name='Count')
            fig_status = px.bar(status_df, x='Count', y='Module', color='Status', orientation='h', color_discrete_sequence=px.colors.qualitative.Safe)
            fig_status.update_layout(
                barmode='stack', margin=dict(t=20, b=5, l=5, r=5), height=220, 
                title_text="ECU Workload Status Stack", title_font_size=12,
                legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, font_size=8, title_font_size=8)
            )
            st.plotly_chart(fig_status, use_container_width=True)

# ==========================================
# --- TAB 2: DATA REGISTRY GRIDVIEW ---
# ==========================================
with tab2:
    if st.session_state.dataframe is None:
        st.info("Execute file layout processing in Tab 1 first.")
    else:
        df_master = st.session_state.dataframe.copy()
        
        # Compact Inline Excel Filter Module Section
        filterable_columns = ["File Name", "Module", "Code", "Description", "Status", "Reviewer", "Vehicle Model Name"]
        filter_cols = st.columns(len(filterable_columns))
        active_filters = {}
        
        for col_idx, col_name in enumerate(filterable_columns):
            with filter_cols[col_idx]:
                opts = sorted(df_master[col_name].dropna().unique().tolist())
                selected_vals = st.multiselect(col_name, options=opts, default=None, key=f"ex_fltr_{col_name}", placeholder="All")
                if selected_vals: active_filters[col_name] = selected_vals

        df_filtered = df_master.copy()
        for col_name, selected_values in active_filters.items():
            df_filtered = df_filtered[df_filtered[col_name].isin(selected_values)]
            
        all_disabled_fields = ["File Name", "Module", "Code", "Description", "Vehicle Model Name", "Last Updated"]
        
        edited_df = st.data_editor(df_filtered, disabled=all_disabled_fields, hide_index=True, use_container_width=True, key="data_editor_registry", height=380)
        
        if not edited_df.equals(df_filtered):
            for index in edited_df.index:
                old_row = df_master.loc[index]
                new_row = edited_df.loc[index]
                has_changes = False
                updates = {}
                for editable_field in ['Comments', 'Status', 'Reviewer']:
                    if old_row[editable_field] != new_row[editable_field]:
                        updates[editable_field] = new_row[editable_field]
                        has_changes = True
                if has_changes:
                    for key, val in updates.items(): st.session_state.dataframe.loc[index, key] = val
                    st.session_state.dataframe.loc[index, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()

        # Export Framework Button Row
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.dataframe.to_excel(writer, index=False, sheet_name='Diagnostic Report')
        st.download_button(label="📥 Export Report to Excel (.xlsx)", data=buffer.getvalue(), file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")