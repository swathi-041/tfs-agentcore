"""
Master Agent for TFS AgentCore Runtime
Orchestrates requests using local agent dispatch instead of HTTP calls
"""
import os
import json
import re
import asyncio
from typing import Dict, Any

# Import local agents
from .qna_agent import QnAAgent
from .planner_agent import PlannerAgent
from .lease_agent import LeaseAgent
from .payment_agent import PaymentAgent

# Import form fill tool from local tools
from tools.form_fill_tool import form_fill_tool


class MasterAgent:
    """Master Orchestrator with local agent dispatch"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.bedrock = None
        
        # Initialize local agents
        self.agents = {
            "qna_agent": QnAAgent(config),
            "planner_agent": PlannerAgent(config),
            "lease_agent": LeaseAgent(config),
            "payment_agent": PaymentAgent(config)
        }
        
        # Initialize Bedrock for intent classification
        try:
            import boto3
            self.bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=config["AWS_REGION"]
            )
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock: {e}")
    
    def classify_query_with_bedrock(self, query: str) -> str:
        """
        Classify query using Bedrock for intelligent routing
        
        Args:
            query: User query
            
        Returns:
            Route string (qna, planner, lease, payment, form)
        """
        if not self.bedrock:
            # Fallback to simple keyword-based routing
            return self._fallback_classification(query)
        
        prompt = f"""
You are a routing classifier for Toyota Financial Services.

Classify the user query into exactly one route:

- qna → informational, FAQ, policy, how-to
- planner → mixed intent, multi-step, buyout + explanation, exchange + explanation, informational + lease action
- lease → direct lease calculation ONLY (keywords: lease, buyout, exchange, calculate, terminate)
- payment → payment-only request
- form → odometer statement / form fill / document generation (keywords: form, fill, odometer, statement, generate)

IMPORTANT:
If query contains BOTH informational question (what/how/why/explain) AND lease action (buyout/exchange/calculate/terminate), route to planner instead of lease.

Examples:
- "what is tfs and calculate buyout for LSE-12345" → planner
- "what are my lease options and calculate exchange" → planner
- "calculate buyout for LSE-12345" → lease
- "exchange my lease LSE-12345" → lease  
- "lease termination LSE-12345" → lease
- "what are my lease options" → qna
- "generate odometer statement" → form

Return ONLY JSON:
{{"route":"lease"}}
{{"route":"qna"}}
{{"route":"payment"}}
{{"route":"form"}}
{{"route":"planner"}}

