import pandas as pd
import src.mps as mps
import src.bom as bom

class Mrp:

    def __init__(self):
        self.mps = mps.Mps()
        self.bom = bom.Bom()
        self.mrp_dfs = {}

    def start_algorithm(self):
        bom_data = self.bom.bom_df
        mps_data = self.mps.mps_df

        first_level_components = bom_data.query("parent_name == 'none'")

        for index, row in first_level_components.iterrows():
            component_name = row['component_name']
            component_mrp_df = self.generate_empty_mrp_df()
            
            print(component_name)


        print(first_level_components)


    @staticmethod
    def generate_empty_mrp_df() -> pd.DataFrame:
        row_indexes = [
            "Gross_Requirements",
            "On_hand",
            "Net_Requirements",
            "Scheduled_receipts",
            "Planned_orders_releases"
            "Planned_orders_receipts"
        ]
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
        return pd.DataFrame(schema, index=row_indexes)




