import streamlit as st
import docx2txt
import re
import os


phrases_of_recommendation = {
            "a contrôler après traitement",
            "une mammographie est à prévoir dans deux ans dans le cadre de dépistage",
            "un contrôle échographique après traitement est indiqué notamment à droite",
            "intérêt d'un contrôle échographique dans 4 à 6 mois, d'un dosage de la prolactinémie, et d'une étude cytologique du liquide d'écoulement mamelonnaire à gauche si persistance. à compléter par cytoponction",
            "a recontrôler dans 06 mois",
            "nécessitant une vérification histologique par macro-biopsie sous stéréotaxie",
            "un contrôle échographique est souhaitable dans six mois",
            "un prélèvement histologique par microbiopsie est indiqué",
            "un contrôle échographique après traitement est indiqué",
            "un contrôle échographique est souhaitable dans 04 à 06 mois",
            "à confronter aux données mammo et échographiques antérieures",
            "prévoir un contrôle échographique dans 04 mois",
            "une vérification cytologique est souhaitable au niveau du qme droit",
            "un contrôle échographique dans 6 mois",
            "prévoir un contrôle échographique dans 06 mois",
            "a recontrôler dans 4 à 6 mois",
            "il serait souhaitable de compléter par une microbiopsie à droite et une cytoponction à gauche",
            "un contrôle échographique après traitement bien conduit est nécessaire à gauche voir prélèvement si persistance ainsi qu'une vérification histologique de la masse mammaire droite",
            "à compléter par irm",
            "une vérification histologique par microbiopsie échoguidée est souhaitable à gauche",
            "un contrôle échographique après traitement bien conduit est nécessaire",
            "un complément irm mammaire après résolution des phénomènes inflammatoires est souhaitable afin de guider un éventuel prélèvement percutané",
            "un contrôle échographique est souhaitable après traitement",
            "intérêt d'un contrôle dans 06 mois",
            "intérêt d'une corrélation aux explorations appropriées",
            "la vérification histologique par microbiopsie échoguidée est indiquée",
            "à compléter par une microbiopsie",
            "une vérification histologique par microbiopsie est nécessaire à droite, ainsi d'une vérification cytologique du creux axillaire est indiquée",
            "un complément irm mammaire est souhaitable pour mieux caractériser l'image de distorsion architecturale du qse droit, et vu les antécédents familiaux de la patiente",
            "vérification histologique dans la crainte d'une dégénérescence",
            "à compléter par micro-biopsie, associée à une adénopathie axillaire homolatérale, à compléter par cytoponction",
            "un complément irm mammaire est également souhaitable vu les antécédents familiaux de la patiente",
            "un contrôle échographique est souhaitable dans 04 mois",
            "prévoir une micro-biopsie échoguidée",
            "un contrôle échographique dans 04 à 06 mois est souhaitable",
            "vérification histologique par macro-biopsie sous-stéréotaxie, notamment dans ce contexte",
            "prévoir un contrôle échographique dans six mois",
            "une vérification histologique par micro-biopsie échoguidée"
        }

def preprocess(report):
    """Preprocesses the report by converting it to lowercase, removing extra whitespaces, and replacing apostrophes."""
    # Convertir le rapport en minuscules pour une correspondance insensible à la casse
    report = report.lower()
    # Remplacer les apostrophes dans le rapport
    report = report.replace('’', "'")
    # Supprimer les espaces blancs supplémentaires
    report = re.sub(r'\s+', ' ', report)

    return report


def extract_date(report):
    """Extracts the date from the report."""
    date_pattern = r'(\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)?\s*\d{1,2}\s+\w+\s+\d{4}\b)'
    date_match = re.search(date_pattern, report)
    return date_match.group(0).strip().capitalize() if date_match else 'Unknown'

def extract_patient_id(head):
    """Extracts the patient ID from the report."""
    patient_id_pattern = r'(pat-\d+)'
    patient_id_match = re.search(patient_id_pattern, head)
    return patient_id_match.group(1) if patient_id_match else 'Unknown'

def extract_age(head):
    """Extracts the age from the report."""
    age_pattern = r'(\d+)\s*(?:ANS|ans)'
    age_match = re.search(age_pattern, head)
    return age_match.group(1) if age_match else 'Unknown'


def extract_line_after_age(head):
        """Extracts the non-empty line that appears after the word 'ANS' or 'ans' in the report."""
        pattern_age = r'\b\d+\s*ANS?\b'
        age_match = re.search(pattern_age, head, re.IGNORECASE)

        if age_match:
            next_line_start = head.find('\n', age_match.end())
            next_line_start = head.find('\n', next_line_start + 1)  # Look for the next line

           # Find the first non-empty line after 'ANS' or 'ans'
            next_line_end = head.find('\n', next_line_start + 1)
            while next_line_end < len(head) and head[next_line_start:next_line_end].strip() == '':
               next_line_end = head.find('\n', next_line_end + 1)

           # Extract the line after 'ANS' or 'ans' (non-empty)
            line = head[next_line_start:next_line_end].strip()
            return line
        else:
            return None
        

