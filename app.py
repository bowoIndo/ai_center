from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import konfigurasi
from groq import Groq
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bowo:mn@localhost:5432/aisuper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class InputOutput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pertanyaan = db.Column(db.Text, nullable=False)
    jawaban = db.Column(db.Text, nullable=False)
    created_timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        return f"Form submitted! Name: {name}, Email: {email}"
    return render_template('form.html')

@app.route('/search', methods=['POST'])
def search():
    searchbox = request.form.get('searchbox')

    if not searchbox:
        return "Kolom pencarian kosong!", 400

    try:
        client = Groq(api_key=konfigurasi.GROQ_API_KEY)

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": searchbox}],
            model="llama3-8b-8192",
        )

        jawaban_server = chat_completion.choices[0].message.content

        # Simpan hasil pencarian ke database
        data = InputOutput(pertanyaan=searchbox, jawaban=jawaban_server)
        db.session.add(data)
        db.session.commit()

        return jsonify({"pertanyaan": searchbox, "jawaban": jawaban_server})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)



# import requests
# from flask import Flask, render_template, request,jsonify
# import os
# from groq import Groq
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime
# import konfigurasi


# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bowo:mn@localhost:5432/aisuper'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)

# class InputOutput(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     pertanyaan = db.Column(db.Text, nullable=False)
#     jawaban = db.Column(db.Text, nullable=False)
#     created_timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         name = request.form.get('name')
#         email = request.form.get('email')
#         return f"Form submitted! Name: {name}, Email: {email}"
#     return render_template('form.html')


# @app.route('/search', methods=['POST'])
# def search():
#     searchbox = request.form.get('searchbox')

#     client = Groq(api_key=konfigurasi.GROQ_API_KEY)

#     chat_completion = client.chat.completions.create(
#         messages=[
#             {
#                 "role": "user",
#                 "content": "Explain the importance of low latency LLMs",
#             }
#         ],
#         model="llama3-8b-8192",
#     )

#     jawaban_server = chat_completion.choices[0].message.content

#     data = InputOutput(pertanyaan=searchbox, jawaban=jawaban_server)
#     db.session.add(data)
#     db.session.commit()

#     return jawaban_server


# if __name__ == '__main__':
#     app.run(debug=True)
