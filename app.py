import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import uuid
import logging

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Storage Bay Designer app")

# --- Page Configuration (Must be the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Storage Bay Designer", page_icon="📐")

# --- Custom CSS for Improved Styling (Theme-Aware) ---
st.markdown("""
<style>
    .stApp {
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #4A90E2;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #357ABD;
    }
    .stSidebar .stNumberInput input, .stSidebar .stTextInput input {
        border: 1px solid var(--text-color, #ccc);
        border-radius: 4px;
    }
    .stError, .error-container {
        background-color: var(--background-color, #ffe6e6);
        border-left: 4px solid #ff4d4d;
        padding: 10px;
        border-radius: 4px;
        color: var(--text-color, #d8000c);
    }
    h1, h2, h3, .stSidebar .stMarkdown {
        color: var(--text-color, #333);
    }
    .stMetric {
        background-color: var(--background-color, #e6f3ff);
        padding: 10px;
        border-radius: 4px;
        color: var(--text-color, #333);
    }
    /* Ensure text visibility in dark mode */
    [data-theme="dark"] .stSidebar .stMarkdown,
    [data-theme="dark"] h1,
    [data-theme="dark"] h2,
    [data-theme="dark"] h3,
    [data-theme="dark"] .stMetric {
        color: #ffffff !important;
    }
    [data-theme="dark"] .stError, [data-theme="dark"] .error-container {
        background-color: #4a0000;
        color: #ff9999;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def hex_to_rgb(hex_color):
    """Converts a hex color structure to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_dimension_line(ax, x1, y1, x2, y2, text, is_vertical=False, offset=10, color='black', fontsize=12):
    """Draws a dimension line with arrows and text on the matplotlib axis."""
    ax.plot([x1, x2], [y1, y2], color=color, lw=1)
    if is_vertical:
        ax.plot(x1, y1, marker='v', color=color, markersize=5)
        ax.plot(x2, y2, marker='^', color=color, markersize=5)
        ax.text(x1 + offset, (y1 + y2) / 2, text, va='center', ha='left', fontsize=fontsize, rotation=90, color=color)
    else:
        ax.plot(x1, y1, marker='<', color=color, markersize=5)
        ax.plot(x2, y2, marker='>', color=color, markersize=5)
        ax.text((x1 + x2) / 2, y1 + offset, text, va='bottom', ha='center', fontsize=fontsize, color=color)

def validate_group_params(params):
    """Validates bay group parameters and returns errors if any."""
    errors = []
    if params['bay_width'] <= 0:
        errors.append("Bay width must be positive.")
    if params['total_height'] <= 0:
        errors.append("Total height must be positive.")
    if params['ground_clearance'] < 0:
        errors.append("Ground clearance cannot be negative.")
    if params['shelf_thickness'] <= 0:
        errors.append("Shelf thickness must be positive.")
    if params['side_panel_thickness'] <= 0:
        errors.append("Side panel thickness must be positive.")
    if params['num_cols'] < 1:
        errors.append("Number of columns must be at least 1.")
    if params['num_rows'] < 1:
        errors.append("Number of rows must be at least 1.")
    total_net_bin_h = sum(params['bin_heights'])
    num_shelves = params['num_rows'] + (1 if params['has_top_cap'] else 0)
    required_height = total_net_bin_h + num_shelves * params['shelf_thickness'] + params['ground_clearance']
    if abs(required_height - params['total_height']) > 0.1:
        errors.append(f"Calculated height ({required_height:.1f} mm) does not match target height ({params['total_height']:.1f} mm).")
    return errors

@st.cache_data
def draw_bay_group(params):
    """Draws a single bay using Matplotlib for the LIVE PREVIEW."""
    bay_width = params['bay_width']
    total_height = params['total_height']
    ground_clearance = params['ground_clearance']
    shelf_thickness = params['shelf_thickness']
    side_panel_thickness = params['side_panel_thickness']
    num_cols = params['num_cols']
    num_rows = params['num_rows']
    has_top_cap = params['has_top_cap']
    color = params['color']
    bin_heights = params['bin_heights']
    zoom_factor = params.get('zoom', 1.0)

    visual_shelf_thickness = min(shelf_thickness, 18.0)
    visual_side_panel_thickness = max(side_panel_thickness, 10.0)

    core_width = bay_width
    total_group_width = core_width + (2 * side_panel_thickness)
    dim_offset_x = 0.1 * core_width
    dim_offset_y = 0.05 * total_height
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.grid(True, linestyle='--', alpha=0.2)

    ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))
    ax.add_patch(patches.Rectangle((core_width, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))

    net_width_per_bay = bay_width - 2 * side_panel_thickness
    bin_width = net_width_per_bay / num_cols if num_cols > 0 else 0

    bin_start_x = 0
    if num_cols > 1:
        for i in range(1, num_cols):
            split_x = bin_start_x + (i * bin_width)
            ax.add_patch(patches.Rectangle((split_x, ground_clearance), 0, total_height - ground_clearance, facecolor='none', edgecolor=color, lw=1.5))

    current_y = ground_clearance
    pitch_offset_x = dim_offset_x * 2.5

    # Dynamic vertical offset for text to prevent overlap
    vertical_text_offset = 0
    text_spacing = max(10.0, total_height / (num_rows * 2))

    for i in range(num_rows):
        shelf_bottom_y = current_y
        ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, shelf_bottom_y), total_group_width, visual_shelf_thickness, facecolor='none', edgecolor=color, lw=1.5))
        shelf_top_y = shelf_bottom_y + shelf_thickness
        
        if i < len(bin_heights):
            net_bin_h = bin_heights[i]
            pitch_h = net_bin_h + shelf_thickness
            pitch_top_y = shelf_bottom_y + pitch_h
            level_name = chr(65 + i)
            
            bin_bottom_y = shelf_top_y
            bin_top_y = bin_bottom_y + net_bin_h
            draw_dimension_line(ax, core_width + visual_side_panel_thickness + dim_offset_x, bin_bottom_y, core_width + visual_side_panel_thickness + dim_offset_x, bin_top_y, f"{net_bin_h:.1f}", is_vertical=True, offset=5, color='#3b82f6', fontsize=12)
            draw_dimension_line(ax, core_width + visual_side_panel_thickness + pitch_offset_x, shelf_bottom_y, core_width + visual_side_panel_thickness + pitch_offset_x, pitch_top_y, f"{pitch_h:.1f}", is_vertical=True, offset=5, color='black', fontsize=12)

            # Adjust text position with dynamic offset to prevent overlap
            text_x = -visual_side_panel_thickness - dim_offset_x * 1.5
            text_y = (bin_bottom_y + bin_top_y) / 2 + vertical_text_offset
            ax.text(text_x, text_y, level_name, va='center', ha='right', fontsize=12, fontweight='bold', color='black')

            # Increment vertical offset for the next text to avoid overlap
            vertical_text_offset += text_spacing / (zoom_factor if zoom_factor > 1 else 1)

            current_y = bin_top_y

    if has_top_cap:
        ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, total_height - visual_shelf_thickness), total_group_width, visual_shelf_thickness, facecolor='none', edgecolor=color, lw=1.5))

    # Move ground clearance dimension to below the design
    draw_dimension_line(ax, -visual_side_panel_thickness, -dim_offset_y * 2, core_width + visual_side_panel_thickness, -dim_offset_y * 2, f"Ground Clearance: {ground_clearance:.0f} mm", offset=10, color='black', fontsize=12)

    draw_dimension_line(ax, -visual_side_panel_thickness, -dim_offset_y * 4, core_width + visual_side_panel_thickness, -dim_offset_y * 4, f"Total Group Width: {total_group_width:.0f} mm", offset=10, color='black', fontsize=12)
    draw_dimension_line(ax, -visual_side_panel_thickness - (dim_offset_x * 4), 0, -visual_side_panel_thickness - (dim_offset_x * 4), total_height, f"Total Height: {total_height:.0f} mm", is_vertical=True, offset=10, color='black', fontsize=12)

    if num_cols > 0:
        dim_y_pos = total_height + dim_offset_y
        bin_start_x = 0
        for i in range(num_cols):
            dim_start_x = bin_start_x + (i * bin_width)
            dim_end_x = dim_start_x + bin_width
            draw_dimension_line(ax, dim_start_x, dim_y_pos, dim_end_x, dim_y_pos, f"{bin_width:.1f}", offset=10, color='#3b82f6', fontsize=12)

    ax.set_aspect('equal', adjustable='box')
    padding_x = core_width * 0.4 + visual_side_panel_thickness
    ax.set_xlim((-padding_x) * zoom_factor, (core_width + padding_x) * zoom_factor)
    ax.set_ylim(-dim_offset_y * 5 * zoom_factor, total_height + dim_offset_y * 2 * zoom_factor)
    ax.axis('off')
    
    return fig