User Query: {query}
"""

        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0
            }
        }

        try:
            response = self.bedrock.invoke_model(
                modelId=self.config["BEDROCK_MODEL_ID"],
                body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())
            text_output = response_body["output"]["message"]["content"][0]["text"].strip()
            text_output = text_output.replace("```json", "").replace("```", "").strip()
            
            print("[DEBUG] Bedrock raw classifier output:", text_output)
            
            try:
                parsed = json.loads(text_output)
                return parsed.get("route", "planner")
            except Exception as e:
                print(f"[ERROR] Classification parse failed: {text_output}")
                return "planner"
        
        except Exception as e:
            print(f"[ERROR] Bedrock classification failed: {e}")
            return self._fallback_classification(query)
    
    def _fallback_classification(self, query: str) -> str:
        """Fallback classification using keyword matching"""
        query_lower = query.lower()
        
        # Form fill detection - more specific patterns
        form_patterns = [
            "odometer statement",
            "form fill", 
            "fill form",
            "generate statement",
            "generate odometer",
            "lease statement"
        ]
        
        if any(pattern in query_lower for pattern in form_patterns):
            return "form"
        
        # Lease calculation detection - check before general keywords
        lease_keywords = ["lease", "buyout", "exchange", "calculate", "terminate"]
        if any(keyword in query_lower for keyword in lease_keywords):
            # But don't classify as lease if it's asking for information about lease options
            if not any(info_word in query_lower for info_word in ["what are", "options", "about", "explain", "tell me about"]):
                return "lease"
        
        # Payment detection
        payment_keywords = ["payment", "pay", "bill", "invoice", "transaction"]
        if any(keyword in query_lower for keyword in payment_keywords):
            return "payment"
        
        # Informational detection - question words and informational queries
        question_words = ["what", "how", "where", "when", "why", "options", "benefits"]
        informational_phrases = ["what are", "tell me about", "explain", "information about"]
        
        if any(word in query_lower for word in question_words) or any(phrase in query_lower for phrase in informational_phrases):
            return "qna"
        
        # Default to planner for complex/unknown queries
        return "planner"
    
    def extract_lease_params(self, query: str) -> dict:
        """Extract lease parameters from natural language query"""
        lease_id_match = re.search(r"(LSE-\d+)", query, re.IGNORECASE)

        condition_match = re.search(
            r"\b(excellent|good|fair|poor)\b",
            query,
            re.IGNORECASE
        )

        # Remove lease id first so digits inside lease id do not interfere
        query_without_lease = re.sub(r"LSE-\d+", "", query, flags=re.IGNORECASE)

        miles_match = re.search(r"\b(\d{2,6})\b", query_without_lease)

        lease_id = lease_id_match.group(1) if lease_id_match else None
        miles = int(miles_match.group(1)) if miles_match else None
        condition = condition_match.group(1).lower() if condition_match else None

        print(f"[DEBUG] Lease params: lease_id={lease_id}, miles={miles}, condition={condition}")

        return {
            "lease_id": lease_id,
            "current_odometer": miles,
            "condition": condition
        }
    
    def extract_form_data(self, query: str) -> tuple:
        """
        Extract form data from natural language query using non-greedy patterns
        
        Returns:
            Tuple of (form_data_dict, confirm_signature_bool)
        """
        patterns = {
            "name": r"Name:\s*(.*?)\s+VIN:",
            "vin": r"VIN:\s*(.*?)\s+Account number:",
            "account_number": r"Account number:\s*(.*?)\s+Make:",
            "make": r"Make:\s*(.*?)\s+Model:",
            "model": r"Model:\s*(.*?)\s+Body type:",
            "body_type": r"Body type:\s*(.*?)\s+Year:",
            "year": r"Year:\s*(.*?)\s+Miles:",
            "miles": r"Miles:\s*(.*?)\s+Date:",
            "date": r"Date:\s*(.*?)\s+Address:",
            "address": r"Address:\s*(.*?)(?:\s+confirm_signature:|$)"
        }

        form_data = {}

        for field, pattern in patterns.items():
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                form_data[field] = match.group(1).strip()

        confirm_signature = "confirm_signature: true" in query.lower()

        return form_data, confirm_signature
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query through appropriate agent
        
        Args:
            query: User query string
            
        Returns:
            Dict with response
        """
        try:
            # Classify query intent
            route = self.classify_query_with_bedrock(query)
            print(f"[DEBUG] Route classified as: {route}")

            # Route to appropriate handler
            if route == "form":
                return await self._handle_form_request(query)
            
            elif route == "lease":
                return await self._handle_lease_request(query)
            
            elif route == "payment":
                return await self._handle_payment_request(query)
            
            elif route == "qna":
                return await self._handle_qna_request(query)
            
            elif route == "planner":
                return await self._handle_planner_request(query)
            
            else:
                return {
                    "error": f"Unknown route: {route}",
                    "answer": "I'm sorry, I couldn't understand how to process your request."
                }
        
        except Exception as e:
            return {
                "error": f"Query processing failed: {str(e)}",
                "answer": "I'm sorry, there was an error processing your request."
            }
    
    async def _handle_form_request(self, query: str) -> Dict[str, Any]:
        """Handle form fill requests"""
        try:
            form_data, confirm_signature = self.extract_form_data(query)

            if not form_data:
                form_data = {
                    "name": "Sample User",
                    "vin": "1HGBH41JXMN109186",
                    "account_number": "ACC-789456",
                    "make": "Toyota",
                    "model": "Camry",
                    "body_type": "Sedan",
                    "year": "2022",
                    "miles": "36000",
                    "date": "03/17/2026",
                    "address": "123 Main Street, New York, NY 10001"
                }

            result = form_fill_tool(form_data, confirm_signature)

            if result.get("status") == "success":
                return {
                    "answer": (
                        "Your odometer statement has been generated successfully.\n"
                        f"Download here: {result.get('download_url')}"
                    )
                }

            if result.get("status") == "error":
                return {
                    "answer": f"Form generation failed: {result.get('message')}"
                }

            return result

        except Exception as e:
            return {"error": f"Form fill error: {str(e)}"}
    
    async def _handle_lease_request(self, query: str) -> Dict[str, Any]:
        """Handle lease calculation requests"""
        try:
            params = self.extract_lease_params(query)
            
            # Select correct action based on query content
            if "buyout" in query.lower() or "payoff" in query.lower():
                action = "calculate_buyout"
                params = {
                    "lease_id": params.get("lease_id"),
                    "current_odometer": params.get("current_odometer")
                }

            elif "exchange" in query.lower() or "trade-in" in query.lower():
                action = "calculate_exchange"
                params = {
                    "lease_id": params.get("lease_id"),
                    "current_odometer": params.get("current_odometer"),
                    "condition": params.get("condition")
                }

            elif "terminate" in query.lower() or "termination" in query.lower():
                action = "terminate_lease"

            elif "lease detail" in query.lower() or "lease details" in query.lower():
                action = "get_lease_details"
                params = {
                    "lease_id": params.get("lease_id")
                }

            else:
                action = "calculate_buyout"
                params = {
                    "lease_id": params.get("lease_id"),
                    "current_odometer": params.get("current_odometer")
                }
            
            print("[DEBUG] Lease payload:", {"action": action, "params": params})
            
            # Execute lease action
            print(f"[DEBUG] About to call lease agent with action={action}, params={params}")
            try:
                result = await self.agents["lease_agent"].execute_action(action, params)
                print(f"[DEBUG] Lease agent returned: {result}")
            except Exception as e:
                print(f"[DEBUG] Lease agent exception: {str(e)}")
                import traceback
                traceback.print_exc()
                return {"error": f"Lease agent execution failed: {str(e)}"}
            
            if result.get("status") == "success" and result.get("explanation"):
                return {"answer": result["explanation"]}
            elif result.get("status") == "success" and result.get("message"):
                return {"answer": result["message"]}
            elif result.get("status") == "success":
                # Return the result directly if no explanation was generated
                return {"answer": str(result.get("result", result))}
            elif result.get("message"):
                return {"answer": result["message"]}
            
            return result

        except Exception as e:
            return {"error": f"Lease calculation error: {str(e)}"}
    
    async def _handle_payment_request(self, query: str) -> Dict[str, Any]:
        """Handle payment requests"""
        try:
            result = self.agents["payment_agent"].process_natural_language_query(query)
            
            if result.get("status") == "success":
                # Check for response field first (payment engine), then message field
                answer = result.get("response") or result.get("message") or "Payment request processed."
                return {"answer": answer}
            
            return result

        except Exception as e:
            return {"error": f"Payment processing error: {str(e)}"}
    
    async def _handle_qna_request(self, query: str) -> Dict[str, Any]:
        """Handle Q&A requests"""
        try:
            result = self.agents["qna_agent"].ask_question(query)
            
            if result.get("answer"):
                return {"answer": result["answer"]}
            
            return result

        except Exception as e:
            return {"error": f"Q&A processing error: {str(e)}"}
    
    async def _handle_planner_request(self, query: str) -> Dict[str, Any]:
        """Handle complex planner requests"""
        try:
            # Generate plan
            plan_result = self.agents["planner_agent"].generate_plan(query)
            
            if "error" in plan_result:
                return {"error": plan_result["error"]}
            
            # Execute plan locally
            execution_result = self.agents["planner_agent"].execute_plan_locally(
                plan_result, 
                self.agents
            )
            
            if "error" in execution_result:
                return {"error": execution_result["error"]}
            
            # Format response
            execution_results = execution_result.get("execution_results", [])
            if execution_results:
                # Combine all successful responses
                answers = []
                for step_result in execution_results:
                    response = step_result.get("response", {})
                    if response.get("answer"):
                        answers.append(response["answer"])
                    elif response.get("explanation"):
                        answers.append(response["explanation"])
                    elif response.get("status") == "success":
                        answers.append(f"Step {step_result['step']} completed successfully.")
                    else:
                        answers.append(f"Step {step_result['step']} failed: {response.get('message', 'Unknown error')}")
                
                return {"answer": "\n\n".join(answers)}
            
            return {"answer": "Plan executed but no results returned."}

        except Exception as e:
            return {"error": f"Planner execution error: {str(e)}"}
