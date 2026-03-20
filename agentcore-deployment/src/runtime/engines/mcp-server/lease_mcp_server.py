# import json
# import os
# from datetime import datetime
# from typing import Dict, Any

# from fastmcp import FastMCP

# # -------------------------------------------------
# # Load mock data
# # -------------------------------------------------

# BASE_DIR = os.path.dirname(__file__)
# DATA_PATH = os.path.join(BASE_DIR, "lease_mock_data.json")

# with open(DATA_PATH, "r", encoding="utf-8") as f:
#     DATA = json.load(f)

# MOCK_LEASES: Dict[str, Any] = DATA["MOCK_LEASES"]
# CONDITION_MULTIPLIERS: Dict[str, float] = DATA["CONDITION_MULTIPLIERS"]
# AVAILABLE_EXCHANGE_VEHICLES = DATA["AVAILABLE_EXCHANGE_VEHICLES"]

# # -------------------------------------------------
# # MCP Server
# # -------------------------------------------------

# mcp = FastMCP("tfs-lease-mcp")

# # -------------------------------------------------
# # Tools
# # -------------------------------------------------

# @mcp.tool()
# def get_lease_details(lease_id: str) -> Dict[str, Any]:
#     lease = MOCK_LEASES.get(lease_id)
#     if not lease:
#         return {"status": "error", "message": "Lease not found"}

#     return {
#         "status": "success",
#         "lease_id": lease_id,
#         "customer_name": lease["customer_name"],
#         "customer_address": lease["customer_address"],
#         "vehicle": lease["vehicle"],
#         "account_number": lease["account_number"],
#     }


# @mcp.tool()
# def calculate_buyout(
#     lease_id: str | None = None,
#     current_odometer: int | None = None,
# ) -> Dict[str, Any]:

#     if not lease_id or current_odometer is None:
#         return {
#             "status": "needs_info",
#             "message": "Lease ID and current odometer reading are required.",
#         }

#     lease = MOCK_LEASES.get(lease_id)
#     if not lease:
#         return {"status": "error", "message": "Lease not found"}

#     allowed_miles = lease["allowed_miles"]
#     per_mile_rate = lease["per_mile_overage"]

#     overage_miles = max(0, current_odometer - allowed_miles)
#     overage_charge = round(overage_miles * per_mile_rate, 2)

#     residual_value = lease["residual_value"]
#     total_buyout = round(residual_value + overage_charge, 2)

#     return {
#         "status": "success",
#         "lease_id": lease_id,
#         "vehicle": f'{lease["vehicle"]["year"]} '
#                    f'{lease["vehicle"]["make"]} '
#                    f'{lease["vehicle"]["model"]}',
#         "allowed_miles": allowed_miles,
#         "current_odometer": current_odometer,
#         "overage_miles": overage_miles,
#         "per_mile_rate": per_mile_rate,
#         "overage_charge": overage_charge,
#         "residual_value": residual_value,
#         "total_buyout_amount": total_buyout,
#     }


# @mcp.tool()
# def calculate_exchange(
#     lease_id: str | None = None,
#     current_odometer: int | None = None,
#     condition: str | None = None,
# ) -> Dict[str, Any]:

#     if not lease_id or current_odometer is None or not condition:
#         return {
#             "status": "needs_info",
#             "message": "Lease ID, odometer, and vehicle condition are required.",
#         }

#     lease = MOCK_LEASES.get(lease_id)
#     if not lease:
#         return {"status": "error", "message": "Lease not found"}

#     condition = condition.lower()
#     multiplier = CONDITION_MULTIPLIERS.get(condition)

#     if multiplier is None:
#         return {
#             "status": "error",
#             "message": "Condition must be one of: excellent, good, fair, poor",
#         }

#     allowed_miles = lease["allowed_miles"]
#     per_mile_rate = lease["per_mile_overage"]

#     overage_miles = max(0, current_odometer - allowed_miles)
#     overage_charge = round(overage_miles * per_mile_rate, 2)

#     adjusted_trade_in = round(
#         lease["base_trade_in_value"] * multiplier, 2
#     )

#     net_trade_in_credit = round(
#         adjusted_trade_in - overage_charge, 2
#     )

#     vehicles = []
#     for v in AVAILABLE_EXCHANGE_VEHICLES:
#         vehicles.append({
#             "id": v["id"],
#             "vehicle": f'{v["year"]} {v["make"]} {v["model"]} {v["trim"]}',
#             "msrp": v["msrp"],
#             "trade_in_credit": net_trade_in_credit,
#             "amount_due": round(v["msrp"] - net_trade_in_credit, 2),
#         })

#     return {
#         "status": "success",
#         "lease_id": lease_id,
#         "current_vehicle": f'{lease["vehicle"]["year"]} '
#                            f'{lease["vehicle"]["make"]} '
#                            f'{lease["vehicle"]["model"]}',
#         "condition": condition,
#         "condition_multiplier": multiplier,
#         "allowed_miles": allowed_miles,
#         "current_odometer": current_odometer,
#         "overage_miles": overage_miles,
#         "overage_charge": overage_charge,
#         "net_trade_in_credit": net_trade_in_credit,
#         "available_vehicles": vehicles,
#     }


# @mcp.tool()
# def terminate_lease(
#     lease_id: str | None = None,
#     reason: str | None = None,
# ) -> Dict[str, Any]:

#     return {
#         "status": "success",
#         "lease_id": lease_id,
#         "message": "Lease terminated successfully",
#         "reason": reason,
#         "terminated_at": datetime.utcnow().isoformat(),
#     }


# @mcp.tool()
# def confirm_purchase(
#     lease_id: str,
#     payment_amount: float,
#     payment_method: str = "credit_card",
# ) -> Dict[str, Any]:

#     return {
#         "status": "ready_for_payment",
#         "transaction_type": "lease_buyout",
#         "lease_id": lease_id,
#         "payment_amount": payment_amount,
#         "payment_method": payment_method,
#     }


# @mcp.tool()
# def confirm_exchange(
#     lease_id: str,
#     new_vehicle_id: str,
#     payment_amount: float,
#     payment_method: str = "financing",
# ) -> Dict[str, Any]:

#     return {
#         "status": "ready_for_payment",
#         "transaction_type": "lease_exchange",
#         "lease_id": lease_id,
#         "new_vehicle_id": new_vehicle_id,
#         "payment_amount": payment_amount,
#         "payment_method": payment_method,
#     }


# # -------------------------------------------------
# # Entrypoint
# # -------------------------------------------------

# if __name__ == "__main__":
#     mcp.run(
#         transport="streamable-http",
#         host="127.0.0.1",
#         port=8001,
#     )

import json
import os
from datetime import datetime
from typing import Dict, Any

from fastmcp import FastMCP


# =========================================================
# LOAD MOCK DATA
# =========================================================

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "lease_mock_data.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

MOCK_LEASES = DATA["MOCK_LEASES"]
CONDITION_MULTIPLIERS = DATA["CONDITION_MULTIPLIERS"]
AVAILABLE_EXCHANGE_VEHICLES = DATA["AVAILABLE_EXCHANGE_VEHICLES"]


# =========================================================
# MCP SERVER
# =========================================================

mcp = FastMCP("tfs-lease-mcp")


# =========================================================
# TOOLS
# =========================================================

@mcp.tool()
def get_lease_details(lease_id: str) -> Dict[str, Any]:
    lease = MOCK_LEASES.get(lease_id)

    if not lease:
        return {
            "status": "error",
            "message": "Lease not found"
        }

    return {
        "status": "success",
        "lease_id": lease_id,
        "customer_name": lease["customer_name"],
        "customer_address": lease["customer_address"],
        "vehicle": lease["vehicle"],
        "account_number": lease["account_number"]
    }


@mcp.tool()
def calculate_buyout(
    lease_id: str | None = None,
    current_odometer: int | None = None
) -> Dict[str, Any]:

    if not lease_id or lease_id == "?ask_user?" or current_odometer is None:
        return {
            "status": "needs_info",
            "message": "To calculate buyout price, please provide Lease ID and current odometer reading."
        }

    if lease_id not in MOCK_LEASES:
        return {
            "status": "error",
            "message": f"Lease {lease_id} not found"
        }

    lease = MOCK_LEASES[lease_id]
    vehicle = lease["vehicle"]

    allowed_miles = lease["allowed_miles"]
    overage_miles = max(0, current_odometer - allowed_miles)
    overage_charge = round(overage_miles * lease["per_mile_overage"], 2)

    residual_value = lease["residual_value"]
    total_buyout = round(residual_value + overage_charge, 2)

    return {
        "status": "success",
        "lease_id": lease_id,
        "customer_name": lease["customer_name"],
        "vehicle_info": f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
        "vehicle_vin": vehicle["vin"],
        "allowed_miles": allowed_miles,
        "current_odometer": current_odometer,
        "overage_miles": overage_miles,
        "per_mile_rate": lease["per_mile_overage"],
        "overage_charge": overage_charge,
        "residual_value": residual_value,
        "total_buyout_amount": total_buyout,
        "message": f"Buyout amount: ${total_buyout:,.2f}"
    }


@mcp.tool()
def calculate_exchange(
    lease_id: str | None = None,
    current_odometer: int | None = None,
    condition: str | None = None
) -> Dict[str, Any]:

    if not lease_id or lease_id == "?ask_user?" or current_odometer is None or not condition:
        return {
            "status": "needs_info",
            "message": "Please provide Lease ID, odometer reading, and vehicle condition (excellent/good/fair/poor)."
        }

    if lease_id not in MOCK_LEASES:
        return {
            "status": "error",
            "message": f"Lease {lease_id} not found"
        }

    condition_lower = condition.lower()

    if condition_lower not in CONDITION_MULTIPLIERS:
        return {
            "status": "error",
            "message": "Condition must be excellent, good, fair, or poor"
        }

    lease = MOCK_LEASES[lease_id]
    vehicle = lease["vehicle"]

    allowed_miles = lease["allowed_miles"]
    overage_miles = max(0, current_odometer - allowed_miles)
    overage_charge = round(overage_miles * lease["per_mile_overage"], 2)

    base_trade_in = lease["base_trade_in_value"]
    condition_multiplier = CONDITION_MULTIPLIERS[condition_lower]

    adjusted_trade_in = round(base_trade_in * condition_multiplier, 2)
    net_trade_in_credit = round(adjusted_trade_in - overage_charge, 2)

    available_vehicles = []

    for v in AVAILABLE_EXCHANGE_VEHICLES:
        amount_due = round(v["msrp"] - net_trade_in_credit, 2)

        available_vehicles.append({
            "id": v["id"],
            "vehicle": f"{v['year']} {v['make']} {v['model']} {v['trim']}",
            "color": v.get("color", "N/A"),
            "msrp": v["msrp"],
            "trade_in_credit": net_trade_in_credit,
            "amount_due": amount_due
        })

    return {
        "status": "success",
        "lease_id": lease_id,
        "customer_name": lease["customer_name"],
        "current_vehicle": f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
        "current_vin": vehicle["vin"],
        "condition": condition_lower,
        "condition_multiplier": f"{int(condition_multiplier * 100)}%",
        "base_trade_in_value": base_trade_in,
        "adjusted_trade_in_value": adjusted_trade_in,
        "allowed_miles": allowed_miles,
        "current_odometer": current_odometer,
        "overage_miles": overage_miles,
        "overage_charge": overage_charge,
        "net_trade_in_credit": net_trade_in_credit,
        "available_vehicles": available_vehicles,
        "message": f"Trade-in credit: ${net_trade_in_credit:,.2f}"
    }


@mcp.tool()
def terminate_lease(
    lease_id: str | None = None,
    reason: str | None = None
) -> Dict[str, Any]:

    return {
        "status": "success",
        "lease_id": lease_id,
        "message": "Lease terminated successfully",
        "reason": reason,
        "terminated_at": datetime.utcnow().isoformat()
    }


@mcp.tool()
def confirm_purchase(
    lease_id: str,
    payment_amount: float,
    payment_method: str = "credit_card"
) -> Dict[str, Any]:

    return {
        "status": "ready_for_payment",
        "transaction_type": "lease_buyout",
        "lease_id": lease_id,
        "payment_amount": payment_amount,
        "payment_method": payment_method
    }


@mcp.tool()
def confirm_exchange(
    lease_id: str,
    new_vehicle_id: str,
    payment_amount: float,
    payment_method: str = "financing"
) -> Dict[str, Any]:

    return {
        "status": "ready_for_payment",
        "transaction_type": "lease_exchange",
        "lease_id": lease_id,
        "new_vehicle_id": new_vehicle_id,
        "payment_amount": payment_amount,
        "payment_method": payment_method
    }


# =========================================================
# START MCP SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8001
    )

