# Tenant Feedback Intelligence System

A Python web application that uses Microsoft Azure AI to automatically analyse housing tenant feedback and classify complaints by sentiment, category, priority, keywords, and named entities.

## What it does

- Analyses tenant feedback text using Azure AI Language service
- Detects sentiment (positive, negative, neutral) with confidence scores
- Extracts key phrases from the complaint
- Identifies named entities such as durations and quantities
- Classifies feedback into categories: MAINTENANCE, RENT & PAYMENTS, COMMUNITY, GENERAL
- Flags priority level: HIGH PRIORITY, MEDIUM PRIORITY, LOW PRIORITY
- Detects language automatically including English, French, Shona and others
- Stores all analyses in a local SQLite database
- Shows analysis history panel with timestamps
- Dashboard page with stats: total analyses, priority breakdown, category breakdown, sentiment breakdown
- Bulk CSV upload to analyse multiple feedback entries at once
- Exports batch analysis results to CSV

## Azure AI Services used

- Sentiment Analysis
- Key Phrase Extraction
- Named Entity Recognition (NER)
- Language Detection

## Language support note

Language detection works well across most languages. The app was tested with English, French, and Shona. English analysis is fully supported across all features. For non-English text, sentiment and key phrase extraction still run but may be less accurate since the NLP models are optimised for English. Named entity recognition in particular performs significantly better on English text and may miss entities or return limited results for other languages.

## Project structure

- app.py - Flask web application with browser interface, history panel, dashboard and bulk upload
- first_ai.py - Batch analysis script with CSV export
- tenant_report.csv - Sample AI generated report

## How to run locally

1. Clone the repository
2. Install dependencies: pip install flask requests python-dotenv
3. Create a .env file in the project root with your Azure key: KEY=your_azure_key_here
4. Run the web app: python app.py
5. Open browser at http://127.0.0.1:5000
6. Use the Dashboard link in the navigation to view analysis statistics

## Pages

- / - Main analysis page with single feedback input and bulk CSV upload
- /dashboard - Statistics dashboard showing priority, category and sentiment breakdowns

## Tech stack

- Python
- Flask
- Azure AI Language Service
- SQLite
- Microsoft Azure for Students
