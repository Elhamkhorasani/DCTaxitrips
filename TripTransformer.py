import random
from abc import ABC, abstractmethod

import pandas as pd
from haversine import haversine, Unit

from configuration import config
from grid_creation.PseudoGridCreator import PseudoSquareGrid, PseudoTriangleGrid, PseudoHexagonGrid


class TripTransformer(ABC):

    def __init__(self):
        self.batch_size = config.tt_batch_size
        self.data_frame = pd.DataFrame()

    def transform_trips(self):
        """All transformations are combined in this method."""
        self.import_trips_from_csv()
        self.add_basic_time_features()
        self.add_time_bin_features()
        self.add_grid_indices()
        self.add_weather_features()
        self.add_district_features()
        self.add_distance_features()
        self.identify_outliers()
        self.export_to_csv()
        print(self.data_frame.tail())

    @abstractmethod
    def import_trips_from_csv(self):
        """Import trips from a csv-file."""
        pass

    @abstractmethod
    def add_basic_time_features(self):
        """Add the basic time features year, month, week, weekday, hour, and minute."""
        pass

    @abstractmethod
    def add_time_bin_features(self):
        """Add time-bin features, that separate one day into time bins. We include both (with weekday separation and
        without weekday separation. """
        pass

    @abstractmethod
    def add_grid_indices(self):
        """Add the grid indices for start and end point of a trip."""
        pass

    @abstractmethod
    def add_weather_features(self):
        """Add weather-related features like precipitation or temperature."""
        pass

    @abstractmethod
    def add_district_features(self):
        """Add district-based features like community district or neighborhood tabulation area."""
        pass

    @abstractmethod
    def add_distance_features(self):
        """Add distance-based features like Haversine or Manhattan distance."""
        pass

    @abstractmethod
    def identify_outliers(self):
        """Identify trips that lie not in the covered area, have an unreasonable duration/distance etc."""
        pass

    @abstractmethod
    def export_to_csv(self):
        """Export the trips to two csv-files. Separate between inlier and outlier dataset."""
        pass

    @staticmethod
    def get_time_bin(hour: int, minute: int, bin_size: int):
        """Get time without weekday separation."""
        minute_of_day = hour * 60 + minute
        return minute_of_day // bin_size

    @staticmethod
    def get_time_bin_with_wds(hour: int, minute: int, weekday: int, bin_size: int):
        """Get time bin with weekday separation (wds)."""
        minute_of_day = hour * 60 + minute
        if weekday <= 5:
            return minute_of_day // bin_size
        else:
            number_of_bins_per_day = 24 * 60 // bin_size
            return number_of_bins_per_day + minute_of_day // bin_size

    def create_index_for_grid(self, grid_type: str, grid_cell_height: int):
        grid_name = grid_type[0].capitalize() + 'GC' + str(grid_cell_height) + 'Index'
        if grid_type == 'square':
            grid = PseudoSquareGrid(
                grid_cell_height,
                None,  # Volume is None, so the grid_cell_height is used to create the grid.
                config.dc_grid_bl_lat, config.dc_grid_bl_lon,
                config.dc_grid_tr_lat, config.dc_grid_tr_lon
            )
        elif grid_type == 'triangle':
            grid = PseudoTriangleGrid(
                grid_cell_height,
                None,  # Volume is None, so the grid_cell_height is used to create the grid.
                config.dc_grid_bl_lat, config.dc_grid_bl_lon,
                config.dc_grid_tr_lat, config.dc_grid_tr_lon
            )
        elif grid_type == 'hexagon':
            grid = PseudoHexagonGrid(
                grid_cell_height,
                None,  # Volume is None, so the grid_cell_height is used to create the grid.
                config.dc_grid_bl_lat, config.dc_grid_bl_lon,
                config.dc_grid_tr_lat, config.dc_grid_tr_lon
            )
        else:
            print('No valid grid type was passed. No grid is created.')
            return None
        self.data_frame['PU' + grid_name + 'X'] = self.data_frame.apply(
            lambda x: grid.get_index(x['pickup_latitude'], x['pickup_longitude'])[0], axis=1)
        self.data_frame['PU' + grid_name + 'Y'] = self.data_frame.apply(
            lambda x: grid.get_index(x['pickup_latitude'], x['pickup_longitude'])[1], axis=1)
        self.data_frame['DO' + grid_name + 'X'] = self.data_frame.apply(
            lambda x: grid.get_index(x['dropoff_latitude'], x['dropoff_longitude'])[0], axis=1)
        self.data_frame['DO' + grid_name + 'Y'] = self.data_frame.apply(
            lambda x: grid.get_index(x['dropoff_latitude'], x['dropoff_longitude'])[1], axis=1)

    @staticmethod
    def get_haversine_distance(point_1, point_2):
        """Get the Haversine distance of two points. Each point consists of a (latitude, longitude) pair."""
        return int(round(haversine(point_1, point_2, unit=Unit.METERS), 0))

    @staticmethod
    def get_manhattan_distance(point_1, point_2):
        """Get the Manhattan distance of two points. Each point consists of a (latitude, longitude) pair. The distance
        is calculated by adding the Haversine distance in both dimensions."""
        return int(round(haversine(point_1, (point_2[0], point_1[1]), unit=Unit.METERS), 0)) + \
               int(round(haversine((point_2[0], point_1[1]), point_2, unit=Unit.METERS), 0))

    @staticmethod
    def get_random_sample_from_file(file_name: str, sample_size: int = 1000):
        """Based on: https://stackoverflow.com/a/22259008/2908475. This solution is relatively slow."""
        input_file = open(file_name)
        number_of_records_in_file = sum(1 for line in input_file)
        input_file.close()
        return sorted(random.sample(range(1, number_of_records_in_file+1), number_of_records_in_file - sample_size))