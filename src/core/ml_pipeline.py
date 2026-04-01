import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score

# Safe Import Layer
def safe_import(module_name):
    try: return __import__(module_name), True
    except ImportError: return None, False

joblib, HAS_JOBLIB = safe_import("joblib")
shap, HAS_SHAP = safe_import("shap")

logger = logging.getLogger(__name__)

class MLPipeline:
    """Production-grade ML Pipeline with modular dependencies."""

    def __init__(self, task: str = 'regression'):
        self.task = task
        self.model = None
        self.history = []

    def build_preprocessor(self, X: pd.DataFrame) -> ColumnTransformer:
        numeric = X.select_dtypes(include=['int64', 'float64']).columns
        categorical = X.select_dtypes(include=['object', 'category', 'bool']).columns
        
        num_tf = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
        cat_tf = Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))])
        
        return ColumnTransformer(transformers=[('num', num_tf, numeric), ('cat', cat_tf, categorical)])

    def train(self, X: pd.DataFrame, y: pd.Series, m_type: str, tune: bool = False) -> Dict[str, Any]:
        prep = self.build_preprocessor(X)
        if m_type == 'Random Forest':
            est = RandomForestRegressor(random_state=42) if self.task == 'regression' else RandomForestClassifier(random_state=42)
        elif m_type == 'Neural Approximation':
            from sklearn.neural_network import MLPRegressor, MLPClassifier
            est = MLPRegressor(random_state=42, max_iter=500) if self.task == 'regression' else MLPClassifier(random_state=42, max_iter=500)
        else:
            est = LinearRegression() if self.task == 'regression' else LogisticRegression(max_iter=1000)

        self.model = Pipeline([('preprocessor', prep), ('model', est)])
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        pred = self.model.predict(X_test)
        metrics = self.evaluate(y_test, pred)
        
        # Performance Tracking
        self.history.append({
            "model": m_type,
            "metrics": metrics,
            "features": list(X.columns)
        })
        
        return metrics

    def evaluate(self, y_t, y_p) -> Dict[str, Any]:
        if self.task == 'regression': return {"RMSE": np.sqrt(mean_squared_error(y_t, y_p)), "R2": r2_score(y_t, y_p)}
        return {"Accuracy": accuracy_score(y_t, y_p), "F1": f1_score(y_t, y_p, average='macro')}

    def save_model(self, path: str):
        if not HAS_JOBLIB: raise ImportError("Joblib not found.")
        joblib.dump({'model': self.model, 'task': self.task, 'history': self.history}, path)

    @classmethod
    def load_model(cls, path: str) -> 'MLPipeline':
        if not HAS_JOBLIB: raise ImportError("Joblib not found.")
        data = joblib.load(path)
        instance = cls(task=data['task'])
        instance.model = data['model']
        instance.history = data.get('history', [])
        return instance

    def explain_model(self, X: pd.DataFrame) -> Optional[Any]:
        if not HAS_SHAP: return None, None
        try:
            X_t = self.model.named_steps['preprocessor'].transform(X)
            explainer = shap.Explainer(self.model.named_steps['model'], X_t)
            return explainer(X_t), X_t
        except Exception as e:
            logger.error(f"SHAP error: {e}")
            return None, None
