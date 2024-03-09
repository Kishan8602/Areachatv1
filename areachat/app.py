from flask import Flask, render_template, request, jsonify
import openai
import os

app = Flask(__name__)

# Make sure to set your OpenAI API key here (ideally through environment variables)
openai.api_key = ('keep api key here')

@app.route("/")
def chat():
    return render_template("chat.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data["message"]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        return jsonify({"response": response.choices[0].message['content']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
