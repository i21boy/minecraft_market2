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
        sheet = gc.open('Minecraft Market').sheet1
        sheet.append_row([item, price, seller])
    except Exception as e:
        st.error(f"Error adding item: {type(e).__name__}: {e}")

def view_market():
    try:
        gc = setup_google_sheets()
        sheet = gc.open('Minecraft Market').sheet1
        
        # Try to get all values by specifying a range
        # Read a generous range (e.g., up to row 1000, column Z)
        # Adjust the range if you expect more data
        all_values = sheet.get_values('A1:Z1000')
        
        # Check if any data was returned (even just headers)
        if not all_values:
             # Return an empty DataFrame with expected columns if completely empty
            return pd.DataFrame(columns=["Item", "Price", "Seller"])
        else:
            # Assume the first row is the header
            headers = all_values[0]
            # The rest are the data rows
            data_rows = all_values[1:]

            # Create DataFrame
            if not data_rows: # If only headers were returned
                 # Ensure headers have no empty strings if range read beyond actual data
                 cleaned_headers = [h for h in headers if h]
                 # Ensure we have at least the expected columns if headers are missing/empty
                 if not cleaned_headers:
                     cleaned_headers = ["Item", "Price", "Seller"]
                 return pd.DataFrame(columns=cleaned_headers) # Create DataFrame with headers but no data
            else:
                 # Ensure headers match the number of columns in data_rows
                 # This can happen if reading a range includes empty cells in header row beyond actual data
                 cleaned_headers = [h for h in headers[:len(data_rows[0])] if h]
                 # Ensure we have at least the expected columns if headers are missing/empty
                 if not cleaned_headers:
                      cleaned_headers = ["Item", "Price", "Seller"]
                 # Pad data rows with empty strings if they are shorter than headers (unlikely with get_values but defensive)
                 padded_data_rows = [row + [''] * (len(cleaned_headers) - len(row)) for row in data_rows]

                 return pd.DataFrame(padded_data_rows, columns=cleaned_headers) # Create DataFrame with headers and data
            
    except FileNotFoundError: # Keep this for local testing if needed, though GSheets won't raise it
         return pd.DataFrame(columns=["Item", "Price", "Seller"])
    except Exception as e:
        st.error(f"Error accessing Google Sheet: {type(e).__name__}: {e}")
        # Ensure an empty DataFrame is returned even on other errors
        return pd.DataFrame(columns=["Item", "Price", "Seller"])

def delete_item(index):
    try:
        gc = setup_google_sheets()
        sheet = gc.open('Minecraft Market').sheet1
        # Add 2 because Google Sheets is 1-indexed and has a header row
        # Note: This assumes a header row is present. If the sheet is truly empty
        # and you haven't added a header row, this might still cause issues.
        sheet.delete_rows(index + 2)
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
                add_items(item, price, seller)
                st.success("Item added successfully!")
                st.rerun()
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
                    item_display_strings = [f"{row['Item']} - {row['Price']} coins - {row['Seller']}" for index, row in df.iterrows()]
                    if selected_item in item_display_strings:
                        # Find the index in the display strings list
                        selected_index_in_list = item_display_strings.index(selected_item)
                        # The index in the DataFrame corresponds to this index in the list
                        # Since we are using get_all_values and handling headers manually,
                        # the DataFrame index should align with the original row index minus the header.
                        # The delete_rows method uses the actual row number (1-indexed).
                        # So, if the selected item was at index 0 in the list/DataFrame (after headers),
                        # it corresponds to row 2 in the sheet.
                        original_sheet_row_to_delete = selected_index_in_list + 2 # +1 for 0-indexing to 1-indexing, +1 for header row

                        if delete_item(selected_index_in_list): # Pass the 0-indexed list index to delete_item
                            st.success("Item deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete item.")
                    else:
                        st.error("Selected item not found in the current market list.")
                except Exception as e:
                    st.error(f"Error finding item index: {type(e).__name__}: {e}")
        else:
            st.error("Market data is in an unexpected format.")
        
        # Show the full table
        st.subheader("All Items")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Market is empty. Add some items!")


if __name__ == "__main__":
    main()


            
