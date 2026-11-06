# Spørgsmål og svar til fremlæggelsen

Svarene er skrevet, så de kan siges højt. **Vis** peger på det, I kan åbne, hvis I bliver bedt om at vise det. Alle tal fra systemet er demodata.

## De 10 SWA-spørgsmål

### 1. Arkitekturdiagrammet
Systemet består af PostgreSQL, en backend med tre lag, Nginx med frontenden, Swagger UI og et engangsjob, der kører migrationer og startdata. Det hele kører i Docker. Browseren taler med Nginx, som sender `/api/` videre til backenden med REST og JSON, og kun backenden taler SQL med databasen. Tableau ligger uden for Docker og henter data gennem OData-delen af API'et. Hotellets bookingsystem er en fremtidig klient, der kan bruge samme API.

**Vis:** `README.md:73-95`, `compose.yaml:21-79`

### 2. Følg et request
Spørgsmålet nævner MySQL, men vi bruger nu PostgreSQL. Når brugeren trykker gem, laver frontenden en idempotensnøgle og sender JSON til `POST /api/bookings`. Nginx sender det videre, og API-laget kontrollerer formatet. Forretningslogikken tjekker reglerne, låser værelsestypen og tæller ledig kapacitet for hver nat. Dataadgangen gemmer bookingen og nøglen i samme transaktion, og browseren får `201` med en `Location`-header.

**Vis:** `frontend/js/app.js:160-168`, `frontend/nginx.conf:6-7`, `backend/app/api/bookings.py:46-58`, `backend/app/business/booking_service.py:136-156`, `backend/app/data_access/repositories.py:114-118`

### 3. Tre-lags arkitektur
API-laget oversætter mellem HTTP, JSON og domæneobjekter. Forretningslogikken har regler, validering og beregninger, og dataadgangen læser og skriver i databasen. Grænsen går mellem mapperne `api`, `business` og `data_access`, og en test fejler, hvis et lag importerer noget, det ikke må. Et bevidst valg er kapacitetsreglen: den ligger i forretningslogikken og ikke i SQL, så den kan testes uden database, mens selve låsen ligger i dataadgangen.

**Vis:** `backend/tests/unit/test_architecture.py:13-17`, `backend/app/business/rules.py:35`, `backend/app/data_access/repositories.py:114`

### 4. Forretningslogikkens placering
Nøgletallene beregnes i backendens forretningslogik, ikke i databasen eller Tableau. Så findes hver regel ét sted, de kan testes automatisk, og alle klienter får samme tal. Hvis vi flyttede beregningen til Tableau, skulle browseren have sin egen kopi, og tallene kunne komme til at afvige. Hvis vi flyttede den til SQL, ville den blive bundet til databasen. Tillægsopgaven viste værdien, for frontenden kunne vise tallene uden nye beregninger.

**Vis:** `backend/app/business/analytics_service.py:42-60`, `backend/app/business/analytics_service.py:103`, `backend/app/business/analytics_feed_service.py:5-6`

### 5. Udskiftelighed
Det har vi faktisk prøvet, da vi skiftede fra MySQL til PostgreSQL. API-laget blev ikke ændret, og i forretningslogikken rettede vi kun to kommentarer. Ændringerne lå i dataadgang, migration, Docker-opsætning, driver og tests. Hvis frontenden blev skiftet ud med hotellets bookingsystem, skulle det system kalde samme API, og backenden skulle ikke ændres. Det viser, at lagdelingen holder, fordi forretningslogikken kun kender en grænseflade til data.

**Vis:** `git diff --stat v1-mysql-tableau HEAD -- backend/app/api backend/app/business backend/app/data_access`, `backend/app/business/ports.py:1-5`

### 6. REST-design
Vores ressourcer er fx `bookings` og `bar-sales`, så URL'en navngiver tingen, og metoden siger, hvad der sker. `POST /api/bookings` opretter og svarer `201` med `Location`. Ugyldigt input giver `400`, en ukendt booking `404`, og manglende plads `409`. `DELETE` svarer `204` og aflyser logisk, så historikken bevares. Domænet ses også i felterne, fx `arrival`, `departure`, `countryId` og `nightlyRate`.

**Vis:** `backend/app/api/bookings.py:45-79`, `backend/app/api/errors.py:32-35`, Swagger UI på `http://127.0.0.1:8081`

### 7. API-kontrakten
OpenAPI-specifikationen er den fælles aftale og skrives før koden. Kunderne er frontenden, hotellets fremtidige bookingsystem og Tableau, som bruger OData-delen. Vi kontrollerer svarene automatisk mod kontrakten: statuskoder, headers og schemas. En anden test kontrollerer, at alle operationer i kontrakten er implementeret. Hvis kode og kontrakt ikke stemmer, fejler testen.

**Vis:** `specs/004-hotelsystem/contracts/openapi.yaml`, `backend/testsupport/contract.py:30`, `backend/tests/contract/test_api_uses_contract.py:17`

