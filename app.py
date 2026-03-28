from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import base64
import json
import requests as http_requests
from dotenv import load_dotenv

# Load .env from the frontend folder (where the key is stored)
load_dotenv(os.path.join(os.path.dirname(__file__), 'frontend', '.env'))

app = Flask(__name__, static_folder='frontend')
CORS(app)

# --------------- Gemini Config ---------------
GEMINI_API_KEY = os.getenv('gemini_api_key')
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# --------------- Serve Frontend Files ---------------
@app.route('/')
def serve_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

# Catch-all: serve any file from frontend (so signin.html, register.html, etc. work)
@app.route('/<path:filename>')
def serve_pages(filename):
    return send_from_directory('frontend', filename)

# --------------- Disease Prediction Route ---------------
@app.route('/predict-disease', methods=['POST'])
def predict_disease():
    try:
        # Get form data
        image_file = request.files.get('image')
        crop = request.form.get('crop', 'Unknown crop')
        symptoms = request.form.get('symptoms', '')

        if not image_file:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        # Read and encode image to base64
        image_bytes = image_file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

        # Determine MIME type
        mime_type = image_file.content_type or 'image/jpeg'

        # Build the prompt
        prompt = f"""You are an expert agricultural plant pathologist AI. Analyze this image of a {crop} plant leaf/part.

Additional symptoms described by the farmer: {symptoms if symptoms else 'None provided'}

Analyze the image and provide a comprehensive diagnosis. Return your response as a valid JSON object ONLY (no markdown, no code fences) with this exact structure:

{{
    "disease_name": "Name of the disease or 'Healthy' if no disease detected",
    "confidence": "High / Medium / Low",
    "severity": "Mild / Moderate / Severe / None",
    "affected_part": "e.g. Leaves, Stem, Fruit, Roots",
    "pathogen_type": "Fungal / Bacterial / Viral / Nutrient Deficiency / Pest / None",
    "cause": "Brief description of what causes this disease",
    "symptoms_list": ["symptom 1", "symptom 2", "symptom 3"],
    "treatment": ["treatment step 1", "treatment step 2", "treatment step 3"],
    "organic_remedies": ["organic remedy 1", "organic remedy 2"],
    "chemical_treatment": "Recommended chemical/pesticide if applicable, or 'Not required'",
    "prevention": ["prevention tip 1", "prevention tip 2", "prevention tip 3"],
    "additional_notes": "Any other important information for the farmer"
}}"""

        # Call Gemini REST API directly
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }]
        }

        response = http_requests.post(GEMINI_URL, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        # Extract text from Gemini response
        response_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

        # Clean markdown code fences if present
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text[:-3].strip()

        diagnosis = json.loads(response_text)

        return jsonify({'success': True, 'diagnosis': diagnosis})

    except json.JSONDecodeError:
        return jsonify({
            'success': True,
            'diagnosis': {
                'disease_name': 'Analysis Complete',
                'confidence': 'Medium',
                'severity': 'Unknown',
                'affected_part': 'Leaf',
                'pathogen_type': 'Unknown',
                'cause': response_text if 'response_text' in dir() else 'Could not parse response',
                'symptoms_list': [],
                'treatment': ['Please consult a local agricultural expert'],
                'organic_remedies': [],
                'chemical_treatment': 'Consult expert',
                'prevention': [],
                'additional_notes': 'The AI returned an unstructured response. Please try again.'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --------------- Soil Analysis Route ---------------
@app.route('/analyze-soil', methods=['POST'])
def analyze_soil():
    try:
        image_file = request.files.get('image')

        if not image_file:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        image_bytes = image_file.read()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = image_file.content_type or 'image/jpeg'

        prompt = """You are an expert soil scientist and agronomist AI. Analyze this soil image carefully.

Provide a comprehensive soil assessment. Return your response as a valid JSON object ONLY (no markdown, no code fences) with this exact structure:

{
    "moisture_level": "Percentage estimate, e.g. '35%'",
    "moisture_status": "Critically Dry / Dry / Moderate / Moist / Waterlogged",
    "soil_type": "e.g. Sandy, Clay, Loamy, Silt, Black Cotton, Red Laterite",
    "soil_color": "Observed color of the soil",
    "health_score": "A number from 0-100",
    "organic_matter": "Low / Medium / High",
    "ph_estimate": "Estimated pH range, e.g. '6.0 - 6.5'",
    "texture": "Fine / Medium / Coarse",
    "compaction": "Loose / Moderate / Compacted",
    "drainage": "Poor / Moderate / Good / Excessive",
    "issues": ["issue 1", "issue 2"],
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"],
    "suitable_crops": ["crop 1", "crop 2", "crop 3"],
    "fertilizer_advice": "What fertilizer to apply based on soil condition",
    "irrigation_advice": "How much and how often to water",
    "additional_notes": "Any other important observations"
}"""

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                    {"text": prompt}
                ]
            }]
        }

        response = http_requests.post(GEMINI_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        response_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1]
            if response_text.endswith('```'):
                response_text = response_text[:-3].strip()

        analysis = json.loads(response_text)
        return jsonify({'success': True, 'analysis': analysis})

    except json.JSONDecodeError:
        return jsonify({
            'success': True,
            'analysis': {
                'moisture_level': 'N/A', 'moisture_status': 'Unknown',
                'soil_type': 'Unknown', 'soil_color': 'N/A',
                'health_score': '50', 'organic_matter': 'Unknown',
                'ph_estimate': 'N/A', 'texture': 'Unknown',
                'compaction': 'Unknown', 'drainage': 'Unknown',
                'issues': ['Could not fully parse AI response'],
                'recommendations': ['Please try again or consult an expert'],
                'suitable_crops': [], 'fertilizer_advice': 'Consult expert',
                'irrigation_advice': 'Consult expert',
                'additional_notes': response_text if 'response_text' in dir() else 'Analysis incomplete'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --------------- Crop Strategy Route ---------------
@app.route('/crop-strategy', methods=['POST'])
def crop_strategy():
    try:
        data = request.get_json()
        crop = data.get('crop', '')
        area = data.get('area', '')
        soil = data.get('soil', '')
        season = data.get('season', '')
        budget = data.get('budget', '')

        if not crop or not area:
            return jsonify({'success': False, 'error': 'Crop and area are required'}), 400

        prompt = f"""You are an expert Indian agriculture consultant. Analyze the following farming request and provide a DETAILED strategy.

Farmer's Input:
- Crop: {crop}
- Land Area: {area} acres
- Soil Type: {soil}
- Season: {season}
- Budget: ₹{budget}

Return a JSON object with EXACTLY this structure (no markdown, no code blocks, just pure JSON):
{{
    "crop_name": "name of the crop",
    "crop_emoji": "relevant emoji",
    "summary": "2-3 line summary of the strategy",
    "planting_guide": {{
        "best_season": "ideal planting season",
        "seed_variety": "recommended seed variety for India",
        "seed_rate": "X kg per acre",
        "total_seeds": "calculated for given area in kg",
        "spacing": "row and plant spacing",
        "depth": "sowing depth",
        "germination_days": "X-Y days"
    }},
    "cost_breakdown": {{
        "seeds": "₹X,XXX",
        "fertilizer": "₹X,XXX",
        "pesticides": "₹X,XXX",
        "labor": "₹X,XXX",
        "irrigation": "₹X,XXX",
        "misc": "₹X,XXX",
        "total_cost": "₹X,XXX"
    }},
    "fertilizer_plan": [
        "Stage 1: Apply X at sowing",
        "Stage 2: Apply Y at 30 days",
        "Stage 3: Apply Z at flowering"
    ],
    "irrigation_plan": "Detailed irrigation schedule",
    "pest_management": ["pest1 - treatment", "pest2 - treatment"],
    "yield_estimate": {{
        "expected_yield": "X quintal per acre",
        "total_yield": "calculated for given area",
        "market_price": "₹X,XXX per quintal",
        "total_revenue": "₹X,XX,XXX",
        "net_profit": "₹X,XX,XXX",
        "roi_percentage": "X%"
    }},
    "timeline": [
        {{"phase": "Land Preparation", "duration": "X days", "tasks": "description"}},
        {{"phase": "Sowing", "duration": "X days", "tasks": "description"}},
        {{"phase": "Growth", "duration": "X days", "tasks": "description"}},
        {{"phase": "Harvest", "duration": "X days", "tasks": "description"}}
    ],
    "tips": ["tip1", "tip2", "tip3"],
    "govt_schemes": ["relevant scheme 1", "relevant scheme 2"]
}}

Use current Indian market prices. Calculate everything for {area} acres. Be specific with numbers."""

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        }

        response = http_requests.post(GEMINI_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        response_text = result['candidates'][0]['content']['parts'][0]['text'].strip()

        # Clean JSON
        if response_text.startswith('```'):
            response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        strategy = json.loads(response_text)
        return jsonify({'success': True, 'strategy': strategy})

    except json.JSONDecodeError:
        return jsonify({'success': True, 'strategy': {
            'crop_name': crop, 'crop_emoji': '🌱', 'summary': 'Strategy generated. Some data may be approximate.',
            'cost_breakdown': {'total_cost': 'Varies'}, 'yield_estimate': {'net_profit': 'Consult local market'}
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --------------- AI Agriculture Chatbot Route ---------------
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        history = data.get('history', [])

        if not user_message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400

        system_prompt = """You are "KrishiMitra" 🌿, an expert AI Agriculture Assistant for Indian farmers. You help with:
- Crop selection and rotation advice
- Soil health and fertilizer recommendations
- Pest and disease identification & treatment
- Weather-based farming tips
- Organic farming methods
- Government schemes for farmers (PM-KISAN, crop insurance, etc.)
- Market price guidance and selling tips
- Irrigation and water management
- Seed selection and sowing schedules
- Post-harvest storage and processing

CRITICAL LANGUAGE RULE:
- ALWAYS detect which language the user is typing in and respond in THAT SAME language.
- If the user writes in English, reply ONLY in English.
- If the user writes in Hindi, reply ONLY in Hindi.
- If the user writes in Tamil, reply ONLY in Tamil.
- If the user writes in Hinglish (mix of Hindi+English), reply in Hinglish.
- If the user writes in Tanglish (mix of Tamil+English), reply in Tanglish.
- NEVER default to Hindi. Match the user's language exactly.
- Default language is English if you cannot detect the language.

Other Guidelines:
- Always respond in a friendly, helpful tone
- Keep answers concise but informative
- Use simple language that farmers can understand
- Include practical, actionable advice
- Mention specific crop names, fertilizer names, and dosages when relevant
- If asked about non-agriculture topics, politely redirect to farming
- Use bullet points and emojis for better readability"""

        # Build conversation for Gemini
        contents = []
        for msg in history:
            contents.append({
                "role": msg.get("role", "user"),
                "parts": [{"text": msg.get("text", "")}]
            })
        contents.append({
            "role": "user",
            "parts": [{"text": f"{system_prompt}\n\nUser query: {user_message}" if len(contents) == 0 else user_message}]
        })

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            }
        }

        response = http_requests.post(GEMINI_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        reply = result['candidates'][0]['content']['parts'][0]['text'].strip()

        return jsonify({'success': True, 'reply': reply})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🌿 GREEN PULSE Backend running on http://localhost:5000")
    app.run(port=5000, debug=True)
