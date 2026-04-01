import pandas as pd
import logging
import io
from typing import Union, Optional, List, Dict, Any
from sqlalchemy import create_engine
from docx import Document

# Safe Import Handlers
def safe_import(module_name):
    try:
        return __import__(module_name), True
    except ImportError:
        return None, False

pl, HAS_POLARS = safe_import("polars")
boto3, HAS_S3 = safe_import("boto3")
gcs, HAS_GCS = safe_import("google.cloud.storage")
azure, HAS_AZURE = safe_import("azure.storage.blob")
pydantic, HAS_PYDANTIC = safe_import("pydantic")

logger = logging.getLogger(__name__)

class ETLEngine:
    """Enterprise-Safe ETL Engine with dynamic dependency handling."""
    
    @staticmethod
    def load_from_file(file: io.BytesIO, filename: str) -> pd.DataFrame:
        try:
            if filename.endswith('.csv'):
                if HAS_POLARS:
                    return pl.read_csv(file).to_pandas()
                return pd.read_csv(file)
            elif filename.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file)
            elif filename.endswith('.docx'):
                return ETLEngine._parse_docx(file)
            raise ValueError(f"Format not supported: {filename}")
        except Exception as e:
            logger.error(f"Load error: {e}")
            raise

    @staticmethod
    def _parse_docx(file: io.BytesIO) -> pd.DataFrame:
        doc = Document(file)
        data = [[cell.text for cell in row.cells] for table in doc.tables for row in table.rows]
        return pd.DataFrame(data[1:], columns=data[0]) if data else pd.DataFrame()

    @staticmethod
    def load_from_sql(conn_str: str, query: str) -> pd.DataFrame:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            return pd.read_sql(query, conn)

    @staticmethod
    def load_from_s3(bucket: str, key: str, ak: str, sk: str) -> pd.DataFrame:
        if not HAS_S3: raise ImportError("AWS SDK (boto3) not installed. Run 'pip install boto3'.")
        s3 = boto3.client('s3', aws_access_key_id=ak, aws_secret_access_key=sk)
        obj = s3.get_object(Bucket=bucket, Key=key)
        return ETLEngine.load_from_file(io.BytesIO(obj['Body'].read()), key)

    @staticmethod
    def validate_schema(df: pd.DataFrame, schema_def: Dict[str, Any]) -> List[str]:
        if not HAS_PYDANTIC: return ["Error: Pydantic not installed for validation."]
        from pydantic import create_model, ValidationError, Field
        fields = {col: (Optional[dtype], Field(default=None)) for col, dtype in schema_def.items()}
        Model = create_model("Schema", **fields)
        errors = []
        for idx, row in df.iterrows():
            try: Model(**row.to_dict())
            except ValidationError as e: errors.append(f"Row {idx}: {e}")
        return errors
