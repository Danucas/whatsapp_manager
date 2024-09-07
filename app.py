from flask import Flask, request, send_file, render_template, redirect
from wrapper import WebWhatsapp
from chatbot import ChatBot, get_appointments

app = Flask(__name__)
wa_engine = WebWhatsapp("1234", {})
app.config["WA_ENGINE"] = wa_engine

chatbot = ChatBot(wa_engine, loop_timeout=1)


@app.route("/auth")
def index():
    url = wa_engine.auth()
    return {
        "qrcode": f"/qrcode/{wa_engine.instance.instance_id}",
        "verification_url": url
    }

@app.route("/session")
def get_session():
    result = wa_engine.open_whatsapp_web()
    return result

@app.route("/qrcode/<id>")
def qr_code(id):

    return send_file(f"images/{id}.png")

@app.route("/scancode/<id>")
def scan_frame(id):
    return render_template("scan.html")

@app.route("/")
def dashboard():
    if not chatbot.active:
        if not chatbot.start_service("agendar-citas"):
            wa_engine.auth()
            return redirect("/scancode/1234", 302)
    history = chatbot.history
    appointments = get_appointments()
    return render_template("dashboard.html", status=chatbot.active, stories=history, appointments=appointments)


@app.route("/web_whatsapp_verify/<id>")
def verify_whatsapp_qr_code(id):
    result = wa_engine.wait_registration()
    return result

@app.route("/message", methods=["POST"])
def send_message():
    target_number = request.json.get("to")
    message = request.json.get("message")
    contact_result = wa_engine.search_contact(target_number)
    message_result = wa_engine.send_whatsapp_message(message)
    return message_result


@app.route("/unread", methods=["GET"])
def get_unread_messages():
    return chatbot.check_old_messages()



if __name__ == '__main__':
    # chatbot.start_service("agendar-citas")
    app.run('0.0.0.0', 5002)