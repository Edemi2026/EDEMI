# =============================================================================
# web_config.py — EDEMI Smart Glasses
# Flask web server for settings configuration
# Accessible via Pi hotspot at 192.168.4.1:5000
# No internet needed — Pi serves the page directly
# =============================================================================

from flask import Flask, render_template, request, jsonify
from settings_manager import get_all_settings, update_settings
import threading
import time
import logging
logging.getLogger("werkzeug").setLevel(logging.ERROR)
app = Flask(__name__)

# =============================================================================
# ROUTES
# =============================================================================

@app.route("/")
def index():
    """Serve settings page."""
    settings = get_all_settings()
    return render_template("index.html", settings=settings)


@app.route("/save", methods=["POST"])
def save():
    """Save settings from form submission."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error",
                           "message": "No data received"}), 400

        # Validate and clean data
        clean = {}

        if "user_name" in data:
            clean["user_name"] = str(data["user_name"]).strip()[:30]

        if "user_religion" in data:
            if data["user_religion"] in ["Christian", "Muslim", "None"]:
                clean["user_religion"] = data["user_religion"]

        if "user_reply_style" in data:
            if data["user_reply_style"] in ["polite", "casual", "formal"]:
                clean["user_reply_style"] = data["user_reply_style"]

        if "user_language" in data:
            if data["user_language"] in ["English"]:
                clean["user_language"] = data["user_language"]

        if "user_city" in data:
            clean["user_city"] = str(data["user_city"]).strip()[:50]

        if "user_age_group" in data:
            if data["user_age_group"] in ["Teen", "Adult", "Senior"]:
                clean["user_age_group"] = data["user_age_group"]

        if "user_gender" in data:
            if data["user_gender"] in ["Male", "Female", "Other"]:
                clean["user_gender"] = data["user_gender"]

        if "auto_reply" in data:
            clean["auto_reply"] = bool(data["auto_reply"])

        if "environment_alerts" in data:
            clean["environment_alerts"] = bool(data["environment_alerts"])

        if "mic_sensitivity" in data:
            if data["mic_sensitivity"] in ["Low", "Medium", "High"]:
                clean["mic_sensitivity"] = data["mic_sensitivity"]

        if "tft_clear_delay" in data:
            delay = int(data["tft_clear_delay"])
            if delay in [5, 10, 15]:
                clean["tft_clear_delay"] = delay

        if "alert_duration" in data:
            dur = int(data["alert_duration"])
            if dur in [3, 5, 8]:
                clean["alert_duration"] = dur

        if "ar_text_size" in data:
            if data["ar_text_size"] in ["Small", "Medium", "Large"]:
                clean["ar_text_size"] = data["ar_text_size"]

        if "show_date" in data:
            clean["show_date"] = bool(data["show_date"])

        if "show_battery" in data:
            clean["show_battery"] = bool(data["show_battery"])

        if "show_wifi" in data:
            clean["show_wifi"] = bool(data["show_wifi"])

        for i in [1, 2, 3]:
            key = f"emergency_message_{i}"
            if key in data:
                clean[key] = str(data[key]).strip()[:50].upper()

        update_settings(clean)

        return jsonify({
            "status":  "success",
            "message": "Settings saved successfully!"
        })

    except Exception as e:
        return jsonify({
            "status":  "error",
            "message": str(e)
        }), 500


@app.route("/status")
def status():
    """Return current system status as JSON."""
    from system_monitor import get_wifi_status, get_uptime, get_power_status
    return jsonify({
        "wifi":     get_wifi_status(),
        "uptime":   get_uptime(),
        "power":    get_power_status(),
        "settings": get_all_settings()
    })


# =============================================================================
# START WEB SERVER
# =============================================================================

@app.route("/screenshot", methods=["POST"])
def screenshot():
    """Take a screenshot of the AR display."""
    import datetime
    import os
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"/home/smart-pi/edemi/screenshots/edemi_{ts}.png"
    os.makedirs("/home/smart-pi/edemi/screenshots", exist_ok=True)
    try:
        with open("/dev/fb0", "rb") as fb:
            raw = fb.read()
        from PIL import Image
        img = Image.frombytes("RGB", (1280, 1024), raw, "raw", "RGB;16")
        img = img.crop((0, 0, 640, 480))
        img.save(path)
        return jsonify({"status": "success", "file": path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/shutdown", methods=["POST"])
def shutdown():
    """Shutdown the Pi safely."""
    import subprocess
    import threading
    def do_shutdown():
        import time
        time.sleep(2)
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    threading.Thread(target=do_shutdown, daemon=True).start()
    return jsonify({"status": "success", "message": "Shutting down"})

def start_web_server(host="0.0.0.0", port=5000):
    """
    Start Flask web server in background.
    Accessible at http://192.168.4.1:5000 via EDEMI hotspot.
    """
    open("/tmp/edemi.log", "a").write(f"Web config started\n")
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )
