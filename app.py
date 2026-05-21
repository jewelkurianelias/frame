import os
import json
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
        
        # 2. Extract the context text fields sent by Noa
        location = request.form.get('location', 'Unknown Location')
        time_str = request.form.get('time', 'Unknown Time')
        messages_str = request.form.get('messages', '[]')
        
        # 3. Parse the conversation history
        # Noa sends history as a JSON string: [{"role": "user", "content": "..."}, ...]
        try:
            noa_history = json.loads(messages_str)
        except json.JSONDecodeError:
            noa_history = []
            
        # Convert Noa's history format into Gemini's expected format
        gemini_history = []
        for msg in noa_history:
            # Map Noa's 'assistant' to Gemini's 'model'
            role = 'model' if msg.get('role') == 'assistant' else 'user'
            text = msg.get('content', '')
            gemini_history.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text)])
            )

        # 4. Prepare the data for the CURRENT turn (the tap you just made)
        current_turn_parts = []
        if image_file:
            current_turn_parts.append(
                types.Part.from_bytes(data=image_file.read(), mime_type='image/jpeg')
            )
        if audio_file:
            current_turn_parts.append(
                types.Part.from_bytes(data=audio_file.read(), mime_type='audio/wav')
            )
            
        if not current_turn_parts:
            return jsonify({"error": "No audio or image received"}), 400

        # 5. Give Gemini its context (Time and Location)
        system_instruction = (
            f"You are a helpful AI assistant living inside smart glasses. "
            f"Please keep your answers brief so they fit on a small screen. "
            f"Context - Current location: {location}. Current time: {time_str}."
        )
        
        # Create a chat session to maintain conversation history
        chat = client.chats.create(
            model='gemini-3.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
            history=gemini_history
        )

        # 6. Send the current audio/image to the chat
        response = chat.send_message(current_turn_parts)

        # 7. Format the response EXACTLY as the PR requires
        return jsonify({
            "user_prompt": "Audio request", # Placeholder since we process audio directly
            "message": response.text,
            "debug": {
                "topic_changed": False
            }
        }), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
