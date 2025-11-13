"""
BigQuery tools for the chatbot - allows Gemini to query your data.
"""

import os
from google.cloud import bigquery
from typing import Dict, Any, List
from config import settings


class BigQueryClient:
    """Simple BigQuery client for chatbot integration."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        if settings.enable_bigquery_mcp:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_application_credentials
            self.client = bigquery.Client(project=settings.bigquery_project_id)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
    
    def list_datasets(self) -> str:
        """List all available datasets."""
        if not self.enabled:
            return "BigQuery not enabled"
        
        datasets = list(self.client.list_datasets())
        if not datasets:
            return "No datasets found"
        
        result = "Available datasets:\n"
        for dataset in datasets:
            result += f"- {dataset.dataset_id}\n"
        return result
    
    def list_tables(self, dataset_id: str) -> str:
        """List tables in a dataset."""
        if not self.enabled:
            return "BigQuery not enabled"
        
        try:
            tables = list(self.client.list_tables(dataset_id))
            if not tables:
                return f"No tables found in dataset: {dataset_id}"
            
            result = f"Tables in {dataset_id}:\n"
            for table in tables:
                result += f"- {table.table_id}\n"
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_table_schema(self, dataset_id: str, table_id: str) -> str:
        """Get schema of a table."""
        if not self.enabled:
            return "BigQuery not enabled"
        
        try:
            table_ref = f"{self.client.project}.{dataset_id}.{table_id}"
            table = self.client.get_table(table_ref)
            
            result = f"Schema for {dataset_id}.{table_id}:\n"
            result += f"Total rows: {table.num_rows:,}\n\n"
            result += "Columns:\n"
            for field in table.schema:
                result += f"- {field.name} ({field.field_type})\n"
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    
    def query(self, sql_query: str) -> str:
        """
        Execute a BigQuery SQL query.
        This is the main function Gemini will use to query your data.
        """
        if not self.enabled:
            return "BigQuery not enabled"
        
        try:
            # Add safety: limit results if LIMIT not specified
            if 'LIMIT' not in sql_query.upper():
                sql_query = sql_query.rstrip(';') + ' LIMIT 100'
            
            print(f"Executing query: {sql_query}")
            query_job = self.client.query(sql_query)
            results = query_job.result()
            
            # Convert results to string
            rows = list(results)
            if not rows:
                return "Query executed successfully but returned no results."
            
            # Format results as table
            result_text = f"Query returned {len(rows)} rows:\n\n"
            
            # Get column names
            if rows:
                columns = list(rows[0].keys())
                result_text += " | ".join(columns) + "\n"
                result_text += "-" * (len(" | ".join(columns))) + "\n"
                
                # Add rows
                for row in rows[:20]:  # Show first 20 rows
                    values = [str(row[col]) for col in columns]
                    result_text += " | ".join(values) + "\n"
                
                if len(rows) > 20:
                    result_text += f"\n... and {len(rows) - 20} more rows"
            
            return result_text
            
        except Exception as e:
            return f"Query error: {str(e)}\n\nPlease check your SQL syntax and table names."


# Global BigQuery client
bq_client = BigQueryClient()


# Tool functions for registration
async def bigquery_list_datasets() -> str:
    """List all available BigQuery datasets."""
    return bq_client.list_datasets()


async def bigquery_list_tables(dataset_id: str) -> str:
    """List all tables in a BigQuery dataset."""
    return bq_client.list_tables(dataset_id)


async def bigquery_get_schema(dataset_id: str, table_id: str) -> str:
    """Get the schema of a BigQuery table."""
    return bq_client.get_table_schema(dataset_id, table_id)


async def bigquery_query(query: str) -> str:
    """
    Execute a SQL query on BigQuery.
    
    The query will automatically be limited to 100 rows if no LIMIT is specified.
    Use proper BigQuery SQL syntax.
    """
    return bq_client.query(query)

