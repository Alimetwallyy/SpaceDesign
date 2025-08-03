import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import io
import uuid
import logging
import numpy as np

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Storage Bay Designer app")

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Storage Bay Designer", page_icon="📐")

# --- Custom CSS for Professional Look ---
# (CSS remains the same as before, so it is omitted here for brevity but is included in the full script below)
st.markdown("""
<style>
    /* CSS styles are unchanged */
    .stApp{background-color:#f9f9f9;font-family:'Arial',sans-serif}.stSidebar{background-color:#fff;padding:20px;border-right:1px solid #ccc}.stButton>button{background-color:#1976d2;color:#fff;border-radius:4px;padding:8px 16px;margin:5px 0;font-weight:500}.stButton>button:hover{background-color:#1565c0}.stNumberInput input,.stTextInput input{border-radius:4px;border:1px solid #bbb}.stExpander{margin-bottom:10px;border:1px solid #ddd;border-radius:4px}.stExpander>div>div{padding:10px}.preview-container{border:1px solid #bbb;border-radius:4px;padding:10px;background-color:#fff;box-shadow:0 2px 4px rgba(0,0,0,.1)}.metric-box{background-color:#e3f2fd;padding:10px;border-radius:4px;margin:10px 0;font-size:14px;color:#1e88e5}[data-theme=dark] .stApp{background-color:#1e1e1e}[data-theme=dark] .stSidebar{background-color:#2c2c2c;border-right:1px solid #444}[data-theme=dark] .preview-container{background-color:#2c2c2c;border-color:#555;box-shadow:0 2px 4px rgba(0,0,0,.3)}[data-theme=dark] .metric-box{background-color:#103a6d;color:#bbdefb}
</style>
""", unsafe_allow_html=True)


# --- NEW: Professional Engineering Dimension Function ---
def draw_dimension(ax, p1, p2, text, axis='y', offset=-50, color='#333333', text_color='#000000'):
    """Draws a professional-style dimension line with extension lines and arrows."""
    p1 = np.array(p1)
    p2 = np.array(p2)
    
    if axis == 'y':
        # Vertical dimension
        ext_line1_start = p1
        ext_line1_end = p1 + [offset, 0]
        ext_line2_start = p2
        ext_line2_end = p2 + [offset, 0]
        dim_line_start = ext_line1_end
        dim_line_end = ext_line2_end
        text_pos = (dim_line_start + dim_line_end) / 2
        rotation = 90
        va = 'center'
        ha = 'right'
    else:
        # Horizontal dimension
        ext_line1_start = p1
        ext_line1_end = p1 + [0, offset]
        ext_line2_start = p2
        ext_line2_end = p2 + [0, offset]
        dim_line_start = ext_line1_end
        dim_line_end = ext_line2_end
        text_pos = (dim_line_start + dim_line_end) / 2
        rotation = 0
        va = 'bottom'
        ha = 'center'

    # Draw extension lines
    ax.plot([ext_line1_start[0], ext_line1_end[0]], [ext_line1_start[1], ext_line1_end[1]], color=color, lw=0.7)
    ax.plot([ext_line2_start[0], ext_line2_end[0]], [ext_line2_start[1], ext_line2_end[1]], color=color, lw=0.7)

    # Draw dimension line with arrows
    arrow_props = dict(arrowstyle='<|-|>', mutation_scale=15, color=color, lw=1.0)
    dim_line = FancyArrowPatch(dim_line_start, dim_line_end, **arrow_props)
    ax.add_patch(dim_line)

    # Draw text with a white background to "break" the line
    ax.text(text_pos[0], text_pos[1], text, rotation=rotation, ha=ha, va=va, fontsize=9,
            color=text_color, fontweight='bold',
            bbox=dict(facecolor='white', edgecolor='none', pad=1))

# --- Helper Functions (Unchanged) ---
def get_default_bay_group():
    """Returns the default dictionary for a new bay group."""
    return {
        "id": str(uuid.uuid4()),"name": "Storage Bay Design","bay_width": 1050.0,"total_height": 2200.0,
        "ground_clearance": 100.0,"depth": 600.0,"shelf_thickness": 18.0,"side_panel_thickness": 18.0,
        "num_rows": 3,"has_top_cap": True,"color": "#424242","bin_heights": [650.0, 650.0, 650.0],
        "bin_counts_per_row": [3, 3, 3],"zoom": 1.0
    }

