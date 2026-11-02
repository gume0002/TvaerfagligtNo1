# Plan: Tillægsopgave uge 2

**Dato:** 2. november 2026. **Grundlag:** [spec.md](spec.md), [constitution](../../.specify/memory/constitution.md) og [planen for hotelsystemet](../004-hotelsystem/plan.md).

**Status:** Forslag til gruppens gennemgang. Intet af det nye er implementeret eller afprøvet.

## Hvad ændrer sig ikke?

Tre lag, REST/JSON, kontrakt, forretningsregler, frontend, OData-feed og Tableau-dashboard bevares. Analyse-endpoints findes allerede, fordi alle nøgletal beregnes i forretningslogikken og ikke i Tableau. Tillægsopgaven er derfor også en prøve på valget i constitution, princip III.

## Hvordan vises analyserne i frontenden?

| Del | Valg |
|---|---|
| Side | `frontend/analytics.html` og `frontend/js/analytics.js`, med link fra bookingsiden og salgssiden |
| Data | Nye funktioner i `frontend/js/api.js` kalder `GET /api/analytics/hotel`, `GET /api/analytics/bar` og `GET /api/catalogs` |
| Filtre | År, sæson, land, værelsestype og medarbejder. Hvert valg giver et nyt kald til API'et |
| Visning | Tabeller med API'ets værdier. `null` med status `no_data` vises som »Intet datagrundlag« |
| Regel | Siden formaterer kun tal og laver ingen beregninger |

Kontrakten skal kun ændres, hvis gennemgangen finder et manglende felt.

## Hvordan skiftes databasen?

| Del | Ændring |
|---|---|
| Database | `postgres` med fast version og digest i `compose.yaml`, navngivet volume `postgres_data` og healthcheck med `pg_isready` |
| Driver | `psycopg[binary]` i stedet for `pymysql` og `cryptography`. `requirements.lock` opdateres |
| `database.py` | Forbindelsesadressen ændres til `postgresql+psycopg`. `READ COMMITTED` bevares |
| `unit_of_work.py` | Fejl oversættes fra MySQL-numre til PostgreSQL-koder: `40P01` (deadlock), `55P03` (lås) og `40001` (serialisering). Snapshot bruger `REPEATABLE READ, READ ONLY` |
| `orm_models.py` | MySQL-indstillinger for tabeller fjernes |
| `repositories.py` | `contains` bliver til `icontains`, så navnesøgning fortsat ignorerer store og små bogstaver |
| Migration | `0001_initial_schema.py` rettes, da databasen er ny og ingen data skal flyttes |
| Tests | `conftest.py` tømmer tabeller med `TRUNCATE ... RESTART IDENTITY CASCADE`, og MySQL-specifikke tests rettes |

**Må ikke ændres uden begrundelse:** `backend/app/api/` og `backend/app/business/`. Hvis databaseskiftet kræver ændringer dér, er det et fund om lagdelingen, som skal stå i pull requesten.

## Risici

| Risiko | Håndtering |
|---|---|
| **Låse:** `FOR UPDATE` må ikke ramme den ydre del af en `LEFT JOIN` i PostgreSQL | `with_for_update(of=BookingRow)` bruges allerede. Samtidighedstestene kører igen |
| **Sortering og søgning:** MySQL's sammenligning ignorerede også accenter | `spec.md` kræver kun store og små bogstaver. Forskellen dokumenteres |
| **Decimaler og JSON:** typerne kan opføre sig anderledes | Skematest og håndberegnede tests kører igen |
| **Sekvenser:** id-rækkefølge kan afvige fra MySQL | Tests bruger ikke faste id'er, og Tableau bruger navne |
| **Tableau:** filen indeholder et gemt udtræk | Adressen er uændret. Refresh afprøves igen af et gruppemedlem |
| **Tolkning af "anden type"** | Står som tolkningsrisiko i `spec.md`, og begrundelsen skal med i præsentationen |

## Hvordan kontrolleres det?

| Krav | Bevis |
|---|---|
| US12, SC-008 | Tagget hentes i en frisk kopi og startes |
| US13 | Kontrakttests og sammenligning med opgavens liste |
| US14 | Browsertests med håndberegnede tal og fejl ved utilgængeligt API |
| US15, SC-010, SC-011 | Samlet testkommando, samtidighedstest, bevidste fejl og frisk kopi |
| SC-009 | Samme filtre i API, browserfront og Tableau. Tableau afprøves af et gruppemedlem |

## Rækkefølge

1. Gruppen godkender constitution, spec og plan.
2. Databaseskiftet laves først, så frontendsiden afprøves mod den endelige database.
3. Frontendsiden laves derefter. De to dele kan også laves samtidig af to personer, da de ikke rører de samme filer.
4. Dokumentation og Converge opdateres til sidst, og `tableau/README.md` får resultatet af den nye prøve.
