import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io

# Streamlit setup
st.set_page_config(page_title="Bay Layout Image Generator", layout="wide")
st.title("📐 Bay Layout Generator (PNG Output)")
st.markdown("Configure your bay layout and generate a clean, scaled diagram as an image with dimensions in **cm**.")

# ------------------ UI INPUT ------------------

num_bays = st.number_input("How many bays do you want to create?", min_value=1, max_value=10, value=1)

bays = []

for bay_idx in range(num_bays):
    with st.expander(f"🧱 Configure Bay {bay_idx + 1}", expanded=True):
        depth = st.number_input(f"Bay {bay_idx + 1} Depth (cm)", min_value=10, value=60, key=f"depth_{bay_idx}")
        num_shelves = st.number_input(f"Number of Shelves", min_value=1, value=3, key=f"shelves_{bay_idx}")

        shelves = []
        for shelf_idx in range(num_shelves):
            with st.expander(f"📚 Shelf {shelf_idx + 1}", expanded=False):
                num_bins = st.number_input(f"Number of Bins in Shelf {shelf_idx + 1}", min_value=1, value=3, key=f"bins_{bay_idx}_{shelf_idx}")
                bins = []
                for bin_idx in range(num_bins):
                    cols = st.columns(2)
                    with cols[0]:
                        width = st.number_input(f"Bin {bin_idx + 1} Width (cm)", min_value=1, value=24, key=f"w_{bay_idx}_{shelf_idx}_{bin_idx}")
                    with cols[1]:
                        height = st.number_input(f"Bin {bin_idx + 1} Height (cm)", min_value=1, value=19, key=f"h_{bay_idx}_{shelf_idx}_{bin_idx}")
                    bins.append({"width": width, "height": height})
                shelves.append({"bins": bins})
        bays.append({"depth": depth, "shelves": shelves})

# ------------------ DRAWING LOGIC ------------------

def draw_bay_image(bay_data):
    shelves = bay_data['shelves']
    depth = bay_data['depth']

    shelf_heights = [max(bin['height'] for bin in shelf['bins']) for shelf in shelves]
    total_height = sum(shelf_heights)
    max_bins_per_shelf = max(len(shelf['bins']) for shelf in shelves)
    total_width = max(sum(bin['width'] for bin in shelf['bins']) for shelf in shelves)

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, total_width + 20)
    ax.set_ylim(0, total_height + 30)
    ax.set_aspect('equal')
    ax.axis('off')

    # Coordinates
    current_y = 5

    # Draw shelves top-down
    for shelf_idx, shelf in enumerate(shelves):
        shelf_height = shelf_heights[shelf_idx]
        current_x = 5
        for bin in shelf['bins']:
            w = bin['width']
            h = bin['height']

            rect = patches.Rectangle((current_x, current_y), w, h, linewidth=2, edgecolor='blue', facecolor='lightblue')
            ax.add_patch(rect)

            # Label inside the bin
            ax.text(current_x + w / 2, current_y + h / 2,
                    f"{w} x {h} cm",
                    color='black', fontsize=8, ha='center', va='center', weight='bold')

            current_x += w
        current_y += shelf_height

    # Total height dimension
    ax.annotate('', xy=(2, 5), xytext=(2, current_y),
                arrowprops=dict(arrowstyle='<->', lw=1.5, color='blue'))
    ax.text(0, current_y / 2, f"{total_height} cm", ha='center', va='center',
            fontsize=12, rotation=90, weight='bold', color='blue')

    # Total width dimension
    ax.annotate('', xy=(5, current_y + 2), xytext=(5 + total_width, current_y + 2),
                arrowprops=dict(arrowstyle='<->', lw=1.5, color='blue'))
    ax.text(5 + total_width / 2, current_y + 4, f"{total_width} cm", ha='center', va='center',
            fontsize=12, weight='bold', color='blue')

    # Bin widths
    current_x = 5
    for bin in shelves[0]['bins']:
        bin_width = bin['width']
        ax.text(current_x + bin_width / 2, current_y + 6, f"{bin_width} cm",
                ha='center', va='bottom', fontsize=10)
        current_x += bin_width

    # Bin heights (left side)
    current_y2 = 5
    for h in shelf_heights:
        ax.text(1.2, current_y2 + h / 2, f"{h} cm", ha='right', va='center', fontsize=10)
        current_y2 += h

    # Bay depth (top center)
    ax.text(5 + total_width / 2, current_y + 10, f"{depth} Deep", ha='center',
            fontsize=12, weight='bold')

    return fig

# ------------------ OUTPUT SECTION ------------------

if st.button("🎨 Generate Bay Layout Image"):
    for idx, bay in enumerate(bays):
        fig = draw_bay_image(bay)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)

        st.success(f"✅ Bay {idx + 1} image generated!")
        st.image(buf, caption=f"Bay {idx + 1} Layout", use_column_width=True)
        st.download_button(
            label=f"📥 Download Bay {idx + 1} PNG",
            data=buf,
            file_name=f"bay_{idx + 1}_layout.png",
            mime="image/png"
        )
        plt.close(fig)
