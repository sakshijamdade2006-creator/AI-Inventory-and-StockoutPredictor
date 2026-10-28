import streamlit as st
import pandas as pd

st.set_page_config(page_title="AI Inventory & Stockout Predictor", page_icon="📦", layout="wide")
st.title("📦 AI Inventory & Stockout Predictor")
st.caption("Python + Streamlit inventory dashboard with stockout-risk estimates and reorder suggestions.")
st.info("Student prototype: current calculations are rule-based, not a trained machine-learning model.")

def sample_data():
    return [
        {"Product":"Wireless Mouse","SKU":"ELEC-001","Category":"Electronics","Current Stock":18,"Daily Sales":5.0,"Lead Time (days)":4,"Safety Stock":8,"Unit Cost (₹)":450.0,"Supplier":"Tech Supply Co."},
        {"Product":"Notebook A5","SKU":"STAT-002","Category":"Stationery","Current Stock":120,"Daily Sales":8.0,"Lead Time (days)":3,"Safety Stock":20,"Unit Cost (₹)":35.0,"Supplier":"Paper World"},
        {"Product":"USB-C Cable","SKU":"ELEC-003","Category":"Electronics","Current Stock":12,"Daily Sales":4.0,"Lead Time (days)":5,"Safety Stock":10,"Unit Cost (₹)":180.0,"Supplier":"Connect Traders"},
        {"Product":"Water Bottle","SKU":"HOME-004","Category":"Home","Current Stock":45,"Daily Sales":3.0,"Lead Time (days)":6,"Safety Stock":10,"Unit Cost (₹)":220.0,"Supplier":"Daily Needs Ltd."},
    ]

if "inventory" not in st.session_state:
    st.session_state.inventory = sample_data()

def calculate(records):
    output = []
    for p in records:
        stock = max(0, float(p["Current Stock"]))
        sales = max(0, float(p["Daily Sales"]))
        lead = max(0, float(p["Lead Time (days)"]))
        safety = max(0, float(p["Safety Stock"]))
        days = stock / sales if sales > 0 else None
        reorder = sales * lead + safety
        if sales == 0:
            status = "No sales data"
        elif days < lead:
            status = "High risk"
        elif stock <= reorder:
            status = "Reorder soon"
        else:
            status = "Healthy"
        suggested = max(0, int(round(sales * (lead + 7) + safety - stock)))
        output.append({**p, "Days of Stock Left": round(days, 1) if days is not None else None,
                       "Reorder Point": int(round(reorder)), "Stock Status": status,
                       "Suggested Order": suggested,
                       "Inventory Value (₹)": round(stock * float(p["Unit Cost (₹)"]), 2)})
    return output

with st.sidebar:
    st.header("Controls")
    if st.button("Load sample data", use_container_width=True):
        st.session_state.inventory = sample_data()
        st.rerun()
    if st.button("Clear all products", use_container_width=True):
        st.session_state.inventory = []
        st.rerun()
    st.divider()
    st.subheader("Formulas")
    st.write("Days left = Current stock ÷ Average daily sales")
    st.write("Reorder point = Daily sales × Lead time + Safety stock")
    st.write("Suggested order covers lead time + 7 days, plus safety stock, minus current stock.")

with st.expander("➕ Add a product"):
    with st.form("add_product", clear_on_submit=True):
        a,b,c = st.columns(3)
        name = a.text_input("Product name *")
        sku = b.text_input("SKU / code *")
        category = c.selectbox("Category", ["Electronics","Stationery","Home","Food","Clothing","Other"])
        a,b,c = st.columns(3)
        stock = a.number_input("Current stock", min_value=0, step=1)
        sales = b.number_input("Average daily sales", min_value=0.0, step=0.5, value=1.0)
        lead = c.number_input("Supplier lead time (days)", min_value=0, step=1, value=3)
        a,b,c = st.columns(3)
        safety = a.number_input("Safety stock", min_value=0, step=1, value=5)
        cost = b.number_input("Unit cost (₹)", min_value=0.0, step=10.0, value=100.0)
        supplier = c.text_input("Supplier", value="Not specified")
        if st.form_submit_button("Add product", type="primary"):
            if not name.strip() or not sku.strip():
                st.error("Enter both product name and SKU.")
            elif any(x["SKU"].lower() == sku.strip().lower() for x in st.session_state.inventory):
                st.error("SKU already exists. Use a unique SKU.")
            else:
                st.session_state.inventory.append({"Product":name.strip(),"SKU":sku.strip(),"Category":category,
                    "Current Stock":int(stock),"Daily Sales":float(sales),"Lead Time (days)":int(lead),
                    "Safety Stock":int(safety),"Unit Cost (₹)":float(cost),"Supplier":supplier.strip() or "Not specified"})
                st.success("Product added.")
                st.rerun()

