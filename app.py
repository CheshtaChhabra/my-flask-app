import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
# PASTE YOUR GOOGLE KEY HERE
os.environ["GOOGLE_API_KEY"] = "AIzaSyDkU2PGywC9sFY_jYeN8aFD9TpxtT3raIM"
MY_SECRET_API_KEY = "12345"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# DEFINE THE BRAIN (The Prompt)
system_instruction = """
You are 'Smt. Lakshmi', a 65-year-old retired Indian teacher.
You are confused by technology. A scammer is messaging you.
Pretend to be a victim. Keep them talking.
Your GOAL: Extract Bank Accounts, UPI IDs, Phone Numbers.
OUTPUT JSON ONLY:
{
  "reply": "your response to scammer",
  "scam_detected": true,
  "extracted_intelligence": {
     "bankAccounts": [],
     "upiIds": [],
     "phoneNumbers": []
  },
  "agentNotes": "summary"
}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={"response_mime_type": "application/json"},
    system_instruction=system_instruction
)

# --- THE API ENDPOINT (The Door) ---
@app.route('/scam-honeypot', methods=['POST'])
def honeypot():
    api_key = request.headers.get("x-api-key")
    if api_key != MY_SECRET_API_KEY:
        return jsonify({
            "status": "error",
            "message": "Invalid API key"
        }), 401

    # 1. READ THE INCOMING MAIL (From Hackathon System)
    data = request.json
    incoming_msg = data['message']['text']
    history = data.get('conversationHistory', [])
    session_id = data.get('sessionId', 'unknown_session')

    # 2. PREPARE CONTEXT FOR AI
    # We combine history + new message so AI knows what's happening
    full_context = f"History: {history}\n\nNew Message from Scammer: {incoming_msg}"

    # 3. ASK THE BRAIN
    response = model.generate_content(full_context)
    ai_result = json.loads(response.text) # Convert AI text to real data

    # 4. REPORT TO POLICE (The Mandatory Callback)
    # The PDF says we MUST do this if we find data.
    intelligence = ai_result.get('extracted_intelligence', {})
    
    # Check if any list in intelligence is NOT empty
    found_something = any(len(v) > 0 for v in intelligence.values())

    if found_something:
        print("🚨 INTELLIGENCE FOUND! Reporting to GUVI...")
        guvi_payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": len(history) + 1,
            "extractedIntelligence": intelligence,
            "agentNotes": ai_result.get('agentNotes')
        }
        # We wrap this in try/except so if GUVI server is down, our bot doesn't crash
        try:
            requests.post("https://hackathon.guvi.in/api/updateHoneyPotFinalResult", json=guvi_payload, timeout=3)
        except:
            print("Could not reach GUVI server (Normal during testing)")

    # 5. REPLY TO SCAMMER
    return jsonify({
        "status": "success",
        "reply": ai_result['reply']
    })

# --- RUN THE SERVER ---
if __name__ == '__main__':
    app.run(port=5000)
