# Tasks: Hotelsystem

**Grundlag:** `spec.md`, `clarify.md`, `plan.md` og `.specify/memory/constitution.md`<br>
**Status:** Første task-udkast udarbejdet 29. oktober 2026. Ingen tasks er implementeret.<br>
**Prioritering:** P1 er nødvendig for prototype og aflevering; P2 er vigtig, men kan følge efter kerneforløbene.

Tasks er grupperet efter brugerhistorier og kan spores til acceptkriterierne i `spec.md`. Afkryds først en task, når den beskrevne leverance findes og dens kontrol er udført. Filstierne følger målstrukturen i `plan.md`.

## Fase 0 – Gennemgå plan og luk designporte

Disse opgaver skal udføres før de afhængige dele af implementeringen. Tableau-resultatet kan ændre integrationsdesignet; det må ikke antages at virke på forhånd.

- [ ] T001 Gennemgå Plan med gruppen, og afklar om nødvendigt med underviseren, hvordan manglende tilfredshedsdata og Tableau som ekstern klient påvirker afleveringskravet. Registrér svar og resterende risiko i `specs/004-hotelsystem/clarify.md`; brugerens accept af manuel refresh må ikke fremstilles som underviserens accept.
- [ ] T002 Afprøv den lokale Tableau Public-version med OData V4-fixture: registrér version, connector, metadata, Decimal/null/tidsstempelfelter, filtrering og manuel refresh; gem trin og resultat i `tableau/README.md`. Hvis OData ikke virker, afprøv og dokumentér en anden API-baseret vej eller revidér integrationsdesignet med gruppen/underviseren før dashboardintegration. CSV-import og direkte databaseadgang opfylder ikke kravet.
- [ ] T003 Skriv den fulde OpenAPI 3.0.3-kontrakt i `specs/004-hotelsystem/contracts/openapi.yaml` ud fra Plan og den afprøvede Tableau-feedform. Beskriv schemas, eksempler, filtre, pagination, idempotens, statuskoder, JSON-fejl, analysefelter og eventuelle OData-metadata. Gennemgå kontrakten før endpointkode påbegyndes.
- [ ] T004 Tilføj en kontraktkontrol, der validerer `openapi.yaml` og sikrer, at Swagger UI og backend bruger den versionsstyrede kontrakt frem for et konkurrerende automatisk schema.

## Fase 1 – Fælles projektfundament

Fundamentet blokerer alle brugerhistorier. Parallelmærkning gælder kun, når opgaverne kan udføres i forskellige filer uden at afhænge af hinandens ændringer.

- [ ] T005 Opret målstrukturen fra `plan.md`: `backend/app/{api,business,data_access}`, `backend/migrations`, `backend/tests/{unit,integration,contract}`, `frontend/`, `tests/browser/` og `tableau/`.
- [ ] T006 [P] Lås kompatible Python- og backendafhængigheder i `backend/requirements.lock`, inklusive FastAPI, Pydantic, SQLAlchemy, PyMySQL, Alembic og testværktøjer.
- [ ] T007 [P] Opret `backend/Dockerfile` og backendens konfiguration fra miljøvariabler; hold hemmeligheder ude af versionsstyring.
- [ ] T008 Opret `compose.yaml` med MySQL 8.4, healthcheck, navngivet `mysql_data`-volume og interne netværksnavne. Verificér at den tomme Compose-konfiguration kan starte databasen.
- [ ] T009 Opret fælles backend-opstart i `backend/app/main.py` med dependency wiring, readiness/health og ensartet JSON-fejlformat med request-id; API-laget må ikke indeholde SQL eller domæneregler.
- [ ] T010 Implementér laggrænser og en automatisk arkitekturkontrol i `backend/tests/`, så API kun kalder business, business kun kalder dataadgang, og SQLAlchemy/SQL ikke bruges uden for dataadgang.
- [ ] T011 Opret Alembic-konfiguration og første MySQL-skema i `backend/migrations/` og `backend/app/data_access/orm_models.py` for værelsestyper, lande, drikke, medarbejdere, bookinger, barsalg, referenceposter, seedmarkør og importlog.
- [ ] T012 Implementér repositories og Unit of Work i `backend/app/data_access/repositories.py` og `unit_of_work.py`, herunder transaktioner, snapshots til analyser, låsning af kapacitet og idempotensnøgler.
- [ ] T013 Implementér domæneobjekter og fælles validering i `backend/app/business/models.py`; brug Decimal for beløb og hotellets lokale dato/tid efter Plan.
- [ ] T014 Opret testprofilen `test-db` og `test` i `compose.yaml` samt samlet kommando `docker compose --profile test run --build --rm test`; tests må aldrig bruge demoens volume.
- [ ] T015 Tilføj den kontraktstyrede Swagger UI-container og API-konfiguration i `compose.yaml`; offentliggør frontend på `localhost:8080` og Swagger UI på `localhost:8081` som beskrevet i Plan.

