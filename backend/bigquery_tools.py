"""
BigQuery tools for the chatbot - allows Gemini to query your data.
"""

import os
import asyncio
from concurrent.futures import TimeoutError as FuturesTimeoutError
from google.cloud import bigquery
from typing import Dict, Any, List, Tuple, Optional
from config import settings
import google.generativeai as genai


class BigQueryClient:
    """Simple BigQuery client for chatbot integration."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        if settings.enable_bigquery_mcp:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_application_credentials
            self.client = bigquery.Client(project=settings.bigquery_project_id)
            self.enabled = True
            # Initialize Gemini for query fixing
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(model_name=settings.gemini_model)
        else:
            self.client = None
            self.enabled = False
            self.gemini_model = None
    
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
    
    def _fix_query_with_llm(self, original_query: str, error_message: str, attempt: int, timeout: int = 30) -> Optional[str]:
        """
        Use Gemini to fix a failed BigQuery query with timeout.
        
        Args:
            original_query: The original SQL query that failed
            error_message: The error message from BigQuery
            attempt: Current retry attempt number
            timeout: Maximum seconds to wait for LLM response (default: 30)
            
        Returns:
            Fixed SQL query or None if LLM couldn't fix it
        """
        if not self.gemini_model:
            return None
        
        try:
            prompt = f"""You are a BigQuery SQL expert. A query has failed with an error. Please fix the SQL query.

Original Query:
```sql
{original_query}
```

Error Message:
{error_message}

Retry Attempt: {attempt}/3

Please analyze the error and provide a corrected SQL query. Respond ONLY with the corrected SQL query, nothing else.
Do not include markdown code blocks, explanations, or any other text - just the raw SQL query.

