"""
Baseline models for MAPAQ Track B - Restaurant risk prediction.

This module implements a lightweight baseline modelling layer using
only the Python standard library (plus pandas for data handling).

It provides:
- A simple logistic regression classifier implemented with gradient descent
- A Gaussian Naive Bayes classifier
- A BaselineModel façade that prepares the cleaned dataset, trains the
  models and computes standard evaluation metrics.

The goal is not state-of-the-art performance, but a clear, inspectable
reference implementation for the rest of the pipeline.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helper models
# ---------------------------------------------------------------------------


class LogisticRegressionBaseline:
    """Minimal logistic regression classifier using gradient descent."""

    def __init__(self, learning_rate: float = 0.1, max_iterations: int = 1000) -> None:
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.weights: Optional[List[float]] = None
        self.bias: float = 0.0
        self.cost_history: List[float] = []

    @staticmethod
    def _sigmoid(z: float) -> float:
        """Numerically-stable sigmoid."""
        if z < -500:
            z = -500
        elif z > 500:
            z = 500
        return 1.0 / (1.0 + math.exp(-z))

    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """Train logistic regression weights."""
        n_samples = len(X)
        if n_samples == 0:
            raise ValueError("Cannot train logistic regression on empty dataset.")
        n_features = len(X[0])
        self.weights = [0.0] * n_features
        self.bias = 0.0
        self.cost_history = []

        for it in range(self.max_iterations):
            grad_w = [0.0] * n_features
            grad_b = 0.0
            cost = 0.0

            for i in range(n_samples):
                xi = X[i]
                z = self.bias
                for j in range(n_features):
                    z += self.weights[j] * xi[j]
                y_hat = self._sigmoid(z)
                error = y_hat - y[i]

                for j in range(n_features):
                    grad_w[j] += error * xi[j]
                grad_b += error

                # logistic loss
                eps = 1e-15
                cost += -(
                    y[i] * math.log(max(y_hat, eps))
                    + (1 - y[i]) * math.log(max(1 - y_hat, eps))
                )

            cost /= n_samples
            self.cost_history.append(cost)

            # gradient descent update
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * grad_w[j] / n_samples
            self.bias -= self.learning_rate * grad_b / n_samples

            # simple early stopping
            if it > 0 and abs(self.cost_history[-2] - cost) < 1e-6:
                break

    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """Predict probability p(y=1|x) for each sample."""
        if self.weights is None:
            raise ValueError("Model not trained.")

        n_features = len(self.weights)
        probs: List[float] = []
        for xi in X:
            z = self.bias
            for j in range(min(n_features, len(xi))):
                z += self.weights[j] * xi[j]
            probs.append(self._sigmoid(z))
        return probs

    def predict(self, X: List[List[float]], threshold: float = 0.5) -> List[int]:
        """Predict class labels 0/1 for each sample."""
        return [1 if p >= threshold else 0 for p in self.predict_proba(X)]


class GaussianNaiveBayesBaseline:
    """Very small Gaussian Naive Bayes implementation."""

    def __init__(self) -> None:
        self.class_priors: Dict[int, float] = {}
        self.means: Dict[int, List[float]] = {}
        self.vars: Dict[int, List[float]] = {}

    def fit(self, X: List[List[float]], y: List[int]) -> None:
        if not X:
            raise ValueError("Cannot train Naive Bayes on empty dataset.")

        n_samples = len(X)
        n_features = len(X[0])

        # group samples by class
        class_samples: Dict[int, List[List[float]]] = {}
        for xi, yi in zip(X, y):
            class_samples.setdefault(int(yi), []).append(xi)

        for cls, samples in class_samples.items():
            self.class_priors[cls] = len(samples) / n_samples
            means: List[float] = []
            vars_: List[float] = []

            for j in range(n_features):
                col = [s[j] for s in samples]
                mean = sum(col) / len(col)
                var = sum((v - mean) ** 2 for v in col) / max(len(col) - 1, 1)
                if var == 0.0:
                    var = 1e-6
                means.append(mean)
                vars_.append(var)

            self.means[cls] = means
            self.vars[cls] = vars_

    @staticmethod
    def _gaussian_log_pdf(x: float, mean: float, var: float) -> float:
        return -0.5 * math.log(2 * math.pi * var) - ((x - mean) ** 2) / (2 * var)

    def _joint_log_likelihood(self, xi: List[float]) -> Dict[int, float]:
        if not self.class_priors:
            raise ValueError("Model not trained.")

        n_features = len(self.means[next(iter(self.means))])
        log_likelihoods: Dict[int, float] = {}

        for cls in self.class_priors:
            log_prob = math.log(self.class_priors[cls])
            means = self.means[cls]
            vars_ = self.vars[cls]
            for j in range(min(n_features, len(xi))):
                log_prob += self._gaussian_log_pdf(xi[j], means[j], vars_[j])
            log_likelihoods[cls] = log_prob

        return log_likelihoods

    def predict(self, X: List[List[float]]) -> List[int]:
        preds: List[int] = []
        for xi in X:
            log_likelihoods = self._joint_log_likelihood(xi)
            best_cls = max(log_likelihoods.items(), key=lambda kv: kv[1])[0]
            preds.append(int(best_cls))
        return preds


# ---------------------------------------------------------------------------
# BaselineModel façade
# ---------------------------------------------------------------------------


class BaselineModel:
    """
    Baseline predictive model for MAPAQ Track B.

    This class wraps the two simple models above and handles:
    - Preparing the cleaned pandas DataFrame
    - Splitting into train/test sets
    - Training logistic regression or Naive Bayes
    - Computing evaluation metrics
    """

    def __init__(
        self,
        clean_data,
        target_column: Optional[str] = None,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> None:
        """
        Args:
            clean_data: pandas DataFrame returned by DataCleaner
            target_column: optional explicit name of the target column.
                If None, it will be inferred from common names.
            test_size: fraction of samples used for evaluation
            random_state: seed for deterministic train/test split
        """
        import pandas as pd  # local import to avoid hard dependency at import time

        if not isinstance(clean_data, pd.DataFrame):
            raise TypeError("clean_data must be a pandas DataFrame")

        self.clean_data = clean_data.copy()
        self.target_column = target_column
        self.test_size = float(test_size)
        self.random_state = int(random_state)

        # Features / target
        self.feature_columns: List[str] = []
        self.X_train: List[List[float]] = []
        self.X_test: List[List[float]] = []
        self.y_train: List[int] = []
        self.y_test: List[int] = []

        # Models
        self.logistic_model: Optional[LogisticRegressionBaseline] = None
        self.naive_bayes_model: Optional[GaussianNaiveBayesBaseline] = None
        self.model: Optional[object] = None
        self.model_type: Optional[str] = None

        self._data_prepared = False

    # ------------------------------------------------------------------
    # Data preparation helpers
    # ------------------------------------------------------------------
    def _infer_target_column(self) -> str:
        """Infer the most likely target/label column from the dataframe."""
        candidate_names = [
            "risk_label",
            "risk_flag",
            "risk_category",
            "has_infraction",
            "is_infraction",
            "infraction_flag",
            "label",
            "target",
            "y",
        ]
        lower_cols = {c.lower(): c for c in self.clean_data.columns}

        for name in candidate_names:
            if name in lower_cols:
                return lower_cols[name]

        # Fallback: use last column
        return str(self.clean_data.columns[-1])

    def _binarize_target(self, y_series) -> List[int]:
        """Convert a pandas Series into a binary target (0/1)."""
        import pandas as pd

        if y_series.dtype == bool:
            return y_series.astype(int).tolist()

        if pd.api.types.is_numeric_dtype(y_series):
            unique_vals = sorted(v for v in y_series.dropna().unique())
            if len(unique_vals) <= 2:
                mapping = {v: int(i == len(unique_vals) - 1) for i, v in enumerate(unique_vals)}
                return [mapping.get(v, 0) for v in y_series]

            # More than 2 numeric values: threshold at median
            median = float(y_series.median())
            return [1 if (v is not None and v >= median) else 0 for v in y_series]

        # Non-numeric: factorize then map first category to 0, others to 1
        codes, uniques = pd.factorize(y_series.fillna("missing"))
        if len(uniques) == 1:
            return [0 for _ in codes]

        first_code = codes[0]
        return [0 if c == first_code else 1 for c in codes]

    def _prepare_data(self) -> None:
        """Prepare feature matrix and target vector, and create train/test split."""
        if self._data_prepared:
            return

        import pandas as pd

        df = self.clean_data.copy()

        target_col = self.target_column or self._infer_target_column()
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in data.")
        self.target_column = target_col

        y_series = df[target_col]

        # Select numeric / boolean features, excluding the target column
        feature_df = df.drop(columns=[target_col]).select_dtypes(include=["number", "bool"])
        if feature_df.empty:
            raise ValueError("No numeric features available for baseline model.")

        self.feature_columns = list(feature_df.columns)

        X_all = feature_df.astype(float).values.tolist()
        y_all = self._binarize_target(y_series)

        n_samples = len(X_all)
        if n_samples != len(y_all):
            raise ValueError("Mismatch between number of samples in X and y.")

        indices = list(range(n_samples))
        rnd = random.Random(self.random_state)
        rnd.shuffle(indices)

        split_index = int(n_samples * (1.0 - self.test_size))
        if split_index <= 0 or split_index >= n_samples:
            split_index = max(1, n_samples - 1)

        train_idx = indices[:split_index]
        test_idx = indices[split_index:]

        self.X_train = [X_all[i] for i in train_idx]
        self.y_train = [y_all[i] for i in train_idx]
        self.X_test = [X_all[i] for i in test_idx]
        self.y_test = [y_all[i] for i in test_idx]

        self._data_prepared = True

    # ------------------------------------------------------------------
    # Training methods
    # ------------------------------------------------------------------
    def train_logistic_regression(self) -> LogisticRegressionBaseline:
        """
        Train a logistic regression baseline model on the cleaned dataset.

        The trained model is stored in `self.logistic_model` and `self.model`,
        with `self.model_type = "logistic_regression"`.
        """
        self._prepare_data()

        model = LogisticRegressionBaseline()
        model.fit(self.X_train, self.y_train)
        self.logistic_model = model
        self.model = model
        self.model_type = "logistic_regression"
        return model

    def train_naive_bayes(self) -> GaussianNaiveBayesBaseline:
        """
        Train a Gaussian Naïve Bayes baseline model on the cleaned dataset.

        The trained model is stored in `self.naive_bayes_model` and `self.model`,
        with `self.model_type = "naive_bayes"`.
        """
        self._prepare_data()

        model = GaussianNaiveBayesBaseline()
        model.fit(self.X_train, self.y_train)
        self.naive_bayes_model = model
        self.model = model
        self.model_type = "naive_bayes"
        return model

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, Any]:
        """Compute accuracy, precision, recall and F1-score."""
        if not y_true:
            raise ValueError("Empty ground-truth labels for evaluation.")

        tp = tn = fp = fn = 0
        for yt, yp in zip(y_true, y_pred):
            if yt == 1 and yp == 1:
                tp += 1
            elif yt == 0 and yp == 0:
                tn += 1
            elif yt == 0 and yp == 1:
                fp += 1
            elif yt == 1 and yp == 0:
                fn += 1

        total = tp + tn + fp + fn
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * precision * recall / (precision + recall)

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        }

    def evaluate_model(self, mode: str = "current") -> Dict[str, Any]:
        """
        Evaluate the trained model using accuracy, precision, recall and F1-score.

        Args:
            mode:
                - "current" (default): evaluate whichever model is in `self.model`.
                  If no model is trained yet, a logistic regression model is trained.
                - "logistic": train (if needed) and evaluate only logistic regression.
                - "naive_bayes": train (if needed) and evaluate only Naïve Bayes.
                - "both": train/evaluate both and return a dict with results for each.

        Returns:
            A dictionary with evaluation metrics. If `mode == "both"`, returns:
            {
                "logistic_regression": {...metrics...},
                "naive_bayes": {...metrics...}
            }
        """
        self._prepare_data()

        def _eval_single(model_name: str) -> Dict[str, Any]:
            if model_name == "logistic":
                if self.logistic_model is None:
                    self.train_logistic_regression()
                model = self.logistic_model
                name = "logistic_regression"
            elif model_name == "naive_bayes":
                if self.naive_bayes_model is None:
                    self.train_naive_bayes()
                model = self.naive_bayes_model
                name = "naive_bayes"
            else:
                raise ValueError(f"Unsupported model_name: {model_name}")

            assert model is not None
            y_pred = model.predict(self.X_test)
            metrics = self._compute_metrics(self.y_test, y_pred)
            metrics["model_type"] = name
            return metrics

        if mode == "both":
            return {
                "logistic_regression": _eval_single("logistic"),
                "naive_bayes": _eval_single("naive_bayes"),
            }

        if mode in {"logistic", "naive_bayes"}:
            return _eval_single(mode)

        # Default: evaluate the "current" model
        if self.model is None:
            # Train logistic regression by default
            self.train_logistic_regression()

        if isinstance(self.model, LogisticRegressionBaseline):
            return _eval_single("logistic")
        if isinstance(self.model, GaussianNaiveBayesBaseline):
            return _eval_single("naive_bayes")

        raise ValueError("Unknown model type stored in self.model.")
