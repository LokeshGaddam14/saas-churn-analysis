"""
============================================================
RaoDo Data Analyst Challenge — Customer Churn Analysis
MongoDB Aggregation Pipeline
Dataset: Telco Customer Churn (7,043 customers)
Author: Lokesh Gaddam | lokeshgaddam2514@gmail.com
============================================================

Setup:
    pip install pymongo pandas

    Each customer document in MongoDB looks like:
    {
        "customer_id": "7590-VHVEG",
        "gender": "Female",
        "senior_citizen": 0,
        "partner": "Yes",
        "dependents": "No",
        "tenure": 1,
        "phone_service": "No",
        "multiple_lines": "No phone service",
        "internet_service": "DSL",
        "online_security": "No",
        "online_backup": "Yes",
        "device_protection": "No",
        "tech_support": "No",
        "streaming_tv": "No",
        "streaming_movies": "No",
        "contract": "Month-to-month",
        "paperless_billing": "Yes",
        "payment_method": "Electronic check",
        "monthly_charges": 29.85,
        "total_charges": 29.85,
        "churn": 1
    }
"""

import pandas as pd
from pymongo import MongoClient

# ============================================================
# CONNECTION SETUP
# ============================================================

client = MongoClient("mongodb://localhost:27017/")
db = client["raodo_churn_db"]
collection = db["telco_churn"]


# ============================================================
# OPTIONAL: Load CSV into MongoDB (run once)
# ============================================================

def load_data_from_csv(csv_path: str):
    """Load the cleaned Telco churn CSV into MongoDB."""
    df = pd.read_csv(csv_path)
    df["churn"] = df["Churn"].map({"Yes": 1, "No": 0})
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    records = df.to_dict(orient="records")
    collection.drop()
    collection.insert_many(records)
    print(f"Inserted {len(records)} documents into MongoDB.")


# ============================================================
# PIPELINE 1: Overall Churn Rate
# ============================================================

