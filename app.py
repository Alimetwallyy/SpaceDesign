import streamlit as st
import pandas as pd
import re

# Function to parse bin ID
def parse_bin_id(bin_id):
    pattern = r'^A(\d{2})P(\d{2,3})L(\d)$'
    match = re.match(pattern, bin_id)
    if not match:
        raise ValueError(f"Invalid bin ID format: {bin_id}. Expected format: AxxPyyLz or AxxPyyyLz (e.g., A08P01L1 or A08P100L1)")
    walkway, position, level = match.groups()
    return {
        'Walkway': f"A{walkway}",
        'Position': int(position),
        'Level': int(level),
        'BinID': bin_id
    }

# Function to generate pick path
def generate_pick_path(bin_ids):
    try:
        # Parse all bin IDs
        bins = [parse_bin_id(bin_id.strip()) for bin_id in bin_ids.split('\n') if bin_id.strip()]
        
        # Convert to DataFrame
        df = pd.DataFrame(bins)
        
        # Group by walkway and sort
        walkways = sorted(df['Walkway'].unique())
        sorted_bins = []
        
        for i, walkway in enumerate(walkways):
            walkway_df = df[df['Walkway'] == walkway]
            # Sort by level, then position
            walkway_sorted = walkway_df.sort_values(by=['Level', 'Position'])
            sorted_bins.append(walkway_sorted)
        
        # Concatenate all walkways
        result = pd.concat(sorted_bins, ignore_index=True)
        
        # If odd-numbered walkway index, reverse the order (simulating reverse direction)
        if len(walkways) > 1:
            for i, walkway in enumerate(walkways):
                if i % 2 == 1:  # Reverse for odd-indexed walkways (A09, A11, etc.)
                    walkway_df = result[result['Walkway'] == walkway]
                    result = result[result['Walkway'] != walkway]
                    result = pd.concat([result, walkway_df[::-1]], ignore_index=True)
        
        return result[['Walkway', 'Position', 'Level', 'BinID']]
    
    except ValueError as e:
        st.error(str(e))
        return None

# Streamlit app
st.title("Warehouse Pick Path Generator")
st.write("Enter bin IDs (one per line, format: AxxPyyLz or AxxPyyyLz, e.g., A08P01L1 or A08P100L1) to generate the pick path.")

# Input text area
bin_input = st.text_area("Bin IDs", height=200, placeholder="A08P01L1\nA08P100L1\nA08P02L1\n...")

if st.button("Generate Pick Path"):
    if bin_input.strip():
        pick_path = generate_pick_path(bin_input)
        if pick_path is not None:
            st.subheader("Generated Pick Path")
            st.dataframe(pick_path, use_container_width=True)
    else:
        st.warning("Please enter at least one valid bin ID.")