### 8. Docker og docker-compose
Containerne er `db`, `init`, `backend`, `frontend` og `swagger`. Først bliver databasen klar, hvilket `pg_isready` kontrollerer. Så kører `init` migrationer og startdata og slutter, og derefter starter backenden og til sidst frontend og Swagger. De finder hinanden ved tjenestenavn på Docker-netværket. Data ligger i volumen `postgres_data`, så de overlever `docker compose down`, men `down -v` sletter dem.

**Vis:** `compose.yaml:21-79`

### 9. Fra statisk til live data
Nye bookinger og salg kommer ind gennem API'et og ligger straks i PostgreSQL, og næste kald til API'et beregner tallene ud fra dem. Rådatafilerne bruges kun ved første start. Hotelposterne gemmes som reference, fordi de mangler datoer, og indgår ikke som aktuelle bookinger. Tableau henter data gennem et OData-feed på `/api/odata/` med syv tabeller. Tableau opdaterer dog først efter manuel refresh, og det har vi accepteret i Clarify.

**Vis:** `README.md:147-156`, `backend/app/api/odata.py:29`, `specs/004-hotelsystem/clarify.md:26`

### 10. Ejerskab og vurdering
Vi fremhæver valget af PostgreSQL. AI'en foreslog det i planen for databaseskiftet, og vi beholdt det, fordi det krævede mindst ombygning, og fordi vi kunne vise, at kun dataadgang og drift skulle ændres. Vi tog stadig selv stilling til risikoen: PostgreSQL er også relationel. Den største svaghed i produktion er manglende adgangskontrol, så alle, der kan nå API'et, kan læse og ændre data. Dertil kommer, at vi kun har én backend og én database.

**Vis:** `specs/005-tillaeg-uge-2/spec.md`, `README.md:158-161`

## Sandsynlige opfølgende spørgsmål

### Hvorfor er PostgreSQL "en anden type", når det også er relationelt?
Det er en anden database, men samme grundtype, så det er en tolkning. Vi valgte den, fordi data om bookinger og salg passer godt til tabeller, relationer og transaktioner, som vi bruger til at undgå overbooking. Hvis I mente en anden slags database, fx NoSQL, opfylder valget det ikke bogstaveligt. Vi har ikke afstemt det med jer, og det vil vi hellere sige direkte.

**Vis:** `specs/005-tillaeg-uge-2/spec.md`

### Opgaven beder om nye endpoints. Hvorfor har I ikke lavet nogen?
Fordi `/api/analytics/hotel` og `/api/analytics/bar` allerede fandtes. Beregningerne lå i backenden fra starten og ikke kun i Tableau. Vi kontrollerede, at de dækkede kravene, og det nye var analysesiden, der viser tallene. Det er kravets indhold, vi opfylder, og vi siger åbent, at vi ikke tilføjede nye endpoints i tillægsopgaven.

**Vis:** `backend/app/api/analytics.py:13-21`, `frontend/js/analytics.js:256-257`

### Hvad betyder "live" hos jer?
Databasen og API'et er altid aktuelle, og der er ingen cache. Browseren viser nye tal, når siden hentes igen eller et filter ændres. Tableau viser dem efter manuel refresh for hver datakilde, fordi Tableau Public ikke har en samlet knap. Vi havde først et mål om fem sekunder, men det blev erstattet i Clarify.

**Vis:** `specs/004-hotelsystem/clarify.md:26`, `README.md:135`

### Hvorfor viser kundetilfredshed "Intet datagrundlag"?
Opgaven nævner tilfredshed, men datasættet indeholder ingen vurderinger. Vi vil ikke opfinde et tal, så systemet viser, at der ikke er data. Det er ikke afstemt med jer, så det står som en åben risiko i vores Converge.

**Vis:** `specs/004-hotelsystem/converge.md:123`

### Hvorfor kører Tableau Public uden for Docker, når opgaven siger "alt"?
Tableau Public er et skrivebordsprogram, som vi behandler som en ekstern klient. Alt det, vi selv driver, starter med én kommando: database, backend, frontend og Swagger. Tableau henter kun data gennem API'et. Det er også en åben tolkning, som vi ikke har afstemt.

**Vis:** `.specify/memory/constitution.md:79`, `specs/004-hotelsystem/converge.md:124`

### Hvorfor er belægningen så lav i demoen?
Fordi datagrundlaget er lille. Vi regner 214 værelser i 365 dage, altså 78.110 værelsesnætter, og demoen har kun omkring 63 bookede nætter i 2026. Det giver cirka 0,08 %. Beregningen er rigtig, men demodata ligner ikke et rigtigt hotel. Hotelposterne fra rådata mangler datoer og kan derfor ikke bruges til belægning.

**Vis:** `README.md:139`, `README.md:150-151`

### Hvad er forskellen på docker compose down og down -v?
`down` fjerner containerne, men den navngivne volume bliver, så data bevares. `down -v` fjerner også volumen, så data slettes, og startdata indlæses igen ved næste start. Vi har kontrolleret i en frisk kopi, at en oprettet booking overlever en genstart.

**Vis:** `README.md:39-43`, `specs/005-tillaeg-uge-2/converge.md`

