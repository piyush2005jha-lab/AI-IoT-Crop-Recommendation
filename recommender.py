# recommender.py
from collections import Counter, defaultdict
import re
from difflib import get_close_matches

DISEASE_TO_RECOMMEND = {
    "powdery mildew": "Apply Sulphur-based fungicide or Azoxystrobin.",
    "late blight": "Use copper fungicide; remove infected material.",
    "early blight": "Apply chlorothalonil/mancozeb and rotate crops.",
    "leaf spot": "Fungicide + remove debris; improve air circulation.",
    "rust": "Systemic fungicides (triazoles) + resistant cultivars.",
    "stem rot": "Improve drainage; fungicide drench where needed.",
    "aphid": "Neem oil, insecticidal soap, or natural predators.",
    "whitefly": "Sticky traps, reflective mulch, insecticides.",
    "borer": "Bt spray, pheromone traps, targeted insecticides.",
    "nematode": "Crop rotation, organic amendments, nematicides."
}

DEFICIENCY_TO_FERTILIZER = {
    "nitrogen deficiency": "Apply Urea (46% N) or Ammonium Nitrate.",
    "phosphorus deficiency": "Apply SSP or DAP near roots.",
    "potassium deficiency": "Use MOP or SOP.",
    "iron deficiency": "Spray Fe-EDDHA chelate or apply soil iron.",
    "zinc deficiency": "Apply Zinc sulfate or foliar Zn sprays.",
    "magnesium deficiency": "Epsom salt foliar spray or soil mix.",
    "sulfur deficiency": "Ammonium sulfate or gypsum.",
    "calcium deficiency": "Gypsum, lime or foliar calcium spray."
}

SYMPTOM_KEYWORDS = {
    "white powder on leaves": "powdery mildew",
    "brown lesions": "leaf spot",
    "dark wet lesions on tubers": "late blight",
    "yellowing of leaves starting from bottom": "nitrogen deficiency",
    "interveinal chlorosis": "iron deficiency",
    "yellowing at leaf margins": "potassium deficiency",
    "holes in leaves": "borer",
    "sticky honeydew on leaves": "aphid",
    "white cottony patches": "whitefly"
}

def normalize_text(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def infer_from_symptoms(symptoms):
    found = Counter()
    text = normalize_text(" ".join(symptoms))
    for phrase, mapped in SYMPTOM_KEYWORDS.items():
        if normalize_text(phrase) in text:
            found[mapped] += 1
    return found

def generate_recommendations(user_symptoms=None):
    rec = defaultdict(list)
    infer = infer_from_symptoms(user_symptoms) if user_symptoms else Counter()

    for disease, cnt in infer.items():
        if disease in DISEASE_TO_RECOMMEND:
            rec['diseases'].append({
                "name": disease, "evidence": cnt, 
                "recommendation": DISEASE_TO_RECOMMEND[disease]
            })
        elif disease in DEFICIENCY_TO_FERTILIZER:
            rec['deficiencies'].append({
                "name": disease, "evidence": cnt, 
                "recommendation": DEFICIENCY_TO_FERTILIZER[disease]
            })
    return rec
