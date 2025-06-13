from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
import difflib

app = Flask(__name__)

def extract_text_from_pdf(file_stream, page=None):
    reader = PdfReader(file_stream)
    pages = reader.pages
    if page is not None and 1 <= page <= len(pages):
        return pages[page-1].extract_text() or ""
    # دمج كل الصفحات إذا لم يحدد المستخدم صفحة
    return "\n".join(p.extract_text() or "" for p in pages)

def generate_questions(text, num_questions=None):
    # نقسم النص إلى جمل
    sentences = [s.strip() for s in text.replace('\n',' ').split('.') if s.strip()]
    total = len(sentences)
    # إذا لم يحدد المستخدم عدد الأسئلة، نولد سؤالاً عن كل جملة
    if num_questions is None or num_questions > total:
        num_questions = total
    questions = []
    for i in range(num_questions):
        sent = sentences[i]
        # نختار أطول كلمة كمفتاح
        words = [w for w in sent.split() if len(w) > 3]
        key = max(words, key=len) if words else None
        if key:
            q = sent.replace(key, "____") + "؟"
            questions.append({"question": q, "expected": key})
    return questions

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json() or {}
    page = data.get("page")  # رقم الصفحة المطلوبة (اختياري)
    num_q = data.get("num_questions")  # عدد الأسئلة المطلوبة (اختياري)
    # إما ملف PDF أو نص:
    if 'file' in request.files:
        raw = extract_text_from_pdf(request.files['file'].stream, page)
    else:
        raw = data.get("text", "")
    qs = generate_questions(raw, num_q)
    if not qs:
        return jsonify({"error": "لا يوجد نص كافٍ لتوليد أسئلة"}), 400
    return jsonify({
        "questions": qs,
        "page": page,
        "total_available": len([s for s in raw.split('.') if s.strip()])
    })

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json() or {}
    user = data.get("answer", "").strip()
    correct = data.get("correct", "").strip()
    sim = difflib.SequenceMatcher(None, user, correct).ratio()
    return jsonify({
        "correct": sim >= 0.8,
        "similarity": sim,
        "expected": correct
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
