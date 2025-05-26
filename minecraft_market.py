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
        
        # Try to get all records
        data = sheet.get_all_records()
        
        # Check if any data was returned
        if not data: # If data is an empty list
             # Return an empty DataFrame with expected columns
            return pd.DataFrame(columns=["Item", "Price", "Seller"])
        else:
            # Otherwise, create DataFrame from the data
            return pd.DataFrame(data)
            
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
                        selected_index_in_df = item_display_strings.index(selected_item)
                        original_index = df.index[selected_index_in_df] # Get the original DataFrame index

                        if delete_item(original_index): # Use the original DataFrame index for deletion
                            st.success("Item deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete item.")
                    else:
                        st.error("Selected item not found in the current market list.")
                except Exception as e:
                    st.error(f"Error finding item index: {type(e).__name__}: {e}")
        
        # Show the full table
        st.subheader("All Items")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Market is empty. Add some items!")


if __name__ == "__main__":
    main()

            
