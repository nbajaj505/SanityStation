# main.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import json, random
from datetime import datetime
from save import write_json

app = Flask(__name__)
app.secret_key = "supersecretkey"

today_str = datetime.today().strftime("%Y-%m-%d")

# ---------------- MINDFULNESS CHALLENGE DATA ----------------
data = [
        "Write down 3 things you have really appreciated from the day today.",
        "Walk for 10 minutes today, without looking at your phone, focused on your surroundings.",
        "Without any judgement or criticism, count how many times your mind gets distracted today.",
        "Every time your phone vibrates or pings today, pause and follow one breath before looking at it.",
        "Brush your teeth with your non-dominant hand today to help encourage attention.",
        "De-clutter part of your house or office today, helping the mind to feel calmer and clearer.",
        "Drink a mindful cup of tea or coffee today, free from other distractions, focused on taste and smell.",
        "Move email and social media apps to the second page of your phone today.",
        "Notice the sensation as you change posture today from standing to sitting or sitting to standing.",
        "Without forcing it, ask someone how they are today and listen to the reply free from opinion.",
        "Commit to no screen time for 2 hours before bed today, other than playing the sleep exercise.",
        "Pause for 60 seconds to follow the breath each time you enter and exit the car/bus/train today.",
        "Sit down and listen to a favorite song or piece of music today, whilst doing nothing else at all.",
        "Take 5 x 2 minute breaks today and simply follow the breath, as you do in your meditation.",
        "Rather than text someone today, call them instead and have a proper conversation.",
        "Check the kids sleeping before going to bed today and follow three of their deep breaths.",
        "Reset your posture each time you sit down today, gently straightening the back.",
        "Give heartfelt thanks to someone today who has recently helped you in some way.",
        "Turn off all notifications on your phone today.",
        "Eat one meal alone today, without any distractions at all, focusing just on the tastes and smells.",
        "Take one full breath (both in and out) before pressing send any email or social post today.",
        "Commute without music today, just for one day and see how much more you notice.",
        "Buy someone a coffee/tea/cake today for no reason, and without expectation of thanks.",
        "Get some exercise today, without your phone, and focus on the physical sensations.",
        "Take 3 x 30 minute breaks from the phone today, set a timer if you need to.",
        "Take one square of chocolate today and allow it to melt in the mouth, enjoying without chewing.",
        "Write a handwritten card/letter to a good friend you've not seen for a long time.",
        "Do something playful, whatever makes you smile or laugh, at least one time today.",
        "When you get to work, or arrive home, today, pause and follow 10 breaths before entering.",
        "Carry some loose change today and share it with people on the street who need it more."
    ]

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- AUTH FUNCTIONS ----------------
@app.route("/get-auth")
def return_auth():
    return jsonify({"logged_in": session.get("logged_in", False)})

def check_auth():
    if not session.get("logged_in"):
        return redirect(url_for("authentication_page"))
    return None

@app.route("/login", methods=["GET", "POST"])
def authentication_page():
    invalid_cred = False

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        action = request.form.get("action")

        # Signup
        if action == "signup":
            new_user_data = {"email": email, "password": password}
            try:
                with open("data.json", "r") as file:
                    data = json.load(file)
            except:
                data = []
            data.append(new_user_data)
            write_json("data.json", data)

            # Store in session only
            session["logged_in"] = True
            session["email"] = email
            return redirect(url_for("dashboard", tab="main"))

        # Login
        elif action == "login":
            try:
                with open("data.json", "r") as file:
                    data = json.load(file)
            except:
                data = []

            for entry in data:
                if entry["email"] == email and entry["password"] == password:
                    # Store in session only
                    session["logged_in"] = True
                    session["email"] = email
                    return redirect(url_for("dashboard", tab="main"))

            invalid_cred = True

    return render_template("auth.html", error="Invalid credentials" if invalid_cred else None)


