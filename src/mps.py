from pathlib import Path
from src.data_handler import load_mps_structure

class Mps:

    def __init__(self):
        self.mps_df = load_mps_structure(Path('data/input/mps_data.csv'))

    def visualize_bom(self):
        print(self.mps_df)
