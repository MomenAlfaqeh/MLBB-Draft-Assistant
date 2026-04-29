from google.cloud import bigquery

PROJECT_ID = "mlbb-draft-assistant-494814"
DATASET = "mlbb_draft"

def create_bigquery_dataset_and_tables():
    client = bigquery.Client(project=PROJECT_ID)
    
    dataset_id = f"{PROJECT_ID}.{DATASET}"
    
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"Created dataset {dataset.dataset_id}")
    except Exception as e:
        print(f"Dataset may already exist: {e}")
    
    schemas = {
        "heroes": [
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
        ],
        "hero_counters": [
            bigquery.SchemaField("hero_id", "INTEGER"),
            bigquery.SchemaField("countered_by_id", "INTEGER"),
            bigquery.SchemaField("counter_score", "FLOAT"),
            bigquery.SchemaField("sample_size", "INTEGER"),
            bigquery.SchemaField("patch", "STRING"),
        ],
        "hero_synergies": [
            bigquery.SchemaField("hero_a_id", "INTEGER"),
            bigquery.SchemaField("hero_b_id", "INTEGER"),
            bigquery.SchemaField("synergy_score", "FLOAT"),
            bigquery.SchemaField("combined_wr", "FLOAT"),
            bigquery.SchemaField("sample_size", "INTEGER"),
            bigquery.SchemaField("patch", "STRING"),
        ],
        "patches": [
            bigquery.SchemaField("patch_id", "STRING"),
            bigquery.SchemaField("release_date", "DATE"),
            bigquery.SchemaField("notes", "STRING"),
        ],
    }
    
    for table_name, schema in schemas.items():
        table_id = f"{dataset_id}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            table = client.create_table(table)
            print(f"Created table {table_id}")
        except Exception as e:
            print(f"Table {table_name} may already exist: {e}")
    
    print("BigQuery setup complete!")

if __name__ == "__main__":
    create_bigquery_dataset_and_tables()
