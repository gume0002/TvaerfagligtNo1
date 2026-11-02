# Converge: Tillægsopgave uge 2

**Dato:** 2. november 2026. **Branch:** `tillaegsopgave-uge-2`. **Status:** Kørt lokalt af Mathilde og Claude. Gruppen har ikke gennemgået det endnu, og intet er pushet eller merget.

## Resultat

| Område | Status |
|---|---|
| Database | PostgreSQL 17 kører. Alle tests består |
| Analyser i API | Findes og er uændrede |
| Analyser i browser | `frontend/analytics.html` viser grafer og tabeller med tal fra API'et |
| Tableau | **Ikke afprøvet mod PostgreSQL** |
| Præsentation | **Ikke opdateret.** Beslutningen er udskudt |

## Kørte kontroller

| Kontrol | Resultat |
|---|---|
| `docker compose --profile test run --build --rm test` | 365 beståede tests, exit 0 |
| Samtidighedstest, 20 gentagelser | 20 af 20 kørsler bestået |
| `backend/testsupport/check_milestone3_mutations.py` | 5 af 5 bevidste fejl fanget |
| Bevidste fejl i dataadgang: ingen lås, søgning med store/små bogstaver, søgning uden escape, ingen låseregel | 4 af 4 fanget. Den sidste blev først fanget, efter at testen af en rigtig låsefejl var tilføjet |
| Bevidste fejl i analysesiden: gamle tal bliver stående ved fejl, medarbejder sendes ikke, andel læses fra forkert felt | 3 af 3 fanget |
| Frisk kopi af tagget `v1-mysql-tableau` fra GitHub (`d38e39b`) | Starter på MySQL 8.4. Frontend og OData svarer 200, og årets omsætning er 128.250,00 DKK |
| Frisk kopi af branchen (`8c4e7bf`) | Starter på PostgreSQL 17.11. Oprettet booking findes stadig efter `docker compose down` og ny start, og startdata indlæses ikke igen (25 bookinger og 30 drikke før og efter) |
| Swagger UI | Viser `/api/analytics/hotel` og `/api/analytics/bar` |
| Skærmbillede af analysesiden med demodata | Set på 1280 og 390 px bredde uden vandret scroll |

Prøverne med frisk kopi brugte `docker compose up --build -d`, så kommandoen kunne køre i baggrunden.

## Brugerhistorier

| Krav | Status | Bevis |
|---|---|---|
| US12.1 | Opfyldt | Frisk kopi af tagget, se ovenfor |
| US12.2 | Delvist | Arbejdet ligger på en branch. Pull request er ikke oprettet |
| US13.1–3 | Opfyldt | Felterne dækker alle krævede tal, og kontrakten er uændret i forhold til tagget. Kontrakttests består |
| US14.1–4 | Opfyldt | `tests/browser/test_analytics_page.py`, herunder 400 DKK, 60/40 % og 75/25 %. En test ændrer API-svaret og viser, at siden viser API'ets tal |
| US14.5 | Opfyldt | Browsertests af oprettet, rettet og aflyst booking samt oprettet og aflyst salg. Rettelse af salg er ikke testet i browseren |
| US14.6 | Opfyldt | Grafer og tabeller. Tabelvisningen for lande er testet i browseren, de øvrige er set i koden |
| US14.7–8 | Opfyldt | Browsertests af demomærke, tidspunkt, »Intet datagrundlag« og tabt API |
| US15.1–4 | Opfyldt | Frisk kopi, testsuite og samtidighedstest |
| US15.5 | Opfyldt | `backend/app/api/` er uændret. I `backend/app/business/` er kun to kommentarer rettet, fordi de nævnte MySQL |
| US15.6 | Opfyldt | Frisk kopi, se ovenfor |
| US15.7 | **Ikke kontrolleret** | Feedet svarer 200 og er testet automatisk, men refresh i Tableau mangler (T093) |

## Krav og succeskriterier

| Krav | Status |
|---|---|
| FR-013 | Opfyldt |
| FR-014 | Opfyldt. JavaScript beregner kun søjlernes længde ud fra API'ets værdier |
| FR-015 | Opfyldt for koden. MySQL nævnes kun i historiske dokumenter, i dokumenter om skiftet og i dette tag |
| SC-008 | Opfyldt |
| SC-009 | **Delvist.** Demoens 128.250,00 DKK og 1.663,47 DKK er ens i API og browser. Tableau mangler |
| SC-010 | Opfyldt |
| SC-011 | Opfyldt |

## Forskelle og begrænsninger

- **Accenter i søgning:** PostgreSQL ignorerer store og små bogstaver, men ikke accenter. Søgning på `Jose` finder derfor ikke `José`. MySQL-versionen fandt begge. Kravet nævner kun store og små bogstaver.
- **Demoens data:** Den lokale demo fik en ny volume, `postgres_data`, med startdata. Den gamle volume `tvaerfagligtno1_mysql_data` er ikke slettet, men bruges ikke længere.
- **Tableau-udtræk:** `tableau/hotel-and-bar.twbx` er ikke ændret og indeholder sit gemte udtræk, indtil nogen trykker refresh.
- **Mørk tilstand:** Siden har ingen mørk tilstand, ligesom resten af frontenden.
- **Tolkning af "anden type":** Risikoen står i `spec.md`, og gruppen skal kunne begrunde valget.

## Tilbage

- T074, T075: Gruppen godkender constitution, spec og plan i pull requesten.
- T093: Et gruppemedlem afprøver refresh i Tableau mod PostgreSQL.
- T096: Præsentationen opdateres, når beslutningen om den er taget.
