from data_preparation.DataTransformer import DataTransformer
from grid_creation.GridCreator import Grid, SquareGrid, TriangleGrid, HexagonGrid

from pyproj import Transformer
import shapely.geometry


def calculate_sw_corner_of_grid_from_center(lat, lon, grid_size, x_number_of_grids, y_number_of_grids):
    transformed_center = Transformer.from_crs('epsg:4326', 'epsg:3857').transform(lat, lon)
    return shapely.geometry.Point(
        Transformer.from_crs('epsg:3857', 'epsg:4326').transform(
            transformed_center[0] - grid_size * x_number_of_grids / 2,  # Movement in x direction
            transformed_center[1] - grid_size * y_number_of_grids / 2))  # Movement in y direction


def get_corners_of_grid(sw_corner):
    coordinate_to_sth = Transformer.from_crs('epsg:4326', 'epsg:3857')
    sth_to_coordinate = Transformer.from_crs('epsg:3857', 'epsg:4326')
    trans_bl = coordinate_to_sth.transform(sw_corner[0], sw_corner[1])
    br = sth_to_coordinate.transform(trans_bl[0] + 212 * 150, trans_bl[1])
    tl = sth_to_coordinate.transform(trans_bl[0], trans_bl[1] + 219 * 150)
    tr = sth_to_coordinate.transform(trans_bl[0] + 212 * 150, trans_bl[1] + 219 * 150)
    return sw_corner, tl, tr, br


def move_sw_corner_of_grid():
    bottom_left_old = calculate_sw_corner_of_grid_from_center(40.7128, -74.0060, 150, 212, 219)
    transformed_bl_old = Transformer.from_crs('epsg:4326', 'epsg:3857').transform(bottom_left_old.x, bottom_left_old.y)
    return Transformer.from_crs('epsg:3857', 'epsg:4326').transform(transformed_bl_old[0] + 13140,
                                                                    transformed_bl_old[1] + 6360)


def main():

    bottom_left = move_sw_corner_of_grid()
    bl, tl, tr, br = get_corners_of_grid(bottom_left)
    print(bl, tl, tr, br)
    # grid = TriangleGrid(bl[0], bl[1], tr[0], tr[1], 2000)
    # grid.visualize_grid()
    # grid = HexagonGrid(bl[0], bl[1], tr[0], tr[1], 2000)
    # grid = HexagonGrid(40.49611539518921, -74.25559136315213, 40.9155327770052, -73.70000906321046, 10000)
    # grid.visualize_grid()


    # additional_features_to_include = ['haversine', 'average temperature']
    # transformer = DataTransformer(
    #     grid,
    #     11382047,
    #     './data/original/yellow_tripdata_2016-02.csv',
    #     'ytt1602-validation200x200.csv',
    #     'ytt1602-trainingTest200x200.csv',
    #     additional_features_to_include,
    #     'weather_nyc_centralpark_2016.csv',
    #     '2016-02-01',
    #     '2016-02-29')


if __name__ == '__main__':
    main()
