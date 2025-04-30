from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import torch
import re
from transformers import AutoTokenizer

# Sample patient data stored on the server
patient_data = {
    "P001": { "Normal": 14000, "Depression": 12000, "Suicidal": 8000, "Anxiety": 3000, "Bipolar": 2000, "Stress": 1500, "Personality_disorder": 800 },
    "P002": { "Normal": 16000, "Depression": 14000, "Suicidal": 9000, "Anxiety": 3500, "Bipolar": 2200, "Stress": 1800, "Personality_disorder": 900 },
    "P003": { "Normal": 15000, "Depression": 13000, "Suicidal": 8500, "Anxiety": 3200, "Bipolar": 2100, "Stress": 1600, "Personality_disorder": 850 },
    "P004": { "Normal": 16351, "Depression": 15404, "Suicidal": 10653, "Anxiety": 3888, "Bipolar": 2877, "Stress": 2669, "Personality_disorder": 1201 }
}

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for frontend access

# Load tokenizer (Make sure it's the same one used during training)
tokenizer = AutoTokenizer.from_pretrained("roberta-base")

# Load the pickled model
model_path = "model/model.pkl"  # Adjust this path if needed
with open(model_path, "rb") as file:
    model = pickle.load(file)

# Ensure the model is on the right device (GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()  # Set model to evaluation mode



# Personality Types data
personality_types = {
    "P001": "Borderline Personality Disorder (BPD)",
    "P002": "Obsessive-Compulsive Personality Disorder (OCPD)",
    "P003": "Antisocial Personality Disorder (ASPD)",
    "P004": "Paranoid Personality Disorder (PPD)"
}

# Function to analyze sentiment and mental health status using the ML model
def analyze_sentiment_and_status(text):
    if not text.strip():
        return {
            "sentiment": "Neutral 😕",
            "emotion": "No valid input",
            "status": "N/A"
        }

    # 🔹 Tokenize text properly before passing it to the model
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)

    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    prediction = torch.argmax(logits, dim=1).item()

    # Map predictions to sentiment labels
    sentiment_map = {
        0: ("Negative 😡", "Frustrated / Angry"),
        1: ("Neutral 😕", "Confused"),
        2: ("Positive 😃", "Happy")
    }

    sentiment, emotion = sentiment_map.get(prediction, ("Unknown", "Unknown"))

    # 🔥 Mental health status detection (basic NLP-based)
    text_lower = text.lower()

    # Keyword-based mental health classification
    status_map = {
    "suicidal": ["suicide", "kill", "end", "die", "no reason", "goodbye", "worth living"],
    "depressed": ["depressed", "hopeless", "sad", "down", "worthless", "empty"],
    "bipolar": ["manic", "bipolar", "mood swings", "super high", "super low"],
    "anxious": ["anxious", "nervous", "panic", "stressed", "worried", "fear"],
    "normal": ["happy", "okay", "fine", "good", "calm", "relaxed"]
    }




    # Inside your analyze_sentiment_and_status function
    status = "Normal"
    for label, keywords in status_map.items():
        for keyword in keywords:
            # Use regex to avoid partial word matches (e.g., "diesel" matching "die")
            if re.search(rf'\b{re.escape(keyword)}\b', text_lower):
                status = label.capitalize()
                break
        if status != "Normal":
            break

    # Return the analysis result
    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "status": status.capitalize()  # Capitalize the status for readability
    }


# 🔹 Flask Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/single_analysis")
def single_analysis():
    return render_template("single_analysis.html")

@app.route("/bulk")
def bulk():
    return render_template("bulk.html")

@app.route("/patient")
def patient():
    return render_template("patient.html")

# 🔹 API: Fetch Patient Data
@app.route("/fetch_patient", methods=["POST"])
def fetch_patient():
    data = request.json
    patient_id = data.get("patient_id", "").upper()

    if patient_id in patient_data:
        patient_info = patient_data[patient_id]
        patient_info["PersonalityType"] = personality_types.get(patient_id, "Not Available")
        return jsonify(patient_info)

    return jsonify({"error": "Patient not found"}), 404

# 🔹 API: Single Sentiment Analysis
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")

    result = analyze_sentiment_and_status(text)
    return jsonify(result)

# 🔹 API: Bulk Sentiment Analysis via CSV Upload
@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    
    try:
        df = pd.read_csv(file)
        if "Text" not in df.columns:
            return jsonify({"error": "CSV must have a 'Text' column"}), 400

        df["Sentiment"] = df["Text"].apply(lambda x: analyze_sentiment_and_status(x)["sentiment"])
        
        results = df.to_dict(orient="records")
        return jsonify(results)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#def infer_personality_type(stats):
    # if stats["suicidal"] > 8000 and stats["depression"] > 10000:
    #     return "Borderline Personality Disorder (BPD)"
    # elif stats["normal"] > 15000 and stats["stress"] > 2000:
    #     return "Obsessive-Compulsive Personality Disorder (OCPD)"
    # elif stats["bipolar"] > 2000 and stats["stress"] > 1000:
    #     return "Antisocial Personality Disorder (ASPD)"
    # else:
    #     return "Undiagnosed / Not Clear"


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
