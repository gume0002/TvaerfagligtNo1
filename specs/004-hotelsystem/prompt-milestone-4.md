# Prompt til Milepæl 4: Tableau og aflevering

**Status:** Dette er en gemt arbejdsinstruks fra før Milepæl 4. Milepæl 4 er siden merged til `main`; brug den aktuelle [taskliste](tasks.md) som statuskilde. Prompten bevares som historik/reference og er ikke i sig selv et ubesvaret krav eller en aktuel opgave.

Kopiér kun teksten nedenfor til en ny implementeringssession, hvis gruppen bevidst genåbner dette arbejde. Prompten er en arbejdsinstruks baseret på de vedtagne dokumenter, ikke en ny kravspecifikation.

---

Du skal gennemføre **Milepæl 4: Tableau og aflevering** for Hotel Kong Arthur i vores GitHub Spec Kit-forløb. Fortsæt fra Milepæl 3; genopfind ikke løsningen eller domænereglerne. Arbejd efter Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge, og brug de eksisterende artefakter.

## Udgangspunkt og mål

Booking- og barsalgsforløbene fungerer gennem browser → REST API → business → dataadgang → MySQL. `GET /api/analytics/hotel` og `GET /api/analytics/bar` leverer de officielle, færdigberegnede nøgletal fra ét konsistent læsesnapshot pr. forespørgsel. Alle hidtil vedtagne REST-endpoints er implementeret; `NOT_IMPLEMENTED_YET` er tomt.

Milepæl 3 blev kontrolleret med 292 beståede tests, fem mutationsprøver og en automatiseret Chromium-prøve mod demoen. Dette er et tidligere observeret resultat, ikke bevis for den aktuelle checkout. Læs `specs/004-hotelsystem/milestone-3.md` og kør baselinetesten igen.

Målet er at levere de manglende Tableau-visninger og det afprøvede API-feed, dokumentere manuel datakilde-refresh og gennemføre den afsluttende kravkontrol. Fungerende REST-analyser er ikke i sig selv bevis for fungerende Tableau.

## Omfang og afhængigheder

- Afklar de åbne designporte **T001 og T002** med de nødvendige personer og den faktiske lokale Tableau Public-version. Færdiggør derefter den manglende feed-del af **T003** med gennemgået kontrakt før endpointkode.
- Implementér **T052–T053** efter den dokumenterede connectorprøve og det godkendte integrationsdesign.
- Færdiggør **T044** samt Tableau-delene af **T047 og T050**. API-delene af disse tasks er allerede implementeret.
- Gennemfør **T054–T055**, herunder US10 og SC-003, mod den rigtige backend og en faktisk Tableau-workbook.
- Gennemfør **T062–T068** i det omfang, de kan udføres og bevises. Menneskelige acceptprøver, review, ejerskab og øvning forbliver åbne, indtil de rette personer faktisk har udført dem.
- Genkontrollér US11/Compose/seed og eksisterende T056–T061, hvor integrationen påvirker dem. Genimplementér ikke allerede færdige tasks uden et konkret fund.

Respektér afhængigheder frem for at bruge tasknummeret som begrundelse for at springe designportene over. Du må forberede uafhængig dokumentation og kontroller, mens en menneskelig afklaring afventes; implementér ikke det afhængige feed på en antagelse.

## Før du ændrer noget

1. Kør `git status --short --branch`. Stop ved et urent arbejdstræ, og beskriv ændringerne; overskriv eller stash dem ikke.
2. Hent status fra `origin`, og kontrollér, at opdateret `main` indeholder den gennemgåede Milepæl 3. Hvis den ikke er merged, stop og bed om afklaring; merge den ikke selv.
3. Opret `milepael-4-tableau-aflevering` fra opdateret `main`. Arbejd aldrig direkte på `main`.
4. Kontrollér `git config user.name`, og brug brugerens eksisterende forfatterkonfiguration. Tilskriv ikke gruppemedlemmer bidrag uden belæg.
5. Kør `docker compose --profile test run --build --rm test`, og registrér exitkode og resultat. Ret ikke en ukendt baselinefejl ved at svække eller springe tests over.
6. Registrér eksisterende containere og volumes før egne opstarter, så oprydning kan ske uden datatab.

