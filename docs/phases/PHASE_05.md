# Phase 5 — Advanced Analytics

## Objective

Add machine learning and forecasting capabilities to the analytical engine.

---

## Scope

### In Scope
- Classification (Scikit-learn)
- Regression (linear, non-linear)
- Time-series forecasting (Statsmodels, Prophet or similar)
- Feature importance and SHAP explanations
- Clustering (k-means, DBSCAN)
- Model evaluation metrics

### Out of Scope
- Deep learning
- Custom model training pipelines

---

## Implementation Tasks

- [ ] Add Scikit-learn classification tools
- [ ] Add regression tools with evaluation metrics
- [ ] Add time-series forecasting tools
- [ ] Add feature importance tool
- [ ] Add clustering tool
- [ ] Extend LangGraph workflow to route ML requests
- [ ] Add ML result visualization (feature charts, confusion matrix, forecast plots)
- [ ] Write tests verifying correct results on known datasets

---

## Acceptance Criteria

- [ ] Classification produces correct predictions on test datasets
- [ ] Regression metrics (R², RMSE) are computed correctly
- [ ] Forecasts are deterministic for the same input
- [ ] Feature importance values sum correctly
- [ ] All calculations are tool-executed — LLM interprets only
