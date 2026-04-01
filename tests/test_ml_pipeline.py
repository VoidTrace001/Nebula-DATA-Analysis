import pytest
import pandas as pd
from src.core.ml_pipeline import MLPipeline

def test_ml_pipeline_train_regression():
    df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'feature2': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        'target': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    })
    pipeline = MLPipeline(task='regression')
    metrics = pipeline.train(df[['feature1', 'feature2']], df['target'], 'Random Forest')
    assert 'RMSE' in metrics
    assert 'R2' in metrics
    assert pipeline.model is not None

def test_ml_pipeline_train_classification():
    df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'target': [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    })
    pipeline = MLPipeline(task='classification')
    metrics = pipeline.train(df[['feature1']], df['target'], 'Random Forest')
    assert 'Accuracy' in metrics
    assert pipeline.model is not None
