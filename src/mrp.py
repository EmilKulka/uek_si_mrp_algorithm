from typing import Any

import pandas as pd
import src.mps as mps
import src.bom as bom

class Mrp:

    def __init__(self):
        self.mps = mps.Mps()
        self.bom = bom.Bom()
        self.mrp_dfs = {}

    #TODO: access csv's via data_handler, de-hardcode mps_lead_time somehow
    def start_algorithm(self):
        bom_data = self.bom.bom_df
        mps_lead_time = 1
        production_weeks = self.get_production_weeks()

        first_level_components = bom_data.query("parent_name == 'none'")

        for index, row in first_level_components.iterrows():
            component_name = row['component_name']
            component_lead_time = row['lead_time']
            component_in_stock = row['in_stock']
            component_batch_size = row['batch_size']
            component_mrp_df = self.generate_empty_mrp_df()

            for production_week, quantity in production_weeks.items():
                gross_req_week = production_week - mps_lead_time

                if gross_req_week > 0:
                    component_mrp_df.at['Gross_Requirements', gross_req_week] = quantity

            self.mrp_dfs[component_name] = component_mrp_df
            print(component_mrp_df)
            print(component_name)

        # print(component_mrp_df)
        # print(component_name)




    def get_production_weeks(self) -> dict[int, Any]:
        mps_production_row = self.mps.mps_df.loc['Produkcja']
        production_weeks = {}

        for week in range(1, 10):
            if mps_production_row[week] > 0:
                production_weeks[week + 1] = mps_production_row[week]

        return production_weeks
    @staticmethod
    def generate_empty_mrp_df() -> pd.DataFrame:
        row_indexes = [
            "Gross_Requirements",
            "Scheduled_receipts",
            "On_hand",
            "Net_Requirements",
            "Planned_orders_releases",
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




