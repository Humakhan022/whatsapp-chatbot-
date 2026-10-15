import os
import json
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
from bot_engine import WhatsAppBotEngine

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Initialize bot with default dataset
bot = WhatsAppBotEngine(os.path.join(config.DATA_DIR, "novatech_store.json"))

def send_meta_whatsapp_message(recipient_phone, message_text, quick_replies=None):
    """Sends message back to user via Meta WhatsApp Cloud API"""
    if not config.WHATSAPP_CLOUD_TOKEN or not config.PHONE_NUMBER_ID:
        print(f"[Meta WhatsApp] Credentials not configured. Simulated response for {recipient_phone}: {message_text}")
        return False

    url = f"https://graph.facebook.com/v19.0/{config.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WHATSAPP_CLOUD_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format quick reply buttons if available
    if quick_replies and len(quick_replies) > 0 and len(quick_replies) <= 3:
        buttons = []
        for idx, qr in enumerate(quick_replies[:3]):
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{idx}",
                    "title": qr[:20]
                }
            })
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message_text},
                "action": {"buttons": buttons}
            }
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {"preview_url": True, "body": message_text}
        }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return res.status_code in [200, 201]
    except Exception as e:
        print(f"Error sending WhatsApp Cloud API message: {e}")
        return False


# ---------------- WEB INTERFACE & SIMULATOR ROUTES ----------------

@app.route("/")
def index():
    """Serves the WhatsApp Web Simulator & Bot Management Studio"""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Live interactive chat simulator API"""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "web_sim_user")

    response_data = bot.process_message(message, session_id=session_id)
    return jsonify({
        "status": "success",
        **response_data
    })


@app.route("/api/datasets", methods=["GET"])
def api_get_datasets():
    """Returns available presets and the active dataset"""
    presets = []
    if os.path.exists(config.DATA_DIR):
        for f in os.listdir(config.DATA_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext in [".json", ".csv"]:
                file_id = os.path.splitext(f)[0]
                name = file_id.replace("_", " ").title()
                presets.append({
                    "id": file_id,
                    "filename": f,
                    "name": name,
                    "type": ext[1:].upper()
                })

    return jsonify({
        "active_dataset_id": bot.active_dataset_id,
        "bot_name": bot.bot_name,
        "category": bot.category,
        "presets": presets
    })


@app.route("/api/dataset/switch", methods=["POST"])
def api_switch_dataset():
    """Switches active dataset to one of the presets or uploaded files"""
    data = request.get_json() or {}
    dataset_id = data.get("dataset_id")
    if not dataset_id:
        return jsonify({"status": "error", "message": "Missing dataset_id"}), 400

    # Look for matching file in data/
    for ext in [".json", ".csv"]:
        filepath = os.path.join(config.DATA_DIR, f"{dataset_id}{ext}")
        if os.path.exists(filepath):
            bot.load_dataset(filepath)
            return jsonify({
                "status": "success",
                "message": f"Successfully loaded dataset: {dataset_id}",
                "summary": bot.get_dataset_summary()
            })

    return jsonify({"status": "error", "message": f"Dataset {dataset_id} not found"}), 404


@app.route("/api/dataset/current", methods=["GET"])
def api_get_current_dataset():
    """Returns full current dataset metadata and entries"""
    return jsonify({
        "status": "success",
        "dataset": bot.get_dataset_summary()
    })


@app.route("/api/dataset/entry", methods=["POST"])
def api_add_or_update_entry():
    """Adds a new QA pair or updates an existing one"""
    data = request.get_json() or {}
    if not data.get("patterns") or not data.get("response"):
        return jsonify({"status": "error", "message": "Both patterns and response are required"}), 400

    saved_entry = bot.add_or_update_entry(data)
    return jsonify({
        "status": "success",
        "message": "Knowledge base entry saved",
        "entry": saved_entry
    })


@app.route("/api/dataset/entry/<entry_id>", methods=["DELETE"])
def api_delete_entry(entry_id):
    """Deletes an entry from knowledge base"""
    success = bot.delete_entry(entry_id)
    if success:
        return jsonify({"status": "success", "message": "Entry removed"})
    return jsonify({"status": "error", "message": "Entry not found"}), 404


@app.route("/api/dataset/upload", methods=["POST"])
def api_upload_dataset():
    """Uploads a custom JSON or CSV dataset file"""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".json", ".csv"]:
        return jsonify({"status": "error", "message": "Only .json and .csv files are supported"}), 400

    saved_path = os.path.join(config.DATA_DIR, filename)
    file.save(saved_path)

    try:
        bot.load_dataset(saved_path)
        return jsonify({
            "status": "success",
            "message": f"Dataset '{filename}' successfully uploaded and activated!",
            "summary": bot.get_dataset_summary()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse dataset: {str(e)}"}), 500


@app.route("/api/dataset/export", methods=["GET"])
def api_export_dataset():
    """Exports current active dataset as formatted JSON download"""
    summary = bot.get_dataset_summary()
    export_obj = {
        "bot_name": summary["bot_name"],
        "bot_tagline": summary["bot_tagline"],
        "category": summary["category"],
        "welcome_message": summary["welcome_message"],
        "fallback_message": summary["fallback_message"],
        "quick_replies": summary["quick_replies"],
        "knowledge_base": summary["knowledge_base"]
    }
    return Response(
        json.dumps(export_obj, indent=2),
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename={bot.active_dataset_id}_export.json"}
    )


@app.route("/api/analytics", methods=["GET"])
def api_get_analytics():
    """Returns analytics and query metrics"""
    return jsonify({
        "status": "success",
        "analytics": bot.analytics,
        "dataset_name": bot.bot_name,
        "total_intents": len(bot.knowledge_base)
    })


@app.route("/api/status", methods=["GET"])
def api_get_status():
    """Returns webhook and environment configuration status"""
    has_meta = bool(config.WHATSAPP_CLOUD_TOKEN and config.PHONE_NUMBER_ID)
    has_twilio = bool(config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN)

    return jsonify({
        "status": "online",
        "active_bot": bot.bot_name,
        "category": bot.category,
        "meta_cloud_api": {
            "configured": has_meta,
            "webhook_path": "/webhook",
            "verify_token": config.VERIFY_TOKEN
        },
        "twilio_api": {
            "configured": has_twilio,
            "webhook_path": "/twilio/webhook"
        }
    })


# ---------------- OFFICIAL META WHATSAPP CLOUD API WEBHOOK ----------------

@app.route("/webhook", methods=["GET"])
def meta_webhook_verification():
    """
    Webhook verification endpoint required by Meta for Developers.
    Meta sends GET request with hub.mode, hub.verify_token, and hub.challenge.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == config.VERIFY_TOKEN:
        print("[Meta Webhook] Successfully verified webhook with challenge token.")
        return challenge, 200
    else:
        print(f"[Meta Webhook] Verification failed. Received token: {token}, expected: {config.VERIFY_TOKEN}")
        return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def meta_webhook_incoming():
    """
    Receives incoming WhatsApp messages from Meta WhatsApp Cloud API.
    """
    body = request.get_json() or {}
    print(f"[Meta Webhook Incoming]: {json.dumps(body)}")

    # Verify standard WhatsApp payload structure
    if body.get("object") == "whatsapp_business_account":
        try:
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        message = messages[0]
                        sender_phone = message.get("from")
                        msg_type = message.get("type")

                        incoming_text = ""
                        if msg_type == "text":
                            incoming_text = message.get("text", {}).get("body", "")
                        elif msg_type == "interactive":
                            # Button reply
                            interactive = message.get("interactive", {})
                            if interactive.get("type") == "button_reply":
                                incoming_text = interactive.get("button_reply", {}).get("title", "")
                            elif interactive.get("type") == "list_reply":
                                incoming_text = interactive.get("list_reply", {}).get("title", "")

                        if incoming_text and sender_phone:
                            # Process message with chatbot engine
                            result = bot.process_message(incoming_text, session_id=sender_phone)
                            reply_text = result["reply"]
                            quick_replies = result.get("quick_replies", [])

                            # Send reply via Meta Graph API
                            send_meta_whatsapp_message(sender_phone, reply_text, quick_replies)

            return jsonify({"status": "EVENT_RECEIVED"}), 200
        except Exception as e:
            print(f"[Meta Webhook Error]: {e}")
            return jsonify({"status": "ERROR", "message": str(e)}), 500

    return "NOT_FOUND", 404


# ---------------- TWILIO WHATSAPP WEBHOOK ----------------

@app.route("/twilio/webhook", methods=["POST"])
def twilio_webhook():
    """
    Receives incoming WhatsApp messages from Twilio Sandbox / Production.
    Responds with TwiML XML.
    """
    incoming_msg = request.form.get("Body", "").strip()
    from_number = request.form.get("From", "unknown_user")
    
    print(f"[Twilio Webhook] Received from {from_number}: {incoming_msg}")

    # Process through bot engine
    bot_result = bot.process_message(incoming_msg, session_id=from_number)
    reply_text = bot_result["reply"]

    # If quick replies exist, append them neatly for WhatsApp text formatting
    if bot_result.get("quick_replies"):
        reply_text += "\n\n💡 *Suggested replies*:\n" + "\n".join([f"• {qr}" for qr in bot_result["quick_replies"][:3]])

    # Escape XML characters
    escaped_reply = (
        reply_text.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
    )

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escaped_reply}</Message>
</Response>"""

    return Response(twiml_response, mimetype="application/xml")


if __name__ == "__main__":
    print(f"🚀 WhatsApp Chatbot Server starting on http://localhost:{config.PORT}")
    print(f"💬 Active Dataset: {bot.bot_name} ({bot.category})")
    print(f"🌐 Meta Webhook URL: http://localhost:{config.PORT}/webhook")
    print(f"📲 Twilio Webhook URL: http://localhost:{config.PORT}/twilio/webhook")
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
