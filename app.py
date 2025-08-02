# generate_pptx.py

from pptx import Presentation
from pptx.util import Emu, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import io

# Convert mm to EMU (English Metric Units)
def mm_to_emu(mm):
    return Emu(mm * 36000)

# Example warehouse bay group configuration
group_data = {
    "name": "Group A",
    "num_bays": 2,
    "bay_width": 1050.0,              # in mm
    "total_height": 2000.0,           # in mm
    "ground_clearance": 50.0,         # in mm
    "shelf_thickness": 18.0,          # in mm
    "side_panel_thickness": 18.0,     # in mm
    "bin_split_thickness": 18.0,      # in mm
    "num_cols": 4,
    "num_rows": 5,
    "has_top_cap": True,
    "color": "#4A90E2",
    "bin_heights": [350.0] * 5        # each bin row height
}

# Create a PowerPoint presentation
prs = Presentation()
prs.slide_width = Inches(16)
prs.slide_height = Inches(9)
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

# Set scale so everything fits nicely on the slide
max_width_mm = group_data["num_bays"] * group_data["bay_width"] + 100
max_height_mm = group_data["total_height"] + 100
scale = min(prs.slide_width / mm_to_emu(max_width_mm), prs.slide_height / mm_to_emu(max_height_mm))

# Position offset from top-left
offset_x = mm_to_emu(50)
offset_y = mm_to_emu(50)

# Colors
main_color = RGBColor(74, 144, 226)
bin_color = RGBColor(255, 255, 255)

# Draw side panels
total_group_width = group_data["num_bays"] * group_data["bay_width"]
for side in ['left', 'right']:
    x = offset_x - mm_to_emu(group_data["side_panel_thickness"] * scale) if side == 'left' \
        else offset_x + mm_to_emu(total_group_width * scale)
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        x,
        offset_y,
        mm_to_emu(group_data["side_panel_thickness"] * scale),
        mm_to_emu(group_data["total_height"] * scale)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = main_color
    shape.line.color.rgb = main_color

# Draw bays
for bay_idx in range(group_data["num_bays"]):
    bay_start_x = offset_x + mm_to_emu(bay_idx * group_data["bay_width"] * scale)
    net_width = group_data["bay_width"] - 2 * group_data["side_panel_thickness"]
    bin_width = (net_width - (group_data["num_cols"] - 1) * group_data["bin_split_thickness"]) / group_data["num_cols"]

    for row in range(group_data["num_rows"]):
        bin_height = group_data["bin_heights"][row]
        y = offset_y + mm_to_emu(group_data["ground_clearance"] * scale)
        for h in range(row):
            y += mm_to_emu((group_data["bin_heights"][h] + group_data["shelf_thickness"]) * scale)

        for col in range(group_data["num_cols"]):
            x = bay_start_x + mm_to_emu((group_data["side_panel_thickness"] +
                                         col * (bin_width + group_data["bin_split_thickness"])) * scale)
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                x,
                y,
                mm_to_emu(bin_width * scale),
                mm_to_emu(bin_height * scale)
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = bin_color
            shape.line.color.rgb = main_color

# Save PowerPoint to file
output_file = "bay_layout_editable.pptx"
prs.save(output_file)
print(f"✅ PowerPoint file saved: {output_file}")
