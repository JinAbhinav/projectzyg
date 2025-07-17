import json
import os
from openai import OpenAI # Import the actual OpenAI library
import logging

logger = logging.getLogger(__name__)

# Ensure your OPENAI_API_KEY environment variable is set.
# The OpenAI client automatically picks it up.
# You can also set it explicitly: client = OpenAI(api_key="YOUR_KEY") but env var is better.

# Model name for GPT-3.5 Turbo
LLM_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo") 

# Global OpenAI client instance
# Initialize it once and reuse. 
# Handle potential errors during initialization if necessary.
llm_client_instance = None

def get_llm_client():
    """
    Initializes and returns the OpenAI LLM client.
    Uses a global instance to avoid re-initializing on every call.
    """
    global llm_client_instance
    if llm_client_instance is None:
        try:
            llm_client_instance = OpenAI()
            logger.info(f"OpenAI client initialized successfully for model: {LLM_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            # Depending on your error handling strategy, you might raise the exception
            # or return None and handle it in the calling function.
            raise # Re-raise for now, so issues are immediately visible
    return llm_client_instance


def build_llm_prompt(text_block: str) -> list[dict]:
    """
    Builds the prompt messages for the LLM based on the provided text block.
    """
    system_message = """You are a cybersecurity analyst assistant. Your task is to analyze the provided text and extract structured information about cyber threats.
Identify the following entity types:
- ThreatActor: (e.g., specific group names, aliases)
- Malware: (e.g., malware family names, specific variants)
- Vulnerability: (e.g., CVE identifiers like CVE-2023-XXXXX)
- Tool: (e.g., legitimate software used maliciously, hacking tools)
- Indicator: (e.g., IP addresses, domain names, file hashes, suspicious URLs)
- Target: (e.g., organizations, industries, geographic regions)
- TTP: (MITRE ATT&CK technique IDs like T1566 or descriptive phrases of tactics)

Identify the relationships between these entities. Common relationship types include:
- uses (e.g., ThreatActor uses Malware; ThreatActor uses Tool)
- targets (e.g., ThreatActor targets Organization; Malware targets Industry)
- exploits (e.g., Malware exploits Vulnerability; ThreatActor exploits Vulnerability)
- attributed_to (e.g., Malware attributed_to ThreatActor)
- hosts (e.g., IP_Indicator hosts Malware; Domain_Indicator hosts Malware_C2)
- communicates_with (e.g., Malware communicates_with Domain_Indicator)
- indicates (e.g., IP_Indicator indicates ThreatActor_Activity)
- located_in (e.g., ThreatActor located_in Country_Target)
- associated_with (a generic association if no other type fits)

For each identified relationship, provide the source entity (including its type and value), the target entity (including its type and value), the relationship type, and the original sentence or phrase from the text that provides the context for this relationship.

Return the output as a JSON object with a single key "extracted_relationships", which is a list of relationship objects. Each relationship object should have the following structure:
{
  "source_entity": { "type": "ENTITY_TYPE", "value": "entity_value" },
  "relationship_type": "RELATIONSHIP_TYPE",
  "target_entity": { "type": "ENTITY_TYPE", "value": "entity_value" },
  "context_sentence": "The sentence from the input text supporting this."
}
"""
    user_message = f"""Analyze the following text:
---
{text_block}
---"""
    
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

def extract_relationships_from_text(text_block: str) -> dict:
    """
    Uses an LLM to extract cyber threat entities and relationships from a block of text.

    Args:
        text_block: The unstructured text to analyze.

    Returns:
        A dictionary containing the extracted relationships, or an error dictionary.
    """
    try:
        llm_client = get_llm_client() # Get the initialized OpenAI client
        if not llm_client:
            # This case might occur if get_llm_client() was modified to return None on error
            # and not re-raise. For now, it re-raises, so this check might be redundant.
            logger.error("LLM client is not available.")
            return {"error": "LLM client initialization failed.", "details": "Check server logs."}
            
        messages = build_llm_prompt(text_block)

        logger.info(f"Sending request to OpenAI API with model {LLM_MODEL_NAME}. Text length: {len(text_block)}")
        response = llm_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            temperature=0.2, # Lower temperature for more deterministic JSON output
            max_tokens=2048,  # Adjusted for potentially larger JSON output with multiple relationships
            # Consider adding response_format={ "type": "json_object" } for newer GPT models that support it,
            # to help ensure the output is valid JSON.
            # For gpt-3.5-turbo, you might need to rely on strong prompting for JSON.
        )
        
        response_content_str = response.choices[0].message.content
        logger.debug(f"Raw response from OpenAI: {response_content_str}")
        
        extracted_data = json.loads(response_content_str)
        
        if "extracted_relationships" not in extracted_data or not isinstance(extracted_data["extracted_relationships"], list):
            logger.warning(f"LLM output did not contain 'extracted_relationships' list or it was not a list. Output: {extracted_data}")
            return {"error": "LLM output format error.", "details": "'extracted_relationships' key missing or not a list.", "llm_response": extracted_data}

        logger.info(f"Successfully extracted {len(extracted_data['extracted_relationships'])} relationships from text.")
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError parsing LLM response: {e}. Raw response: '{response_content_str if 'response_content_str' in locals() else 'N/A'}'", exc_info=True)
        return {"error": "Failed to parse LLM response as JSON.", "details": str(e), "raw_response": response_content_str if 'response_content_str' in locals() else 'N/A'}
    except Exception as e:
        logger.error(f"Error during LLM call or processing: {e}", exc_info=True)
        return {"error": "An unexpected error occurred during LLM interaction.", "details": str(e)}

if __name__ == '__main__':
    # Configure basic logging for testing this module directly
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # IMPORTANT: Ensure your OPENAI_API_KEY environment variable is set to run this test.
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set. Please set it to run the test.")
        exit(1)

    sample_text = (
        "The recent espionage campaign by ShadowNet Group involved their custom malware, DataThief.exe, "
        "which exploits CVE-2023-12345 to gain initial access. DataThief.exe was observed "
        "communicating with command and control server at 198.51.100.10. "
        "ShadowNet Group primarily targets financial institutions in North America. "
        "Another actor, APT42, was seen using the CobaltStrike framework against energy sectors in Europe."
    )
    
    logger.info(f"Analyzing sample text:\n{sample_text}\n")
    extraction_result = extract_relationships_from_text(sample_text)
    
    if "error" in extraction_result:
        logger.error(f"Error extracting relationships: {extraction_result['error']}")
        if extraction_result.get('details'):
            logger.error(f"Details: {extraction_result['details']}")
        if extraction_result.get('raw_response'):
            logger.error(f"Raw LLM Response: {extraction_result.get('raw_response')}")
    else:
        logger.info("Successfully extracted relationships:")
        print(json.dumps(extraction_result, indent=2))
        # Example of how you might pass to the graph updater (if it were in this file or imported)
        # from seer.db.knowledge_graph_updater import process_and_update_knowledge_graph, MockSupabaseClient
        # import asyncio
        # async def run_kg_update():
        #     mock_supabase = MockSupabaseClient() 
        #     await process_and_update_knowledge_graph(mock_supabase, extraction_result['extracted_relationships'], "sample_run_direct")
        # asyncio.run(run_kg_update()) 