import random
import bisect
from datetime import datetime
from os import listdir
from os.path import isfile, join

import pandas as pd
import shapefile
from shapely.geometry import Point, shape

from configuration import config
from data_preparation.TripTransformer import TripTransformer


class DC2017TripTransformer(TripTransformer):

    def __init__(self, taxi_trip_input_file_name: str, batch_id: int):
        self.taxi_trip_input_file_name = taxi_trip_input_file_name
        self.batch_id = batch_id
        self.weather_hourly_df = pd.read_csv(
            config.dc_wp_weather_output_file,
            parse_dates=['reported_date_time', 'start_date_time'],
            date_parser=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))
        cd_shapes = shapefile.Reader(config.di_cd_shapes_file)
        self.cd_raw_shapes = cd_shapes.shapes()
        self.cd_records = cd_shapes.records()
        super().__init__()

    def import_trips_from_csv(self):
        # Read in the original csv-file
        self.data_frame = pd.read_csv(
            self.taxi_trip_input_file_name,
            # skiprows=self.batch_id * self.batch_size, # Iterate through a whole file
            nrows=1000

        )
        # skiprows=self.get_random_sample_from_file(self.taxi_trip_input_file_name, self.batch_size),

        self.data_frame['StartDateTime'] = pd.to_datetime(self.data_frame['StartDateTime'],
                                                          format='%Y-%m-%d %H:%M:%S.%f %z')
        self.data_frame = self.data_frame.sort_values(by=['StartDateTime'])
        self.data_frame.update(self.data_frame[['OriginLatitude', 'OriginLongitude', 'DestinationLatitude',
                                                "DestinationLongitude"]].fillna(0))
        self.data_frame = self.data_frame.rename(columns={'OriginLatitude': 'pickup_latitude',
                                                          'OriginLongitude': 'pickup_longitude',
                                                          'DestinationLatitude': 'dropoff_latitude',
                                                          'DestinationLongitude': 'dropoff_longitude'})


        # I added this line
        # print(self.datetime.strptime("%Y-%m-%d %H:%M:%S").strptime("%Y-%m-%d %H:%M:%S")
        # print(self.data_frame.astype(str)
        print(self.data_frame['StartDateTime'].head)
        print(self.data_frame.dtypes)
        print(self.data_frame.columns)
        print(self.data_frame.head)

        # Sort data_frame
        self.data_frame.sort_values(by=['StartDateTime'], inplace=True)

    def add_basic_time_features(self):
        self.data_frame['year'] = self.data_frame['StartDateTime'].dt.year
        self.data_frame['month'] = self.data_frame['StartDateTime'].dt.month
        self.data_frame['week'] = self.data_frame['StartDateTime'].dt.isocalendar().week
        self.data_frame['weekday'] = self.data_frame['StartDateTime'].dt.weekday
        self.data_frame['hour'] = self.data_frame['StartDateTime'].dt.hour
        self.data_frame['minute'] = self.data_frame['StartDateTime'].dt.minute

    def add_time_bin_features(self):
        for time_bin_size in config.tt_time_bins:
            # Without weekday separation.
            self.data_frame['timeBin' + str(time_bin_size)] = self.data_frame.apply(
                lambda x: self.get_time_bin(x['hour'], x['minute'], time_bin_size), axis=1)
            # With weekday separation.
            self.data_frame['timeBinWWDS' + str(time_bin_size)] = self.data_frame.apply(
                lambda x: self.get_time_bin(x['hour'], x['minute'], time_bin_size), axis=1)

    def add_grid_indices(self):
        for grid_cell_height in config.dc_grid_cell_heights:
            self.create_index_for_grid('square', grid_cell_height)
            self.create_index_for_grid('triangle', grid_cell_height)
            self.create_index_for_grid('hexagon', grid_cell_height)

    def add_weather_features(self):
        weather_df_for_trips = self.data_frame.apply(
            lambda x: (
                self.weather_hourly_df.iloc[
                   self.get_weather_hourly_df_if_for_time(x['StartDateTime'].to_datetime64())].to_dict()
            ), axis=1)
        weather_df_for_trips = pd.json_normalize(weather_df_for_trips)
        weather_df_for_trips.drop(['reported_date_time', 'start_date_time'], inplace=True, axis=1)
        weather_df_for_trips = weather_df_for_trips.add_prefix('weather_hourly_')
        weather_df_for_trips.rename(columns={weather_df_for_trips.columns[0]: 'weather_hourly_id'}, inplace=True)
        self.data_frame = pd.concat([self.data_frame, weather_df_for_trips.reindex(self.data_frame.index)], axis=1)

    def get_weather_hourly_df_if_for_time(self, time: datetime):
        """Returns the row id for the given time in the weather hourly df."""
        weather_time_points = list(self.weather_hourly_df['start_date_time'])
        if time > weather_time_points[-1] + pd.offsets.Hour(1) or time < weather_time_points[0]:
            return None
        else:
            return bisect.bisect(weather_time_points, time) - 1

    def add_district_features(self):
        self.data_frame['communityDistrictStart'] = self.data_frame.apply(
            lambda x: self.get_community_district(
                x['pickup_latitude'], x['pickup_longitude']
            ), axis=1
        )

        self.data_frame['communityDistrictEnd'] = self.data_frame.apply(
            lambda x: self.get_community_district(
                x['dropoff_latitude'], x['dropoff_longitude']
            ), axis=1
        )

    def get_community_district(self, latitude: float, longitude: float) -> int:
        for curr_shape_id in range(len(self.cd_raw_shapes)):
            if Point(longitude, latitude).within(shape(self.cd_raw_shapes[curr_shape_id])):
                return curr_shape_id
        return 999999999  # Not in any shape.

    def add_distance_features(self):
        self.data_frame['haversineDistance'] = self.data_frame.apply(
            lambda x: self.get_haversine_distance(
                (x['pickup_latitude'], x['pickup_longitude']),
                (x['dropoff_latitude'], x['dropoff_longitude'])
            ), axis=1
        )

        self.data_frame['manhattanDistance'] = self.data_frame.apply(
            lambda x: self.get_manhattan_distance(
                (x['pickup_latitude'], x['pickup_longitude']),
                (x['dropoff_latitude'], x['dropoff_longitude'])
            ), axis=1

        )

    def identify_outliers(self):

        # District-based
        self.data_frame[config.tt_outlier_prefix + 'OriginCity'] = \
            self.data_frame['OriginCity'].apply(lambda x: True if x == 999999999 else False)
        self.data_frame[config.tt_outlier_prefix + 'DestinationCity'] = \
            self.data_frame['DestinationCity'].apply(lambda x: True if x == 999999999 else False)

        # Grid-based
        for grid_cell_height in config.dc_grid_cell_heights:
            for grid_type in ['S', 'T', 'H']:
                for index_dimension in ['X', 'Y']:
                    for location in ['PU', 'DO']:
                        index_name = location + grid_type + 'GC' + str(grid_cell_height) + 'Index' + index_dimension
                        self.data_frame[config.tt_outlier_prefix + index_name] = self.data_frame[index_name].apply(
                            lambda x: True if x == 999999999 else False)

        # Duration-based
        self.data_frame[config.tt_outlier_prefix + 'unreasonable_high_duration'] = \
            self.data_frame['Duration'].apply(
                lambda x: True if x > 10902 else False)
        self.data_frame[config.tt_outlier_prefix + 'zero_duration'] = self.data_frame['Duration'].apply(
            lambda x: True if x == 0 else False)
        self.data_frame[config.tt_outlier_prefix + 'very_low_duration'] = self.data_frame['Duration'].apply(
            lambda x: True if x < 30 else False)
        self.data_frame[config.tt_outlier_prefix + 'duration_is_much_higher_than_travelled_distance'] = \
            self.data_frame.apply(lambda x:
                                  True if (x['haversineDistance'] > 0 and x['haversineDistance'] / 11.4263 * 50 < x[
                                      'Duration'])
                                  else False, axis=1)
        self.data_frame[config.tt_outlier_prefix + 'very_low_duration_despite_large_distance'] = \
            self.data_frame.apply(lambda x:
                                  True if (x['Duration'] > 0 and (
                                              x['haversineDistance'] / 1000 / x['Duration'] / 60 * 60) > 112.654)
                                  else False, axis=1)
        self.data_frame[config.tt_outlier_prefix + 'very_low_duration_despite_large_haversine'] = \
            self.data_frame.apply(lambda x:
                                  True if (x['haversineDistance'] / 1000 / 11.4263 * 25 > x[
                                      'Duration'] / 60 * 60) else False, axis=1)

        # Distance-based
        self.data_frame[config.tt_outlier_prefix + 'distance'] = self.data_frame['haversineDistance'].apply(
            lambda x: True if x == 0 else False)

        # Passenger-based
        # self.data_frame[config.tt_outlier_prefix + 'passenger_count'] = self.data_frame['passenger_count'].apply(
        #     lambda x: True if (x > 7 or x == 0) else False)

    def export_to_csv(self):
        file_name = 'DCExport' + str(self.batch_id) + '_' + str(self.batch_size) + '.csv'

        # Separate inliers from outliers
        outlier_columns = list(self.data_frame.filter(regex=config.tt_outlier_prefix, axis=1).columns)
        outlier_df = self.data_frame[self.data_frame[outlier_columns].any(1)]
        inlier_df = self.data_frame[~self.data_frame[outlier_columns].any(1)]

        # Export both datasets
        outlier_df.to_csv(config.tt_export_directory + config.tt_outlier_prefix + file_name, sep=';')
        inlier_df.to_csv(config.tt_export_directory + 'inlier_df' + file_name, sep=';')


def main():
    """Transform multiple batches of trips randomly selected from files of the specified directory."""
    list_of_files = [f for f in listdir(config.tt_trip_directory) if isfile(join(config.tt_trip_directory, f))]
    for i in range(config.tt_number_of_batches):
        importer = DC2017TripTransformer(
            config.tt_trip_directory + '\\' + random.choice(list_of_files),
            i)
        importer.transform_trips()


if __name__ == '__main__':
    main()
