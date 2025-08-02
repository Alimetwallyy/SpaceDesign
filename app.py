import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import uuid
import logging

# --- Configure Logging (suppressed in production) ---
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Storage Bay Designer", page_icon="📐")

# --- Helper Functions ---
def hex_to_rgb(hex_color):
    """Converts a hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_dimension_line(ax, x1, y1, x2, y2, text, is_vertical=False, offset=10, color='black', fontsize=9):
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
    if params['num_bays'] < 1:
        errors.append("Number of bays must be at least 1.")
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
    if params['bin_split_thickness'] <= 0:
        errors.append("Bin split thickness must be positive.")
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
    """Draws a group of bays using Matplotlib for the LIVE PREVIEW."""
    num_bays = params['num_bays']
    bay_width = params['bay_width']
    total_height = params['total_height']
    ground_clearance = params['ground_clearance']
    shelf_thickness = params['shelf_thickness']
    side_panel_thickness = params['side_panel_thickness']
    bin_split_thickness = params['bin_split_thickness']
    num_cols = params['num_cols']
    num_rows = params['num_rows']
    has_top_cap = params['has_top_cap']
    color = params['color']
    bin_heights = params['bin_heights']
    zoom_factor = params.get('zoom', 1.0)

    visual_shelf_thickness = min(shelf_thickness, 18.0)
    visual_bin_split_thickness = min(bin_split_thickness, 18.0)
    visual_side_panel_thickness = max(side_panel_thickness, 10.0)

    core_width = num_bays * bay_width
    total_group_width = core_width + (2 * side_panel_thickness)
    dim_offset_x = 0.05 * core_width
    dim_offset_y = 0.05 * total_height
    
    fig, ax = plt.subplots(figsize=(12, 8))

    ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))
    ax.add_patch(patches.Rectangle((core_width, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1.5))

    current_x = 0
    for bay_idx in range(num_bays):
        net_width_per_bay = bay_width - 2 * side_panel_thickness
        total_internal_dividers = (num_cols - 1) * bin_split_thickness
        bin_width = (net_width_per_bay - total_internal_dividers) / num_cols if num_cols > 0 else 0

        bin_start_x = current_x
        if num_cols > 1:
            for i in range(1, num_cols):
                split_x = bin_start_x + (i * bin_width) + ((i-1) * bin_split_thickness)
                ax.add_patch(patches.Rectangle((split_x, ground_clearance), visual_bin_split_thickness, total_height - ground_clearance, facecolor='none', edgecolor=color, lw=1.5))
        
        if bay_idx < num_bays - 1:
            divider_x = current_x + bay_width
            ax.plot([divider_x, divider_x], [ground_clearance, total_height - ground_clearance], color='#aaaaaa', lw=1, linestyle='--')

        current_x += bay_width

    current_y = ground_clearance
    pitch_offset_x = dim_offset_x * 2.5

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
            draw_dimension_line(ax, core_width + visual_side_panel_thickness + dim_offset_x, bin_bottom_y, core_width + visual_side_panel_thickness + dim_offset_x, bin_top_y, f"{net_bin_h:.1f}", is_vertical=True, offset=5, color='#3b82f6')
            draw_dimension_line(ax, core_width + visual_side_panel_thickness + pitch_offset_x, shelf_bottom_y, core_width + visual_side_panel_thickness + pitch_offset_x, pitch_top_y, f"{pitch_h:.1f}", is_vertical=True, offset=5, color='black')

            ax.text(-visual_side_panel_thickness - dim_offset_x, (bin_bottom_y + bin_top_y) / 2, level_name, va='center', ha='center', fontsize=12, fontweight='bold')
            
            current_y = bin_top_y

    if has_top_cap:
        ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, total_height - visual_shelf_thickness), total_group_width, visual_shelf_thickness, facecolor='none', edgecolor=color, lw=1.5))

    draw_dimension_line(ax, -visual_side_panel_thickness, -dim_offset_y * 2, core_width + visual_side_panel_thickness, -dim_offset_y * 2, f"Total Group Width: {total_group_width:.0f} mm", offset=10)
    draw_dimension_line(ax, -visual_side_panel_thickness - (dim_offset_x * 4), 0, -visual_side_panel_thickness - (dim_offset_x * 4), total_height, f"Total Height: {total_height:.0f} mm", is_vertical=True, offset=10)

    if num_cols > 0:
        dim_y_pos = total_height + dim_offset_y
        loop_current_x = 0
        for bay_idx in range(num_bays):
            net_width_per_bay = bay_width - 2 * side_panel_thickness
            total_internal_dividers = (num_cols - 1) * bin_split_thickness
            bin_width = (net_width_per_bay - total_internal_dividers) / num_cols if num_cols > 0 else 0
            
            bin_start_x = loop_current_x
            for i in range(num_cols):
                dim_start_x = bin_start_x + (i * (bin_width + bin_split_thickness))
                dim_end_x = dim_start_x + bin_width
                draw_dimension_line(ax, dim_start_x, dim_y_pos, dim_end_x, dim_y_pos, f"{bin_width:.1f}", offset=10, color='#3b82f6')
            
            loop_current_x += bay_width

    ax.set_aspect('equal', adjustable='box')
    padding_x = core_width * 0.4 + visual_side_panel_thickness
    ax.set_xlim((-padding_x) * zoom_factor, (core_width + padding_x) * zoom_factor)
    ax.set_ylim(-dim_offset_y * 3 * zoom_factor, total_height + dim_offset_y * 2 * zoom_factor)
    ax.axis('off')
    
    return fig

def create_editable_svg(bay_groups):
    """Creates an SVG file from bay group data using Matplotlib."""
    all_svgs = []
    for group_data in bay_groups:
        logger.debug(f"Processing group: {group_data['name']}")
        fig = draw_bay_group(group_data)
        
        svg_buf = io.BytesIO()
        fig.savefig(svg_buf, format='svg', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        svg_buf.seek(0)
        all_svgs.append((group_data['name'], svg_buf))
    
    if not all_svgs:
        logger.error("No SVG files generated")
        st.error("Failed to generate SVG file. Please check configuration.")
        return None
    
    # Combine into a single SVG or zip if multiple groups (for simplicity, single file per group for now)
    combined_buf = io.BytesIO()
    if len(all_svgs) == 1:
        combined_buf.write(all_svgs[0][1].getvalue())
    else:
        from zipfile import ZipFile
        with ZipFile(combined_buf, 'w') as zip_file:
            for name, buf in all_svgs:
                zip_file.writestr(f"{name}.svg", buf.getvalue())
        combined_buf.seek(0)
    
    return combined_buf

# --- Initialize Session State ---
if 'bay_groups' not in st.session_state:
    st.session_state.bay_groups = [{
        "id": str(uuid.uuid4()),
        "name": "Group A",
        "num_bays": 2,
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "bin_split_thickness": 18.0,
        "num_cols": 4,
        "num_rows": 5,
        "has_top_cap": True,
        "color": "#4A90E2",
        "bin_heights": [350.0] * 5,
        "lock_heights": [False] * 5,
        "zoom": 1.5
    }]

for group in st.session_state.bay_groups:
    if 'bin_split_thickness' not in group:
        group['bin_split_thickness'] = 18.0
    if 'zoom' not in group:
        group['zoom'] = 1.5

# --- UI and Logic ---
st.title("Storage Bay Designer")
st.markdown("Design and visualize storage bay configurations with real-time previews and generate editable SVG outputs.")

st.sidebar.header("Manage Bay Groups", divider="gray")
st.sidebar.markdown("Create and configure storage bay groups below.")

with st.sidebar.expander("Add New Group", expanded=True):
    with st.form("new_group_form"):
        new_group_name = st.text_input("Group Name", "New Group", help="Enter a unique name for the bay group.")
        add_group_submitted = st.form_submit_button("Add Group")
        if add_group_submitted:
            if any(g['name'] == new_group_name for g in st.session_state.bay_groups):
                st.error("Group name must be unique.")
            else:
                new_group = st.session_state.bay_groups[0].copy()
                new_group['id'] = str(uuid.uuid4())
                new_group['name'] = new_group_name
                st.session_state.bay_groups.append(new_group)
                st.success(f"Added group: {new_group_name}")
                st.rerun()

if len(st.session_state.bay_groups) > 1:
    if st.sidebar.button("Remove Last Group", help="Remove the most recently added group."):
        removed_group = st.session_state.bay_groups.pop()
        st.success(f"Removed group: {removed_group['name']}")
        st.rerun()

st.sidebar.markdown("---")

group_names = [g['name'] for g in st.session_state.bay_groups]
selected_group_name = st.sidebar.selectbox("Select Group to Edit", group_names, help="Choose a group to modify its configuration.")
active_group_idx = group_names.index(selected_group_name)
group_data = st.session_state.bay_groups[active_group_idx]

def distribute_total_height():
    active_group = st.session_state.bay_groups[active_group_idx]
    num_shelves_for_calc = active_group['num_rows'] + (1 if active_group['has_top_cap'] else 0)
    total_shelf_thickness = num_shelves_for_calc * active_group['shelf_thickness']
    available_space = active_group['total_height'] - active_group['ground_clearance'] - total_shelf_thickness
    unlocked_indices = [i for i, locked in enumerate(active_group['lock_heights']) if not locked]
    num_unlocked = len(unlocked_indices)
    if available_space > 0 and num_unlocked > 0:
        uniform_net_h = available_space / num_unlocked
        for i in unlocked_indices:
            active_group['bin_heights'][i] = uniform_net_h

def update_total_height():
    active_group = st.session_state.bay_groups[active_group_idx]
    num_shelves_for_calc = active_group['num_rows'] + (1 if active_group['has_top_cap'] else 0)
    total_shelf_thickness = num_shelves_for_calc * active_group['shelf_thickness']
    total_net_bin_h = sum(active_group['bin_heights'])
    active_group['total_height'] = total_net_bin_h + total_shelf_thickness + active_group['ground_clearance']

with st.sidebar.expander("Structure", expanded=True):
    st.markdown("**Configure the bay group structure.**")
    group_data['num_bays'] = st.number_input("Number of Bays", min_value=1, value=int(group_data['num_bays']), key=f"num_bays_{group_data['id']}", help="Number of bays in the group.")
    group_data['bay_width'] = st.number_input("Width per Bay (mm)", min_value=1.0, value=float(group_data['bay_width']), key=f"bay_width_{group_data['id']}", help="Width of each bay in millimeters.")
    group_data['total_height'] = st.number_input("Target Total Height (mm)", min_value=1.0, value=float(group_data['total_height']), key=f"total_height_{group_data['id']}", on_change=distribute_total_height, help="Total height of the bay group.")
    group_data['ground_clearance'] = st.number_input("Ground Clearance (mm)", min_value=0.0, value=float(group_data['ground_clearance']), key=f"ground_clearance_{group_data['id']}", on_change=update_total_height, help="Height from ground to first shelf.")
    group_data['has_top_cap'] = st.checkbox("Include Top Cap", value=group_data['has_top_cap'], key=f"has_top_cap_{group_data['id']}", on_change=update_total_height, help="Add a top cap shelf.")

with st.sidebar.expander("Layout", expanded=True):
    st.markdown("**Configure the bay layout.**")
    prev_num_rows = group_data['num_rows']
    group_data['num_rows'] = st.number_input("Shelves (Rows)", min_value=1, value=int(group_data['num_rows']), key=f"num_rows_{group_data['id']}", on_change=update_total_height, help="Number of shelves (rows).")
    group_data['num_cols'] = st.number_input("Bin Columns", min_value=1, value=int(group_data['num_cols']), key=f"num_cols_{group_data['id']}", help="Number of bin columns per bay.")

    if prev_num_rows != group_data['num_rows']:
        if group_data['num_rows'] > len(group_data['bin_heights']):
            default_height = group_data['bin_heights'][0] if group_data['bin_heights'] else 350.0
            group_data['bin_heights'].extend([default_height] * (group_data['num_rows'] - len(group_data['bin_heights'])))
            group_data['lock_heights'].extend([False] * (group_data['num_rows'] - len(group_data['lock_heights'])))
        else:
            group_data['bin_heights'] = group_data['bin_heights'][:group_data['num_rows']]
            group_data['lock_heights'] = group_data['lock_heights'][:group_data['num_rows']]
        update_total_height()

with st.sidebar.expander("Individual Bin Heights", expanded=True):
    st.markdown("**Set individual bin heights.**")
    auto_distribute = st.checkbox("Auto-distribute Heights", value=True, key=f"auto_distribute_{group_data['id']}", help="Automatically distribute height across unlocked bins.")
    
    current_bin_heights = []
    current_lock_heights = []
    for j in range(group_data['num_rows']):
        level_name = chr(65 + j)
        col1, col2 = st.columns([3, 1])
        with col1:
            height = st.number_input(
                f"Level {level_name} Net Height (mm)",
                min_value=1.0,
                value=float(group_data['bin_heights'][j]),
                key=f"level_{group_data['id']}_{j}",
                disabled=auto_distribute and not group_data['lock_heights'][j],
                on_change=update_total_height,
                help=f"Net height for bin level {level_name}."
            )
        with col2:
            locked = st.checkbox("Lock", value=group_data['lock_heights'][j], key=f"lock_{group_data['id']}_{j}", on_change=update_total_height, help="Lock this height to prevent auto-distribution.")
        current_bin_heights.append(height)
        current_lock_heights.append(locked)
    
    group_data['bin_heights'] = current_bin_heights
    group_data['lock_heights'] = current_lock_heights
    if auto_distribute:
        distribute_total_height()
    else:
        update_total_height()

with st.sidebar.expander("Materials & Appearance", expanded=True):
    st.markdown("**Customize materials and visual settings.**")
    group_data['shelf_thickness'] = st.number_input(
        "Shelf Thickness (mm)", 
        min_value=1.0, 
        value=float(group_data['shelf_thickness']), 
        key=f"shelf_thick_{group_data['id']}", 
        on_change=update_total_height,
        help="Thickness of shelves."
    )
    group_data['bin_split_thickness'] = st.number_input(
        "Bin Split Thickness (mm)", 
        min_value=1.0, 
        value=float(group_data['bin_split_thickness']), 
        key=f"bin_split_thick_{group_data['id']}",
        help="Thickness of bin dividers."
    )
    group_data['side_panel_thickness'] = st.number_input(
        "Side Panel Thickness (mm)", 
        min_value=1.0, 
        value=float(group_data['side_panel_thickness']), 
        key=f"side_panel_thick_{group_data['id']}",
        help="Thickness of outer side panels."
    )
    group_data['color'] = st.color_picker("Structure Color", value=group_data['color'], key=f"color_{group_data['id']}", help="Color of the bay structure.")
    group_data['zoom'] = st.slider("Zoom Level", 1.0, 5.0, group_data['zoom'], 0.1, key=f"zoom_{group_data['id']}", help="Adjust zoom for preview and output.")

errors = validate_group_params(group_data)
if errors:
    st.sidebar.error("**Configuration Errors**\n" + "\n".join(f"- {e}" for e in errors))

total_net_bin_h = sum(group_data['bin_heights'])
num_shelves_for_calc = group_data['num_rows'] + (1 if group_data['has_top_cap'] else 0)
total_shelf_h = num_shelves_for_calc * group_data['shelf_thickness']
calculated_total_height = total_net_bin_h + total_shelf_h + group_data['ground_clearance']
st.sidebar.metric("Calculated Total Height", f"{calculated_total_height:.1f} mm", help="Sum of bin heights, shelf thicknesses, and ground clearance.")

st.header(f"Design Preview: {group_data['name']}")
if not errors:
    try:
        fig = draw_bay_group(group_data)
        st.pyplot(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering preview: {str(e)}")
else:
    st.error("Please resolve configuration errors to view the design.")

st.sidebar.markdown("---")
st.sidebar.header("Export Designs", divider="gray")

download_button_placeholder = st.sidebar.empty()

if st.sidebar.button("Generate SVG", type="primary", help="Generate an editable SVG file with all bay designs."):
    has_errors = False
    for group in st.session_state.bay_groups:
        if validate_group_params(group):
            has_errors = True
            st.error(f"Cannot generate SVG due to errors in group: {group['name']}")
    
    if not has_errors:
        svg_buffer = create_editable_svg(st.session_state.bay_groups)
        if svg_buffer:
            file_extension = ".zip" if len(st.session_state.bay_groups) > 1 else ".svg"
            file_name = f"storage_bay_designs{file_extension}"
            download_button_placeholder.download_button(
                label="Download SVG",
                data=svg_buffer,
                file_name=file_name,
                mime="application/zip" if len(st.session_state.bay_groups) > 1 else "image/svg+xml",
                type="primary",
                help="Download the generated SVG file(s)."
            )
        else:
            st.error("Failed to generate SVG file. Please check configuration and try again.")
