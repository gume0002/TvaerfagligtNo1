# Tableau-dashboard

**Status:** Dashboardet virker med demodata. Tallene for hotellet er sammenlignet med API'et for flere filtervalg, og tallene for baren for standardvalget. Refresh mod det rigtige system er afprøvet for bookinger, men ikke for barsalg (T054), og de 60 prøver i T055 er ikke udført.

## Åbn dashboardet

1. Start systemet med `docker compose up`.
2. Åbn `tableau/hotel-and-bar.twbx` i Tableau Public 2026.3 eller nyere.
3. Vælg fanen **Hotel** eller **Cocktailbar**, og brug dropdown-felterne øverst.

Filen indeholder et gemt udtræk med demodata. For at se data fra dit eget system skal du vælge **Data → [datakilde] → Refresh** for hver af de syv datakilder.

**Vigtigt om filen:**

- Vælg aldrig **Save to Tableau Public**. Det offentliggør projektmappen, og en publiceret version kan ikke nå det lokale API.
- Dropdowns skal bruges med pilen ▼. Det lille ✕ på et markeret felt fjerner det fra dashboardet.
- Tidspunktet **Datagrundlag (UTC)** er i UTC, altså en time eller to før dansk tid.
- Port 8080 skal være fri, eller adressen skal være `127.0.0.1`.

## Sådan hænger det sammen

Tableaus filtre kalder ikke API'et, men virker kun på det gemte udtræk. Prøven nedenfor viste, at to samtidige filtervalg lægges sammen. Derfor leverer feedet de officielle resultater for hver kombination af år, sæson, land og værelsestype, og dropdowns vælger netop én af dem. Det betyder, at Tableau ikke selv beregner nøgletal og ikke kan lægge belægning eller ADR sammen på tværs af filtervalg.

Beregningerne ligger i `backend/app/business/analytics_service.py`. Feedet i `backend/app/api/odata.py` og `backend/app/business/analytics_feed_service.py` viser kun resultaterne. Med 1.000 bookinger og 1.000 salg tog hele feedet 2,6 sekunder at hente i en måling.

## Refresh mod det rigtige system (T054)

Prøven er udført 2. november 2026 i Tableau Public 2026.3 med det færdige dashboard mod det kørende system. Tallene er sammenlignet med `GET /api/analytics/hotel` for samme filtre, og serverens log viser, at Tableau hentede data igen efter hver ændring.

| Ændring i browseren | Filter | Tableau efter refresh | Datagrundlag (UTC) |
|---|---|---|---|
| Start | Alle | Samlet 128.250,00 og 63 nætter | 13.25.33 |
| Oprettelse: én nat til 900 DKK | Alle | Samlet 129.150,00, 64 nætter og ADR 2.017,97 | 13.58.35 |
| Rettelse: prisen til 1.000 DKK | Denmark | Samlet 1.000,00, 1 nat og ADR 1.000,00 | 14.02.25 |
| Aflysning | Denmark | Samlet 0,00, 0 nætter, tom ADR og »Intet datagrundlag« | 14.03.59 |

Før refresh viste Tableau de gamle tal. Hver datakilde skal opdateres for sig, så en visning viser gamle tal, indtil dens egen datakilde er opdateret. API'et var tilbage på 128.250,00 og 63 nætter efter aflysningen, og bookingen er bevaret som aflyst.

**Mangler:** barsalg og fejlet refresh mod det rigtige system. T054 er derfor ikke afkrydset.

## Byg dashboardet igen

Tableau Public afviser en projektmappe uden udtræk, og kun Tableau kan oprette dem. Derfor sker det i to skridt:

1. I en tom projektmappe: Vælg for hver af de syv tabeller **Data → New Data Source → OData** med adressen `http://127.0.0.1:8080/api/odata/`, træk tabellen ind, og klik på et ark. Gem som `.twb`, og lad vinduet stå åbent.
2. Kør programmet, åbn resultatet, og vælg **File → Export Packaged Workbook...**:

```sh
python3 tableau/build_workbook.py <gemte datakilder.twb> <resultat.twb>
```

Tableau skriver konto- og maskine-id'er i filen. Fjern attributterne, der starter med `_.fcp.WorkbookFingerprinting`, før filen lægges i repoet, fordi repoet er offentligt.

# Tableau-afprøvning (T002)

**Status:** Forbindelse, datatyper, pagination, manuel refresh og fejlet refresh er afprøvet i Tableau Public mod fixturen. Se resultaterne nederst. To forhold mangler: `update` og `cancel` er ikke afprøvet med refresh, og kun arket med begge filtervalg er kontrolleret.

Prøven skal vise, om Tableau Public kan hente data fra et OData V4-API og hente nye tal ved manuel refresh. Den afgør, om vi kan bygge videre på OData-sporet fra [Plan, afsnit 7](../specs/004-hotelsystem/plan.md).

Fixturen i `fixture/` er ikke hotelbackenden. Den har ingen database eller forretningsregler. Dens tal er håndberegnede konstanter fra acceptkriterierne, så en fejl i Tableau peger på forbindelsen og ikke på en beregning.

