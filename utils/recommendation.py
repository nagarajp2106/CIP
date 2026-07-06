"""
Recommendation Utilities — Product recommendation engine.
"""
from config import PRODUCT_LIST


def generate_recommendations(customer_data: dict, existing_products: list = None) -> list[dict]:
    """
    Generate product recommendations based on customer profile.

    Args:
        customer_data: Dict with customer fields
        existing_products: List of products the customer already has

    Returns:
        List of recommendation dicts sorted by score
    """
    if existing_products is None:
        existing_products = []

    recommendations = []
    age = customer_data.get("age", 35)
    income = customer_data.get("income", 40000)
    balance = customer_data.get("balance", 5000)
    credit_score = customer_data.get("credit_score", 650)

    # Product eligibility rules
    rules = {
        "Savings Account": {
            "min_income": 0, "min_age": 18, "min_credit_score": 0,
            "base_score": 80,
            "reason": "Build emergency fund and earn interest on deposits."
        },
        "Current Account": {
            "min_income": 40000, "min_age": 21, "min_credit_score": 0,
            "base_score": 60,
            "reason": "Ideal for business transactions and high-volume banking."
        },
        "Credit Card": {
            "min_income": 25000, "min_age": 21, "min_credit_score": 650,
            "base_score": 55,
            "reason": "Build credit history and earn rewards on purchases."
        },
        "Home Loan": {
            "min_income": 40000, "min_age": 25, "min_credit_score": 650,
            "base_score": 50,
            "reason": "Competitive rates for home ownership financing."
        },
        "Personal Loan": {
            "min_income": 20000, "min_age": 21, "min_credit_score": 600,
            "base_score": 55,
            "reason": "Flexible financing for personal needs."
        },
        "Fixed Deposit": {
            "min_income": 15000, "min_age": 18, "min_credit_score": 0,
            "base_score": 65,
            "reason": "Guaranteed returns with higher interest than savings."
        },
        "Insurance": {
            "min_income": 20000, "min_age": 25, "min_credit_score": 0,
            "base_score": 60,
            "reason": "Financial protection for you and your family."
        },
        "Investment Plan": {
            "min_income": 50000, "min_age": 25, "min_credit_score": 600,
            "base_score": 45,
            "reason": "Grow your wealth with diversified investment options."
        },
    }

    for product, rule in rules.items():
        if product in existing_products:
            continue

        # Check eligibility
        if age < rule["min_age"] or income < rule["min_income"] or credit_score < rule["min_credit_score"]:
            continue

        # Calculate score
        score = rule["base_score"]
        score += min((income - rule["min_income"]) / 10000, 15)  # Income bonus
        score += min((credit_score - rule.get("min_credit_score", 0)) / 50, 10)  # Credit bonus
        score += min(balance / 20000, 10)  # Balance bonus
        score = min(round(score, 1), 99)

        recommendations.append({
            "product": product,
            "score": score,
            "reason": rule["reason"]
        })

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations


def get_product_match_score(customer_data: dict, product: str) -> float:
    """Get match score for a specific product (0-100)."""
    recs = generate_recommendations(customer_data)
    for rec in recs:
        if rec["product"] == product:
            return rec["score"]
    return 0.0
