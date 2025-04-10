import pandas as pd

class Bom:
    def __init__(self):
        data = {
            "LVL": [1, 1, 1, 2, 2, 2, 2],
            "component_name": ["Podstawka", "Ramie", "Klosz", "Przycisk", "Kabel", "Śruba", "Żarówka"],
            "parent_name": ["none", "none", "none", "Podstawka", "Podstawka", "Ramie", "Klosz"],
            "quantity": [1, 1, 1, 1, 1, 2, 1],
            "lead_time": [3, 2, 3, 2, 2, 2, 2],
            "in_stock": [22, 40, 50, 25, 40, 120, 100],
            "batch_size": [40, 120, 10, 120, 15, 200, 50]
        }
        self.bom_df = pd.DataFrame(data)

    def visualize_bom(self):
        print(self.bom_df)