## Fase 2 – US1: Opret booking (P1)

**Mål:** En receptionist kan oprette et gyldigt ophold, og backend afviser ugyldige eller kapacitetsoverskridende bookinger.<br>
**Selvstændig kontrol:** Opret og genlæs en booking; afvis ugyldig kapacitet/pris/dato og samtidige forsøg på sidste enhed.

- [ ] T016 Implementér bookingoprettelse og natlig kapacitetsvalidering i `backend/app/business/booking_service.py`, inklusive intervallet `[arrival, departure)` og gæsteantal pr. værelsestype.
- [ ] T017 Implementér `POST /api/bookings` i `backend/app/api/bookings.py` efter OpenAPI: valider strukturelt input, kald businesslaget, returnér 201/Location og ensartede fejl.
- [ ] T018 Implementér idempotent og atomisk bookingoprettelse i `backend/app/data_access/`, så to samtidige forespørgsler ikke kan reservere den sidste enhed.
- [ ] T019 Byg bookingformular og oprettelsesflow i `frontend/index.html` og `frontend/js/`; kald kun REST API'et, hent valgmuligheder fra katalog-API'et, vis valideringsfejl og bekræftelse. UI'et kan bygges mod fixtures, men end-to-end-kontrol afhænger af T034 og T057.
- [ ] T020 Dæk US1-kriterierne i `backend/tests/unit/`, `backend/tests/integration/` og `tests/browser/`, inklusive afrejse/ankomst samme dag og samtidighed mod MySQL.

## Fase 3 – US2: Find booking (P1)

**Mål:** Receptionisten kan finde aktive bookinger med navne- og datofiltre og vælge historik.<br>
**Selvstændig kontrol:** Kombinér søgning og datointerval, og kontrollér tomt resultat samt aflyste poster.

- [ ] T021 Implementér søgning, overlap på mindst én nat, statusfilter og pagination i `backend/app/business/booking_service.py` og bookingrepository.
- [ ] T022 Implementér `GET /api/bookings` og `GET /api/bookings/{id}` efter kontrakten i `backend/app/api/bookings.py`, inklusive synlighed af aflyste poster.
- [ ] T023 Byg bookingliste, navnesøgning, datofilter, historikfilter og tom tilstand i `frontend/`.
- [ ] T024 Dæk US2-kriterierne med API- og browserkontroller i `backend/tests/` og `tests/browser/`.

## Fase 4 – US3: Ret booking (P1)

**Mål:** Receptionisten kan rette alle bookingfelter uden at miste den eksisterende booking ved ugyldig ændring.<br>
**Selvstændig kontrol:** Ret en booking; afvis ændring der giver overbooking; kontrollér at tidligere værdier og pris består.

- [ ] T025 Implementér fuld bookingrettelse i `backend/app/business/booking_service.py`; udelad den aktuelle booking fra kapacitetstælling og bevar aftalt natpris, medmindre den ændres eksplicit.
- [ ] T026 Implementér `PUT /api/bookings/{id}` i `backend/app/api/bookings.py` med atomisk opdatering og kontraktens 400/404/409-fejl.
- [ ] T027 Tilføj redigering i bookinglisten/formularen i `frontend/`, og vis fejl uden at overskrive formularens gemte værdier.
- [ ] T028 Dæk US3-kriterierne i unit-, MySQL-integration-, kontrakt- og browserkontroller.

## Fase 5 – US4: Slet booking (P1)

**Mål:** DELETE aflyser en booking, bevarer historikken og frigiver kapacitet.<br>
**Selvstændig kontrol:** Aflys, find i historik, genbrug kapaciteten, og gentag DELETE.

- [ ] T029 Implementér idempotent logisk aflysning i `backend/app/business/booking_service.py`; aflyste bookinger udelades fra aktive opslag og analyser.
- [ ] T030 Implementér `DELETE /api/bookings/{id}` i `backend/app/api/bookings.py` med kontraktens 204/404-adfærd.
- [ ] T031 Tilføj bekræftet aflysning og opdatering af aktive/historiske visninger i `frontend/`.
- [ ] T032 Dæk US4-kriterierne, inklusive frigivet kapacitet, ingen analysebidrag og gentaget sletning.

## Fase 6 – US5: Registrer barsalg (P1)

**Mål:** Medarbejderens salg gemmes med den faktiske enhedspris og salgsdato.<br>
**Selvstændig kontrol:** Registrér tre cocktails til 100 DKK og kontrollér tre enheder/300 DKK; afvis fremtidig dato og ugyldige felter.

- [ ] T033 Implementér salgsregler i `backend/app/business/sale_service.py`: positivt heltal, kendt drik/medarbejder, positiv pris med højst to decimaler, salgsdato højst dags dato og fastfrosset salgspris.
- [ ] T034 Implementér `GET /api/catalogs` gennem alle tre lag for lande, værelsestyper, sæsonpriser, medarbejdere og drikke samt `POST /api/bar-sales` i `backend/app/api/catalogs.py` og `sales.py` efter OpenAPI.
- [ ] T035 Byg registreringsformular og salgsoversigt i `frontend/`; hent drikke og medarbejdere fra API'et.
- [ ] T036 Dæk US5-kriterierne med business-, MySQL-, kontrakt- og browserkontroller.

## Fase 7 – US6: Ret eller aflys barsalg (P2)

**Mål:** Fejl i salg kan rettes eller aflyses uden at forvride historik og analyser.<br>
**Selvstændig kontrol:** Ret mængde fra tre til to, aflys salget, og kontrollér historik/idempotens.

- [ ] T037 Implementér rettelse og logisk aflysning i `backend/app/business/sale_service.py`; aflyste salg kan hverken rettes eller genaktiveres.
- [ ] T038 Implementér `GET/PUT/DELETE /api/bar-sales/{id}` samt liste/historik i `backend/app/api/sales.py` efter kontrakten.
- [ ] T039 Tilføj redigerings-, aflysnings- og historikforløb i `frontend/`.
- [ ] T040 Dæk US6-kriterierne, herunder at ugyldig rettelse bevarer de oprindelige værdier.

## Fase 8 – US7: Hotellets omsætning og gæstelande (P1)

**Mål:** API'et leverer aktuelle, håndberegnelige hotelresultater; Tableau viser krævede fordelinger og ranglister.<br>
**Selvstændig kontrol:** Kontrollér årsskifte, sæsonskifte, gæsteophold, filtre, aflysninger og delte førstepladser mod håndberegnede resultater.

- [ ] T041 Implementér hotelomsætning i `backend/app/business/analytics_service.py` pr. overnatningsnat, kalenderår, sæson, værelsestype og land; adskil passeret, forventet og samlet omsætning.
- [ ] T042 Implementér gæsteophold pr. land, omsætning pr. type/sæson/land samt filtrerede ranglister med delte førstepladser i businesslaget.
- [ ] T043 Implementér `GET /api/analytics/hotel` i `backend/app/api/analytics.py` efter OpenAPI; alle grupper og summer skal komme fra samme datagrundlag og filtre.
- [ ] T044 Byg Tableau hotelvisninger for gæstelande, omsætning pr. type og sæson, lande, topindtjening og årstotal i `tableau/`; layout kan udvikles mod fixture, men forbind først til det godkendte API-feed efter T052–T053. Vis filtre, demo-markering og snapshot-tidspunkt.
- [ ] T045 Dæk US7 med håndberegnelige tests for årsskifte, sæsoner, skuddag, land/type/år-filtre, ranglistelighed og udeladelse af aflyste bookinger.

## Fase 9 – US8: Belægning og ekstra nøgletal (P1)

**Mål:** Hotellet viser belægning og ADR med dokumenterede nævnere samt manglende tilfredshedsgrundlag.<br>
**Selvstændig kontrol:** To værelser over to nætter med én booking på begge nætter giver 50 % belægning og 1.000 DKK ADR.

- [ ] T046 Beregn tilgængelige/bookede værelsesnætter, belægningsgrad og ADR i `backend/app/business/analytics_service.py`, opdelt på passeret/forventet/samlet og med landefilterets nævnerregel.
- [ ] T047 Tilføj nøgletal, nulgrundlag og `no_data`-status for tilfredshed til `GET /api/analytics/hotel` og Tableauvisningen; ingen opdigtet tilfredshedsscore. Tableauvisningen forbindes til API-feedet efter T052–T053.
- [ ] T048 Dæk US8 med tests for nulgrundlag, skudår, landefilter, kapacitetsnævner og historik/prognose.

