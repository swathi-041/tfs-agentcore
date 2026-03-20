"""
Payment Engine for TFS AgentCore Runtime
Complete payment processing with mock data and NLP support
"""

import os
import uuid
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== MOCK DATA ====================
MOCK_MEMBERS = {
    "MEM-001": {"member_id": "MEM-001", "name": "John Smith", "email": "john.smith@email.com", "phone": "+1-555-0101", "address": "123 Main St, New York, NY 10001"},
    "MEM-002": {"member_id": "MEM-002", "name": "Sarah Johnson", "email": "sarah.j@email.com", "phone": "+1-555-0102", "address": "456 Oak Ave, Los Angeles, CA 90001"},
    "MEM-003": {"member_id": "MEM-003", "name": "Michael Chen", "email": "m.chen@email.com", "phone": "+1-555-0103", "address": "789 Pine Rd, Chicago, IL 60601"},
    "MEM-004": {"member_id": "MEM-004", "name": "Emily Davis", "email": "emily.d@email.com", "phone": "+1-555-0104", "address": "321 Elm St, Houston, TX 77001"},
    "MEM-005": {"member_id": "MEM-005", "name": "Robert Wilson", "email": "r.wilson@email.com", "phone": "+1-555-0105", "address": "654 Maple Dr, Phoenix, AZ 85001"},
}

MOCK_LEASES = {
    "LSE-100": {"member_id": "MEM-001", "property_address": "100 Property Road, City 1, ST 10000", "rent_amount": 1200.0},
    "LSE-101": {"member_id": "MEM-002", "property_address": "101 Property Road, City 2, ST 10001", "rent_amount": 1300.0},
    "LSE-102": {"member_id": "MEM-003", "property_address": "102 Property Road, City 3, ST 10002", "rent_amount": 1400.0},
    "LSE-103": {"member_id": "MEM-004", "property_address": "103 Property Road, City 4, ST 10003", "rent_amount": 1500.0},
    "LSE-104": {"member_id": "MEM-005", "property_address": "104 Property Road, City 5, ST 10004", "rent_amount": 1600.0},
}

MOCK_PAYMENTS = {
    "LSE-100": [
        {"transaction_id": "TXN-MOCK001", "amount": 1200.0, "payment_type": "rent", "payment_date": "2026-01-15T10:00:00", "status": "completed"},
        {"transaction_id": "TXN-MOCK002", "amount": 1200.0, "payment_type": "rent", "payment_date": "2025-12-15T10:00:00", "status": "completed"}
    ],
    "LSE-101": [
        {"transaction_id": "TXN-MOCK003", "amount": 1300.0, "payment_type": "rent", "payment_date": "2026-01-20T10:00:00", "status": "completed"}
    ]
}

def get_mock_member(member_id: str = None, email: str = None):
    if member_id and member_id in MOCK_MEMBERS:
        return {"status": "success", **MOCK_MEMBERS[member_id], "mock_data": True}
    elif email:
        for mid, member_info in MOCK_MEMBERS.items():
            if member_info["email"] == email:
                return {"status": "success", "member_id": mid, **member_info, "mock_data": True}
    return {"status": "error", "error": "Member not found", "mock_data": True}

def get_mock_lease(lease_id: str):
    if lease_id in MOCK_LEASES:
        return {"status": "success", "lease_id": lease_id, **MOCK_LEASES[lease_id], "mock_data": True}
    return {"status": "error", "error": "Lease not found", "mock_data": True}

def get_mock_payment_history(lease_id: str):
    if lease_id in MOCK_PAYMENTS:
        history = [{"date": p["payment_date"], "amount": p["amount"], "type": p["payment_type"], "status": p["status"], "transaction_id": p["transaction_id"]} for p in MOCK_PAYMENTS[lease_id]]
        return {"status": "success", "lease_id": lease_id, "history": history, "total_records": len(history), "mock_data": True}
    return {"status": "error", "error": "No payment history found", "mock_data": True}

