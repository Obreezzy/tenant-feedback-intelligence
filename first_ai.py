import requests
import csv
import os

os.chdir(r"C:\Users\user\Desktop\DB")
from dotenv import load_dotenv
import os
load_dotenv(r"C:\Users\user\Desktop\DB\.env", encoding="utf-8")
KEY = os.getenv("KEY")
ENDPOINT = "https://obreeze-ai-hub.cognitiveservices.azure.com/"

headers = {
    "Ocp-Apim-Subscription-Key": KEY,
    "Content-Type": "application/json"
}

feedbacks = [
    "The boiler has been broken for two weeks and we have no hot water. Nobody is responding to our calls.",
    "Rent payment was processed smoothly this month, thank you for the easy online system.",
    "There is mould growing on the bedroom walls and my children are getting sick. This is urgent.",
    "The new community garden is wonderful, residents are really enjoying the space.",
    "We have been waiting 3 months for the roof repair. Water is leaking into the living room."
]

body = {
    "documents": [
        {"id": str(i+1), "language": "en", "text": text}
        for i, text in enumerate(feedbacks)
    ]
}

sentiment_response = requests.post(
    ENDPOINT + "text/analytics/v3.1/sentiment",
    headers=headers, json=body
).json()

keyphrases_response = requests.post(
    ENDPOINT + "text/analytics/v3.1/keyPhrases",
    headers=headers, json=body
).json()

def categorise(text):
    text = text.lower()
    if any(w in text for w in ["boiler","heating","water","roof","leak","repair","mould","broken"]):
        return "MAINTENANCE"
    elif any(w in text for w in ["rent","payment","invoice","charge","bill"]):
        return "RENT & PAYMENTS"
    elif any(w in text for w in ["garden","community","space","neighbours","noise"]):
        return "COMMUNITY"
    else:
        return "GENERAL"

def priority(sentiment, category):
    if sentiment == "negative" and category == "MAINTENANCE":
        return "HIGH PRIORITY"
    elif sentiment == "negative":
        return "MEDIUM PRIORITY"
    else:
        return "LOW PRIORITY"

print("=" * 65)
print("   TENANT FEEDBACK INTELLIGENCE SYSTEM")
print("   Powered by Azure AI")
print("=" * 65)

for i, feedback in enumerate(feedbacks):
    doc_id = str(i + 1)
    sentiment = next(d for d in sentiment_response["documents"] if d["id"] == doc_id)
    phrases = next(d for d in keyphrases_response["documents"] if d["id"] == doc_id)

    category = categorise(feedback)
    sent = sentiment["sentiment"]
    prio = priority(sent, category)

    print(f"\nFeedback #{doc_id}")
    print(f"Text      : {feedback[:70]}...")
    print(f"Category  : {category}")
    print(f"Sentiment : {sent.upper()}")
    print(f"Keywords  : {', '.join(phrases['keyPhrases'])}")
    print(f"Status    : {prio}")
    print("-" * 65)

with open("tenant_report.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["Feedback", "Category", "Sentiment", "Keywords", "Priority"])
    for i, feedback in enumerate(feedbacks):
        doc_id = str(i + 1)
        sentiment = next(d for d in sentiment_response["documents"] if d["id"] == doc_id)
        phrases = next(d for d in keyphrases_response["documents"] if d["id"] == doc_id)
        category = categorise(feedback)
        sent = sentiment["sentiment"].upper()
        prio = priority(sentiment["sentiment"], category)
        writer.writerow([feedback, category, sent, ", ".join(phrases["keyPhrases"]), prio])

print("\nReport saved to tenant_report.csv")