## Fase 10 – US9: Helene Christines baranalyser (P1)

**Mål:** Tableau viser årets salg, omsætning pr. drik og cocktail/kaffe-fordeling efter antal og omsætning.<br>
**Selvstændig kontrol:** Tre cocktails til 100 DKK og to kaffer til 50 DKK giver 400 DKK, fem enheder, antalandele 60/40 % og omsætningsandele 75/25 %.

- [ ] T049 Implementér barens år/medarbejderfiltre, totaler, omsætning pr. navngiven drik og begge kategoriandele i `backend/app/business/analytics_service.py`.
- [ ] T050 Implementér `GET /api/analytics/bar` i `backend/app/api/analytics.py` og Tableau barvisninger med Helene Christine som standard, nulgrundlag, demo-markering og snapshot-tidspunkt. Layout kan udvikles mod fixture; feedintegration afhænger af T052–T053.
- [ ] T051 Dæk US9 med håndberegnede tests for kategoriandele, medarbejder/år, aflyste salg, nulgrundlag og katalogets 20 cocktails/10 kaffetyper.

## Fase 11 – US10: Aktuelle data i Tableau (P1)

**Mål:** Manuel datakilde-refresh henter backendens opdaterede API-data; dashboardet viser kun API-resultater og tydeligt snapshot.<br>
**Afhængighed:** T002 skal vise, at den valgte Public-forbindelse kan afprøves. Hvis ikke, skal designet revideres før denne fase fortsætter.

- [ ] T052 Implementér den API-læseprojektion, som T002 og den godkendte kontrakt har vist virker i Tableau Public (OData V4 hvis afprøvningen lykkes), i `backend/app/api/`; fladgør færdigberegnede resultater fra samme analytics-service uden SQL eller egne Tableau-regler.
- [ ] T053 Implementér feedmetadata, datatyper, filtre og paginering, så de følger `openapi.yaml` og den dokumenterede Tableau Public-afprøvning.
- [ ] T054 Afprøv fuld indlæsning/manuel refresh i Tableau efter oprettelse, rettelse og aflysning af booking og salg; kontrollér API-paritet for samme filtre, snapshot-tidspunkt og fejl ved utilgængeligt API. Dokumentér forløb og begrænsninger i `tableau/README.md`.
- [ ] T055 Gennemfør og registrér SC-003-kontrolarket med 1.000 bookinger og 1.000 salg: ti oprettelser, ti rettelser og ti aflysninger for hver ressourcetype, hver fulgt af Tableau-refresh og sammenligning med API. Registrér også afbrudt API; ingen femsekundersmåling kræves.

## Fase 12 – US11: Start og bevar prototype (P1)

**Mål:** Frisk kopi starter med én kommando, starter data én gang og bevarer ændringer ved genstart.<br>
**Selvstændig kontrol:** Følg README fra ren checkout, opret data, stop/start og kontrollér data samt Swagger UI.

- [ ] T056 Implementér katalogindlæsning og historisk rådataimport i `backend/app/business/` og `backend/app/data_access/`: bevar originalfiler, importér ikke CSV og Excel dobbelt, udelad ekstra celle E1002, rapportér de 54 erstatningstegn og ukendte værdier, og brug ikke udaterede summer som kalenderårsdata.
- [ ] T057 Implementér deterministiske, mærkede `demo-v1`-data med fast seed, kapacitetsfordeling på 214 værelser og engangskørsel gennem migrations-/init-tjenesten; gentagelse må ikke skabe dubletter eller overskrive eksisterende data.
- [ ] T058 Opret `frontend/Dockerfile`, `frontend/nginx.conf` og statiske frontendfiler, så browseren serverer UI'et og videresender `/api/` til backend.
- [ ] T059 Færdiggør afhængigheder og readiness i `compose.yaml`: MySQL healthcheck → init/migration/seed → backend; tilføj frontend/Nginx og Swagger UI. Begræns publicerede porte til localhost.
- [ ] T060 Opdatér `README.md` med faktisk arkitekturdiagram, start/stop/nulstilling, lokale adresser, data/seed, Tableau-forbindelse, kendte begrænsninger samt links til OpenAPI-kontrakten og Swagger UI; opdatér `CONTRIBUTE.md` med faktisk testkommando og reviewflow.
- [ ] T061 Verificér SC-005 fra frisk checkout med `docker compose up`, genstart med vedvarende data, seedens afbruds-/gentagelsesforløb og Swagger UI på den dokumenterede kontrakt.

