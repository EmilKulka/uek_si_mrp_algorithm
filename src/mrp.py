from typing import Any, Tuple, Dict

import pandas as pd
import src.mps as mps
import src.bom as bom

class Mrp:
    def __init__(self, custom_mps=None, lead_time=None):
        if custom_mps is not None:
            self.mps = custom_mps
        else:
            self.mps = mps.Mps(lead_time=lead_time)
        
        self.bom = bom.Bom()
        self.mrp_dfs = {}
        self.interactive_mode = False
        self.pending_decisions = []
        self.component_params = {}

    def start_algorithm(self, interactive=False):
        self.interactive_mode = interactive
        self.pending_decisions = []
        
        self._process_first_level_components()
        self._process_second_level_components()
        
        return self.mrp_dfs, self.pending_decisions

    def _process_first_level_components(self):
        bom_data = self.bom.bom_df
        mps_lead_time = self.mps.lead_time
        first_lvl_comp_production_weeks = self.get_first_lvl_comp_prod_weeks()

        first_level_components = bom_data.query("LVL == 1")

        for index, row in first_level_components.iterrows():
            component_name = row['component_name']
            component_lead_time = row['lead_time']
            component_in_stock = row['in_stock']
            component_batch_size = row['batch_size']

            self.component_params[component_name] = {
                'lead_time': component_lead_time,
                'batch_size': component_batch_size
            }
            
            component_mrp_df = self.generate_empty_mrp_df()

            for production_week, quantity in first_lvl_comp_production_weeks.items():
                gross_req_week = production_week - mps_lead_time

                if gross_req_week > 0:
                    component_mrp_df.at['Gross_Requirements', gross_req_week] = quantity

            for week in range(1, 11):
                component_in_stock = self._process_weekly_requirements(
                    component_mrp_df, week, component_in_stock, 
                    component_lead_time, component_batch_size, component_name
                )

            self.mrp_dfs[component_name] = component_mrp_df

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

            self.component_params[component_name] = {
                'lead_time': component_lead_time,
                'batch_size': component_batch_size
            }

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

                component_in_stock = self._process_weekly_requirements(
                    component_mrp_df, week, component_in_stock, 
                    component_lead_time, component_batch_size, component_name
                )

            self.mrp_dfs[component_name] = component_mrp_df

    def _process_weekly_requirements(self, mrp_df, week, in_stock, lead_time, batch_size, component_name):
        gross_req = mrp_df.at['Gross_Requirements', week]
        if pd.isna(gross_req):
            gross_req = 0

        sched_receipts = mrp_df.at['Scheduled_receipts', week]
        if pd.isna(sched_receipts):
            sched_receipts = 0

        left_in_stock = in_stock - gross_req + sched_receipts

        if left_in_stock >= 0:
            mrp_df.at['On_hand', week] = left_in_stock
            return left_in_stock
        else:
            net_req = abs(left_in_stock)
            mrp_df.at['Net_Requirements', week] = net_req

            planned_order_release_week = week - lead_time

            if planned_order_release_week <= 0:
                if self.interactive_mode:
                    self.pending_decisions.append({
                        'component': component_name,
                        'week': week,
                        'lead_time': lead_time,
                        'batch_size': batch_size,
                        'net_requirement': net_req,
                        'current_stock': in_stock
                    })
                    mrp_df.at['Planned_orders_receipts', week] = -1
                    left_in_stock = 0
                    return left_in_stock
                else:
                    mrp_df.at['Scheduled_receipts', week] = net_req
                    mrp_df.at['On_hand', week] = 0
                    return 0
            else:
                if batch_size > 0:
                    order_size = batch_size
                else:
                    order_size = net_req

                new_left_in_stock = left_in_stock + order_size

                if new_left_in_stock >= 0:
                    mrp_df.at['Planned_orders_releases', planned_order_release_week] = order_size
                    mrp_df.at['Planned_orders_receipts', week] = order_size
                    mrp_df.at['On_hand', week] = new_left_in_stock
                    return new_left_in_stock
                else:
                    if self.interactive_mode:
                        self.pending_decisions.append({
                            'component': component_name,
                            'week': week,
                            'lead_time': lead_time,
                            'batch_size': batch_size,
                            'net_requirement': net_req,
                            'current_stock': in_stock
                        })
                        mrp_df.at['Planned_orders_receipts', week] = -1
                        mrp_df.at['Planned_orders_releases', planned_order_release_week] = order_size
                        left_in_stock = left_in_stock + order_size

                        return left_in_stock
                    else:
                        mrp_df.at['Planned_orders_releases', planned_order_release_week] = order_size
                        mrp_df.at['Planned_orders_receipts', week] = order_size
                        mrp_df.at['On_hand', week] = new_left_in_stock
                        return new_left_in_stock

    def apply_user_decision(self, component_name, week, receipt_quantity):
        if component_name not in self.mrp_dfs:
            raise ValueError(f"Component {component_name} not found in MRP data")
            
        mrp_df = self.mrp_dfs[component_name]

        decision_index = None
        for i, decision in enumerate(self.pending_decisions):
            if decision['component'] == component_name and decision['week'] == week:
                decision_index = i
                break
                
        if decision_index is not None:
            decision = self.pending_decisions[decision_index]

            component_params = self.component_params.get(component_name, {})
            lead_time = component_params.get('lead_time', 1)
            batch_size = component_params.get('batch_size', 0)

            mrp_df.at['Scheduled_receipts', week] = receipt_quantity

            in_stock = decision['current_stock']
            gross_req = mrp_df.at['Gross_Requirements', week] if not pd.isna(mrp_df.at['Gross_Requirements', week]) else 0
            
            left_in_stock = in_stock - gross_req + receipt_quantity
            mrp_df.at['On_hand', week] = left_in_stock

            mrp_df.at['Planned_orders_receipts', week] = None

            self.pending_decisions.pop(decision_index)

            for next_week in range(week + 1, 11):
                gross_req = mrp_df.at['Gross_Requirements', next_week] 
                if pd.isna(gross_req):
                    gross_req = 0

                sched_receipts = mrp_df.at['Scheduled_receipts', next_week]
                if pd.isna(sched_receipts):
                    sched_receipts = 0

                left_in_stock = left_in_stock - gross_req + sched_receipts
                
                if left_in_stock >= 0:
                    mrp_df.at['On_hand', next_week] = left_in_stock
                    mrp_df.at['Net_Requirements', next_week] = 0
                    mrp_df.at['Planned_orders_receipts', next_week] = None
                else:
                    net_req = abs(left_in_stock)
                    mrp_df.at['Net_Requirements', next_week] = net_req
                    
                    planned_order_release_week = next_week - lead_time
                    
                    if planned_order_release_week > 0:
                        order_size = max(batch_size, net_req) if batch_size > 0 else net_req
                        if batch_size > 0:
                            order_size = batch_size
                        
                        mrp_df.at['Planned_orders_releases', planned_order_release_week] = order_size
                        mrp_df.at['Planned_orders_receipts', next_week] = order_size

                        left_in_stock = left_in_stock + order_size
                        mrp_df.at['On_hand', next_week] = left_in_stock
                    else:
                        self.pending_decisions.append({
                            'component': component_name,
                            'week': next_week,
                            'lead_time': lead_time,
                            'batch_size': batch_size,
                            'net_requirement': net_req,
                            'current_stock': left_in_stock + gross_req
                        })
                        mrp_df.at['Planned_orders_receipts', next_week] = f"Need decision ({net_req})"
                        left_in_stock = 0
            
            return True
        
        return False

    def get_first_lvl_comp_prod_weeks(self) -> dict[int, Any]:
        mps_production_row = self.mps.mps_df.loc['Produkcja']
        production_weeks = {}

        for week in range(1, 11):
            if mps_production_row[week] > 0:
                production_weeks[week] = mps_production_row[week]

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
        df = pd.DataFrame(schema, index=row_indexes)
        return df.astype('object')