def create_editable_export(bay_group, format_type):
    """Creates an export file (SVG, PNG, or PDF) from bay group data using Matplotlib."""
    logger.debug(f"Processing group: {bay_group['name']} in {format_type} format")
    fig = draw_bay_group(bay_group)
    
    export_buf = io.BytesIO()
    if format_type == 'svg':
        fig.savefig(export_buf, format='svg', bbox_inches='tight', pad_inches=0.1)
        filename = "storage_bay_design.svg"
        mime_type = "image/svg+xml"
    elif format_type == 'png':
        fig.savefig(export_buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        filename = "storage_bay_design.png"
        mime_type = "image/png"
    elif format_type == 'pdf':
        fig.savefig(export_buf, format='pdf', bbox_inches='tight', pad_inches=0.1)
        filename = "storage_bay_design.pdf"
        mime_type = "application/pdf"
    
    plt.close(fig)
    export_buf.seek(0)
    
    return export_buf, filename, mime_type

# --- Initialize Session State ---
if 'bay_group' not in st.session_state:
    st.session_state.bay_group = {
        "id": str(uuid.uuid4()),
        "name": "Bay Design",
        "num_bays": 1,
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "num_cols": 3,
        "num_rows": 3,
        "has_top_cap": True,
        "color": "#4A90E2",
        "bin_heights": [350.0] * 3,
        "lock_heights": [False] * 3,
        "zoom": 1.5
    }

group_data = st.session_state.bay_group

def distribute_total_height():
    num_shelves_for_calc = group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)
    total_shelf_thickness = num_shelves_for_calc * group_data['shelf_thickness']
    available_space = group_data['total_height'] - group_data['ground_clearance'] - total_shelf_thickness
    unlocked_indices = [i for i, locked in enumerate(group_data['lock_heights']) if not locked]
    num_unlocked = len(unlocked_indices)
    if available_space > 0 and num_unlocked > 0:
        uniform_net_h = available_space / num_unlocked
        for i in unlocked_indices:
            group_data['bin_heights'][i] = uniform_net_h

