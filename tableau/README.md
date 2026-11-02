# Tableau-afprøvning (T002)

**Status:** Forbindelse, datatyper, pagination, manuel refresh og fejlet refresh er afprøvet i Tableau Public mod fixturen. Filtre og beløb som tekst mangler, og T002 er først færdig, når resultatskemaet nederst er udfyldt.

Prøven skal vise, om Tableau Public kan hente data fra et OData V4-API og hente nye tal ved manuel refresh. Den afgør, om vi kan bygge videre på OData-sporet fra [Plan, afsnit 7](../specs/004-hotelsystem/plan.md).

Fixturen i `fixture/` er ikke hotelbackenden. Den har ingen database eller forretningsregler. Dens tal er håndberegnede konstanter fra acceptkriterierne, så en fejl i Tableau peger på forbindelsen og ikke på en beregning.

## Start fixturen

Vælg én af disse fra projektroden:

```sh
python3 tableau/fixture/odata_fixture.py
```

```sh
docker run --rm -p 127.0.0.1:8090:8090 -e FIXTURE_HOST=0.0.0.0 -v "$PWD/tableau/fixture:/app:ro" python:3.13-slim python /app/odata_fixture.py
```

Lad terminalen stå åben. Den viser alle forespørgsler, som Tableau sender, og dem skal du bruge, hvis noget fejler.

Kontrollér i en anden terminal, at fixturen svarer:

```sh
curl -s http://localhost:8090/api/odata/
```

## Trin 1: Forbind Tableau Public

1. Åbn Tableau Public, og notér versionen under **Tableau Public → About**.
2. Vælg **OData** under **Connect → To a Server**. Du finder den muligvis under **More...**. Hvis OData ikke findes, er det et vigtigt resultat: Notér det, og stop prøven.
3. Skriv `localhost:8090/api/odata/` som server **uden** `http://`, og vælg ingen godkendelse. Med `http://` foran gør Tableau adressen til `https://http://...`, og forbindelsen fejler.
4. Træk tabellen `HotelKpis` ind, og klik på et ark. Først da hentes rækkerne, for der er ingen **Update Now**. Se dem med **Data → [datakilde] → View Data...**. Gentag med `RoomTypeSeasonRevenue` og `BarCategoryShares` som separate datakilder via **Data → New Data Source**.

Tableau opretter et udtræk.

## Trin 2: Kontrollér data og datatyper

Sammenlign med disse værdier:

**`HotelKpis`**: tre rækker. Der er flere rækker end fixturens sidestørrelse på 2, så færre end tre betyder, at Tableau ikke følger `@odata.nextLink`.

| `scenario` | `revenue` | `occupancyRatePercent` | `adr` |
|---|---:|---:|---:|
| `us8-1-two-rooms-two-nights` | 2000.00 | 50.00 | 1000.00 |
| `us8-3-no-booked-nights` | 0.00 | 0.00 | null |
| `zero-capacity` | 0.00 | null | null |

Kontrollér også:

- Beløb og procenter er tal og ikke tekst, og de har ikke mistet præcision.
- `null` vises som tom værdi og ikke som 0.
- `generatedAt` er genkendt som dato og tid. Værdien er UTC.

## Trin 3: Filtre

`RoomTypeSeasonRevenue` har tre rækker fra US7.5. Rækker med forskellig `filterKey` hører til forskellige filtervalg:

| `filterKey` | `season` | `revenue` |
|---|---|---:|
| `year=2026` | `low` | 1000.00 |
| `year=2026` | `mid` | 1000.00 |
| `year=2026;season=low` | `low` | 1000.00 |

1. Læg `filterKey` på **Filters** som et filter med én valgt værdi, og lav en visning af `revenue` pr. `season`.
2. Vælg `year=2026`. Resultatet skal være low 1000 og mid 1000.
3. Vælg `year=2026;season=low`. Resultatet skal være low 1000.
4. Notér, om filtervalget sender nye forespørgsler i terminalen. Plan forventer, at det ikke sker, fordi data ligger i et udtræk.

Denne prøve afgør, om dashboardets filtre kan bygges på færdigberegnede rækker pr. filterkombination.

## Trin 4: Manuel refresh

Lav en tabel over `BarCategoryShares` med `category`, `quantity`, `revenue`, `quantitySharePercent`, `revenueSharePercent` og `generatedAt`. Skift tilstand i en anden terminal, og gennemfør datakilde-refresh inde i Tableau efter hvert skift med **Data → [datakilde] → Refresh**.

Første tilstand er `start`. Du behøver ikke sætte den, når fixturen lige er startet.

