import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import io
import uuid
import logging

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Storage Bay Designer app")

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Storage Bay Designer", page_icon="📐")

# --- Custom CSS for Modern Look ---
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
        font-family: 'Helvetica', sans-serif;
    }
    .stSidebar {
        background-color: #ffffff;
        padding: 20px;
        border-right: 1px solid #ddd;
    }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
        margin: 5px 0;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
    }
    .stNumberInput input, .stTextInput input {
        border-radius: 4px;
        border: 1px solid #ccc;
    }
    .stExpander {
        margin-bottom: 10px;
    }
    .stExpander > div > div {
        padding: 10px;
    }
    .preview-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        background-color: white;
    }
    .metric-box {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    [data-theme="dark"] .stApp {
        background-color: #212121;
    }
    [data-theme="dark"] .stSidebar {
        background-color: #2c2c2c;
        border-right: 1px solid #444;
    }
    [data-theme="dark"] .preview-container {
        background-color: #333;
        border-color: #555;
    }
    [data-theme="dark"] .metric-box {
        background-color: #1b5e20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def draw_dimension_line(ax, x1, y1, x2, y2, text, is_vertical=False, offset=10, color='black', fontsize=8):
    """Draws a dimension line with arrows and text."""
    ax.plot([x1, x2], [y1, y2], color=color, lw=1)
    if is_vertical:
        ax.plot([x1, x1], [y1, y1 + 5], color=color, lw=1)
        ax.plot([x2, x2], [y2, y2 - 5], color=color, lw=1)
        ax.text(x1 + offset, (y1 + y2) / 2, text, va='center', ha='left', fontsize=fontsize, color=color)
    else:
        ax.plot([x1, x1 + 5], [y1, y1], color=color, lw=1)
        ax.plot([x2, x2 - 5], [y2, y2], color=color, lw=1)
        ax.text((x1 + x2) / 2, y1 + offset, text, va='bottom', ha='center', fontsize=fontsize, color=color)

@st.cache_data
def draw_bay_group(params):
    """Draws a 2D bay design with clear dimensions."""
    bay_width = params['bay_width']
    total_height = params['total_height']
    ground_clearance = params['ground_clearance']
    depth = params['depth']
    shelf_thickness = params['shelf_thickness']
    side_thickness = params['side_panel_thickness']
    num_rows = params['num_rows']
    has_top_cap = params['has_top_cap']
    color = params['color']
    bin_heights = params['bin_heights']
    bin_counts = params['bin_counts_per_row']
    zoom = params.get('zoom', 1.0)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor('#f0f0f0')
    ax.grid(False)

    # Draw side panels and shelves
    ax.add_patch(Rectangle((-side_thickness, 0), side_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))
    ax.add_patch(Rectangle((bay_width, 0), side_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))

    current_y = ground_clearance
    for i in range(num_rows):
        shelf_y = current_y
        ax.add_patch(Rectangle((0, shelf_y), bay_width, shelf_thickness, facecolor='none', edgecolor=color, lw=1.5))
        if i < len(bin_heights):
            bin_height = bin_heights[i]
            bin_y = shelf_y + shelf_thickness
            bin_top = bin_y + bin_height
            num_bins = bin_counts[i]
            bin_width = bay_width / num_bins

            # Draw bins
            for j in range(num_bins):
                bin_x = j * bin_width
                ax.add_patch(Rectangle((bin_x, bin_y), bin_width, bin_height, facecolor='#e0e0e0', edgecolor=color, lw=1, alpha=0.5))
                # Dimension inside bin
                ax.text(bin_x + bin_width / 2, bin_y + bin_height / 2, f"{bin_width:.0f}x{depth:.0f}",
                        ha='center', va='center', fontsize=8, color='black', bbox=dict(facecolor='white', alpha=0.7))

            # Shelf height dimension
            draw_dimension_line(ax, bay_width + side_thickness + 10, bin_y, bay_width + side_thickness + 10, bin_top,
                              f"{bin_height:.0f}", True, 5, '#2196F3')

            current_y = bin_top

    if has_top_cap:
        ax.add_patch(Rectangle((0, total_height - shelf_thickness), bay_width, shelf_thickness, facecolor='none', edgecolor=color, lw=1.5))

    # Overall dimensions
    draw_dimension_line(ax, -side_thickness - 10, 0, bay_width + side_thickness + 10, 0, f"Width: {bay_width + 2 * side_thickness:.0f}", False, 5, 'black')
    draw_dimension_line(ax, -side_thickness - 20, 0, -side_thickness - 20, total_height, f"Height: {total_height:.0f}", True, 5, 'black')
    draw_dimension_line(ax, -side_thickness - 30, 0, -side_thickness - 30, depth, f"Depth: {depth:.0f}", True, 5, 'black')

    ax.set_xlim(-side_thickness * 2 - 30, bay_width + side_thickness * 2 + 30)
    ax.set_ylim(-10, max(total_height, depth) + 10)
    ax.axis('off')
    return fig

def create_editable_export(bay_group, format_type):
    """Creates an export file from bay group data."""
    logger.debug(f"Processing group: {bay_group['name']} in {format_type} format")
    fig = draw_bay_group(bay_group)
    export_buf = io.BytesIO()
    if format_type == 'svg':
        fig.savefig(export_buf, format='svg', bbox_inches='tight', pad_inches=0.1)
        filename = "bay_design.svg"
        mime_type = "image/svg+xml"
    elif format_type == 'png':
        fig.savefig(export_buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=300)
        filename = "bay_design.png"
        mime_type = "image/png"
    elif format_type == 'pdf':
        fig.savefig(export_buf, format='pdf', bbox_inches='tight', pad_inches=0.1)
        filename = "bay_design.pdf"
        mime_type = "application/pdf"
    plt.close(fig)
    export_buf.seek(0)
    return export_buf, filename, mime_type

def update_bin_counts():
    if len(group_data['bin_counts_per_row']) != group_data['num_rows']:
        if group_data['num_rows'] > len(group_data['bin_counts_per_row']):
            group_data['bin_counts_per_row'].extend([3] * (group_data['num_rows'] - len(group_data['bin_counts_per_row'])))
        else:
            group_data['bin_counts_per_row'] = group_data['bin_counts_per_row'][:group_data['num_rows']]

def update_total_height():
    total_shelf_h = (group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)) * group_data['shelf_thickness']
    group_data['total_height'] = sum(group_data['bin_heights']) + total_shelf_h + group_data['ground_clearance']

# --- Initialize Session State ---
if 'bay_group' not in st.session_state:
    st.session_state.bay_group = {
        "id": str(uuid.uuid4()),
        "name": "Bay Design",
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "depth": 600.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "num_rows": 3,
        "has_top_cap": True,
        "color": "#2196F3",
        "bin_heights": [650.0, 650.0, 650.0],
        "bin_counts_per_row": [3, 3, 3],
        "zoom": 1.0
    }

group_data = st.session_state.bay_group
update_bin_counts()
update_total_height()

# --- UI Layout ---
st.title("Storage Bay Designer")
st.markdown("Create and visualize storage bay designs with precise dimensions.")

# Sidebar Configuration
with st.sidebar:
    st.header("Design Settings")
    with st.expander("Basic Dimensions", expanded=True):
        group_data['bay_width'] = st.number_input("Bay Width (mm)", min_value=300.0, value=group_data['bay_width'], step=50.0, key=f"width_{group_data['id']}")
        group_data['depth'] = st.number_input("Bay Depth (mm)", min_value=300.0, value=group_data['depth'], step=50.0, key=f"depth_{group_data['id']}")
        group_data['ground_clearance'] = st.number_input("Ground Clearance (mm)", min_value=0.0, value=group_data['ground_clearance'], step=10.0, key=f"clearance_{group_data['id']}", on_change=update_total_height)
        group_data['shelf_thickness'] = st.number_input("Shelf Thickness (mm)", min_value=10.0, value=group_data['shelf_thickness'], step=1.0, key=f"shelf_thick_{group_data['id']}", on_change=update_total_height)
        group_data['side_panel_thickness'] = st.number_input("Side Panel Thickness (mm)", min_value=10.0, value=group_data['side_panel_thickness'], step=1.0, key=f"side_thick_{group_data['id']}")
        group_data['has_top_cap'] = st.checkbox("Include Top Cap", value=group_data['has_top_cap'], key=f"top_cap_{group_data['id']}", on_change=update_total_height)
    
    with st.expander("Shelf Configuration", expanded=True):
        group_data['num_rows'] = st.number_input("Number of Shelves", min_value=1, max_value=10, value=group_data['num_rows'], step=1, key=f"rows_{group_data['id']}", on_change=update_bin_counts)
        for i in range(group_data['num_rows']):
            col1, col2 = st.columns(2)
            with col1:
                group_data['bin_heights'][i] = st.number_input(f"Shelf {chr(65 + i)} Height (mm)", min_value=100.0, value=group_data['bin_heights'][i], step=10.0, key=f"height_{i}_{group_data['id']}", on_change=update_total_height)
            with col2:
                group_data['bin_counts_per_row'][i] = st.number_input(f"Shelf {chr(65 + i)} Bin Count", min_value=1, max_value=10, value=group_data['bin_counts_per_row'][i], step=1, key=f"bins_{i}_{group_data['id']}")
    
    with st.expander("Visual Settings"):
        group_data['color'] = st.color_picker("Bay Color", value=group_data['color'], key=f"color_{group_data['id']}")
        group_data['zoom'] = st.slider("Zoom Level", 0.5, 2.0, group_data['zoom'], 0.1, key=f"zoom_{group_data['id']}")
    
    if st.button("Reset to Defaults"):
        st.session_state.bay_group = {
            "id": str(uuid.uuid4()),
            "name": "Bay Design",
            "bay_width": 1050.0,
            "total_height": 2000.0,
            "ground_clearance": 50.0,
            "depth": 600.0,
            "shelf_thickness": 18.0,
            "side_panel_thickness": 18.0,
            "num_rows": 3,
            "has_top_cap": True,
            "color": "#2196F3",
            "bin_heights": [650.0, 650.0, 650.0],
            "bin_counts_per_row": [3, 3, 3],
            "zoom": 1.0
        }
        update_bin_counts()
        update_total_height()
        st.rerun()

# Main Area
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Design Metrics")
    with st.container():
        st.markdown('<div class="metric-box">Total Height: {:.0f} mm</div>'.format(group_data['total_height']), unsafe_allow_html=True)
        st.markdown('<div class="metric-box">Total Width: {:.0f} mm</div>'.format(group_data['bay_width'] + 2 * group_data['side_panel_thickness']), unsafe_allow_html=True)
        st.markdown('<div class="metric-box">Depth: {:.0f} mm</div>'.format(group_data['depth']), unsafe_allow_html=True)

with col2:
    st.subheader("Design Preview")
    with st.container():
        st.markdown('<div class="preview-container">', unsafe_allow_html=True)
        if st.checkbox("Show Preview", value=False):
            with st.spinner("Rendering..."):
                fig = draw_bay_group(group_data)
                st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

# Export Section
with st.sidebar:
    st.header("Export")
    export_format = st.selectbox("Format", ["svg", "png", "pdf"], key="export_format")
    if st.button("Download Design"):
        with st.spinner(f"Generating {export_format.upper()}..."):
            export_buf, filename, mime_type = create_editable_export(group_data, export_format)
            st.download_button(label=f"Download {export_format.upper()}", data=export_buf, file_name=filename, mime=mime_type)
