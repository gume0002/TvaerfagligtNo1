# Constitution for Hotel Kong Arthur

Denne constitution fastlægger de principper og rammer, der gælder for hele projektet. Den bygger på opgaveformuleringen (`opgavebeskrivelse/E26 Tværfaglig Opgave Hotel Kong Arthur.pdf`), SWA-tillægsspørgsmålene (`opgavebeskrivelse/Tillægsspørgsmål_swa.pdf`) og gruppens beslutninger.

Constitution indeholder kun principper og faste rammer. Konkrete domænedefinitioner afgøres i Specify og Clarify, fx hvilket niveau af "live" vi vælger, hvornår sæsonerne er, og hvordan belægningsgraden beregnes. Teknologivalg som programmeringssprog og framework afgøres i Plan.

## Kerneprincipper

### I. Spec-drevet udvikling

Projektet følger GitHub Spec Kit: Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge.

- Vi beskriver, *hvad* systemet skal gøre, før der skrives kode.
- User stories skrives i formatet "Som <rolle> ønsker jeg <mål>, så <værdi>", følger INVEST og har acceptkriterier.
- En user story er først færdig, når dens acceptkriterier er kontrolleret i Converge. Mangler bliver til nye tasks.

### II. Streng 3-lagsarkitektur

Backenden består af tre lag med hvert sit ansvar:

1. **Præsentationslag (REST API):** Modtager HTTP-forespørgsler, oversætter mellem JSON og domæneobjekter og returnerer statuskoder. Indeholder ingen forretningsregler og ingen databasekode.
2. **Forretningslogik:** Indeholder forretningsregler, validering og beregning af nøgletal.
3. **Dataadgang:** Læser og skriver data i MySQL. SQL og databasespecifik kode findes kun her.

Hvert lag må kun kalde laget lige under sig. Der er ingen genveje, heller ikke ved simple opslag. Hvis databasen skiftes ud, skal kun dataadgangslaget ændres. Hvis frontenden skiftes ud med hotellets eget bookingsystem, skal backenden ikke ændres.

### III. Backenden ejer nøgletallene

De officielle nøgletal beregnes i forretningslogikken og leveres via API'et. Det gælder fx omsætning, belægningsgrad og barens salg.

- Tableau må visualisere, filtrere og aggregere tallene, men må ikke indeholde forretningsregler.
- Alle klienter får dermed de samme tal for de samme data.

### IV. Contract-first API

- API'et bruger REST og JSON.
- OpenAPI-specifikationen skrives og godkendes, før et endpoint implementeres. Koden skal følge kontrakten, ikke omvendt.
- Kontrakten er den fælles aftale med alle klienter: bookingfrontenden, Tableau og hotellets fremtidige bookingsystem.
- Swagger UI kører i Docker og viser den gældende kontrakt.
- Hvis koden og kontrakten ikke stemmer overens, er det en fejl, der skal rettes.

### V. MySQL er den eneste sandhed

- Alle driftsdata, både for hotellet og baren, ligger i MySQL.
- CSV/Excel-filerne bruges kun som startdata, der indlæses automatisk, når databasen er tom. De genindlæses ikke senere.
- Alle ændringer sker via REST API'et. Ingen klient må skrive direkte til databasen.
- Data bevares på tværs af genstarter via en navngivet Docker-volume. Data nulstilles kun bevidst, fx med `docker compose down -v`.

### VI. Backenden håndhæver forretningsreglerne

- Forretningslogikken validerer alle forespørgsler, uanset hvilken klient der kalder.
- Ugyldige forespørgsler afvises med passende HTTP-statuskoder, fx 400, 404 eller 409, og en ensartet JSON-fejl.
- Validering i frontenden er kun en hjælp til brugeren og erstatter ikke backendens validering.

### VII. Forretningslogikken testes automatisk

- Nøgletalsberegninger og forretningsregler dækkes af automatiske tests.
- Testene kan køres med én kommando og bruges som bevis for acceptkriterierne i Converge.

### VIII. Ét kommando-opstart

- Hele systemet starter fra en frisk `git clone` med kun `docker compose up`.
- Der må ikke kræves andre lokale installationer end Docker og ingen manuelle trin.
- Startdata indlæses automatisk, og backenden venter på, at MySQL er klar.

## Systemets grænser

### Dette er "hele systemet"

Følgende tjenester kører i Docker og starter med `docker compose up`:

- MySQL
- Backend (REST API med tre lag)
- Swagger UI
- Bookingfrontend i browseren, hvor bookinger kan oprettes, redigeres og slettes

### Eksterne klienter

- **Tableau** kører uden for Docker. Tableau er en ekstern klient, der kun henter data via REST API'et og aldrig direkte fra MySQL.
- **Hotellets eget bookingsystem** skal på sigt kunne skrive til API'et med POST, PUT og DELETE på samme måde som bookingfrontenden.

### Erkendte begrænsninger

- **Ingen adgangskontrol:** Prototypen har bevidst ingen login eller adgangskontrol. Alle, der kan nå API'et, kan læse og ændre data. Det skal løses, før systemet kan gå i produktion.

## Opgavens faste krav

Følgende krav kommer fra opgaveformuleringen og er ikke til forhandling.

### Teknologi

- Backend med 3-lagsarkitektur og REST API med JSON.
- API-kontrakten leveres som OpenAPI-specifikation og vises i Swagger UI.
- Databasen er MySQL.
- Alt kører i Docker og startes med Docker Compose.
- Programmeringssproget er frit og vælges i Plan.

### Funktionalitet

- Systemet skal løbende kunne opdatere data og vise aktuelle data, ikke kun historiske CSV-data.
- En frontend i browseren skal kunne oprette, redigere og slette bookinger via backenden.

### Hotellets dashboard i Tableau

Med udgangspunkt i backendens REST API skal dashboardet vise:

- Hvilke lande gæsterne kommer fra.
- Omsætning pr. værelsestype pr. sæson og pr. land.
- Hvilke værelsestyper og lande hotellet tjener flest penge på.
- Årets samlede omsætning.
- Mindst ét ekstra nøgletal, som gruppen selv vælger.

### Cocktailbaren i Tableau

- Helene Christines samlede salg for året.
- Omsætning pr. drink.
- Procentfordelingen mellem cocktails og kaffe for Helene Christine.

### Domænerammer fra opgaven

- Hotellet har 214 værelser fordelt på 8 værelsestyper med 1–4 personer pr. værelse.
- Værelsespriserne i opgaven er estimater, der varierer med sæsonen.
- Helene Christine laver 20 forskellige cocktails og 10 forskellige kaffetyper.

### Aflevering

- Spec-artefakter i `specs/`: constitution, spec, plan og tasks.
- User stories med acceptkriterier.
- Resultatet af det sidste Converge-tjek: hvad er implementeret, og hvad mangler.
- Kildekode i GitHub, hvor alle gruppemedlemmer har bidraget med commits.
- `README.md` med et arkitekturdiagram over hele systemet, `CONTRIBUTE.md` og Swagger UI kørende i Docker.

## Udviklingsproces

### Git og pull requests

- Alle ændringer laves på en branch og lægges ind i `main` via en pull request.
- Mindst ét andet gruppemedlem skal gennemgå og godkende pull requesten. Der pushes ikke direkte til `main`.

### Dokumentation følger koden

En pull request kan først godkendes, når den berørte dokumentation er opdateret i samme pull request. Det gælder:

- OpenAPI-kontrakten.
- `README.md` med arkitekturdiagrammet.
- `CONTRIBUTE.md`.

Beslutninger dokumenteres i spec, plan og pull requests. Der føres ingen særskilt beslutningslog.

### Sprog

- Dokumentation skrives på dansk: spec, plan, tasks, `README.md` og `CONTRIBUTE.md`.
- Kode, API-endpoints, JSON-felter og databasenavne skrives på engelsk, fx `/bookings` og `roomType`.

### Brug af AI og ejerskab

- Vi bruger AI til at løse opgaven, men gruppen gennemgår alt, AI'en laver.
- Alle i gruppen skal kunne forklare og vurdere det afleverede.
- Hvert gruppemedlem står inde for sit eget bidrag. Ingen tilskriver sig andres arbejde.

## Styring

- Constitution går forud for andre arbejdsaftaler i projektet. Opgavens faste krav går forud for tekniske bekvemmelighedshensyn.
- Ændringer i constitution laves som en almindelig pull request med én godkendelse. Pull requesten skal begrunde ændringen og tælle versionsnummeret op.
- I Converge sammenholdes løsningen med constitution, spec, plan, tasks og acceptkriterier.

**Version:** 1.0.0 · **Vedtaget:** Afventer godkendelse af pull request · **Senest ændret:** 26. oktober 2026
