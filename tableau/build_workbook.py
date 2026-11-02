"""Adds worksheets and dashboards to a workbook with Tableau's own data sources.

Tableau Public refuses a workbook without extracts, and only Tableau can create
them. So a person connects the seven feed tables once and saves the workbook,
and this script adds everything else to that file.

The workbook only shows and selects rows from the OData feed. It has no business
rules: its single calculation picks the one row set that matches the dropdowns,
so results from different filter choices are never added together.

Run: python3 tableau/build_workbook.py <saved sources.twb> <output.twb> [API base URL]
Only the Python standard library is used.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import uuid
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

DEFAULT_API = 'http://127.0.0.1:8080'
SELECTED = 'Calculation_selected'

TEXT, NUMBER, COUNT, RANK, BOOL, TIME, DATE = 'text', 'number', 'count', 'rank', 'bool', 'time', 'date'
HOTEL_FILTERS = {'year': COUNT, 'seasonFilter': TEXT, 'countryFilter': TEXT, 'roomTypeFilter': TEXT}
BAR_FILTERS = {'year': COUNT, 'employee': TEXT}
METADATA = {'demoData': BOOL, 'generatedAt': TIME}

DATASOURCES = {
    'HotelTotals': {**HOTEL_FILTERS, 'period': TEXT, 'revenue': NUMBER, 'bookedRoomNights': NUMBER,
                    'availableRoomNights': NUMBER, 'occupancyRatePercent': NUMBER, 'occupancyStatus': TEXT,
                    'adr': NUMBER, 'adrStatus': TEXT, 'occupancyScope': TEXT, 'satisfactionStatus': TEXT,
                    'businessDate': DATE, **METADATA},
    'HotelRoomTypeSeason': {**HOTEL_FILTERS, 'roomType': TEXT, 'season': TEXT, 'revenue': NUMBER, **METADATA},
    'HotelCountries': {**HOTEL_FILTERS, 'country': TEXT, 'revenue': NUMBER, 'revenueRank': RANK,
                       'guestStays': NUMBER, **METADATA},
    'HotelRoomTypeRanks': {**HOTEL_FILTERS, 'roomType': TEXT, 'revenue': NUMBER, 'revenueRank': RANK, **METADATA},
    'BarTotals': {**BAR_FILTERS, 'quantity': NUMBER, 'revenue': NUMBER, **METADATA},
    'BarDrinks': {**BAR_FILTERS, 'drink': TEXT, 'category': TEXT, 'quantity': NUMBER, 'revenue': NUMBER, **METADATA},
    'BarCategories': {**BAR_FILTERS, 'category': TEXT, 'quantity': NUMBER, 'revenue': NUMBER,
                      'quantitySharePercent': NUMBER, 'revenueSharePercent': NUMBER, 'shareStatus': TEXT, **METADATA},
}
CAPTIONS = {
    'revenue': 'Omsætning (DKK)', 'bookedRoomNights': 'Bookede værelsesnætter', 'availableRoomNights': 'Tilgængelige værelsesnætter',
    'occupancyRatePercent': 'Belægning (%)', 'adr': 'ADR (DKK)', 'period': 'Periode', 'country': 'Land', 'roomType': 'Værelsestype',
    'season': 'Sæson', 'guestStays': 'Gæsteophold', 'revenueRank': 'Placering', 'drink': 'Drik', 'category': 'Kategori',
    'quantity': 'Antal', 'quantitySharePercent': 'Andel af antal (%)', 'revenueSharePercent': 'Andel af omsætning (%)',
    'generatedAt': 'Datagrundlag (UTC)', 'demoData': 'Demodata', 'occupancyScope': 'Belægningens grundlag',
    'satisfactionStatus': 'Gæstetilfredshed', 'businessDate': 'Hotellets dato', 'shareStatus': 'Status for andele',
    'adrStatus': 'Status for ADR', 'occupancyStatus': 'Status for belægning', 'employee': 'Medarbejder',
}


STATUS_LABELS = {'ok': 'OK', 'no_data': 'Intet datagrundlag'}
LABELS = {
    'period': {'all': 'Samlet', 'past': 'Passeret', 'upcoming': 'Kommende'},
    'season': {'low': 'Lavsæson', 'mid': 'Mellemsæson', 'high': 'Højsæson'},
    'category': {'cocktail': 'Cocktail', 'coffee': 'Kaffe'},
    'occupancyScope': {'hotel': 'Hele hotellet', 'country_contribution': 'Landets bidrag'},
    'satisfactionStatus': STATUS_LABELS,
    'occupancyStatus': STATUS_LABELS,
    'adrStatus': STATUS_LABELS,
    'shareStatus': STATUS_LABELS,
}
TWO_DECIMALS = {'occupancyRatePercent', 'adr', 'quantitySharePercent', 'revenueSharePercent', 'revenue'}
WHOLE_NUMBERS = {'bookedRoomNights', 'availableRoomNights', 'guestStays', 'quantity'}


def attr(value) -> str:
    return quoteattr(str(value), {'"': '&quot;'})


def formula_text(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def new_id() -> str:
    return '{' + str(uuid.uuid4()).upper() + '}'


REAL_NAMES = {}
REAL_COLUMNS = {}


def ds_name(table: str) -> str:
    return REAL_NAMES[table]


def real_column(table: str, field: str) -> str:
    return REAL_COLUMNS[table][field]


def selection_formula(table: str) -> str:
    if 'seasonFilter' in DATASOURCES[table]:
        return ('STR([year]) = [Parameters].[Parameter 1] AND [seasonFilter] = [Parameters].[Parameter 2] '
                'AND [countryFilter] = [Parameters].[Parameter 3] AND [roomTypeFilter] = [Parameters].[Parameter 4]')
    return 'STR([year]) = [Parameters].[Parameter 1] AND [employee] = [Parameters].[Parameter 5]'


def selection_column(table: str) -> str:
    return (f"<column caption='Valgt filter' datatype='boolean' name='[{SELECTED}]' role='dimension' type='nominal'>"
            f"<calculation class='tableau' formula={attr(selection_formula(table))} /></column>")


def adapted_datasource(table: str, block: str) -> str:
    """Use readable captions, make placements discrete and add the selection."""
    columns = {}

    def adapt(match):
        column = match.group(0)
        field = re.search(r"name='\[([^\]]*)\]'", column).group(1)
        if field not in DATASOURCES[table]:
            return column
        if field in CAPTIONS:
            column = re.sub(r"caption='[^']*'", f"caption={attr(CAPTIONS[field])}", column, count=1)
        if DATASOURCES[table][field] == RANK:
            column = column.replace("role='measure'", "role='dimension'").replace("type='quantitative'", "type='ordinal'")
        if field in TWO_DECIMALS:
            column = column.replace(' caption=', " default-format='n#,##0.00' caption=", 1)
        if field in WHOLE_NUMBERS:
            column = column.replace(' caption=', " default-format='n#,##0' caption=", 1)
        labels = dict(LABELS.get(field, {}))
        keys = {key: formula_text(key) for key in labels}
        if field == 'demoData':
            labels, keys = {'true': 'Ja', 'false': 'Nej'}, {'true': 'true', 'false': 'false'}
        if labels:
            aliases = ''.join(f"<alias key={attr(keys[key])} value={attr(value)} />" for key, value in labels.items())
            column = column.replace(' />', f'><aliases>{aliases}</aliases></column>')
        columns[field] = column
        return column

    head, extract, tail = block.partition('<extract ')
    head = re.sub(r"<column caption='[^']*' datatype='[^']*' name='\[[^\]]*\]'[^>]*/>", adapt, head)
    missing = set(DATASOURCES[table]) - set(columns)
    if missing:
        raise SystemExit(f'{table} mangler felterne {sorted(missing)} i den gemte projektmappe')
    REAL_COLUMNS[table] = columns
    head = head.rstrip() + selection_column(table) + '\n      '
    return head + extract + tail


def parameter(number: int, caption: str, values: list, default, aliases: dict | None = None) -> str:
    aliases = aliases or {}
    if isinstance(default, int):
        members = ''.join(f"<member value='{value}' />" for value in values)
        return (f"<column caption={attr(caption)} datatype='integer' name='[Parameter {number}]' param-domain-type='list' "
                f"role='measure' type='quantitative' value='{default}'><calculation class='tableau' formula='{default}' />"
                f"<members>{members}</members></column>")
    members = ''
    alias_xml = ''
    for value in values:
        key = formula_text(value)
        label = aliases.get(value)
        if label:
            alias_xml += f"<alias key={attr(key)} value={attr(label)} />"
            members += f"<member alias={attr(label)} value={attr(key)} />"
        else:
            members += f"<member value={attr(key)} />"
    return (f"<column caption={attr(caption)} datatype='string' name='[Parameter {number}]' param-domain-type='list' "
            f"role='measure' type='nominal' value={attr(formula_text(default))}><calculation class='tableau' "
            f"formula={attr(formula_text(default))} />"
            + (f"<aliases>{alias_xml}</aliases>" if alias_xml else '') + f"<members>{members}</members></column>")


def parameters_xml(years, current_year, countries, room_types, employees) -> tuple[str, dict]:
    columns = {
        1: parameter(1, 'År', [str(year) for year in years], str(current_year)),
        2: parameter(2, 'Sæson', ['all', 'low', 'mid', 'high'], 'all',
                     {'all': 'Alle', 'low': 'Lavsæson', 'mid': 'Mellemsæson', 'high': 'Højsæson'}),
        3: parameter(3, 'Land', ['all', *countries], 'all', {'all': 'Alle'}),
        4: parameter(4, 'Værelsestype', ['all', *room_types], 'all', {'all': 'Alle'}),
        5: parameter(5, 'Medarbejder', employees, 'Helene Christine'),
    }
    return "<datasource hasconnection='false' inline='true' name='Parameters' version='18.1'><aliases enabled='yes' />" + ''.join(columns.values()) + '</datasource>', columns


def instance(field: str, kind: str, aggregate: str = 'Sum') -> tuple[str, str]:
    """Return the shelf name and the XML for one use of a field."""
    if kind == NUMBER:
        prefix = aggregate.lower()
        name = f'{prefix}:{field}:qk'
        return name, f"<column-instance column='[{field}]' derivation={attr(aggregate)} name='[{name}]' pivot='key' type='quantitative' />"
    suffix = 'nk' if kind in (TEXT, BOOL) else 'ok'
    name = f'none:{field}:{suffix}'
    node_type = 'nominal' if suffix == 'nk' else 'ordinal'
    return name, f"<column-instance column='[{field}]' derivation='None' name='[{name}]' pivot='key' type={attr(node_type)} />"


class Sheet:
    def __init__(self, name, table, rows=(), cols=(), text=None, mark='Automatic', measures=(), sort=None, labels=False, parameters=()):
        self.name, self.table, self.rows, self.cols = name, table, list(rows), list(cols)
        self.text, self.mark, self.measures, self.sort, self.labels = text, mark, list(measures), sort, labels
        self.parameters = parameters

    def xml(self, parameter_columns: dict) -> str:
        ds = ds_name(self.table)
        fields = DATASOURCES[self.table]
        used = dict.fromkeys(self.rows + self.cols + self.measures + ([self.text] if self.text else []) + ([self.sort] if self.sort else []))
        dependency = {}
        instances = {}
        for field in used:
            dependency[field] = real_column(self.table, field)
            name, node = instance(field, fields[field])
            instances[field] = name
            dependency[f'#{field}'] = node
        selected = f'none:{SELECTED}:nk'
        selection = (selection_column(self.table)
                     + f"<column-instance column='[{SELECTED}]' derivation='None' name='[{selected}]' pivot='key' type='nominal' />")
        for field in ('year',) + (('seasonFilter', 'countryFilter', 'roomTypeFilter') if 'seasonFilter' in fields else ('employee',)):
            dependency.setdefault(field, real_column(self.table, field))
        filters = (f"<filter class='categorical' column='[{ds}].[{selected}]'>"
                   f"<groupfilter function='member' level='[{selected}]' member='true' user:ui-domain='database' "
                   "user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
        slices = f"<column>[{ds}].[{selected}]</column>"
        if self.measures:
            members = ''.join(
                f"<groupfilter function='member' level='[:Measure Names]' member={attr(formula_text(f'[{ds}].[{instances[field]}]'))} />"
                for field in self.measures)
            filters += (f"<filter class='categorical' column='[{ds}].[:Measure Names]'><groupfilter function='union' "
                        f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate'>{members}</groupfilter></filter>")
            slices += f"<column>[{ds}].[:Measure Names]</column>"
        sort = ''
        if self.sort:
            target = self.rows[-1]
            sort = f"<sort class='computed' column='[{ds}].[{instances[target]}]' direction='DESC' using='[{ds}].[{instances[self.sort]}]' />"
        shelf = lambda items: ' / '.join(f'[{ds}].[{instances[field]}]' for field in items)  # noqa: E731
        rows = shelf(self.rows)
        cols = shelf(self.cols)
        text_column = None
        if self.measures:
            cols = f'[{ds}].[:Measure Names]'
            text_column = f'[{ds}].[Multiple Values]'
        elif self.text:
            text_column = f'[{ds}].[{instances[self.text]}]'
        encodings = f"<encodings><text column={attr(text_column)} /></encodings>" if text_column else ''
        style = ("<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /></style-rule></style>"
                 if self.labels else '')
        parameter_numbers = (1, 2, 3, 4) if 'seasonFilter' in fields else (1, 5)
        parameter_dependency = ("<datasource-dependencies datasource='Parameters'>"
                                + ''.join(parameter_columns[number] for number in parameter_numbers) + '</datasource-dependencies>')
        title = f"<layout-options><title><formatted-text><run>{escape(self.name)}</run></formatted-text></title></layout-options>"
        return (
            f"<worksheet name={attr(self.name)}>{title}<table><view><datasources>"
            f"<datasource caption={attr(self.table)} name={attr(ds)} /><datasource name='Parameters' />"
            f"</datasources>{parameter_dependency}<datasource-dependencies datasource={attr(ds)}>"
            f"{''.join(dependency.values())}{selection}</datasource-dependencies>{filters}{sort}<slices>{slices}</slices>"
            f"<aggregation value='true' /></view><style /><panes><pane selection-relaxation-option='selection-relaxation-allow'>"
            f"<view><breakdown value='auto' /></view><mark class={attr(self.mark)} />{encodings}{style}</pane></panes>"
            f"<rows>{rows}</rows><cols>{cols}</cols></table><simple-id uuid={attr(new_id())} /></worksheet>"
        )


SHEETS = [
    Sheet('Hotel nøgletal', 'HotelTotals', rows=['period', 'adrStatus'], measures=['revenue', 'occupancyRatePercent', 'adr', 'bookedRoomNights', 'availableRoomNights']),
    Sheet('Datagrundlag', 'HotelTotals', rows=['generatedAt', 'businessDate', 'demoData', 'occupancyScope', 'satisfactionStatus']),
    Sheet('Gæster pr. land', 'HotelCountries', rows=['country'], cols=['guestStays'], mark='Bar', text='guestStays', sort='guestStays', labels=True),
    Sheet('Omsætning pr. land', 'HotelCountries', rows=['revenueRank', 'country'], cols=['revenue'], mark='Bar', text='revenue', labels=True),
    Sheet('Omsætning pr. type og sæson', 'HotelRoomTypeSeason', rows=['roomType'], cols=['season'], text='revenue'),
    Sheet('Rangliste værelsestyper', 'HotelRoomTypeRanks', rows=['revenueRank', 'roomType'], cols=['revenue'], mark='Bar', text='revenue', labels=True),
    Sheet('Bar nøgletal', 'BarTotals', rows=['employee'], measures=['revenue', 'quantity']),
    Sheet('Bar datagrundlag', 'BarTotals', rows=['generatedAt', 'demoData']),
    Sheet('Omsætning pr. drik', 'BarDrinks', rows=['category', 'drink'], cols=['revenue'], mark='Bar', text='revenue', labels=True),
    Sheet('Cocktails og kaffe', 'BarCategories', rows=['category', 'shareStatus'], measures=['quantity', 'quantitySharePercent', 'revenue', 'revenueSharePercent']),
]


def worksheet_window(sheet: Sheet) -> str:
    return (
        f"<window class='worksheet' name={attr(sheet.name)}><cards><edge name='left'><strip size='160'>"
        "<card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'>"
        "<strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip>"
        f"<strip size='31'><card type='title' /></strip></edge></cards><simple-id uuid={attr(new_id())} /></window>"
    )


class Ids:
    def __init__(self):
        self.value = 1

    def next(self) -> int:
        self.value += 1
        return self.value


def dashboard_xml(name: str, controls: list, zones: list) -> str:
    ids = Ids()
    parts = []
    width = 100000 // max(len(controls), 1)
    for position, number in enumerate(controls):
        parts.append(
            f"<zone h='7000' id='{ids.next()}' mode='compact' param='[Parameters].[Parameter {number}]' "
            f"type-v2='paramctrl' w='{width}' x='{position * width}' y='0' />")
    for sheet, x, y, w, h in zones:
        parts.append(f"<zone h='{h}' id='{ids.next()}' name={attr(sheet)} w='{w}' x='{x}' y='{y}' />")
    return (
        f"<dashboard name={attr(name)}><style /><size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' />"
        f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{''.join(parts)}</zone></zones>"
        f"<simple-id uuid={attr(new_id())} /></dashboard>"
    )


DASHBOARDS = [
    ('Hotel', [1, 2, 3, 4], [
        ('Hotel nøgletal', 0, 7000, 50000, 20000),
        ('Datagrundlag', 50000, 7000, 50000, 20000),
        ('Omsætning pr. type og sæson', 0, 27000, 50000, 30000),
        ('Rangliste værelsestyper', 50000, 27000, 50000, 30000),
        ('Omsætning pr. land', 0, 57000, 50000, 43000),
        ('Gæster pr. land', 50000, 57000, 50000, 43000),
    ]),
    ('Cocktailbar', [1, 5], [
        ('Bar nøgletal', 0, 7000, 50000, 15000),
        ('Bar datagrundlag', 50000, 7000, 50000, 15000),
        ('Cocktails og kaffe', 0, 22000, 40000, 78000),
        ('Omsætning pr. drik', 40000, 22000, 60000, 78000),
    ]),
]


def dashboard_window(name: str, zones: list) -> str:
    viewpoints = ''.join(f"<viewpoint name={attr(zone[0])}><zoom type='entire-view' /></viewpoint>" for zone in zones)
    return (f"<window class='dashboard' maximized='true' name={attr(name)}><viewpoints>{viewpoints}</viewpoints>"
            f"<active id='-1' /><simple-id uuid={attr(new_id())} /></window>")


def read_json(url: str):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def build(sources: str, api: str) -> str:
    catalogs = read_json(f'{api}/api/catalogs')
    hotel = read_json(f'{api}/api/odata/HotelTotals')['value']
    years = {row['year'] for row in hotel} | {row['year'] for row in read_json(f'{api}/api/odata/BarTotals')['value']}
    parameters, parameter_columns = parameters_xml(
        sorted(years),
        int(hotel[0]['businessDate'][:4]),
        [item['name'] for item in catalogs['countries']],
        [item['name'] for item in catalogs['roomTypes']],
        [item['name'] for item in catalogs['employees']],
    )

    def adapt_source(match):
        block = match.group(0)
        table = re.search(r"<relation connection='[^']*' name='([^']*)'", block).group(1)
        REAL_NAMES[table] = re.search(r"<datasource [^>]*name='([^']*)'", block).group(1)
        return adapted_datasource(table, block)

    workbook = re.sub(r"<datasource caption='[^']*' inline='true' name='odata\.[^']*'.*?</datasource>", adapt_source, sources, flags=re.S)
    missing = set(DATASOURCES) - set(REAL_NAMES)
    if missing:
        raise SystemExit(f'Den gemte projektmappe mangler datakilderne {sorted(missing)}')
    workbook = workbook.replace('<datasources>', '<datasources>' + parameters, 1)
    worksheets = ''.join(sheet.xml(parameter_columns) for sheet in SHEETS)
    dashboards = ''.join(dashboard_xml(*definition) for definition in DASHBOARDS)
    windows = (''.join(worksheet_window(sheet) for sheet in SHEETS)
               + ''.join(dashboard_window(name, zones) for name, _, zones in DASHBOARDS))
    workbook = re.sub(r'<worksheets>.*?</worksheets>', lambda _: f'<worksheets>{worksheets}</worksheets>\n  <dashboards>{dashboards}</dashboards>', workbook, flags=re.S)
    workbook = re.sub(r"(<windows [^>]*>).*?(</windows>)", lambda m: m.group(1) + windows + m.group(2), workbook, flags=re.S)
    return re.sub(r'\s*<thumbnails>.*?</thumbnails>', '', workbook, flags=re.S)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    api = sys.argv[3].rstrip('/') if len(sys.argv) > 3 else DEFAULT_API
    Path(sys.argv[2]).write_text(build(Path(sys.argv[1]).read_text(encoding='utf-8'), api), encoding='utf-8')
    print(f'Skrev {sys.argv[2]}')


if __name__ == '__main__':
    main()
