import pandas as pd

class Mps:
    def __init__(self, custom_mps_df=None, lead_time=None):
        if custom_mps_df is not None:
            self.mps_df = custom_mps_df
        else:
            data = {
                1: [0, 0, 2],
                2: [0, 0, 2],
                3: [0, 0, 2],
                4: [0, 0, 2],
                5: [20, 28, 10],
                6: [0, 0, 10],
                7: [40, 30, 0],
                8: [0, 0, 0],
                9: [0, 0, 0],
                10: [0, 0, 0],
            }
            index = ["Przewidywany popyt", "Produkcja", "Dostępne"]
            self.mps_df = pd.DataFrame(data, index=index)

        self.lead_time = lead_time if lead_time is not None else 1
    
    @classmethod
    def from_form_data(cls, forecast_demand, production, available, lead_time=1):
        schema = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
            8: 0,
            9: 0,
            10: 0,
        }
        df = pd.DataFrame(schema, index=['Przewidywany_popyt', 'Produkcja', 'Dostępne'])

        for week in range(1, 11):
            df.at['Przewidywany_popyt', week] = forecast_demand[week-1]
            df.at['Produkcja', week] = production[week-1]
            df.at['Dostępne', week] = available[week-1]
        
        return cls(df, lead_time)