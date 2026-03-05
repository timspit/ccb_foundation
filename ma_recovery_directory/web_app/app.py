"""
Main Flask application for Massachusetts Recovery Services Directory
"""

import math
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

sys.path.append(str(Path(__file__).parent.parent))

app = Flask(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "recovery_services.csv"


class RecoveryDirectoryApp:
    def __init__(self):
        self.df = None
        self.load_data()

    def load_data(self):
        """Load recovery services data from CSV."""
        if DATA_FILE.exists():
            self.df = pd.read_csv(DATA_FILE, dtype={"zip_code": str})
            self.df["zip_code"] = self.df["zip_code"].str.strip().str.zfill(5)
        else:
            columns = [
                "name", "address", "city", "state", "zip_code",
                "phone", "email", "website", "service_types",
                "hours", "populations_served", "languages",
                "eligibility", "payment_options", "data_source",
                "latitude", "longitude",
            ]
            self.df = pd.DataFrame(columns=columns)

    def search_services(self, filters: Dict) -> List[Dict]:
        """Search services based on filters."""
        filtered_df = self.df.copy()

        if filters.get("text"):
            text = filters["text"].lower()
            name_match = filtered_df["name"].str.lower().str.contains(text, na=False)
            city_match = filtered_df["city"].str.lower().str.contains(text, na=False)
            filtered_df = filtered_df[name_match | city_match]

        if filters.get("zip_code"):
            filtered_df = filtered_df[
                filtered_df["zip_code"].str.contains(filters["zip_code"], na=False)
            ]

        if filters.get("service_type"):
            filtered_df = filtered_df[
                filtered_df["service_types"].str.contains(
                    filters["service_type"], na=False, case=False
                )
            ]

        if filters.get("language"):
            filtered_df = filtered_df[
                filtered_df["languages"].str.contains(
                    filters["language"], na=False, case=False
                )
            ]

        if filters.get("population"):
            filtered_df = filtered_df[
                filtered_df["populations_served"].str.contains(
                    filters["population"], na=False, case=False
                )
            ]

        if filters.get("near_zip") and filters.get("max_miles"):
            filtered_df = self._filter_by_distance(
                filtered_df, filters["near_zip"], float(filters["max_miles"])
            )

        filtered_df = filtered_df.copy()
        filtered_df["id"] = filtered_df.index
        return filtered_df.to_dict("records")

    def _filter_by_distance(self, df, zip_code: str, max_miles: float):
        """Filter providers by distance from a ZIP code centroid."""
        try:
            import pgeocode

            nomi = pgeocode.Nominatim("us")
            result = nomi.query_postal_code(zip_code.zfill(5))
            if pd.isna(result.latitude):
                return df
            ref_lat, ref_lng = float(result.latitude), float(result.longitude)
        except Exception:
            return df

        if "latitude" not in df.columns or "longitude" not in df.columns:
            return df

        has_coords = df["latitude"].notna() & df["longitude"].notna()

        def haversine(lat2, lng2):
            R = 3958.8
            lat1r, lng1r = math.radians(ref_lat), math.radians(ref_lng)
            lat2r, lng2r = math.radians(lat2), math.radians(lng2)
            dlat, dlng = lat2r - lat1r, lng2r - lng1r
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlng / 2) ** 2
            return R * 2 * math.asin(math.sqrt(a))

        distances = df.loc[has_coords].apply(
            lambda row: haversine(row["latitude"], row["longitude"]), axis=1
        )
        in_range = distances[distances <= max_miles].index
        return df[df.index.isin(in_range)]

    def get_providers_geojson(self) -> Dict:
        """Return all geocoded providers as a GeoJSON FeatureCollection."""
        if "latitude" not in self.df.columns:
            return {"type": "FeatureCollection", "features": []}

        has_coords = self.df["latitude"].notna() & self.df["longitude"].notna()
        geo_df = self.df[has_coords].copy()
        geo_df["id"] = geo_df.index

        features = []
        for _, row in geo_df.iterrows():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": {
                    "id": int(row["id"]),
                    "name": row.get("name", "") or "",
                    "address": row.get("address", "") or "",
                    "city": row.get("city", "") or "",
                    "state": row.get("state", "") or "",
                    "zip_code": row.get("zip_code", "") or "",
                    "phone": row.get("phone", "") or "",
                    "service_types": row.get("service_types", "") or "",
                    "data_source": row.get("data_source", "") or "",
                },
            })

        return {"type": "FeatureCollection", "features": features}

    def get_provider(self, idx: int) -> Optional[Dict]:
        """Get a single provider by DataFrame index."""
        if idx not in self.df.index:
            return None
        result = self.df.loc[idx].to_dict()
        result["id"] = idx
        # Convert NaN floats to empty strings so templates can safely call .split() etc.
        for key, val in result.items():
            if isinstance(val, float) and pd.isna(val):
                result[key] = ""
        return result


directory_app = RecoveryDirectoryApp()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/map")
def map_view():
    return render_template("map.html")


@app.route("/provider/<int:idx>")
def provider_detail(idx):
    provider = directory_app.get_provider(idx)
    if provider is None:
        return render_template("404.html"), 404
    return render_template("provider.html", provider=provider)


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "Massachusetts Recovery Services Directory",
        "version": "2.0.0",
    }), 200


@app.route("/api/search", methods=["POST"])
def search():
    filters = request.json or {}
    results = directory_app.search_services(filters)
    return jsonify(results)


@app.route("/api/providers")
def providers_geojson():
    return jsonify(directory_app.get_providers_geojson())


@app.route("/api/export", methods=["POST"])
def export_results():
    filters = request.json or {}
    results = directory_app.search_services(filters)

    if not results:
        return jsonify({"error": "No results to export"}), 400

    temp_df = pd.DataFrame(results)
    skip_cols = {"id", "latitude", "longitude"}
    export_cols = [c for c in temp_df.columns if c not in skip_cols]
    temp_file = "/tmp/recovery_export.csv"
    temp_df[export_cols].to_csv(temp_file, index=False)

    return send_file(temp_file, as_attachment=True, download_name="recovery_services.csv")


@app.route("/api/stats")
def stats():
    df = directory_app.df
    geocoded = int(df["latitude"].notna().sum()) if "latitude" in df.columns else 0
    sources = (
        df["data_source"].value_counts().to_dict() if "data_source" in df.columns else {}
    )
    return jsonify({
        "total_services": len(df),
        "cities_covered": int(df["city"].nunique()),
        "geocoded": geocoded,
        "data_sources": sources,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
