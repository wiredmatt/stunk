"""Utility functions for the application."""
import numpy as np
import pandas as pd


def convert_numpy_types(obj):
    """Convert numpy types to Python native types."""
    if isinstance(obj, (np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.datetime64):
        return pd.Timestamp(obj).to_pydatetime()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, pd.Series):
        return convert_numpy_types(obj.to_dict())
    elif isinstance(obj, pd.DataFrame):
        return {col: convert_numpy_types(obj[col]) for col in obj.columns}
    return obj
