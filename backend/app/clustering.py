import numpy as np
from sklearn.cluster import DBSCAN
import h3

EARTH_M = 6371000.0

def _to_radians(points):
    arr = np.radians(np.array([[p[0], p[1]] for p in points]))
    return arr

def dbscan_haversine(points, eps_m=500, min_samples=5):
    X = _to_radians(points)
    eps = eps_m / EARTH_M
    db = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
    labels = db.fit_predict(X)
    return labels

def h3_bin(points, res=7):
    bins = {}
    for lat, lon in points:
        idx = h3.geo_to_h3(lat, lon, res)
        bins[idx] = bins.get(idx, 0) + 1
    return bins
