# Tasks: Tillægsopgave uge 2

**Grundlag:** [spec.md](spec.md) og [plan.md](plan.md). Numrene fortsætter fra [hotelsystemets tasks](../004-hotelsystem/tasks.md).

Afkryds først en task, når leverancen findes, og kontrollen faktisk er kørt.

## Fase 0 – Sikring og grundlag

- [x] T072 Sæt tagget `v1-mysql-tableau` på `main` og push det (US12). Tagget peger på `d38e39b`.
- [x] T073 Hent tagget i en frisk kopi, start systemet, og kontrollér, at det er den forventede version (SC-008).
- [x] T074 Opdatér constitution til version 1.1.0 og projektets retningslinjer med PostgreSQL. Gruppen godkender i en PR.
- [ ] T075 Gruppen gennemgår `spec.md` og `plan.md` og tager stilling til de åbne punkter.

## Fase 1 – US15: Skift database

- [x] T076 Skift `db` og `test-db` til PostgreSQL i `compose.yaml` med fast version, digest, healthcheck og `postgres_data`.
- [x] T077 Skift driver i `requirements.in`, og opdatér `requirements.lock`.
- [x] T078 Tilpas `database.py`, `orm_models.py` og migrationen til PostgreSQL.
- [x] T079 Tilpas fejloversættelse og analysesnapshot i `unit_of_work.py`.
- [x] T080 Tilpas navnesøgningen i `repositories.py`, så store og små bogstaver stadig ignoreres.
- [x] T081 Tilpas `conftest.py` og MySQL-specifikke tests. Testene må ikke svækkes.
- [x] T082 Kør alle tests, de bevidste fejl og 20 gentagelser af samtidighedstesten mod PostgreSQL (SC-010).
- [x] T083 Kontrollér, at `backend/app/api/` og `backend/app/business/` er uændrede, eller begrund ændringerne.
- [x] T084 Start systemet fra en frisk kopi, opret data, og kontrollér, at de overlever en genstart (SC-011).

## Fase 2 – US13: Analyser i API'et

- [x] T085 Sammenlign `GET /api/analytics/hotel` og `/bar` med alle krav i opgaven og `spec.md`. Tilføj kun manglende felter, og opdatér kontrakten først.
- [x] T086 Kontrollér endpoints i Swagger UI.

## Fase 3 – US14: Analyser i browseren

- [x] T087 Tilføj funktioner til `frontend/js/api.js`, der henter hotel- og baranalyser.
- [x] T088 Byg `frontend/analytics.html` og `frontend/js/analytics.js` med filtre og hotelvisninger som grafer og tabeller.
- [x] T089 Tilføj barens visninger som grafer og tabeller: årets salg, omsætning pr. drik og begge kategoriandele.
- [x] T090 Vis datagrundlagets tidspunkt, »Demodata«, »Intet datagrundlag« og fejl ved utilgængeligt API.
- [x] T091 Tilføj links fra bookingsiden og salgssiden, og tilpas `frontend/Dockerfile`, hvis det er nødvendigt.
- [x] T092 Dæk US14 inkl. grafer og tabelvisning med browsertests, herunder 400 DKK og andelene 60/40 % og 75/25 % samt nye tal efter en ændring.

## Fase 4 – Tableau, dokumentation og Converge

- [x] T093 Et gruppemedlem afprøver refresh i Tableau mod PostgreSQL og sammenligner med API og browserfront (US15.7, SC-009).
- [x] T094 Opdatér `README.md` med diagram, `CONTRIBUTE.md`, `tableau/README.md` og `specs/README.md`.
- [x] T095 Opret `specs/005-tillaeg-uge-2/converge.md` med status og bevis for US12–US15, FR-013–FR-015 og SC-008–SC-011. Mangler bliver til nye tasks.
- [ ] T096 Opdatér præsentationen, så den forklarer valget af PostgreSQL, hvad skiftet ændrede, og svaret på SWA-spørgsmål 5.

## Forslag til fordeling

Faserne 1 og 3 rører ikke de samme filer og kan laves af hver sin person. Fase 2 og 4 kan laves af en tredje. Det er kun et forslag, og gruppen fordeler selv arbejdet.