def extract_indication(head):
    """Extracts the indication from the report."""
    indication_pattern = r'(?i)(indication|motif)\s*:\s*(.*)'
    indication_match = re.search(indication_pattern, head)
    return indication_match.group(2).strip() if indication_match else 'no indication'

def extract_mammographie(result):
    """Extracte les informations de mammographie du résultat."""
    pattern = r'RESULTATS\s*(.*?)\s*(?:le complément échographique|échographie)'
    match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)

    mammographie = {'mammo_droite': 'Pas de mammographie', 'mammo_gauche': 'Pas de mammographie', 'mammo_both': 'Pas de mammographie', 'extracted_mammographie': 'Pas de mammographie'}

    if match:
        mammographie_text = match.group(1).strip()
        mammo_droite = []
        mammo_gauche = []
        mammo_both = []

        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', mammographie_text)  # Split into sentences

        for sentence in sentences:
            if 'gauche' in sentence.lower():
                mammo_gauche.append(sentence)
            elif 'droit' in sentence.lower():
                mammo_droite.append(sentence)
            else:
                mammo_both.append(sentence)

        # Joining sentences back into strings
        mammographie['extracted_mammographie'] = mammographie_text
        mammographie['mammo_droite'] = '. '.join(mammo_droite) if mammo_droite else 'Pas de mammographie'
        mammographie['mammo_gauche'] = '. '.join(mammo_gauche) if mammo_gauche else 'Pas de mammographie'
        mammographie['mammo_both'] = '. '.join(mammo_both) if mammo_both else 'Pas de mammographie'

    return mammographie


def extract_echographie(result):
    """Extracte les informations d'echographie du résultat."""
    pattern = r'(?:échographie|complément échographique)(.*?)(?=conclusion|$)'
    match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)

    echographie = {'echo_droite': 'Pas d\'échographie', 'echo_gauche': 'Pas d\'échographie', 'echo_both': 'Pas d\'échographie', 'extracted_echographie': 'Pas d\'échographie'}

    if match:
        echographie_text = match.group(1).strip()
        echo_droite = []
        echo_gauche = []
        echo_both = []

        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s',echographie_text)  # Split into sentences

        for sentence in sentences:
            if 'gauche' in sentence.lower():
                echo_gauche.append(sentence)
            elif 'droit' in sentence.lower():
                echo_droite.append(sentence)
            else:
                echo_both.append(sentence)

        # Joining sentences back into strings
        echographie['echo_droite'] = '. '.join(echo_droite) if echo_droite else 'Pas d\'échographie'
        echographie['echo_gauche'] = '. '.join(echo_gauche) if echo_gauche else 'Pas d\'échographie'
        echographie['echo_both'] = '. '.join(echo_both) if echo_both else 'Pas d\'échographie'

        # Ajout de la partie échographie extraite
        echographie['extracted_echographie'] = echographie_text

    return echographie


def extract_recommendations(conclusion):
    """Extracts the recommendations from the report."""
    recommendations = []
    for recommendation in phrases_of_recommendation:
        if re.search(re.escape(recommendation), conclusion):
            recommendations.append(recommendation)
    return recommendations


