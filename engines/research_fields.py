"""
engines/research_fields.py — Research Field Opportunity Engine
Scores research fields by global funding volume, growth, and policy priority.
"""

RESEARCH_FIELDS = {
    "Artificial Intelligence": {
        "estimated_funding": "$18.5B",
        "growth_trend": "Rapidly Growing",
        "policy_priority": "Critical",
        "avg_grant_size": "$850K",
        "opportunity_score": 9.5,
        "keywords": [
            "machine learning", "deep learning", "neural network", "artificial intelligence",
            "nlp", "natural language processing", "computer vision", "large language model",
            "generative ai", "reinforcement learning", "ai ethics", "explainable ai",
        ],
    },
    "Digital Health": {
        "estimated_funding": "$14.2B",
        "growth_trend": "Rapidly Growing",
        "policy_priority": "Critical",
        "avg_grant_size": "$920K",
        "opportunity_score": 9.3,
        "keywords": [
            "digital health", "health informatics", "telemedicine", "electronic health",
            "wearable", "medical ai", "clinical decision", "patient data", "health technology",
            "precision medicine", "genomics", "bioinformatics",
        ],
    },
    "Climate Science": {
        "estimated_funding": "$12.1B",
        "growth_trend": "Rapidly Growing",
        "policy_priority": "Critical",
        "avg_grant_size": "$620K",
        "opportunity_score": 9.2,
        "keywords": [
            "climate change", "carbon", "emissions", "greenhouse gas", "climate model",
            "global warming", "climate adaptation", "net zero", "decarbonization",
            "climate risk", "sea level", "arctic", "permafrost",
        ],
    },
    "Public Health": {
        "estimated_funding": "$22.3B",
        "growth_trend": "Stable Growth",
        "policy_priority": "Critical",
        "avg_grant_size": "$780K",
        "opportunity_score": 9.0,
        "keywords": [
            "epidemiology", "public health", "pandemic", "infectious disease", "vaccination",
            "global health", "health equity", "mental health", "nutrition", "maternal health",
            "child health", "neglected tropical disease",
        ],
    },
    "Energy Transition": {
        "estimated_funding": "$10.8B",
        "growth_trend": "Rapidly Growing",
        "policy_priority": "High",
        "avg_grant_size": "$540K",
        "opportunity_score": 8.8,
        "keywords": [
            "renewable energy", "solar energy", "wind energy", "battery storage", "hydrogen",
            "energy transition", "grid", "photovoltaic", "energy storage", "fuel cell",
            "smart grid", "energy efficiency",
        ],
    },
    "Biotechnology": {
        "estimated_funding": "$16.4B",
        "growth_trend": "Rapidly Growing",
        "policy_priority": "Critical",
        "avg_grant_size": "$1.1M",
        "opportunity_score": 8.7,
        "keywords": [
            "biotechnology", "crispr", "gene editing", "synthetic biology", "protein",
            "genomics", "proteomics", "metabolomics", "cell therapy", "drug discovery",
            "vaccine development", "molecular biology",
        ],
    },
    "Environmental Sustainability": {
        "estimated_funding": "$9.6B",
        "growth_trend": "Growing",
        "policy_priority": "High",
        "avg_grant_size": "$480K",
        "opportunity_score": 8.5,
        "keywords": [
            "sustainability", "biodiversity", "ecosystem", "conservation", "water",
            "deforestation", "ocean", "soil", "circular economy", "waste management",
            "environmental policy", "green infrastructure",
        ],
    },
    "Agriculture and Food Systems": {
        "estimated_funding": "$8.3B",
        "growth_trend": "Growing",
        "policy_priority": "High",
        "avg_grant_size": "$420K",
        "opportunity_score": 8.2,
        "keywords": [
            "agriculture", "food security", "crop", "soil health", "irrigation",
            "precision agriculture", "food systems", "livestock", "aquaculture",
            "plant science", "agronomy", "food supply",
        ],
    },
    "Cybersecurity": {
        "estimated_funding": "$7.4B",
        "growth_trend": "Growing",
        "policy_priority": "High",
        "avg_grant_size": "$380K",
        "opportunity_score": 7.9,
        "keywords": [
            "cybersecurity", "network security", "cryptography", "privacy", "data security",
            "threat detection", "malware", "intrusion detection", "zero trust", "blockchain",
        ],
    },
    "Education Technology": {
        "estimated_funding": "$5.2B",
        "growth_trend": "Growing",
        "policy_priority": "Medium",
        "avg_grant_size": "$280K",
        "opportunity_score": 7.1,
        "keywords": [
            "education technology", "e-learning", "learning analytics", "adaptive learning",
            "educational ai", "stem education", "higher education", "pedagogy",
        ],
    },
}


def get_field_opportunity(keywords: list, field: str = "", description: str = "") -> dict:
    """
    Match a researcher's keywords to funded research fields.
    Returns the best matching field with its opportunity data.
    """
    text = " ".join(keywords + [field, description]).lower()
    best_score = 5.0
    best_field = "General Research"
    best_data = {
        "estimated_funding": "N/A",
        "growth_trend": "Stable",
        "policy_priority": "Medium",
        "avg_grant_size": "N/A",
        "opportunity_score": 5.0,
    }

    for field_name, data in RESEARCH_FIELDS.items():
        for kw in data["keywords"]:
            if kw in text:
                if data["opportunity_score"] > best_score:
                    best_score = data["opportunity_score"]
                    best_field = field_name
                    best_data = data
                break

    return {"field": best_field, **best_data}


def get_all_fields() -> list[dict]:
    """Return all research fields sorted by opportunity score."""
    return sorted(
        [{"field": k, **v} for k, v in RESEARCH_FIELDS.items()],
        key=lambda x: x["opportunity_score"],
        reverse=True,
    )
