from pyairtable import Table
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="Minecraft Market",
    page_icon="⛏️",
    layout="wide"
)

# Airtable credentials from Streamlit secrets
token = st.secrets["airtable"]["token"]
base_id = st.secrets["airtable"]["base_id"]
table_name = st.secrets["airtable"]["table_name"]

table = Table(token, base_id, table_name)

def add_items(item, price, seller):
    # Remove any accidental extra quotes from user input
    item = item.strip('"')
    price = price.strip('"')
    seller = seller.strip('"')
    try:
        table.create({"Item": item, "Price": price, "Seller": seller})
        return True
    except Exception as e:
        st.error(f"Error adding item: {type(e).__name__}: {e}")
        return False

def view_market():
    try:
        records = table.all()
        data = []
        record_ids = []
        for r in records:
            fields = r.get("fields", {})
            data.append(fields)
            record_ids.append(r.get("id"))
        df = pd.DataFrame(data)
        if not df.empty:
            df["_record_id"] = record_ids
        return df
    except Exception as e:
        st.error(f"Error accessing Airtable: {type(e).__name__}: {e}")
        return pd.DataFrame(columns=["Item", "Price", "Seller", "_record_id"])

def delete_item(record_id):
    try:
        table.delete(record_id)
        return True
    except Exception as e:
        st.error(f"Error deleting item: {type(e).__name__}: {e}")
        return False

def get_next_refresh_time():
    # Get current time
    now = datetime.now()
    # Calculate next refresh time (5 minutes from now)
    next_refresh = now + timedelta(minutes=5)
    # Format the time
    return next_refresh.strftime("%H:%M:%S")

def main():
    st.title("Minecraft Market")
    
    # Initialize session state for form data and last update time
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "last_update" not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    # Add refresh status
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # Create a container for the refresh info
    refresh_info = st.sidebar.container()
    with refresh_info:
        st.markdown(f"🔄 Last updated: {current_time}")
    
    # Create a container for the market table
    market_container = st.container()
    
    # Sidebar for adding and deleting items
    with st.sidebar:
        st.header("Add New Item")
        with st.form("add_item_form"):
            item = st.text_input("Item Name")
            price = st.text_input("Price (coins)")
            seller = st.text_input("Seller Name")
            add_submitted = st.form_submit_button("Add Item")
            
            if add_submitted:
                if item and price and seller:
                    if add_items(item, price, seller):
                        st.success("Item added successfully!")
                        st.session_state.form_submitted = True
                        st.session_state.last_update = datetime.now()
                        st.rerun()  # Trigger immediate update
                    else:
                        st.error("Failed to add item.")
                else:
                    st.error("Please fill in all fields")

        st.header("Delete Item")
        df = view_market()
        if not df.empty:
            # Create display column for selection
            df["display"] = df.apply(lambda row: f"{row['Item']} - {row['Price']} coins - {row['Seller']}", axis=1)
            items_to_delete = df["display"].tolist()
            
            with st.form("delete_item_form"):
                selected_item = st.selectbox("Select item to delete:", items_to_delete, key="delete_select")
                delete_submitted = st.form_submit_button("Delete Selected Item")
                
                if delete_submitted:
                    try:
                        record_id = df[df["display"] == selected_item]["_record_id"].values[0]
                        if delete_item(record_id):
                            st.success("Item deleted!")
                            st.session_state.form_submitted = True
                            st.session_state.last_update = datetime.now()
                            st.rerun()  # Trigger immediate update
                        else:
                            st.error("Failed to delete item.")
                    except Exception as e:
                        st.error(f"Error during deletion: {str(e)}")
        else:
            st.info("Market is empty. Add some items!")

    # Main area for viewing market
    with market_container:
        st.header("Market Items")
        df = view_market()
        if not df.empty:
            # Safely drop columns that might not exist
            display_df = df.copy()
            for col in ["display", "_record_id"]:
                if col in display_df.columns:
                    display_df = display_df.drop(columns=[col])
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Market is empty. Add some items!")

    # Reset form submitted state after displaying the updated data
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False

if __name__ == "__main__":
    main()






            
