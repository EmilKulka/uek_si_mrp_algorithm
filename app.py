import pandas as pd
import streamlit as st
import src.mrp as mrp
import src.mps as mps
import src.bom as bom


st.set_page_config(layout="wide", page_title="System planowania wymagań materiałowych (MRP)")

st.title("System planowania wymagań materiałowych (MRP)")

tab1, tab2 = st.tabs(["Dane wejściowe", "Wyniki MRP"])

if 'mrp_instance' not in st.session_state:
    st.session_state.mrp_instance = None
if 'mrp_results' not in st.session_state:
    st.session_state.mrp_results = {}
if 'pending_decisions' not in st.session_state:
    st.session_state.pending_decisions = []
if 'custom_mps' not in st.session_state:
    st.session_state.custom_mps = None
if 'processed_components' not in st.session_state:
    st.session_state.processed_components = set()
if 'component_parameters' not in st.session_state:
    st.session_state.component_parameters = {}

with tab1:
    st.header("Dane MPS")
    
    mps_input_method = st.radio(
        "Wybierz sposób wprowadzania danych MPS:",
        ["Domyślne dane", "Wprowadź dane ręcznie"]
    )
    
    mps_lead_time = st.number_input("Czas realizacji produktu końcowego (MPS Lead Time):", 
                              min_value=1, value=1, step=1)
    
    if mps_input_method == "Wprowadź dane ręcznie":
        st.info("Wprowadź dane MPS dla każdego tygodnia:")
        
        forecast_demand = [0] * 10
        production = [0] * 10
        available = [0] * 10
        
        st.write("Wprowadź dane dla każdego tygodnia:")
        
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Tydzień")
        for i in range(1, 11):
            with cols[i]:
                st.write(f"{i}")
        
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Przewidywany popyt")
        for i in range(10):
            with cols[i+1]:
                forecast_demand[i] = st.number_input(f"Popyt wk{i+1}", value=0, key=f"demand_{i}", 
                                         label_visibility="collapsed")
        
        
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Produkcja")
        for i in range(10):
            with cols[i+1]:
                production[i] = st.number_input(f"Prod wk{i+1}", value=0, key=f"prod_{i}", 
                                  label_visibility="collapsed")
        
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Dostępne")
        for i in range(10):
            with cols[i+1]:
                available[i] = st.number_input(f"Avail wk{i+1}", value=0, key=f"avail_{i}", 
                                 label_visibility="collapsed")
        
        if st.button("Potwierdź dane MPS"):
            try:
                st.session_state.custom_mps = mps.Mps.from_form_data(
                    forecast_demand, production, available, lead_time=mps_lead_time
                )
                # Resetujemy wyniki po zmianie MPS
                st.session_state.mrp_instance = None
                st.session_state.mrp_results = {}
                st.session_state.processed_components = set()
                st.session_state.pending_decisions = []
                
                st.success("Dane MPS zostały wprowadzone pomyślnie!")
                st.dataframe(st.session_state.custom_mps.mps_df)
            except Exception as e:
                st.error(f"Błąd podczas przetwarzania danych MPS: {str(e)}")
    else:
        st.session_state.custom_mps = mps.Mps(lead_time=mps_lead_time)
        st.info("Zostaną użyte domyślne dane MPS")
        st.dataframe(st.session_state.custom_mps.mps_df)
    
    st.header("Zarządzanie komponentami")
    
    # Inicjalizacja instancji MRP i BOM
    if st.session_state.mrp_instance is None:
        st.session_state.mrp_instance = mrp.Mrp(st.session_state.custom_mps)
        
    bom_instance = bom.Bom()
    bom_df = bom_instance.bom_df
    
    # Wyświetlenie struktury BOM
    st.subheader("Struktura BOM")
    st.dataframe(bom_df)
    
    # Inicjalizacja parametrów komponentów, jeśli jeszcze nie istnieją
    if not st.session_state.component_parameters:
        for _, row in bom_df.iterrows():
            component_name = row['component_name']
            st.session_state.component_parameters[component_name] = {
                'lead_time': row['lead_time'],
                'in_stock': row['in_stock'],
                'batch_size': row['batch_size']
            }
    
    # Sekcja do edycji parametrów komponentów
    st.subheader("Edycja parametrów komponentów")
    
    component_col1, component_col2 = st.columns(2)
    
    with component_col1:
        selected_component = st.selectbox("Wybierz komponent:", bom_df['component_name'].unique())
    
    with component_col2:
        st.write("Poziom:", bom_df[bom_df['component_name'] == selected_component]['LVL'].values[0])
        st.write("Komponent nadrzędny:", bom_df[bom_df['component_name'] == selected_component]['parent_name'].values[0])
        st.write("Ilość:", bom_df[bom_df['component_name'] == selected_component]['quantity'].values[0])
    
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        lead_time = st.number_input(
            "Czas realizacji (Lead Time):", 
            min_value=1, 
            value=st.session_state.component_parameters[selected_component]['lead_time'], 
            step=1,
            key=f"lead_time_{selected_component}"
        )
        st.session_state.component_parameters[selected_component]['lead_time'] = lead_time
    
    with param_col2:
        in_stock = st.number_input(
            "Stan magazynowy (In Stock):", 
            min_value=0, 
            value=st.session_state.component_parameters[selected_component]['in_stock'], 
            step=1,
            key=f"in_stock_{selected_component}"
        )
        st.session_state.component_parameters[selected_component]['in_stock'] = in_stock
    
    with param_col3:
        batch_size = st.number_input(
            "Wielkość partii (Batch Size):", 
            min_value=0, 
            value=st.session_state.component_parameters[selected_component]['batch_size'], 
            step=1,
            key=f"batch_size_{selected_component}"
        )
        st.session_state.component_parameters[selected_component]['batch_size'] = batch_size
    
    # Sekcja do uruchamiania algorytmu MRP dla wybranego komponentu
    st.subheader("Uruchom algorytm MRP dla komponentu")
    
    first_level_components = bom_df[bom_df['LVL'] == 1]['component_name'].tolist()
    second_level_components = bom_df[bom_df['LVL'] == 2]['component_name'].tolist()
    
    for component in first_level_components:
        component_status = "✅" if component in st.session_state.processed_components else "❌"
        if st.button(f"Oblicz MRP dla {component} {component_status}", key=f"calc_{component}"):
            with st.spinner(f"Obliczanie MRP dla {component}..."):
                # Aktualizacja parametrów komponentu w BOM
                bom_df.loc[bom_df['component_name'] == component, 'lead_time'] = st.session_state.component_parameters[component]['lead_time']
                bom_df.loc[bom_df['component_name'] == component, 'in_stock'] = st.session_state.component_parameters[component]['in_stock']
                bom_df.loc[bom_df['component_name'] == component, 'batch_size'] = st.session_state.component_parameters[component]['batch_size']
                
                # Aktualizacja BOM w instancji MRP
                st.session_state.mrp_instance.bom.bom_df = bom_df
                
                # Obliczenia MRP dla komponentu pierwszego poziomu
                component_mrp_df = st.session_state.mrp_instance.generate_empty_mrp_df()
                
                # Pobieranie danych produkcji dla pierwszego poziomu
                first_lvl_comp_production_weeks = st.session_state.mrp_instance.get_first_lvl_comp_prod_weeks()
                mps_lead_time = st.session_state.mrp_instance.mps.lead_time
                
                # Obliczanie zapotrzebowania brutto
                for production_week, quantity in first_lvl_comp_production_weeks.items():
                    gross_req_week = production_week - mps_lead_time
                    if gross_req_week > 0:
                        component_mrp_df.at['Gross_Requirements', gross_req_week] = quantity
                
                # Przetwarzanie tygodniowego zapotrzebowania
                component_in_stock = st.session_state.component_parameters[component]['in_stock']
                component_lead_time = st.session_state.component_parameters[component]['lead_time']
                component_batch_size = st.session_state.component_parameters[component]['batch_size']
                
                # Włączamy tryb interaktywny, aby zbierać decyzje użytkownika
                st.session_state.mrp_instance.interactive_mode = True
                
                for week in range(1, 11):
                    component_in_stock = st.session_state.mrp_instance._process_weekly_requirements(
                        component_mrp_df, week, component_in_stock, 
                        component_lead_time, component_batch_size, component
                    )
                
                # Zapisanie wyników
                st.session_state.mrp_results[component] = component_mrp_df
                st.session_state.processed_components.add(component)
                
                # Aktualizujemy pending_decisions
                st.session_state.pending_decisions = st.session_state.mrp_instance.pending_decisions
                
                st.success(f"Obliczenia MRP dla {component} zakończone pomyślnie!")
                if len(st.session_state.pending_decisions) > 0:
                    st.info(f"Masz {len(st.session_state.pending_decisions)} decyzji do podjęcia w zakładce Wyniki MRP.")
                st.rerun()
    
    st.markdown("---")
    st.subheader("Komponenty drugiego poziomu")
    
    for component in second_level_components:
        parent_name = bom_df[bom_df['component_name'] == component]['parent_name'].values[0]
        component_status = "✅" if component in st.session_state.processed_components else "❌"
        parent_status = "✅" if parent_name in st.session_state.processed_components else "❌"
        
        button_disabled = parent_name not in st.session_state.processed_components
        
        if button_disabled:
            st.warning(f"Najpierw oblicz MRP dla komponentu nadrzędnego: {parent_name}")
        
        if st.button(f"Oblicz MRP dla {component} {component_status}", key=f"calc_{component}", disabled=button_disabled):
            with st.spinner(f"Obliczanie MRP dla {component}..."):
                # Aktualizacja parametrów komponentu w BOM
                bom_df.loc[bom_df['component_name'] == component, 'lead_time'] = st.session_state.component_parameters[component]['lead_time']
                bom_df.loc[bom_df['component_name'] == component, 'in_stock'] = st.session_state.component_parameters[component]['in_stock']
                bom_df.loc[bom_df['component_name'] == component, 'batch_size'] = st.session_state.component_parameters[component]['batch_size']
                
                # Aktualizacja BOM w instancji MRP
                st.session_state.mrp_instance.bom.bom_df = bom_df
                
                # Pobieranie informacji o komponencie
                component_quantity = bom_df[(bom_df['component_name'] == component) & 
                                           (bom_df['parent_name'] == parent_name)]['quantity'].values[0]
                component_lead_time = st.session_state.component_parameters[component]['lead_time']
                component_in_stock = st.session_state.component_parameters[component]['in_stock']
                component_batch_size = st.session_state.component_parameters[component]['batch_size']
                
                # Tworzenie pustego dataframe MRP
                component_mrp_df = st.session_state.mrp_instance.generate_empty_mrp_df()
                
                # Pobieranie danych MRP komponentu nadrzędnego
                parent_mrp_df = st.session_state.mrp_results.get(parent_name)
                
                # Włączamy tryb interaktywny, aby zbierać decyzje użytkownika
                st.session_state.mrp_instance.interactive_mode = True
                
                # Obliczanie zapotrzebowania brutto na podstawie planowanych zamówień komponentu nadrzędnego
                for week in range(1, 11):
                    parent_planned_releases = parent_mrp_df.at['Planned_orders_releases', week]
                    
                    if parent_planned_releases and parent_planned_releases > 0:
                        gross_req = parent_planned_releases * component_quantity
                        component_mrp_df.at['Gross_Requirements', week] = gross_req
                
                # Przetwarzanie tygodniowego zapotrzebowania
                for week in range(1, 11):
                    component_in_stock = st.session_state.mrp_instance._process_weekly_requirements(
                        component_mrp_df, week, component_in_stock, 
                        component_lead_time, component_batch_size, component
                    )
                
                # Zapisanie wyników
                st.session_state.mrp_results[component] = component_mrp_df
                st.session_state.mrp_instance.mrp_dfs[component] = component_mrp_df
                st.session_state.processed_components.add(component)
                
                # Aktualizujemy pending_decisions
                st.session_state.pending_decisions = st.session_state.mrp_instance.pending_decisions
                
                st.success(f"Obliczenia MRP dla {component} zakończone pomyślnie!")
                if len(st.session_state.pending_decisions) > 0:
                    st.info(f"Masz {len(st.session_state.pending_decisions)} decyzji do podjęcia w zakładce Wyniki MRP.")
                st.rerun()
    
    if st.button("Wyczyść wszystkie obliczenia"):
        st.session_state.mrp_results = {}
        st.session_state.processed_components = set()
        st.session_state.pending_decisions = []
        st.success("Wszystkie obliczenia zostały wyczyszczone.")
        st.rerun()

