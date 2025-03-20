import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple, Any

class StrategySelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Backtester - Wybór Strategii")
        self.root.geometry("800x600")

        self.strategy_descriptions = {
            "Moving Average Crossover": """
            Strategia wykorzystuje przecięcia dwóch średnich kroczących:
            - Sygnał kupna: krótsza MA przebija dłuższą MA od dołu
            - Sygnał sprzedaży: krótsza MA przebija dłuższą MA od góry
            - Parametry: okres krótkiej MA (domyślnie 20), okres długiej MA (domyślnie 50)
            - Skuteczność: działa najlepiej w trendach, słabsza w konsolidacji
            """,
            "RSI": """
            Strategia bazuje na wskaźniku względnej siły (RSI):
            - Sygnał kupna: RSI poniżej poziomu wykupienia (domyślnie 30)
            - Sygnał sprzedaży: RSI powyżej poziomu wyprzedania (domyślnie 70)
            - Parametry: okres RSI (domyślnie 14), poziomy wykupienia/wyprzedania
            - Skuteczność: najlepsza w rynkach bez wyraźnego trendu
            """,
            "Bollinger Bands": """
            Strategia wykorzystuje wstęgi Bollingera:
            - Sygnał kupna: cena poniżej dolnej wstęgi
            - Sygnał sprzedaży: cena powyżej górnej wstęgi
            - Parametry: okres (domyślnie 20), liczba odchyleń std. (domyślnie 2.0)
            - Skuteczność: dobra w okresach zmienności, ryzyko w silnych trendach
            """
        }

        # Lista dostępnych tickerów
        self.available_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'TSLA']

        # Setup UI
        self.setup_ui()
        self.result = None

    def setup_ui(self):
        # Wybór strategii
        strategy_frame = ttk.LabelFrame(self.root, text="Wybór Strategii", padding=10)
        strategy_frame.pack(fill="x", padx=10, pady=5)

        self.strategy_var = tk.StringVar()
        for i, strategy in enumerate(self.strategy_descriptions.keys()):
            rb = ttk.Radiobutton(strategy_frame, text=strategy,
                               variable=self.strategy_var, value=strategy)
            rb.pack(anchor="w")
            if i == 0:
                rb.invoke()

        # Opis strategii
        desc_frame = ttk.LabelFrame(self.root, text="Opis Strategii", padding=10)
        desc_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.desc_label = ttk.Label(desc_frame, wraplength=750)
        self.desc_label.pack(fill="both", expand=True)

        # Wybór tickera
        ticker_frame = ttk.LabelFrame(self.root, text="Wybór Tickera", padding=10)
        ticker_frame.pack(fill="x", padx=10, pady=5)

        self.ticker_var = tk.StringVar()
                rb.invoke()  # Domyślnie wybrana pierwsza strategia

        # Opis strategii
        desc_frame = ttk.LabelFrame(self.strategy_tab, text="Opis Strategii", padding=10)
        desc_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.desc_label = ttk.Label(desc_frame, wraplength=550)
        self.desc_label.pack(fill="both", expand=True)

        # Aktualizacja opisu przy zmianie strategii
        self.strategy_var.trace('w', self.update_description)
        self.update_description()

    def setup_ticker_tab(self):
        # Dodanie opisu i filtrowania tickerów
        search_frame = ttk.LabelFrame(self.ticker_tab, text="Wyszukiwanie", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Filtruj tickery:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tickers)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True)

        # Lista tickerów
        self.ticker_listbox = tk.Listbox(self.ticker_tab, height=10)
        self.ticker_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        # Wypełnienie listy tickerów
        for ticker in sorted(self.available_tickers):
            self.ticker_listbox.insert(tk.END, ticker)

    def filter_tickers(self, *args):
        search_term = self.search_var.get().lower()
        self.ticker_listbox.delete(0, tk.END)
        for ticker in sorted(self.available_tickers):
            if search_term in ticker.lower():
                self.ticker_listbox.insert(tk.END, ticker)

    def get_strategy_parameters(self) -> Dict[str, Any]:
        # Dodatkowe okno do konfiguracji parametrów
        param_window = tk.Toplevel(self.root)
        param_window.title("Parametry Strategii")
        param_window.grab_set()

        # ...existing code for parameter configuration...

    def on_submit(self):
        if not self.ticker_listbox.curselection():
            tk.messagebox.showerror("Błąd", "Wybierz ticker!")
            return

        strategy = self.strategy_var.get()
        ticker = self.ticker_listbox.get(self.ticker_listbox.curselection())
        params = self.get_strategy_parameters()

        self.result = (strategy, ticker, params)
        self.root.quit()

    def get_selection(self) -> Tuple[str, str, Dict[str, Any]]:
        self.root.mainloop()
        self.root.destroy()
        return self.result
