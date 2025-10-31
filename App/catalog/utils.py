# App/catalog/utils.py
from math import radians, sin, cos, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Distancia en km entre dos coordenadas en grados decimales.
    """
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2.0)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2.0)**2
    c = 2 * asin(sqrt(a))
    return R * c