def create_mock_payment(lease_id: str, amount: float, payment_type: str = "rent"):
    transaction_id = f"TXN-MOCK{uuid.uuid4().hex[:6].upper()}"
    new_payment = {"transaction_id": transaction_id, "amount": amount, "payment_type": payment_type, "payment_date": datetime.now().isoformat(), "status": "completed"}
    
    if lease_id not in MOCK_PAYMENTS:
        MOCK_PAYMENTS[lease_id] = []
    MOCK_PAYMENTS[lease_id].append(new_payment)
    
    return {
        "status": "success", "transaction_id": transaction_id, "lease_id": lease_id,
        "member_id": MOCK_LEASES[lease_id]["member_id"], "amount": amount, "payment_type": payment_type,
        "payment_date": new_payment["payment_date"], "message": f"Successfully processed {payment_type} payment of ${amount}", "mock_data": True
    }

# ==================== AWS LLM ====================
import boto3

class AWSLLMProcessor:
    def __init__(self):
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            self.model_id = os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-lite-v1:0')
            self.available = True
        except Exception:
            self.available = False
    
    def understand_query(self, user_input: str) -> Dict[str, Any]:
        if self.available:
            try:
                return self._extract_with_llm(user_input)
            except Exception:
                return self._extract_with_keywords(user_input)
        else:
            return self._extract_with_keywords(user_input)
    
    def _extract_with_llm(self, user_input: str) -> Dict[str, Any]:
        prompt = f"""
        Extract payment information from this user query: "{user_input}"
        
        Return a JSON object with these fields:
        - action: one of "process_payment", "get_payment_history", "get_member_info"
        - lease_id: lease ID if mentioned (format like LSE-123)
        - amount: payment amount if mentioned (number only)
        - payment_type: one of "rent", "deposit", "fee"
        - member_info: member identifier (email or name) if mentioned
        
        IMPORTANT: 
        - If "history" is mentioned, ALWAYS use "get_payment_history" regardless of other words
        - If "pay" or "payment" is mentioned WITHOUT "history", use "process_payment"
        - If "balance", "owe", or "due" is mentioned, use "get_payment_history"
        
        Examples:
        "Pay rent for lease LSE-100" -> {{"action": "process_payment", "lease_id": "LSE-100", "amount": null, "payment_type": "rent", "member_info": null}}
        "Show payment history for LSE-101" -> {{"action": "get_payment_history", "lease_id": "LSE-101", "amount": null, "payment_type": null, "member_info": null}}
        "Get all payment history of LSE-100" -> {{"action": "get_payment_history", "lease_id": "LSE-100", "amount": null, "payment_type": null, "member_info": null}}
        "What's my balance for lease LSE-102" -> {{"action": "get_payment_history", "lease_id": "LSE-102", "amount": null, "payment_type": null, "member_info": null}}
        "Info for john.smith@email.com" -> {{"action": "get_member_info", "lease_id": null, "amount": null, "payment_type": null, "member_info": "john.smith@email.com"}}
        """
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {"maxTokens": 300, "topP": 0.9, "temperature": 0.3}
            })
        )
        
        response_body = json.loads(response['body'].read())
        extracted_text = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '{}')
        
        try:
            json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {k: v for k, v in result.items() if v is not None}
            else:
                raise ValueError("No JSON found in LLM response")
        except Exception:
            return self._extract_with_keywords(user_input)
    
    def _extract_with_keywords(self, user_input: str) -> Dict[str, Any]:
        user_input_lower = user_input.lower()
        
        # Enhanced lease ID extraction - multiple patterns
        lease_id = None
        lease_patterns = [
            r'lease\s+(lse-\d+)',  # "lease LSE-100"
            r'(lse-\d+)',          # "LSE-100" standalone
            r'lease\s+id\s+(lse-\d+)',  # "lease id LSE-100"
            r'lease\s*#?\s*(lse-\d+)',   # "lease # LSE-100"
            r'for\s+(lse-\d+)',    # "for LSE-100"
            r'account\s+(lse-\d+)', # "account LSE-100"
        ]
        
        for pattern in lease_patterns:
            lease_match = re.search(pattern, user_input_lower)
            if lease_match:
                lease_id = lease_match.group(1).upper()
                break
        
        # Enhanced amount extraction
        amount = None
        amount_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # "$1200.00"
            r'(\d{3,4}\.?\d*)',      # "1200" or "1200.00"
            r'amount\s+(\d+(?:\.\d{2})?)',  # "amount 1200"
            r'pay\s+(\d+(?:\.\d{2})?)',    # "pay 1200"
        ]
        
        for pattern in amount_patterns:
            amount_match = re.search(pattern, user_input_lower)
            if amount_match:
                try:
                    amount = float(amount_match.group(1))
                    if amount > 0:  # Valid amount
                        break
                except ValueError:
                    continue
        
        # Enhanced payment type detection
        payment_type = "rent"  # default
        if "deposit" in user_input_lower:
            payment_type = "deposit"
        elif "fee" in user_input_lower or "fees" in user_input_lower:
            payment_type = "fee"
        elif "rent" in user_input_lower:
            payment_type = "rent"
        
        # Enhanced member info extraction
        member_info = None
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input_lower)
        if email_match:
            member_info = email_match.group()
        
        # Extract member ID (MEM-XXX format)
        member_id_match = re.search(r'(mem-\d+)', user_input_lower)
        if member_id_match:
            member_info = member_id_match.group(1).upper()
        
        # Also check for member ID in different patterns
        if not member_info:
            member_id_match = re.search(r'\b(MEM-\d+)\b', user_input.upper())
            if member_id_match:
                member_info = member_id_match.group(1)
        
        # Action detection - improved priority order
        action = "get_payment_history"  # default
        
        # Check for history first (highest priority for payment-related queries)
        if "history" in user_input_lower:
            action = "get_payment_history"
        # Check for balance/owe/due queries
        elif "balance" in user_input_lower or "owe" in user_input_lower or "due" in user_input_lower:
            action = "get_payment_history"
        # Check for payment processing - but only if not history
        elif ("pay" in user_input_lower and "history" not in user_input_lower) or \
             ("payment" in user_input_lower and "history" not in user_input_lower):
            action = "process_payment"
        # Check for member info
        elif "member" in user_input_lower or "info" in user_input_lower or "information" in user_input_lower:
            action = "get_member_info"
        
        # Special handling for balance queries without lease ID
        if not lease_id and ("balance" in user_input_lower or "owe" in user_input_lower):
            # Try to find any lease ID in the query
            any_lease_match = re.search(r'(lse-\d+)', user_input_lower)
            if any_lease_match:
                lease_id = any_lease_match.group(1).upper()
        
        return {
            "action": action,
            "lease_id": lease_id,
            "amount": amount,
            "payment_type": payment_type,
            "member_info": member_info
        }
    
    def generate_response(self, result: Dict[str, Any], action: str) -> str:
        if not self.available:
            return self._generate_fallback_response(result, action)
        
        try:
            prompt = f"""
            Generate a user-friendly response for the following payment processing result:
            
            Action: {action}
            Result: {json.dumps(result, indent=2)}
            
            IMPORTANT: Use the ACTUAL amounts from the database result, not any other amounts.
            For payment processing, use the "amount" field from the result.
            For payment history, use the actual payment amounts from the history.
            Include the "rent_amount" field if available (this is the expected monthly rent).
            
            Make the response professional and clear. Include relevant details like transaction IDs,
            amounts, and next steps if applicable. Keep it concise and helpful.
            """
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {"maxTokens": 200, "topP": 0.9, "temperature": 0.7}
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            # Safe response parsing with multiple fallbacks
            try:
                content_list = response_body.get('output', {}).get('message', {}).get('content', [])
                if content_list and len(content_list) > 0:
                    generated_text = content_list[0].get('text', '')
                else:
                    generated_text = ''
            except (KeyError, IndexError, TypeError):
                generated_text = ''
            
            if generated_text and generated_text.strip():
                return generated_text.strip()
            else:
                return self._generate_fallback_response(result, action)
                
        except Exception:
            return self._generate_fallback_response(result, action)
    
    def _generate_fallback_response(self, result: Dict[str, Any], action: str) -> str:
        if result.get("status") == "success":
            if action == "process_payment":
                return f"Payment processed successfully! Transaction ID: {result.get('transaction_id', 'N/A')}. Amount: ${result.get('amount', 0)} for lease {result.get('lease_id', 'N/A')}."
            elif action == "get_payment_history":
                count = result.get("total_records", 0)
                return f"Found {count} payment records for lease {result.get('lease_id', 'N/A')}."
            elif action == "get_member_info":
                return f"Member information retrieved for {result.get('name', 'N/A')} ({result.get('email', 'N/A')})."
        else:
            return f"Error: {result.get('error', 'Unknown error occurred')}"
        
        return "Operation completed."