# ---------------- DASHBOARD ----------------
@app.route("/dashboard/")
@app.route("/dashboard/<tab>", methods=["GET", "POST"])
def dashboard(tab=None):
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect

    valid_tabs = {
        None: "main",
        "main": "main",
        "journal": "journal",
        "resources": "resources",
        "ai": "ai",
        "guided_breathing": "guided_breathing",
        "mindfulness_challenge": "mindfulness_challenge",
        "crisis_support": "crisis_support"
    }

    if tab not in valid_tabs:
        return redirect(url_for("dashboard", tab="main"))

    context = {"tab": valid_tabs[tab]}

    context["username"] = session.get("email", "friend").split("@")[0]

    try:
        with open("entries.json", "r") as f:
            all_entries = json.load(f)
        user_entries = [e for e in all_entries if e["email"] == session["email"]]
    except (FileNotFoundError, json.JSONDecodeError):
        user_entries = []

    context["number_of_entries"] = len(user_entries)
     

    # Journal entries
    if tab == "journal":
        search_date = request.args.get("date")
        try:
            with open("entries.json", "r") as f:
                entries = json.load(f)
            if search_date:
                context["searched_entries"] = [
                    e for e in entries
                    if e["email"] == session["email"] and e["date"] == search_date
                ]
            else:
                context["searched_entries"] = [
                    e for e in entries if e["email"] == session["email"]
                ]
        except (FileNotFoundError, json.JSONDecodeError):
            context["searched_entries"] = []

    # Mindfulness challenge session data
    if tab == "mindfulness_challenge":
        context["accepted_challenge"] = session.get("accepted_challenge", False)
        context["challenge"] = session.get("challenge")
        context["success_msg"] = session.get("success_msg")

    return render_template("dashboard.html", **context)

# ---------------- AI POST ----------------
@app.route('/dashboard/ai', methods=["POST", "GET"])
def ai():
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect


    from google import genai
    import os
    api_key = "KEY_HERE"
    
    if not api_key:
        return jsonify({"reply": "API key not found. Please set GEMINI_API_KEY."})

    client = genai.Client(api_key=api_key)
  
    global username
    username = session.get("email", "friend").split("@")[0]

    if request.method == "POST":
        user_message = request.json.get("message")
        print(f"[DEBUG] User message: {user_message}")

        gemini_prompt = f"""
        You are a compassionate and professional therapist.
        Provide emotional support, guidance, and encouragement to {username}.
        User says: "{user_message}"

        Instructions:
        1. Be empathetic, patient, and understanding.
        2. Keep responses appropriate, respectful, and safe.
        3. Focus on listening and offering gentle guidance.
        """

        try:
            # 1️⃣ Create chat
            chat = client.chats.create(model="gemini-2.0-flash")

            # 2️⃣ Send the prompt
            response = chat.send_message(gemini_prompt)

            reply_text = response.text if response else "Sorry, I couldn't get a response."
            print(f"[DEBUG] AI reply: {reply_text}")

            return jsonify({"reply": reply_text})

        except Exception as e:
            print(f"[ERROR] Gemini API failed: {e}")
            return jsonify({"reply": "Sorry, the AI is currently unavailable."})

    # GET request just renders the page
    return render_template("dashboard.html", tab="ai")


# ---------------- JOURNAL POST ----------------
@app.route("/dashboard/journal", methods=["POST"])
def journal_post():
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect

    entry = request.form.get("entry")
    entry_dict = {
        "email": session["email"],
        "entry": entry,
        "date": today_str
    }

    try:
        with open("entries.json", "r") as f:
            entries = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    entries.append(entry_dict)
    write_json("entries.json", entries)

    flash("Entry saved!", "success")
    return redirect(url_for("dashboard", tab="journal"))

# ---------------- MINDFULNESS CHALLENGE POST ----------------
@app.route("/mindfulness_challenge", methods=["POST"])
def mindfulness_challenge_post():
    auth_redirect = check_auth()
    if auth_redirect:
        return auth_redirect

    if "accepted_challenge" not in session:
        session["accepted_challenge"] = False
        session["challenge"] = None
        session["success_msg"] = None

    form_type = request.form.get("form_type")
    if form_type == "get_challenge":
        session["challenge"] = random.choice(data)
        session["accepted_challenge"] = True
        session["success_msg"] = None
    elif form_type == "finish_challenge":
        username = session.get("email", "friend").split("@")[0]
        session["success_msg"] = f"Great job, {username}!"

    return redirect(url_for("dashboard", tab="mindfulness_challenge"))

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