def update_total_height():
    num_shelves_for_calc = group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)
    total_shelf_h = num_shelves_for_calc * group_data['shelf_thickness']
    total_net_bin_h = sum(group_data['bin_heights'])
    group_data['total_height'] = total_net_bin_h + total_shelf_h + group_data['ground_clearance']

# --- UI and Logic ---
st.title("Storage Bay Designer")
st.markdown("Design a single storage bay with real-time previews and download as an editable file.")

# Sidebar Introduction
st.sidebar.markdown("""
**How to Use**  
1. Configure the bay’s dimensions and layout below.  
2. View the real-time preview on the right.  
3. Download a file when satisfied with the design.
""")

# Reset Button
if st.sidebar.button("Reset to Defaults", help="Reset all settings to default values."):
    st.session_state.bay_group = {
        "id": str(uuid.uuid4()),
        "name": "Bay Design",
        "num_bays": 1,
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "num_cols": 3,
        "num_rows": 3,
        "has_top_cap": True,
        "color": "#4A90E2",
        "bin_heights": [350.0] * 3,
        "lock_heights": [False] * 3,
        "zoom": 1.5
    }
    st.rerun()

# Quick Presets
st.sidebar.header("Quick Presets", divider="gray")
col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Small Bay", help="Apply settings for a small storage bay."):
        group_data.update({
            "bay_width": 600.0,
            "total_height": 1200.0,
            "num_rows": 2,
            "num_cols": 2,
            "bin_heights": [350.0] * 2,
            "lock_heights": [False] * 2,
            "ground_clearance": 50.0,
            "shelf_thickness": 18.0,
            "side_panel_thickness": 18.0,
            "has_top_cap": True,
            "color": "#4A90E2",
            "zoom": 1.5
        })
        update_total_height()
        st.rerun()