## Fase 13 – Afsluttende kvalitet og Converge

- [ ] T062 Kør den samlede testkommando fra en isoleret testdatabase; kontrollér unit-, integration-, kontrakt-, arkitektur- og browsertests samt fejlretninger.
- [ ] T063 Gennemfør den manuelle to-minutters bookingprøve for SC-001 uden Swagger eller databaseværktøjer.
- [ ] T064 Kontrollér alle user story-acceptkriterier, FR-001–FR-012 og SC-001–SC-007 mod faktisk løsning; følg browser → API → business → dataadgang → MySQL for booking og analyse, og kontrollér Tableau/API-paritet.
- [ ] T065 Opret `specs/004-hotelsystem/converge.md` med status og konkret bevis/filsti for hvert acceptkriterium; angiv mangler som nye tasks, ikke som opfyldte krav.
- [ ] T066 Kontrollér `README.md`, `CONTRIBUTE.md`, OpenAPI/Swagger, arkitekturdiagram, filhenvisninger og `git diff --check`; beskriv kun faktisk udført arbejde og tilskriv ikke gruppemedlemmers bidrag til hinanden.
- [ ] T067 Sørg for, at ændringer leveres gennem branches og pull requests med et andet gruppemedlems review, og at hvert gruppemedlems faktiske bidrag kan dokumenteres med egne commits; fordel ikke arbejde eller tilskriv bidrag uden aftale.
- [ ] T068 Forbered og øv den 10-minutters projektpræsentation samt 10 minutters spørgsmål/feedback inden gruppens fremlæggelse fredag 6. november; brug fungerende demo og Converge-resultater som bevis, og aftal taleroller samt eventuel notetagning/feedbackrolle.

## Afhængigheder og leveringsrækkefølge

- T001–T003 er designporte. T001/T002 skal være afklaret, før tilfredshed og Tableau-forbindelsen kan beskrives som løst; T002 skal være afsluttet, før API-feed og Tableau-dashboardets refreshforløb fastlåses. T003 skal være gennemgået før endpointimplementering; T004 kontrollerer, at den godkendte kontrakt er styrende.
- T005–T015 er fælles fundament og blokerer stories. T006–T008 kan udføres parallelt med kontraktarbejde; databaseskema og repositories følger de godkendte entiteter og kontrakt.
- US1–US4 bygger bookingens CRUD; US5–US6 kan starte parallelt med bookingstories efter fundamentet. Booking- og salgsformularer kan udvikles mod fixtures, men skal integreres med `GET /api/catalogs` (T034) og mærkede startdata (T057) før browserens end-to-end-prøver.
- US7–US9 kræver relevante booking-/salgsdata og analytics-service, men kan udvikles med håndberegnede fixtures. Tableau-layout kan ligeledes bygges med fixtures; faktisk feedkobling afhænger af T052–T053.
- US10 afhænger af T002, T003 og analyseendpoints. Tableau-refresh må ikke godkendes på en fixture alene; SC-003 bruger den færdige løsning.
- US11's init/seed afhænger af skema og kataloger. T056–T059 leverer katalogdata, demoindlæsning og fuld Compose-opstart. README/CONTRIBUTE opdateres, når faktiske tjenester og kommandoer findes.
- T062–T068 følger implementeringen; Converge registrerer reelle resultater ja/nej/ikke afprøvet og skaber opfølgende tasks for mangler. Præsentationen skal afspejle det faktiske Converge-resultat.

## Foreslåede leveringsmilepæle

1. **Teknisk risiko afklaret:** T001–T004, herunder OpenAPI-godkendelse og dokumenteret Tableau-prøve.
2. **Brugbar MVP:** fundament samt US1–US4 og US11, så bookingforløb kan demonstreres i Docker.
3. **Aktuelle data:** US5–US6 og API-baserede bar-/hotelanalyser US7–US9.
4. **Tableau og aflevering:** US10, fuld Compose-/seedkontrol, obligatoriske tests og Converge.

Milepælene viser rækkefølge, ikke at funktionalitet allerede findes eller at arbejdet er fordelt på bestemte gruppemedlemmer.
