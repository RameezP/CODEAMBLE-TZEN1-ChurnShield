import os
import json
import logging
import requests

# ── API key resolution (priority: GEMINI_API_KEY > LLM_API_KEY > CEREBRAS_API_KEY) ──
DEFAULT_API_KEY = "csk-cr68pkdfjy2kcwdx5r9jpnkchxfchrenvd66tryh2pdt4w85"
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("CEREBRAS_API_KEY") or DEFAULT_API_KEY
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_FAILED_KEYS: set = set()


# ─────────────────────────────────────────────────────────────────────────────
# FIX #1 + #2 + #5 — SHAP Feature Formatter
# ─────────────────────────────────────────────────────────────────────────────
def _format_shap_features_for_llm(industry: str, top_drivers: list, profile: dict = None) -> tuple:
    """
    Converts structured SHAP driver dicts into two lists of human-readable strings:
        positive_drivers  — CHURN RISK drivers  (+SHAP)
        negative_drivers  — PROTECTIVE FACTORS  (-SHAP)

    FIX #1: Direction is determined ONLY by the sign of `impact`.
            The `direction` field on each driver is ignored for classification.
    FIX #2: feature_value and feature name are already resolved by agent_engine's
            _reverse_onehot_map, so we use them directly.
    FIX #5: importance % is included in the output string.
    """
    profile = profile or {}
    positive_drivers = []
    negative_drivers = []

    for d in top_drivers[:8]:
        if isinstance(d, dict):
            fname     = d.get("feature", "")
            impact    = d.get("impact", 0.0)
            feat_val  = d.get("feature_value")
            importance = d.get("importance", 0.0)
        else:
            fname     = str(d)
            impact    = 0.0
            feat_val  = None
            importance = 0.0

        val_str = f" = {feat_val}" if feat_val is not None and str(feat_val).strip() != "" else ""
        imp_str = f", {importance:.1f}% relative importance" if importance else ""

        # FIX #1: ONLY the sign of impact determines direction — never the string field
        if impact > 0:
            positive_drivers.append(
                f"{fname}{val_str}  [SHAP +{abs(impact):.4f}{imp_str} → CHURN RISK DRIVER]"
            )
        else:
            negative_drivers.append(
                f"{fname}{val_str}  [SHAP -{abs(impact):.4f}{imp_str} → PROTECTIVE FACTOR]"
            )

    return positive_drivers, negative_drivers


def _human_driver_labels(industry: str, top_drivers: list) -> list:
    """Backwards-compatibility helper for legacy callers."""
    results = []
    for d in top_drivers[:5]:
        if isinstance(d, dict):
            raw = d.get("feature", "")
            val = d.get("feature_value", "")
            val_str = f" ({val})" if val is not None and str(val) != "" else ""
            results.append(f"{raw}{val_str}")
        else:
            results.append(str(d).replace("_", " "))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# LLM API Caller