### Hvorfor er der ikke noget login, og hvad skulle ændres før produktion?
Det var et bevidst valg i en prototype, og det står i vores constitution. Før produktion skal API'et have login og roller, fx så Tableau kun kan læse. Trafikken skal også krypteres, og vi skulle kigge på drift, fordi vi kun har én backend og én database.

**Vis:** `.specify/memory/constitution.md:84`, `README.md:160-161`

### Hvad er ikke testet? (T069-T071)
Vi har ikke klikket alle filtervalg igennem i Tableau: kombinerede filtre, skift af medarbejder, andre år og salg uden data. Vi har heller ikke prøvet en afvist ændring med refresh i Tableau. Logikken er testet automatisk i API og feed, og refresh er afprøvet, men kravene står derfor som delvist opfyldt.

**Vis:** `specs/004-hotelsystem/tasks.md:155-157`, `specs/004-hotelsystem/converge.md:9`

### Har I kørt alle 60 refresh-runder? (T055)
Nej, vi har kørt 12 ud af de 60, og alle 12 gav de forventede tal. Vi valgte en stikprøve, fordi hver runde kræver manuel refresh i Tableau. Kriteriet SC-003 er derfor kun delvist opfyldt. Refresh er også afprøvet igen efter skiftet til PostgreSQL.

**Vis:** `tableau/sc003-kontrolark.md`, `tableau/README.md`

### Hvor stor en del af systemet har AI lavet, og kan I forklare det?
AI'en har skrevet meget af koden, og opgaven forventer, at vi bruger den. Vi har styret den med specifikationer, gennemgået resultatet og kontrolleret det med tests og Converge. Hver af os svarer selv for sit eget bidrag. **Tilføj jeres egne eksempler, når I har fordelt emnerne.**

**Vis:** `.specify/memory/constitution.md:156-160`

### Hvordan har I samarbejdet?
Alle ændringer efter opstarten den 26. oktober kom ind gennem pull requests fra hver sin branch. 17 af 19 mergede pull requests blev merget af en anden end den, der lavede dem. Kun tre har en formel godkendelse på GitHub, og det vil vi gøre bedre. Vi delte opgaven i milepæle og brugte fælles AI-instruktioner i `AGENTS.md`.

**Vis:** pull requests på GitHub, `AGENTS.md`

### Hvem har lavet hvad?
**Skal svares af hver enkelt.** Vi bedømmes også på commits, og fordelingen i Git er ujævn. Sig ærligt, hvad du selv har lavet, og hvordan I har arbejdet sammen. Tilskriv ikke andres arbejde til dig selv.

**Vis:** `git shortlog -sn --all --no-merges`

### Hvad gør I, hvis to prøver at booke det sidste værelse samtidig?
Forretningslogikken låser værelsestypen gennem dataadgangen, så den anden venter og derefter tæller kapaciteten igen. Den anden får `409`. Vi har en test af det, og den fejler, hvis låsen fjernes. Efter skiftet til PostgreSQL har vi kørt den 20 gange, og alle bestod.

**Vis:** `backend/tests/integration/test_booking_concurrency.py:66`, `backend/app/data_access/repositories.py:114-118`

### Hvor kan I bevise, at browser og API viser det samme?
En browsertest ændrer bevidst API'ets svar og kontrollerer, at siden viser det ændrede tal. Det viser, at siden ikke regner tallene selv. Med ægte data viser testen 400 DKK og fordelingerne 60/40 og 75/25. JavaScript beregner kun søjlernes længde.

**Vis:** `tests/browser/test_analytics_page.py:140`, `frontend/js/analytics.js:126`

## Kontrolspørgsmål til hver fremlægger

Svar uden at læse op. Hvis I kan svare på alle tre for jeres emne, er I klar.

| Emne | Kontrolspørgsmål |
|---|---|
| **Behov, Spec Kit og Converge** | 1. Hvad er forskellen på Specify, Plan og Converge? 2. Hvad skete der, hvis et krav ikke var opfyldt i Converge? 3. Hvorfor betyder det noget, at AI'en styres af specifikationer? |
| **Arkitektur og booking** | 1. Hvad må API-laget ikke indeholde? 2. Hvorfor låses værelsestypen? 3. Hvad gør idempotensnøglen, hvis svaret går tabt? |
| **REST, OpenAPI, Docker og databaseskiftet** | 1. Hvorfor giver manglende plads `409` og ikke `400`? 2. I hvilken rækkefølge starter containerne, og hvorfor? 3. Hvad måtte ændres ved databaseskiftet, og hvad var uberørt? |
| **Analyser, Tableau og demo** | 1. Hvordan beregnes belægning og ADR? 2. Hvordan kommer et tal fra databasen til Tableau? 3. Hvad betyder live hos os, og hvad er begrænsningen? |
| **Status og svagheder** | 1. Hvad er delvist opfyldt, og hvorfor? 2. Hvad er den største svaghed før produktion? 3. Hvilke to fortolkninger har vi ikke afstemt med underviserne? |
