import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / "outputs"


def get_district_risk_profile():
    path = OUTPUT / "district_risk_profile.csv"
    return pd.read_csv(path)


def get_candidate_facilities(district=None):
    path = OUTPUT / "candidate_facilities.csv"
    df = pd.read_csv(path)

    if district:
        df = df[df["district"] == district]

    return df


def get_infrastructure_summary():
    path = OUTPUT / "infrastructure_summary.csv"
    return pd.read_csv(path)


def get_historical_hazard():
    path = OUTPUT / "historical_hazard_summary.csv"
    return pd.read_csv(path)


if __name__ == "__main__":
    print("DISTRICT RISK PROFILE")
    print(get_district_risk_profile().to_string(index=False))

    print("\nCANDIDATE FACILITIES")
    print(get_candidate_facilities().shape)

    print("\nINFRASTRUCTURE SUMMARY")
    print(get_infrastructure_summary().shape)

    print("\nHISTORICAL HAZARD")
    print(get_historical_hazard().shape)
