# AI占い Webアプリ（Flask + OpenAI API + Stripe Checkout）

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, session, make_response
import openai
import stripe
import os
from xhtml2pdf import pisa
from io import BytesIO

# Flaskアプリを初期化
app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

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

    session["name"] = name
    session["birthdate"] = birthdate
    session["question"] = question

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
        success_url=request.host_url.rstrip("/") + "/premium_result",
        cancel_url=request.host_url.rstrip("/") + "/result",
    )
    return redirect(checkout_session.url, code=303)

# プレミアム鑑定結果の表示
@app.route("/premium_result")
def premium_result():
    name = session.get("name")
    birthdate = session.get("birthdate")
    question = session.get("question")

    if not all([name, birthdate, question]):
        return redirect("/")

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
    session["premium_result"] = premium_result
    return render_template("premium_result.html", result=premium_result)

# PDFダウンロード
@app.route("/download")
def download_pdf():
    name = session.get("name")
    birthdate = session.get("birthdate")
    question = session.get("question")
    result = session.get("premium_result")

    if not result:
        return redirect("/premium_result")

    result_html = result.replace('\n', '<br>')

    html = f"""
    <h2>プレミアム鑑定結果</h2>
    <p><strong>名前:</strong> {name}</p>
    <p><strong>誕生日:</strong> {birthdate}</p>
    <p><strong>相談内容:</strong> {question}</p>
    <hr>
    <div>{result_html}</div>
    """

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=pdf)
    pdf.seek(0)

    response = make_response(pdf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="uranai_result.pdf"'
    return response

# アプリ起動
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
