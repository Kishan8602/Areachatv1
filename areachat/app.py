from flask import Flask, render_template, request, jsonify, session # to take input from frontend to our side
import openai # for openai api and assistants
import requests
import mysql.connector # for mysql db access
import logging # for logging steps for our(developer) understanding
from api import OPENAI_API_KEY, WIT_AI_API_KEY, assistant_map, DATABASE_CONFIG, FLASK_SECRET_KEY
# api keys of the above are stored in a file called api.py , this file cannot be shared for privacy

## setting up logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

#initialising flask
app = Flask(__name__)

# setting api keys for necessary pipes
app.secret_key = FLASK_SECRET_KEY
openai.api_key = OPENAI_API_KEY
wit_ai_api_key = WIT_AI_API_KEY

# establishing databse connection
def get_db():
    return mysql.connector.connect(**DATABASE_CONFIG)

# routing to fetch all conversation_logs
@app.route("/conversations", methods=["GET"])
def get_conversations():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT conversation_id, initial_start_time FROM conversation_logs ORDER BY initial_start_time DESC")
    conversations = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(conversations)

# saving feedback from user this part is incomplete will complete this by review 3
@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json()
    conversation_id = data['conversation_id']
    helpful = data['helpful']
    comments = data['comments']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO feedback (conversation_id, helpful, comments) VALUES (%s, %s, %s)", (conversation_id, helpful, comments))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "success"})


# main chat route for a new convo (BASIC)
@app.route("/")
def chat():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO conversation_logs (initial_start_time) VALUES (CURRENT_TIMESTAMP)")
    db.commit()
    conversation_id = cursor.lastrowid
    session['conversation_id'] = conversation_id
    logger.info(f"New conversation started with ID: {conversation_id}")
    return render_template("chat.html")

# ROUTE TO PROCESS AND RESPONDING TO USER MESSAGES
# creating a conversation history to add a unique feature of ours later
#select * from messages; to understand how we are fetching and storing history 

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data["message"]
    logger.info(f"Received message from user: {user_message}")
    
    conversation_id = session.get('conversation_id')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute('INSERT INTO messages (conversation_id, user, message, timestamp) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)', (conversation_id, 'user', user_message))
    db.commit()
    
    cursor.execute('SELECT user, message FROM messages WHERE conversation_id = %s ORDER BY timestamp ASC', (conversation_id,))
    conversation_history = cursor.fetchall()

    response_message = process_ai_response(user_message, conversation_history)
    
    cursor.execute('INSERT INTO messages (conversation_id, user, message, timestamp) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)', (conversation_id, 'ai', response_message))
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"response": response_message})


# FUNCTION TO GET A RESPONSE REPORT FROM WIT.AI OF USER'S MSG
def get_wit_ai_response(message):
    logger.info("Sending message to Wit.ai")
    headers = {'Authorization': f'Bearer {wit_ai_api_key}'}
    wit_ai_url = f'https://api.wit.ai/message?v=20240312&q={message}'
    response = requests.get(wit_ai_url, headers=headers)
    if response.status_code == 200:
        wit_ai_data = response.json()
        logger.info(f"Wit.ai response for '{message}': {wit_ai_data}")
        return wit_ai_data
    else:
        logger.error(f"Wit.ai Error: {response.status_code}")
        return None


# FUNCTION TO PROCESS THE AI response based on user's message and conversation history
# conversation_history gathered in above function brought us a way to fix the persistance threading issue
# relevancy between the conversation context ( conversation_history) and current user message will be contextually analysed
# new response is created based on our logic its unstable for now but after finetuning instructions given to assistants and
# sorting the struct from areachat databse and accessing proper data will give us a more stable approach
# this is our unique idea which mkes our model standout by processing the i reponse with our touch
# current user messages intent is taken and processed gets a reply as user message and 
# conversatio_history is converted to context and the user method and context ane now taken togather 
# now the last assistant that acted on user_message will now combine context and user_message nd craft a new response
#this response can fill gaps in a conversation/ follow persistance threading/ be relavant
# this is our idea
def process_ai_response(user_message, conversation_history):
    wit_ai_response = get_wit_ai_response(user_message)
    if wit_ai_response and 'intents' in wit_ai_response and wit_ai_response['intents']:
        intent = wit_ai_response['intents'][0]['name']
        assistant_info = assistant_map.get(intent.capitalize(), assistant_map.get('RequirementGathering'))
    else:
        assistant_info = assistant_map.get('RequirementGathering')

    if "summary" in user_message.lower():
        assistant_info = assistant_map.get('Summary-Assistant')

    logger.info(f"Using {assistant_info['name']} for processing the response.")
    return get_chat_completion(user_message, assistant_info, conversation_history)

# function to complete the chat response using open ai chat completion module api and sending out the final response
# based on the explanation above you probably understood and that this is unstable for now but 
# more precise context sharp in future will be less overwhelming and be more stable then.


def get_chat_completion(user_message, assistant_info, conversation_history):
    assistant_id = assistant_info['id']
    assistant_name = assistant_info['name']
    context = " ".join([f"{msg['user']}: {msg['message']}" for msg in conversation_history])

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": f"You are the {assistant_name}.\n{context}"}, {"role": "user", "content": user_message}],
            user=assistant_id
        )
        return response.choices[0].message['content']
    except openai.error.OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return "I'm having trouble processing that. Could you rephrase or provide more details?"

if __name__ == "__main__":
    app.run(debug=True)



# things that needs work for review 
# we will end conversations after approval of desired output
# after that we can start crafting feedback and resume the function along with its db
# feedback will be set and then final summary of functional and non functional requirements will be formed
# feedback, report of requirements, ending conversations, testing
# ui development whenever we can
# this is version 1 so its design wise not likable but efficiency wise it will be a breakthrough
#better versions can be possible with heavy improvement in ui which makes clients and everyone more likable to use our tool.
# AreaCHAT V1 t&c applicable.