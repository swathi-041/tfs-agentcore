"""
Lease Agent for TFS AgentCore Runtime
Handles lease operations using MCP tools with Bedrock explanations
"""
import os
import json
import boto3
import asyncio
import re
import sys
from typing import Dict, Any

# Import lease tools from local engines
from engines.lease_tools import init_mcp_tools, invoke_lease_tool


class LeaseAgent:
    """Lease Agent with MCP tool integration"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=config["AWS_REGION"]
        )
        self.followup_model_id = "amazon.nova-lite-v1:0"
    
    def _sync_bedrock_call(self, action: str, result: dict) -> str:
        """Synchronous Bedrock call for generating explanations"""
        prompt = f"""
You are Toyota Financial Services Lease Assistant.

Given this lease result:

Action:
{action}

Result:
{json.dumps(result)}

Generate ONLY:

Follow-up Questions:
1.
2.

Next Steps:
1.
2.

Rules:
- Do not repeat numeric values
- Do not calculate
- Do not rewrite tool output
- Only generate relevant follow-up questions and next steps
"""

        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 150,
                "temperature": 0.3
            }
        }

        response = self.bedrock.invoke_model(
            modelId=self.followup_model_id,
            body=json.dumps(body)
        )

        response_body = json.loads(response["body"].read())
        return response_body["output"]["message"]["content"][0]["text"]

    async def format_with_bedrock(self, action: str, result: dict) -> str:
        """Async wrapper for Bedrock formatting"""
        return await asyncio.to_thread(self._sync_bedrock_call, action, result)

    def format_exchange(self, result: dict) -> str:
        """Format exchange calculation result"""
        vehicles = result.get("available_vehicles", [])

        lines = [
            f"Here are the exchange details for your lease {result['lease_id']}:",
            "",
            f"* Vehicle: {result['current_vehicle']}",
            f"* Condition: {result['condition']}",
            f"* Condition multiplier: {result['condition_multiplier']}",
            f"* Allowed miles: {result['allowed_miles']:,.1f}",
            f"* Current odometer: {result['current_odometer']}",
            f"* Overage miles: {result['overage_miles']}",
            f"* Overage charge: ${result['overage_charge']:,.2f}",
            f"* Net trade-in credit: ${result['net_trade_in_credit']:,.2f}",
            "",
            "Available Vehicles:",
            ""
        ]

        for i, v in enumerate(vehicles, 1):
            lines.append(
                f"{i}. ID: {v['id']}, "
                f"Vehicle: {v['vehicle']}, "
                f"MSRP: ${v['msrp']:,.2f}, "
                f"Trade-in credit: ${v['trade_in_credit']:,.2f}, "
                f"Amount due: ${v['amount_due']:,.2f}"
            )

        return "\n".join(lines)

    def format_buyout(self, result: dict) -> str:
        """Format buyout calculation result"""
        return f"""
Here are the buyout details for your lease {result['lease_id']}:

* Vehicle: {result['vehicle_info']}
* VIN: {result['vehicle_vin']}
* Allowed miles: {result['allowed_miles']:,.1f}
* Current odometer: {result['current_odometer']}
* Overage miles: {result['overage_miles']}
* Overage charge: ${result['overage_charge']:,.2f}
* Residual value: ${result['residual_value']:,.2f}
* Total buyout amount: ${result['total_buyout_amount']:,.2f}
""".strip()

    def format_lease_details(self, result: dict) -> str:
        """Format lease details result"""
        vehicle = result["vehicle"]

        return f"""
Here are the lease details for {result['lease_id']}:

