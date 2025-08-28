# Track B – MAPAQ Predictive Health Model (Karamba)

Goal: Predict restaurant risk profiles based on public inspection datasets + derived variables.

Dataset Preparation

- Collect MAPAQ inspection data.
  --> /data_ingest.py

- Clean the dataset (remove nulls, unify column formats, encode categorical variables).
  --> /data_cleaner.py

Dictionaries

- Addresses Dictionary: Normalize addresses → enable geocoding for map display.
  --> /address_dict.py

- Themes Dictionary: Build keyword-based classification system (e.g., “Sushi,” “Trattoria,” “BBQ”) to infer cuisine type.
  --> /theme_dict.py

Probability Model

- Implement baseline model (logistic regression or Naïve Bayes).
  --> /model_baseline.py

- Calculate conditional probabilities for infractions given variables (theme, size, past history).
  --> /probability_engine.py

Rule Adaptation

- Add logic to adjust probabilities when regulations change (store effective dates in DB, apply time-based weights).
  --> /rule_adapter.py

Risk Profiling

- Generate risk score per restaurant.
  --> /risk_score.py

- Categorize into Low / Medium / High risk.
  --> /risk_categorizer.py

Visualization

- Build dashboard showing probabilities and trends.
  --> /dashboard.py (Flask/Django + frontend framework)

- Map restaurants (using geocoded addresses).
  --> /geo_map.py
