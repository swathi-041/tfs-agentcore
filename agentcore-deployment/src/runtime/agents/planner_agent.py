"""
Planner Agent for TFS AgentCore Runtime
Handles complex multi-step workflow planning using Bedrock
"""
import os
import json
import boto3
from typing import Dict, Any


class PlannerAgent:
    """Planner Agent for complex workflow orchestration"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=config["AWS_REGION"]
        )
    
    AVAILABLE_AGENTS = """
1. QnA_Agent
   Actions: search_knowledge, answer_question

2. LeaseAgent
   Actions:
     - get_lease_details(lease_id: str) → Returns lease information
     - calculate_buyout(lease_id: str, current_odometer: int) → Returns buyout amount and breakdown
     - calculate_exchange(lease_id: str, current_odometer: int, condition: str) → Returns exchange credit and available vehicles
     - terminate_lease(lease_id: str, reason: str) → Terminates lease agreement
     - confirm_purchase(lease_id: str, payment_amount: float, payment_method: str="credit_card") → Confirms buyout
     - confirm_exchange(lease_id: str, new_vehicle_id: str, payment_amount: float, payment_method: str="financing") → Confirms exchange
     - create_lease(vehicle_id: str, monthly_payment: float, term_months: int) → Creates new lease

3. PaymentAgent
   Actions:
     - process_payment(lease_id: str, amount: float, payment_type: str) → Processes payment
     - get_payment_history(lease_id: str) → Returns payment history
     - get_member_info(member_id: str, email: str) → Returns member information
"""

    PLANNER_PROMPT = """
You are a Task Planner Agent. Analyze the user request and create a detailed JSON plan.

## Available Agents

{available_agents}

## Response Format

{{
    "task_summary": "Brief description of the task",
    "complexity": "simple|moderate|complex",
    "total_steps": number,
    "plan": [
        {{
            "step": 1,
            "agent": "AgentName",
            "action": "action_name",
            "description": "What this step does",
            "params": {{}},
            "depends_on": []
        }}
    ],
    "expected_outcome": "What the user will receive"
}}

## Rules

- Return ONLY valid JSON, no markdown or explanation
- For informational queries → route to QnA_Agent
- For transactional/operational → route to LeaseAgent or PaymentAgent
- For informational queries → route to QnA_Agent
- **For queries mixing information + lease details → create multiple steps with direct agent responses**
- Use EXACT parameter names and types from specs above:
  - "current_odometer" not "current_mileage" (integer, odometer reading)
  - "reason" for terminate_lease
  - "condition" for calculate_exchange (e.g., "excellent", "good", "fair", "poor")
- Use placeholder format "?from_step_N?" to reference earlier step outputs
- Extract numeric values from natural language (e.g., "40000 miles" → 40000)
- If parameters are missing, use "?ask_user?"
- terminate_lease only needs lease_id and reason, NOT mileage
- For "fee" or "termination" questions → use terminate_lease
- For "buyout" or "payoff" questions → use calculate_buyout with current_odometer
- For "exchange" or "trade-in" questions → use calculate_exchange with current_odometer and condition
- Only use confirm_purchase/confirm_exchange if user explicitly asks to confirm  
  - For termination results: use "termination_fees": "?from_step_N?"
  - For lease details: use "lease_details": "?from_step_N?"
"""

    def generate_plan(self, user_query: str) -> Dict[str, Any]:
        """
        Generate a plan for complex user queries
        
        Args:
            user_query: User's request
            
        Returns:
            Dict containing the plan
        """
        try:
            prompt_with_agents = self.PLANNER_PROMPT.replace("{available_agents}", self.AVAILABLE_AGENTS)
            full_prompt = prompt_with_agents + f"\nUser Request: {user_query}"

            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": full_prompt}
                        ]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1500,
                    "temperature": 0
                }
            }

            response = self.bedrock.invoke_model(
                modelId=self.config["BEDROCK_MODEL_ID"],
                body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())
            text_output = response_body["output"]["message"]["content"][0]["text"].strip()

            try:
                parsed_json = json.loads(text_output)
                return parsed_json
            except Exception as e:
                return {
                    "error": f"Planner returned invalid JSON: {text_output}",
                    "details": str(e)
                }

        except Exception as e:
            return {
                "error": f"Plan generation failed: {str(e)}"
            }
    
    def execute_plan_locally(self, plan: Dict[str, Any], agents: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plan using local agent instances
        
        Args:
            plan: Generated plan from planner
            agents: Dictionary of agent instances
            
        Returns:
            Dict with execution results
        """
        try:
            plan_steps = plan.get("plan", [])
            execution_results = []
            
            for step in plan_steps:
                step_id = step.get("step")
                agent_name = (step.get("agent") or "").lower()
                action = step.get("action")
                params = step.get("params") or {}
                
                # Route to appropriate agent
                if "qna" in agent_name:
                    if "qna_agent" in agents:
                        result = agents["qna_agent"].ask_question(
                            params.get("query") or params.get("question") or step.get("description")
                        )
                    else:
                        result = {"error": "QnA agent not available"}
                        
                elif "lease" in agent_name:
                    if "lease_agent" in agents:
                        result = agents["lease_agent"].execute_action(action, params)
                    else:
                        result = {"error": "Lease agent not available"}
                        
                elif "payment" in agent_name:
                    if "payment_agent" in agents:
                        result = agents["payment_agent"].execute_action(action, params)
                    else:
                        result = {"error": "Payment agent not available"}
                        
                else:
                    result = {"error": f"Unknown agent in plan: {step.get('agent')}"}
                
                # Capture the agent response
                execution_results.append({
                    "step": step_id,
                    "agent": step.get("agent"),
                    "action": action,
                    "request": params,
                    "response": result
                })
            
            # Return planner metadata, original plan, and actual execution results
            return {
                "planner_response": {k: v for k, v in plan.items() if k != "plan"},
                "plan": plan_steps,
                "execution_results": execution_results
            }
            
        except Exception as e:
            return {
                "error": f"Plan execution failed: {str(e)}",
                "plan": plan
            }
