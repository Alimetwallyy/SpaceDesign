import streamlit as st
from pptx import Presentation
from pptx.util import Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import io

def mm_to_emu(mm):
    return Emu(mm * 36000)

def generate_pptx(group):
    prs = Presentation()
    prs.slide_width = Emu(40640000)  # 16 inches
    prs.slide_height = Emu(22860000)  # 9 inches
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    scale = 0.2
    offset_x = mm_to_emu(50)
    offset_y = mm_to_emu(50)

    main_color = RGBColor(74, 144, 226)
    bin_color = RGBColor(255, 255, 255)

    bay_width = group["bay_width"]
    total_height = group["total_height"]
    ground_clearance = group["ground_clearance"]
    shelf_thickness = group["shelf_thickness"]
    side_panel_thickness = group["side_panel_thickness"]
    split_thickness = group["bin_split_thickness"]
    cols = group["num_cols"]
    rows = group["num_rows"]
    bin_heights = group["bin_heights"]

    # Draw left side panel
    slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        offset_x - mm_to_emu(side_panel_thickness * scale),
        offset_y,
        mm_to_emu(side_panel_thickness * scale),
        mm_to_emu(total_height * scale)
    ).fill.solid()
    
    # Draw right side panel
    slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        offset_x + mm_to_emu(bay_width * scale),
        offset_y,
        mm_to_emu(side_panel_thickness * scale),
        mm_to_emu(total_height * scale)
    ).fill.solid()

    # Draw bins
    net_width = bay_width - 2 * side_panel_thickness
    bin_width = (net_width - (cols - 1) * split_thickness) / cols
    y = offset_y + mm_to_emu(ground_clearance * scale)

    for row in range(rows):
        h = bin_heights[row]
        for col in range(cols):
            x = offset_x + mm_to_emu(
                (side_panel_thickness + col * (bin_width + split_thickness)) * scale
            )
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                x,
                y,
                mm_to_emu(bin_width * scale),
                mm_to_emu(h * scale)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = bin_color
            shape.line.color.rgb = main_color
        y += mm_to_emu((h + shelf_thickness) * scale)

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ---- Streamlit App ----
st.set_page_config(page_title="Warehouse Bay Layout", layout="centered")
st.title("📦 Editable Bay Layout Generator (.pptx)")

if st.button("Generate Bay Layout PowerPoint"):
    group_data = {
        "num_bays": 1,
        "bay_width": 1050.0,
        "total_height": 2000.0,
        "ground_clearance": 50.0,
        "shelf_thickness": 18.0,
        "side_panel_thickness": 18.0,
        "bin_split_thickness": 18.0,
        "num_cols": 4,
        "num_rows": 5,
        "bin_heights": [350.0] * 5,
        "color": "#4A90E2"
    }
    pptx_file = generate_pptx(group_data)

    st.success("✅ PowerPoint file generated!")
    st.download_button(
        label="📥 Download PPTX",
        data=pptx_file,
        file_name="bay_layout_editable.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
