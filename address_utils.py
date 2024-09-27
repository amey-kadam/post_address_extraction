import json
import re
from fuzzywuzzy import process


with open('indian_states_districts.json') as f:
    states_districts = json.load(f)

def process_gemini_response(response):
    """Process the Gemini API response and handle potential errors."""
    try:

        if not response.candidates:
            return {"error": "The API returned an empty response. No text could be extracted."}

        candidate = response.candidates[0]

        # Extract the text from the response candidate
        if hasattr(candidate, 'content') and candidate.content.parts:
            extracted_text = candidate.content.parts[0].text
        elif hasattr(candidate, 'text'):
            extracted_text = candidate.text
        else:
            return {"error": f"Unable to extract text. Response structure: {candidate}"}

        # Validate and correct the extracted address
        corrected_address = validate_and_correct_address(extracted_text)

        # Parse the corrected address (pass only the remaining address part)
        parsed_address = parse_address(corrected_address['address'])

        # Return a structured response including the corrections
        return {
            "extracted_text": extracted_text,
            "corrected_address": corrected_address,
            "parsed_address": parsed_address
        }

    except Exception as e:
        return {"error": f"Error processing response: {str(e)}"}



def validate_and_correct_address(address):
    components = re.findall(r'\b\w+\b', address.lower())
    corrected_components = {
        'district': '',
        'state': '',
        'pincode': '',
        'address': ''
    }

    # Similar matching logic
    found_district = None
    found_state = None

    for component in components:
        for state, districts in states_districts.items():
            if component in map(str.lower, districts):
                found_district = component
                found_state = state
                break

    # If district is found, check if the state is correct
    if found_district and found_state:
        corrected_state = found_state
        if not any(found_district.lower() == district.lower() for district in states_districts[corrected_state]):
            corrected_state = None
            for state, districts in states_districts.items():
                if found_district.lower() in map(str.lower, districts):
                    corrected_state = state
                    break

        corrected_components['district'] = found_district
        corrected_components['state'] = corrected_state if corrected_state else found_state
    else:
        # Use FuzzyWuzzy for fallback
        best_match_state = process.extractOne(component, list(states_districts.keys()))
        all_districts = [district for districts in states_districts.values() for district in districts]
        best_match_district = process.extractOne(component, all_districts)

        if best_match_state and best_match_state[1] > 80:
            corrected_components['state'] = best_match_state[0]
        elif best_match_district and best_match_district[1] > 80:
            corrected_components['district'] = best_match_district[0]

    # Handle pincode
    pincode = re.search(r'\b\d{5,6}\b', address)
    if pincode:
        corrected_components['pincode'] = pincode.group()

    corrected_components['address'] = address  # Keep remaining address
    return corrected_components


def parse_address(address):
    """Parse the address into state, district, pincode, and remaining address."""
    address_parts = {
        'state': '',
        'district': '',
        'pincode': '',
        'address': address
    }

    # Extract pincode
    pincode_match = re.search(r'\b\d{6}\b', address)
    if pincode_match:
        address_parts['pincode'] = pincode_match.group()
        address_parts['address'] = address.replace(pincode_match.group(), '').strip()

    # Extract district using JSON and FuzzyWuzzy
    for state, districts in states_districts.items():
        for district in districts:
            if district.lower() in address.lower():
                address_parts['district'] = district
                address_parts['state'] = state
                address_parts['address'] = address.replace(district, '').replace(state, '').strip()

    # Cross-check using JSON if district/state are incorrect
    if not address_parts['district'] or not address_parts['state']:
        all_districts = [district for districts in states_districts.values() for district in districts]
        district_match = process.extractOne(address, all_districts, score_cutoff=90)
        if district_match:
            for state, districts in states_districts.items():
                if district_match[0] in districts:
                    address_parts['district'] = district_match[0]
                    address_parts['state'] = state
                    break

    return address_parts