```sh
curl -X POST http://localhost:8090/fixture/state/create
curl -X POST http://localhost:8090/fixture/state/update
curl -X POST http://localhost:8090/fixture/state/cancel
```

| Tilstand | Ændring | Cocktail: antal / DKK / antal-% / DKK-% | Kaffe: antal / DKK / antal-% / DKK-% |
|---|---|---|---|
| `start` | US9.1 | 3 / 300.00 / 60.00 / 75.00 | 2 / 100.00 / 40.00 / 25.00 |
| `create` | Oprettelse: to kaffer til 50 DKK | 3 / 300.00 / 42.86 / 60.00 | 4 / 200.00 / 57.14 / 40.00 |
| `update` | Rettelse: cocktails fra 3 til 2 | 2 / 200.00 / 33.33 / 50.00 | 4 / 200.00 / 66.67 / 50.00 |
| `cancel` | Aflysning af salget med to kaffer | 2 / 200.00 / 50.00 / 66.67 | 2 / 100.00 / 50.00 / 33.33 |

Efter hver refresh skal alle tal svare til tabellen, og `generatedAt` skal være nyere. Det viser, at data er hentet igen og ikke kun tegnet igen fra udtrækket.

## Trin 5: Fejlet refresh

1. Stop fixturen med `Ctrl+C`.
2. Gennemfør refresh i Tableau.
3. Notér fejlbeskeden, om de gamle tal bliver stående, og om `generatedAt` er uændret. Et gammelt snapshot må ikke se nyt ud.
4. Start fixturen igen, og gennemfør refresh. Fixturen starter forfra i tilstanden `start`, så tallene skal svare til første række i tabellen.

## Trin 6: Beløb som tekst

OData sender som standard `Edm.Decimal` som JSON-tal, mens Plan beskriver beløb som strenge, fx `"1000.00"`. Prøv derfor også den variant:

```sh
python3 tableau/fixture/odata_fixture.py --decimals-as-strings
```

Opret en ny forbindelse, og gentag trin 2. Notér, om felterne stadig er tal i Tableau. Resultatet bestemmer, hvordan API-feedet skal beskrives i kontrakten.

## Resultat

Udfyldes af den, der gennemfører prøven. Skriv kun det, der faktisk er observeret.

| Punkt | Resultat |
|---|---|
| Dato og udført af | 2. november 2026, gennemført af et gruppemedlem med AI-vejledning |
| Tableau Public-version og styresystem | 2026.3.0 (Apple silicon) på macOS, version læst fra appens filer |
| OData-connector findes, og forbindelsen virker | Ja, over `http` med adressen uden `http://`. Med `http://` foran fejler den med fejlkode 7C19CF64 |
| Metadata og tabeller indlæses | Ja, alle tre tabeller |
| Alle tre rækker hentes (`@odata.nextLink`) | Ja, 3 rækker. Loggen viser `HotelKpis` og derefter `HotelKpis?$skip=2` |
| Decimal som JSON-tal | Ja, felterne er tal, fx `Adr` 1,000.00 |
| Decimal som tekst | |
| `null` vises som tom værdi | Ja, vises som `Null` og ikke som 0 |
| `generatedAt` genkendes som tidsstempel | Ja, men vises i UTC uden tidszone, fx 12.38.48 mens klokken var 13.38 i Danmark |
| Filtrering med `filterKey` virker | |
| Filtrering sender nye forespørgsler | |
| Menuhandling for manuel refresh | **Data → [datakilde] → Refresh** |
| Refresh efter `create`, `update` og `cancel` giver de forventede tal | `create` er afprøvet: `Quantity` gik fra 3 og 2 til 3 og 4, og loggen viser et nyt kald. Før refresh viste Tableau stadig de gamle tal. `update` og `cancel` er ikke afprøvet |
| `generatedAt` bliver nyere ved refresh | Ja, fra 12.40.48 til 12.42.22 |
| Fejlbesked og tal ved stoppet fixture | "There was a problem connecting to the data source", fejlkode 7C19CF64. Tal og `generatedAt` bevares (3 og 4, 12.42.22) |
| Forespørgsler i terminalen, som fejlede | |
| Samlet vurdering: kan OData bruges? | |

Hvis OData ikke virker, må vi ikke skifte stiltiende til filimport eller direkte MySQL. Så skal en anden API-baseret vej afprøves, eller integrationsdesignet skal revideres med gruppen og underviseren.

## Automatisk kontrol af fixturen

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tableau/fixture -v
```

Testene viser kun, at fixturen svarer som beskrevet. De viser ikke, at Tableau kan bruge den.
