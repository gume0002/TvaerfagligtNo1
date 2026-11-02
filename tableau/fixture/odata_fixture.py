"""Isolated OData V4 fixture for the Tableau Public test in task T002.

This is NOT the hotel backend. It has no database and no business rules. All
values are hand-calculated constants taken from the acceptance criteria in
specs/004-hotelsystem/spec.md, so a wrong number in Tableau points at the
connection and not at a calculation.

Run: python3 tableau/fixture/odata_fixture.py
Only the Python standard library is used.
"""

import argparse
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlsplit

ROOT = "/api/odata"
NAMESPACE = "HotelKongArthur.Fixture"
PAGE_SIZE = 2

# Property types decide how a value is rendered, see render_value().
ENTITY_SETS = {
    "HotelKpis": {
        "type": "HotelKpi",
        "properties": [
            ("id", "Edm.Int32", False),
            ("scenario", "Edm.String", False),
            ("revenue", "Edm.Decimal", False),
            ("bookedRoomNights", "Edm.Int32", False),
            ("availableRoomNights", "Edm.Int32", False),
            ("occupancyRatePercent", "Edm.Decimal", True),
            ("adr", "Edm.Decimal", True),
            ("demoData", "Edm.Boolean", False),
            ("generatedAt", "Edm.DateTimeOffset", False),
        ],
    },
    "RoomTypeSeasonRevenue": {
        "type": "RoomTypeSeasonRevenueRow",
        "properties": [
            ("id", "Edm.Int32", False),
            ("filterKey", "Edm.String", False),
            ("roomType", "Edm.String", False),
            ("season", "Edm.String", False),
            ("revenue", "Edm.Decimal", False),
            ("demoData", "Edm.Boolean", False),
            ("generatedAt", "Edm.DateTimeOffset", False),
        ],
    },
    "BarCategoryShares": {
        "type": "BarCategoryShare",
        "properties": [
            ("id", "Edm.Int32", False),
            ("category", "Edm.String", False),
            ("quantity", "Edm.Int32", False),
            ("revenue", "Edm.Decimal", False),
            ("quantitySharePercent", "Edm.Decimal", True),
            ("revenueSharePercent", "Edm.Decimal", True),
            ("demoData", "Edm.Boolean", False),
            ("generatedAt", "Edm.DateTimeOffset", False),
        ],
    },
}

# US8.1 (50 % / 1000.00) and US8.3 (no data). Decimals are strings so that the
# exact two-decimal text reaches the client without passing through a float.
HOTEL_KPIS = [
    {"id": 1, "scenario": "us8-1-two-rooms-two-nights", "revenue": "2000.00",
     "bookedRoomNights": 2, "availableRoomNights": 4,
     "occupancyRatePercent": "50.00", "adr": "1000.00"},
    {"id": 2, "scenario": "us8-3-no-booked-nights", "revenue": "0.00",
     "bookedRoomNights": 0, "availableRoomNights": 4,
     "occupancyRatePercent": "0.00", "adr": None},
    {"id": 3, "scenario": "zero-capacity", "revenue": "0.00",
     "bookedRoomNights": 0, "availableRoomNights": 0,
     "occupancyRatePercent": None, "adr": None},
]

# US7.5: a stay 28 Feb - 2 Mar 2026 at 1000.00 per night. Rows with different
# filterKey values describe different filter choices and must never be summed.
ROOM_TYPE_SEASON_REVENUE = [
    {"id": 1, "filterKey": "year=2026", "roomType": "Standard Double",
     "season": "low", "revenue": "1000.00"},
    {"id": 2, "filterKey": "year=2026", "roomType": "Standard Double",
     "season": "mid", "revenue": "1000.00"},
    {"id": 3, "filterKey": "year=2026;season=low", "roomType": "Standard Double",
     "season": "low", "revenue": "1000.00"},
]

