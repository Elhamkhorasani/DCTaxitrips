
import pandas as pd
import shapefile
from shapely.geometry import Point, shape

import geopandas as gpd
gdf = gpd.read_file('C:/Users/elham/Desktop/travel-time-prediction-2/data/original/Neighborhood_Cluster-shp')
print (gdf)