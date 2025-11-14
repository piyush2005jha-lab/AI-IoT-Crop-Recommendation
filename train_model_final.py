import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE
import joblib
import os

# 1. Load Dataset
data = pd.read_csv("jharkhand_crops_filled_int.csv")

# ✅ Match columns exactly as in CSV
expected_columns = [
    "Temparature",   # spelling in CSV
    "Humidity",
    "Moisture",
    "Nitrogen",
    "Phosphorous",
    "Potassium",
    "Ph",            # matches CSV
    "Zn",
    "S",
    "Rainfall",
    "Wind Speed",
    "CLOUD_AMT",
    "PS",
    "Crop"
]

# Keep only required columns
data = data[expected_columns]

# 2. Handle Missing Values
data = data.dropna(subset=['Crop'])  # remove rows with missing target

feature_columns = [col for col in expected_columns if col != 'Crop']
for col in feature_columns:
    if data[col].isna().any():
        data[col] = data[col].fillna(data[col].mean())

# 3. Split Features & Target
X = data.drop(columns=["Crop"])   # features
y = data["Crop"]                  # target label

# Encode crop labels into numbers
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# ✅ 4. Apply SMOTE Balancing
smote = SMOTE(random_state=42, k_neighbors=3)
X_balanced, y_balanced = smote.fit_resample(X, y_encoded)

print("Before SMOTE:", pd.Series(y_encoded).value_counts().to_dict())
print("After SMOTE:", pd.Series(y_balanced).value_counts().to_dict())

# 5. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42
)

# 6. Train Model
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# 7. Evaluate
y_pred = model.predict(X_test)
print("\n✅ Accuracy:", round(accuracy_score(y_test, y_pred) * 100, 2), "%")
print("\n📊 Classification Report:\n", classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# 8. Save Model, Encoder, Feature List, and Feature Means
feature_means = X.mean(numeric_only=True)

joblib.dump(model, "crop_recommendation_model.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
joblib.dump(list(X.columns), "feature_columns.pkl")
joblib.dump(feature_means, "feature_means.pkl")

print("✅ Model training complete with SMOTE balanced data! Model, encoder, feature list, and means saved.")

# 9. Function to Suggest Top Crops
def suggest_crop(input_values, top_n=3):
    """
    input_values: list of sensor + weather values in the same order as dataset columns (except Crop).
                  If some values are missing, just put None.
    top_n: how many crop suggestions to return (default = 3).
    """
    # Load saved model and encoder
    model = joblib.load("crop_recommendation_model.pkl")
    label_encoder = joblib.load("label_encoder.pkl")
    feature_columns = joblib.load("feature_columns.pkl")
    feature_means = joblib.load("feature_means.pkl")

    # Convert to DataFrame
    input_df = pd.DataFrame([input_values], columns=feature_columns)

    # Fill missing values with saved means
    input_df = input_df.fillna(feature_means)

    # Predict probabilities
    probabilities = model.predict_proba(input_df)[0]

    # Get top_n crops
    top_indices = probabilities.argsort()[-top_n:][::-1]

    # Map back to crop names
    top_crops = [
        (label_encoder.inverse_transform([i])[0], round(probabilities[i] * 100, 2))
        for i in top_indices
    ]
    return top_crops


# 🔍 Debug: list saved files
print("\nSaved files:", os.listdir())
