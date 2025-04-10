import pandas as pd
import streamlit as st
import src.mrp as mrp
import src.mps as mps


st.set_page_config(layout="wide", page_title="System planowania wymagań materiałowych (MRP)")

st.title("System planowania wymagań materiałowych (MRP)")

# Utworzenie zakładek dla różnych funkcji aplikacji
tab1, tab2 = st.tabs(["Dane wejściowe", "Wyniki MRP"])

# Przechowywaj stan aplikacji w session_state
if 'mrp_instance' not in st.session_state:
    st.session_state.mrp_instance = None
if 'mrp_results' not in st.session_state:
    st.session_state.mrp_results = None
if 'pending_decisions' not in st.session_state:
    st.session_state.pending_decisions = []
if 'custom_mps' not in st.session_state:
    st.session_state.custom_mps = None

# Zakładka z danymi wejściowymi
with tab1:
    st.header("Dane MPS")
    
    mps_input_method = st.radio(
        "Wybierz sposób wprowadzania danych MPS:",
        ["Domyślne dane", "Wprowadź dane ręcznie"]
    )
    
    # Lead time dla MPS
    mps_lead_time = st.number_input("Czas realizacji produktu końcowego (MPS Lead Time):", 
                              min_value=1, value=1, step=1)
    
    if mps_input_method == "Wprowadź dane ręcznie":
        st.info("Wprowadź dane MPS dla każdego tygodnia:")
        
        col1, col2, col3 = st.columns(3)
        
        # Inicjalizacja list na dane
        forecast_demand = [0] * 10
        production = [0] * 10
        available = [0] * 10
        
        # Tabela do wprowadzania danych
        st.write("Wprowadź dane dla każdego tygodnia:")
        
        # Nagłówki kolumn
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Tydzień")
        for i in range(1, 11):
            with cols[i]:
                st.write(f"{i}")
        
        # Przewidywany popyt
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Przewidywany popyt")
        for i in range(10):
            with cols[i+1]:
                forecast_demand[i] = st.number_input(f"Popyt wk{i+1}", value=0, key=f"demand_{i}", 
                                         label_visibility="collapsed")
        
        # Produkcja
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Produkcja")
        for i in range(10):
            with cols[i+1]:
                production[i] = st.number_input(f"Prod wk{i+1}", value=0, key=f"prod_{i}", 
                                  label_visibility="collapsed")
        
        # Dostępne
        cols = st.columns([1] + [1] * 10)
        with cols[0]:
            st.write("Dostępne")
        for i in range(10):
            with cols[i+1]:
                available[i] = st.number_input(f"Avail wk{i+1}", value=0, key=f"avail_{i}", 
                                 label_visibility="collapsed")
        
        if st.button("Potwierdź dane MPS"):
            try:
                # Utwórz obiekt MPS z danych formularza
                st.session_state.custom_mps = mps.Mps.from_form_data(
                    forecast_demand, production, available, lead_time=mps_lead_time
                )
                st.success("Dane MPS zostały wprowadzone pomyślnie!")
                st.dataframe(st.session_state.custom_mps.mps_df)
            except Exception as e:
                st.error(f"Błąd podczas przetwarzania danych MPS: {str(e)}")
    else:
        st.session_state.custom_mps = mps.Mps(lead_time=mps_lead_time)
        st.info("Zostaną użyte domyślne dane MPS")
        st.dataframe(st.session_state.custom_mps.mps_df)
    
    st.header("Uruchom algorytm MRP")
    
    if st.button("Start Algorithm"):
        with st.spinner("Uruchamianie algorytmu MRP..."):
            # Inicjalizacja nowej instancji MRP z niestandardowym MPS, jeśli istnieje
            mrp_instance = mrp.Mrp(st.session_state.custom_mps)
            # Uruchom algorytm w trybie interaktywnym
            mrp_results, pending_decisions = mrp_instance.start_algorithm(interactive=True)
            
            # Zapisz wyniki w stanie sesji
            st.session_state.mrp_instance = mrp_instance
            st.session_state.mrp_results = mrp_results
            st.session_state.pending_decisions = pending_decisions
            
            st.success("Algorytm MRP został uruchomiony pomyślnie!")
            st.info(f"Liczba decyzji oczekujących na użytkownika: {len(st.session_state.pending_decisions)}")

