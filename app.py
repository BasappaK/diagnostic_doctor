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

# Set page configuration
st.set_page_config(page_title="Vehicle Diagnostics Dashboard", layout="wide")

# -----------------------------------------------------------------------------
# 1. GLOBAL THREAD QUEUE FOR REAL-TIME LOGGING
# -----------------------------------------------------------------------------
if 'log_queue' not in st.session_state:
    st.session_state.log_queue = queue.Queue()

# -----------------------------------------------------------------------------
# 2. BACKEND DIAGNOSTIC PARSER CLASS (Updated Schema Integration)
# -----------------------------------------------------------------------------
class DiagnosticParser:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        
    def parse_files(self, log_queue):
        log_queue.put({"message": f"Checking directory: '{self.folder_path}'...", "level": "info", "time": datetime.now().strftime("%H:%M:%S")})
        time.sleep(0.5)
        
        if not os.path.exists(self.folder_path):
            log_queue.put({"message": f"Error: The directory path '{self.folder_path}' was not found.", "level": "error", "time": datetime.now().strftime("%H:%M:%S")})
            raise FileNotFoundError(f"Path {self.folder_path} does not exist.")
            
        simulated_files = [f"log_file_{i}.txt" for i in range(1, 11)]
        log_queue.put({"message": f"Successfully mapped directory. Found {len(simulated_files)} logs.", "level": "info", "time": datetime.now().strftime("%H:%M:%S")})
        time.sleep(0.5)
        
        # Production Domain Dictionaries mapping precisely to the requested schema
        dtc_pool = {
            'P0101': 'Mass Air Flow Sensor Circuit Range/Performance',
            'P0300': 'Random/Multiple Cylinder Misfire Detected',
            'P0420': 'Catalyst System Efficiency Below Threshold',
            'P0171': 'System Too Lean (Bank 1)',
            'P0700': 'Transmission Control System Malfunction',
            'U0100': 'Lost Communication With ECM/PCM',
            'B0028': 'Right Side Airbag Deployment Control',
            'C0045': 'Brake Pressure Sensor \'B\' Malfunction'
        }
        models = ['Model S', 'Model X', 'Truck Series A', 'Sedan Eco', 'SUV Luxury']
        modules = ['ECM (Engine)', 'TCM (Transmission)', 'BCM (Body)', 'ABS Module', 'SRS (Airbag)']
        statuses = ['Open', 'In Progress', 'Resolved', 'Under Investigation']
        
        rows = []
        for idx, file in enumerate(simulated_files):
            log_queue.put({"message": f"Processing target log -> {file}...", "level": "info", "time": datetime.now().strftime("%H:%M:%S")})
            time.sleep(0.1)
            
            for _ in range(np.random.randint(8, 20)):
                chosen_code = np.random.choice(list(dtc_pool.keys()))
                rows.append({
                    "File Name": file,
                    "Module": np.random.choice(modules),
                    "Code": chosen_code,
                    "Description": dtc_pool[chosen_code],
                    "Status": np.random.choice(statuses),
                    "Comments": "Auto-generated log entry.",
                    "Reviewer": "System Admin",
                    "Vehicle Model Name": np.random.choice(models),
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
        log_queue.put({"message": "Data Parsing Complete!", "level": "success", "time": datetime.now().strftime("%H:%M:%S")})
        
        df_result = pd.DataFrame(rows)
        return df_result

# -----------------------------------------------------------------------------
# 3. BACKGROUND WORKER WRAPPER
# -----------------------------------------------------------------------------
def background_worker(folder_path, log_queue, result_container):
    try:
        parser = DiagnosticParser(folder_path)
        df_result = parser.parse_files(log_queue)
        result_container['dataframe'] = df_result
        result_container['status'] = 'done'
    except Exception as e:
        result_container['status'] = 'error'

# -----------------------------------------------------------------------------
# 4. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if 'status_logs' not in st.session_state: st.session_state.status_logs = []
if 'processing_complete' not in st.session_state: st.session_state.processing_complete = False
if 'is_processing' not in st.session_state: st.session_state.is_processing = False
if 'dataframe' not in st.session_state: st.session_state.dataframe = None
if 'thread_result' not in st.session_state: st.session_state.thread_result = {'status': 'idle', 'dataframe': None}

# -----------------------------------------------------------------------------
# 5. STREAMLIT UI DESIGN
# -----------------------------------------------------------------------------
st.title("⚡ Production Vehicle Diagnostic Parser")

tab1, tab2 = st.tabs(["📊 DTC Summary & Insights", "📋 Detailed Data Report"])

# ==========================================
# --- TAB 1: SUMMARY & VISUALIZATIONS ---
# ==========================================
with tab1:
    st.subheader("1. File Ingestion Configuration")
    
    folder_input = st.text_input(
        "Enter Target Folder Absolute Directory Path:",
        placeholder="e.g., C:/Users/Documents/DiagnosticLogs  or  /var/data/logs",
        disabled=st.session_state.is_processing
    )

    if folder_input and not st.session_state.is_processing and not st.session_state.processing_complete:
        if st.button("🚀 Start Diagnostic Processing", type="primary"):
            st.session_state.is_processing = True
            st.session_state.processing_complete = False
            st.session_state.status_logs = []
            st.session_state.thread_result = {'status': 'running', 'dataframe': None}
            
            while not st.session_state.log_queue.empty():
                try: st.session_state.log_queue.get_nowait()
                except queue.Empty: break
            
            threading.Thread(target=background_worker, args=(folder_input, st.session_state.log_queue, st.session_state.thread_result)).start()
            st.rerun()

    if st.session_state.processing_complete:
        if st.button("Reset / Parse New Folder Location"):
            st.session_state.processing_complete = False
            st.session_state.is_processing = False
            st.session_state.dataframe = None
            st.session_state.status_logs = []
            st.session_state.thread_result = {'status': 'idle', 'dataframe': None}
            st.rerun()

    # --- LIVE LOG CONTAINER ---
    @st.fragment(run_every=1.0)
    def render_live_logs():
        if st.session_state.is_processing:
            st.write("---")
            st.subheader("⚙️ Live Diagnostic Backend Engine Status")
            
            while not st.session_state.log_queue.empty():
                try: st.session_state.status_logs.append(st.session_state.log_queue.get_nowait())
                except queue.Empty: break
            
            if st.session_state.thread_result['status'] == 'done':
                st.session_state.dataframe = st.session_state.thread_result['dataframe']
                st.session_state.processing_complete = True
                st.session_state.is_processing = False
                st.rerun()
            elif st.session_state.thread_result['status'] == 'error':
                st.session_state.processing_complete = True
                st.session_state.is_processing = False
                st.error("❌ Critical execution block aborted.")
                st.rerun()
                
            with st.container(height=180, border=True):
                for log in reversed(st.session_state.status_logs):
                    msg_txt = f"[{log['time']}] {log['message']}"
                    if log['level'] == 'success': st.success(msg_txt)
                    elif log['level'] == 'warning': st.warning(msg_txt)
                    elif log['level'] == 'error': st.error(msg_txt)
                    else: st.info(msg_txt)

    render_live_logs()

    # --- VISUALIZATION ENGINES ---
    if st.session_state.dataframe is not None:
        st.write("---")
        df = st.session_state.dataframe
        
        st.subheader("2. Core Multi-Perspective Drill-Down Tree Analytics")
        perspective = st.selectbox("Select Root Hierarchy View Structure:", ["Code Perspective", "Vehicle Model Perspective"])
        hierarchy = ["Code", "Vehicle Model Name", "Module"] if perspective == "Code Perspective" else ["Vehicle Model Name", "Code", "Module"]
        
        # Side-by-Side Charts Configuration
        drilldown_col1, drilldown_col2 = st.columns(2)
        
        with drilldown_col1:
            fig_sunburst = px.sunburst(df, path=hierarchy, title=f"Sunburst Hierarchy Layout ({perspective})", color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_sunburst, use_container_width=True)
            
        with drilldown_col2:
            fig_treemap = px.treemap(df, path=hierarchy, title=f"Treemap Hierarchy Layout Breakdown ({perspective})", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_treemap, use_container_width=True)
            
        # Alternative Views Expander Drawer
        with st.expander("✨ View Alternative Drill-Down Chart Frameworks"):
            alt_chart_type = st.radio("Choose Alternative Display Structure:", ["Icicle Plot Hierarchy", "Parallel Multi-Stage Paths (Sankey Style)"], horizontal=True)
            if alt_chart_type == "Icicle Plot Hierarchy":
                fig_icicle = px.icicle(df, path=hierarchy, title=f"Icicle Cascading View", color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig_icicle, use_container_width=True)
            else:
                fig_parallel = px.parallel_categories(df, dimensions=hierarchy, title=f"Categorical Flow Path Mapping Matrix", color_continuous_scale=px.colors.sequential.Inferno)
                st.plotly_chart(fig_parallel, use_container_width=True)

        st.write("---")
        st.subheader("3. Core Metric Profiles & Distribution Summaries")
        
        c_1, c_2, c_3 = st.columns(3)
        
        with c_1:
            code_counts = df['Code'].value_counts().reset_index().head(20)
            code_counts.columns = ['Code', 'Occurrences Count']
            fig_code = px.bar(code_counts, x='Code', y='Occurrences Count', title="Top Active DTC Codes Detected", color='Occurrences Count', color_continuous_scale=px.colors.sequential.Viridis)
            st.plotly_chart(fig_code, use_container_width=True)
            
        with c_2:
            module_counts = df['Module'].value_counts().reset_index()
            module_counts.columns = ['Module', 'DTC Count']
            fig_module = px.bar(module_counts, x='Module', y='DTC Count', title="Module Total Fault Metrics", color='DTC Count', color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig_module, use_container_width=True)
            
        with c_3:
            # Grouping records explicitly by Module and Status
            status_df = df.groupby(['Module', 'Status']).size().reset_index(name='Record Count')
            
            # Stacked Horizontal Bar Chart Configuration
            fig_status = px.bar(
                status_df, 
                x='Record Count', 
                y='Module', 
                color='Status', 
                orientation='h',
                title="Module Workload Breakdown by Status",
                color_discrete_sequence=px.colors.qualitative.Safe,
                labels={'Record Count': 'Total DTC Count', 'Module': 'Target System Module'}
            )
            fig_status.update_layout(barmode='stack', yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_status, use_container_width=True)

# ==========================================
# --- TAB 2: DATA REGISTRY GRIDVIEW ---
# ==========================================
with tab2:
    st.subheader("📋 Advanced Global Diagnostic Registry Data Grid")
    
    if st.session_state.dataframe is None:
        st.info("Please explicitly configure a path location layout configuration profile inside Tab 1 first.")
    else:
        df_master = st.session_state.dataframe.copy()
        
        # --- EXCEL-STYLE COLUMN FILTERS RIBBON PANEL ---
        st.markdown("#### 🔍 Excel Column Filters")
        filterable_columns = ["File Name", "Module", "Code", "Description", "Status", "Reviewer", "Vehicle Model Name"]
        filter_cols = st.columns(len(filterable_columns))
        active_filters = {}
        
        # Build individual column multi-select widgets side-by-side
        for col_idx, col_name in enumerate(filterable_columns):
            with filter_cols[col_idx]:
                unique_options = sorted(df_master[col_name].dropna().unique().tolist())
                selected_vals = st.multiselect(f"Filter {col_name}", options=unique_options, default=None, key=f"excel_filter_{col_name}")
                if selected_vals: 
                    active_filters[col_name] = selected_vals

        # Filter operations mapped to master data cache copy
        df_filtered = df_master.copy()
        for col_name, selected_values in active_filters.items():
            df_filtered = df_filtered[df_filtered[col_name].isin(selected_values)]
            
        st.write("") 
        
        # Immutable field configurations based on new column mappings
        all_disabled_fields = ["File Name", "Module", "Code", "Description", "Vehicle Model Name", "Last Updated"]
        
        # Dynamic Data Editing Sheet Environment
        edited_df = st.data_editor(
            df_filtered, 
            disabled=all_disabled_fields, 
            hide_index=True, 
            use_container_width=True, 
            key="data_editor_registry"
        )
        
        # Sync updates on comments, status, or reviewer back to Master State Cache
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
                    for key, val in updates.items(): 
                        st.session_state.dataframe.loc[index, key] = val
                    st.session_state.dataframe.loc[index, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
            st.success("Changes saved! Audit timestamps updated.")
            st.rerun()

        # Excel Export Engine Utility Block
        st.write("---")
        st.subheader("📥 Export Records Hub")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.dataframe.to_excel(writer, index=False, sheet_name='Diagnostic Report')
            
        st.download_button(
            label="📥 Export Complete Matrix Records to Microsoft Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Diagnostic_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )