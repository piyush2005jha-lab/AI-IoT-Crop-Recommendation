📌 AI + IoT Based Crop Recommendation System

This project is a Smart Agriculture System that uses Machine Learning + IoT sensors to recommend the best crop based on soil, weather, and market data.
It includes a fully designed web UI + real-time IoT integration.

🚀 Features
🌱 AI/ML Features

Predicts best crop using ML model
Uses sensor + weather + soil inputs
Cleaned and preprocessed dataset
Feature encoding + scaling
ML model trained (Random Forest / XGBoost etc.)

📡 IoT Features

IoT sensors capture real-time farm data
Sensor output sent to backend API
Data processed via ML recommender
Live readings displayed on dashboard

💻 Web Application

Clean HTML templates

Includes:
Crop recommendation
Fertilizer advice
Weather forecast
Market price
IoT live data
Manual crop input

🏗 Tech Stack
💡 Machine Learning
Python
Pandas
NumPy
Scikit-learn
Joblib / Pickle

📡 IoT Hardware

NodeMCU / ESP8266 / ESP32
DHT11 / DHT22
Soil Moisture Sensor
pH Sensor

🖥 Backend
Flask (Python)

🎨 Frontend

HTML
CSS
Bootstrap

📁 Project Structure
AI-IoT-Crop-Recommendation/
│
├── app.py
├── recommender.py
├── sensor_output.py
├── cleanData.py
├── train_model_final.py
├── weather_service.py
├── avg.txt
│
├── static/
│   └── images/
│
├── templates/
│   ├── index.html
│   ├── crop.html
│   ├── fertilizer.html
│   ├── recommend_crop.html
│   ├── weather.html
│   ├── market.html
│   ├── iot.html
│   └── manual.html
│
└── iot_device/
    └── sensor_code.py

📊 How the ML Model Works

Data cleaned using cleanData.py
Feature engineering applied
Encoding + scaling
ML model trained using train_model_final.py
Model saved (not uploaded due to size)
Model used inside recommender.py
Web UI shows output

☁️ Dataset & ML Model

📥 Download Dataset + Trained ML Model

Due to GitHub’s 100MB file-size limit, the complete dataset and the trained ML model files are stored on Google Drive.

You can download all the required files from the link below:

👉 Google Drive Folder:
https://drive.google.com/drive/folders/1EuV2aX22pSRApxB5BmvHwvtyR8CqnYDM?usp=sharing

This folder includes:

Full dataset (.xlsx / .csv)
Trained ML model (.pkl files)
Encoders
Any additional large resources
