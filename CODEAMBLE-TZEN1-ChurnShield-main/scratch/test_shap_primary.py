import sys
import os
sys.path.append(os.path.abspath("backend"))

from app.agent_engine import RetentionAgentOrchestrator, _reverse_onehot_map

orchestrator = RetentionAgentOrchestrator("telecom")

# Test Customer A: High Risk (Satisfaction = 1, Month-to-Month)
cust_a = {
    "Age": 35,
    "Gender": "Male",
    "Tenure in Months": 2,
    "Contract": "Month-to-Month",
    "Internet Type": "Fiber Optic",
    "Payment Method": "Bank Withdrawal",
    "Monthly Charge": 95.0,
    "Satisfaction Score": 1,
    "Online Security": "0",
    "Premium Tech Support": "0",
    "Number of Referrals": 0,
    "Internet Service": "1",
    "Married": "0"
}

res_a = orchestrator.run_pipeline(cust_a, "CUST-A")
print("=== CUSTOMER A (High Risk: Sat=1, Month-to-Month) ===")
print("Prob:", res_a["churn_probability"], "Risk:", res_a["risk_level"])
print("Top Drivers:")
for d in res_a["top_drivers"]:
    print(f"  - {d['feature']}: val={d['feature_value']}, impact={d['impact']}, direction={d['direction']}, imp={d['importance']}%")

# Test Customer B: Low Risk (Satisfaction = 5, Two Year)
cust_b = {
    "Age": 45,
    "Gender": "Female",
    "Tenure in Months": 48,
    "Contract": "Two Year",
    "Internet Type": "DSL",
    "Payment Method": "Credit Card",
    "Monthly Charge": 45.0,
    "Satisfaction Score": 5,
    "Online Security": "1",
    "Premium Tech Support": "1",
    "Number of Referrals": 5,
    "Internet Service": "1",
    "Married": "1"
}

res_b = orchestrator.run_pipeline(cust_b, "CUST-B")
print("\n=== CUSTOMER B (Low Risk: Sat=5, Two Year) ===")
print("Prob:", res_b["churn_probability"], "Risk:", res_b["risk_level"])
print("Top Drivers:")
for d in res_b["top_drivers"]:
    print(f"  - {d['feature']}: val={d['feature_value']}, impact={d['impact']}, direction={d['direction']}, imp={d['importance']}%")
