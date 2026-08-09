from app.gemini_service import generate_ai_communication

def generate_communication(
    customer_id: str,
    industry: str,
    risk_level: str,
    churn_probability: float,
    top_drivers: list,
    recommendation: str,
    channel: str = "email",
    tone: str = "professional",
    profile: dict = None
) -> dict:
    return generate_ai_communication(
        customer_id=customer_id,
        industry=industry,
        risk_level=risk_level,
        churn_probability=churn_probability,
        top_drivers=top_drivers,
        recommendation=recommendation,
        channel=channel,
        tone=tone,
        profile=profile
    )
