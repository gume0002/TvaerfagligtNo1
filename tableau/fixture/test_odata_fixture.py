"""Checks the fixture itself. Says nothing about whether Tableau accepts it.

Run: python3 -m unittest discover -s tableau/fixture -v
"""

import json
import threading
import unittest
import urllib.request
import xml.etree.ElementTree as ET
from decimal import Decimal

from odata_fixture import BAR_STATES, ENTITY_SETS, create_server

BASE = "/api/odata"


class FixtureCase(unittest.TestCase):
    decimals_as_strings = False

    def setUp(self):
        self.server = create_server("127.0.0.1", 0, self.decimals_as_strings)
        self.port = self.server.server_address[1]
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def url(self, path):
        return "http://127.0.0.1:{}{}".format(self.port, path)

    def get_raw(self, path, headers=None):
        request = urllib.request.Request(self.url(path), headers=headers or {})
        with urllib.request.urlopen(request) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8")

    def get_json(self, path, headers=None):
        return json.loads(self.get_raw(path, headers)[2], parse_float=Decimal)

    def read_all(self, entity_set):
        """Follow every nextLink, as an OData client has to."""
        rows = []
        page = self.get_json("{}/{}".format(BASE, entity_set))
        rows.extend(page["value"])
        while "@odata.nextLink" in page:
            with urllib.request.urlopen(page["@odata.nextLink"]) as response:
                page = json.loads(response.read().decode("utf-8"), parse_float=Decimal)
            rows.extend(page["value"])
        return rows


