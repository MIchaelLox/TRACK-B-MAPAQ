# ===========================================
# File: data_cleaner.py
# Purpose: Clean and preprocess dataset
# ===========================================


class DataCleaner:
def __init__(self, raw_data):
# Accept raw dataset (pandas DataFrame)
self.raw_data = raw_data


def remove_nulls(self):
"""
Drop rows/columns with null values.
"""
pass


def unify_formats(self):
"""
Standardize column names, dates, numeric types.
"""
pass


def encode_categoricals(self):
"""
Encode categorical variables into numeric format.
"""
pass


def get_clean_data(self):
"""
Return cleaned dataset.
"""
pass
