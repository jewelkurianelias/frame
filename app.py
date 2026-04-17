import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the Gemini client. 
# It will automatically securely pull your API key from the environment variables.
client = genai.Client()

@app.route('/', methods=['POST'])
def noa_webhook():
    try:
        # 1. Receive the webhook payload (transcribed text) from Noa
        data = request.get_json()
        
        # Note: You may need to adjust the "text" key below to match 
        # the exact JSON structure Noa sends in the Hack tab.
        user_text = data.get("text", "")
        
        if not user_text:
            return jsonify({"error": "No text received"}), 400

        # 2. Forward that data to the Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
        )

        # 3. Return the text response back to Noa for display and TTS
        return jsonify({"message": response.text}), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Render assigns a dynamic port, so we catch it here.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
