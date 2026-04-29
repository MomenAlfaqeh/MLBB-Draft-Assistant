from google.cloud import bigquery
from pandas import DataFrame

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


PROJECT_ID = "mlbb-draft-assistant-494814"
DATASET = "mlbb_draft"
TABLE = "heroes"


@data_exporter
def export_to_bigquery(df: DataFrame, **kwargs) -> None:
    """
    Export cleaned hero data to BigQuery
    Table: mlbb_draft.heroes
    Write disposition: WRITE_TRUNCATE (replace existing data)
    Uses ADC for authentication
    """
    if df.empty:
        print("DataFrame is empty, nothing to export")
        return
    
    df = df.copy()
    
    if 'last_updated' not in df.columns:
        from datetime import datetime
        df['last_updated'] = datetime.now()
    
    bq_schema = [
        bigquery.SchemaField("id", "INTEGER"),
        bigquery.SchemaField("name", "STRING"),
        bigquery.SchemaField("role", "STRING"),
        bigquery.SchemaField("specialty", "STRING"),
        bigquery.SchemaField("base_win_rate", "FLOAT"),
        bigquery.SchemaField("pick_rate", "FLOAT"),
        bigquery.SchemaField("ban_rate", "FLOAT"),
        bigquery.SchemaField("tier", "STRING"),
        bigquery.SchemaField("patch", "STRING"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
    ]
    
    column_mapping = {
        'win_rate': 'base_win_rate',
        'specialty': 'specialty',
        'pick_rate': 'pick_rate',
        'ban_rate': 'ban_rate',
    }
    
    df_export = df.copy()
    for old_col, new_col in column_mapping.items():
        if old_col in df_export.columns and new_col != old_col:
            df_export = df_export.rename(columns={old_col: new_col})
    
    required_cols = ['id', 'name', 'role', 'specialty', 'base_win_rate', 
                    'pick_rate', 'ban_rate', 'tier', 'patch', 'last_updated']
    
    for col in required_cols:
        if col not in df_export.columns:
            df_export[col] = None
    
    df_export = df_export[required_cols]
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    job_config = bigquery.LoadJobConfig(
        schema=bq_schema,
        write_disposition="WRITE_TRUNCATE",
    )
    
    print(f"Loading {len(df_export)} rows to {table_id}...")
    
    job = client.load_table_from_dataframe(
        df_export, table_id, job_config=job_config
    )
    
    job.result()
    
    table = client.get_table(table_id)
    print(f"Loaded {table.num_rows} rows to {table_id}")