## Læs før implementering

Ved konflikt går den øverste kilde forud:

1. `opgavebeskrivelse/E26 Tværfaglig Opgave Hotel Kong Arthur.pdf` og `opgavebeskrivelse/Tillægsspørgsmål_swa.pdf`.
2. `.specify/memory/constitution.md`.
3. `specs/004-hotelsystem/spec.md` og de godkendte afklaringer i `clarify.md`.
4. `specs/004-hotelsystem/plan.md`, især afsnit 5–7 og 11–12.
5. `specs/004-hotelsystem/contracts/openapi.yaml`.
6. `specs/004-hotelsystem/tasks.md`.

Læs også `AGENTS.md`, `project-skills/hotel-architecture-review/SKILL.md`, `README.md`, `CONTRIBUTE.md`, `specs/004-hotelsystem/milestone-3.md`, `tableau/README.md` samt fixturen og testene i `tableau/fixture/`.

Følg den faktiske implementering i:

- `backend/app/business/analytics_service.py`, `models.py`, `ports.py`, `rules.py`, `booking_service.py` og `sale_service.py`.
- `backend/app/api/analytics.py`, `schemas.py`, `errors.py` og wiring i `backend/app/main.py`.
- `backend/app/data_access/repositories.py`, `unit_of_work.py` og `database.py`.
- `backend/tests/integration/test_analytics_api.py`, `test_analytics_snapshot.py`, `test_sales_api.py` og `test_booking_concurrency.py`.
- `backend/tests/unit/test_analytics_rules.py`, `test_architecture.py`, `backend/tests/contract/` og `backend/testsupport/contract.py`.
- `backend/testsupport/check_milestone3_mutations.py`, `smoke_milestone3.py`, `compose.yaml` og frontendens booking-/salgsforløb.

Opsummér kort scope, åbne afhængigheder og acceptkriterier før kodeændringer. Fortsæt derefter selvstændigt, medmindre en stopregel gælder.

## Faste beslutninger

- Bevar Python/FastAPI, SQLAlchemy/PyMySQL, MySQL og de tre backendlag. SQL og SQLAlchemy findes kun i dataadgangen. Arkitekturtesten må ikke svækkes.
- Alle officielle nøgletal beregnes i `business/analytics_service.py`. Feedet må kun projicere/formate disse resultater; ingen nye formler i SQL, frontend, connector eller Tableau.
- Bevar in-memory-beregning uden cache eller rapporttabeller. Hver analyse skal stadig bruge et konsistent snapshot; skrivetransaktionerne forbliver `READ COMMITTED`.
- Brug Decimal til beløb. Den eksisterende REST-kontrakt leverer beløb og procenter som strenge med to decimaler. En eventuel protokolmapping til OData skal afprøves og beskrives før implementering; ændr ikke stiltiende REST-svarene.
- Bookingomsætning fordeles pr. overnatningsnat i `[arrival, departure)`. Aflyste bookinger og salg udelades helt. Aftalte priser fastholdes.
- Dagsgrænser følger Europe/Copenhagen. `past` er nætter før dags dato; dags dato og senere er `upcoming`. Tests bruger `FrozenClock` fra `conftest.py`.
- Gæsteophold tælles én gang pr. inkluderet booking. Landefilter ændrer ikke kapacitetsnævneren. Belægning og ADR må ikke summeres eller gennemsnitsberegnes på tværs af forskellige filtergrundlag i Tableau.
- Ranglister følger den godkendte konkurrenceplacering: 3.000, 3.000 og 2.000 DKK giver `rank` 1, 1 og 3.
- `byDrink` indeholder alle katalogets drikke, også dem uden salg. `byCategory` indeholder altid cocktail og coffee. Helene Christine er standard i baranalysen.
- Ved nul nævner er forholdstallet `null` med `no_data`; summer er nul. Tilfredshed har kun status `no_data`, aldrig en opdigtet score.
- Katalogets værelsesfordeling og aktive demodata skal mærkes som demodata; råfiler er ikke dokumenteret hotelhistorik og ændres aldrig.
- Tableau Public er valgt. Manuel datakilde-refresh inde i Tableau er accepteret; der gælder intet femsekunderskrav. En sidegenindlæsning eller et gammelt udtræk er ikke bevis for nye API-data.
- Ingen nye licenskøb, loginløsninger, offentlig eksponering eller alternativ teknologistak som genvej til forbindelsen.

