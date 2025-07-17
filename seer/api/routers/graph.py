# seer/api/routers/graph.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client
from typing import Dict, Any, List, Optional
import asyncio # Import asyncio for executor

# Assuming utility functions are correctly set up for imports
# Adjust paths if necessary based on your project structure when running
try:
    from seer.utils.supabase_client import get_supabase_client
    # Import the functions needed to update the graph tables
    from seer.db.knowledge_graph_updater import get_or_create_entity_node, create_relationship_edge
except ImportError:
    # Fallback for simpler execution if the script is deep and Python can't find seer.utils
    # This assumes a certain directory structure. Best to run with `python -m` from project root.
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))) # Go up two levels to project root
    from seer.utils.supabase_client import get_supabase_client
    from seer.db.knowledge_graph_updater import get_or_create_entity_node, create_relationship_edge

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/graph",
    tags=["Knowledge Graph"],
    responses={404: {"description": "Not found"}},
)

# Helper to run sync Supabase calls in a thread pool (if needed for sync client)
async def run_sync_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

# --- Graph Population Logic (Now with Implementation) ---

async def populate_nodes_and_edges(supabase: Client):
    """
    (Background Task) Fetches data from existing structured tables 
    and populates the graph tables (graph_nodes, graph_edges).
    """
    logger.info("Background task 'populate_nodes_and_edges' started.")
    summary = {"nodes_processed_in_batch": 0, "edges_added_or_existing": 0, "threats_processed": 0, "errors": 0}
    # Use a cache just for this population run to avoid duplicate node lookups/creations
    processed_nodes_cache: Dict[tuple[str, str], Optional[str]] = {} 

    # --- Helper Functions within the task ---
    async def _ensure_node(node_type: str, node_value: str) -> Optional[str]:
        """Gets/creates a node, updates cache and summary."""
        if not node_type or not node_value: 
            logger.warning(f"Attempted to ensure node with missing type ({node_type}) or value ({node_value})")
            return None
        
        cache_key = (node_type, node_value)
        if cache_key in processed_nodes_cache:
            # Return cached ID, even if it was None (indicating previous failure)
            return processed_nodes_cache[cache_key] 
        
        node_id = await get_or_create_entity_node(supabase, node_type, node_value)
        processed_nodes_cache[cache_key] = node_id # Cache the result (ID or None)
        
        if node_id:
            # Note: This counts unique nodes processed in this batch, not necessarily *newly* created in DB
            summary["nodes_processed_in_batch"] += 1 
        else:
            # Error logged within get_or_create_entity_node
            summary["errors"] += 1
        return node_id

    async def _ensure_edge(source_id: Optional[str], target_id: Optional[str], rel_type: str, context: Optional[str] = None):
        """Creates an edge if source/target IDs are valid, updates summary."""
        if not source_id or not target_id or not rel_type: 
            logger.warning(f"Skipping edge creation due to missing data: source={source_id}, target={target_id}, type={rel_type}")
            # Don't count as error if node creation failed earlier, just skip edge
            return
        
        created_or_exists = await create_relationship_edge(supabase, source_id, target_id, rel_type, context)
        if created_or_exists:
            summary["edges_added_or_existing"] += 1 # Counts successful creations or existing edges
        else:
            # Error logged within create_relationship_edge
            summary["errors"] += 1
    # --- End Helper Functions ---

    try:
        # 1. Fetch Threats 
        # IMPORTANT: Adjust the select query based on your actual 'threats' table columns
        #            especially how actors, indicators, systems, TTPs are stored (e.g., JSONB arrays, separate tables).
        #            This example assumes they are JSONB arrays in the threats table.
        logger.info("Fetching threats from database...")
        
        def fetch_threats_sync():
             # Select fields assumed to contain linkable data
             # Consider adding .limit() or pagination for very large threats tables
             return supabase.table("threats").select(
                 "id, title, threat_type, indicators, threat_actors, affected_systems, tactics, techniques" 
             ).execute()

        threat_response = await run_sync_in_executor(fetch_threats_sync)

        # Use hasattr for safer error checking
        if hasattr(threat_response, 'error') and threat_response.error:
            logger.error(f"Error fetching threats: {threat_response.error}")
            summary["errors"] += 1
            summary["message"] = f"Failed to fetch threats: {threat_response.error}"
            logger.error(f"Graph population failed. Summary: {summary}")
            return # Stop processing if threats can't be fetched
        
        threats_data = threat_response.data if threat_response.data else []
        summary["threats_processed"] = len(threats_data)
        logger.info(f"Processing {len(threats_data)} threats...")

        # 2. Iterate and Create Nodes/Edges
        for threat in threats_data:
            threat_title = threat.get("title", f"Untitled Threat {threat.get('id')}")
            threat_type = threat.get("threat_type", "UnknownThreatType")
            
            # Ensure Threat Node (using title as value - consider if ID is better for uniqueness if titles aren't unique)
            threat_node_id = await _ensure_node("Threat", threat_title)
            if not threat_node_id: 
                logger.warning(f"Skipping relationships for threat '{threat_title}' due to node creation failure.")
                continue # Skip relationships if threat node couldn't be handled

            # Ensure Threat Type Node & Link
            threat_type_node_id = await _ensure_node("ThreatType", threat_type)
            await _ensure_edge(threat_node_id, threat_type_node_id, "has_type", f"Threat '{threat_title}' is type '{threat_type}'")

            # Process Threat Actors (Example assumes JSONB list of objects or strings)
            actors = threat.get("threat_actors")
            if isinstance(actors, list):
                for actor_data in actors:
                    # Handle both simple strings and dicts like { "name": "..." }
                    actor_name = actor_data.get("name") if isinstance(actor_data, dict) else str(actor_data)
                    if actor_name: # Ensure we have a name
                        actor_node_id = await _ensure_node("ThreatActor", actor_name)
                        # Changed relationship type to be more descriptive
                        await _ensure_edge(actor_node_id, threat_node_id, "involved_in", f"Actor '{actor_name}' involved in threat '{threat_title}'") 

            # Process Indicators (Example assumes JSONB list of objects with type/value)
            indicators = threat.get("indicators")
            if isinstance(indicators, list):
                 for ioc_data in indicators:
                    ioc_value = ioc_data.get("value") if isinstance(ioc_data, dict) else None
                    ioc_type = ioc_data.get("type", "Indicator") if isinstance(ioc_data, dict) else "Indicator"
                    if ioc_value: # Ensure we have a value
                         ioc_node_id = await _ensure_node(ioc_type, ioc_value)
                         await _ensure_edge(ioc_node_id, threat_node_id, "indicates", f"Indicator '{ioc_value}' ({ioc_type}) indicates threat '{threat_title}'")

            # Process Affected Systems (Example assumes JSONB list of objects or strings)
            systems = threat.get("affected_systems")
            if isinstance(systems, list):
                 for sys_data in systems:
                      system_name = sys_data.get("name") if isinstance(sys_data, dict) else str(sys_data)
                      if system_name: # Ensure we have a name
                           system_node_id = await _ensure_node("AffectedSystem", system_name)
                           await _ensure_edge(threat_node_id, system_node_id, "affects", f"Threat '{threat_title}' affects system '{system_name}'")

            # Process Tactics (Example assumes JSONB list of strings or objects with ID)
            tactics = threat.get("tactics")
            if isinstance(tactics, list):
                 for tactic_data in tactics:
                      # Assuming tactic data is MITRE ID like T1566 or object {"id": "T1566", ...}
                      tactic_id = tactic_data.get("id") if isinstance(tactic_data, dict) else str(tactic_data) 
                      if tactic_id: # Ensure we have an ID
                           tactic_node_id = await _ensure_node("Tactic", tactic_id)
                           await _ensure_edge(threat_node_id, tactic_node_id, "uses_tactic", f"Threat '{threat_title}' uses tactic '{tactic_id}'")
            
            # Process Techniques (Example assumes JSONB list of strings or objects with ID)
            techniques = threat.get("techniques")
            if isinstance(techniques, list):
                 for tech_data in techniques:
                      tech_id = tech_data.get("id") if isinstance(tech_data, dict) else str(tech_data)
                      if tech_id: # Ensure we have an ID
                           tech_node_id = await _ensure_node("Technique", tech_id)
                           await _ensure_edge(threat_node_id, tech_node_id, "uses_technique", f"Threat '{threat_title}' uses technique '{tech_id}'")
                           # Optional: Link Technique -> Tactic if data structure allows mapping

        summary["message"] = f"Graph population task completed processing {summary['threats_processed']} threats."
        logger.info(f"Graph population finished. Summary: {summary}")

    except Exception as e:
        logger.error(f"Unexpected error during graph population background task: {e}", exc_info=True)
        summary["errors"] += 1
        summary["message"] = f"An unexpected error occurred during population: {str(e)}"
        logger.error(f"Graph population failed. Summary: {summary}")
    # End of background task


