import re

def extract_deal_terms(sec_text: str) -> dict:
    deal = {
        "upfront_investment_usd": None,
        "total_deal_value_usd": None,
        "participation_rights": None,
        "deal_date": None,
        "cross_source_discrepancies": [],
        "confidence_score": "Medium",
        "manual_review_flag": True
    }

    upfront_match = re.search(r'\$([0-9,.]+)\s*(million|M)?\s*(in\s+)?(cash|upfront)', sec_text, re.IGNORECASE)
    if upfront_match:
        value = upfront_match.group(1).replace(',', '')
        deal["upfront_investment_usd"] = float(value) * (1e6 if upfront_match.group(2) else 1)
        deal["confidence_score"] = "High"
        deal["manual_review_flag"] = False

    # Adjusted regex to capture "up to X million in milestones" or "total deal value"
    total_match = re.search(r'(total\s+deal\s+value|up\s+to|worth)\s+\$([0-9,.]+)\s*(million|M)?', sec_text, re.IGNORECASE)
    if total_match:
        value = total_match.group(2).replace(',', '') # Group 2 now captures the number
        deal["total_deal_value_usd"] = float(value) * (1e6 if total_match.group(3) else 1) # Group 3 for 'million'
        # If total value is found, and upfront was also high, maintain high confidence
        if deal["confidence_score"] == "High":
            deal["confidence_score"] = "High"
            deal["manual_review_flag"] = False
        else: # If upfront wasn't found, but total was, still medium confidence
            deal["confidence_score"] = "Medium"
            deal["manual_review_flag"] = True # Flag for review if only total is present

    # More robust regex for participation rights (including just percentages)
    rights_match = re.search(r'(royalties\s+of\s+\d+%)|(co-commercialization)|(\d+%)', sec_text, re.IGNORECASE)
    if rights_match:
        # Prioritize full phrase, then co-commercialization, then just percentage
        if rights_match.group(1):
            deal["participation_rights"] = rights_match.group(1)
        elif rights_match.group(2):
            deal["participation_rights"] = rights_match.group(2)
        elif rights_match.group(3):
            deal["participation_rights"] = f"royalties of {rights_match.group(3)}" # Format if only percentage found
        
        # If any rights found, it boosts confidence if it was low, but still flag if not explicit
        if deal["confidence_score"] == "Low":
            deal["confidence_score"] = "Medium"
            deal["manual_review_flag"] = True # Still needs review if not a perfect match
        elif deal["confidence_score"] == "Medium" and not (rights_match.group(1) or rights_match.group(2)):
            deal["manual_review_flag"] = True # Flag if only percentage found, not full phrase

    # FIX APPLIED HERE: More robust regex for deal date (including "Agreement dated")
    date_match = re.search(r'(dated as of|effective as of|entered into on|signed on|agreement dated)\s+(\w+\s+\d{1,2},\s+\d{4})', sec_text, re.IGNORECASE)
    if date_match:
        deal["deal_date"] = date_match.group(2)
        # If date is found, it adds to confidence, but doesn't override financial confidence
        if deal["confidence_score"] == "Medium":
            deal["confidence_score"] = "Medium" # Stays medium if financials were medium
        elif deal["confidence_score"] is None: # If no financials found yet
            deal["confidence_score"] = "Low"
            deal["manual_review_flag"] = True

    # Final check on confidence based on what was found
    if deal["upfront_investment_usd"] is None and deal["total_deal_value_usd"] is None:
        deal["cross_source_discrepancies"].append("Missing upfront and total deal value in SEC text.")
        deal["confidence_score"] = "Low"
        deal["manual_review_flag"] = True
    elif deal["upfront_investment_usd"] is None or deal["total_deal_value_usd"] is None:
        if deal["confidence_score"] == "High": # If one was found with high, but other not
            deal["confidence_score"] = "Medium"
            deal["manual_review_flag"] = True

    return deal