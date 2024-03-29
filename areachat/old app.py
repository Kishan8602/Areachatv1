from flask import Flask, render_template, request, jsonify, session
import openai
import requests
import os

app = Flask(__name__)
app.secret_key = 'kishaisghae'  # Replace with a real secret key in production

# Ensure these API keys are set in your environment variables or securely stored
openai.api_key = 
wit_ai_api_key = 'CXCPPWRYPQZBOJGTWWNHD7W72JLRUUXL'

def get_wit_ai_response(message):
    headers = {'Authorization': f'Bearer {wit_ai_api_key}'}
    wit_ai_url = f'https://api.wit.ai/message?v=20240312&q={message}'
    response = requests.get(wit_ai_url, headers=headers)
    if response.status_code == 200:
        print("Wit.ai Response:", response.json())  # Log the response to console
        return response.json()
    else:
        print("Wit.ai Error:", response.status_code)  # Log any errors
        return None

@app.route("/")
def chat():
    session['conversation'] = []  # Initialize conversation history
    return render_template("chat.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data["message"]
    session['conversation'].append({'role': 'user', 'content': user_message})

    wit_ai_response = get_wit_ai_response(user_message)
    intent = wit_ai_response['intents'][0]['name'] if wit_ai_response.get('intents') else 'unknown_intent'
    confidence = wit_ai_response['intents'][0]['confidence'] if wit_ai_response.get('intents') else 0

    if intent == 'end_conversation' and confidence > 0.5:
        requirements = process_conversation_to_requirements(session['conversation'])
        session['conversation'] = []
        return jsonify({"response": "Conversation ended. Requirements gathered.", "requirements": requirements})
    elif intent != 'greeting' and confidence > 0.5:
        store_requirement(user_message, intent)
        response_message = "Requirement understood. You can continue or end the conversation."
    elif intent == 'greeting':
        response_message = "Hello! How can I assist you with your requirements?"
    else:
        response_message = generate_clarification_request(user_message, intent, session['conversation'])

    session['conversation'].append({'role': 'system', 'content': response_message})
    return jsonify({"response": response_message})

def store_requirement(message, intent):
    print(f"Storing requirement: {message} with intent {intent}")
    # Implement actual storage logic here

def process_conversation_to_requirements(conversation):
    print("Processing conversation to extract requirements")
    # Implement logic to process and summarize the conversation into requirements
    return {"summary": "Requirements extracted from the conversation."}

def generate_clarification_request(user_message, intent, conversation):
    return f"Can you provide more details or clarify what you mean by '{user_message}'?"

if __name__ == "__main__":
    app.run(debug=True)
