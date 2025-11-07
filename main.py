from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Body
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
import io
import unicodedata
import country_converter as coco
from rapidfuzz import process, fuzz
from starlette.requests import Request
import json

app = FastAPI()
cc = coco.CountryConverter()

ISO3_TO_COUNTRY = {
    "DZA": "Algeria", "AGO": "Angola", "BEN": "Benin", "BWA": "Botswana", "BFA": "Burkina Faso", "BDI": "Burundi",
    "CMR": "Cameroon", "CPV": "Cape Verde", "CAF": "Central African Republic", "TCD": "Chad", "COM": "Comoros",
    "COG": "Congo", "DJI": "Djibouti", "EGY": "Egypt", "GNQ": "Equatorial Guinea", "ERI": "Eritrea", "SWZ": "Eswatini",
    "ETH": "Ethiopia", "GAB": "Gabon", "GMB": "Gambia", "GHA": "Ghana", "GIN": "Guinea", "GNB": "Guinea-Bissau",
    "CIV": "Ivory Coast", "KEN": "Kenya", "LSO": "Lesotho", "LBR": "Liberia", "LBY": "Libya", "MDG": "Madagascar",
    "MWI": "Malawi", "MLI": "Mali", "MRT": "Mauritania", "MUS": "Mauritius", "MAR": "Morocco", "MOZ": "Mozambique",
    "NAM": "Namibia", "NER": "Niger", "NGA": "Nigeria", "RWA": "Rwanda", "STP": "Sao Tome and Principe", "SEN": "Senegal",
    "SYC": "Seychelles", "SLE": "Sierra Leone", "SOM": "Somalia", "ZAF": "South Africa", "SSD": "South Sudan",
    "SDN": "Sudan", "TZA": "Tanzania", "TGO": "Togo", "TUN": "Tunisia", "UGA": "Uganda", "ZMB": "Zambia",
    "ZWE": "Zimbabwe", "COD": "Democratic Congo"
}

def clean_country_name(name: str):
    if not name or not isinstance(name, str):
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower().strip()
    return name

def match_country_name(name: str):
    if not name or not isinstance(name, str):
        return (None,None)
    cleaned_name = clean_country_name(name)
    iso3_code = cc.convert(names=cleaned_name, to='ISO3', not_found=None)
    if iso3_code and iso3_code in ISO3_TO_COUNTRY:
        return iso3_code, ISO3_TO_COUNTRY[iso3_code]
    return (None,None)

def read_dataframe(file: UploadFile) -> pd.DataFrame:
    file_bytes = file.file.read()
    if file.filename.endswith(".csv"):
        try:
            content = file_bytes.decode('utf-8')
            return pd.read_csv(io.StringIO(content))
        except UnicodeDecodeError:
            content = file_bytes.decode('latin1')
            return pd.read_csv(io.StringIO(content))
    elif file.filename.endswith((".xls", ".xlsx")):
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

@app.post("/detect-columns")
async def detect_columns(file: UploadFile = File(...)):
    df = read_dataframe(file)
    columns = df.columns.tolist()

    # Score columns by similarity to "country"
    scored_cols = []
    for col in columns:
        score = fuzz.token_sort_ratio(col.lower(), "country")
        scored_cols.append((col, score))

    # Sort descending by score (most likely country columns first)
    scored_cols.sort(key=lambda x: x[1], reverse=True)

    # Extract only the ordered column names
    country_columns = [col for col, score in scored_cols]

    # Detect numeric indicator columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    indicator_cols = [col for col in numeric_cols if all(
        k not in col.lower() for k in ["id", "year", "rank"])]


    return {
        "countryColumns": country_columns,
        "indicatorColumns": indicator_cols
    }


##### step 2 #####

class IndicatorColumn(BaseModel):
    columnName: str
    indicatorId: str
    normalizationType: str | None = None

class ProcessConfirmedRequest(BaseModel):
    countryColumn: str
    indicatorColumns: List[IndicatorColumn]

