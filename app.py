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

# --- Custom CSS for Professional Look ---
st.markdown("""
<style>
    .stApp {
        background-color: #f9f9f9;
        font-family: 'Arial', sans-serif;
    }
    .stSidebar {
        background-color: #ffffff;
        padding: 20px;
        border-right: 1px solid #ccc;
    }
    .stButton>button {
        background-color: #1976d2;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
        margin: 5px 0;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1565c0;
    }
    .stNumberInput input, .stTextInput input {
        border-radius: 4px;
        border: 1px solid #bbb;
    }
    .stExpander {
        margin-bottom: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .stExpander > div > div {
        padding: 10px;
    }
    .preview-container {
        border: 1px solid #bbb;
        border-radius: 4px;
        padding: 10px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-box {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 14px;
        color: #1e88e5;
    }
    [data-theme="dark"] .stApp {
        background-color: #1e1e1e;
    }
    [data-theme="dark"] .stSidebar {
        background-color: #2c2c2c;
        border-right: 1px solid #444;
    }
    [data-theme="dark"] .preview-container {
        background-color: #2c2c2c;
        border-color: #555;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    [data-theme="dark"] .metric-box {
        background-color: #103a6d;
        color: #bbdefb;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_default_bay_group():
    """Returns the default dictionary for a new bay group."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Storage Bay Design",
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "depth": 600.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "num_rows": 3,
        "has_top_cap": True,
        "color": "#1976d2",
        "bin_heights": [650.0, 650.0, 650.0],
        "bin_counts_per_row": [3, 3, 3],
        "zoom": 1.0
    }