## Tableau-designporten: gør dette først

Følg T002 og den eksisterende prøvevejledning. Registrér faktisk Public-version, styresystem, tilgængelig connector, metadata, Decimal-mapping, null, tidsstempler, pagination og den konkrete menuhandling for manuel refresh. Skeln mellem fixturens automatiske tests og observationer i Tableau. Om nødvendigt verificeres connectorens aktuelle forudsætninger i officielle kilder; dokumentation alene er ikke en gennemført prøve.

Vis, om filtervalg sender nye API-kald eller kun filtrerer et udtræk. Fastlæg ikke en løsning med dynamiske API-filtre, hvis appen ikke udfører dem. Hvis den afprøvede løsning bruger færdigberegnede filterkombinationer, skal præcis én relevant kombination vælges, og rækker fra forskellige grundlag må ikke lægges sammen.

OData V4 er en kandidat, ikke en bevist forbindelse. Hvis connectoren mangler eller refresh fejler, dokumentér den konkrete fejl og stop afhængig implementering. Skift ikke stiltiende til CSV/Excel-import, direkte MySQL eller en anden klient. En anden API-baseret løsning eller ændring af Plan/kontrakt kræver afklaring og godkendelse før kode.

Når prøven og integrationsdesignet er bekræftet, udarbejd det konkrete feedkontraktudsnit med felter, datatyper, nøgler, filtre, metadata, pagination, tidsstempler og fejl. Forelæg den reviewbare kontrakt før nye endpoints implementeres. Bevar den eksisterende REST-kontrakt og dens kontroller.

## Implementering og kontroller

Tag én task ad gangen, skriv relevante tests sammen med koden, og commit med tasknummer i beskeden. Afkryds først efter en eksisterende leverance og faktisk udført kontrol. Delvise tasks får noter; allerede godkendte API-dele må ikke nulstilles eller fejlagtigt genrapporteres som nye bidrag.

Tableau skal vise hotellets gæstelande, omsætning pr. type opdelt på sæson, pr. land, ranglister, årstotaler, historik/prognose, belægning og ADR samt barens årstotal, omsætning pr. navngiven drik og begge kategoriandele. Vis aktive filtre, demomarkering, manglende datagrundlag og datagrundlagets tidspunkt. Brug ikke render-/refresh-tid som et falsk nyt snapshot-tidspunkt.

Sammenlign Tableau og API med præcis samme data og filtre. Genbrug de håndberegnede eksempler fra US7–US9: årsskifte 2.000/1.000 DKK, sæsonskifte 1.000/1.000 DKK, to gæster/tre nætter, delte førstepladser, 50 %-eksemplet, skudår, nulgrundlag og barens 400 DKK med 60/40 % og 75/25 %. Bevis korrekt nævner og gæsteoptælling ved filtrering. Test feedprojektionens paritet med analytics-servicen; beregn ikke forventninger med de samme produktionsfunktioner.

For US10 skal oprettelse, rettelse og aflysning af både booking og salg blive synlig efter manuel datakilde-refresh. En afvist ændring må ikke ændre tallene. Ved utilgængeligt API skal Tableau give en forståelig fejl og bevare det gamle snapshots tidspunkt. Et fejlet refresh må ikke godkendes som aktuelt.

