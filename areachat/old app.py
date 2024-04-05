from flask import Flask, render_template, request, jsonify, session
import openai
import requests
import os
import json
import time

app = Flask(__name__)
app.secret_key = 'teamareachat'

# Assuming you have an `api.py` file with OPENAI_API_KEY and WIT_AI_API_KEY variables
from api import OPENAI_API_KEY, WIT_AI_API_KEY

openai.api_key = OPENAI_API_KEY
wit_ai_api_key = WIT_AI_API_KEY

assistant_map = {
    'RequirementGathering': {'id': 'asst_KzVgfNZPsLYuG2vyGeBYLTEj', 'name': 'RequirementGathering-Assistant'},
    'HelpRequest': {'id': 'asst_54ni2tc6SOhkOMtrgTk9Rni4', 'name': 'HelpRequest-Assistant'},
    'Greeting': {'id': 'asst_i6A3ZsAgnJWkYzkQrUMsZayJ', 'name': 'Greeting-Assistant'},
    'Farewell': {'id': 'asst_UEl7WyzgRR0BvcoFyXjaxJ7U', 'name': 'Farewell-Assistant'},
    'Confirmation': {'id': 'asst_OmMIH613xaB4J8BsQTum1p9R', 'name': 'Confirmation-Assistant'},
    'ClarificationRequest': {'id': 'asst_2FYgYGwOn67o6gAHTioOTrKE', 'name': 'Clarification-Assistant'}
}

def get_wit_ai_response(message):
    headers = {'Authorization': f'Bearer {wit_ai_api_key}'}
    wit_ai_url = f'https://api.wit.ai/message?v=20240312&q={message}'
    response = requests.get(wit_ai_url, headers=headers)
    if response.status_code == 200:
        wit_ai_data = response.json()
        print("Wit.ai Response:", wit_ai_data)
        return wit_ai_data
    else:
        print("Wit.ai Error:", response.status_code)
        return None

@app.route("/")
def chat():
    session['conversation'] = []
    session['file_name'] = f"conversation_{int(time.time())}"
    return render_template("chat.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data["message"]
    session['conversation'].append({'role': 'user', 'content': user_message})

    wit_ai_response = get_wit_ai_response(user_message)
    if not wit_ai_response or 'intents' not in wit_ai_response or not wit_ai_response['intents']:
        response_message = "I'm having trouble understanding. Could you please clarify?"
    else:
        intent = wit_ai_response['intents'][0]['name']
        assistant_info = assistant_map.get(intent)

        if intent == 'Farewell':
            response_message = process_conversation_to_requirements(session['file_name'])
            session['conversation'] = []
        elif assistant_info:
            store_requirement(user_message, intent, session['file_name'])
            response_message = get_chat_completion(user_message, assistant_info)
        else:
            response_message = "Intent not recognized. Please try again."

    session['conversation'].append({'role': 'system', 'content': response_message})
    return jsonify({"response": response_message})

def get_chat_completion(message, assistant_info):
    assistant_id = assistant_info['id']
    assistant_name = assistant_info['name']
    print(f"Using assistant: {assistant_name} with ID: {assistant_id}")
    
    prompt = f"{message}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are the {assistant_name}."}, {"role": "user", "content": message}],
            user=assistant_id
        )
        return response.choices[0].message['content']
    except openai.error.OpenAIError as e:
        error_message = f"I'm having trouble processing that. Could you rephrase or provide more details? Error: {str(e)}"
        print(error_message)
        return error_message

def store_requirement(message, intent, file_name):
    requirement = {
        'intent': intent,
        'message': message
    }
    print(f"Storing requirement: {requirement}")
    try:
        with open(f'{file_name}.json', 'a') as file:
            json.dump(requirement, file)
            file.write('\n')
    except IOError as e:
        print(f"Error storing requirement: {e}")

def process_conversation_to_requirements(file_name):
    print("Processing conversation to extract requirements")
    try:
        with open(f'{file_name}.json', 'r') as file:
            lines = file.readlines()
            requirements = [json.loads(line) for line in lines]

        summary_table = "Requirements Summary:\n"
        summary_table += "-" * 50 + "\n"
        summary_table += "{:<20} | {:<30}\n".format("Intent", "Message")
        summary_table += "-" * 50 + "\n"
        for req in requirements:
            summary_table += "{:<20} | {:<30}\n".format(req['intent'], req['message'][:28] + '...' if len(req['message']) > 28 else req['message'])

        return summary_table
    except IOError as e:
        print(f"Error processing requirements: {e}")
        return "Error in processing requirements."

def generate_clarification_request(user_message, intent, conversation):
    return f"Can you provide more details or clarify what you mean by '{user_message}'?"

if __name__ == "__main__":
    app.run(debug=True)