# --- UPDATED: Main Drawing Function ---
@st.cache_data
def draw_bay_group(params):
    """Draws a professional 2D bay design with clear, non-overlapping dimensions."""
    bay_width = params['bay_width']
    total_height = params['total_height']
    ground_clearance = params['ground_clearance']
    shelf_thickness = params['shelf_thickness']
    side_thickness = params['side_panel_thickness']
    num_rows = params['num_rows']
    has_top_cap = params['has_top_cap']
    main_color = params['color']
    bin_heights = params['bin_heights']
    bin_counts = params['bin_counts_per_row']
    zoom = params.get('zoom', 1.0)
    design_name = params.get('name', "Storage Bay Design")

    fig, ax = plt.subplots(figsize=(10 * zoom, 7 * zoom), dpi=120)
    ax.set_facecolor('#ffffff')
    ax.grid(False)

    # Draw main structure
    left_panel_x = -side_thickness
    right_panel_x = bay_width
    
    # Side Panels
    ax.add_patch(Rectangle((left_panel_x, 0), side_thickness, total_height, facecolor='#BDBDBD', edgecolor=main_color, lw=1.5))
    ax.add_patch(Rectangle((right_panel_x, 0), side_thickness, total_height, facecolor='#BDBDBD', edgecolor=main_color, lw=1.5))
    
    # Base "floor" line
    ax.plot([left_panel_x - 100, right_panel_x + side_thickness + 100], [0,0], color='#9E9E9E', lw=2)

    current_y = ground_clearance
    for i in range(min(num_rows, len(bin_heights))):
        shelf_y = current_y
        ax.add_patch(Rectangle((0, shelf_y), bay_width, shelf_thickness, facecolor='#D6D6D6', edgecolor=main_color, lw=1.0))
        
        bin_height = bin_heights[i]
        bin_y = shelf_y + shelf_thickness
        
        # Draw shelf height dimension
        draw_dimension(ax, (right_panel_x + side_thickness, bin_y), (right_panel_x + side_thickness, bin_y + bin_height), 
                       f"{bin_height:.0f}", axis='y', offset=50)
                       
        current_y = bin_y + bin_height

    if has_top_cap:
        top_cap_y = total_height - shelf_thickness
        ax.add_patch(Rectangle((0, top_cap_y), bay_width, shelf_thickness, facecolor='#D6D6D6', edgecolor=main_color, lw=1.0))

    # --- OVERALL DIMENSIONS (Professional Style) ---
    # Total Height (Left Side)
    draw_dimension(ax, (left_panel_x, 0), (left_panel_x, total_height), f"{total_height:.0f} mm", 
                   axis='y', offset=-60)
                   
    # Total Width (Bottom)
    draw_dimension(ax, (left_panel_x, 0), (right_panel_x + side_thickness, 0), f"{bay_width + 2*side_thickness:.0f} mm", 
                   axis='x', offset=-60)

    # Ground Clearance
    draw_dimension(ax, (0, 0), (0, ground_clearance), f"{ground_clearance:.0f}", 
                   axis='y', offset=60, color='#388e3c')

    # Bay Width (Top)
    draw_dimension(ax, (0, total_height), (bay_width, total_height), f"{bay_width:.0f}", 
                   axis='x', offset=50, color='#1976d2')

    # Set plot limits and turn off axis
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    plt.tight_layout(pad=2.0)
    return fig

# --- Other Helper Functions (Unchanged) ---
def create_editable_export(bay_group, format_type):
    """Creates an export file from bay group data."""
    logger.debug(f"Processing group: {bay_group['name']} in {format_type} format")
    fig = draw_bay_group(bay_group)
    export_buf = io.BytesIO()
    if format_type == 'svg':
        fig.savefig(export_buf, format='svg', bbox_inches='tight')
        filename = f"{bay_group['name'].replace(' ', '_')}.svg"
        mime_type = "image/svg+xml"
    elif format_type == 'png':
        fig.savefig(export_buf, format='png', bbox_inches='tight', dpi=300)
        filename = f"{bay_group['name'].replace(' ', '_')}.png"
        mime_type = "image/png"
    elif format_type == 'pdf':
        fig.savefig(export_buf, format='pdf', bbox_inches='tight')
        filename = f"{bay_group['name'].replace(' ', '_')}.pdf"
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
        group_data['bin_counts_per_row'].extend([1] * (new_rows - current_rows))
        group_data['bin_heights'].extend([650.0] * (new_rows - current_rows))
    elif new_rows < current_rows:
        group_data['bin_counts_per_row'] = group_data['bin_counts_per_row'][:new_rows]
        group_data['bin_heights'] = group_data['bin_heights'][:new_rows]

