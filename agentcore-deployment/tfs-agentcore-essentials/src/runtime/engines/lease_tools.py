"""
Lease Tools for TFS AgentCore Runtime
MCP tool integration with fallback to mock responses
"""

import json
import asyncio
import time
import os
from typing import Dict, Any, Optional

# Load real mock data
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "mcp-server", "lease_mock_data.json")

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        DATA = json.load(f)
    MOCK_LEASES = DATA["MOCK_LEASES"]
    CONDITION_MULTIPLIERS = DATA["CONDITION_MULTIPLIERS"]
    AVAILABLE_EXCHANGE_VEHICLES = DATA["AVAILABLE_EXCHANGE_VEHICLES"]
except Exception as e:
    print(f"Warning: Could not load mock data: {e}")
    # Fallback to minimal data
    MOCK_LEASES = {}
    CONDITION_MULTIPLIERS = {"excellent": 1.0, "good": 0.85, "fair": 0.7, "poor": 0.5}
    AVAILABLE_EXCHANGE_VEHICLES = []

# Global MCP availability flag
MCP_AVAILABLE = False

# Try to import MCP client, fallback to mock if not available
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None  # Define as None to avoid NameError
    print("Warning: MCP client not available, using mock responses")

# MCP Server configuration (will be used if available)
MCP_SERVERS = {
    "server": {
        "transport": "streamable_http",
        "url": "http://127.0.0.1:8001/mcp"
    }
}

_mcp_client: Optional['MultiServerMCPClient'] = None
_TOOLS_BY_NAME: Dict[str, Any] = {}


async def init_mcp_tools():
    """Initialize MCP tools if available"""
    global _mcp_client, _TOOLS_BY_NAME

    # For now, always skip MCP initialization to avoid issues
    print("MCP initialization skipped for standalone operation")
    return


async def invoke_lease_tool(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke lease tool using MCP or fallback to mock"""
    
    # For now, always use mock responses to avoid MCP issues
    return _mock_lease_response(action, params)


async def _invoke_mcp_tool(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke actual MCP tool"""
    if action not in _TOOLS_BY_NAME:
        return {
            "status": "error",
            "message": f"Unknown lease action: {action}"
        }

    tool = _TOOLS_BY_NAME[action]

    try:
        raw = await tool.ainvoke(params)
    except Exception as e:
        print(f"[ERROR] Tool invoke failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Tool invocation failed: {str(e)}"
        }

    try:
        if isinstance(raw, list) and raw:
            msg = raw[0]

            if isinstance(msg, dict) and "text" in msg:
                try:
                    return json.loads(msg["text"])
                except Exception:
                    return {
                        "status": "success",
                        "raw": msg["text"]
                    }

            elif isinstance(msg, dict):
                return msg

            elif isinstance(msg, str):
                try:
                    return json.loads(msg)
                except Exception:
                    return {
                        "status": "success",
                        "raw": msg
                    }

        if isinstance(raw, dict):
            return raw

        return {
            "status": "success",
            "result": raw
        }

    except Exception as e:
        print(f"[ERROR] Unexpected error in invoke_lease_tool: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected processing error: {str(e)}"
        }


def _mock_lease_response(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate mock lease responses for standalone operation"""
    
    lease_id = params.get("lease_id", "LSE-12345")
    current_odometer = params.get("current_odometer", 40000)
    condition = params.get("condition", "good")
    
    if action == "calculate_buyout":
        lease = MOCK_LEASES.get(lease_id)
        if not lease:
            return {"status": "error", "message": f"Lease not found: {lease_id}"}
        
        allowed_miles = lease.get("allowed_miles", 36000)
        overage_miles = max(0, current_odometer - allowed_miles)
        overage_charge = overage_miles * lease.get("per_mile_overage", 0.25)
        residual_value = lease.get("residual_value", 18000)
        
        return {
            "status": "success",
            "lease_id": lease_id,
            "vehicle_info": f"{lease['vehicle']['year']} {lease['vehicle']['make']} {lease['vehicle']['model']}",
            "vehicle_vin": lease["vehicle"]["vin"],
            "allowed_miles": allowed_miles,
            "current_odometer": current_odometer,
            "overage_miles": overage_miles,
            "overage_charge": overage_charge,
            "residual_value": residual_value,
            "total_buyout_amount": residual_value + overage_charge,
            "mock_data": True
        }
    
    elif action == "calculate_exchange":
        lease = MOCK_LEASES.get(lease_id)
        if not lease:
            return {"status": "error", "message": f"Lease not found: {lease_id}"}
        
        allowed_miles = lease.get("allowed_miles", 36000)
        overage_miles = max(0, current_odometer - allowed_miles)
        overage_charge = overage_miles * lease.get("per_mile_overage", 0.25)
        
        multiplier = CONDITION_MULTIPLIERS.get(condition, 0.85)
        base_trade_in = lease.get("base_trade_in_value", 15000)
        net_trade_in_credit = base_trade_in * multiplier
        
        return {
            "status": "success",
            "lease_id": lease_id,
            "current_vehicle": f"{lease['vehicle']['year']} {lease['vehicle']['make']} {lease['vehicle']['model']}",
            "condition": condition,
            "condition_multiplier": multiplier,
            "allowed_miles": allowed_miles,
            "current_odometer": current_odometer,
            "overage_miles": overage_miles,
            "overage_charge": overage_charge,
            "net_trade_in_credit": net_trade_in_credit,
            "available_vehicles": [
                {
                    "id": vehicle["id"],
                    "vehicle": f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle['trim']}",
                    "msrp": vehicle["msrp"],
                    "trade_in_credit": net_trade_in_credit,
                    "amount_due": vehicle["msrp"] - net_trade_in_credit
                }
                for vehicle in AVAILABLE_EXCHANGE_VEHICLES
            ],
            "mock_data": True
        }
    
    elif action == "get_lease_details":
        lease = MOCK_LEASES.get(lease_id)
        if not lease:
            return {"status": "error", "message": f"Lease not found: {lease_id}"}
        
        return {
            "status": "success",
            "lease_id": lease_id,
            "customer_name": lease["customer_name"],
            "account_number": lease["account_number"],
            "customer_address": lease["customer_address"],
            "vehicle": lease["vehicle"],
            "status": lease.get("status", "active"),
            "mock_data": True
        }
    
    elif action == "terminate_lease":
        lease = MOCK_LEASES.get(lease_id)
        if not lease:
            return {"status": "error", "message": f"Lease not found: {lease_id}"}
        
        allowed_miles = lease.get("allowed_miles", 36000)
        overage_miles = max(0, current_odometer - allowed_miles)
        overage_charge = overage_miles * lease.get("per_mile_overage", 0.25)
        
        return {
            "status": "success",
            "lease_id": lease_id,
            "termination_date": "2026-03-19",
            "termination_fees": 250.00,
            "final_odometer": current_odometer,
            "overage_charges": overage_charge,
            "total_amount_due": 250.00 + overage_charge,
            "message": f"Lease {lease_id} terminated successfully",
            "mock_data": True
        }
    
    else:
        return {
            "status": "error",
            "message": f"Unknown lease action: {action}",
            "mock_data": True
        }
