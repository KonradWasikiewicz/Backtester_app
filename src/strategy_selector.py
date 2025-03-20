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
        self.ticker_combo = ttk.Combobox(ticker_frame,
                                       textvariable=self.ticker_var,
                                       values=sorted(self.available_tickers),
                                       state="readonly")
        self.ticker_combo.set(self.available_tickers[0])
        self.ticker_combo.pack(fill="x")

        # Przycisk zatwierdzenia
        ttk.Button(self.root, text="Zatwierdź",
                  command=self.on_submit).pack(pady=20)

        # Aktualizacja opisu przy zmianie strategii
        self.strategy_var.trace('w', self.update_description)
        self.update_description()

    def update_description(self, *args):
        strategy = self.strategy_var.get()
        self.desc_label.config(text=self.strategy_descriptions.get(strategy, ""))

    def get_strategy_parameters(self, strategy_name: str) -> Dict[str, Any]:
        param_window = tk.Toplevel(self.root)
        param_window.title("Parametry Strategii")
        param_window.geometry("400x300")

        params = {}
        entries = {}

        if strategy_name == "Moving Average Crossover":
            params = {
                "short_window": ("Krótka średnia", "20"),
                "long_window": ("Długa średnia", "50")
            }
        elif strategy_name == "RSI":
            params = {
                "period": ("Okres RSI", "14"),
                "overbought": ("Poziom wykupienia", "70"),
                "oversold": ("Poziom wyprzedania", "30")
            }
        elif strategy_name == "Bollinger Bands":
            params = {
                "window": ("Okres", "20"),
                "num_std": ("Liczba odchyleń std.", "2.0")
            }

        for i, (key, (label, default)) in enumerate(params.items()):
            frame = ttk.Frame(param_window)
            frame.pack(fill="x", padx=5, pady=5)
            ttk.Label(frame, text=label).pack(side="left", padx=5)
            entry = ttk.Entry(frame)
            entry.insert(0, default)
            entry.pack(side="right", padx=5)
            entries[key] = entry

        result = {}

        def on_submit():
            for key, entry in entries.items():
                val = entry.get().strip()
                if val:  # jeśli pole nie jest puste
                    try:
                        # konwersja na odpowiedni typ
                        if key in ["num_std"]:
                            result[key] = float(val)
                        else:
                            result[key] = int(val)
                    except ValueError:
                        # jeśli konwersja się nie powiedzie, użyj wartości domyślnej
                        result[key] = float(params[key][1]) if key in ["num_std"] else int(params[key][1])
                else:
                    # użyj wartości domyślnej jeśli pole jest puste
                    result[key] = float(params[key][1]) if key in ["num_std"] else int(params[key][1])
            param_window.destroy()

        ttk.Button(param_window, text="OK", command=on_submit).pack(pady=20)

        param_window.wait_window()
        return result

    def on_submit(self):
        strategy = self.strategy_var.get()
        ticker = self.ticker_var.get()

        if not ticker:
            messagebox.showerror("Błąd", "Wybierz ticker!")
            return

        params = self.get_strategy_parameters(strategy)
        self.result = (strategy, ticker, params)
        self.root.quit()

    def get_selection(self) -> Tuple[str, str]:
        self.root.mainloop()
        self.root.destroy()
        return self.result
