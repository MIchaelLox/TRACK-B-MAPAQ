# ===========================================
# File: model_baseline.py
# Purpose: Train baseline probability model
# ===========================================


class BaselineModel:
def __init__(self, clean_data):
self.clean_data = clean_data
self.model = None


def train_logistic_regression(self):
"""
Train logistic regression model on cleaned dataset.
Save model in self.model.
"""
pass


def train_naive_bayes(self):
"""
Train Naïve Bayes classifier on cleaned dataset.
Save model in self.model.
"""
pass


def evaluate_model(self):
"""
Evaluate trained model using accuracy, precision, recall, F1-score.
"""
pass