# Initialize LLM processor
llm_processor = AWSLLMProcessor()

# ==================== PAYMENT PROCESSING FUNCTIONS ====================
def process_payment(lease_id: str, amount: float = None, payment_type: str = "rent") -> dict:
    try:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        
        # Use mock data for standalone runtime
        mock_lease = get_mock_lease(lease_id)
        if mock_lease["status"] == "success":
            # Use database rent amount if no amount specified
            if amount is None:
                amount = mock_lease["rent_amount"]
            
            mock_result = create_mock_payment(lease_id, amount, payment_type)
            mock_result["database"] = False
            # Add transaction_id and member_id like the backend
            mock_result["transaction_id"] = transaction_id
            mock_result["member_id"] = mock_lease.get("member_id", "MEM-001")
            mock_result["rent_amount"] = mock_lease["rent_amount"]
            return mock_result
        else:
            return mock_lease
            
    except Exception:
        return create_mock_payment(lease_id, amount or 1200.0, payment_type)

def get_payment_history(lease_id: str) -> dict:
    try:
        mock_history = get_mock_payment_history(lease_id)
        mock_history["database"] = False
        return mock_history
            
    except Exception:
        mock_history = get_mock_payment_history(lease_id)
        mock_history["database"] = False
        return mock_history

def get_member_info(member_id: str = None, email: str = None) -> dict:
    try:
        return get_mock_member(member_id, email)
            
    except Exception:
        return get_mock_member(member_id, email)