def minmax_normalize(series, reference=None):
    ref = reference if reference is not None else series
    min_val = ref.min()
    max_val = ref.max()
    if max_val == min_val:
        return pd.Series([100]*len(series), index=series.index)
    return ((series - min_val) / (max_val - min_val) * 100).round(2).clip(0, 100)


def zscore_normalize(series, reference=None):
    ref = reference if reference is not None else series
    mean = ref.mean()
    std = ref.std()
    if std == 0:
        return pd.Series([100]*len(series), index=series.index)
    z_scores = (series - mean) / std
    z_min, z_max = -3, 3
    return ((z_scores - z_min) / (z_max - z_min) * 100).round(2).clip(0, 100)


def robust_normalize(series, reference=None):
    ref = reference if reference is not None else series
    median = ref.median()
    q1 = ref.quantile(0.25)
    q3 = ref.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return pd.Series([100]*len(series), index=series.index)
    scaled = (series - median) / iqr
    scaled = scaled.clip(-2, 2)
    return ((scaled - scaled.min()) / (scaled.max() - scaled.min()) * 100).round(2)


def quantile_transform(series, reference=None):
    ref = reference if reference is not None else series
    return series.apply(lambda x: (ref <= x).mean() * 100).round(2)

def apply_normalization_with_full_reference(african_scores, full_scores, normalization_type):
    if not normalization_type:
        return african_scores.round(2)
    
    nt = normalization_type.lower()
    if nt == "minmax normalisation":
        return minmax_normalize(african_scores, reference=full_scores)
    elif nt == "z-score normalisation":
        return zscore_normalize(african_scores, reference=full_scores)
    elif nt == "robust scaling":
        return robust_normalize(african_scores, reference=full_scores)
    elif nt == "quantile transformation":
        return quantile_transform(african_scores, reference=full_scores)
    else:
        return minmax_normalize(african_scores, reference=full_scores)


@app.post("/process-confirmed")
async def process_confirmed(
    file: UploadFile = File(...),
    columns: str = Form(...)
):
    try:
        parsed_json = json.loads(columns)
        data = ProcessConfirmedRequest(**parsed_json)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid columns JSON: {str(e)}")

    try:
        # Read the full dataset (all countries) first
        full_df = read_dataframe(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    country_col = data.countryColumn
    indicators = data.indicatorColumns

    if country_col not in full_df.columns:
        raise HTTPException(status_code=400, detail=f"Country column '{country_col}' not found in file.")

    # Filter for African countries only
    full_df = full_df.dropna(subset=[country_col])
    country_matches = full_df[country_col].apply(match_country_name)
    full_df[["iso3", "matched_country"]] = pd.DataFrame(country_matches.tolist(), index=full_df.index)
    african_df = full_df.dropna(subset=["iso3", "matched_country"]).copy()

    results = []

    for indicator in indicators:
        col = indicator.columnName
        norm_type = indicator.normalizationType

        if col not in full_df.columns:
            continue

        # Convert columns to numeric (both full and African datasets)
        full_df[col] = pd.to_numeric(full_df[col], errors="coerce")
        african_df[col] = pd.to_numeric(african_df[col], errors="coerce")
        
        # Get African countries with valid scores
        valid_african_scores = african_df.dropna(subset=[col])[col]
        
        # Get normalization reference from ALL countries
        full_scores = full_df[col].dropna()

        if len(valid_african_scores) == 0:
            continue  # Skip if no valid African scores

        # Apply normalization using full dataset statistics
        normalized_scores = apply_normalization_with_full_reference(
            african_scores=valid_african_scores,
            full_scores=full_scores,
            normalization_type=norm_type
        )

        # Build results
        for idx, score in normalized_scores.items():
            row = african_df.loc[idx]
            results.append({
                "countryName": row["matched_country"],
                "countryCode": row["iso3"],
                "indicatorId": indicator.indicatorId,
                "score": float(score)
            })
    return results