# app/gpt_connector.py (Full corrected version - FINAL FIX FOR INTERVENTIONS)

import requests
from datetime import datetime
from app.sec_parser import extract_deal_terms


def assemble_deal_profile(nct_id: str, sec_text: str, sec_url: str = "[SEC filing URL placeholder]") -> dict:
    discrepancies = []
    clinical_data = {}
    ct_api_error_detail = "No error" 

    try:
        response = requests.get(f"https://clinicaltrials.gov/api/v2/studies/{nct_id}")
        
        raw_ct_response_json = {}
        try:
            raw_ct_response_json = response.json()
            print("DEBUG 1: Raw CT.gov API Response (from .json()):", raw_ct_response_json)
        except ValueError: 
            print(f"DEBUG 1: Raw CT.gov API Response (NOT JSON): {response.text[:500]}...")
            raw_ct_response_json = {"error": "Response was not valid JSON"}

        response.raise_for_status() 
        
        clinical_data = raw_ct_response_json  
        print("DEBUG 2: Assigned clinical_data (after assignment):", clinical_data)

    except requests.exceptions.HTTPError as http_err:
        ct_api_error_detail = (
            f"HTTP Error for NCT {nct_id}: Status {http_err.response.status_code}. "
            f"Reason: {http_err.response.reason}. "
            f"Response Text: {http_err.response.text[:200]}..." 
        )
        discrepancies.append(ct_api_error_detail)
        print(f"ERROR: {ct_api_error_detail}")
    except requests.exceptions.ConnectionError as conn_err:
        ct_api_error_detail = f"Connection Error for NCT {nct_id}: {conn_err}"
        discrepancies.append(ct_api_error_detail)
        print(f"ERROR: {ct_api_error_detail}")
    except requests.exceptions.Timeout as timeout_err:
        ct_api_error_detail = f"Timeout Error for NCT {nct_id}: {timeout_err}"
        discrepancies.append(ct_api_error_detail)
        print(f"ERROR: {ct_api_error_detail}")
    except requests.exceptions.RequestException as req_err: 
        ct_api_error_detail = f"General Request Error for NCT {nct_id}: {req_err}"
        discrepancies.append(ct_api_error_detail)
        print(f"ERROR: {ct_api_error_detail}")
    except Exception as e: 
        ct_api_error_detail = f"An unexpected error occurred during CT.gov API call for NCT {nct_id}: {e}"
        discrepancies.append(ct_api_error_detail)
        print(f"ERROR: {ct_api_error_detail}")


    # --- Robustly get top-level modules from protocolSection ---
    protocol_section = clinical_data.get("protocolSection", {})
    status_module = protocol_section.get("statusModule", {})
    identification_module = protocol_section.get("identificationModule", {})
    design_module = protocol_section.get("designModule", {})
    sponsor_collaborators_module = protocol_section.get("sponsorCollaboratorsModule", {})
    conditions_module = protocol_section.get("conditionsModule", {})
    arms_interventions_module = protocol_section.get("armsInterventionsModule", {}) # Use armsInterventionsModule
    results_section = clinical_data.get("resultsSection", {})


    sec_data = extract_deal_terms(sec_text) 
    discrepancies.extend(sec_data.get("cross_source_discrepancies", []))

    ctgov_date = status_module.get("lastUpdatePostDateStruct", {}).get("date")
    deal_date = sec_data.get("deal_date")

    if ctgov_date and deal_date:
        try:
            ctgov_dt = datetime.strptime(ctgov_date, "%Y-%m-%d")
            deal_dt = None
            for fmt in ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"]:
                try:
                    deal_dt = datetime.strptime(deal_date, fmt)
                    break
                except ValueError:
                    continue 
            if not deal_dt:
                discrepancies.append("SEC deal date format unrecognized.")
            elif ctgov_dt > deal_dt:
                discrepancies.append("ClinicalTrials.gov data updated after deal signing; phase may not reflect status at deal time.")
        except ValueError as e: 
            discrepancies.append(f"Date parsing failed for CT.gov or SEC deal date: {e}")
        except Exception as e: 
            discrepancies.append(f"An unexpected error occurred during date comparison: {e}")

    confidence = sec_data.get("confidence_score", "Medium")
    if discrepancies:
        confidence = "Medium" if confidence == "High" else "Low"
    manual_review = confidence != "High"

    # --- Extracting specific fields using the robust module assignments ---
    primary_nct_id = identification_module.get("nctId", nct_id)
    trial_overall_status = status_module.get("overallStatus")
    trial_completion_date = status_module.get("completionDateStruct", {}).get("date")
    last_update_post_date = ctgov_date 
    
    development_stage_at_signing = design_module.get("phases", [])
    if development_stage_at_signing:
        development_stage_at_signing = development_stage_at_signing[0] 
    else:
        development_stage_at_signing = None

    lead_sponsor_name = sponsor_collaborators_module.get("leadSponsor", {}).get("name")
    collaborator_names = [c.get("name") for c in sponsor_collaborators_module.get("collaborators", [])]
    
    conditions_list = conditions_module.get("conditions", []) 
    
    # FIX APPLIED HERE: Corrected keys for intervention objects
    interventions_list = []
    for i in arms_interventions_module.get("interventions", []): 
        interventions_list.append({
            "type": i.get("type"),          # This is the 'type' field within the intervention object
            "name": i.get("name")           # This is the 'name' field within the intervention object
        })

    return {
        "primary_nct_id": primary_nct_id,
        "trial_overall_status": trial_overall_status,
        "trial_completion_date": trial_completion_date,
        "last_update_post_date": last_update_post_date,
        "development_stage_at_signing": development_stage_at_signing,
        "lead_sponsor": lead_sponsor_name,
        "collaborators": collaborator_names,
        "conditions": conditions_list,
        "interventions": interventions_list,
        **sec_data,
        "confidence_score": confidence,
        "manual_review_flag": manual_review,
        "cross_source_discrepancies": discrepancies,
        "supporting_sources": [
            f"https://clinicaltrials.gov/study/{nct_id}" if clinical_data else ct_api_error_detail,
            sec_url
        ]
    }