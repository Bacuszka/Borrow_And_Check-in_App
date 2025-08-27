import streamlit as st
import pandas as pd
from datetime import datetime, date
from babel.dates import format_date
import json
import os

# Komentarz: Usunięto import i konfigurację 'locale',
# ponieważ babel.dates.format_date ma wbudowane wsparcie dla języków.

# --- Konfiguracja strony i danych ---
st.set_page_config(
    page_title="Borrow And Check-in App",
    page_icon="🎲",
    layout="wide"
)

# Ścieżki do plików z danymi
GAMES_FILE = 'games.json'
CLIENTS_FILE = 'clients.json'
RENTALS_FILE = 'rentals.json'
HISTORY_FILE = 'history.json'

# --- Funkcje do obsługi plików JSON ---
def load_data(file_path, default_data):
    """Ładuje dane z pliku JSON. Jeśli plik nie istnieje lub jest uszkodzony, tworzy go z domyślnymi danymi."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Błąd odczytu pliku {file_path}. Plik jest uszkodzony. Zostanie utworzony nowy, pusty plik.")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            return default_data
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data

def save_data(file_path, data_list):
    """Zapisuje dane do pliku JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

# Inicjalizacja danych w sesji
if 'games_data' not in st.session_state:
    st.session_state.games_data = load_data(GAMES_FILE, [])

if 'clients_data' not in st.session_state:
    st.session_state.clients_data = load_data(CLIENTS_FILE, [])

if 'rentals_data' not in st.session_state:
    st.session_state.rentals_data = load_data(RENTALS_FILE, [])

if 'history_data' not in st.session_state:
    st.session_state.history_data = load_data(HISTORY_FILE, [])

# Konwersja danych z JSON na DataFrame dla łatwiejszego wyświetlania
st.session_state.games = pd.DataFrame(st.session_state.games_data)
st.session_state.clients = pd.DataFrame(st.session_state.clients_data)

# --- Nagłówek i aktualna data/godzina ---
st.title("Borrow And Check-in App")
st.markdown("---")

current_date = datetime.now()
# Zmieniono formatowanie daty, aby jawnie używać polskiej lokalizacji
st.sidebar.markdown(f"**Dzisiaj jest:** {format_date(current_date, format='full', locale='pl_PL')}")
st.sidebar.markdown(f"**Aktualna godzina:** {current_date.strftime('%H:%M:%S')}")

