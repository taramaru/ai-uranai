# AI占い Webアプリ（Flask + OpenAI API + Stripe Checkout）

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, session
import openai
import stripe
import os

# Flaskアプリを初期化
app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"] # 任意のキー
# APIキーの設定
openai.api_key = os.environ.get("OPENAI_API_KEY")
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

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

# フォーム表示
@app.route("/")
def index():
    return render_template("form.html")

# 無料鑑定結果の表示
@app.route("/result", methods=["POST"])
def result():
    name = request.form["name"]
    birthdate = request.form["birthdate"]
    question = request.form["question"]

    # セッションに保存しておく
    session["name"] = name
    session["birthdate"] = birthdate
    session["question"] = question

    # 通常の簡易プロンプト
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

# Stripe Checkout 経由で購入
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

@app.route("/premium_result")
def premium_result():
    name = session.get("name")
    birthdate = session.get("birthdate")
    question = session.get("question")

    if not all([name, birthdate, question]):
        return redirect("/")

    # 有料版のプロンプト（より詳細に）
    premium_prompt = f"""
あなたはプロの占い師です。以下の情報に基づいて、相手に対して数秘術による総合鑑定を丁寧に伝えてください。

【情報】
名前：{name}
誕生日：{birthdate}
相談内容：{question}

▼詳細鑑定の構成：
① 基本的な性格と深層心理
② 現在の運気と人生サイクル
③ 相談に対する多角的なアドバイス（仕事、金運、人間関係）
④ 幸運を引き寄せるための行動指針とタイミング
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたはプロの占い師です。"},
            {"role": "user", "content": premium_prompt},
        ]
    )

    premium_result = response.choices[0].message["content"]
    return render_template("premium_result.html", result=premium_result)

# アプリ起動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