items = calculate(st.session_state.inventory)
df = pd.DataFrame(items)
total = len(items)
attention_count = sum(x["Stock Status"] in ["High risk","Reorder soon"] for x in items)
risk_count = sum(x["Stock Status"] == "High risk" for x in items)
value = sum(float(x["Current Stock"]) * float(x["Unit Cost (₹)"]) for x in items)
k1,k2,k3,k4 = st.columns(4)
k1.metric("Total products", total)
k2.metric("Low stock / reorder", attention_count)
k3.metric("High stockout risk", risk_count)
k4.metric("Inventory value", f"₹{value:,.2f}")

st.divider()
st.subheader("📊 Inventory overview")
if df.empty:
    st.warning("No products yet. Add one above or load sample data from the sidebar.")
else:
    a,b = st.columns([2,1])
    search = a.text_input("Search product, SKU, category, or supplier")
    status_filter = b.selectbox("Filter status", ["All","Healthy","Reorder soon","High risk","No sales data"])
    shown = df.copy()
    if search.strip():
        q = search.strip().lower()
        mask = (shown["Product"].astype(str).str.lower().str.contains(q, na=False) |
                shown["SKU"].astype(str).str.lower().str.contains(q, na=False) |
                shown["Category"].astype(str).str.lower().str.contains(q, na=False) |
                shown["Supplier"].astype(str).str.lower().str.contains(q, na=False))
        shown = shown[mask]
    if status_filter != "All":
        shown = shown[shown["Stock Status"] == status_filter]
    st.dataframe(shown[["Product","SKU","Category","Current Stock","Daily Sales","Days of Stock Left",
        "Lead Time (days)","Reorder Point","Stock Status","Suggested Order","Inventory Value (₹)"]],
        use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download inventory CSV", shown.to_csv(index=False).encode("utf-8"),
                       "inventory_report.csv", "text/csv")

    st.subheader("🚨 Products needing attention")
    attention = df[df["Stock Status"].isin(["High risk","Reorder soon"])].copy()
    if attention.empty:
        st.success("No products currently need reordering based on these estimates.")
    else:
        st.dataframe(attention[["Product","SKU","Current Stock","Days of Stock Left","Lead Time (days)",
            "Reorder Point","Suggested Order","Supplier"]].sort_values("Days of Stock Left", na_position="last"),
            use_container_width=True, hide_index=True)

    st.subheader("✏️ Edit or delete a product")
    skus = [x["SKU"] for x in st.session_state.inventory]
    selected_sku = st.selectbox("Select SKU", skus)
    selected = next(x for x in st.session_state.inventory if x["SKU"] == selected_sku)
    with st.form("edit_product"):
        a,b,c = st.columns(3)
        edit_name = a.text_input("Product name", selected["Product"])
        categories = ["Electronics","Stationery","Home","Food","Clothing","Other"]
        edit_category = b.selectbox("Category", categories, index=categories.index(selected["Category"]) if selected["Category"] in categories else 5)
        edit_supplier = c.text_input("Supplier", selected["Supplier"])
        a,b,c = st.columns(3)
        edit_stock = a.number_input("Current stock ", min_value=0, step=1, value=int(selected["Current Stock"]))
        edit_sales = b.number_input("Daily sales ", min_value=0.0, step=0.5, value=float(selected["Daily Sales"]))
        edit_lead = c.number_input("Lead time (days) ", min_value=0, step=1, value=int(selected["Lead Time (days)"]))
        a,b = st.columns(2)
        edit_safety = a.number_input("Safety stock ", min_value=0, step=1, value=int(selected["Safety Stock"]))
        edit_cost = b.number_input("Unit cost (₹) ", min_value=0.0, step=10.0, value=float(selected["Unit Cost (₹)"]))
        if st.form_submit_button("Save changes"):
            for p in st.session_state.inventory:
                if p["SKU"] == selected_sku:
                    p.update({"Product":edit_name.strip() or p["Product"],"Category":edit_category,
                        "Supplier":edit_supplier.strip() or "Not specified","Current Stock":int(edit_stock),
                        "Daily Sales":float(edit_sales),"Lead Time (days)":int(edit_lead),
                        "Safety Stock":int(edit_safety),"Unit Cost (₹)":float(edit_cost)})
                    break
            st.success("Product updated.")
            st.rerun()
    if st.button("🗑️ Delete selected product"):
        st.session_state.inventory = [p for p in st.session_state.inventory if p["SKU"] != selected_sku]
        st.rerun()

st.divider()
st.caption("Educational prototype. For a real AI forecasting project, train and evaluate a model using historical sales data.")
