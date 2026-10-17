from typing import Tuple, List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from app.nlp.preprocessor import clean_legal_text

# Human-readable display titles for categories
CATEGORY_DISPLAY_NAMES = {
    "CHEQUE_BOUNCE_NOTICE": "Cheque Dishonour Notice (Sec 138 NI Act)",
    "EMPLOYMENT_DISPUTE_NOTICE": "Employment & Termination Dispute Notice",
    "TENANCY_AND_EVICTION_NOTICE": "Tenancy Default & Eviction Notice",
    "COMMERCIAL_CONTRACT": "Commercial Agreement / Contract",
    "CONSUMER_COMPLAINT_NOTICE": "Consumer Grievance & Deficiency Notice",
    "DEFAMATION_NOTICE": "Defamation Cease & Desist Notice",
    "MATRIMONIAL_DISPUTE_NOTICE": "Matrimonial / Conjugal Dispute Notice",
    "COURT_SUMMONS_OR_ORDER": "Court Summons / Judicial Order",
    "GENERIC_LEGAL_NOTICE": "General Legal Notice / Communication"
}

# Training corpus for Indian Legal Document Categories
# Represents authentic statutory language, notice headers, and dispute clauses
LEGAL_TRAINING_CORPUS = [
    # CHEQUE_BOUNCE_NOTICE
    ("Demand notice under section 138 of negotiable instruments act cheque dishonoured for insufficient funds memo drawer bank", "CHEQUE_BOUNCE_NOTICE"),
    ("Dishonour of cheque statutory notice section 138 NI act 15 days notice pay cheque amount failing criminal proceedings complaint under section 142", "CHEQUE_BOUNCE_NOTICE"),
    ("Legal notice for dishonour of cheque drawn on State Bank of India returned unpaid with remarks funds insufficient or signature mismatch", "CHEQUE_BOUNCE_NOTICE"),
    ("Pay the cheque amount within 15 days of service of notice else criminal complaint under section 138 negotiable instruments act", "CHEQUE_BOUNCE_NOTICE"),
    
    # EMPLOYMENT_DISPUTE_NOTICE
    ("Termination of employment wrongful termination without notice period severance pay unpaid salary and dues employment contract breach", "EMPLOYMENT_DISPUTE_NOTICE"),
    ("Notice for recovery of pending salary gratuity provident fund bonus and wrongful termination of employment service by employer", "EMPLOYMENT_DISPUTE_NOTICE"),
    ("Employment agreement breach of non-compete clause non-solicitation notice period absconding from duty employment dues", "EMPLOYMENT_DISPUTE_NOTICE"),
    ("Relieving letter full and final settlement pending salary dues labour court industrial dispute employment termination", "EMPLOYMENT_DISPUTE_NOTICE"),
    
    # TENANCY_AND_EVICTION_NOTICE
    ("Notice to quit and vacate leased premises tenancy eviction default in payment of monthly rent lease deed termination Transfer of Property Act", "TENANCY_AND_EVICTION_NOTICE"),
    ("Eviction notice to tenant arrears of rent vacate the rented premises within thirty days failing eviction suit will be filed", "TENANCY_AND_EVICTION_NOTICE"),
    ("Landlord tenant dispute termination of lease agreement hand over vacant peaceful physical possession arrears of maintenance", "TENANCY_AND_EVICTION_NOTICE"),
    ("Termination of tenancy under section 106 transfer of property act vacate property illegal subletting non payment of rent", "TENANCY_AND_EVICTION_NOTICE"),
    
    # COMMERCIAL_CONTRACT
    ("Non-disclosure agreement service level agreement master services contract terms of payment indemnification liability clause", "COMMERCIAL_CONTRACT"),
    ("This agreement entered into between client and service provider representations warranties term and termination arbitration clause", "COMMERCIAL_CONTRACT"),
    ("Vendor agreement supply of software deliverables intellectual property rights governing law jurisdiction confidentiality obligations", "COMMERCIAL_CONTRACT"),
    ("Consultancy agreement scope of work force majeure dispute resolution schedule of fees mutually agreed terms", "COMMERCIAL_CONTRACT"),
    
    # CONSUMER_COMPLAINT_NOTICE
    ("Notice under Consumer Protection Act 2019 deficiency in service defective product unfair trade practice refund and compensation", "CONSUMER_COMPLAINT_NOTICE"),
    ("Deficiency of service consumer forum district consumer commission claim compensation for mental agony and harassment refund amount", "CONSUMER_COMPLAINT_NOTICE"),
    ("Notice to manufacturer defective goods failure to provide warranty replacement or repair consumer rights protection complaint", "CONSUMER_COMPLAINT_NOTICE"),
    ("Consumer grievance flight cancellation refund non-delivery of service deficient customer care unfair business practice", "CONSUMER_COMPLAINT_NOTICE"),
    
    # DEFAMATION_NOTICE
    ("Cease and desist notice defamation civil defamation criminal defamation section 499 500 IPC false and defamatory statements", "DEFAMATION_NOTICE"),
    ("Tender unconditional apology withdraw defamatory remarks posted on social media damage to client reputation damages worth crores", "DEFAMATION_NOTICE"),
    ("Defamatory video publication malicious falsehood damage to goodwill character assassination legal notice unconditional retraction", "DEFAMATION_NOTICE"),
    
    # MATRIMONIAL_DISPUTE_NOTICE
    ("Notice for restitution of conjugal rights section 9 Hindu Marriage Act cruelty maintenance section 125 CrPC matrimonial dispute", "MATRIMONIAL_DISPUTE_NOTICE"),
    ("Divorce notice mental cruelty desertion streedhan return of dowry articles domestic violence maintenance petition family court", "MATRIMONIAL_DISPUTE_NOTICE"),
    ("Matrimonial discord separation custody of minor child alimony permanent alimony family court mediation", "MATRIMONIAL_DISPUTE_NOTICE"),
    
    # COURT_SUMMONS_OR_ORDER
    ("Summons to appear before the court of civil judge appearance in person or through pleader order 5 rule 1 CPC writ petition", "COURT_SUMMONS_OR_ORDER"),
    ("Notice of motion high court interim stay order injunction granted status quo directed compliance report within two weeks", "COURT_SUMMONS_OR_ORDER"),
    ("Bailable warrant summons issued by chief judicial magistrate criminal case number date of hearing appear before court", "COURT_SUMMONS_OR_ORDER"),
    
    # GENERIC_LEGAL_NOTICE
    ("Legal notice under instruction of client calling upon to settle pending dispute within stipulated time failing legal recourse", "GENERIC_LEGAL_NOTICE"),
    ("Final reminder demand notice legal notice to settle accounts breach of obligation take appropriate legal proceedings in competent court", "GENERIC_LEGAL_NOTICE")
]

