from typing import Any

import pandas as pd
import src.mps as mps
import src.bom as bom

class Mrp:

    def __init__(self):
        self.mps = mps.Mps()
        self.bom = bom.Bom()
        self.mrp_dfs = {}

    def start_algorithm(self):
        self._process_first_level_components()
        self._process_second_level_components()


    def _process_first_level_components(self):
        bom_data = self.bom.bom_df
        mps_lead_time = 1
        first_lvl_comp_production_weeks = self.get_first_lvl_comp_prod_weeks()

        first_level_components = bom_data.query("parent_name == 'none'")

        for index, row in first_level_components.iterrows():
            component_name = row['component_name']
            component_lead_time = row['lead_time']
            component_in_stock = row['in_stock']
            component_batch_size = row['batch_size']
            component_mrp_df = self.generate_empty_mrp_df()

            for production_week, quantity in first_lvl_comp_production_weeks.items():
                gross_req_week = production_week - mps_lead_time

                if gross_req_week > 0:
                    component_mrp_df.at['Gross_Requirements', gross_req_week] = quantity

            for week in range(1,11):
                left_in_stock = component_in_stock - component_mrp_df.at['Gross_Requirements', week]
                if left_in_stock > 0:
                    component_mrp_df.at['On_hand', week] = left_in_stock
                    component_in_stock= left_in_stock
                else:
                    component_mrp_df.at['Net_Requirements', week] = left_in_stock * -1
                    planned_order_release_week = week - component_lead_time
                    if planned_order_release_week > 0:
                        component_mrp_df.at['Planned_orders_releases', planned_order_release_week] = component_batch_size
                        receipt_component_amount = component_batch_size
                        component_mrp_df.at['Planned_orders_receipts', week] = component_batch_size
                        left_in_stock = left_in_stock + receipt_component_amount
                        component_in_stock = left_in_stock
                        component_mrp_df.at['On_hand', week] = left_in_stock
                    else:
                        raise ValueError("UJEMNY TYDZIEŃ")


            self.mrp_dfs[component_name] = component_mrp_df
            print(component_mrp_df)
            print(component_name)

    def _process_second_level_components(self):
        bom_data = self.bom.bom_df

        second_level_components = bom_data.query("LVL == 2")

        for index, row in second_level_components.iterrows():
            component_name = row['component_name']
            parent_name = row['parent_name']
            component_lead_time = row['lead_time']
            component_in_stock = row['in_stock']
            component_batch_size = row['batch_size']
            component_quantity = row['quantity']

            component_mrp_df = self.generate_empty_mrp_df()

            parent_mrp_df = self.mrp_dfs.get(parent_name)

            if parent_mrp_df is None:
                print(f"Warning: No MRP data found for parent {parent_name}")
                continue

            for week in range(1, 11):
                parent_planned_releases = parent_mrp_df.at['Planned_orders_releases', week]

                if parent_planned_releases > 0:
                    gross_req = parent_planned_releases * component_quantity
                    component_mrp_df.at['Gross_Requirements', week] = gross_req

                    left_in_stock = component_in_stock - gross_req
                    if left_in_stock > 0:
                        component_mrp_df.at['On_hand', week] = left_in_stock
                        component_in_stock = left_in_stock
                    else:
                        component_mrp_df.at['Net_Requirements', week] = abs(left_in_stock)
                        planned_order_release_week = week - component_lead_time

                        if planned_order_release_week > 0:
                            component_mrp_df.at[
                                'Planned_orders_releases', planned_order_release_week] = component_batch_size
                            component_mrp_df.at['Planned_orders_receipts', week] = component_batch_size
                            left_in_stock = left_in_stock + component_batch_size
                            component_in_stock = left_in_stock
                            component_mrp_df.at['On_hand', week] = left_in_stock
                        else:
                            raise ValueError("Negative week detected")

            self.mrp_dfs[component_name] = component_mrp_df
            print(f"MRP for second-level component: {component_name}")
            print(component_mrp_df)

    def get_first_lvl_comp_prod_weeks(self) -> dict[int, Any]:
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




