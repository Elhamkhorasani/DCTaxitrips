

class OutlierIdentifier:

    def _get_trips_with_unreasonable_high_duration(self, tx, duration:int, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip) 
            WHERE a.duration > """ + str(duration) + """
            RETURN id(a)""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_with_zero_duration(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip) 
                WHERE a.duration = 0
                RETURN id(a)""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_with_very_low_duration(self, tx, duration:int, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip) 
                    WHERE a.duration < """ + str(duration) + """
                    RETURN id(a)""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_where_duration_is_much_higher_than_travelled_distance(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip)
            WHERE a.haversineDistance > 0
            AND (a.haversineDistance / 11.4263 * 50) < a.duration
            RETURN id(a);""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_with_very_low_duration_despite_large_distance(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip)
            WHERE a.duration > 0
            AND ((a.haversineDistance / 1000) / (toFloat(a.duration) / (60*60))) > 112.654
            RETURN id(a);""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_with_very_low_duration_despite_large_haversine(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip)
            WHERE ((a.haversineDistance / 1000) / (11.4263 * 25)) < (a.duration / (60*60))
            RETURN id(a);""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trip_ids_not_in_shape_collection(self, tx, cell_name, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Coordinate)<-[:IS_DROPPED_OFF_AT]-(b:Trip)
            WHERE NOT (a)-[:BELONGS_TO]->(:""" + cell_name + """)
            RETURN id(b) AS id
            UNION ALL MATCH (c:Coordinate)<-[:IS_PICKED_UP_AT]-(d:Trip)
            WHERE NOT (c)-[:BELONGS_TO]->(:""" + cell_name + """)
            RETURN id(d) AS id;""")
        trip_ids = set([])
        [trip_ids.add(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trip_ids_not_in_grid(self, tx, cell_name, filter_node_name, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (endGF:""" + filter_node_name + """)<-[:HAS]-(a:Coordinate)<-[:IS_DROPPED_OFF_AT]-(b:Trip)
            WHERE NOT (:""" + cell_name + """IndexX)<-[:BELONGS_TO]-(endGF)-[:BELONGS_TO]->(:""" + cell_name + """IndexY)
            RETURN id(b) AS id
            UNION ALL MATCH (endGF:""" + filter_node_name + """)<-[:HAS]-(a:Coordinate)<-[:IS_PICKED_UP_AT]-(b:Trip)
            WHERE NOT (:""" + cell_name + """IndexX)<-[:BELONGS_TO]-(endGF)-[:BELONGS_TO]->(:""" + cell_name + """IndexY)
            RETURN id(b) AS id;""")
        trip_ids = set([])
        [trip_ids.add(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    @staticmethod
    def _mark_as_outliers(tx, trip_ids, method_identifier):
        for trip_id in trip_ids:
            tx.run("""MATCH (n:Trip) 
                WHERE id(n) = """ + str(trip_id) + """ 
                SET n.outlier = TRUE,
                n.outlierMethod = n.outlierMethod + toInteger(""" + str(method_identifier) + """);""")

    @staticmethod
    def _get_all_outlier_ids(tx):
        result = tx.run("""MATCH (a:Trip)
            WHERE a.outlier = TRUE
            RETURN id(a);""")
        outlier = []
        [outlier.append(record[0]) for record in result]
        return outlier

    @staticmethod
    def _get_outliers_from_method(tx, method_id):
        result = tx.run("""MATCH (a:Trip)
            WHERE a.outlier = TRUE
            AND toInteger(""" + str(method_id) + """) IN a.outlierMethod
            RETURN id(a);""")
        outlier = []
        [outlier.append(record[0]) for record in result]
        return outlier

    @staticmethod
    def _reset_outliers(tx):
        tx.run("""MATCH(n: Trip)
            WHERE n.outlier = TRUE
            SET n.outlier = FALSE, n.outlierMethod = [0];""")

    def _get_trips_with_haversine_distance_of_zero(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (a:Trip)
                WHERE a.haversineDistance = 0
                RETURN id(a);""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def _get_trips_with_unusual_passenger_count(self, tx, mark_as_outliers, method_identifier):
        result = tx.run("""MATCH (n:Trip)
            WHERE n.passengerCount = 0 OR n.passengerCount > 7 
            RETURN id(n);""")
        trip_ids = []
        [trip_ids.append(record[0]) for record in result]
        if mark_as_outliers:
            self._mark_as_outliers(tx, trip_ids, method_identifier)

    def identify_outliers(self, tx):
        # TODO: List of ids should be returned directly by _get_trip_methods

        # Reset outlier identification
        self._reset_outliers(tx)

        # District-based
        self._get_trip_ids_not_in_shape_collection(tx, 'CD', True, 1)
        self._get_trip_ids_not_in_shape_collection(tx, 'NTA', True, 2)
        self._get_trip_ids_not_in_shape_collection(tx, 'TaxiZone', True, 3)

        # SquareGrid-based
        self._get_trip_ids_not_in_grid(tx, 'SGC1000', 'SquareGridFilter', True, 4)
        self._get_trip_ids_not_in_grid(tx, 'SGC500', 'SquareGridFilter', True, 5)
        self._get_trip_ids_not_in_grid(tx, 'SGC250', 'SquareGridFilter', True, 6)
        self._get_trip_ids_not_in_grid(tx, 'SGC150', 'SquareGridFilter', True, 7)
        self._get_trip_ids_not_in_grid(tx, 'SGC100', 'SquareGridFilter', True, 8)
        self._get_trip_ids_not_in_grid(tx, 'SGC50', 'SquareGridFilter', True, 9)
        self._get_trip_ids_not_in_grid(tx, 'SGC25', 'SquareGridFilter', True, 10)
        self._get_trip_ids_not_in_grid(tx, 'SGC15', 'SquareGridFilter', True, 11)
        self._get_trip_ids_not_in_grid(tx, 'SGC10', 'SquareGridFilter', True, 12)
        self._get_trip_ids_not_in_grid(tx, 'SGC5', 'SquareGridFilter', True, 13)

        # HexagonGrid-based
        self._get_trip_ids_not_in_grid(tx, 'HGC1000', 'HexagonGridFilter', True, 14)
        self._get_trip_ids_not_in_grid(tx, 'HGC500', 'HexagonGridFilter', True, 15)
        self._get_trip_ids_not_in_grid(tx, 'HGC250', 'HexagonGridFilter', True, 16)
        self._get_trip_ids_not_in_grid(tx, 'HGC150', 'HexagonGridFilter', True, 17)
        self._get_trip_ids_not_in_grid(tx, 'HGC100', 'HexagonGridFilter', True, 18)
        self._get_trip_ids_not_in_grid(tx, 'HGC50', 'HexagonGridFilter', True, 19)
        self._get_trip_ids_not_in_grid(tx, 'HGC25', 'HexagonGridFilter', True, 20)
        self._get_trip_ids_not_in_grid(tx, 'HGC15', 'HexagonGridFilter', True, 21)
        self._get_trip_ids_not_in_grid(tx, 'HGC10', 'HexagonGridFilter', True, 22)
        self._get_trip_ids_not_in_grid(tx, 'HGC5', 'HexagonGridFilter', True, 23)

        # TriangleGrid-based
        self._get_trip_ids_not_in_grid(tx, 'TGC1000', 'TriangleGridFilter', True, 24)
        self._get_trip_ids_not_in_grid(tx, 'TGC500', 'TriangleGridFilter', True, 25)
        self._get_trip_ids_not_in_grid(tx, 'TGC250', 'TriangleGridFilter', True, 26)
        self._get_trip_ids_not_in_grid(tx, 'TGC150', 'TriangleGridFilter', True, 27)
        self._get_trip_ids_not_in_grid(tx, 'TGC100', 'TriangleGridFilter', True, 28)
        self._get_trip_ids_not_in_grid(tx, 'TGC50', 'TriangleGridFilter', True, 29)
        self._get_trip_ids_not_in_grid(tx, 'TGC25', 'TriangleGridFilter', True, 30)
        self._get_trip_ids_not_in_grid(tx, 'TGC15', 'TriangleGridFilter', True, 31)
        self._get_trip_ids_not_in_grid(tx, 'TGC10', 'TriangleGridFilter', True, 32)
        self._get_trip_ids_not_in_grid(tx, 'TGC5', 'TriangleGridFilter', True, 33)

        # Duration-based
        self._get_trips_with_unreasonable_high_duration(tx, 10902, True, 34)
        self._get_trips_with_zero_duration(tx, True, 35)
        self._get_trips_with_very_low_duration(tx, 30, True, 36)
        self._get_trips_where_duration_is_much_higher_than_travelled_distance(tx, True, 37)
        self._get_trips_with_very_low_duration_despite_large_distance(tx, True, 38)
        self._get_trips_with_very_low_duration_despite_large_haversine(tx, True, 39)

        # Distance-based
        self._get_trips_with_haversine_distance_of_zero(tx, True, 40)

        # Passenger-based
        self._get_trips_with_unusual_passenger_count(tx, True, 41)

        # Produce report
        ids_of_all_outliers = self._get_all_outlier_ids(tx)
        print(f'\nOUTLIER REPORT\n{len(ids_of_all_outliers)} outliers overall.')
        for i in range(1, 42):
            print(f'{len(self._get_outliers_from_method(tx, i))} by outlier method {i}')

        return None