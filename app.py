import os
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)
client = genai.Client()

@app.route('/', methods=['POST'])
def noa_webhook():
    try:
        # 1. Extract the audio and image files sent by the Noa app
        audio_file = request.files.get('audio')
        image_file = request.files.get('image')
        
        if not audio_file and not image_file:
            return jsonify({"error": "No audio or image received"}), 400

        # 2. Prepare the payload for Gemini
        contents = []
        
        # Add the image if the user tapped to take a photo
        if image_file:
            contents.append(
                types.Part.from_bytes(
                    data=image_file.read(), 
                    mime_type='image/jpeg'
                )
            )
            
        # Add the audio of the user's voice
        if audio_file:
            contents.append(
                types.Part.from_bytes(
                    data=audio_file.read(), 
                    mime_type='audio/wav'
                )
            )
            
        # Add a system prompt so Gemini knows how to behave
        contents.append("You are an AI assistant living inside my smart glasses. Please answer my audio request briefly so it can fit on a small screen.")

        # 3. Send everything directly to Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
        )

        # 4. Format the response exactly how Noa's Dart code expects it
        return jsonify({
            "user_prompt": "Audio request received", # Displayed as your input
            "message": response.text,                # Displayed as Noa's output
            "debug": {"topic_changed": False}
        }), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