@router.post(
    "/populate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Populate Knowledge Graph from Existing Tables",
    response_description="Population task accepted and started in the background."
)
async def trigger_graph_population(
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Triggers a background task to populate the knowledge graph tables
    (graph_nodes, graph_edges) based on data in existing structured tables
    (like threats, threat_actors, etc.).
    """
    logger.info("Received request to populate knowledge graph from existing data.")
    background_tasks.add_task(populate_nodes_and_edges, supabase)
    return {"message": "Knowledge graph population task started in the background."}


# --- Endpoint to Fetch Graph Data ---

@router.get(
    "/data",
    summary="Fetch Knowledge Graph Data",
    response_description="Nodes and edges for graph visualization."
    # Define response_model later if needed with Pydantic models
)
async def get_graph_data(
    limit: int = 1000, # Limit nodes/edges to avoid huge responses
    supabase: Client = Depends(get_supabase_client) # Use the dependency
):
    """
    Retrieves nodes and edges from the graph tables for visualization.
    """
    try:
        logger.info(f"Fetching graph data with limit {limit}...")
        
        # --- Define sync functions for DB operations --- 
        def fetch_nodes_sync():
            # Fetch nodes using the injected sync client
            return supabase.table("graph_nodes").select("id, node_type, node_value, properties").limit(limit).execute()

        def fetch_edges_sync():
            # Fetch edges using the injected sync client
            # Renaming columns in select or formatting afterwards
            return supabase.table("graph_edges").select("id, source_node_id, target_node_id, relationship_type, context, properties, weight").limit(limit).execute()
        # ----------------------------------------------

        # Run the sync Supabase calls in the executor
        nodes_response = await run_sync_in_executor(fetch_nodes_sync)
        edges_response = await run_sync_in_executor(fetch_edges_sync)

        # Check for errors after execution
        if hasattr(nodes_response, 'error') and nodes_response.error:
            logger.error(f"Error fetching graph nodes: {nodes_response.error}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch graph nodes: {nodes_response.error}")
        
        if hasattr(edges_response, 'error') and edges_response.error:
             logger.error(f"Error fetching graph edges: {edges_response.error}")
             raise HTTPException(status_code=500, detail=f"Failed to fetch graph edges: {edges_response.error}")

        # Format for frontend libraries (e.g., react-force-graph)
        formatted_nodes = [
            {"id": n["id"], "type": n["node_type"], "value": n["node_value"], **(n.get("properties") or {})}
            for n in nodes_response.data if n # Ensure n is not None
        ]
        formatted_edges = [
            {
                "id": e["id"], 
                "source": e["source_node_id"], # Map DB column to expected 'source'
                "target": e["target_node_id"], # Map DB column to expected 'target'
                "type": e["relationship_type"],
                "context": e.get("context"),
                 **(e.get("properties") or {})
            } 
            for e in edges_response.data if e # Ensure e is not None
        ]
        logger.info(f"Successfully fetched {len(formatted_nodes)} nodes and {len(formatted_edges)} edges.")
        return {"nodes": formatted_nodes, "links": formatted_edges} # 'links' is common for edge lists

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except ConnectionError as conn_err:
        # Handle cases where the client couldn't connect (e.g., from Depends)
        logger.error(f"Supabase connection error: {conn_err}")
        raise HTTPException(status_code=503, detail=f"Database connection error: {conn_err}")
    except Exception as e:
        # Catch-all for other unexpected errors
        logger.error(f"Error fetching graph data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred fetching graph data: {str(e)}") 