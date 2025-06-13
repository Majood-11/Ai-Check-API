from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
import difflib

app = Flask(__name__)

# 📘 استخراج النص من PDF
def extract_text_from_pdf(file_stream, page=None):
    reader = PdfReader(file_stream)
    pages = reader.pages
    if page is not None and 1 <= page <= len(pages):
        return pages[page - 1].extract_text() or ""
    return "\n".join(p.extract_text() or "" for p in pages)

# 🧠 توليد الأسئلة
def generate_questions(text, num_questions=None):
    sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
    total = len(sentences)
    if num_questions is None or num_questions > total:
        num_questions = total
    questions = []
    for i in range(num_questions):
        sent = sentences[i]
        words = [w for w in sent.split() if len(w) > 3]
        key = max(words, key=len) if words else None
        if key:
            q = sent.replace(key, "____") + "؟"
            questions.append({"question": q, "expected": key})
    return questions

# 🏠 الصفحة الرئيسية (للتأكد أن الـ API يعمل)
@app.route('/')
def home():
    return "✅ AI Check API is running!"

# 📤 توليد أسئلة من النص أو PDF
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json() or {}
    page = data.get("page")
    num_q = data.get("num_questions")
    raw = ""

    if 'file' in request.files:
        raw = extract_text_from_pdf(request.files['file'].stream, page)
    elif data.get("text"):
        raw = data.get("text")
    else:
        return jsonify({"error": "يرجى إرسال نص أو ملف PDF"}), 400

    qs = generate_questions(raw, num_q)
    if not qs:
        return jsonify({"error": "لا يوجد نص كافٍ لتوليد أسئلة"}), 400

    return jsonify({
        "questions": qs,
        "page": page,
        "total_available": len([s for s in raw.split('.') if s.strip()])
    })

# ✅ التحقق من الإجابة
@app.route('/check', methods=['POST'])
def check():
    data = request.get_json() or {}
    user = data.get("answer", "").strip()
    correct = data.get("correct", "").strip()
    sim = difflib.SequenceMatcher(None, user, correct).ratio()

    feedback = "✅ أحسنت! إجابتك صحيحة." if sim >= 0.8 else f"❌ الإجابة الصحيحة: {correct}. لا تيأس وجرّب مرة أخرى!"

    return jsonify({
        "correct": sim >= 0.8,
        "similarity": sim,
        "expected": correct,
        "feedback": feedback
    })

# 🚀 تشغيل التطبيق
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
