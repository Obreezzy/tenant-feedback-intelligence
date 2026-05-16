from flask import Flask, request, jsonify, Response, render_template
from dotenv import load_dotenv
import requests, os, sqlite3, csv, io
from datetime import datetime

load_dotenv(r"C:\Users\user\Desktop\DB\phase2\.env", encoding="utf-8")

app = Flask(__name__, template_folder=r"C:\Users\user\Desktop\DB\phase2", static_folder=r"C:\Users\user\Desktop\DB\phase2", static_url_path="/static")
KEY = os.getenv("KEY")
ENDPOINT = "https://obreeze-ai-hub.cognitiveservices.azure.com/"
HEADERS = {"Ocp-Apim-Subscription-Key": KEY, "Content-Type": "application/json"}
DB_PATH = r"C:\Users\user\Desktop\DB\phase2\feedback.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        feedback TEXT,
        sentiment TEXT,
        confidence REAL,
        category TEXT,
        priority TEXT,
        keywords TEXT,
        entities TEXT,
        language TEXT
    )''')
    conn.commit()
    conn.close()

def save_analysis(data, feedback):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO analyses
        (timestamp, feedback, sentiment, confidence, category, priority, keywords, entities, language)
        VALUES (?,?,?,?,?,?,?,?,?)''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        feedback,
        data["sentiment"],
        data["confidence"],
        data["category"],
        data["priority"],
        ", ".join(data["keywords"]),
        ", ".join([f"{e['text']} ({e['type']})" for e in data["entities"]]),
        data["language"]
    ))
    conn.commit()
    conn.close()

def get_history(limit=50, category=None, priority=None, search=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT * FROM analyses WHERE 1=1"
    params = []
    if category and category != "ALL":
        query += " AND category=?"
        params.append(category)
    if priority and priority != "ALL":
        query += " AND priority=?"
        params.append(priority)
    if search:
        query += " AND feedback LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_analysis(analysis_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
    conn.commit()
    conn.close()

def get_all_for_export(category=None, priority=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT * FROM analyses WHERE 1=1"
    params = []
    if category and category != "ALL":
        query += " AND category=?"
        params.append(category)
    if priority and priority != "ALL":
        query += " AND priority=?"
        params.append(priority)
    query += " ORDER BY id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM analyses")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM analyses WHERE priority='HIGH PRIORITY'")
    high = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM analyses WHERE priority='MEDIUM PRIORITY'")
    medium = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM analyses WHERE priority='LOW PRIORITY'")
    low = c.fetchone()[0]
    c.execute("SELECT category, COUNT(*) as count FROM analyses GROUP BY category ORDER BY count DESC")
    categories = c.fetchall()
    c.execute("SELECT sentiment, COUNT(*) as count FROM analyses GROUP BY sentiment ORDER BY count DESC")
    sentiments = c.fetchall()
    c.execute("SELECT AVG(confidence) FROM analyses")
    avg_conf = c.fetchone()[0] or 0
    conn.close()
    return {
        "total": total, "high": high, "medium": medium, "low": low,
        "categories": categories, "sentiments": sentiments,
        "avg_confidence": round(avg_conf, 1)
    }

def detect_language(text):
    body = {"documents": [{"id": "1", "text": text}]}
    response = requests.post(ENDPOINT + "text/analytics/v3.1/languages", headers=HEADERS, json=body).json()
    lang = response["documents"][0]["detectedLanguage"]
    return lang["name"], lang["confidenceScore"]

def get_entities(text):
    body = {"documents": [{"id": "1", "language": "en", "text": text}]}
    response = requests.post(ENDPOINT + "text/analytics/v3.1/entities/recognition/general", headers=HEADERS, json=body).json()
    useful_types = ["Duration", "Quantity", "Location", "DateTime"]
    entities = []
    for entity in response["documents"][0]["entities"]:
        if entity["category"] in useful_types:
            entities.append({"text": entity["text"], "type": entity["category"]})
    return entities

def analyse(text):
    body = {"documents": [{"id": "1", "language": "en", "text": text}]}
    sentiment_resp = requests.post(ENDPOINT + "text/analytics/v3.1/sentiment", headers=HEADERS, json=body).json()
    phrases_resp = requests.post(ENDPOINT + "text/analytics/v3.1/keyPhrases", headers=HEADERS, json=body).json()
    sent_doc = sentiment_resp["documents"][0]
    sent = sent_doc["sentiment"]
    confidence = sent_doc["confidenceScores"][sent]
    keys = phrases_resp["documents"][0]["keyPhrases"]
    entities = get_entities(text)
    language, lang_confidence = detect_language(text)

    text_lower = text.lower()
    if any(w in text_lower for w in ["boiler","heating","water","roof","leak","repair","mould","broken","damp","pipe","electrical","wiring"]):
        category = "MAINTENANCE"
    elif any(w in text_lower for w in ["rent","payment","invoice","charge","bill","deposit","refund"]):
        category = "RENT & PAYMENTS"
    elif any(w in text_lower for w in ["garden","community","space","neighbours","noise","parking","communal"]):
        category = "COMMUNITY"
    else:
        category = "GENERAL"

    if sent == "negative" and category == "MAINTENANCE":
        priority = "HIGH PRIORITY"
        color = "#ff4444"
    elif sent == "negative":
        priority = "MEDIUM PRIORITY"
        color = "#ffaa00"
    else:
        priority = "LOW PRIORITY"
        color = "#00aa44"

    return {
        "sentiment": sent.upper(),
        "confidence": round(confidence * 100, 1),
        "category": category,
        "keywords": keys,
        "priority": priority,
        "color": color,
        "entities": entities,
        "language": language,
        "lang_confidence": round(lang_confidence * 100, 1)
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyse", methods=["POST"])
def analyse_route():
    text = request.json.get("text", "")
    result = analyse(text)
    save_analysis(result, text)
    return jsonify(result)

@app.route("/history")
def history():
    category = request.args.get("category", "ALL")
    priority = request.args.get("priority", "ALL")
    search = request.args.get("search", "")
    rows = get_history(category=category, priority=priority, search=search)
    return jsonify([{
        "id": r[0], "timestamp": r[1], "feedback": r[2],
        "sentiment": r[3], "confidence": r[4], "category": r[5],
        "priority": r[6], "keywords": r[7], "entities": r[8], "language": r[9]
    } for r in rows])

@app.route("/delete/<int:analysis_id>", methods=["DELETE"])
def delete_route(analysis_id):
    delete_analysis(analysis_id)
    return jsonify({"status": "deleted"})

@app.route("/export")
def export():
    category = request.args.get("category", "ALL")
    priority = request.args.get("priority", "ALL")
    rows = get_all_for_export(category=category, priority=priority)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Feedback", "Sentiment", "Confidence", "Category", "Priority", "Keywords", "Entities", "Language"])
    for r in rows:
        writer.writerow(r)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=feedback_export.csv"}
    )

@app.route("/dashboard")
def dashboard():
    stats = get_stats()
    return render_template("dashboard.html", stats=stats)

if __name__ == "__main__":
    os.chdir(r"C:\Users\user\Desktop\DB\phase2")
    init_db()
    app.run(debug=True)