import src.mrp as mrp
import streamlit as st

st.title("Material Requirements Planning System (MRP)")

tab1 = st.tabs(["MRP"])[0]

with tab1:
    if st.button("Start Algorithm"):
        mrp1 = mrp.Mrp()
        mrp1.start_algorithm()

        st.header("Wyniki MRP")
        for component, mrp_df in mrp1.mrp_dfs.items():
            st.subheader(f"Plan MRP dla komponentu: {component}")
            st.dataframe(mrp_df)




