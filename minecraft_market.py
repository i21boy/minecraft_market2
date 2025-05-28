from pyairtable import Table
import streamlit as st
import pandas as pd

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

def main():
    # Initialize session state for rerun if not exists
    if "rerun" not in st.session_state:
        st.session_state.rerun = False

    # Handle rerun at the very top
    if st.session_state.rerun:
        st.session_state.rerun = False
        st.experimental_rerun()
        return

    st.title("Minecraft Market")
    
    # Load market data
    df = view_market()
    
    # Sidebar for adding and deleting items
    with st.sidebar:
        st.header("Add New Item")
        item = st.text_input("Item Name")
        price = st.text_input("Price (coins)")
        seller = st.text_input("Seller Name")

        if st.button("Add Item"):
            if item and price and seller:
                if add_items(item, price, seller):
                    st.success("Item added successfully!")
                    st.session_state.rerun = True
                    return
                else:
                    st.error("Failed to add item.")
            else:
                st.error("Please fill in all fields")

        st.header("Delete Item")
        if not df.empty:
            # Create display column for selection
            df["display"] = df.apply(lambda row: f"{row['Item']} - {row['Price']} coins - {row['Seller']}", axis=1)
            items_to_delete = df["display"].tolist()
            
            # Use a unique key for the selectbox
            selected_item = st.selectbox("Select item to delete:", items_to_delete, key="delete_select")
            
            if st.button("Delete Selected Item"):
                try:
                    record_id = df[df["display"] == selected_item]["_record_id"].values[0]
                    if delete_item(record_id):
                        st.success("Item deleted!")
                        st.session_state.rerun = True
                        return
                    else:
                        st.error("Failed to delete item.")
                except Exception as e:
                    st.error(f"Error during deletion: {str(e)}")
        else:
            st.info("Market is empty. Add some items!")

    # Main area for viewing market
    st.header("Market Items")
    if not df.empty:
        # Safely drop columns that might not exist
        display_df = df.copy()
        for col in ["display", "_record_id"]:
            if col in display_df.columns:
                display_df = display_df.drop(columns=[col])
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Market is empty. Add some items!")

if __name__ == "__main__":
    main()






            