* Customer Name: {result['customer_name']}
* Vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}
* VIN: {vehicle['vin']}
* Account Number: {result['account_number']}
* Address: {result['customer_address']}
""".strip()

    def extract_common_params(self, raw_text: str) -> dict:
        """Extract common parameters from natural language"""
        result = {}

        lease_match = re.search(r"LSE-\d+", raw_text, re.IGNORECASE)
        if lease_match:
            result["lease_id"] = lease_match.group()

        query_without_lease = re.sub(r"LSE-\d+", "", raw_text, flags=re.IGNORECASE)

        mileage_match = re.search(r"\b\d{2,6}\b", query_without_lease)
        if mileage_match:
            result["current_odometer"] = int(mileage_match.group())

        condition_match = re.search(
            r"\b(excellent|good|fair|poor)\b",
            raw_text,
            re.IGNORECASE
        )
        if condition_match:
            result["condition"] = condition_match.group().lower()

        return result

    async def execute_action(self, action: str, params: dict) -> Dict[str, Any]:
        """
        Execute a lease action using MCP tools or mock responses
        
        Args:
            action: Action to execute
            params: Parameters for the action
            
        Returns:
            Dict with execution result and explanation
        """
        try:
            print(f"[DEBUG] Lease agent execute_action called: action={action}, params={params}")
            
            # Initialize MCP tools
            await init_mcp_tools()

            # Parse parameters if needed
            needs_parse = (
                not params
                or not params.get("lease_id")
                or (
                    action in ["calculate_buyout", "calculate_exchange"]
                    and params.get("current_odometer") is None
                )
            )

            if needs_parse:
                raw_text = (
                    params.get("text")
                    or params.get("query")
                    or params.get("message")
                    or ""
                )

                if raw_text:
                    parsed = self.extract_common_params(raw_text)

                    if action == "calculate_exchange":
                        params["lease_id"] = parsed.get("lease_id")
                        params["current_odometer"] = parsed.get("current_odometer")

                    elif action == "calculate_buyout":
                        params["lease_id"] = parsed.get("lease_id")
                        params["current_odometer"] = parsed.get("current_odometer")

            # Normalize parameter aliases
            if "miles" in params and "current_odometer" not in params:
                params["current_odometer"] = params.pop("miles")

            if "mileage" in params and "current_odometer" not in params:
                params["current_odometer"] = params.pop("mileage")

            if "odometer" in params and "current_odometer" not in params:
                params["current_odometer"] = params.pop("odometer")

            if action == "calculate_exchange" and "condition" in params:
                params["condition"] = params["condition"].lower()

            # Invoke MCP tool
            print(f"[DEBUG] Lease agent invoking: action={action}, params={params}")
            result = await invoke_lease_tool(action, params)
            print(f"[DEBUG] Lease tool result: {result}")

            # Format response based on action
            if action == "calculate_exchange" and result.get("status") == "success":
                base = self.format_exchange(result)
                print(f"[DEBUG] Formatted exchange response")

            elif action == "calculate_buyout" and result.get("status") == "success":
                base = self.format_buyout(result)
                print(f"[DEBUG] Formatted buyout response")

            elif action == "get_lease_details" and result.get("status") == "success":
                base = self.format_lease_details(result)
                print(f"[DEBUG] Formatted lease details response")

            else:
                # If no formatting was applied, create a simple response
                if result.get("status") == "success":
                    base = f"Lease {action} completed for {result.get('lease_id', 'Unknown')}."
                else:
                    base = f"Lease {action} failed: {result.get('message', 'Unknown error')}"
                print(f"[DEBUG] Created simple response for action={action}, status={result.get('status')}")

            try:
                llm_extra = await self.format_with_bedrock(action, result)
                explanation = base + ("\n\n" + llm_extra if base else llm_extra)
                print(f"[DEBUG] Final explanation length: {len(explanation)}")
            except Exception as e:
                explanation = base if base else "Unable to generate explanation."
                print(f"[DEBUG] Bedrock formatting failed: {e}")

            final_result = {
                "status": "success",
                "action": action,
                "result": result,
                "explanation": explanation
            }
            print(f"[DEBUG] Lease agent returning: {final_result}")
            return final_result

        except Exception as e:
            error_result = {
                "status": "error",
                "action": action,
                "message": f"Lease action failed: {str(e)}"
            }
            print(f"[DEBUG] Lease agent exception: {error_result}")
            return error_result