with col2:
    if st.button("Medium Bay", help="Apply settings for a medium storage bay."):
        group_data.update({
            "bay_width": 1050.0,
            "total_height": 2000.0,
            "num_rows": 3,
            "num_cols": 3,
            "bin_heights": [350.0] * 3,
            "lock_heights": [False] * 3,
            "ground_clearance": 50.0,
            "shelf_thickness": 18.0,
            "side_panel_thickness": 18.0,
            "has_top_cap": True,
            "color": "#4A90E2",
            "zoom": 1.5
        })
        update_total_height()
        st.rerun()
with col3:
    if st.button("Large Bay", help="Apply settings for a large storage bay."):
        group_data.update({
            "bay_width": 1500.0,
            "total_height": 3000.0,
            "num_rows": 4,
            "num_cols": 4,
            "bin_heights": [400.0] * 4,
            "lock_heights": [False] * 4,
            "ground_clearance": 50.0,
            "shelf_thickness": 18.0,
            "side_panel_thickness": 18.0,
            "has_top_cap": True,
            "color": "#4A90E2",
            "zoom": 1.5
        })
        update_total_height()
        st.rerun()

# Error Display
errors = validate_group_params(group_data)
if errors:
    st.sidebar.markdown("<div class='error-container'>**Configuration Errors**</div>", unsafe_allow_html=True)
    for e in errors:
        st.sidebar.markdown(f"<div class='error-container'>• {e}</div>", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("Configure Bay Design", divider="gray")
with st.sidebar.expander("Bay Configuration", expanded=False):
    st.markdown("**Set bay dimensions and materials.**")
    group_data['ground_clearance'] = st.number_input("Ground Clearance (mm)", min_value=0.0, value=float(group_data['ground_clearance']), key=f"ground_clearance_{group_data['id']}", on_change=update_total_height, help="Height from ground to the first shelf.")
    group_data['has_top_cap'] = st.checkbox("Include Top Cap", value=group_data['has_top_cap'], key=f"has_top_cap_{group_data['id']}", on_change=update_total_height, help="Add a top cap shelf to the bay.")
    group_data['shelf_thickness'] = st.number_input("Shelf Thickness (mm)", min_value=1.0, value=float(group_data['shelf_thickness']), key=f"shelf_thick_{group_data['id']}", on_change=update_total_height, help="Thickness of each shelf.")
    group_data['side_panel_thickness'] = st.number_input("Side Panel Thickness (mm)", min_value=1.0, value=float(group_data['side_panel_thickness']), key=f"side_panel_thick_{group_data['id']}", help="Thickness of the outer side panels.")
    group_data['color'] = st.color_picker("Structure Color", value=group_data['color'], key=f"color_{group_data['id']}", help="Color of the bay structure in the preview.")

with st.sidebar.expander("Layout", expanded=False):
    st.markdown("**Configure the bay layout.**")
    prev_num_rows = group_data['num_rows']
    group_data['num_rows'] = st.number_input("Shelves (Rows)", min_value=1, max_value=10, value=int(group_data['num_rows']), key=f"num_rows_{group_data['id']}", on_change=update_total_height, help="Number of shelves (rows) in the bay (max 10).")
    group_data['num_cols'] = st.number_input("Bin Columns", min_value=1, max_value=10, value=int(group_data['num_cols']), key=f"num_cols_{group_data['id']}", help="Number of bin columns in the bay (max 10).")

    if prev_num_rows != group_data['num_rows']:
        if group_data['num_rows'] > len(group_data['bin_heights']):
            default_height = group_data['bin_heights'][0] if group_data['bin_heights'] else 350.0
            group_data['bin_heights'].extend([default_height] * (group_data['num_rows'] - len(group_data['bin_heights'])))
            group_data['lock_heights'].extend([False] * (group_data['num_rows'] - len(group_data['lock_heights'])))
        else:
            group_data['bin_heights'] = group_data['bin_heights'][:group_data['num_rows']]
            group_data['lock_heights'] = group_data['lock_heights'][:group_data['num_rows']]
        update_total_height()

with st.sidebar.expander("Bin Height Settings", expanded=False):
    st.markdown("**Configure bin heights.**")
    auto_distribute = st.checkbox("Auto-distribute Heights", value=True, key=f"auto_distribute_{group_data['id']}", help="Automatically distribute available height evenly across bins.")
    if not auto_distribute:
        heights_input = st.text_input("Bin Heights (mm, comma-separated)", value=",".join(str(h) for h in group_data['bin_heights']), key=f"heights_{group_data['id']}", help="Enter heights for each level, e.g., 350,350,350")
        try:
            new_heights = [float(h) for h in heights_input.split(",") if h.strip()]
            if len(new_heights) != group_data['num_rows']:
                st.error(f"Number of heights ({len(new_heights)}) must match number of rows ({group_data['num_rows']}).")
            elif any(h <= 0 for h in new_heights):
                st.error("All bin heights must be positive numbers.")
            else:
                group_data['bin_heights'] = new_heights
                group_data['lock_heights'] = [False] * len(new_heights)
                update_total_height()
        except ValueError:
            st.error("Invalid height format. Use comma-separated numbers (e.g., 350,350,350).")
    else:
        distribute_total_height()

with st.sidebar.expander("Advanced Settings", expanded=False):
    st.markdown("**Adjust advanced visual settings.**")
    group_data['zoom'] = st.slider("Zoom Level", 1.0, 5.0, group_data['zoom'], 0.1, key=f"zoom_{group_data['id']}", help="Adjust the zoom level for the preview and export.")

# Calculated Height Metric
total_net_bin_h = sum(group_data['bin_heights'])
num_shelves_for_calc = group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)
total_shelf_h = num_shelves_for_calc * group_data['shelf_thickness']
calculated_total_height = total_net_bin_h + total_shelf_h + group_data['ground_clearance']
st.sidebar.metric("Calculated Total Height", f"{calculated_total_height:.1f} mm", help="Sum of bin heights, shelf thicknesses, and ground clearance.")