# ─────────────────────────────────────────────────────────────────────────────
def call_llm_api(prompt: str, temperature: float = 0.75) -> str:
    """
    Executes a live LLM API call.
    Priority: GEMINI_API_KEY → LLM_API_KEY/CEREBRAS_API_KEY → None (fallback).
    """
    key = API_KEY
    if not key or key in _FAILED_KEYS:
        return None

    # ── Gemini path ──────────────────────────────────────────────
    if key and not key.startswith("csk-"):
        # Try official SDK first
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            models_to_try = [GEMINI_MODEL, "gemini-1.5-flash", "gemini-1.5-pro"]
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    resp = model.generate_content(prompt)
                    if resp and resp.text:
                        logging.info(f"[Gemini SDK] Success with model: {model_name}")
                        return resp.text.strip()
                except Exception as model_err:
                    logging.warning(f"[Gemini SDK] {model_name} failed: {model_err}")
                    continue
        except Exception as sdk_err:
            logging.warning(f"[Gemini SDK] Import/configure failed: {sdk_err}")

        # Try REST API fallback
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature}
            }
            res = requests.post(url, json=payload, timeout=8)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0]["content"]["parts"]
                    return "".join([p["text"] for p in parts]).strip()
            elif res.status_code in (400, 401, 403):
                logging.warning(f"[Gemini REST] Status {res.status_code} — disabling key")
                _FAILED_KEYS.add(key)
            elif res.status_code == 429:
                logging.warning("[Gemini REST] Rate limited (429)")
            else:
                logging.warning(f"[Gemini REST] Unexpected status {res.status_code}")
        except requests.exceptions.Timeout:
            logging.warning("[Gemini REST] Request timed out")
        except Exception as rest_err:
            logging.warning(f"[Gemini REST] Exception: {rest_err}")

    # ── Cerebras path (csk-* keys) ───────────────────────────────
    elif key.startswith("csk-"):
        try:
            url = "https://api.cerebras.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            for model_name in ["llama-3.3-70b", "llama3.1-70b", "llama3.1-8b"]:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature
                }
                res = requests.post(url, headers=headers, json=payload, timeout=1.5)
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices:
                        return choices[0]["message"]["content"].strip()
                elif res.status_code in (401, 402):
                    logging.warning(f"Cerebras API: Status {res.status_code} — disabling key {key[:8]}...")
                    _FAILED_KEYS.add(key)
                    break
        except Exception as e:
            logging.warning(f"Cerebras API exception: {e}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# FIX #3 — Structured Gemini Output Schema
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_strategy(
    customer_id: str,
    industry: str,
    risk_level: str,
    churn_probability: float,
    top_drivers: list,
    profile: dict
) -> dict:
    """
    Generates a fully structured, customer-specific retention strategy.
    Returns the full FIX #3 schema including risk_drivers[] and protective_factors[].
    """
    pos_drivers, neg_drivers = _format_shap_features_for_llm(industry, top_drivers, profile)

    pos_block = "\n".join([f"  {d}" for d in pos_drivers]) if pos_drivers else "  - None identified"
    neg_block = "\n".join([f"  {d}" for d in neg_drivers]) if neg_drivers else "  - None identified"

    # Build a concise profile snapshot (first 10 meaningful fields)
    profile_items = [
        f"{k}: {v}" for k, v in (profile or {}).items()
        if v is not None and str(v).strip() not in ("", "nan", "None")
    ]
    profile_ctx = "\n".join(f"  {x}" for x in profile_items[:10]) or "  (no profile data)"

    prompt = f"""You are a senior customer retention strategist at a leading {industry.upper()} company.
Generate a fully-grounded retention strategy for ONE specific customer.

════════════════════════════════════════
CUSTOMER DATA
════════════════════════════════════════
Customer ID     : {customer_id}
Industry        : {industry.upper()}
Churn Probability: {round(churn_probability * 100, 2)}%
Risk Tier       : {risk_level}

Customer Profile:
{profile_ctx}

════════════════════════════════════════
SHAP ANALYSIS
════════════════════════════════════════
▲ CHURN RISK DRIVERS (positive SHAP — pushing toward churn):
{pos_block}

▼ PROTECTIVE RETENTION FACTORS (negative SHAP — reducing churn likelihood):
{neg_block}

════════════════════════════════════════
STRICT RULES — YOU MUST FOLLOW ALL OF THESE:
════════════════════════════════════════
1. Use ONLY the data provided above. Never invent facts.
2. Positive SHAP (▲) = this feature is DRIVING churn risk. Address it.
3. Negative SHAP (▼) = this feature is PROTECTING retention. Acknowledge it.
4. Never claim a feature is high when it is low, or vice versa. Use exact provided values.
5. If risk is LOW (< 30%), say the customer is HEALTHY and frame around loyalty. Do NOT pretend they are at risk.
6. If risk is CRITICAL (> 85%), frame around urgent intervention.
7. Recommendations must reference actual numeric values from the profile (e.g. exact monthly charge, transaction count, watch hours).
8. Avoid all generic boilerplate. Every sentence must be customer-specific.

════════════════════════════════════════
REQUIRED OUTPUT — Return ONLY valid JSON:
════════════════════════════════════════
{{
  "summary": "Exactly 3 to 4 simple, clear sentences in plain everyday English explaining why this customer is at risk and how the strategy retains them. Use simple, easy-to-understand words for everyone.",
  "risk_explanation": "1-2 sentences specifically about the top churn driver and its SHAP contribution.",
  "risk_drivers": [
    {{"feature": "...", "value": "...", "reason": "Why this specific value drives churn risk."}}
  ],
  "protective_factors": [
    {{"feature": "...", "value": "...", "reason": "Why this specific value reduces churn likelihood."}}
  ],
  "recommendation": "A single crisp, specific offer headline for this customer.",
  "recommendations": [
    "Specific recommendation 1 referencing actual values",
    "Specific recommendation 2",
    "Specific recommendation 3"
  ],
  "action_items": [
    "Immediate action 1 with timeline",
    "Action 2",
    "Action 3"
  ]
}}"""

    llm_raw = call_llm_api(prompt)
    if llm_raw:
        try:
            cleaned = llm_raw.replace("```json", "").replace("```", "").strip()
            start = cleaned.find("{")
            end   = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                cleaned = cleaned[start:end]
            data = json.loads(cleaned)
            # Validate required fields
            if data.get("summary") and data.get("recommendation"):
                # Ensure all schema keys exist (fill missing with defaults)
                data.setdefault("risk_explanation", "")
                data.setdefault("risk_drivers", [])
                data.setdefault("protective_factors", [])
                data.setdefault("recommendations", [])
                data.setdefault("action_items", [])
                return data
        except Exception as e:
            logging.warning(f"[Strategy] JSON parse error: {e} — raw: {llm_raw[:200]}")

    # Fallback to dynamic multi-factor engine
    return _build_unique_fallback_strategy(
        customer_id, industry, risk_level, churn_probability,
        top_drivers, profile, pos_drivers, neg_drivers
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Fallback Strategy Engine
# ─────────────────────────────────────────────────────────────────────────────
def _build_unique_fallback_strategy(
    customer_id: str,
    industry: str,
    risk_level: str,
    churn_probability: float,
    top_drivers: list,
    profile: dict,
    pos_drivers: list = None,
    neg_drivers: list = None
) -> dict:
    """
    FIX #3 — Returns the full structured output schema even without Gemini.
    Each field is built from actual customer metrics — no generic boilerplate.
    """
    ind      = industry.lower()
    prob_pct = round(churn_probability * 100, 1)
    profile  = profile or {}
    pos_drivers = pos_drivers or []
    neg_drivers = neg_drivers or []
    top_pos = pos_drivers[0] if pos_drivers else "usage pattern change"
    top_neg = neg_drivers[0] if neg_drivers else "established account history"

    # Build risk_drivers and protective_factors arrays from actual SHAP data
    def _make_driver_list(drivers_list: list, top_drivers_raw: list, is_positive: bool) -> list:
        out = []
        for d in top_drivers_raw[:3]:
            if not isinstance(d, dict):
                continue
            if is_positive and d.get("impact", 0) <= 0:
                continue
            if not is_positive and d.get("impact", 0) >= 0:
                continue
            feat = d.get("feature", "")
            val  = d.get("feature_value", "N/A")
            imp  = d.get("importance", 0.0)
            direction_word = "drives churn risk" if is_positive else "reduces churn likelihood"
            out.append({
                "feature": feat,
                "value":   str(val) if val is not None else "N/A",
                "reason":  f"{feat} = {val} ({imp:.1f}% importance) {direction_word}."
            })
        return out

    risk_driver_list       = _make_driver_list(pos_drivers, top_drivers, True)
    protective_factor_list = _make_driver_list(neg_drivers, top_drivers, False)

    # ── OTT ──────────────────────────────────────────────────────
    if ind == "ott":
        watch_hours   = profile.get("Avg Monthly Watch Hours", 15.0)
        days_inactive = profile.get("Days Since Last Login", 7)
        sub_type      = str(profile.get("Subscription Type", "Standard"))
        tickets       = profile.get("Support Tickets", 0)
        try: watch_hours   = float(watch_hours)
        except: watch_hours = 15.0
        try: days_inactive = int(days_inactive)
        except: days_inactive = 7

        if churn_probability >= 0.60:
            if watch_hours < 15 or "Watch" in str(top_pos):
                rec = f"Re-engagement for {customer_id}: 50% Off 3-Month {sub_type} Upgrade ({watch_hours} hrs/mo)"
                summary = (f"Subscriber {customer_id} is at {risk_level} churn risk ({prob_pct}%) driven by "
                           f"critically low viewing engagement ({watch_hours} hrs/month) and {days_inactive} days "
                           f"since last login. Immediate content re-activation is required.")
                risk_exp = f"Low watch hours ({watch_hours} hrs/mo) is the primary SHAP churn driver, indicating content disengagement."
                recs = [
                    f"Deploy personalised top-5 content recommendations for their {sub_type} tier immediately.",
                    f"Offer 50% discount on 3-month Ultra-HD Premium upgrade to re-engage {customer_id}.",
                    "Set automated re-engagement push alert if no login occurs within 7 days of offer."
                ]
                actions = [
                    f"Within 24hrs: Send personalised email to {customer_id} with curated watchlist.",
                    f"Within 48hrs: Apply 50% discount promo to account {customer_id}.",
                    "Within 7 days: Review login activity and escalate if no session recorded."
                ]
            elif tickets >= 2 or "Ticket" in str(top_pos):
                rec = f"VIP Support Escalation for {customer_id}: 1 Month Free {sub_type} ({tickets} tickets)"
                summary = (f"Subscriber {customer_id} is at {risk_level} risk ({prob_pct}%) driven by "
                           f"{tickets} unresolved support tickets creating service friction.")
                risk_exp = f"{tickets} support tickets is the primary churn driver — unresolved friction accelerates cancellation."
                recs = [
                    f"Assign senior support lead to resolve all {tickets} open tickets for {customer_id}.",
                    f"Credit 1 full month {sub_type} subscription as a proactive goodwill gesture.",
                    "Verify streaming compatibility across all registered devices."
                ]
                actions = [
                    f"Within 12hrs: Assign escalation specialist to {customer_id}'s ticket queue.",
                    "Within 24hrs: Issue subscription credit to account.",
                    "Within 72hrs: Follow-up satisfaction check-in call."
                ]
            else:
                rec = f"Annual Lock-in for {customer_id}: 30% Off {sub_type} ({days_inactive}d inactive)"
                summary = (f"Subscriber {customer_id} shows {risk_level} risk ({prob_pct}%) after "
                           f"{days_inactive} days of inactivity on their {sub_type} plan.")
                risk_exp = f"{days_inactive} days since last login is the top churn driver, suggesting disengagement."
                recs = [
                    f"Propose annual {sub_type} lock-in at 30% discount over monthly rate.",
                    "Add 2 additional profile slots at zero extra charge as loyalty incentive.",
                    "Schedule automated loyalty milestone reward every 90 days of continuous subscription."
                ]
                actions = [
                    f"Within 24hrs: Send annual plan proposal to {customer_id}.",
                    "Within 72hrs: Follow up if no response received.",
                    "Day 7: Assign relationship manager if still inactive."
                ]
        elif churn_probability >= 0.30:
            rec = f"Proactive Perk for {customer_id}: 30-Day Premium Feature Access ({watch_hours} hrs/mo)"
            summary = (f"Subscriber {customer_id} shows moderate engagement ({watch_hours} hrs/mo, "
                       f"last login {days_inactive} days ago) with {prob_pct}% churn risk. "
                       f"Proactive perks will maintain retention momentum.")
            risk_exp = f"Moderate watch hours ({watch_hours} hrs/mo) and {days_inactive} day login gap form a moderate risk pattern."
            recs = [
                f"Grant 30-day complimentary premium access on {customer_id}'s {sub_type} tier.",
                f"Push genre-matched recommendations based on their {watch_hours} hrs/mo watch benchmark.",
                "Enrol in quarterly subscriber loyalty appreciation program."
            ]
            actions = [
                f"Within 48hrs: Apply premium trial to {customer_id}'s account.",
                "Day 3: Send genre recommendation email.",
                "Day 30: Review if engagement improved before trial ends."
            ]
        else:
            rec = f"Loyalty Milestone for {customer_id}: Early Premiere Access ({watch_hours} Watch Hrs)"
            summary = (f"Subscriber {customer_id} has excellent account health ({prob_pct}% churn risk). "
                       f"Strong watch engagement ({watch_hours} hrs/mo, {days_inactive} days since login) "
                       f"anchors solid retention.")
            risk_exp = f"Low risk driven by healthy watch engagement ({watch_hours} hrs/mo) — no immediate intervention required."
            recs = [
                f"Reward {customer_id} with exclusive early premiere access for upcoming season launches.",
                f"Maintain {sub_type} plan satisfaction with monthly surprise loyalty perks.",
                "Send annual membership appreciation campaign with milestone milestone milestone badge."
            ]
            actions = [
                f"This week: Issue early premiere access token to {customer_id}.",
                "Monthly: Trigger automated loyalty perk delivery.",
                "Quarterly: Review account health and upgrade offer eligibility."
            ]

    # ── Banking ──────────────────────────────────────────────────
    elif ind == "banking":
        inactive_months = profile.get("Months_Inactive_12_mon", 2)
        trans_ct        = profile.get("Total_Trans_Ct", 45)
        trans_amt       = profile.get("Total_Trans_Amt", 3500)
        revol_bal       = profile.get("Total_Revolving_Bal", 1200)
        try: inactive_months = int(inactive_months)
        except: inactive_months = 2
        try: trans_ct = int(trans_ct)
        except: trans_ct = 45
        try: trans_amt = float(trans_amt)
        except: trans_amt = 3500.0
        try: revol_bal = float(revol_bal)
        except: revol_bal = 1200.0

        if churn_probability >= 0.60:
            if inactive_months >= 3 or "Inactive" in str(top_pos):
                rec = f"Card Reactivation for {customer_id}: 5,000 Pts + 3x Cashback ({inactive_months} Mo Inactive)"
                summary = (f"Account {customer_id} is at {risk_level} risk ({prob_pct}%) following "
                           f"{inactive_months} months of inactivity and only {trans_ct} total transactions. "
                           f"Proactive relationship manager outreach is urgently required.")
                risk_exp = f"{inactive_months} months of account inactivity is the top SHAP churn driver, signalling disengagement."
                recs = [
                    f"Assign dedicated Relationship Officer for a personal check-in call with Account {customer_id}.",
                    f"Credit 5,000 bonus reward points on completing 3 transactions in the next 30 days.",
                    f"Waive annual card maintenance fee for {customer_id} as a reactivation incentive."
                ]
                actions = [
                    f"Within 24hrs: Trigger outbound call to {customer_id} from Relationship Team.",
                    "Within 48hrs: Apply 5,000-point reactivation bonus to account.",
                    "Day 30: Review if 3 qualifying transactions were completed."
                ]
            elif trans_ct < 30 or "Trans" in str(top_pos):
                rec = f"Spend Multiplier for {customer_id}: 3x Points on Next 10 Purchases ({trans_ct} Txns)"
                summary = (f"Account {customer_id} shows critically low transaction velocity "
                           f"({trans_ct} transactions, ${trans_amt:.0f} volume) driving a {prob_pct}% churn risk. "
                           f"Spend stimulation is the primary intervention.")
                risk_exp = f"Low transaction count ({trans_ct}) is the top SHAP driver, indicating card underutilisation."
                recs = [
                    f"Activate 3x reward multiplier on dining, groceries, and travel for {customer_id} for 60 days.",
                    f"Send personalised spend opportunity summary — ${trans_amt:.0f} current volume vs. peer average.",
                    "Propose auto-bill pay setup with a $25 statement credit activation bonus."
                ]
                actions = [
                    f"Within 24hrs: Enable 3x reward multiplier on {customer_id}'s card.",
                    "Within 48hrs: Send personalised spend insights email.",
                    "Day 60: Review transaction uplift — escalate if no change."
                ]
            else:
                rec = f"Balance Restructuring for {customer_id}: 0% APR Transfer (${int(revol_bal)} Revolving Bal)"
                summary = (f"Account {customer_id} carries a ${revol_bal:.0f} revolving balance with a {prob_pct}% churn probability. "
                           f"Credit restructuring addresses the primary financial friction.")
                risk_exp = f"Revolving balance of ${revol_bal:.0f} is the primary churn risk driver, creating payment stress."
                recs = [
                    f"Offer 0% introductory APR on balance transfers for 12 months to Account {customer_id}.",
                    "Provide low-interest debt consolidation option for the revolving balance.",
                    "Schedule a financial advisory session with Senior Wealth Management team."
                ]
                actions = [
                    f"Within 24hrs: Send 0% APR balance transfer offer to {customer_id}.",
                    "Within 72hrs: Assign financial advisor if customer responds.",
                    "Day 14: Follow up on whether transfer was completed."
                ]
        elif churn_probability >= 0.30:
            rec = f"Engagement Boost for {customer_id}: 2x Reward Multiplier (${int(trans_amt)} Spend Vol)"
            summary = (f"Account {customer_id} shows moderate activity ({trans_ct} transactions, "
                       f"{inactive_months} inactive months) at {prob_pct}% churn risk. "
                       f"Targeted incentives will strengthen engagement.")
            risk_exp = f"Moderate transaction volume (${trans_amt:.0f}) with {inactive_months} inactive months forms a medium risk signal."
            recs = [
                f"Apply 2x reward point multiplier on {customer_id}'s top spending categories for 90 days.",
                "Provide complimentary credit monitoring and fraud protection tier upgrade.",
                "Conduct semi-annual card benefits review and credit limit optimisation."
            ]
            actions = [
                f"Within 48hrs: Enable 2x multiplier on {customer_id}'s account.",
                "Day 7: Send benefits upgrade notification.",
                "Day 90: Review engagement metrics and decide on continued incentive."
            ]
        else:
            # LOW risk — dynamic headline based on strongest retention anchor
            if trans_ct >= 60:
                rec = f"Velocity VIP Reward for {customer_id}: {trans_ct} Txns Milestone Cashback"
            elif trans_amt >= 5000:
                rec = f"Spend Volume Elite for {customer_id}: ${int(trans_amt)} Category Upgrade Reward"
            elif revol_bal >= 1500:
                rec = f"Credit Balance Privilege for {customer_id}: Preferred APR + Fee Waiver"
            else:
                rec = f"Preferred Status for {customer_id}: Zero Foreign Fees + 2,500 Loyalty Points"

            summary = (f"Account {customer_id} demonstrates excellent relationship health at {prob_pct}% churn risk, "
                       f"anchored by {trans_ct} transactions totalling ${trans_amt:.0f}. "
                       f"Proactive recognition reinforces this positive relationship.")
            risk_exp = f"Very low churn risk ({prob_pct}%) anchored by strong transaction behaviour ({trans_ct} txns, ${trans_amt:.0f} volume)."
            recs = [
                f"Upgrade {customer_id} to Preferred Banking status with zero foreign transaction fees.",
                "Offer complimentary travel insurance and concierge service benefit tier.",
                "Send annual relationship milestone gift with 2,500 bonus loyalty points."
            ]
            actions = [
                f"This week: Issue Preferred Banking status to {customer_id}.",
                "Monthly: Ensure benefit tier notifications are personalised.",
                "Annually: Conduct relationship health review and reward milestone."
            ]

    # ── Telecom ──────────────────────────────────────────────────
    else:
        monthly_charge = profile.get("Monthly Charge", profile.get("MonthlyCharge", 75))
        contract       = str(profile.get("Contract", "Month-to-Month"))
        tenure         = profile.get("Tenure in Months", 12)
        try: monthly_charge = float(monthly_charge)
        except: monthly_charge = 75.0

        if churn_probability >= 0.60:
            discount_amt = round(monthly_charge * 0.15, 2)
            new_charge   = round(monthly_charge * 0.85, 2)
            rec = f"Rate Relief for {customer_id}: 15% Discount (${discount_amt}/mo savings, ${new_charge} new rate)"
            summary = (f"Customer {customer_id} is at {risk_level} churn risk ({prob_pct}%) driven by "
                       f"rate sensitivity on their ${monthly_charge}/mo {contract} plan. "
                       f"Targeted billing relief directly addresses the primary SHAP driver.")
            risk_exp = f"Monthly charge of ${monthly_charge} on a {contract} contract is the top SHAP churn driver."
            recs = [
                f"Apply 15% monthly discount: ${monthly_charge}/mo → ${new_charge}/mo for Customer {customer_id}.",
                f"Propose 12-month contract upgrade with 2 months free to secure long-term retention.",
                "Enrol {customer_id} in Tier-1 Priority Support for 24/7 access."
            ]
            actions = [
                f"Within 24hrs: Apply billing discount to {customer_id}'s account.",
                f"Within 48hrs: Send contract upgrade proposal with comparison chart.",
                "Day 14: Follow up on contract upgrade acceptance."
            ]
        else:
            rec = f"Loyalty Perk for {customer_id}: Free Speed Boost ({tenure} Mo Tenure Milestone)"
            summary = (f"Customer {customer_id} maintains a stable account at {prob_pct}% churn risk "
                       f"with {tenure} months tenure on a ${monthly_charge}/mo {contract} plan. "
                       f"Proactive loyalty rewards reinforce retention.")
            risk_exp = f"Low churn risk ({prob_pct}%) with {tenure} months tenure and ${monthly_charge}/mo stable billing."
            recs = [
                f"Apply complimentary internet speed upgrade for Customer {customer_id} as tenure milestone reward.",
                f"Issue 1,000 loyalty points redeemable on accessories or bill credits.",
                "Conduct annual plan review to ensure optimal plan alignment and pricing."
            ]
            actions = [
                f"This week: Trigger speed upgrade for {customer_id}'s connection.",
                "Day 7: Issue loyalty points to account.",
                "Day 30: Send personalised tenure milestone thank-you message."
            ]

    return {
        "summary":            summary,
        "risk_explanation":   risk_exp,
        "risk_drivers":       risk_driver_list,
        "protective_factors": protective_factor_list,
        "recommendation":     rec,
        "recommendations":    recs,
        "action_items":       actions
    }


# ─────────────────────────────────────────────────────────────────────────────
# Communication Generator
# ─────────────────────────────────────────────────────────────────────────────
def generate_ai_communication(
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
    pos_drivers, _ = _format_shap_features_for_llm(industry, top_drivers, profile)
    risk_context   = "; ".join(pos_drivers[:2]) if pos_drivers else "usage pattern change"

    CHANNEL_SPECS = {
        "email":       "Write a formal 2-3 paragraph retention email with subject line, personalised greeting, clear offer, and call-to-action (150-200 words).",
        "sms":         "Write a concise single SMS under 160 characters with clear offer and reply CTA.",
        "whatsapp":    "Write a friendly WhatsApp message with bolded offer, natural line breaks, and clear CTA (80-120 words).",
        "call_script": "Write a phone script with [OBJECTIVE], [OPENING], [VALUE PITCH], and [CLOSE] sections."
    }
    spec = CHANNEL_SPECS.get(channel, CHANNEL_SPECS["email"])

    prompt = f"""You are a customer retention copywriter for a {industry.upper()} brand.
Write a personalised {channel.upper()} retention message for Customer {customer_id}.

Context:
- Churn Risk: {risk_level} ({round(churn_probability*100, 1)}%)
- Key Factors: {risk_context}
- Retention Offer: {recommendation}
- Channel: {channel}
- Tone: {tone}

Instructions: {spec}
DO NOT mention "SHAP", "churn probability", or any ML/model terminology.

Return ONLY valid JSON:
{{
  "subject": "Subject line or descriptor",
  "content": "Full message text"
}}"""

    llm_raw = call_llm_api(prompt)
    if llm_raw:
        try:
            cleaned = llm_raw.replace("```json", "").replace("```", "").strip()
            start = cleaned.find("{")
            end   = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                cleaned = cleaned[start:end]
            data = json.loads(cleaned)
            if data.get("content"):
                return {
                    "channel": channel,
                    "tone":    tone,
                    "subject": data.get("subject", ""),
                    "content": data.get("content", ""),
                    "body":    data.get("content", "")
                }
        except Exception as e:
            logging.warning(f"[Communication] JSON parse error: {e}")

    # Static fallback message
    offer = recommendation or "an exclusive loyalty offer"
    if channel == "sms":
        content = f"Hi {customer_id}! We have an exclusive offer for you: {offer[:70]}. Reply YES to claim. T&Cs apply."
        if len(content) > 160:
            content = content[:157] + "..."
        subject = "SMS Notification"
    elif channel == "whatsapp":
        content = (f"Hello! 👋\n\nWe value your {industry.title()} relationship.\n\n"
                   f"✨ *Exclusive Offer Reserved for You:*\n👉 *{offer}*\n\nReply *YES* to activate now!")
        subject = "WhatsApp Outreach"
    elif channel == "call_script":
        content = (f"[OBJECTIVE] Retain Customer {customer_id}\n"
                   f"[OPENING] Hello, I'm calling from the {industry.title()} retention team regarding your account...\n"
                   f"[VALUE PITCH] We've pre-approved an exclusive offer: {offer}.\n"
                   f"[CLOSE] Can we apply this to your account today?")
        subject = "Call Script"
    else:
        subject = f"Exclusive Offer for Account {customer_id}"
        content = (f"Dear Customer {customer_id},\n\nThank you for being a valued customer. "
                   f"We have pre-approved an exclusive offer for you:\n\n{offer}\n\n"
                   f"Please reply to this email to claim your offer.\n\nBest regards,\nRetention Team")

    return {"channel": channel, "tone": tone, "subject": subject, "content": content, "body": content}