### Start fixturen

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

### Trin 1: Forbind Tableau Public

1. Åbn Tableau Public, og notér versionen under **Tableau Public → About**.
2. Vælg **OData** under **Connect → To a Server**. Du finder den muligvis under **More...**. Hvis OData ikke findes, er det et vigtigt resultat: Notér det, og stop prøven.
3. Skriv adressen, og vælg ingen godkendelse. I prøven virkede `localhost:8090/api/odata/` kun **uden** `http://`, mens `http://127.0.0.1:8080/api/odata/` kun virkede **med**.
4. Træk tabellen `HotelKpis` ind, og klik på et ark. Først da hentes rækkerne, for der er ingen **Update Now**. Se dem med **Data → [datakilde] → View Data...**. Gentag med `RoomTypeSeasonRevenue` og `BarCategoryShares` som separate datakilder via **Data → New Data Source**.

Tableau opretter et udtræk.

### Trin 2: Kontrollér data og datatyper

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

### Trin 3: Filtre

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

### Trin 4: Manuel refresh

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

### Trin 5: Fejlet refresh

1. Stop fixturen med `Ctrl+C`.
2. Gennemfør refresh i Tableau.
3. Notér fejlbeskeden, om de gamle tal bliver stående, og om `generatedAt` er uændret. Et gammelt snapshot må ikke se nyt ud.
4. Start fixturen igen, og gennemfør refresh. Fixturen starter forfra i tilstanden `start`, så tallene skal svare til første række i tabellen.

### Trin 6: Beløb som tekst

OData sender som standard `Edm.Decimal` som JSON-tal, mens Plan beskriver beløb som strenge, fx `"1000.00"`. Prøv derfor også den variant:

```sh
python3 tableau/fixture/odata_fixture.py --decimals-as-strings
```

Opret en ny forbindelse, og gentag trin 2. Notér, om felterne stadig er tal i Tableau. Resultatet bestemmer, hvordan API-feedet skal beskrives i kontrakten.

### Resultat

Udfyldes af den, der gennemfører prøven. Skriv kun det, der faktisk er observeret.

| Punkt | Resultat |
|---|---|
| Dato og udført af | 2. november 2026, gennemført af et gruppemedlem med AI-vejledning |
| Tableau Public-version og styresystem | 2026.3.0 (Apple silicon) på macOS, version læst fra appens filer |
| OData-connector findes, og forbindelsen virker | Ja, over `http` med adressen uden `http://`. Med `http://` foran fejler den med fejlkode 7C19CF64 |
| Metadata og tabeller indlæses | Ja, alle tre tabeller |
| Alle tre rækker hentes (`@odata.nextLink`) | Ja, 3 rækker. Loggen viser `HotelKpis` og derefter `HotelKpis?$skip=2` |
| Decimal som JSON-tal | Ja, felterne er tal, fx `Adr` 1,000.00 |
| Decimal som tekst | Ikke afprøvet. Ikke nødvendig, fordi JSON-tal virker, og feedet bruger dem |
| `null` vises som tom værdi | Ja, vises som `Null` og ikke som 0 |
| `generatedAt` genkendes som tidsstempel | Ja, men vises i UTC uden tidszone, fx 12.38.48 mens klokken var 13.38 i Danmark |
| Filtrering med `filterKey` virker | Ja. Valgte man begge værdier, blev tallene lagt sammen: `low` 2.000. Dashboardet skal derfor tvinge præcis ét filtervalg |
| Filtrering sender nye forespørgsler | Nej. Hverken filter eller åbning af projektmappen gav nye kald i loggen, så filtre virker kun på udtrækket |
| Menuhandling for manuel refresh | **Data → [datakilde] → Refresh** |
| Refresh efter `create`, `update` og `cancel` giver de forventede tal | `create` er afprøvet: `Quantity` gik fra 3 og 2 til 3 og 4, og loggen viser et nyt kald. Før refresh viste Tableau stadig de gamle tal. `update` og `cancel` er ikke afprøvet |
| `generatedAt` bliver nyere ved refresh | Ja, fra 12.40.48 til 12.42.22 |
| Fejlbesked og tal ved stoppet fixture | "There was a problem connecting to the data source", fejlkode 7C19CF64. Tal og `generatedAt` bevares (3 og 4, 12.42.22) |
| Forespørgsler i terminalen, som fejlede | Ingen. Tableau brugte ikke `$top`, `$filter` eller andre query-parametre, kun `$skip` fra vores eget sidelink |
| Samlet vurdering: kan OData bruges? | Ja, til hentning og manuel refresh. Filtre skal bygge på færdigberegnede rækker pr. filterkombination |

Hvis OData ikke virker, må vi ikke skifte stiltiende til filimport eller direkte MySQL. Så skal en anden API-baseret vej afprøves, eller integrationsdesignet skal revideres med gruppen og underviseren.

### Automatisk kontrol af fixturen

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tableau/fixture -v
```

Testene viser kun, at fixturen svarer som beskrevet. De viser ikke, at Tableau kan bruge den.
