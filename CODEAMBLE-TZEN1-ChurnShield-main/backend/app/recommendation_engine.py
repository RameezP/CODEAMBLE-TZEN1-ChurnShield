def get_risk_level(probability: float) -> str:
    if probability >= 0.80:
        return "CRITICAL"
    elif probability >= 0.60:
        return "HIGH"
    elif probability >= 0.30:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_financial_exposure(customer_data: dict, probability: float, industry: str) -> dict:
    industry = industry.lower()
    exposure = {}

    if industry in ["telecom", "ott"]:
        monthly_charge = float(customer_data.get("Monthly Charge", customer_data.get("MonthlyCharge", 0)))
        exposure["risk_revenue_loss"] = round(probability * monthly_charge, 2)
        if "CLTV" in customer_data:
            exposure["cltv_value_at_risk"] = round(probability * float(customer_data["CLTV"]), 2)

    elif industry == "banking":
        trans_amt = float(customer_data.get("Total_Trans_Amt", 0))
        revol_bal = float(customer_data.get("Total_Revolving_Bal", 0))
        credit_limit = float(customer_data.get("Credit_Limit", 0))

        exposure["transaction_volume_at_risk"] = round(probability * trans_amt, 2)
        exposure["revolving_balance_exposure"] = round(probability * revol_bal, 2)
        exposure["credit_limit_at_risk"] = round(probability * credit_limit, 2)

    return exposure

def get_retention_recommendations(customer_data: dict, top_reasons: list, industry: str = "telecom") -> list:
    recommendations = []

    def add(issue: str, action: str):
        recommendations.append({
            "issue": issue,
            "recommended_action": action
        })

    industry = industry.lower()

    if industry == "telecom":
        if "Satisfaction Score" in top_reasons or "Satisfaction" in top_reasons:
            score = float(customer_data.get("Satisfaction Score", customer_data.get("Satisfaction", 0)))
            if score <= 2:
                add("Low customer satisfaction", "Assign priority customer support and offer service recovery bonus.")
            elif score == 3:
                add("Moderate customer satisfaction", "Send feedback survey and provide engagement offers.")

        if "Monthly Charge" in top_reasons:
            charge = float(customer_data.get("Monthly Charge", 0))
            if charge >= 80:
                add("High monthly charges", "Offer 15-20% discount or suggest a tailored plan upgrade.")

        if "Contract" in top_reasons:
            contract = str(customer_data.get("Contract", ""))
            if contract == "Month-to-Month":
                add("Short-term contract risk", "Offer annual contract upgrade with 2 months free.")

    elif industry == "ott":
        if "Avg Monthly Watch Hours" in top_reasons or "Watch Hours" in top_reasons:
            hours = float(customer_data.get("Avg Monthly Watch Hours", 0))
            if hours < 15:
                add("Low watch time engagement", "Send personalized content recommendations and trending watchlist alerts.")

        if "Days Since Last Login" in top_reasons:
            days = float(customer_data.get("Days Since Last Login", 0))
            if days >= 14:
                add("High inactivity risk", "Launch win-back campaign with premier release access.")

        if "Support Tickets" in top_reasons:
            tickets = float(customer_data.get("Support Tickets", 0))
            if tickets >= 2:
                add("Multiple unresolved support tickets", "Escalate to dedicated VIP customer success rep.")

    elif industry == "banking":
        if "Months_Inactive_12_mon" in top_reasons:
            months = float(customer_data.get("Months_Inactive_12_mon", 0))
            if months >= 3:
                add("Extended account inactivity", "Assign relationship manager and send personalized reactivation cashback offer.")

        if "Total_Trans_Ct" in top_reasons or "Total_Trans_Amt" in top_reasons:
            txns = float(customer_data.get("Total_Trans_Ct", 0))
            if txns < 40:
                add("Low transaction velocity", "Offer 3x reward bonus points on next 10 credit card purchases.")

        if "Total_Revolving_Bal" in top_reasons:
            bal = float(customer_data.get("Total_Revolving_Bal", 0))
            if bal > 2000:
                add("High revolving credit balance", "Promote lower interest rate balance transfer program.")

        if "Contacts_Count_12_mon" in top_reasons:
            contacts = float(customer_data.get("Contacts_Count_12_mon", 0))
            if contacts >= 3:
                add("Frequent customer service inquiries", "Schedule proactive call from senior account officer.")

    if not recommendations:
        add("General churn risk mitigation", "Engage customer with targeted loyalty rewards and periodic service check-in.")

    return recommendations
