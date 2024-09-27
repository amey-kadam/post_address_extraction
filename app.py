from flask import Flask, request, jsonify, render_template, redirect, url_for
import google.generativeai as genai
from PIL import Image
import io
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import traceback
from address_utils import process_gemini_response

load_dotenv()

app = Flask(__name__)


api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("No API key found. Please set GEMINI_API_KEY in your .env file.")

genai.configure(api_key=api_key)


model = genai.GenerativeModel('gemini-1.5-flash')

def save_to_json(data):
    """Save the parsed address to a JSON file with a timestamp in the filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"parsed_address_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return filename

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file:
            try:
                # Process the image file and extract the address
                image_bytes = file.read()
                image = Image.open(io.BytesIO(image_bytes))

                prompt = "Extract the full address from this image, including all components such as house number, street, city, district, state, and postal code (if present). Ensure no part of the address is missing. If sometimes you don't see any proper address then just display the text that you see."

                response = model.generate_content([prompt, image])


                parsed_address = process_gemini_response(response)

                # Save the parsed address to a JSON file
                saved_filename = save_to_json(parsed_address)

                parsed_address['saved_file'] = saved_filename

                return redirect(url_for('result', 
                                        address=parsed_address.get('address', ''),
                                        district=parsed_address.get('district', ''),
                                        state=parsed_address.get('state', ''),
                                        pincode=parsed_address.get('pincode', '')))
            except Exception as e:
                error_traceback = traceback.format_exc()
                return jsonify({'error': str(e), 'traceback': error_traceback}), 500

    return render_template('upload.html')

@app.route('/result')
def result():
    """Render the result page with extracted address components."""
    address = request.args.get('address', 'Address not found')
    district = request.args.get('district', '')
    state = request.args.get('state', '')
    pincode = request.args.get('pincode', '')

    return render_template('result.html', address=address, district=district, state=state, pincode=pincode)

if __name__ == '__main__':
    app.run(debug=True)
