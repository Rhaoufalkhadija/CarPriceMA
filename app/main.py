from flask import Flask, render_template, request
import pandas as pd
import json
import joblib
import os

app = Flask(__name__)

# Chemin absolu vers le dossier courant (app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin vers les dossiers mappings et model
mappings_path = os.path.join(BASE_DIR, "mappings")  # app/mappings
model_path = os.path.join(BASE_DIR, "model", "xgb_model_voiture_transformed.pkl")  # app/model/xgb_model_voiture_transformed.pkl

# Vérifier que le modèle existe
if not os.path.isfile(model_path):
    raise FileNotFoundError(f"Modèle introuvable : {model_path}")

# Charger tous les fichiers JSON dans mappings/
def load_all_mappings(mapping_dir):
    mappings = {}
    for filename in os.listdir(mapping_dir):
        if filename.endswith('.json'):
            key = filename.replace('.json', '')
            with open(os.path.join(mapping_dir, filename), 'r', encoding='utf-8') as file:
                mappings[key] = json.load(file)
    return mappings

mappings = load_all_mappings(mappings_path)
model = joblib.load(model_path)
colonnes_modele = model.get_booster().feature_names

def preprocess_input(data):
    processed_data = {
        'kilometrage': float(data.get('kilometrage', 0)),
        'Age': mappings['Age_mapping'].get(str(2025 - int(data.get('annee', 2025))), 0),
        'NBporte': mappings['NBporte_mapping'].get(str(data.get('nombre_de_porte', '')), 0),
        'Puissance fiscale': mappings['Puissance_fiscale_mapping'].get(str(data.get('puissance_fiscale', '')), 0),
        'Marque_freq': mappings['Marque_mapping'].get(data.get('marque', ''), 0),
        'Modèle_freq': mappings['Modèle_mapping'].get(data.get('modele', ''), 0),
        'Etat': mappings['Etat_mapping'].get(data.get('Etat', ''), 0),
        'Origine': mappings['Origine_mapping'].get(data.get('Origine', ''), 0),
        'BoiteàV': mappings['BoiteàV_mapping'].get(data.get('transmission', ''), 0),
        'Carburant': mappings['Carburant_mapping'].get(data.get('carburant', ''), 0),
        'Première main': mappings['Première_main_mapping'].get(data.get('première_maint', ''), 0)
    }

    equipements = mappings.get('équipements_mapping', {})
    selected_equipements = data.get('equipements', [])

    for eq in equipements:
        processed_data[eq] = 1 if eq in selected_equipements else 0

    # Ajouter les colonnes manquantes à 0
    for col in colonnes_modele:
        if col not in processed_data:
            processed_data[col] = 0

    df = pd.DataFrame([processed_data])
    df = df[colonnes_modele]
    return df

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        try:
            data = request.form.to_dict(flat=True)
            data['equipements'] = request.form.getlist('equipements[]')
            input_df = preprocess_input(data)
            prediction = round(model.predict(input_df)[0], 2)
            return render_template('predict.html', predicted_price=prediction)
        except Exception as e:
            print("Erreur lors de la prédiction :", str(e))
            return render_template('predict.html', error="Erreur lors de la prédiction")
    return render_template('predict.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    print(f"Chargement du modèle depuis : {model_path}")
    app.run(debug=True)