class ServiceTests(FixtureCase):
    def test_service_document_lists_every_entity_set(self):
        status, headers, body = self.get_raw(BASE + "/")
        self.assertEqual(status, 200)
        self.assertEqual(headers["OData-Version"], "4.0")
        self.assertEqual(
            {item["name"] for item in json.loads(body)["value"]}, set(ENTITY_SETS)
        )

    def test_metadata_is_xml_and_describes_decimal_and_nullable(self):
        status, headers, body = self.get_raw(BASE + "/$metadata")
        self.assertEqual(status, 200)
        self.assertIn("application/xml", headers["Content-Type"])
        root = ET.fromstring(body)
        edm = "{http://docs.oasis-open.org/odata/ns/edm}"
        types = {node.get("Name"): node for node in root.iter(edm + "EntityType")}
        adr = next(p for p in types["HotelKpi"].iter(edm + "Property") if p.get("Name") == "adr")
        self.assertEqual(adr.get("Type"), "Edm.Decimal")
        self.assertEqual(adr.get("Nullable"), "true")
        self.assertEqual(len(list(root.iter(edm + "EntitySet"))), len(ENTITY_SETS))

    def test_pagination_returns_all_rows_exactly_once(self):
        first_page = self.get_json(BASE + "/HotelKpis")
        self.assertEqual(len(first_page["value"]), 2)
        self.assertIn("@odata.nextLink", first_page)
        self.assertEqual([row["id"] for row in self.read_all("HotelKpis")], [1, 2, 3])

    def test_top_skip_count_and_select(self):
        page = self.get_json(BASE + "/HotelKpis?$top=1&$skip=1&$count=true&$select=id,adr")
        self.assertEqual(page["@odata.count"], 3)
        self.assertEqual(page["value"], [{"id": 2, "adr": None}])
        self.assertNotIn("@odata.nextLink", page)

    def test_invalid_query_gives_json_error(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get_raw(BASE + "/HotelKpis?$top=abc")
        self.assertEqual(caught.exception.code, 400)
        self.assertEqual(json.loads(caught.exception.read())["error"]["code"], "invalid_query")
        caught.exception.close()


class ValueTests(FixtureCase):
    def test_us8_1_and_null_ratios(self):
        rows = {row["id"]: row for row in self.read_all("HotelKpis")}
        self.assertEqual(rows[1]["occupancyRatePercent"], Decimal("50.00"))
        self.assertEqual(rows[1]["adr"], Decimal("1000.00"))
        self.assertEqual(rows[2]["occupancyRatePercent"], Decimal("0.00"))
        self.assertIsNone(rows[2]["adr"])
        self.assertIsNone(rows[3]["occupancyRatePercent"])

    def test_decimals_are_json_numbers_by_default_with_exact_text(self):
        body = self.get_raw(BASE + "/HotelKpis?$top=1")[2]
        self.assertIn('"revenue":2000.00', body)

    def test_ieee754compatible_header_gives_decimal_strings(self):
        page = self.get_json(
            BASE + "/HotelKpis?$top=1",
            {"Accept": "application/json;IEEE754Compatible=true"},
        )
        self.assertEqual(page["value"][0]["revenue"], "2000.00")

    def test_us7_5_season_split_and_filter_key(self):
        rows = self.read_all("RoomTypeSeasonRevenue")
        full_year = [row for row in rows if row["filterKey"] == "year=2026"]
        self.assertEqual(
            {row["season"]: row["revenue"] for row in full_year},
            {"low": Decimal("1000.00"), "mid": Decimal("1000.00")},
        )
        low_only = [row for row in rows if row["filterKey"] == "year=2026;season=low"]
        self.assertEqual([row["revenue"] for row in low_only], [Decimal("1000.00")])

    def test_generated_at_is_utc_timestamp_and_rows_are_marked_demo(self):
        for row in self.read_all("BarCategoryShares"):
            self.assertRegex(row["generatedAt"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertIs(row["demoData"], True)


class BarStateTests(FixtureCase):
    def set_state(self, name):
        request = urllib.request.Request(self.url("/fixture/state/" + name), method="POST")
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)

    def test_us9_1_start_state(self):
        rows = {row["category"]: row for row in self.read_all("BarCategoryShares")}
        self.assertEqual(rows["cocktail"]["quantity"], 3)
        self.assertEqual(rows["cocktail"]["revenue"], Decimal("300.00"))
        self.assertEqual(rows["cocktail"]["quantitySharePercent"], Decimal("60.00"))
        self.assertEqual(rows["cocktail"]["revenueSharePercent"], Decimal("75.00"))
        self.assertEqual(rows["coffee"]["quantitySharePercent"], Decimal("40.00"))
        self.assertEqual(rows["coffee"]["revenueSharePercent"], Decimal("25.00"))

    def test_changes_are_visible_on_the_next_read(self):
        for name, (cocktail, coffee) in BAR_STATES.items():
            self.set_state(name)
            rows = {row["category"]: row for row in self.read_all("BarCategoryShares")}
            self.assertEqual(rows["cocktail"]["revenue"], Decimal(cocktail[2]))
            self.assertEqual(rows["coffee"]["revenue"], Decimal(coffee[2]))

    def test_hand_calculated_states_match_their_shares(self):
        """Recalculates the constants, so a typing error cannot reach Tableau."""
        for rows in BAR_STATES.values():
            total_quantity = sum(row[1] for row in rows)
            total_revenue = sum(Decimal(row[2]) for row in rows)
            for _category, quantity, revenue, quantity_share, revenue_share in rows:
                expected_quantity = (Decimal(quantity) * 100 / total_quantity).quantize(Decimal("0.01"))
                expected_revenue = (Decimal(revenue) * 100 / total_revenue).quantize(Decimal("0.01"))
                self.assertEqual(Decimal(quantity_share), expected_quantity)
                self.assertEqual(Decimal(revenue_share), expected_revenue)

    def test_unknown_state_is_rejected(self):
        request = urllib.request.Request(self.url("/fixture/state/nope"), method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 404)
        caught.exception.close()


class DecimalStringModeTests(FixtureCase):
    decimals_as_strings = True

    def test_string_mode_sends_decimal_strings_and_real_nulls(self):
        rows = {row["id"]: row for row in self.read_all("HotelKpis")}
        self.assertEqual(rows[1]["adr"], "1000.00")
        self.assertIsNone(rows[2]["adr"])


if __name__ == "__main__":
    unittest.main()
