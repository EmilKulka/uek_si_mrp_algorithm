from pathlib import Path
from src.data_handler import load_bom_structure
import streamlit as st
import pandas as pd
import numpy as np

class Bom:

    def __init__(self):
        self.bom_df = load_bom_structure(Path('data/input/bom_data.csv'))

    def visualize_bom(self):
        print(self.bom_df)