def process_natural_language_query(query: str) -> dict:
    try:
        extracted_info = llm_processor.understand_query(query)
        
        if extracted_info.get("error"):
            return {"status": "error", "error": "Failed to understand query", "details": extracted_info["error"]}
        
        action = extracted_info.get("action", "process_payment")
        
        if action == "process_payment":
            if not extracted_info.get("lease_id"):
                return {"status": "error", "error": "Missing lease ID. Please specify lease ID (e.g., LSE-100)"}
            
            result = process_payment(
                lease_id=extracted_info["lease_id"],
                amount=extracted_info.get("amount"),  # Let process_payment handle amount logic
                payment_type=extracted_info.get("payment_type", "rent")
            )
            
            if result["status"] == "success":
                result["extracted_info"] = extracted_info
                result["response"] = llm_processor.generate_response(result, action)
            
            return result
            
        elif action == "get_payment_history":
            if not extracted_info.get("lease_id"):
                return {"status": "error", "error": "Missing lease ID. Please specify lease ID (e.g., LSE-100)"}
            
            result = get_payment_history(extracted_info["lease_id"])
            if result["status"] == "success":
                result["extracted_info"] = extracted_info
                result["response"] = llm_processor.generate_response(result, action)
            
            return result
            
        elif action == "get_member_info":
            member_info = extracted_info.get("member_info")
            if not member_info:
                return {"status": "error", "error": "Missing member information. Please provide email or member ID"}
            
            if "@" in member_info:
                result = get_member_info(email=member_info)
            else:
                result = get_member_info(member_id=member_info)
            
            if result["status"] == "success":
                result["extracted_info"] = extracted_info
                result["response"] = llm_processor.generate_response(result, action)
            
            return result
            
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}
