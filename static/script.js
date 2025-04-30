// Function to handle patient form submission and fetch data from Flask API
document.getElementById('patientForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    let patientID = document.getElementById('patientID').value.trim().toUpperCase();
    let statusDiv = document.getElementById('patientStatus');

    if (!patientID) {
        statusDiv.innerHTML = `<p style="color: red;">Please enter a Patient ID.</p>`;
        return;
    }

    try {
        let response = await fetch(`/patient/${patientID}`); // Flask API request
        if (!response.ok) throw new Error("Patient not found.");

        let data = await response.json(); // Get JSON response from Flask backend

        // Build UI with fetched patient data
        statusDiv.innerHTML = `
            <h2>Patient ID: ${patientID}</h2>
            <table>
                <tr><th>Status</th><th>Count</th></tr>
                <tr><td>Normal</td><td>${data.Normal}</td></tr>
                <tr><td>Depression</td><td>${data.Depression}</td></tr>
                <tr><td>Suicidal</td><td>${data.Suicidal}</td></tr>
                <tr><td>Anxiety</td><td>${data.Anxiety}</td></tr>
                <tr><td>Bipolar</td><td>${data.Bipolar}</td></tr>
                <tr><td>Stress</td><td>${data.Stress}</td></tr>
                <tr><td>Personality Disorder</td><td>${data.Personality_disorder}</td></tr>
            </table>
        `;

        // Add Personality Disorder Type if available
        if (data.PersonalityType) {
            statusDiv.innerHTML += `<p><strong>Personality Disorder Type:</strong> ${data.PersonalityType}</p>`;
        }

    } catch (error) {
        console.error("Error fetching patient data:", error);
        statusDiv.innerHTML = `<p style="color: red;">Patient ID not found. Please try again.</p>`;
    }
});

// Function to analyze user feedback
async function analyzeFeedback() {
    const feedback = document.getElementById("feedbackInput").value;

    if (!feedback.trim()) {
        alert("Please enter some text.");
        return;
    }

    fetch("/analyze", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: feedback })
    })
    .then(response => response.json())
    .then(data => {
        // Display the results
        document.getElementById("sentimentResult").textContent = data.sentiment;
        document.getElementById("emotionResult").textContent = data.emotion;
        document.getElementById("statusResult").textContent = data.status;

        // Color coding for status
        const statusElement = document.getElementById("statusResult");
        switch (data.status.toLowerCase()) {
            case "depressed":
                statusElement.style.color = "red";
                break;
            case "suicidal":
                statusElement.style.color = "darkred";
                break;
            case "bipolar":
                statusElement.style.color = "purple";
                break;
            case "anxious":
                statusElement.style.color = "orange";
                break;
            case "normal":
                statusElement.style.color = "green";
                break;
            default:
                statusElement.style.color = "black";
        }
    })
    .catch(error => {
        console.error("Error:", error);
        alert("An error occurred while analyzing the feedback.");
    });
}


// Function to handle CSV file upload and analyze sentiment
async function uploadFile() {
    let fileInput = document.getElementById("fileInput").files[0];
    if (!fileInput) {
        alert("Please select a CSV file.");
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput);

    let summaryText = document.getElementById("summaryText");

    // Total time in seconds (2 hours)
    let totalSeconds = 2 * 60 * 60;

    // Start countdown timer
    let interval = setInterval(() => {
        let hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
        let minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
        let seconds = String(totalSeconds % 60).padStart(2, '0');

        summaryText.innerHTML = `⏳ Uploading... Time remaining: ${hours}:${minutes}:${seconds}`;
        totalSeconds--;

        if (totalSeconds < 0) {
            clearInterval(interval);
        }
    }, 1000);

    try {
        // Fake 2-hour delay
        await new Promise(resolve => setTimeout(resolve, 2 * 60 * 60 * 1000));

        clearInterval(interval);

        let response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        let results = await response.json();

        let resultsTable = document.getElementById("resultsTable").getElementsByTagName("tbody")[0];
        resultsTable.innerHTML = "";

        results.forEach((row, index) => {
            let newRow = resultsTable.insertRow();
            newRow.innerHTML = `<td>${index + 1}</td><td>${row.Sentiment}</td>`;
        });

        summaryText.innerHTML = "✔️ Sentiment analysis completed.";
    } catch (error) {
        clearInterval(interval);
        console.error("Error uploading file:", error);
        alert("An error occurred while uploading the file.");
        summaryText.innerHTML = "❌ Upload failed.";
    }
}


