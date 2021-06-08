import unittest
from datetime import datetime

from haversine import haversine, Unit

from configuration import config
from data_preparation.DC2017TripTransformer import DC2017TripTransformer
from data_preparation.NYC2016TripTransformer import NYC2016TripTransformer
from data_preparation.TripTransformer import TripTransformer


class TripImporterTest(unittest.TestCase):

    def test_get_time_bin(self):
        self.assertEqual(0, TripTransformer.get_time_bin(0, 0, 10))
        self.assertEqual(1, TripTransformer.get_time_bin(0, 10, 10))
        self.assertEqual(65, TripTransformer.get_time_bin(10, 52, 10))
        self.assertEqual(65, TripTransformer.get_time_bin(5, 29, 5))
        self.assertEqual(47, TripTransformer.get_time_bin(23, 59, 30))
        self.assertEqual(143, TripTransformer.get_time_bin(23, 59, 10))

    def test_get_time_bin_with_wds(self):
        self.assertEqual(0, TripTransformer.get_time_bin_with_wds(0, 0, 0, 10))
        self.assertEqual(144, TripTransformer.get_time_bin_with_wds(0, 0, 6, 10))
        self.assertEqual(1, TripTransformer.get_time_bin_with_wds(0, 10, 1, 10))
        self.assertEqual(145, TripTransformer.get_time_bin_with_wds(0, 10, 7, 10))
        self.assertEqual(65, TripTransformer.get_time_bin_with_wds(10, 52, 2, 10))
        self.assertEqual(209, TripTransformer.get_time_bin_with_wds(10, 52, 6, 10))
        self.assertEqual(65, TripTransformer.get_time_bin_with_wds(5, 29, 3, 5))
        self.assertEqual(353, TripTransformer.get_time_bin_with_wds(5, 29, 7, 5))
        self.assertEqual(47, TripTransformer.get_time_bin_with_wds(23, 59, 4, 30))
        self.assertEqual(95, TripTransformer.get_time_bin_with_wds(23, 59, 6, 30))
        self.assertEqual(143, TripTransformer.get_time_bin_with_wds(23, 59, 5, 10))
        self.assertEqual(287, TripTransformer.get_time_bin_with_wds(23, 59, 7, 10))


class DC2017TripTransformerTest(unittest.TestCase):

    def test_import_trips(self):
        importer = DC2017TripTransformer(
            config.tt_trips_dc,
            0)
        importer.transform_trips()


class NYC2016TripImporterTest(unittest.TestCase):

    def test_import_trips(self):
        importer = NYC2016TripTransformer(
            config.tt_trips_nyc_2016_02,
            0)
        importer.transform_trips()

    def test_get_weather_hourly_for_a_trip(self):
        importer = NYC2016TripTransformer(
            config.tt_trips_nyc_2016_02,
            0)
        date_time_1 = datetime.strptime('2016-02-19 20:51:23', '%Y-%m-%d %H:%M:%S')
        self.assertEqual(452, importer.get_weather_hourly_df_if_for_time(date_time_1))
        date_time_2 = datetime.strptime('2016-02-01 00:51:00', '%Y-%m-%d %H:%M:%S')  # 1
        self.assertEqual(1, importer.get_weather_hourly_df_if_for_time(date_time_2))
        date_time_3 = datetime.strptime('2016-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.assertEqual(0, importer.get_weather_hourly_df_if_for_time(date_time_3))
        date_time_4 = datetime.strptime('2015-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.assertEqual(None, importer.get_weather_hourly_df_if_for_time(date_time_4))
        date_time_5 = datetime.strptime('2016-02-01 00:51:23', '%Y-%m-%d %H:%M:%S')  # 1
        self.assertEqual(1, importer.get_weather_hourly_df_if_for_time(date_time_5))
        date_time_6 = datetime.strptime('2017-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        importer.get_weather_hourly_df_if_for_time(date_time_6)
        self.assertEqual(None, importer.get_weather_hourly_df_if_for_time(date_time_6))


if __name__ == '__main__':
    unittest.main()
