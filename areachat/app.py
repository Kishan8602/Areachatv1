from flask import Flask, render_template, request, jsonify
import openai
import os
import requests

app = Flask(__name__)

# Environment variables for API keys
openai.api_key = ('')
wit_ai_api_key = ('')

@app.route("/")
def chat():
    return render_template("chat.html")
#
def get_wit_ai_response(message):
    """Send user message to Wit.ai and get intent and entities."""
    headers = {'Authorization': f'Bearer '}
    wit_ai_url = f'https://api.wit.ai/message?v=20240312&q={message}'
    response = requests.get(wit_ai_url, headers=headers)
    if response.status_code == 200:
        print("Wit.ai Response:", response.json())  # Log the response to console
        return response.json()
    else:
        print("Wit.ai Error:", response.status_code)  # Log any errors
        return None
#
@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data["message"]
    try:
        # First, get the analysis from Wit.ai
        wit_ai_response = get_wit_ai_response(user_message)
        # Process Wit.ai response (this part depends on your Wit.ai app setup)
        # For simplicity, let's just pass the original message to ChatGPT.
        intent = wit_ai_response['intents'][0]['name'] if wit_ai_response.get('intents') else 'No intent detected'
        # You can modify this to include intent and entities in the prompt.

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        chat_response = response.choices[0].message['content']
        
        # Append Wit.ai intent to the response for debugging
        debug_response = f"{chat_response}\n\n[Debug: Intent detected by Wit.ai - {intent}]"
        #
        return jsonify({"response": response.choices[0].message['content']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
