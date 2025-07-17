from typing import List, Dict, Any, Optional
from supabase import Client, PostgrestAPIResponse
import logging
import uuid # For generating potential unique IDs if DB doesn't auto-generate them in a way you can retrieve easily
import asyncio # Import asyncio

logger = logging.getLogger(__name__)

# Helper to run sync Supabase calls in a thread pool
async def run_sync_in_executor(func, *args):
    # Runs a synchronous function `func` with arguments `args` in asyncio's default executor
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args) # None uses the default ThreadPoolExecutor

async def get_or_create_entity_node(
    supabase: Client, 
    entity_type: str, 
    entity_value: str, 
    source_document_id: Optional[str] = None
) -> Optional[str]:
    """
    Retrieves an existing entity node or creates a new one. Uses executor for sync DB calls.
    """
    if not entity_type or not entity_value:
        logger.warning("Entity type or value is missing, cannot get/create node.")
        return None

    try:
        # --- Define sync functions for DB operations --- 
        def check_node_sync():
            return (
                supabase.table('graph_nodes')
                .select('id')
                .eq('node_type', entity_type)
                .eq('node_value', entity_value)
                .limit(1)
                .execute()
            )
        
        def create_node_sync():
            node_properties = {}
            if source_document_id:
                node_properties['first_seen_document_id'] = source_document_id
            return (
                supabase.table('graph_nodes')
                .insert({
                    'node_type': entity_type,
                    'node_value': entity_value,
                    'properties': node_properties if node_properties else None 
                })
                .execute()
            )
        # ----------------------------------------------

        # 1. Check if the node exists (run sync check in executor)
        response: PostgrestAPIResponse = await run_sync_in_executor(check_node_sync)
        
        if response.data:
            found_node_id = response.data[0]['id']
            logger.info(f"Node found: type='{entity_type}', value='{entity_value}', id={found_node_id}")
            return found_node_id
        else:
            # 2. If not, create the node (run sync create in executor)
            logger.info(f"Node not found. Creating new node: type='{entity_type}', value='{entity_value}'")
            insert_response: PostgrestAPIResponse = await run_sync_in_executor(create_node_sync)

            if insert_response.data:
                created_node_id = insert_response.data[0]['id']
                logger.info(f"Successfully created node: type='{entity_type}', value='{entity_value}', id={created_node_id}")
                return created_node_id
            else:
                # Log potential error from Supabase if available
                error_details = insert_response.error if hasattr(insert_response, 'error') else 'Unknown error during insert'
                logger.error(f"Failed to create node after attempting insert. Error: {error_details}")
                return None

    except Exception as e:
        logger.error(f"Error in get_or_create_entity_node for '{entity_type}':'{entity_value}': {e}", exc_info=True)
        return None

async def create_relationship_edge(
    supabase: Client, 
    source_node_id: str, 
    target_node_id: str, 
    relationship_type: str, 
    context_sentence: Optional[str] = None, 
    source_document_id: Optional[str] = None,
    weight: Optional[float] = 1.0 
) -> bool:
    """
    Creates a relationship edge. Uses executor for sync DB calls.
    """
    if not all([source_node_id, target_node_id, relationship_type]):
        logger.warning("Missing IDs or relationship type for edge creation.")
        return False
    try:
        logger.info(f"Creating edge: {source_node_id} -[{relationship_type}]-> {target_node_id}")
        edge_properties = {}
        if source_document_id:
            edge_properties['source_document_id'] = source_document_id

        edge_data_to_insert = {
            'source_node_id': source_node_id,
            'target_node_id': target_node_id,
            'relationship_type': relationship_type,
            'context': context_sentence,
            'properties': edge_properties if edge_properties else None,
            'weight': weight
        }

        # --- Define sync function for DB operation --- 
        def create_edge_sync():
            return (
                supabase.table('graph_edges')
                .insert(edge_data_to_insert)
                .execute()
            )
        # -------------------------------------------

        # Run sync insert in executor
        insert_response: PostgrestAPIResponse = await run_sync_in_executor(create_edge_sync)

        if insert_response.data:
            logger.info(f"Successfully created edge: {source_node_id} -[{relationship_type}]-> {target_node_id}")
            return True
        # Check for unique constraint violation (error code 23505)
        elif hasattr(insert_response, 'error') and insert_response.error and '23505' in str(insert_response.error.code if hasattr(insert_response.error, 'code') else insert_response.error):
            logger.warning(f"Edge already exists (unique constraint violation): {source_node_id} -[{relationship_type}]-> {target_node_id} with context '{context_sentence}'. Not an error.")
            return True # Treat as success if it already exists
        else:
            # Log other errors
            error_details = insert_response.error if hasattr(insert_response, 'error') else 'Unknown error during insert'
            logger.error(f"Failed to create edge. Error: {error_details}")
            return False

    except Exception as e:
        logger.error(f"Error in create_relationship_edge for {source_node_id} -> {target_node_id}: {e}", exc_info=True)
        return False

