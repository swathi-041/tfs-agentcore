"""
Payment Agent for TFS AgentCore Runtime
Handles payment processing with NLP support
"""
import os
import sys
from typing import Dict, Any

# Import payment engine from local engines
from engines.payment_engine import process_payment, get_payment_history, get_member_info, process_natural_language_query


class PaymentAgent:
    """Payment Agent with database integration and NLP"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    def execute_action(self, action: str, params: dict) -> Dict[str, Any]:
        """
        Execute a payment action
        
        Args:
            action: Action to execute
            params: Parameters for the action
            
        Returns:
            Dict with execution result
        """
        try:
            if action == "process_payment":
                return process_payment(
                    lease_id=params.get("lease_id"),
                    amount=params.get("amount"),
                    payment_type=params.get("payment_type", "rent")
                )
            
            elif action == "get_payment_history":
                return get_payment_history(lease_id=params.get("lease_id"))
            
            elif action == "get_member_info":
                return get_member_info(
                    member_id=params.get("member_id"),
                    email=params.get("email")
                )
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Payment action failed: {str(e)}"
            }
    
    def process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """
        Process natural language payment query
        
        Args:
            query: Natural language query
            
        Returns:
            Dict with query result
        """
        try:
            return process_natural_language_query(query=query)
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"NLP query failed: {str(e)}"
            }
    
    
