# Travel Time Predictor

This project contains code to create grids (different shapes and sizes), import existing taxi trip datasets into a graph 
database, enhance those datasets by additional features, and predict the estimated time of arrival (ETA). 

#### Folder structure
- `data` contains the data used and generated within this project.
    - `generated` contains the generated data.
    - `original` contains the original data. All data was downloaded from [here](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
- `data_preparation` contains source code to prepare data that can be used by models in `prediction`.
    - `DataTransformer.py` transforms a given Yellow Cab NYC Taxi dataset into one with grids.
- `documentation` contains presentations and files generated for documenting the research.
- `grid_creation` is used for creating grids.
    - `GridCreator.py` can be used to create a grid with square grid cells.
- `prediction` holds source code for models that estimate the time of arrival.
    - `models` stores generated models.
    - `runs` keeps data that can be visualized by [Tensorboard](https://www.tensorflow.org/tensorboard).

#### TODO
- Grid
    - [x] Square shape
    - [x] Hexagon shape
        - [x] Realize `visualize_grid` method
    - [x] Triangle shape
        - [x] (Julia) Corner points should be starting points for new triangles
        - [x] (Julia) Change triangle side length to height
    - [x] (Julia) Enhance existing methods for grid creation by wrapper that uses parameter `area` instead of `height`
        - Make use of a constructor that accepts `cell_area` and `cell_height`
    - [x] (Julia) Add types to functions/classes
    - [x] (Julia) Documentation to function/classes
    - [x] (Julia) Move main method for grid to test-files
    - [x] (Sören) Remove old code and move most recent code into directory `grid_creation`

- TripTransformer
    - Other datasets
        - Use also Green taxi data
    - NYC2016TripTransformer    
        - [x] Basic features (start/end coordinate, duration)
        - Additional features
            - [x] Time-related features
                - [x] Year, month, week, day, weekday, hour, minute
                - [x] Variants for time-bins (with and without weekday separation)
            - [x] Grid-based features
            - [ ] Weather-related data
                - [ ] ?Add a new wrapper around NYC2016TripTransformer to store data like weather-data
                - [x] Hourly
                - [ ] Daily
            - [x] District-based features
                - [x] Community districts
                    - [x] Minimize time for calculating by iterating through districts with descending occurrence  
                - [ ] Neighborhood Tabulation Areas
                    - [ ] Minimize time for calculating by iterating through districts with descending occurrence  
                - [ ] Taxi zones
                    - [ ] Minimize time for calculating by iterating through districts with descending occurrence
            - [x] Distance-based features
            - [ ] Holiday
            - [ ] Accident data (Safe Routes from Goodtechs might be a good starting point)
        - [x] Identification of outliers
            - [x] District-based
            - [x] Grid-based
            - [x] Duration-based
            - [x] Distance-based
            - [x] Passenger-based
        - General
            - [ ] Remove unnecessary columns at the end (especially the outlier columns in the non-outlier export)
            - [x] Separate outliers and inliers in export
        - [ ] TypeError: Cannot index by location index with a non-integer key - NYC2016TripTransformer - line 73
        - [ ] Use different file names of the generated code that simplifies the continuation after the process has stopped.
        - [ ] Weather is not correct. Check function and change it accordingly.

- Prediction    
    - [ ] Some numbers as categorical values instead of int?
        - Maybe test this for RF and check whether it makes a difference
    - [x] Reorganize jupyter-Notebooks
    - [ ] Make sure features are read in correct
        - [ ] District not as int, but as category
    - [ ] FCNN with two hidden layers     
        - [x] Is `optim.SGD` right for this model?
            - No, Adam seems to work better
        - [x] Calculate loss by hand and fix current error
            - Dividing by the batch size does not make sense
        - [x] Perform calculation on CUDA
        - [x] Fix visualization of weights (don't overwrite the previously existing every time)
        - [ ] Learning-rate schedule
        - [ ] UserWarning: Using a target size (torch.Size([1024, 1])) that is different to the input size (torch.Size([1024, 6])). This will likely lead to incorrect results due to broadcasting. Please ensure they have the same size.
        - [ ] Ceiling the maximum value for weights does technically not work so far - or at least the weights are not recorded anymore
    - Random Forest
        - [ ] Memory error with RandomizedSearchCV
            - [ ] Update sklearn
    - XGBoost
    - Other NN
    
- Evaluation
    - [x] Mean Squared Logarithmic Error like in https://www.kaggle.com/c/nyc-taxi-trip-duration/leaderboard
    - [ ] Integrate validation data set performance in the end
    - [ ] Integrate MARE & MAPE [Li+18]

- Project structure/organisation
    - [ ] Restructure `analysis` directory

#### Useful Resources
- Grid creation
    - [Geodesic Discrete Global Grid Systems](http://cs.sou.edu/~sahrk/dgg/pubs/gdggs03.pdf)
    - [Shapes on a plane: evaluating the impact of projection distortion on spatial binning](https://doi.org/10.1080/15230406.2016.1180263)
    
#### Helpful commands
- Run tensorboard: `tensorboard --logdir=runs`

#### Ideas 
- How to fit coordinates into NN?
    - Maybe use flat coordination system
    - GIS coordinate system (ArcPy)
    - Continuous to discrete coordination (fine-grid-based system)
    - Geohash could be used for building the grid-system

#### Miscellaneous
- Pytorch: `.clamp(min=0)` and `F.relu()` can be used interchangable. `torch.nn.ReLU` can only be used in `nn.Sequential` [see here](https://discuss.pytorch.org/t/why-are-there-3-relu-functions-or-maybe-even-more/5891).
- EPSG & CRS
    - `epsg:2263`: New York State Plane Long Island Zone is a local coordinate system
    - `espg:6539`: current
    - `espg:3857`: most accurate version
    - OSM uses WGS 84
    - Google uses Web Mercator
    
# How to use `from pyproj import Transformer`
- Don't use ´always_xy=True´.
- Transformer.from_crs('epsg:4326', 'epsg:3857') takes (lat (y), lon (x))

```trans_coord_to_meter = Transformer.from_crs('epsg:4326', 'epsg:3857')```

```bl_t = trans_coord_to_meter.transform(40.64423086189233, -74.0307935018417)```

- and returns (x, y).
- When using the transformer with `direction='INVERSE'`, (x, y) is inserted and
- (lat (y), lon (x)) is returned. 

```trans_coord_to_meter.transform(bl_t[0], bl_t[1], direction='INVERSE')```

- But, keep in mind that in between the two transformations the order is (x, y).