def update_total_height():
    """Recalculates total height based on all components."""
    group_data = st.session_state.bay_group
    total_shelf_h = (group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)) * group_data['shelf_thickness']
    group_data['total_height'] = sum(group_data['bin_heights']) + total_shelf_h + group_data['ground_clearance']

# --- Session State and UI (Largely Unchanged) ---
if 'bay_group' not in st.session_state:
    st.session_state.bay_group = get_default_bay_group()

group_data = st.session_state.bay_group
update_bin_counts()
update_total_height()

st.title("Storage Bay Designer")
st.markdown("Create and visualize professional storage bay designs.")

# Sidebar Configuration
with st.sidebar:
    st.header("Design Settings")
    with st.expander("Basic Dimensions", expanded=True):
        group_data['bay_width'] = st.number_input("Bay Width (mm)", min_value=300.0, value=group_data['bay_width'], step=50.0)
        group_data['depth'] = st.number_input("Bay Depth (mm)", min_value=300.0, value=group_data['depth'], step=50.0)
        group_data['ground_clearance'] = st.number_input("Ground Clearance (mm)", min_value=0.0, value=group_data['ground_clearance'], step=10.0, on_change=update_total_height)
        group_data['shelf_thickness'] = st.number_input("Shelf Thickness (mm)", min_value=10.0, value=group_data['shelf_thickness'], step=1.0, on_change=update_total_height)
        group_data['side_panel_thickness'] = st.number_input("Side Panel Thickness (mm)", min_value=10.0, value=group_data['side_panel_thickness'], step=1.0)
        group_data['has_top_cap'] = st.checkbox("Include Top Cap", value=group_data['has_top_cap'], on_change=update_total_height)

    with st.expander("Shelf Configuration", expanded=True):
        group_data['num_rows'] = st.number_input("Number of Shelves", min_value=1, max_value=10, value=group_data['num_rows'], step=1, on_change=update_bin_counts)
        for i in range(group_data['num_rows']):
            group_data['bin_heights'][i] = st.number_input(f"Shelf {chr(65 + i)} Height (mm)", min_value=100.0, value=float(group_data['bin_heights'][i]), step=10.0, key=f"height_{i}", on_change=update_total_height)

    with st.expander("Visual & Export Settings"):
        group_data['color'] = st.color_picker("Outline Color", value=group_data['color'])
        group_data['zoom'] = st.slider("Zoom Level", 0.5, 2.0, group_data['zoom'], 0.1)
        group_data['name'] = st.text_input("Design Name", value=group_data['name'])

    if st.button("Reset to Defaults"):
        st.session_state.bay_group = get_default_bay_group()
        st.rerun()

    st.header("Export")
    export_format = st.selectbox("Format", ["png", "svg", "pdf"], key="export_format")
    export_buf, filename, mime_type = create_editable_export(group_data, export_format)
    st.download_button(label=f"Download {export_format.upper()}", data=export_buf, file_name=filename, mime=mime_type)

# Main Area
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Design Metrics")
    st.markdown(f"""
    <div class="metric-box"><b>Overall Width:</b> {group_data['bay_width'] + 2 * group_data['side_panel_thickness']:.0f} mm</div>
    <div class="metric-box"><b>Overall Height:</b> {group_data['total_height']:.0f} mm</div>
    <div class="metric-box"><b>Overall Depth:</b> {group_data['depth']:.0f} mm</div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("Technical Drawing")
    with st.container():
        st.markdown('<div class="preview-container">', unsafe_allow_html=True)
        with st.spinner("Rendering Technical Drawing..."):
            fig = draw_bay_group(group_data)
            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
