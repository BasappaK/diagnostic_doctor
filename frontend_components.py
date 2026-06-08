import streamlit as st
import plotly.express as px
import pandas as pd
import io
from datetime import datetime

def inject_compact_css():
    """Injects custom CSS to remove whitespace and enforce a compact layout."""
    st.markdown("""
        <style>
            .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 98%;}
            h1 {margin-top: -15px; margin-bottom: 2px; font-size: 1.8rem !important;}
            h2 {margin-top: 2px; margin-bottom: 2px; font-size: 1.25rem !important;}
            h3 {margin-top: 2px; margin-bottom: 2px; font-size: 1.05rem !important;}
            .stTabs [data-baseweb="tab-list"] {gap: 4px;}
            .stTabs [data-baseweb="tab"] {padding: 4px 10px; border-radius: 4px;}
            .element-container {margin-bottom: 0.4rem !important;}
            .small-log-text {font-size: 11px !important; font-family: monospace; line-height: 1.3;}
        </style>
    """, unsafe_allow_html=True)


def render_ingestion_controls(is_processing, processing_complete, on_start_callback, on_reset_callback):
    """Renders the folder ingestion controls."""
    col_in1, col_in2 = st.columns([3, 1])
    with col_in1:
        folder_input = st.text_input(
            "Path Container Input:", 
            placeholder="e.g., C:/DiagnosticLogs", 
            label_visibility="collapsed", 
            disabled=is_processing
        )
    with col_in2:
        if not is_processing and not processing_complete:
            if st.button("🚀 Run Parse Engine", type="primary", use_container_width=True) and folder_input:
                on_start_callback(folder_input)
        if processing_complete:
            if st.button("Clear / Reset Path", use_container_width=True):
                on_reset_callback()


def render_live_status_box(status_logs):
    """Renders a stable log status panel showing at least 3 historical lines of system activity."""
    with st.container(border=True):
        st.caption("⚙️ Live Diagnostic Backend Engine Log Activity Stream:")
        display_logs = status_logs[-3:] if len(status_logs) >= 3 else ([""] * (3 - len(status_logs)) + status_logs)
        
        for log in reversed(display_logs):
            if isinstance(log, dict):
                log_text = f"[{log['time']}] {log['message']}"
            else:
                log_text = log if log != "" else "Waiting for backend pipeline engine sequence cycle..."
                
            st.markdown(f"<div class='small-log-text'>{log_text}</div>", unsafe_allow_html=True)