def get_overall_churn_metrics():
    """Calculate overall churn rate and customer counts."""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_customers": {"$sum": 1},
                "churned_customers": {"$sum": "$churn"},
                "retained_customers": {"$sum": {"$subtract": [1, "$churn"]}},
                "avg_monthly_charges_churned": {
                    "$avg": {
                        "$cond": [{"$eq": ["$churn", 1]}, "$monthly_charges", None]
                    }
                },
                "avg_monthly_charges_retained": {
                    "$avg": {
                        "$cond": [{"$eq": ["$churn", 0]}, "$monthly_charges", None]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_customers": 1,
                "churned_customers": 1,
                "retained_customers": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned_customers", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges_churned": {"$round": ["$avg_monthly_charges_churned", 2]},
                "avg_monthly_charges_retained": {"$round": ["$avg_monthly_charges_retained", 2]}
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[1] Overall Churn Metrics:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 2: Revenue at Risk
# ============================================================

def get_revenue_at_risk():
    """Quantify monthly and annualized revenue lost to churn."""
    pipeline = [
        {
            "$match": {"churn": 1}
        },
        {
            "$group": {
                "_id": None,
                "churned_customers": {"$sum": 1},
                "monthly_revenue_lost": {"$sum": "$monthly_charges"},
                "total_charges_lost": {"$sum": "$total_charges"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "churned_customers": 1,
                "monthly_revenue_lost": {"$round": ["$monthly_revenue_lost", 2]},
                "annualized_revenue_at_risk": {
                    "$round": [{"$multiply": ["$monthly_revenue_lost", 12]}, 2]
                },
                "total_charges_lost": {"$round": ["$total_charges_lost", 2]}
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[2] Revenue at Risk:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 3: Churn by Contract Type
# ============================================================

def get_churn_by_contract():
    """Break down churn rate and revenue at risk by contract type."""
    pipeline = [
        {
            "$group": {
                "_id": "$contract",
                "total_customers": {"$sum": 1},
                "churned": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"},
                "monthly_revenue_at_risk": {
                    "$sum": {
                        "$cond": [{"$eq": ["$churn", 1]}, "$monthly_charges", 0]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "contract": "$_id",
                "total_customers": 1,
                "churned": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]},
                "annualized_revenue_at_risk": {
                    "$round": [{"$multiply": ["$monthly_revenue_at_risk", 12]}, 2]
                }
            }
        },
        {"$sort": {"churn_rate_pct": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[3] Churn by Contract Type:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 4: Churn by Tenure Segment (Cohort Analysis)
# ============================================================

def get_churn_by_tenure_segment():
    """Segment customers by tenure bands and calculate churn per cohort."""
    pipeline = [
        {
            "$addFields": {
                "tenure_segment": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$tenure", 12]}, "then": "0-12 months (New)"},
                            {"case": {"$lte": ["$tenure", 24]}, "then": "13-24 months (Developing)"},
                            {"case": {"$lte": ["$tenure", 48]}, "then": "25-48 months (Established)"},
                            {"case": {"$lte": ["$tenure", 72]}, "then": "49-72 months (Loyal)"}
                        ],
                        "default": "72+ months (Champion)"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$tenure_segment",
                "total_customers": {"$sum": 1},
                "churned": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"},
                "min_tenure": {"$min": "$tenure"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "tenure_segment": "$_id",
                "total_customers": 1,
                "churned": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]},
                "min_tenure": 1
            }
        },
        {"$sort": {"min_tenure": 1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[4] Churn by Tenure Segment (Cohort):")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 5: Churn by Internet Service
# ============================================================

def get_churn_by_internet_service():
    """Analyze churn rate per internet service type."""
    pipeline = [
        {
            "$group": {
                "_id": "$internet_service",
                "total_customers": {"$sum": 1},
                "churned": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "internet_service": "$_id",
                "total_customers": 1,
                "churned": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]}
            }
        },
        {"$sort": {"churn_rate_pct": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[5] Churn by Internet Service:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 6: Churn by Payment Method
# ============================================================

def get_churn_by_payment_method():
    """Identify churn rate by payment method (electronic check is highest risk)."""
    pipeline = [
        {
            "$group": {
                "_id": "$payment_method",
                "total_customers": {"$sum": 1},
                "churned": {"$sum": "$churn"},
                "monthly_revenue_at_risk": {
                    "$sum": {
                        "$cond": [{"$eq": ["$churn", 1]}, "$monthly_charges", 0]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "payment_method": "$_id",
                "total_customers": 1,
                "churned": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "annualized_revenue_at_risk": {
                    "$round": [{"$multiply": ["$monthly_revenue_at_risk", 12]}, 2]
                }
            }
        },
        {"$sort": {"churn_rate_pct": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[6] Churn by Payment Method:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 7: High-Risk Customer Segment Identification
# ============================================================

def get_high_risk_segment():
    """
    High-risk = Month-to-month contract + Fiber optic + Electronic check
    This is the 282-customer segment responsible for $1.67M revenue at risk.
    """
    pipeline = [
        {
            "$match": {
                "contract": "Month-to-month",
                "internet_service": "Fiber optic",
                "payment_method": "Electronic check"
            }
        },
        {
            "$group": {
                "_id": None,
                "segment_size": {"$sum": 1},
                "churned_count": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"},
                "total_monthly_revenue": {"$sum": "$monthly_charges"},
                "at_risk_monthly_revenue": {
                    "$sum": {
                        "$cond": [{"$eq": ["$churn", 1]}, "$monthly_charges", 0]
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "segment": "Month-to-month + Fiber optic + Electronic check",
                "segment_size": 1,
                "churned_count": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned_count", "$segment_size"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]},
                "annualized_revenue_at_risk": {
                    "$round": [{"$multiply": ["$at_risk_monthly_revenue", 12]}, 2]
                }
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[7] High-Risk Segment (282 customers, $1.67M at risk):")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 8: Senior Citizen Churn Analysis
# ============================================================

def get_churn_by_senior_status():
    """Compare churn rates between senior and non-senior citizens."""
    pipeline = [
        {
            "$group": {
                "_id": "$senior_citizen",
                "total_customers": {"$sum": 1},
                "churned": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "segment": {
                    "$cond": [{"$eq": ["$_id", 1]}, "Senior Citizen", "Non-Senior"]
                },
                "total_customers": 1,
                "churned": 1,
                "churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$churned", "$total_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]}
            }
        },
        {"$sort": {"churn_rate_pct": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[8] Churn by Senior Citizen Status:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 9: Cross-Segment Revenue at Risk Matrix
# ============================================================

def get_revenue_risk_matrix():
    """Contract type × Internet service cross-segment revenue risk."""
    pipeline = [
        {
            "$match": {"churn": 1}
        },
        {
            "$group": {
                "_id": {
                    "contract": "$contract",
                    "internet_service": "$internet_service"
                },
                "churned_customers": {"$sum": 1},
                "monthly_revenue_lost": {"$sum": "$monthly_charges"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "contract": "$_id.contract",
                "internet_service": "$_id.internet_service",
                "churned_customers": 1,
                "monthly_revenue_lost": {"$round": ["$monthly_revenue_lost", 2]},
                "annualized_revenue_at_risk": {
                    "$round": [{"$multiply": ["$monthly_revenue_lost", 12]}, 2]
                }
            }
        },
        {"$sort": {"annualized_revenue_at_risk": -1}}
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[9] Revenue at Risk Matrix (Contract × Internet Service):")
    for doc in result:
        print(doc)
    return result


# ============================================================
# PIPELINE 10: Retention Opportunity — Auto-Pay Conversion Impact
# ============================================================

def get_autopay_conversion_impact():
    """
    Model revenue saved if electronic check customers switched to auto-pay.
    Electronic check churn rate: ~45% | Auto-pay churn rate: ~15%
    """
    pipeline = [
        {
            "$match": {"payment_method": "Electronic check"}
        },
        {
            "$group": {
                "_id": None,
                "total_electronic_check_customers": {"$sum": 1},
                "currently_churned": {"$sum": "$churn"},
                "avg_monthly_charges": {"$avg": "$monthly_charges"},
                "total_monthly_charges": {"$sum": "$monthly_charges"}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_electronic_check_customers": 1,
                "currently_churned": 1,
                "current_churn_rate_pct": {
                    "$round": [
                        {"$multiply": [
                            {"$divide": ["$currently_churned", "$total_electronic_check_customers"]},
                            100
                        ]},
                        2
                    ]
                },
                "avg_monthly_charges": {"$round": ["$avg_monthly_charges", 2]},
                "expected_churn_at_current_rate": {
                    "$round": [
                        {"$multiply": ["$total_electronic_check_customers", 0.45]},
                        0
                    ]
                },
                "expected_churn_if_autopay": {
                    "$round": [
                        {"$multiply": ["$total_electronic_check_customers", 0.15]},
                        0
                    ]
                },
                "monthly_revenue_saved_by_conversion": {
                    "$round": [
                        {"$multiply": [
                            {"$subtract": [
                                {"$multiply": ["$total_electronic_check_customers", 0.45]},
                                {"$multiply": ["$total_electronic_check_customers", 0.15]}
                            ]},
                            "$avg_monthly_charges"
                        ]},
                        2
                    ]
                }
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    print("\n[10] Auto-Pay Conversion Retention Impact:")
    for doc in result:
        print(doc)
    return result


# ============================================================
# RUN ALL PIPELINES
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("RaoDo Take-Home Challenge — MongoDB Churn Analysis")
    print("Author: Lokesh Gaddam | lokeshgaddam2514@gmail.com")
    print("=" * 60)

    # Uncomment to load data from CSV on first run:
    # load_data_from_csv("data/telco_churn_cleaned.csv")

    get_overall_churn_metrics()
    get_revenue_at_risk()
    get_churn_by_contract()
    get_churn_by_tenure_segment()
    get_churn_by_internet_service()
    get_churn_by_payment_method()
    get_high_risk_segment()
    get_churn_by_senior_status()
    get_revenue_risk_matrix()
    get_autopay_conversion_impact()

    print("\n✅ All 10 MongoDB aggregation pipelines completed.")
    client.close()
