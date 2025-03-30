from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import konfigurasi
from groq import Groq
from flask_migrate import Migrate
import json
from openai import OpenAI
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bowo:mn@localhost:5432/aisuper'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class InputOutput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pertanyaan = db.Column(db.Text, nullable=False)
    jawaban = db.Column(db.Text, nullable=False)
    server_ai = db.Column(db.Text, nullable=False, default='')
    is_pembuat_kesimpulan = db.Column(db.Boolean, default=False)
    created_timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        return f"Form submitted! Name: {name}, Email: {email}"
    return render_template('form.html')


@app.route('/kesimpulan', methods=['POST'])
def kesimpulan():
    searchbox = request.form.get('searchbox')
    hasil = InputOutput.query.filter_by(pertanyaan=searchbox).all()
    tampungan_jawaban = '' # menampung semua jawaban di pisah memakai spasi antar jawaban
    if hasil:
        for row in hasil:
            tampungan_jawaban = ' '.join([row.jawaban for row in hasil])

    pertanyaan_ke_deepseek = 'buat kesimpulan dari : ' + tampungan_jawaban

    # insert pertanyaan = pertanyaan_ke_deepseek , server_ai = 'deepseek' , is_pembuat_kesimpulan = True ke table input_output,setelah sukses insert ambil id input_output yang baru di input
    jawaban = 'jawaban kesimpulan dari deepseek'

    data_baru = InputOutput(
        pertanyaan=pertanyaan_ke_deepseek,
        jawaban = jawaban,  
        server_ai='deepseek',
        is_pembuat_kesimpulan=True
    )

    db.session.add(data_baru)
    db.session.commit()

    # Ambil ID dari input baru
    id_baru = data_baru.id

    # update isi kesimpulan_id = id_baru dari setiap data hasil
    for row in hasil:
        row.kesimpulan_id = id_baru
    
    db.session.commit()  # Simpan perubahan ke database

    # client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

    # response = client.chat.completions.create(
    #     model="deepseek-chat",
    #     messages=[
    #         {"role": "system", "content": "You are a helpful assistant"},
    #         {"role": "user", "content": searchbox},
    #     ],
    #     stream=False
    # )
    # jawaban = response.choices[0].message.content

    return jawaban  


@app.route('/you', methods=['POST'])
def you():

    searchbox = request.form.get('searchbox')

    headers = {"X-API-Key": konfigurasi.YOU_API_KEY}
    params = {"query": searchbox}
    jawaban = requests.get(
        "https://chat-api.you.com/search?query={query}",
        params=params,
        headers=headers,
    ).json()

    data = InputOutput(pertanyaan=searchbox, jawaban=jawaban, server_ai='you')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": jawaban})



@app.route('/grok', methods=['POST'])
def grok():


    searchbox = request.form.get('searchbox')

    client = OpenAI(
        api_key=konfigurasi.GROK_API_KEY,
        base_url="https://api.x.ai/v1",
    )



    completion = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {"role": "system", "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."},
            {"role": "user", "content": "Explain the risks of improper AI usage and its contribution to autocratic regimes."},
        ],
    )

    jawaban=completion.choices[0].message

    data = InputOutput(pertanyaan=searchbox, jawaban=jawaban, server_ai='grok')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": jawaban})






@app.route('/perplexity', methods=['POST'])
def perplexity():

    searchbox = request.form.get('searchbox')
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            ),
        },
        {   
            "role": "user",
            "content": (
                searchbox
            ),
        },
    ]
    client = OpenAI(api_key=konfigurasi.PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )

    data = InputOutput(pertanyaan=searchbox, jawaban=response, server_ai='perplexity')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": response})



@app.route('/gemini', methods=['POST'])
def gemini():
    searchbox = request.form.get('searchbox')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3:generateContent?key={konfigurasi.GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "text": searchbox
            }
        ]
    }


    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        jawaban = response.json()

        # result = response.json()
        # answer = result['choices'][0]['message']['content']
        # jawaban = answer.strip()

    else:
        response_dict = json.loads(response.text)
        jawaban = response_dict['error']['message']



    data = InputOutput(pertanyaan=searchbox, jawaban=jawaban, server_ai='gemini')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": jawaban})


@app.route('/chatgpt', methods=['POST'])
def chatgpt():
    searchbox = request.form.get('searchbox')

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {konfigurasi.CHATGPT_API_KEY}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": searchbox}
        ],
        "max_tokens": 100
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        # Ambil konten teks dari response
        answer = result['choices'][0]['message']['content']
        jawaban = answer.strip()

    else:
        response_dict = json.loads(response.text)
        jawaban = response_dict['error']['message']



    data = InputOutput(pertanyaan=searchbox, jawaban=jawaban, server_ai='chatgpt')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": jawaban})


@app.route('/huggingface', methods=['POST'])
def huggingface():
    searchbox = request.form.get('searchbox')

    url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {
        "Authorization": f"Bearer {konfigurasi.HUGGINGFACE_API_KEY}"
    }
    data = {
        "inputs": searchbox
    }

    response = requests.post(url, headers=headers, json=data)
    data = json.loads(response.text)
    jawaban = data[0]["generated_text"]

    data = InputOutput(pertanyaan=searchbox, jawaban=jawaban, server_ai='hugging_face')
    db.session.add(data)
    db.session.commit()

    return jsonify({"pertanyaan": searchbox, "jawaban": jawaban})



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

        data = InputOutput(pertanyaan=searchbox, jawaban=jawaban_server, server_ai='groq')
        db.session.add(data)
        db.session.commit()

        return jsonify({"pertanyaan": searchbox, "jawaban": jawaban_server})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