Corrected Query:"""

            print(f"⏳ Waiting for LLM response (timeout: {timeout}s)...")
            
            # Use request_options to set timeout for the API call
            response = self.gemini_model.generate_content(
                prompt,
                request_options={"timeout": timeout}
            )
            
            fixed_query = response.text.strip()
            
            # Remove markdown code blocks if present
            if fixed_query.startswith('```'):
                lines = fixed_query.split('\n')
                # Remove first and last lines (markdown markers)
                fixed_query = '\n'.join(lines[1:-1]) if len(lines) > 2 else fixed_query
            
            # Remove any remaining ```sql or ``` markers
            fixed_query = fixed_query.replace('```sql', '').replace('```', '').strip()
            
            print(f"\n🔧 LLM Fixed Query (Attempt {attempt}):")
            print(f"Original: {original_query[:100]}...")
            print(f"Fixed: {fixed_query[:100]}...")
            
            return fixed_query
            
        except FuturesTimeoutError:
            print(f"⏱️ Timeout: LLM took longer than {timeout} seconds to respond")
            return None
        except TimeoutError:
            print(f"⏱️ Timeout: LLM took longer than {timeout} seconds to respond")
            return None
        except Exception as e:
            error_str = str(e)
            if 'timeout' in error_str.lower() or 'deadline' in error_str.lower():
                print(f"⏱️ Timeout: LLM request timed out - {error_str}")
            else:
                print(f"❌ Error using LLM to fix query: {error_str}")
            return None
    
    def _execute_query_once(self, sql_query: str, timeout: int = 60) -> Tuple[bool, str]:
        """
        Execute a BigQuery query once without retry logic.
        
        Args:
            sql_query: SQL query to execute
            timeout: Maximum seconds to wait for query execution (default: 60)
            
        Returns:
            Tuple of (success: bool, result: str)
        """
        try:
            # Add safety: limit results if LIMIT not specified
            query_to_execute = sql_query
            if 'LIMIT' not in sql_query.upper():
                query_to_execute = sql_query.rstrip(';') + ' LIMIT 100'
            
            print(f"📊 Executing query (timeout: {timeout}s): {query_to_execute[:200]}...")
            
            # Configure job with timeout (removed maximum_bytes_billed as it can cause access denied)
            from google.cloud.bigquery import QueryJobConfig
            job_config = QueryJobConfig(
                use_query_cache=True
            )
            
            query_job = self.client.query(query_to_execute, job_config=job_config)
            
            # Wait for query with timeout
            try:
                results = query_job.result(timeout=timeout)
            except FuturesTimeoutError:
                return False, f"Query execution timed out after {timeout} seconds. The query may be too complex or processing too much data."
            except TimeoutError:
                return False, f"Query execution timed out after {timeout} seconds. The query may be too complex or processing too much data."
            
            # Convert results to string
            rows = list(results)
            if not rows:
                return True, "Query executed successfully but returned no results."
            
            # Format results as table
            result_text = f"✅ Query returned {len(rows)} rows:\n\n"
            
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
            
            return True, result_text
            
        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower() or 'deadline' in error_msg.lower():
                return False, f"Query execution timed out: {error_msg}"
            return False, error_msg
    
    def query(self, sql_query: str, max_retries: int = 3, query_timeout: int = 60, llm_timeout: int = 30) -> str:
        """
        Execute a BigQuery SQL query with automatic retry and LLM-based error fixing.
        This is the main function Gemini will use to query your data.
        
        Args:
            sql_query: The SQL query to execute
            max_retries: Maximum number of retry attempts (default: 3)
            query_timeout: Timeout in seconds for BigQuery execution (default: 60)
            llm_timeout: Timeout in seconds for LLM fix attempts (default: 30)
            
        Returns:
            Query results or detailed error message
        """
        if not self.enabled:
            return "BigQuery not enabled"
        
        current_query = sql_query
        error_history = []
        
        for attempt in range(1, max_retries + 1):
            print(f"\n{'='*60}")
            print(f"Query Attempt {attempt}/{max_retries}")
            print(f"{'='*60}")
            
            # Try to execute the query
            success, result = self._execute_query_once(current_query, timeout=query_timeout)
            
            if success:
                # Query succeeded!
                if attempt > 1:
                    # Add context that this was a retry
                    retry_info = f"\n\n📝 Note: Query succeeded after {attempt} attempt(s)."
                    if error_history:
                        retry_info += f"\nPrevious errors were automatically fixed by the LLM."
                    result = result + retry_info
                return result
            
            # Query failed - record the error
            error_msg = result
            error_history.append({
                "attempt": attempt,
                "query": current_query,
                "error": error_msg
            })
            
            print(f"❌ Query failed on attempt {attempt}: {error_msg[:200]}...")
            
            # If we've exhausted all retries, return detailed error
            if attempt >= max_retries:
                detailed_error = self._format_final_error(sql_query, error_history)
                return detailed_error
            
            # Try to fix the query using LLM
            print(f"🤖 Asking LLM to fix the query...")
            fixed_query = self._fix_query_with_llm(current_query, error_msg, attempt, timeout=llm_timeout)
            
            if not fixed_query or fixed_query == current_query:
                # LLM couldn't fix it or returned the same query
                print(f"⚠️ LLM could not provide a fix. Stopping retries.")
                detailed_error = self._format_final_error(sql_query, error_history)
                return detailed_error
            
            # Use the fixed query for the next attempt
            current_query = fixed_query
        
        # Should not reach here, but just in case
        return self._format_final_error(sql_query, error_history)
    
    def _format_final_error(self, original_query: str, error_history: List[Dict[str, Any]]) -> str:
        """
        Format a detailed error message after all retries have failed.
        
        Args:
            original_query: The original SQL query
            error_history: List of all errors encountered
            
        Returns:
            Formatted error message
        """
        error_msg = "❌ Query Failed After Multiple Attempts\n\n"
        error_msg += f"Original Query:\n```sql\n{original_query}\n```\n\n"
        error_msg += f"Attempted {len(error_history)} times with automatic LLM fixes.\n\n"
        error_msg += "Error History:\n"
        
        # Check if any errors were timeout-related
        has_timeout = False
        has_llm_timeout = False
        
        for i, error_info in enumerate(error_history, 1):
            error_msg += f"\n--- Attempt {i} ---\n"
            if i > 1:
                error_msg += f"Query: {error_info['query'][:200]}...\n"
            error_text = error_info['error'][:300]
            error_msg += f"Error: {error_text}\n"
            
            # Check for timeout indicators
            if 'timeout' in error_text.lower() or 'timed out' in error_text.lower():
                has_timeout = True
        
        error_msg += "\n💡 Suggestions:\n"
        
        if has_timeout:
            error_msg += "⏱️  TIMEOUT DETECTED:\n"
            error_msg += "- The query or LLM is taking too long to respond\n"
            error_msg += "- Try simplifying the query or adding more specific filters\n"
            error_msg += "- Consider using smaller date ranges or LIMIT clauses\n"
            error_msg += "- Check if you're querying very large tables\n\n"
        
        error_msg += "General tips:\n"
        error_msg += "- Check table names and dataset IDs\n"
        error_msg += "- Verify column names match the schema\n"
        error_msg += "- Ensure you have proper permissions\n"
        error_msg += "- Review BigQuery SQL syntax\n"
        
        return error_msg


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

