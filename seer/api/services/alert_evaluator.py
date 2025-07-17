# seer/api/services/alert_evaluator.py
import logging
from typing import Dict, Any, List, Optional
from supabase import Client
from datetime import datetime
import json
import uuid # Import uuid module

# Import the centralized Supabase client utility
import os
from seer.utils.supabase_client import get_supabase_client

# Setup logging
logger = logging.getLogger(__name__)
# --- Force DEBUG level for this specific logger ---
logger.setLevel(logging.DEBUG)
# Ensure there's a handler (useful if running standalone or if root handler isn't picking up)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.debug("--- Alert Evaluator Logger configured for DEBUG --- ") # Confirmation
# ------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
LOCAL_THREAT_STORAGE_PATH = os.path.join(PROJECT_ROOT, "parsed_threats")
# --- Define path for local alert history --- 
LOCAL_ALERT_HISTORY_PATH = os.path.join(PROJECT_ROOT, "triggered_alerts.jsonl") 
# -----------------------------------------

def evaluate_data_against_rules(input_data: Dict[str, Any], data_type: str = 'threat'):
    """
    Evaluates input data against active alert rules and logs history if matched.

    Args:
        input_data: A dictionary containing the data to evaluate (e.g., a parsed threat).
                    Expected structure depends on data_type.
        data_type: A string indicating the type of data ('threat', 'network_event', etc.).
                   Used to determine how to extract relevant fields for evaluation.
    """
    try:
        supabase = get_supabase_client()

        # 1. Fetch active alert rules
        rules_response = supabase.table("alert_rules")\
            .select("*")\
            .eq("enabled", True)\
            .execute()

        if hasattr(rules_response, 'error') and rules_response.error:
            logger.error(f"[Alert Evaluator] Failed to fetch rules: {rules_response.error.message}")
            return # Cannot evaluate without rules

        active_rules: List[Dict[str, Any]] = rules_response.data if rules_response.data else []
        if not active_rules:
            # logger.info("[Alert Evaluator] No active alert rules found.")
            return # No active rules to check against

        # Log the fetched rules and the start of evaluation
        logger.debug(f"[Alert Evaluator] Fetched rules data: {active_rules}")
        logger.info(f"[Alert Evaluator] Evaluating data against {len(active_rules)} active rules.")

        # Log rules list with the specific logger
        logger.debug(f"[Alert Evaluator] Rules list before loop: {active_rules}")

        matched_rules = []

        # 2. Iterate through rules and evaluate conditions
        for rule in active_rules:
            # Use the configured logger
            logger.debug(f"---> Entering loop for Rule ID: {rule.get('id')}") 
            logger.debug(f"--- Evaluating Rule ID: {rule.get('id')}, Name: {rule.get('name')} ---")
            logger.debug(f"Rule Config: {rule}")
            logger.debug(f"Input Data Keys: {list(input_data.keys())}")
            
            rule_type = rule.get('type')
            conditions = rule.get('condition_config', {})
            rule_matched = False

            # --- Evaluation logic based on rule type ---
            if rule_type == 'severity_confidence' and data_type == 'threat':
                # Example: Check threat severity and confidence
                rule_severity = conditions.get('severity') # e.g., 'HIGH', 'CRITICAL'
                rule_confidence = conditions.get('confidence') # e.g., 75 (percent)
                data_severity = input_data.get('severity')
                data_confidence = input_data.get('confidence')

                # Convert rule_confidence to float for safe comparison
                try:
                    rule_confidence_float = float(rule_confidence) if rule_confidence is not None else None
                except (ValueError, TypeError):
                    logger.warning(f"[Rule {rule['id']}] Could not convert rule confidence '{rule_confidence}' to float. Skipping comparison.")
                    rule_confidence_float = None

                # --- Normalize data_confidence (0.0-1.0) to percentage (0-100) ---
                data_confidence_percent = None
                if data_confidence is not None:
                    try:
                        data_confidence_percent = float(data_confidence) * 100.0
                    except (ValueError, TypeError):
                        logger.warning(f"[Rule {rule['id']}] Could not convert data confidence '{data_confidence}' to float percentage.")
                # -------------------------------------------------------------------

                logger.debug(f"[Rule {rule['id']}] Sev/Conf Check: RuleSev='{rule_severity}', RuleConf={rule_confidence_float} | DataSev='{data_severity}', DataConf={data_confidence_percent}") # Use logger, show normalized data conf

                # Define severity order (adjust as needed)
                severity_order = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}

                # --- Refactored Condition Check --- 
                severity_match = False
                confidence_match = False

                # Check severity if both rule and data have it
                if rule_severity and data_severity:
                    data_sev_val = severity_order.get(data_severity.upper(), 0)
                    rule_sev_val = severity_order.get(rule_severity.upper(), 0)
                    if data_sev_val >= rule_sev_val:
                        severity_match = True
                        logger.debug(f"[Rule {rule['id']}] Severity condition met: DataVal({data_sev_val}) >= RuleVal({rule_sev_val})")
                elif not rule_severity:
                    severity_match = True # If rule doesn't specify severity, it passes

                # Check confidence if both rule and data have it (use normalized percentage)
                if rule_confidence_float is not None and data_confidence_percent is not None:
                    if data_confidence_percent >= rule_confidence_float:
                        confidence_match = True
                        logger.debug(f"[Rule {rule['id']}] Confidence condition met: DataVal({data_confidence_percent}) >= RuleVal({rule_confidence_float})")
                elif rule_confidence_float is None:
                    confidence_match = True # If rule doesn't specify confidence, it passes

                # Rule matches if BOTH defined conditions are met (or if a condition wasn't defined in the rule)
                if severity_match and confidence_match:
                    rule_matched = True
                    logger.info(f"[Alert Evaluator] Matched rule ID {rule['id']} (severity_confidence) - Conditions Met (SevOK={severity_match}, ConfOK={confidence_match})")
                # ------------------------------------
            
            elif rule_type == 'ioc_match' and data_type == 'threat':
                # Example: Check if threat justification/content contains IOC pattern
                # This is simplified - real IOC matching would be more complex (e.g., regex on specific fields)
                ioc_pattern = conditions.get('ioc_value')
                # Assuming IOCs might be in 'justification' or a dedicated 'iocs' field
                search_text = input_data.get('justification', '') + " " + str(input_data.get('iocs', [])) 
                
                logger.debug(f"[Rule {rule['id']}] IOC Check: RulePattern={ioc_pattern} | SearchText Length={len(search_text)}")

                if ioc_pattern and ioc_pattern in search_text: # Simple substring match for demo
                    rule_matched = True
                    logger.info(f"[Alert Evaluator] Matched rule ID {rule['id']} (ioc_match) - Condition Met: Found '{ioc_pattern}'")

            # --- Add more rule type evaluations here (network_anomaly, specific_threat) ---
            elif rule_type == 'specific_threat' and data_type == 'threat':
                 threat_name_condition = conditions.get('threat_name')
                 data_category = input_data.get('category') # Assuming threat category field exists
                 logger.debug(f"[Rule {rule['id']}] Specific Threat Check: RuleThreatName={threat_name_condition} | DataCategory={data_category}")
                 if threat_name_condition and data_category and \
                    threat_name_condition.lower() in data_category.lower():
                     rule_matched = True
                     logger.info(f"[Alert Evaluator] Matched rule ID {rule['id']} (specific_threat) - Condition Met: '{threat_name_condition}' found in '{data_category}'")

            # --- Log if rule did not match ---
            if not rule_matched:
                logger.debug(f"[Rule {rule['id']}] No conditions met for this rule.")

            # --- If rule matched, prepare history record ---
            if rule_matched:
                # Simplify details stored for now
                simple_details = {
                    "source_url": input_data.get('source_url'),
                    "title": input_data.get('title')
                }
                history_record = {
                    "id": str(uuid.uuid4()), # Generate a unique string ID
                    "rule_id": rule['id'],
                    "rule_name_snapshot": rule.get('name', 'Unnamed Rule') or 'Unnamed Rule',
                    "triggered_at": datetime.utcnow().isoformat(), # Use ISO format with TZ for Supabase Timestamptz
                    "severity": input_data.get('severity') if data_type == 'threat' else None,
                    "alert_type": rule_type,
                    "summary": f"Rule '{rule.get('name')}' triggered by {data_type}", # Basic summary
                    "details": simple_details, # Store simplified details
                    "acknowledged": False
                }
                matched_rules.append(history_record)

        # 3. Insert matched rules into history table
        # --- Remove Supabase insert --- 
        # if matched_rules:
        #     logger.info(f"[Alert Evaluator] Inserting {len(matched_rules)} records into alert_history.")
        #     insert_response = supabase.table("alert_history").insert(matched_rules).execute()
        #     if hasattr(insert_response, 'error') and insert_response.error:
        #          logger.error(f"[Alert Evaluator] Failed to insert alert history: {insert_response.error.message}")
        #     else:
        #          logger.info(f"[Alert Evaluator] Successfully inserted alert history records.")
        # --------------------------

        # --- Append matched rules to local file --- 
        if matched_rules:
            try:
                # Ensure directory exists (though PROJECT_ROOT should exist)
                os.makedirs(os.path.dirname(LOCAL_ALERT_HISTORY_PATH), exist_ok=True)
                
                with open(LOCAL_ALERT_HISTORY_PATH, 'a', encoding='utf-8') as f:
                    for record in matched_rules:
                        # Ensure datetime objects are serialized correctly if any remain
                        # (triggered_at is already isoformat string which is good)
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n') # Write each record as a new line
                logger.info(f"[Alert Evaluator] Appended {len(matched_rules)} records to {LOCAL_ALERT_HISTORY_PATH}")
            except Exception as file_err:
                logger.error(f"[Alert Evaluator] Failed to write alert history to local file: {file_err}")
        # ----------------------------------------

    except Exception as e:
        logger.exception(f"[Alert Evaluator] Error during evaluation: {e}")

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    print("Testing Alert Evaluator...")
    # Example threat data matching a potential rule
    mock_threat = {
        'id': 123,
        'category': 'Ransomware',
        'severity': 'CRITICAL', # Should match HIGH or CRITICAL severity rules
        'confidence': 95.0, # Should match confidence >= 90 rules
        'potential_targets': ['Finance'],
        'justification': 'Detected critical LockBit variant IOC: example.com/payload.exe', # Contains an IOC pattern
        'created_at': '2023-11-10T10:00:00Z',
        'iocs': ['example.com/payload.exe']
    }
    
    # Make sure Supabase env vars are set or client is configured via utils/config.py
    evaluate_data_against_rules(mock_threat, data_type='threat')
    print("Evaluation test finished.") 