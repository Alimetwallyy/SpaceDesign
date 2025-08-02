import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import io

# Set Streamlit page config
st.set_page_config(page_title="Bay Layout Generator", layout="wide")

st.title("📦 Bay Layout PowerPoint Generator")
st.markdown("""
This tool helps you automate bay layout drawings in PowerPoint.  
Configure multiple bays, shelves, and bins, and download the slide design in seconds.
""")

# ---------- Helper Functions ----------

def create_bin_box(slide, left, top, width, height, label):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left,
        top,
        width,
        height
    )
    shape.text = label
    text_frame = shape.text_frame
    text_frame.paragraphs[0].font.size = Pt(10)
    text_frame.paragraphs[0].font.bold = True
    text_frame.paragraphs[0].font.name = 'Arial'
    text_frame.paragraphs[0].alignment = 1  # center

    # Set colors
    fill = shape.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(200, 200, 255)
    line = shape.line
    line.color.rgb = RGBColor(0, 0, 0)

def draw_bay_slide(prs, bay_index, bay_data):
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank slide

    # Title
    title_box = slide.shapes.add_textbox(Inches(0.3), Inches(0.2), Inches(8), Inches(0.5))
    title_frame = title_box.text_frame
    title_frame.text = f"Bay {bay_index + 1} Layout"
    title_frame.paragraphs[0].font.size = Pt(24)
    title_frame.paragraphs[0].font.bold = True

    # Display depth (static for whole bay)
    depth = bay_data['depth']
    depth_box = slide.shapes.add_textbox(Inches(6.5), Inches(0.2), Inches(2.5), Inches(0.3))
    depth_box.text = f"Depth: {depth} mm"
    depth_box.text_frame.paragraphs[0].font.size = Pt(14)
    depth_box.text_frame.paragraphs[0].font.bold = True

    # Draw shelves (top-down layout)
    start_top = 1.0  # inches
    spacing = 0.3  # vertical spacing between shelves

    for shelf_index, shelf in enumerate(bay_data['shelves']):
        bins = shelf['bins']
        bin_top = Inches(start_top + shelf_index * (1.0 + spacing))

        total_width = sum([b['width'] for b in bins])
        scale = 6.0 / total_width  # scale to fit in 6 inches horizontally

        current_left = Inches(0.5)
        for bin_index, bin_data in enumerate(bins):
            bin_width_in = Inches(bin_data['width'] * scale)
            bin_height_in = Inches(bin_data['height'] * 0.02)  # scale height visually

            label = f"{bin_data['width']} x {bin_data['height']}"
            create_bin_box(
                slide,
                left=current_left,
                top=bin_top,
                width=bin_width_in,
                height=bin_height_in,
                label=label
            )
            current_left += bin_width_in + Inches(0.05)

# ---------- Streamlit Input UI ----------

num_bays = st.number_input("How many bays do you want to create?", min_value=1, max_value=10, value=1)

bays = []

for bay_idx in range(num_bays):
    with st.expander(f"🧱 Configure Bay {bay_idx + 1}", expanded=True):
        bay_depth = st.number_input(f"Bay {bay_idx + 1} Depth (mm)", min_value=100, max_value=2000, value=600, key=f"depth_{bay_idx}")
        num_shelves = st.number_input(f"Number of Shelves in Bay {bay_idx + 1}", min_value=1, max_value=20, value=3, key=f"shelves_{bay_idx}")

        shelves = []
        for shelf_idx in range(num_shelves):
            with st.expander(f"  📚 Shelf {shelf_idx + 1} in Bay {bay_idx + 1}"):
                num_bins = st.number_input(f"  Number of Bins in Shelf {shelf_idx + 1}", min_value=1, max_value=20, value=3, key=f"bins_{bay_idx}_{shelf_idx}")
                bins = []
                for bin_idx in range(num_bins):
                    col1, col2 = st.columns(2)
                    with col1:
                        width = st.number_input(f"    Bin {bin_idx + 1} Width (mm)", min_value=50, max_value=2000, value=400, key=f"w_{bay_idx}_{shelf_idx}_{bin_idx}")
                    with col2:
                        height = st.number_input(f"    Bin {bin_idx + 1} Height (mm)", min_value=50, max_value=2000, value=300, key=f"h_{bay_idx}_{shelf_idx}_{bin_idx}")
                    bins.append({"width": width, "height": height})
                shelves.append({"bins": bins})

        bays.append({"depth": bay_depth, "shelves": shelves})

# ---------- Generate PowerPoint ----------

if st.button("📤 Generate PowerPoint Layout"):
    prs = Presentation()
    for i, bay in enumerate(bays):
        draw_bay_slide(prs, i, bay)

    ppt_io = io.BytesIO()
    prs.save(ppt_io)
    ppt_io.seek(0)

    st.success("✅ PowerPoint created successfully!")
    st.download_button(
        label="📥 Download Bay Layout PowerPoint",
        data=ppt_io,
        file_name="bay_layouts.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
