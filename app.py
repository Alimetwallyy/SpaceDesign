import streamlit as st
import pandas as pd
import re
from io import BytesIO

# Function to parse bin ID
def parse_bin_id(bin_id):
    pattern = r'P-(\d+)-([A-Z])(\d+)([A-Z])(\d+)'
    match = re.match(pattern, bin_id)
    if match:
        floor, mod, aisle, shelf, bin_num = match.groups()
        return {
            'bin_id': bin_id,
            'floor': int(floor),
            'mod': mod,
            'aisle': int(aisle),
            'shelf': shelf,
            'bin_num': int(bin_num)
        }
    return None

# Function to sort bins for picking sequence
def sort_bins(bin_ids):
    parsed_bins = [parse_bin_id(bin_id) for bin_id in bin_ids if parse_bin_id(bin_id)]
    # Sort by aisle, then shelf (A to Z), then bin number
    sorted_bins = sorted(parsed_bins, key=lambda x: (x['aisle'], x['shelf'], x['bin_num']))
    return sorted_bins

# Function to convert sorted bins to Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pick Sequence')
    return output.getvalue()

# Streamlit app
st.title("Warehouse Pick Sequence Generator")
st.write("Enter bin IDs (one per line, e.g., P-1-B200A200) and generate a sorted pick sequence.")

# Input for bin IDs
bin_input = st.text_area("Enter Bin IDs", placeholder="P-1-B200A200\nP-1-B200A201\nP-1-B201B202")
generate_button = st.button("Generate Pick Sequence")

if generate_button and bin_input:
    # Process input
    bin_ids = [bid.strip() for bid in bin_input.split('\n') if bid.strip()]
    if not bin_ids:
        st.error("Please enter at least one valid bin ID.")
    else:
        # Parse and sort bins
        sorted_bins = sort_bins(bin_ids)
        if not sorted_bins:
            st.error("No valid bin IDs found. Format: P-floor-mod aisle shelf bin (e.g., P-1-B200A200).")
        else:
            # Create DataFrame
            df = pd.DataFrame(sorted_bins)
            df = df[['bin_id', 'floor', 'mod', 'aisle', 'shelf', 'bin_num']]
            df.columns = ['Bin ID', 'Floor', 'Mod', 'Aisle', 'Shelf', 'Bin Number']
            
            # Display results
            st.subheader("Sorted Pick Sequence")
            st.dataframe(df)
            
            # Excel download
            excel_data = to_excel(df)
            st.download_button(
                label="Download Pick Sequence as Excel",
                data=excel_data,
                file_name="pick_sequence.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Enter bin IDs and click 'Generate Pick Sequence' to see results.")