async def process_and_update_knowledge_graph(
    supabase_client: Client, 
    extracted_relationships: List[Dict[str, Any]], 
    source_document_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Processes a list of extracted relationships and updates the knowledge graph.
    Iterates through relationships, creates/retrieves nodes, and creates edges.
    """
    summary = {"nodes_processed": 0, "edges_attempted": 0, "edges_created_or_existing": 0, "errors": 0}

    if not extracted_relationships:
        summary["message"] = "No relationships provided to process."
        return summary

    # Track nodes processed in this run to avoid redundant DB calls for the same entity within the same batch
    processed_nodes_cache = {} # Key: (entity_type, entity_value), Value: node_id

    for rel_data in extracted_relationships:
        source_entity_info = rel_data.get('source_entity')
        target_entity_info = rel_data.get('target_entity')
        relationship_type = rel_data.get('relationship_type')
        context_sentence = rel_data.get('context_sentence')

        if not (source_entity_info and isinstance(source_entity_info, dict) and 
                target_entity_info and isinstance(target_entity_info, dict) and 
                relationship_type):
            logger.warning(f"Skipping incomplete relationship data: {rel_data}")
            summary["errors"] += 1
            continue

        source_type = source_entity_info.get('type')
        source_value = source_entity_info.get('value')
        target_type = target_entity_info.get('type')
        target_value = target_entity_info.get('value')

        if not (source_type and source_value and target_type and target_value):
            logger.warning(f"Skipping relationship with missing entity type/value: {rel_data}")
            summary["errors"] += 1
            continue
        
        source_cache_key = (source_type, source_value)
        if source_cache_key in processed_nodes_cache:
            source_node_id = processed_nodes_cache[source_cache_key]
        else:
            source_node_id = await get_or_create_entity_node(
                supabase_client, source_type, source_value, source_document_id
            )
            if source_node_id:
                processed_nodes_cache[source_cache_key] = source_node_id
                summary["nodes_processed"] += 1
        
        target_cache_key = (target_type, target_value)
        if target_cache_key in processed_nodes_cache:
            target_node_id = processed_nodes_cache[target_cache_key]
        else:
            target_node_id = await get_or_create_entity_node(
                supabase_client, target_type, target_value, source_document_id
            )
            if target_node_id:
                processed_nodes_cache[target_cache_key] = target_node_id
                # Avoid double counting if source and target are the same new entity (unlikely but possible)
                if source_cache_key != target_cache_key or source_node_id is None: 
                    summary["nodes_processed"] += 1

        if source_node_id and target_node_id:
            summary["edges_attempted"] += 1
            edge_created_or_exists = await create_relationship_edge(
                supabase_client, 
                source_node_id, 
                target_node_id, 
                relationship_type, 
                context_sentence,
                source_document_id
            )
            if edge_created_or_exists:
                summary["edges_created_or_existing"] += 1
            else:
                # Error already logged in create_relationship_edge
                summary["errors"] += 1
        else:
            logger.error(f"Could not obtain node IDs for relationship: {rel_data}. Source: {source_node_id}, Target: {target_node_id}")
            summary["errors"] += 1
            
    summary["message"] = f"Processed {len(extracted_relationships)} relationships. Nodes processed (created or found in this batch): {summary['nodes_processed']}."
    logger.info(f"Knowledge graph update summary: {summary}")
    return summary

if __name__ == '__main__':
    # Configure basic logging for the test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Import the actual Supabase client utility
    import asyncio
    import os
    # Ensure the path is correct to import from seer.utils if running as a script/module
    # This might require setting PYTHONPATH or running with python -m seer.db.knowledge_graph_updater
    # from ...utils.supabase_client import get_supabase_client, initialize_client # Example relative import if structure allows
    
    # For direct script execution, adjust path to seer.utils.supabase_client as needed
    # This often means ensuring the project root is in sys.path
    import sys
    # Assuming the script is run from the project root or PYTHONPATH is set
    try:
        from seer.utils.supabase_client import get_supabase_client, initialize_client
    except ImportError:
        # Fallback for simpler execution if the script is deep and Python can't find seer.utils
        # This assumes a certain directory structure. Best to run with `python -m` from project root.
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))) # Go up two levels to project root
        from seer.utils.supabase_client import get_supabase_client, initialize_client

    async def main_test():
        # Initialize and get the actual Supabase client
        # Ensure SUPABASE_URL and SUPABASE_KEY are in your environment or settings
        logger.info("Attempting to initialize actual Supabase client for testing...")
        initialize_client() # Ensure client is initialized based on your logic in supabase_client.py
        try:
            actual_supabase_client = get_supabase_client()
            logger.info("Actual Supabase client obtained.")
        except ConnectionError as e:
            logger.error(f"Failed to get actual Supabase client: {e}. Ensure Supabase URL/KEY are set.")
            logger.error("Falling back to MockSupabaseClient for this test run. Database will not be updated.")
            # Fallback to mock client if real one fails (e.g., for CI without Supabase creds)
            class MockSupabaseClient:
                async def table(self, table_name: str):
                    logger.info(f"[MOCK Supabase] Accessing table: {table_name}")
                    return MockQueryBuilder(table_name)

            class MockQueryBuilder:
                def __init__(self, table_name):
                    self._table_name = table_name
                    self._queries = []
                    self._insert_data = None
                    self._select_cols = "*"
                    self._filters = []

                def select(self, columns: str = "*"):
                    self._select_cols = columns
                    self._queries.append(f"SELECT {columns}")
                    return self
                
                def insert(self, data: dict, returning: Optional[str] = None):
                    self._insert_data = data
                    self._queries.append(f"INSERT {data}")
                    return self

                def eq(self, column: str, value: Any):
                    self._filters.append((column, value))
                    self._queries.append(f"EQ {column}={value}")
                    return self
                
                def limit(self, count: int):
                    self._queries.append(f"LIMIT {count}")
                    return self
                
                async def execute(self) -> PostgrestAPIResponse:
                    logger.info(f"[MOCK Supabase] Executing for table {self._table_name}: {self._queries}")
                    if self._insert_data:
                        if self._table_name == 'graph_nodes':
                            mock_id = str(uuid.uuid4())
                            logger.info(f"[MOCK DB] Simulating insert for graph_nodes, generated id: {mock_id}")
                            return PostgrestAPIResponse(data=[{**self._insert_data, 'id': mock_id}], count=1)
                        elif self._table_name == 'graph_edges':
                            logger.info(f"[MOCK DB] Simulating insert for graph_edges")
                            return PostgrestAPIResponse(data=[{**self._insert_data, 'id': str(uuid.uuid4())}], count=1)
                    if self._table_name == 'graph_nodes' and self._filters:
                        logger.info(f"[MOCK DB] Simulating select for graph_nodes with filters {self._filters} - returning not found.")
                        return PostgrestAPIResponse(data=[], count=0)
                    return PostgrestAPIResponse(data=[], count=0)
            actual_supabase_client = MockSupabaseClient()

        sample_relationships = [
            {
                "source_entity": { "type": "ThreatActor", "value": "ShadowNet Group Test" },
                "relationship_type": "uses",
                "target_entity": { "type": "Malware", "value": "DataThiefTest.exe" },
                "context_sentence": "ShadowNet Group Test used DataThiefTest.exe..."
            },
            {
                "source_entity": { "type": "Malware", "value": "DataThiefTest.exe" },
                "relationship_type": "exploits",
                "target_entity": { "type": "Vulnerability", "value": "CVE-2023-99999" },
                "context_sentence": "DataThiefTest.exe exploits CVE-2023-99999..."
            }
        ]
        
        print("\n--- Testing process_and_update_knowledge_graph with an attempt to use REAL Supabase client ---")
        result_summary = await process_and_update_knowledge_graph(
            actual_supabase_client, 
            sample_relationships, 
            source_document_id="direct_script_run_doc_123"
        )
        print(f"Test run summary: {result_summary}")

    asyncio.run(main_test()) 