# US9.1 and the three changes used to test refresh. Each state is calculated by
# hand and documented in tableau/README.md.
BAR_STATES = {
    "start": [
        ("cocktail", 3, "300.00", "60.00", "75.00"),
        ("coffee", 2, "100.00", "40.00", "25.00"),
    ],
    "create": [
        ("cocktail", 3, "300.00", "42.86", "60.00"),
        ("coffee", 4, "200.00", "57.14", "40.00"),
    ],
    "update": [
        ("cocktail", 2, "200.00", "33.33", "50.00"),
        ("coffee", 4, "200.00", "66.67", "50.00"),
    ],
    "cancel": [
        ("cocktail", 2, "200.00", "50.00", "66.67"),
        ("coffee", 2, "100.00", "50.00", "33.33"),
    ],
}


class FixtureState:
    """Holds the demonstration state and how decimals are serialized."""

    def __init__(self, decimals_as_strings=False):
        self.bar_state = "start"
        self.decimals_as_strings = decimals_as_strings

    def rows(self, entity_set):
        if entity_set == "HotelKpis":
            rows = HOTEL_KPIS
        elif entity_set == "RoomTypeSeasonRevenue":
            rows = ROOM_TYPE_SEASON_REVENUE
        else:
            rows = [
                {"id": index, "category": category, "quantity": quantity,
                 "revenue": revenue, "quantitySharePercent": quantity_share,
                 "revenueSharePercent": revenue_share}
                for index, (category, quantity, revenue, quantity_share, revenue_share)
                in enumerate(BAR_STATES[self.bar_state], start=1)
            ]
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return [dict(row, demoData=True, generatedAt=generated_at) for row in rows]


def render_value(value, edm_type, decimals_as_strings):
    """Render one JSON value. Edm.Decimal keeps its exact text either way."""
    if value is None:
        return "null"
    if edm_type == "Edm.Decimal" and not decimals_as_strings:
        return value
    return json.dumps(value, ensure_ascii=False)


def render_row(row, entity_set, selected, decimals_as_strings):
    parts = []
    for name, edm_type, _nullable in ENTITY_SETS[entity_set]["properties"]:
        if selected is None or name in selected:
            rendered = render_value(row[name], edm_type, decimals_as_strings)
            parts.append(json.dumps(name) + ":" + rendered)
    return "{" + ",".join(parts) + "}"


def metadata_xml():
    types = []
    sets = []
    for set_name, definition in ENTITY_SETS.items():
        properties = "".join(
            '<Property Name="{}" Type="{}" Nullable="{}"{}/>'.format(
                name, edm_type, str(nullable).lower(),
                ' Precision="12" Scale="2"' if edm_type == "Edm.Decimal" else "",
            )
            for name, edm_type, nullable in definition["properties"]
        )
        types.append(
            '<EntityType Name="{}"><Key><PropertyRef Name="id"/></Key>{}</EntityType>'.format(
                definition["type"], properties
            )
        )
        sets.append(
            '<EntitySet Name="{}" EntityType="{}.{}"/>'.format(
                set_name, NAMESPACE, definition["type"]
            )
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<edmx:Edmx Version="4.0" xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx">'
        "<edmx:DataServices>"
        '<Schema Namespace="{ns}" xmlns="http://docs.oasis-open.org/odata/ns/edm">'
        "{types}"
        '<EntityContainer Name="Container">{sets}</EntityContainer>'
        "</Schema></edmx:DataServices></edmx:Edmx>"
    ).format(ns=NAMESPACE, types="".join(types), sets="".join(sets))