# Main Area Layout
col1, col2 = st.columns([1, 2])
with col1:
    st.header("Key Settings")
    group_data['bay_width'] = st.number_input("Bay Width (mm)", min_value=1.0, value=float(group_data['bay_width']), key=f"bay_width_{group_data['id']}", help="Width of the bay in millimeters.")
    group_data['total_height'] = st.number_input("Target Total Height (mm)", min_value=1.0, value=float(group_data['total_height']), key=f"total_height_{group_data['id']}", on_change=distribute_total_height, help="Total height of the bay.")

with col2:
    st.header(f"Design Preview: {group_data['name']}")
    show_preview = st.checkbox("Show Live Preview", value=False, help="Toggle real-time design preview to improve performance.")
    if show_preview and not errors:
        with st.spinner("Rendering preview..."):
            fig = draw_bay_group(group_data)
            st.pyplot(fig, use_container_width=True)
    elif errors:
        st.error("Please resolve configuration errors to view the design.")

# SVG Download
st.sidebar.header("Export Design", divider="gray")
export_format = st.selectbox("Export Format", ["svg", "png", "pdf"], index=0, help="Choose the file format for export.")
if st.sidebar.button("Download File", type="primary", help="Download the bay design in the selected format."):
    if not errors:
        with st.spinner(f"Generating {export_format.upper()}..."):
            export_buffer, filename, mime_type = create_editable_export(group_data, export_format)
            if export_buffer:
                st.sidebar.download_button(
                    label=f"Download {export_format.upper()} File",
                    data=export_buffer,
                    file_name=filename,
                    mime=mime_type,
                    type="primary",
                    help=f"Download the generated {export_format.upper()} file."
                )
            else:
                st.sidebar.error(f"Failed to generate {export_format.upper()} file. Please check configuration.")
    else:
        st.sidebar.error("Cannot generate file due to configuration errors.")