def draw_dimension_line(ax, x1, y1, x2, y2, text, is_vertical=False, offset=15, color='black', fontsize=10):
    """Draws a dimension line with arrows and bold text."""
    ax.plot([x1, x2], [y1, y2], color=color, lw=0.5, linestyle='--')
    if is_vertical:
        ax.plot([x1, x1], [y1, y1 + 5], color=color, lw=0.5)
        ax.plot([x2, x2], [y2, y2 - 5], color=color, lw=0.5)
        ax.text(x1 + offset, (y1 + y2) / 2, text, va='center', ha='left', fontsize=fontsize, color=color, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    else:
        ax.plot([x1, x1 + 5], [y1, y1], color=color, lw=0.5)
        ax.plot([x2, x2 - 5], [y2, y2], color=color, lw=0.5)
        ax.text((x1 + x2) / 2, y1 + offset, text, va='bottom', ha='center', fontsize=fontsize, color=color, fontweight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

@st.cache_data
def draw_bay_group(params):
    """Draws a professional 2D bay design with clear, non-overlapping dimensions."""
    bay_width = params['bay_width']
    total_height = params['total_height']
    ground_clearance = params['ground_clearance']
    depth = params['depth']  # Fixed, shown separately
    shelf_thickness = params['shelf_thickness']
    side_thickness = params['side_panel_thickness']
    num_rows = params['num_rows']
    has_top_cap = params['has_top_cap']
    color = params['color']
    bin_heights = params['bin_heights']
    bin_counts = params['bin_counts_per_row']
    zoom = params.get('zoom', 1.0)
    design_name = params.get('name', "Storage Bay Design")

    fig, ax = plt.subplots(figsize=(12 * zoom, 8 * zoom), dpi=100)
    ax.set_facecolor('#f5f5f5')
    ax.grid(False)

    # Title block with custom name
    ax.text(0.5, 1.02, f"{design_name} - Rev 1.0", transform=ax.transAxes, ha='center', va='bottom', fontsize=12, fontweight='bold', color='#424242')

    # Draw side panels and shelves
    ax.add_patch(Rectangle((-side_thickness, 0), side_thickness, total_height, facecolor='#e0e0e0', edgecolor=color, lw=1.0))
    ax.add_patch(Rectangle((bay_width, 0), side_thickness, total_height, facecolor='#e0e0e0', edgecolor=color, lw=1.0))

    current_y = ground_clearance
    for i in range(min(num_rows, len(bin_heights))):
        shelf_y = current_y
        ax.add_patch(Rectangle((0, shelf_y), bay_width, shelf_thickness, facecolor='#d0d0d0', edgecolor=color, lw=1.0))
        bin_height = bin_heights[i]
        bin_y = shelf_y + shelf_thickness
        bin_top = bin_y + bin_height
        num_bins = bin_counts[i]
        bin_width = bay_width / num_bins

        # Draw bins
        for j in range(num_bins):
            bin_x = j * bin_width
            ax.add_patch(Rectangle((bin_x, bin_y), bin_width, bin_height, facecolor='white', edgecolor=color, lw=0.8))
            # Display height and width inside bin (no depth)
            ax.text(bin_x + bin_width / 2, bin_y + bin_height / 2, f"H: {bin_height:.0f}\nW: {bin_width:.0f}",
                      ha='center', va='center', fontsize=10, color='black', fontweight='bold', bbox=dict(facecolor='white', alpha=0.9, edgecolor='none'))

        # Shelf height dimension (outside right)
        draw_dimension_line(ax, bay_width + side_thickness + 20, bin_y, bay_width + side_thickness + 20, bin_top,
                            f"{bin_height} mm", True, 10, '#1976d2')

        current_y = bin_top

    if has_top_cap:
        ax.add_patch(Rectangle((0, total_height - shelf_thickness), bay_width, shelf_thickness, facecolor='#d0d0d0', edgecolor=color, lw=1.0))

    # Overall dimensions (outside edges)
    draw_dimension_line(ax, 0, -20, bay_width, -20, f"Bay Width: {bay_width:.0f} mm", False, 10, 'black')
    # Total height with vertical arrows (left side, larger and clearer)
    draw_dimension_line(ax, -side_thickness - 60, 0, -side_thickness - 60, total_height, f"Total Height: {total_height:.0f} mm", True, 10, '#1976d2', fontsize=12)
    # Ground clearance dimension (below design)
    draw_dimension_line(ax, 0, 0, 0, ground_clearance, f"{ground_clearance:.0f} mm", True, 10, '#388e3c')

    # Total width text
    ax.text((bay_width) / 2, total_height + 25, f"Overall Width: {bay_width + 2 * side_thickness:.0f} mm",
            ha='center', va='bottom', fontsize=12, fontweight='bold', color='black')

    ax.set_xlim(-side_thickness * 2 - 70, bay_width + side_thickness * 2 + 50)
    ax.set_ylim(-40, total_height + 50)
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
    """Syncs the bin heights and counts lists with the number of rows."""
    group_data = st.session_state.bay_group
    current_rows = len(group_data['bin_counts_per_row'])
    new_rows = group_data['num_rows']
    if new_rows > current_rows:
        group_data['bin_counts_per_row'].extend([3] * (new_rows - current_rows))
        group_data['bin_heights'].extend([650.0] * (new_rows - current_rows))
    elif new_rows < current_rows:
        group_data['bin_counts_per_row'] = group_data['bin_counts_per_row'][:new_rows]
        group_data['bin_heights'] = group_data['bin_heights'][:new_rows]

def update_total_height():
    """Recalculates total height based on all components."""
    group_data = st.session_state.bay_group
    total_shelf_h = (group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)) * group_data['shelf_thickness']
    group_data['total_height'] = sum(group_data['bin_heights']) + total_shelf_h + group_data['ground_clearance']

# --- Initialize Session State ---
if 'bay_group' not in st.session_state:
    st.session_state.bay_group = get_default_bay_group()

group_data = st.session_state.bay_group
# Initial sync and calculation on script run
update_bin_counts()
update_total_height()

# --- UI Layout ---
st.title("Storage Bay Designer")
st.markdown("Create and visualize storage bay designs with precise dimensions.")

# --- Sidebar Configuration ---
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
                group_data['bin_heights'][i] = st.number_input(f"Shelf {chr(65 + i)} Height (mm)", min_value=100.0, value=float(group_data['bin_heights'][i]), step=10.0, key=f"height_{i}_{group_data['id']}", on_change=update_total_height)
            with col2:
                group_data['bin_counts_per_row'][i] = st.number_input(f"Shelf {chr(65 + i)} Bin Count", min_value=1, max_value=10, value=group_data['bin_counts_per_row'][i], step=1, key=f"bins_{i}_{group_data['id']}")
    
    with st.expander("Visual Settings"):
        group_data['color'] = st.color_picker("Bay Color", value=group_data['color'], key=f"color_{group_data['id']}")
        group_data['zoom'] = st.slider("Zoom Level", 0.5, 2.0, group_data['zoom'], 0.1, key=f"zoom_{group_data['id']}")
        group_data['name'] = st.text_input("Bay Design Name", value=group_data['name'], key=f"name_{group_data['id']}")
    
    if st.button("Reset to Defaults"):
        st.session_state.bay_group = get_default_bay_group()
        update_bin_counts()
        update_total_height()
        st.rerun()

    st.header("Export")
    export_format = st.selectbox("Format", ["svg", "png", "pdf"], key="export_format")
    
    # Correctly prepare data for the download button
    export_buf, filename, mime_type = create_editable_export(group_data, export_format)
    
    st.download_button(
        label=f"Download {export_format.upper()}",
        data=export_buf,
        file_name=filename,
        mime=mime_type,
        key='download_button'
    )

# --- Main Area ---
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
        with st.spinner("Rendering..."):
            fig = draw_bay_group(group_data)
            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