For T055/SC-003 bruges et isoleret, kontrolleret datagrundlag med 1.000 bookinger og 1.000 salg. Gennemfør ti oprettelser, ti rettelser og ti aflysninger for hver ressourcetype: **60 ændringer med hver sin Tableau-refresh og API-sammenligning**, plus fejlprøven ved afbrudt API. Registrér forventet/faktisk værdi, filtre, snapshot-tidspunkt og refresh-resultat i et kontrolark. Overhold kapacitet og salgsdatoer. Overskriv ikke demoens eksisterende volume eller ændr `demo-v1` for at fremstille prøvedata. En fixture, en API-test eller et genereret kontrolark alene er ikke en gennemført SC-003-prøve.

Færdiggør `README.md`, `CONTRIBUTE.md`, OpenAPI, `tableau/README.md` og de faktiske workbook-/feedartefakter i samme branch. Opret `specs/004-hotelsystem/converge.md` med en række pr. nummereret acceptkriterium, FR-001–FR-012 og SC-001–SC-007, status og konkret bevis/filsti. Opret konkrete opfølgende tasks for fund; markér ikke mangler som bestået.

## Stopregler og menneskelig kontrol

Stop afhængigt arbejde og stil ét præcist spørgsmål, når dokumenter er i konflikt, en manglende regel ændrer adfærd/tal/kontrakt, en plan-/spec-/kontraktændring behøves, eller en nødvendig menneskelig handling mangler. Gæt ikke forretningsregler.

Du må ikke selv erklære T001/T002, underviseraccept, en menneskelig Tableau-prøve, T063, andre medlemmers review eller T068's øvning bestået. Hjælp med forberedelse og dokumentér faktisk observerede trin, men kræv de relevante personers resultat/bekræftelse før godkendelse. En automatiseret browserprøve erstatter ikke testpersonens to-minuttersprøve. T067 er ikke afsluttet alene ved at oprette en PR; et andet gruppemedlems review skal faktisk foreligge.

Hvis en app eller forbindelse ikke kan tilgås, angiv præcis hvilken prøve der ikke kunne gennemføres. Fortsæt kun med uafhængigt arbejde; foregiv ikke workbook, refresh, tilladelse eller gruppens ejerskab. Beskriv aldrig brugerens accept som underviserens accept.

## Inden du afslutter

1. Kør `docker compose --profile test run --build --rm test` og registrér resultat/exitkode. Bevar eksisterende tests; ingen sletning, svækkelse eller skjulte skips for at opnå grønt.
2. Gentag relevante mutationskontroller, og tilføj meningsfuld negativ kontrol af nye feed-/paritetsregler, så en tom testløkke eller et ikke-kontrolleret svar ikke kan bestå.
3. Afprøv fuld Compose-opstart, Swagger, booking-/salgsbrowserforløb, begge analyser og den faktisk understøttede Tableau-refresh. Brug et særskilt disponibelt miljø til frisk-start-/seedprøven; slet ikke eksisterende volumes.
4. Kør `git diff --check`, kontrollér dokumentationslinks og gennemgå browser → API → business → dataadgang → MySQL med konkrete filstier. Sammenlign faktisk API-adfærd med kontrakten.
5. Stop egne prøvecontainere bagefter; bevar data og brugerens eksisterende miljø. Registrér, hvad du har efterladt.

Afslut med færdige/delvise/ikke påbegyndte tasks, acceptkriterier med testbeviser, faktisk kørte kommandoer, ikke afprøvede dele, afvigelser og resterende handlinger. Giv en dansk PR-tekst og en kort forklaring af lagansvar, snapshot, filtergrundlag, belægning, ADR, omsætning, API/Tableau-paritet og begrænsninger. Forbind forklaringen til de ti SWA-spørgsmål, især 4 om beregningernes placering og 9 om aktuelle data.

Push, opret eller merge ikke en PR uden en særskilt anmodning. Stop efter denne milepæl og afvent gruppens gennemgang; erklær kun hele opgaven færdig, hvis alle krævede beviser og menneskelige godkendelser faktisk foreligger.