with tab2:
    st.header("Wyniki MRP")

    if st.session_state.mrp_results:
        # Wyświetl decyzje oczekujące na użytkownika
        if st.session_state.pending_decisions:
            st.subheader("Decyzje oczekujące na użytkownika (opcjonalne)")
            st.info(
                "Algorytm będzie kontynuowany nawet bez podejmowania tych decyzji. Możesz je jednak dostosować dla lepszych wyników.")

            for i, decision in enumerate(st.session_state.pending_decisions):
                with st.expander(f"Decyzja dla komponentu: {decision['component']} (Tydzień {decision['week']})"):
                    st.write(f"Komponent: {decision['component']}")
                    st.write(f"Tydzień: {decision['week']}")
                    st.write(f"Wymagana ilość: {decision['net_requirement']}")
                    st.write(f"Czas realizacji: {decision['lead_time']}")
                    st.write(f"Standardowa wielkość partii: {decision['batch_size']}")

                    # Formularz do decyzji użytkownika
                    receipt_quantity = st.number_input(
                        f"Wprowadź planowaną ilość przyjęcia dla {decision['component']} w tygodniu {decision['week']}:",
                          # Convert to float to avoid type issues
                        value=float(max(decision['batch_size'], decision['net_requirement'])),
                        key=f"decision_{i}"
                    )

                    # Wizualizacja wpływu decyzji
                    st.info(
                        f"Po wprowadzeniu {receipt_quantity} sztuk w tygodniu {decision['week']}, stan zapasowy będzie wynosił: {decision['current_stock'] - decision['net_requirement'] + receipt_quantity}")

                    if st.button(f"Zatwierdź decyzję", key=f"confirm_{i}"):
                        # Zastosuj decyzję użytkownika
                        if st.session_state.mrp_instance.apply_user_decision(
                                decision['component'], decision['week'], receipt_quantity
                        ):
                            st.success(
                                f"Decyzja została zastosowana dla komponentu {decision['component']} w tygodniu {decision['week']}")
                            # Aktualizacja stanu sesji
                            st.session_state.mrp_results = st.session_state.mrp_instance.mrp_dfs
                            st.session_state.pending_decisions = st.session_state.mrp_instance.pending_decisions
                            st.rerun()
        
        # Wyświetl rezultaty MRP dla każdego komponentu
        for component, mrp_df in st.session_state.mrp_results.items():
            st.subheader(f"Plan MRP dla komponentu: {component}")

            # Replace NaN with empty string and 0 with empty string for display
            display_df = mrp_df.copy()

            # Zamień kody na czytelne komunikaty i usuń zera
            for col in display_df.columns:
                for idx in display_df.index:
                    value = display_df.at[idx, col]
                    # Jeśli wartość to -1, oznacza to potrzebę decyzji
                    if value == -1:
                        # Znajdź odpowiednią decyzję w pending_decisions
                        for decision in st.session_state.pending_decisions:
                            if decision['component'] == component and decision['week'] == col:
                                display_df.at[idx, col] = f"Need decision ({decision['net_requirement']})"
                                break
                    elif pd.isna(value):
                        display_df.at[idx, col] = ""  # Pusta komórka zamiast None
                    elif value == 0:
                        display_df.at[idx, col] = ""  # Pusta komórka zamiast zera
                    elif isinstance(value, float) and value.is_integer():
                        display_df.at[idx, col] = int(value)  # Usuń .0 dla liczb całkowitych

            st.dataframe(display_df)

            # Przycisk do pobierania planu MRP jako CSV
            csv = mrp_df.to_csv(sep=';')
            st.download_button(
                label=f"Pobierz plan MRP dla {component} jako CSV",
                data=csv,
                file_name=f"mrp_plan_{component}.csv",
                mime="text/csv"
            )
    else:
        st.info("Uruchom algorytm MRP w zakładce 'Dane wejściowe', aby zobaczyć wyniki.")