def extract_classification(report):
    # Utiliser des motifs regex pour rechercher des informations spécifiques
    birads_both_pattern = [
        r'bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+au\s+niveau\s+des\s+deux\s+seins',
        r'bilatérale\s+classé\s+bi-rads\s+(\d+[a-c]?)',
        r'bi-rads\s+(\d+[a-c]?)de\s+l\'acr\s+de\s+façon\s+bilatérale',
        r'classée\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite\s+comme\s+à\s+gauche',
        r'classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite\s+comme\s+à\s+gauche',
        r'examen.*classée\s+bi-rads\s+(\d+[a-c]?)',
        r'bi-rads\s+(\d+)\s+de\s+l\'acr(?!.*\bdroite\b)(?!.*\bgauche\b)',# classées bi-rads 1 de l'acr à droite comme à gauche.
        r'classées\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite\s+comme\s+à\s+gauche',
    ]
    birads_patterns_droit = [# sein droit classé bi-rads 1 de l'acr
        r'(?:examen\s+du\s+sein\s+droite\s+est\s+classé\s+bi-rads\s+(\d+[a-c]?))',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s*de\s+l\'acr\s+à\s+droite)', #Examen classé BI-RADS 3 de l’ACR à droite
        r'(?:classées\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite)',
        r'(?:classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite)',
        r'(?:classée\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+droite)',
        r'(?:\s*(\d+[a-c]?)\s*de\s*l\'acr\s*à\s*droite)',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s+à\s+droite\s+de\s+l\'acr)',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s+à\s+droite\s+de\s+l\'acr)', #gauches classés BI-RADS 4 de l'ACR, la masse mammaire gauche, classée BI-RADS 6 de l’ACR.
        r'(?:droits\s+classés\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)',# droit, classé BI-RADS 3 de l’ACR.
        r'(?:droit/s+,/s+classé\s+bi-rads\s+(\d+[a-c]?)\s+\s+de\s+l\'acr)',#Kyste remanié mammaire droit, classé BI-RADS 3 de l’ACR.
        r'(?:droite\s*[\w\s]+\s*,\s*classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)'#droite (qsi), classée birads 4 de l'acr
        r'(?:sein\s+droit\s+classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)',
        r'(?:droite\s*[\w\s]+\s*,\s*classée\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)' ,

    ]
    birads_patterns_gauche = [
        r'(?:examen\s+du\s+sein\s+gauche\s+est\s+classé\s+bi-rads\s+(\d+[a-c]?))',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s*de\s+l\'acr\s+à\s+gauche)',
        r'(?:classées\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+gauche)',
        r'(?:classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+gauche)',
        r'(?:classée\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+gauche)',
        r'(?:bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr\s+à\s+gauche)',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s+à\s+gauche\s+de\s+l\'acr)',
        r'(?:examen\s+classé\s+bi-rads\s+(\d+[a-c]?)\s+à\s+gauche\s+de\s+l\'acr)',
        r'(?:gauches\s+classés\s+bi-rads\s+(\d+[a-c]?)\s+à\s+droite\s+de\s+l\'acr)',
        r'(?:gauche\s+classée\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)',
        r'(?:gauche/s+,/s+classé\s+bi-rads\s+(\d+[a-c]?)\s+\s+de\s+l\'acr)',
        r'(?:gauche\s*[\w\s]+\s*,\s*classé\s+bi-rads\s+(\d+[a-c]?)\s+de\s+l\'acr)',# sein gauche classé bi-rads 3de l'acr.
        r'(?:gauche\s+classé\s+bi-rads\s+(\d+[a-c]?)de\s+l\'acr)',



    ]

    classifications = {'Left Breast Classification': 'Unknown', 'Right Breast Classification': 'Unknown'}
    for pattern in birads_both_pattern:
        match = re.search(pattern, report)
        if match:
            classification = match.group(1)
            classifications['Left Breast Classification'] = classification
            classifications['Right Breast Classification'] = classification
            break

    if classifications['Left Breast Classification'] == 'Unknown':
        for pattern in birads_patterns_gauche:
            match = re.search(pattern, report)
            if match:
                classifications['Left Breast Classification'] = match.group(1)
                break

    if classifications['Right Breast Classification'] == 'Unknown':
        for pattern in birads_patterns_droit:
            match = re.search(pattern, report)
            if match:
                classifications['Right Breast Classification'] = match.group(1)
                break

    return classifications


def extractReportPart(report):
        # Define patterns
    result_pattern = r'(?i)(RESULTATS?\s*:\s*)'
    conclusion_pattern = r'(?i)(CONCLUSIONS?\s*:\s*)'

    result_match = re.search(result_pattern, report)
    conclusion_match = re.search(conclusion_pattern, report)

    # Split the text based on patterns
    head_text =report[:result_match.start()] if result_pattern else ''
    result_text = report[result_match.start():conclusion_match.start()] if result_match and conclusion_match else report[result_match.start():] if result_match else ''
    conclusion_text = report[conclusion_match.start():] if conclusion_match else ''

    return preprocess(head_text),preprocess(result_text),preprocess(conclusion_text)


def extract_information(report:str):
    """Extracts all the relevant information from the mammography report."""


    head, result, conclusion = extractReportPart(report)
    report = preprocess(report)
    extracted_info = {
      'report':report,
      'head':head,
      'result':result,
      'conclusion':conclusion,
      'Date': extract_date(head),
      'Patient ID': extract_patient_id(head),
      'Age': extract_age(head),
    #   'title': extract_line_after_age(head),
      'Indication':extract_indication(head),
      **extract_mammographie(result),
      **extract_echographie(result),
      'Recommendations': extract_recommendations(conclusion),
      **extract_classification(conclusion)
   }
    return extracted_info



def main():
    st.title("Mammography Report Processing")

    # Upload text or .docx file
    upload_type = st.radio("Select upload type", ("Text", "Document"))

    if upload_type == "Text":
        report_text = st.text_area("Enter the report text")
        if report_text and st.button("Process Report"):
            extracted_info = extract_information(report_text)
            st.write(extracted_info)

    elif upload_type == "Document":
        uploaded_file = st.file_uploader("Choose a .docx file", type="docx")
        if uploaded_file is not None:
            report_text = docx2txt.process(uploaded_file)
            if st.button("Process Report"):
                extracted_info = extract_information(report_text)
                st.write(extracted_info)

if __name__ == "__main__":
    main()