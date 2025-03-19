import pandas as pd
import pathlib

def load_bom_structure(bom_csv_path: pathlib.Path ) -> pd.DataFrame:
    if not bom_csv_path.exists():
        raise FileNotFoundError(f'File {bom_csv_path} does not exist')
    return pd.read_csv(bom_csv_path, index_col=0, sep=";")

def load_mps_structure(mps_csv_path: pathlib.Path ) -> pd.DataFrame:
    if not mps_csv_path.exists():
        raise FileNotFoundError(f'File {mps_csv_path} does not exist')
    return pd.read_csv(mps_csv_path, index_col=0, sep=";")
