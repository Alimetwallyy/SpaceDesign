from pptx import Presentation
from pptx.util import Emu, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def mm_to_emu(mm):
    return Emu(mm * 36000)

def create_bay_layout_pptx(filename="bay_layout_editable.pptx"):
    group = {
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

    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank slide

    scale = 0.2  # Adjust scale to fit slide

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
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        offset_x - mm_to_emu(side_panel_thickness * scale),
        offset_y,
        mm_to_emu(side_panel_thickness * scale),
        mm_to_emu(total_height * scale)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = main_color
    shape.line.color.rgb = main_color

    # Draw right side panel
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        offset_x + mm_to_emu(bay_width * scale),
        offset_y,
        mm_to_emu(side_panel_thickness * scale),
        mm_to_emu(total_height * scale)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = main_color
    shape.line.color.rgb = main_color

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

    prs.save(filename)
    print(f"✅ Saved PowerPoint file: {filename}")

if __name__ == "__main__":
    create_bay_layout_pptx()
