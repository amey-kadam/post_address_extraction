import pandas as pd
from fuzzywuzzy import process
import re
import json

# Load CSV data
df = pd.read_csv('datas.csv')  # Replace with your CSV file path

def validate_and_correct_address(address):
    components = re.findall(r'\b\w+\b', address.lower())

    corrected_components = []
    for component in components:
        # Check if it's a potential state or district
        if len(component) > 3:  # Assuming state/district names are longer than 3 characters
            best_match_state = process.extractOne(component, df['StateName'].unique().tolist())
            best_match_district = process.extractOne(component, df['District'].unique().tolist())

            if best_match_state and best_match_state[1] > 80:
                corrected_components.append(best_match_state[0])
            elif best_match_district and best_match_district[1] > 80:
                corrected_components.append(best_match_district[0])
            else:
                corrected_components.append(component)
        else:
            corrected_components.append(component)

    # Handle incomplete pincode
    pincode = re.search(r'\b\d{5,6}\b', address)
    if pincode:
        pincode = pincode.group()
        if len(pincode) == 5:
            # Find matching 6-digit pincodes in the CSV
            possible_pincodes = df[df['Pincode'].astype(str).str.startswith(pincode)]['Pincode'].tolist()
            if possible_pincodes:
                corrected_components.append(str(possible_pincodes[0]))
            else:
                corrected_components.append(pincode)
        else:
            corrected_components.append(pincode)

    # Combine corrected components into a corrected address
    corrected_address = ' '.join(corrected_components)

    # Re-check for state and district matches based on the corrected address
    state_match = process.extractOne(corrected_address, df['StateName'].unique().tolist())
    district_match = process.extractOne(corrected_address, df['District'].unique().tolist())

    if state_match and state_match[1] > 90:
        corrected_components.append(state_match[0])
    elif district_match and district_match[1] > 90:
        corrected_components.append(district_match[0])

    return corrected_address


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
        address_parts['address'] = address_parts['address'].replace(address_parts['pincode'], '').strip()

    # Extract district
    district_match = process.extractOne(address, df['District'].unique(), score_cutoff=90)
    if district_match:
        address_parts['district'] = district_match[0]
        address_parts['address'] = re.sub(r'\b' + re.escape(district_match[0]) + r'\b', '', address_parts['address'], flags=re.IGNORECASE).strip()

    # Extract state
    state_match = process.extractOne(address, df['StateName'].unique(), score_cutoff=90)
    if state_match:
        address_parts['state'] = state_match[0]
        address_parts['address'] = re.sub(r'\b' + re.escape(state_match[0]) + r'\b', '', address_parts['address'], flags=re.IGNORECASE).strip()

    # Clean up the address
    address_parts['address'] = re.sub(r'\s+', ' ', address_parts['address']).strip(', ')

    return address_parts

def process_gemini_response(response):
    """Process the Gemini API response and handle potential errors."""
    try:
        if not response.candidates:
            return {"error": "The API returned an empty response. No text could be extracted."}

        candidate = response.candidates[0]

        if hasattr(candidate, 'content') and candidate.content.parts:
            extracted_text = candidate.content.parts[0].text
        elif hasattr(candidate, 'text'):
            extracted_text = candidate.text
        else:
            return {"error": f"Unable to extract text. Response structure: {candidate}"}

        # Validate and correct the extracted address
        corrected_address = validate_and_correct_address(extracted_text)

        # Parse the corrected address into structured format
        parsed_address = parse_address(corrected_address)

        return parsed_address
    except Exception as e:
        return {"error": f"Error processing response: {str(e)}"}