class LegalDocumentClassifier:
    """
    TF-IDF Vectorizer + Calibrated Logistic Regression model for classifying Indian legal documents.
    Provides explainable confidence metrics and identifies top predictive keywords.
    """
    def __init__(self):
        texts = [item[0] for item in LEGAL_TRAINING_CORPUS]
        labels = [item[1] for item in LEGAL_TRAINING_CORPUS]
        
        # Word and bigram TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )
        
        # Multiclass Logistic Regression with balanced class weights
        self.classifier = LogisticRegression(
            C=5.0,
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )
        
        self.pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('clf', self.classifier)
        ])
        
        self.pipeline.fit(texts, labels)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())

    def predict(self, document_text: str) -> Tuple[str, str, float, List[str]]:
        """
        Classifies input text.
        
        Returns:
            category_key: Machine identifier e.g. 'CHEQUE_BOUNCE_NOTICE'
            category_display_name: Human-friendly name e.g. 'Cheque Dishonour Notice (Sec 138 NI Act)'
            confidence: Probability score between 0.0 and 1.0
            top_keywords: Explainable keywords that drove this prediction
        """
        cleaned = clean_legal_text(document_text)
        if not cleaned or len(cleaned) < 15:
            return "GENERIC_LEGAL_NOTICE", CATEGORY_DISPLAY_NAMES["GENERIC_LEGAL_NOTICE"], 0.5, []
            
        # 1. Statistical Prediction via TF-IDF + Logistic Regression
        probs = self.pipeline.predict_proba([cleaned])[0]
        classes = self.pipeline.classes_
        top_idx = int(np.argmax(probs))
        predicted_category = str(classes[top_idx])
        confidence = float(probs[top_idx])
        
        # 2. Extract Top Predictive Keywords for this document using TF-IDF weights
        tfidf_vec = self.vectorizer.transform([cleaned])
        nonzero_indices = tfidf_vec.nonzero()[1]
        tfidf_scores = tfidf_vec.data
        
        # Match with classifier coefficients for predicted class
        class_coef_idx = list(classes).index(predicted_category)
        coefs = self.classifier.coef_[class_coef_idx]
        
        # Importance = TF-IDF weight * classifier coefficient
        feature_importance = []
        for feat_idx, tfidf_val in zip(nonzero_indices, tfidf_scores):
            importance = tfidf_val * coefs[feat_idx]
            feature_importance.append((self.feature_names[feat_idx], importance))
            
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [item[0] for item in feature_importance[:5] if item[1] > 0]
        
        # Heuristic calibration for definitive Indian statutory markers
        if "138" in cleaned and ("cheque" in cleaned.lower() or "dishonour" in cleaned.lower()):
            predicted_category = "CHEQUE_BOUNCE_NOTICE"
            confidence = max(confidence, 0.95)
            if "section 138" not in top_keywords:
                top_keywords.insert(0, "section 138")
                
        display_name = CATEGORY_DISPLAY_NAMES.get(predicted_category, predicted_category)
        return predicted_category, display_name, round(confidence, 4), top_keywords[:5]

# Singleton instance
_classifier_instance = None

def get_legal_classifier() -> LegalDocumentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = LegalDocumentClassifier()
    return _classifier_instance
