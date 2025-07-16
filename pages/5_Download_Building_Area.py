import streamlit as st
import requests
import json
import tempfile
import osm2geojson


def search_buildings(area_name):
    """
    Search buildings by name in a given area using Overpass API.
    """
    query = f"""
    [out:json][timeout:60];
    area["name"="{area_name}"]->.searchArea;
    (
      way["building"](area.searchArea);
      relation["building"](area.searchArea);
    );
    out tags center;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API.")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        return []

    results = []
    for el in data['elements']:
        tags = el.get("tags", {})
        name = tags.get("name")
        btype = tags.get("building")
        if name:
            results.append({
                "name": name,
                "type": btype or "unknown",
                "lat": el.get("lat") or el.get("center", {}).get("lat"),
                "lon": el.get("lon") or el.get("center", {}).get("lon")
            })
    return results


def download_building_geojson(area_name, save_as='buildings.geojson'):
    """
    Downloads building polygons from OpenStreetMap for a given area using Overpass API.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    area["name"="{area_name}"]->.searchArea;
    (
      way["building"](area.searchArea);
      relation["building"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API.")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        raise ValueError(f"No building data found for '{area_name}'.")

    geojson = osm2geojson.json2geojson(data)

    # Filter only Polygon/MultiPolygon features
    features = [
        feat for feat in geojson['features']
        if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']
    ]

    if not features:
        raise ValueError(f"No polygon building features found for '{area_name}'.")

    geojson_filtered = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_filtered, f, ensure_ascii=False, indent=2)

    return geojson_filtered, save_as
