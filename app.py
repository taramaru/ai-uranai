# AI占い Webアプリ（Flask + OpenAI API）
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request
import openai
import os
import stripe

# Stripe初期化
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

@app.route("/buy", methods=["POST"])
def buy():
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": os.environ.get("STRIPE_PRICE_ID"),
            "quantity": 1,
        }],
        mode="payment",
        success_url=request.host_url + "premium_result",
        cancel_url=request.host_url + "result",
    )
    return redirect(checkout_session.url, code=303)

app = Flask(__name__)

# OpenAI APIキー（環境変数から取得する設計）
openai.api_key = os.environ.get("OPENAI_API_KEY")

# 占いプロンプトのベース（数秘術）
def generate_prompt(name, birthdate, question):
    return f"""
あなたはプロの占い師です。以下の情報に基づいて、相手に対して数秘術による性格診断と今月の運勢を、優しく丁寧に伝えてください。

【情報】
名前：{name}
誕生日：{birthdate}
相談内容：{question}

▼占いの構成：
① 性格の傾向
② 今月の運気
③ 相談へのアドバイス（数秘術の観点から）
"""

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    birthdate = request.form["birthdate"]
    question = request.form["question"]

    prompt = generate_prompt(name, birthdate, question)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはプロの占い師です。"},
            {"role": "user", "content": prompt},
        ]
    )

    result_text = response.choices[0].message["content"]
    return render_template("result.html", result=result_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)