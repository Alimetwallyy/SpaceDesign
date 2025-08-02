import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io

st.set_page_config(layout="wide", page_title="Warehouse Bay Designer")

# --- Helper Functions ---
def draw_dimension_line(ax, x1, y1, x2, y2, text, is_vertical=False, offset=10, color='black', fontsize=9):
    ax.plot([x1, x2], [y1, y2], color=color, lw=1)
    if is_vertical:
        ax.plot(x1, y1, marker='v', color=color, markersize=5)
        ax.plot(x2, y2, marker='^', color=color, markersize=5)
        ax.text(x1 + offset, (y1 + y2) / 2, text, va='center', ha='left', fontsize=fontsize, rotation=90, color=color)
    else:
        ax.plot(x1, y1, marker='<', color=color, markersize=5)
        ax.plot(x2, y2, marker='>', color=color, markersize=5)
        ax.text((x1 + x2) / 2, y1 + offset, text, va='bottom', ha='center', fontsize=fontsize, color=color)

@st.cache_data
def draw_bay_group(params):
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

    fig, ax = plt.subplots(figsize=(12, 12))

    def draw_side_panels():
        ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1))
        ax.add_patch(patches.Rectangle((core_width, 0), visual_side_panel_thickness, total_height, facecolor='none', edgecolor=color, lw=1))

    def draw_bays():
        current_x = 0
        for bay_idx in range(num_bays):
            net_width_per_bay = bay_width - 2 * side_panel_thickness
            total_internal_dividers = (num_cols - 1) * bin_split_thickness
            bin_width = (net_width_per_bay - total_internal_dividers) / num_cols if num_cols > 0 else 0

            bin_start_x = current_x
            if num_cols > 1:
                for i in range(1, num_cols):
                    split_x = bin_start_x + (i * bin_width) + ((i-1) * bin_split_thickness)
                    ax.add_patch(patches.Rectangle((split_x, ground_clearance), visual_bin_split_thickness, structure_height, facecolor='none', edgecolor=color, lw=1))

            if bay_idx < num_bays - 1:
                divider_x = current_x + bay_width
                ax.plot([divider_x, divider_x], [ground_clearance, structure_height], color='#aaaaaa', lw=1, linestyle='--')

            current_x += bay_width

    def draw_shelves_and_dimensions():
        current_y = ground_clearance
        pitch_offset_x = dim_offset_x * 2.5

        for i in range(num_rows):
            shelf_bottom_y = current_y
            ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, shelf_bottom_y), total_group_width, visual_shelf_thickness, facecolor='none', edgecolor=color, lw=1))
            shelf_top_y = shelf_bottom_y + shelf_thickness

            if i < len(bin_heights):
                net_bin_h = bin_heights[i]
                pitch_h = net_bin_h + shelf_thickness
                level_name = chr(65 + i)

                bin_bottom_y = shelf_top_y
                bin_top_y = bin_bottom_y + net_bin_h
                draw_dimension_line(ax, core_width + visual_side_panel_thickness + dim_offset_x, bin_bottom_y, core_width + visual_side_panel_thickness + dim_offset_x, bin_top_y, f"{net_bin_h:.1f}", is_vertical=True, offset=5, color='#3b82f6')
                draw_dimension_line(ax, core_width + visual_side_panel_thickness + pitch_offset_x, shelf_bottom_y, core_width + visual_side_panel_thickness + pitch_offset_x, pitch_h + shelf_bottom_y, f"{pitch_h:.1f}", is_vertical=True, offset=5, color='black')
                ax.text(-visual_side_panel_thickness - dim_offset_x, (bin_bottom_y + bin_top_y) / 2, level_name, va='center', ha='center', fontsize=12, fontweight='bold')
                current_y = bin_top_y

        if has_top_cap:
            ax.add_patch(patches.Rectangle((-visual_side_panel_thickness, total_height - visual_shelf_thickness), total_group_width, visual_shelf_thickness, facecolor='none', edgecolor=color, lw=1))

    def draw_main_dimensions():
        draw_dimension_line(ax, -visual_side_panel_thickness, -dim_offset_y * 2, core_width + visual_side_panel_thickness, -dim_offset_y * 2, f"Total Group Width: {total_group_width:.0f} mm", offset=10)
        draw_dimension_line(ax, -visual_side_panel_thickness - (dim_offset_x * 4), 0, -visual_side_panel_thickness - (dim_offset_x * 4), total_height, f"Total Height: {total_height:.0f} mm", is_vertical=True, offset=10)

    structure_height = total_height - ground_clearance
    draw_side_panels()
    draw_bays()
    draw_shelves_and_dimensions()
    draw_main_dimensions()

    ax.set_aspect('equal', adjustable='box')
    padding_x = core_width * 0.4 + visual_side_panel_thickness
    ax.set_xlim((-padding_x) * zoom_factor, (core_width + padding_x) * zoom_factor)
    ax.set_ylim(-dim_offset_y * 3 * zoom_factor, total_height + dim_offset_y * 2 * zoom_factor)
    ax.axis('off')

    return fig

def generate_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

# --- Sample Bay Configuration ---
group_data = {
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
    "zoom": 1.0
}

# --- Main Drawing Area ---
st.header(f"Generated Layout: {group_data['name']}")
fig = draw_bay_group(group_data)
st.pyplot(fig, use_container_width=True)

png_buf = generate_png(fig)
st.download_button(
    label="Download as PNG",
    data=png_buf,
    file_name="bay_layout.png",
    mime="image/png"
)