class Handler(BaseHTTPRequestHandler):
    server_version = "HotelODataFixture/1"
    protocol_version = "HTTP/1.1"

    @property
    def state(self):
        return self.server.fixture_state

    def base_url(self):
        host = self.headers.get("Host", "localhost")
        return "http://{}{}".format(host, ROOT)

    def send_body(self, status, body, content_type):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("OData-Version", "4.0")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_json(self, status, payload):
        self.send_body(
            status,
            json.dumps(payload, ensure_ascii=False),
            "application/json;odata.metadata=minimal;charset=utf-8",
        )

    def send_error_json(self, status, code, message):
        self.send_json(status, {"error": {"code": code, "message": message}})

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parts = urlsplit(self.path)
        path = parts.path.rstrip("/")
        query = parse_qs(parts.query)
        if path == ROOT:
            self.send_json(200, {
                "@odata.context": self.base_url() + "/$metadata",
                "value": [
                    {"name": name, "kind": "EntitySet", "url": name}
                    for name in ENTITY_SETS
                ],
            })
        elif path == ROOT + "/$metadata":
            self.send_body(200, metadata_xml(), "application/xml;charset=utf-8")
        elif path.startswith(ROOT + "/") and path[len(ROOT) + 1:] in ENTITY_SETS:
            self.send_entity_set(path[len(ROOT) + 1:], query)
        else:
            self.send_error_json(404, "not_found", "Unknown path: " + parts.path)

    def do_POST(self):
        # Test control only. It is not part of the OData service.
        path = urlsplit(self.path).path.rstrip("/")
        prefix = "/fixture/state/"
        name = path[len(prefix):] if path.startswith(prefix) else None
        if name not in BAR_STATES:
            self.send_error_json(404, "not_found", "Unknown fixture state")
            return
        self.state.bar_state = name
        self.send_json(200, {"barState": name})

    def send_entity_set(self, entity_set, query):
        try:
            skip = int(query.get("$skip", ["0"])[0])
            top = int(query["$top"][0]) if "$top" in query else None
        except ValueError:
            self.send_error_json(400, "invalid_query", "$skip and $top must be integers")
            return
        if skip < 0 or (top is not None and top < 0):
            self.send_error_json(400, "invalid_query", "$skip and $top must not be negative")
            return

        selected = None
        if "$select" in query:
            selected = {name.strip() for name in query["$select"][0].split(",")}
            known = {prop[0] for prop in ENTITY_SETS[entity_set]["properties"]}
            if selected - known:
                self.send_error_json(400, "invalid_query", "Unknown property in $select")
                return

        rows = self.state.rows(entity_set)
        total = len(rows)
        end = total if top is None else min(total, skip + top)
        page_end = min(end, skip + PAGE_SIZE)
        page = rows[skip:page_end]

        # IEEE754Compatible=true is the OData way to ask for decimals as strings.
        as_strings = (
            self.state.decimals_as_strings
            or "ieee754compatible=true" in self.headers.get("Accept", "").lower()
            or "ieee754compatible=true" in self.headers.get("Content-Type", "").lower()
        )
        fields = ['"@odata.context":' + json.dumps(
            "{}/$metadata#{}".format(self.base_url(), entity_set))]
        if query.get("$count", ["false"])[0].lower() == "true":
            fields.append('"@odata.count":{}'.format(total))
        if page_end < end:
            next_query = {"$skip": page_end}
            if top is not None:
                next_query["$top"] = end - page_end
            for name in ("$select", "$count"):
                if name in query:
                    next_query[name] = query[name][0]
            fields.append('"@odata.nextLink":' + json.dumps(
                "{}/{}?{}".format(self.base_url(), entity_set, urlencode(next_query))))
        items = ",".join(render_row(row, entity_set, selected, as_strings) for row in page)
        fields.append('"value":[' + items + "]")
        self.send_body(
            200,
            "{" + ",".join(fields) + "}",
            "application/json;odata.metadata=minimal;charset=utf-8",
        )


def create_server(host, port, decimals_as_strings=False):
    server = ThreadingHTTPServer((host, port), Handler)
    server.fixture_state = FixtureState(decimals_as_strings)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("FIXTURE_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("FIXTURE_PORT", "8090")))
    parser.add_argument(
        "--decimals-as-strings",
        action="store_true",
        default=os.environ.get("FIXTURE_DECIMALS_AS_STRINGS", "").lower() == "true",
        help='Always send Edm.Decimal as a string, e.g. "1000.00".',
    )
    args = parser.parse_args()
    server = create_server(args.host, args.port, args.decimals_as_strings)
    print("OData fixture: http://localhost:{}{}/".format(args.port, ROOT), flush=True)
    print("Decimals as strings: {}".format(args.decimals_as_strings), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