# Dodany stały tekst w menu bocznym, zgodnie z prośbą
st.sidebar.markdown(
    '<span style="font-size: 20px; color: red;">KOD DO WYPOZYCZENIA W SUBIEKCIE 000301</span>', 
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# --- Menu boczne ---
st.sidebar.header("Menu Główne")
menu_selection = st.sidebar.radio(
    "Wybierz opcję:",
    ["Wypożyczenie gry", "Zwrot gry", "Zarządzanie grami", "Zarządzanie klientami", "Historia"]
)

# --- Główna sekcja aplikacji w zależności od wyboru z menu ---

if menu_selection == "Wypożyczenie gry":
    st.header("Wypożyczenie gry")

    # Wybór klienta z listy
    st.subheader("Wybierz klienta")
    
    # Zabezpieczenie przed błędem, gdy lista klientów jest pusta
    if not st.session_state.clients.empty:
        clients_list = st.session_state.clients.apply(lambda row: f"{row['Imię']} {row['Nazwisko']} ({row['Telefon']})", axis=1).tolist()
    else:
        clients_list = []
    
    if not clients_list:
        st.warning("Brak zarejestrowanych klientów. Dodaj klienta w sekcji 'Zarządzanie klientami'.")
        selected_client_full_name = None
    else:
        selected_client_full_name = st.selectbox("Wybierz klienta", clients_list)

    # Wybór gry
    st.subheader("Wybór gry")
    available_games = st.session_state.games[st.session_state.games['Dostępna'] == True]['Nazwa Gry'].tolist()
    
    if not available_games:
        st.warning("Brak dostępnych gier do wypożyczenia.")
        selected_game = None
    else:
        selected_game = st.selectbox("Wybierz grę", available_games)
    
    # Daty wypożyczenia
    if selected_game and selected_client_full_name:
        st.subheader("Okres wypożyczenia")
        start_date = st.date_input("Data wypożyczenia (od)")
        end_date = st.date_input("Data zwrotu (do)")
        
        # Obliczenie kosztów
        if start_date and end_date:
            delta = end_date - start_date
            rental_days = max(1, delta.days)
            
            st.subheader("Koszty wypożyczenia")
            st.write(f"Wyliczony okres wypożyczenia: **{rental_days} dni**")
            
            edited_days = st.number_input("Edytuj liczbę dni", min_value=1, value=rental_days, key="new_rental_days")
            cost_per_day = st.number_input("Cena za dzień", min_value=1, value=5, key="new_rental_cost")
            
            total_cost = edited_days * cost_per_day

            st.markdown(f"**Całkowity koszt: {total_cost} zł**")

        if st.button("Zarejestruj wypożyczenie"):
            if not all([selected_client_full_name, selected_game, start_date, end_date]):
                st.error("Wybierz klienta, grę i daty!")
            else:
                new_rental = {
                    'Klient': selected_client_full_name,
                    'Tytuł Gry': selected_game,
                    'Od': start_date.isoformat(),
                    'Do': end_date.isoformat(),
                    'Koszt': total_cost,
                    'Cena za dzień': cost_per_day # Nowy atrybut
                }
                st.session_state.rentals_data.append(new_rental)
                save_data(RENTALS_FILE, st.session_state.rentals_data)
                
                # Zmiana statusu dostępności gry
                for game in st.session_state.games_data:
                    if game['Nazwa Gry'] == selected_game:
                        game['Dostępna'] = False
                        break
                save_data(GAMES_FILE, st.session_state.games_data)
                
                # Zapisanie do historii
                new_history_entry = {
                    'Data': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Typ zdarzenia': 'Wypożyczenie',
                    'Tytuł Gry': selected_game,
                    'Klient': selected_client_full_name,
                    'Koszt': total_cost,
                    'Opłata za zwłokę': 0, # W momencie wypożyczenia opłata za zwłokę to 0
                    'Suma': total_cost # Dodana kolumna Suma
                }
                st.session_state.history_data.append(new_history_entry)
                save_data(HISTORY_FILE, st.session_state.history_data)
                
                # Zaktualizowanie DataFrame z grami
                st.session_state.games = pd.DataFrame(st.session_state.games_data)
                st.success("Wypożyczenie zarejestrowane pomyślnie!")

elif menu_selection == "Zwrot gry":
    st.header("Zwrot gry")
    
    # Nowa, bezpieczniejsza logika filtrowania
    unavailable_games_titles = {game['Nazwa Gry'] for game in st.session_state.games_data if not game.get('Dostępna', True)}
    
    rented_games = [
        rental for rental in st.session_state.rentals_data
        if rental.get('Tytuł Gry') in unavailable_games_titles
    ]
    
    if rented_games:
        st.subheader("Aktualne wypożyczenia")
        
        # Tworzenie DataFrame dla lepszego widoku
        df_rented_games = pd.DataFrame(rented_games)
        df_rented_games['Od'] = pd.to_datetime(df_rented_games['Od']).dt.date
        df_rented_games['Do'] = pd.to_datetime(df_rented_games['Do']).dt.date
        st.dataframe(df_rented_games)
        
        st.markdown("---")
        st.subheader("Zaznacz grę do zwrotu")
        
        rental_to_return_idx = st.selectbox(
            "Wybierz wypożyczenie:",
            options=range(len(rented_games)),
            format_func=lambda idx: f"{rented_games[idx]['Tytuł Gry']} - {rented_games[idx]['Klient']}"
        )

        rental_to_return = rented_games[rental_to_return_idx]
        game_title = rental_to_return['Tytuł Gry']
        client_name = rental_to_return['Klient']
        declared_end_date = datetime.strptime(rental_to_return['Do'], '%Y-%m-%d').date()
        daily_cost = rental_to_return.get('Cena za dzień', 5) # Pobranie ceny za dzień, z domyślną wartością 5
        
        st.markdown("---")
        st.subheader("Rozliczenie zwłoki")
        
        late_fee_method = st.radio(
            "Jak chcesz określić zwłokę?",
            ["Ręcznie wpisz dni", "Wybierz datę z kalendarza"],
            key="late_fee_method"
        )
        
        days_late = 0
        
        if late_fee_method == "Ręcznie wpisz dni":
            days_late = st.number_input("Ile dni klient oddał grę po czasie?", min_value=0, value=0, step=1, key="manual_days_late")
        else:
            return_date = st.date_input("Wybierz datę zwrotu", value=date.today(), key="calendar_return_date")
            if return_date > declared_end_date:
                days_late = (return_date - declared_end_date).days
            else:
                days_late = 0

        late_fee = days_late * daily_cost

        st.markdown(f"**Opłata za zwłokę: {late_fee} zł** (dni zwłoki: {days_late}, cena za dzień: {daily_cost} zł)")
        
        # Obliczenie całkowitego kosztu dla historii
        original_cost = rental_to_return.get('Koszt', 0)
        final_cost = original_cost + late_fee
        st.markdown(f"**Całkowity koszt dla klienta: {final_cost} zł** (wypożyczenie: {original_cost} zł + zwłoka: {late_fee} zł)")
        
        if st.button("Zwróć zaznaczoną grę"):
            # Usunięcie z listy wypożyczeń
            st.session_state.rentals_data.remove(rental_to_return)
            save_data(RENTALS_FILE, st.session_state.rentals_data)

            # Zmiana statusu gry na dostępną
            for game in st.session_state.games_data:
                if game['Nazwa Gry'] == game_title:
                    game['Dostępna'] = True
                    break
            save_data(GAMES_FILE, st.session_state.games_data)
            
            # Zapisanie do historii
            new_history_entry = {
                'Data': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Typ zdarzenia': 'Zwrot',
                'Tytuł Gry': game_title,
                'Klient': client_name,
                'Koszt': original_cost,
                'Opłata za zwłokę': late_fee, # Dodana kolumna z opłatą za zwłokę
                'Suma': final_cost # Dodana kolumna Suma
            }
            st.session_state.history_data.append(new_history_entry)
            save_data(HISTORY_FILE, st.session_state.history_data)

            # Zmieniony komunikat - wyświetla tylko opłatę za zwłokę
            st.success(f"Gra '{game_title}' została zwrócona pomyślnie! Kwota do dopłaty: {late_fee} zł.")
    else:
        st.info("Obecnie nie ma żadnych wypożyczonych gier.")

elif menu_selection == "Zarządzanie grami":
    st.header("Zarządzanie grami")
    
    st.subheader("Lista gier")
    
    # Dodanie pola wyszukiwania
    search_query = st.text_input("Wyszukaj po tytule...", key="game_search")

    if not st.session_state.games.empty:
        games_with_status = st.session_state.games.copy()
        
        if search_query:
            games_with_status = games_with_status[games_with_status['Nazwa Gry'].str.contains(search_query, case=False, na=False)]

        games_with_status['Status'] = games_with_status['Dostępna'].apply(lambda x: "Dostępna" if x else "Wypożyczona")

        df_to_display = games_with_status[['Nazwa Gry', 'Status']]

        def color_status_text(s):
            return ['color: #4CAF50' if 'Dostępna' in v else 'color: #f44336' for v in s]

        st.dataframe(
            df_to_display.style.apply(color_status_text, subset=['Status']),
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Brak gier na liście. Dodaj nową grę, aby rozpocząć.")

    st.markdown("---")
    st.subheader("Dodaj nową grę")
    new_game_name = st.text_input("Nazwa nowej gry")
    
    if st.button("Dodaj grę"):
        if new_game_name:
            if any(game['Nazwa Gry'] == new_game_name for game in st.session_state.games_data):
                st.warning("Gra o tej nazwie już istnieje.")
            else:
                st.session_state.games_data.append({'Nazwa Gry': new_game_name, 'Dostępna': True})
                save_data(GAMES_FILE, st.session_state.games_data)
                st.session_state.games = pd.DataFrame(st.session_state.games_data)
                st.success(f"Gra '{new_game_name}' została dodana!")
        else:
            st.warning("Wpisz nazwę gry, aby ją dodać.")
            
    st.markdown("---")
    st.subheader("Edytuj grę")
    games_to_edit = [game['Nazwa Gry'] for game in st.session_state.games_data]
    if games_to_edit:
        selected_game_edit = st.selectbox("Wybierz grę do edycji", games_to_edit)
        new_game_name_edit = st.text_input("Nowa nazwa", value=selected_game_edit)
        
        if st.button("Zapisz zmiany"):
            if new_game_name_edit:
                for game in st.session_state.games_data:
                    if game['Nazwa Gry'] == selected_game_edit:
                        game['Nazwa Gry'] = new_game_name_edit
                        break
                save_data(GAMES_FILE, st.session_state.games_data)
                st.session_state.games = pd.DataFrame(st.session_state.games_data)
                st.success(f"Gra '{selected_game_edit}' zmieniona na '{new_game_name_edit}'!")
            else:
                st.warning("Nowa nazwa nie może być pusta.")

    st.markdown("---")
    st.subheader("Usuń grę")
    games_to_delete = [game['Nazwa Gry'] for game in st.session_state.games_data]
    if games_to_delete:
        selected_game_delete = st.selectbox("Wybierz grę do usunięcia", games_to_delete, key="delete_game_select")
        
        # Flaga do potwierdzenia usunięcia gry
        if 'confirm_delete_game' not in st.session_state:
            st.session_state.confirm_delete_game = False

        if st.button("Usuń grę"):
            st.session_state.confirm_delete_game = True

        if st.session_state.confirm_delete_game:
            st.warning(f"Czy na pewno chcesz usunąć '{selected_game_delete}'? Tej operacji nie można cofnąć.")
            if st.button("Tak, na pewno chcę usunąć"):
                st.session_state.games_data = [game for game in st.session_state.games_data if game['Nazwa Gry'] != selected_game_delete]
                save_data(GAMES_FILE, st.session_state.games_data)
                st.session_state.games = pd.DataFrame(st.session_state.games_data)
                st.success(f"Gra '{selected_game_delete}' została usunięta!")
                st.session_state.confirm_delete_game = False
                st.rerun()

elif menu_selection == "Zarządzanie klientami":
    st.header("Zarządzanie klientami")
    
    st.subheader("Lista klientów")
    
    if not st.session_state.clients.empty:
        st.dataframe(st.session_state.clients, use_container_width=True, hide_index=True)
    else:
        st.info("Brak klientów na liście.")
        
    st.markdown("---")
    st.subheader("Dodaj nowego klienta")
    new_client_first_name = st.text_input("Imię klienta")
    new_client_last_name = st.text_input("Nazwisko klienta")
    new_client_phone = st.text_input("Numer telefonu")
    
    if st.button("Dodaj klienta"):
        if new_client_first_name and new_client_last_name and new_client_phone:
            st.session_state.clients_data.append({
                'Imię': new_client_first_name,
                'Nazwisko': new_client_last_name,
                'Telefon': new_client_phone
            })
            save_data(CLIENTS_FILE, st.session_state.clients_data)
            st.session_state.clients = pd.DataFrame(st.session_state.clients_data)
            st.success(f"Klient {new_client_first_name} {new_client_last_name} został dodany!")
        else:
            st.warning("Wypełnij wszystkie pola, aby dodać klienta.")
            
    st.markdown("---")
    st.subheader("Edytuj klienta")
    if not st.session_state.clients.empty:
        clients_to_edit = [f"{client['Imię']} {client['Nazwisko']}" for client in st.session_state.clients_data]
        selected_client_edit_name = st.selectbox("Wybierz klienta do edycji", clients_to_edit)
        
        selected_client_data = next((c for c in st.session_state.clients_data if f"{c['Imię']} {c['Nazwisko']}" == selected_client_edit_name), None)
        
        if selected_client_data:
            new_first_name_edit = st.text_input("Nowe imię", value=selected_client_data['Imię'])
            new_last_name_edit = st.text_input("Nowe nazwisko", value=selected_client_data['Nazwisko'])
            new_phone_edit = st.text_input("Nowy numer telefonu", value=selected_client_data['Telefon'])
            
            if st.button("Zapisz zmiany w kliencie"):
                if new_first_name_edit and new_last_name_edit and new_phone_edit:
                    for i, client in enumerate(st.session_state.clients_data):
                        if f"{client['Imię']} {client['Nazwisko']}" == selected_client_edit_name:
                            st.session_state.clients_data[i]['Imię'] = new_first_name_edit
                            st.session_state.clients_data[i]['Nazwisko'] = new_last_name_edit
                            st.session_state.clients_data[i]['Telefon'] = new_phone_edit
                            break
                    save_data(CLIENTS_FILE, st.session_state.clients_data)
                    st.session_state.clients = pd.DataFrame(st.session_state.clients_data)
                    st.success(f"Dane klienta {selected_client_edit_name} zostały zaktualizowane!")
                else:
                    st.warning("Wypełnij wszystkie pola, aby edytować klienta.")

    st.markdown("---")
    st.subheader("Usuń klienta")
    if not st.session_state.clients.empty:
        clients_to_delete = [f"{client['Imię']} {client['Nazwisko']}" for client in st.session_state.clients_data]
        selected_client_delete = st.selectbox("Wybierz klienta do usunięcia", clients_to_delete, key="delete_client_select")
        
        # Flaga do potwierdzenia usunięcia klienta
        if 'confirm_delete_client' not in st.session_state:
            st.session_state.confirm_delete_client = False

        if st.button("Usuń klienta"):
            st.session_state.confirm_delete_client = True
        
        if st.session_state.confirm_delete_client:
            st.warning(f"Czy na pewno chcesz usunąć '{selected_client_delete}'? Tej operacji nie można cofnąć.")
            if st.button("Tak, na pewno chcę usunąć"):
                st.session_state.clients_data = [c for c in st.session_state.clients_data if f"{c['Imię']} {c['Nazwisko']}" != selected_client_delete]
                save_data(CLIENTS_FILE, st.session_state.clients_data)
                st.session_state.clients = pd.DataFrame(st.session_state.clients_data)
                st.success(f"Klient {selected_client_delete} został usunięty!")
                st.session_state.confirm_delete_client = False
                st.rerun()


elif menu_selection == "Historia":
    st.header("Historia wypożyczeń i zwrotów")
    
    if st.session_state.history_data:
        history_df = pd.DataFrame(st.session_state.history_data)
        
        if 'Data' in history_df.columns:
            history_df['Data'] = pd.to_datetime(history_df['Data'])
        
        # Funkcja do kolorowania komórek w kolumnie 'Typ zdarzenia'
        def color_event_cell(val):
            if val == 'Wypożyczenie':
                return 'color: #3182CE; font-weight: bold'
            elif val == 'Zwrot':
                return 'color: #ED8936; font-weight: bold'
            return ''
        
        # Zmodyfikowane formatowanie, aby nie wyświetlać miejsc po przecinku
        styled_history = history_df.style.applymap(
            color_event_cell, 
            subset=['Typ zdarzenia']
        ).format({
            'Koszt': '{:.0f}',
            'Opłata za zwłokę': '{:.0f}',
            'Suma': '{:.0f}'
        })
        
        st.dataframe(
            styled_history,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Brak wpisów w historii.")
        
    st.markdown("---")
    if 'confirm_clear' not in st.session_state:
        st.session_state.confirm_clear = False
        
    if st.button("Wyczyść historię"):
        # Ustawienie flagi na True, co spowoduje pojawienie się drugiego przycisku
        st.session_state.confirm_clear = True
        st.warning("Czy na pewno chcesz wyczyścić całą historię? Tej operacji nie można cofnąć.")
        
    if st.session_state.confirm_clear:
        if st.button("Tak, wyczyść historię"):
            if st.session_state.history_data:
                st.session_state.history_data = []
                save_data(HISTORY_FILE, st.session_state.history_data)
                st.success("Historia została pomyślnie wyczyszczona.")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.info("Historia jest już pusta.")
                st.session_state.confirm_clear = False