with tab2:
    st.header("Wyniki MRP")

    if st.session_state.mrp_results:
        if st.session_state.pending_decisions:
            st.subheader("Decyzje oczekujące na użytkownika")
            st.info(
                "Te decyzje wymagają Twojej interwencji. Możesz je dostosować dla lepszych wyników.")

            for i, decision in enumerate(st.session_state.pending_decisions):
                with st.expander(f"Decyzja dla komponentu: {decision['component']} (Tydzień {decision['week']})"):
                    st.write(f"Komponent: {decision['component']}")
                    st.write(f"Tydzień: {decision['week']}")
                    st.write(f"Wymagana ilość: {decision['net_requirement']}")
                    st.write(f"Czas realizacji: {decision['lead_time']}")
                    st.write(f"Standardowa wielkość partii: {decision['batch_size']}")

                    receipt_quantity = st.number_input(
                        f"Wprowadź planowaną ilość przyjęcia:",
                        value=int(decision['net_requirement']),
                        key=f"decision_{i}"
                    )

                    st.info(
                        f"Po wprowadzeniu {receipt_quantity} sztuk w tygodniu {decision['week']}, stan zapasowy będzie wynosił: {-decision['net_requirement'] + receipt_quantity}")

                    if st.button(f"Zatwierdź decyzję", key=f"confirm_{i}"):
                        if st.session_state.mrp_instance.apply_user_decision(
                                decision['component'], decision['week'], receipt_quantity
                        ):
                            st.success(
                                f"Decyzja została zastosowana dla komponentu {decision['component']} w tygodniu {decision['week']}")
                            st.session_state.mrp_results[decision['component']] = st.session_state.mrp_instance.mrp_dfs[decision['component']]
                            st.session_state.pending_decisions = st.session_state.mrp_instance.pending_decisions
                            st.rerun()
        
        # Wyświetlanie wyników MRP dla każdego przetworzonego komponentu
        for component, mrp_df in st.session_state.mrp_results.items():
            st.subheader(f"Plan MRP dla komponentu: {component}")

            display_df = mrp_df.copy()

            for col in display_df.columns:
                for idx in display_df.index:
                    value = display_df.at[idx, col]
                    if value == -1:
                        for decision in st.session_state.pending_decisions:
                            if decision['component'] == component and decision['week'] == col:
                                display_df.at[idx, col] = f"Need decision ({decision['net_requirement']})"
                                break
                    elif pd.isna(value):
                        display_df.at[idx, col] = "" 
                    elif value == 0:
                        if idx == 'On_hand':
                            continue
                        display_df.at[idx, col] = ""  
                    elif isinstance(value, float) and value.is_integer():
                        display_df.at[idx, col] = int(value)  

            st.dataframe(display_df)

            csv = mrp_df.to_csv(sep=';')
            st.download_button(
                label=f"Pobierz plan MRP dla {component} jako CSV",
                data=csv,
                file_name=f"mrp_plan_{component}.csv",
                mime="text/csv"
            )
    else:
        st.info("Oblicz MRP dla przynajmniej jednego komponentu w zakładce 'Dane wejściowe', aby zobaczyć wyniki.")