import csv
import streamlit as st
import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials

def setup_google_sheets():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    
    gc = gspread.authorize(credentials)
    return gc

def add_items(item, price, seller):
    try:
        gc = setup_google_sheets()
        sheet = gc.open('minecraft market').sheet1
        sheet.append_row([item, price, seller])
        return True
    except Exception as e:
        st.error(f"Error adding item: {type(e).__name__}: {e}")
        return False

def view_market():
    try:
        gc = setup_google_sheets()
        sheet = gc.open('minecraft market').sheet1
        
        # *** Test reading the first row explicitly ***
        try:
            header_row_values = sheet.row_values(1) # Read the first row
            st.write("DEBUG: Successfully read header row:", header_row_values)
        except Exception as e:
             st.error(f"DEBUG: Failed to read header row: {type(e).__name__}: {e}")
             # If reading header fails, return empty DataFrame and stop
             return pd.DataFrame(columns=["Item", "Price", "Seller"])

        # Original logic to get all values (keeping for now, but main focus is above test)
        all_values = sheet.get_values('A1:Z1000') # Using get_values as in previous attempt
        
        st.write("DEBUG: Data read from sheet (get_values):", all_values)
        
        # Check if any data was returned (even just headers)
        if not all_values:
            st.write("DEBUG: Sheet is completely empty via get_values.")
            return pd.DataFrame(columns=["Item", "Price", "Seller"])
        else:
            st.write("DEBUG: Sheet has values via get_values.")
            # Assume the first row is the header
            headers = all_values[0]
            st.write("DEBUG: Headers detected from get_values:", headers)

            # The rest are the data rows
            data_rows = all_values[1:]
            st.write("DEBUG: Data rows detected from get_values:", data_rows)

            # Clean headers - remove empty strings if range read extends beyond actual columns
            cleaned_headers = [h for h in headers if h]
            st.write("DEBUG: Cleaned headers:", cleaned_headers)

            # Ensure we have at least the expected columns if headers are missing/empty
            if not cleaned_headers:
                cleaned_headers = ["Item", "Price", "Seller"]
                st.write("DEBUG: Using default headers.")

            # Create DataFrame
            if not data_rows: # If only headers were returned
                st.write("DEBUG: Only headers found, no data rows via get_values.")
                # Create DataFrame with headers but no data
                return pd.DataFrame(columns=cleaned_headers)
            else:
                st.write("DEBUG: Headers and data rows found via get_values.")
                # Ensure data rows have the same number of columns as cleaned headers
                # Pad data rows with empty strings if they are shorter than headers
                # This can happen if get_values reads a rectangular range into jagged data
                expected_cols = len(cleaned_headers)
                padded_data_rows = [row + [''] * (expected_cols - len(row)) for row in data_rows]

                # Trim data rows if they have more columns than headers (less likely with get_values but defensive)
                trimmed_padded_data_rows = [row[:expected_cols] for row in padded_data_rows]
                st.write("DEBUG: Padded/trimmed data rows:", trimmed_padded_data_rows)

                # Create DataFrame with headers and data
                return pd.DataFrame(trimmed_padded_data_rows, columns=cleaned_headers)
            
    except FileNotFoundError: # Keep this for local testing if needed, though GSheets won't raise it
        st.error("DEBUG: FileNotFoundError caught.")
        return pd.DataFrame(columns=["Item", "Price", "Seller"])
    except Exception as e:
        # This is where the unusual <Response [200]> error might be coming from
        st.error(f"Error accessing Google Sheet: {type(e).__name__}: {e}")
        # Ensure an empty DataFrame is returned even on other errors
        return pd.DataFrame(columns=["Item", "Price", "Seller"])

def delete_item(index):
    try:
        gc = setup_google_sheets()
        sheet = gc.open('minecraft market').sheet1
        # Add 2 because Google Sheets is 1-indexed and has a header row
        # Pass the 0-indexed list/DataFrame index from main()
        # Convert it to the 1-indexed sheet row number
        sheet_row_to_delete = index + 2
        st.write(f"DEBUG: Deleting sheet row: {sheet_row_to_delete}")
        sheet.delete_rows(sheet_row_to_delete)
        return True
    except Exception as e:
        st.error(f"Error deleting item: {type(e).__name__}: {e}")
        return False

def main():
    st.title("Minecraft Market")
    
    # Sidebar for adding items
    with st.sidebar:
        st.header("Add New Item")
        item = st.text_input("Item Name")
        price = st.text_input("Price (coins)")
        seller = st.text_input("Seller Name")
        
        if st.button("Add Item"):
            if item and price and seller:
                if add_items(item, price, seller):
                    st.success("Item added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add item.")
            else:
                st.error("Please fill in all fields")

    # Main area for viewing market
    st.header("Market Items")
    df = view_market()
    if not df.empty:
        # Add delete section
        st.subheader("Delete Item")
        # Create a dropdown with all items
        if all(col in df.columns for col in ["Item", "Price", "Seller"]):
            items_to_delete = [f"{row['Item']} - {row['Price']} coins - {row['Seller']}" for _, row in df.iterrows()]
            selected_item = st.selectbox("Select item to delete:", items_to_delete)
            
            if st.button("Delete Selected Item"):
                # Find the index of the selected item
                try:
                    # Recreate the display string for comparison
                    matching_rows = df[
                        (df['Item'].astype(str) == selected_item.split(' - ')[0]) &
                        (df['Price'].astype(str) == selected_item.split(' - ')[1].replace(' coins', '').strip()) &
                        (df['Seller'].astype(str) == selected_item.split(' - ')[2].replace('Seller: ', '').strip())
                    ]

                    if not matching_rows.empty:
                        # Get the index of the first matching row (should be unique if items are unique)
                        original_index = matching_rows.index[0]

                        # The delete_item function expects the 0-indexed DataFrame/list index
                        if delete_item(original_index):
                            st.success("Item deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete item.")
                    else:
                        st.error("Selected item not found in the current market list.")
                except Exception as e:
                    st.error(f"Error finding item index or deleting: {type(e).__name__}: {e}")
        else:
            st.error("Market data is in an unexpected format or empty after attempted read.")
        
        # Show the full table
        st.subheader("All Items")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Market is empty. Add some items!")


if __name__ == "__main__":
    main()



            
