import time
import queue
import threading
from datetime import datetime
import streamlit as st

# Decoupled custom layout references
from backend import background_worker
import frontend_components as ui

# Enforce clean custom style rules
ui.inject_compact_css()

if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()

# State Machine Checkpoints
if 'status_logs' not in st.session_state: st.session_state.status_logs = []
if 'processing_complete' not in st.session_state: st.session_state.processing_complete = False
if 'is_processing' not in st.session_state: st.session_state.is_processing = False
if 'dataframe' not in st.session_state: st.session_state.dataframe = None
if 'thread_result' not in st.session_state: st.session_state.thread_result = {'status': 'idle', 'dataframe': None}

st.title("⚡ Vehicle Diagnostic Parser Workspace")
tab1, tab2 = st.tabs(["📊 Summary & Insights", "📋 Detailed Data Report"])

def start_processing_callback(folder_path):
    st.session_state.is_processing, st.session_state.processing_complete = True, False
    st.session_state.status_logs, st.session_state.thread_result = [], {'status': 'running', 'dataframe': None}
    threading.Thread(target=background_worker, args=(folder_path, st.session_state.log_queue, st.session_state.thread_result)).start()
    st.rerun()

def reset_processing_callback():
    st.session_state.processing_complete = st.session_state.is_processing = False
    st.session_state.dataframe = None
    st.session_state.status_logs = []
    st.session_state.thread_result = {'status': 'idle', 'dataframe': None}
    st.rerun()

# ==========================================
# --- TAB 1: SUMMARY & VISUALIZATIONS ---
# ==========================================
with tab1:
    ui.render_ingestion_controls(
        st.session_state.is_processing,
        st.session_state.processing_complete,
        start_processing_callback,
        reset_processing_callback
    )

    # In-progress processing activity loop tracking
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
            st.error("Engine pipeline execution failure.")
            st.rerun()
            
        # Draw the layout-safe 3-line status logger box during runtime processing updates
        ui.render_live_status_box(st.session_state.status_logs)
        time.sleep(0.4)
        st.rerun()

    if st.session_state.dataframe is not None:
        ui.render_analytics_dashboard(st.session_state.dataframe)

# ==========================================
# --- TAB 2: DATA REGISTRY GRIDVIEW ---
# ==========================================
with tab2:
    if st.session_state.dataframe is None:
        st.info("Execute file layout processing in Tab 1 first.")
    else:
        edited_df, has_mutated = ui.render_data_registry_grid(st.session_state.dataframe)
        
        if has_mutated:
            df_master = st.session_state.dataframe
            for index in edited_df.index:
                old_row = df_master.loc[index]
                new_row = edited_df.loc[index]
                row_changed = False
                for field in ['Comments', 'Status', 'Reviewer']:
                    if old_row[field] != new_row[field]:
                        st.session_state.dataframe.loc[index, field] = new_row[field]
                        row_changed = True
                if row_changed:
                    st.session_state.dataframe.loc[index, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()

        ui.render_export_module(st.session_state.dataframe)