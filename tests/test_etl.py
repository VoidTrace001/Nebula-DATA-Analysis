import pytest
import pandas as pd
import io
from src.core.etl import ETLEngine

def test_load_from_file_csv():
    csv_data = "col1,col2\n1,2\n3,4"
    file = io.BytesIO(csv_data.encode())
    df = ETLEngine.load_from_file(file, "test.csv")
    assert df.shape == (2, 2)
    assert list(df.columns) == ["col1", "col2"]

def test_validate_schema_success():
    df = pd.DataFrame({"age": [25, 30], "name": ["Alice", "Bob"]})
    schema = {"age": int, "name": str}
    errors = ETLEngine.validate_schema(df, schema)
    assert len(errors) == 0

def test_validate_schema_failure():
    df = pd.DataFrame({"age": ["wrong", 30]})
    schema = {"age": int}
    errors = ETLEngine.validate_schema(df, schema)
    assert len(errors) > 0