def render_analytics_dashboard(df):
    """Renders both hierarchies side-by-side with a single representation selector dropdown."""
    st.write("---")
    
    # SINGLE SELECTOR REMAINING: Controls the chart type for both sides simultaneously
    chart_style = st.selectbox(
        "Select Drill-Down Diagram Representation Framework:",
        ["Standard Nested Radial Sunburst", "Standard Rectangular Nested Treemap", "Linear Icicle Cascading Flow Matrix"]
    )

    # Hardcoded structural paths for both requested strategies
    model_hierarchy = ["Vehicle Model Name", "Vehicle VIN", "Module", "Code"]
    dtc_hierarchy = ["Module", "Code", "Vehicle Model Name", "Vehicle VIN"]

    # Permanent side-by-side multi-perspective presentation grid
    drilldown_col1, drilldown_col2 = st.columns(2)
    
    with drilldown_col1:
        if chart_style == "Standard Nested Radial Sunburst":
            fig1 = px.sunburst(df, path=model_hierarchy, color_discrete_sequence=px.colors.qualitative.Safe)
            title_text = "By Vehicle Model (Sunburst)"
        elif chart_style == "Standard Rectangular Nested Treemap":
            fig1 = px.treemap(df, path=model_hierarchy, color_discrete_sequence=px.colors.qualitative.Pastel)
            title_text = "By Vehicle Model (Treemap)"
        else:
            fig1 = px.icicle(df, path=model_hierarchy, color_discrete_sequence=px.colors.qualitative.Set3)
            title_text = "By Vehicle Model (Icicle)"
            
        fig1.update_layout(margin=dict(t=25, l=5, r=5, b=5), height=340, title_text=title_text, title_font_size=13)
        st.plotly_chart(fig1, use_container_width=True)
        
    with drilldown_col2:
        if chart_style == "Standard Nested Radial Sunburst":
            fig2 = px.sunburst(df, path=dtc_hierarchy, color_discrete_sequence=px.colors.qualitative.Safe)
            title_text = "By DTC / Fault Code (Sunburst)"
        elif chart_style == "Standard Rectangular Nested Treemap":
            fig2 = px.treemap(df, path=dtc_hierarchy, color_discrete_sequence=px.colors.qualitative.Pastel)
            title_text = "By DTC / Fault Code (Treemap)"
        else:
            fig2 = px.icicle(df, path=dtc_hierarchy, color_discrete_sequence=px.colors.qualitative.Set3)
            title_text = "By DTC / Fault Code (Icicle)"
            
        fig2.update_layout(margin=dict(t=25, l=5, r=5, b=5), height=340, title_text=title_text, title_font_size=13)
        st.plotly_chart(fig2, use_container_width=True)

    # Bottom Profile Summary Metrics
    st.write("---")
    c_1, c_2, c_3 = st.columns(3)
    with c_1:
        code_counts = df['Code'].value_counts().reset_index().head(10)
        code_counts.columns = ['Code', 'Count']
        fig_code = px.bar(code_counts, x='Code', y='Count', color_continuous_scale=px.colors.sequential.Viridis)
        fig_code.update_layout(margin=dict(t=20, b=5, l=5, r=5), height=210, title_text="Top Fault Codes", title_font_size=12)
        st.plotly_chart(fig_code, use_container_width=True)
        
    with c_2:
        module_counts = df['Module'].value_counts().reset_index()
        module_counts.columns = ['Module', 'Count']
        fig_module = px.bar(module_counts, x='Module', y='Count', color_continuous_scale=px.colors.sequential.Plasma)
        fig_module.update_layout(margin=dict(t=20, b=5, l=5, r=5), height=210, title_text="Module Metrics Distribution", title_font_size=12)
        st.plotly_chart(fig_module, use_container_width=True)
        
    with c_3:
        status_df = df.groupby(['Module', 'Status']).size().reset_index(name='Count')
        fig_status = px.bar(status_df, x='Count', y='Module', color='Status', orientation='h', color_discrete_sequence=px.colors.qualitative.Safe)
        fig_status.update_layout(
            barmode='stack', margin=dict(t=20, b=5, l=5, r=5), height=210, 
            title_text="ECU Workload Status Stack", title_font_size=12,
            legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, font_size=8, title_font_size=8)
        )
        st.plotly_chart(fig_status, use_container_width=True)


def render_data_registry_grid(df_master):
    """Renders the data editor grid with filters."""
    filterable_columns = ["File Name", "Module", "Code", "Status", "Reviewer", "Vehicle Model Name", "Vehicle VIN"]
    filter_cols = st.columns(len(filterable_columns))
    active_filters = {}
    
    for col_idx, col_name in enumerate(filterable_columns):
        with filter_cols[col_idx]:
            opts = sorted(df_master[col_name].dropna().unique().tolist())
            selected_vals = st.multiselect(col_name, options=opts, default=None, key=f"ex_fltr_{col_name}", placeholder="All")
            if selected_vals: 
                active_filters[col_name] = selected_vals

    df_filtered = df_master.copy()
    for col_name, selected_values in active_filters.items():
        df_filtered = df_filtered[df_filtered[col_name].isin(selected_values)]
        
    all_disabled_fields = ["File Name", "Module", "Code", "Description", "Vehicle Model Name", "Vehicle VIN", "Last Updated"]
    
    edited_df = st.data_editor(
        df_filtered, 
        disabled=all_disabled_fields, 
        hide_index=True, 
        use_container_width=True, 
        key="data_editor_registry", 
        height=380
    )
    
    if not edited_df.equals(df_filtered):
        return edited_df, True
    return df_master, False


def render_export_module(df):
    """Renders the excel download module."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Diagnostic Report')
    st.download_button(
        label="📥 Export Report to Excel (.xlsx)", 
        data=buffer.getvalue(), 
        file_name=f"Report_{datetime.now().strftime('%Y%m%d')}.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )