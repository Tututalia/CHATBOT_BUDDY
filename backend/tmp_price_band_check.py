import json
import intelligent_agent_graph as g

def check(query, expect_min=None, expect_max=None):
    raw = g.inventory_agent.invoke({"search_query": query, "customer_id": "CUST001"})
    print("\n===", query, "===")
    print(raw)
    data = json.loads(raw)
    prods = data.get("products") or []
    prices = [p.get("price") for p in prods]
    print("prices:", prices)
    if expect_min is not None:
        assert all(p is not None and float(p) >= expect_min for p in prices), f"Found price below min: {prices}"
    if expect_max is not None:
        assert all(p is not None and float(p) <= expect_max for p in prices), f"Found price above max: {prices}"

check("watches above 1000", expect_min=1000)
check("watches under 1000", expect_max=1000)
check("kurtis between 1500-2000", expect_min=1500, expect_max=2000)
check("kurtis 1500-2000", expect_min=1500, expect_max=2000)
print("\nALL_CHECKS_PASSED")
