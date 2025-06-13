from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/check', methods=['POST'])
def check_answer():
    data = request.json
    user_answer = data.get("answer", "").strip().lower()
    correct_answer = data.get("correct", "").strip().lower()
    return jsonify({
        "correct": user_answer == correct_answer,
        "user": user_answer,
        "expected": correct_answer
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
