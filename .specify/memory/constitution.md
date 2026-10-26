# Grundprincipper for Hotel Kong Arthur

**Status: Udkast til gruppens gennemgang.** Her er opgavens faste krav samlet i nogle principper for projektet. Gruppen skal gennemgå og godkende dem, før de regnes som endelige.

## Principper

### 1. Beskriv løsningen, før den bygges

Følg Spec Kit-forløbet: grundprincipper → specifikation → afklaringer → plan → opgaver → implementering → afsluttende gennemgang. Beskriv først, hvad brugeren skal kunne, og hvordan vi kan se, at det virker. Hold brugerhistorierne små og værdifulde.

### 2. Backend har tre klare lag

Backend består af præsentationslaget (REST/API), forretningslogikken og dataadgangen. API-laget håndterer anmodninger og svar. Forretningslogikken står for regler og officielle beregninger af nøgletal. Dataadgangen læser og skriver data. Hvis en opgave kræver en undtagelse, skal planen forklare hvorfor.

### 3. API-kontrakten beskriver den faktiske løsning

Backend-funktioner skal kunne bruges gennem et REST API med JSON. OpenAPI er kontrakten, og Swagger UI skal kunne åbnes som en Docker-tjeneste. Kontraktens felter, svar og statuskoder skal passe til API'et. Bookingbrugerfladen, Tableau og et eventuelt bookingsystem skal bruge API'et som klienter.

### 4. MySQL indeholder de aktuelle data

Brug MySQL til hotellets og barens driftsdata. CSV-filerne fra opgaven kan bruges til at indlæse historiske eksempeldata, men må ikke være den eneste måde at rette aktuelle data på. Bookinger skal kunne ændres gennem API'et, og dataintegriteten skal beskyttes i forretningslogikken og dataadgangen.

### 5. Nøgletal skal kunne forklares

API'et og dashboardet skal understøtte opgavens nøgletal, herunder belægning og gæstetilfredshed, hvis der findes data nok til at beregne dem på en meningsfuld måde. Forretningslogikken er udgangspunktet for de officielle definitioner og beregninger; Tableau viser og filtrerer resultaterne.

Før implementering skal gruppen beskrive sæsonernes datoer, beregningen af belægning, rapporteringsåret, datagrundlaget for tilfredshed og reglerne for omsætning. Værelsespriser fra opgaven er estimater, ikke dokumenterede indtægter fra faktiske bookinger.

### 6. Systemet skal være nemt at starte igen

Hele prototypen skal starte med `docker compose up`. Beskriv tjenesterne, deres forbindelser, hvordan MySQL bliver klar, og hvordan data bevares. Swagger UI skal også køre i Docker. Planen skal forklare, hvordan Tableau forbindes til systemet, og om Tableau kører uden for Docker.

### 7. Gruppen skal kunne stå inde for arbejdet

Brug gerne AI som hjælp, men gennemgå resultatet. Alle i gruppen skal forstå og kunne forklare det afleverede og tage ansvar for deres egne bidrag.

## Opgavens faste rammer

- Hotel Kong Arthur har 214 værelser fordelt på otte værelsestyper. Opgaven anslår en samlet kapacitet på 428 gæster.
- Hoteldashboardet skal vise gæsternes lande, omsætning fordelt på værelsestype, sæson og land, de bedst indtjenende værelsestyper og lande, årets samlede omsætning samt mindst ét ekstra nøgletal.
- Belægning og gæstetilfredshed skal med, når datagrundlaget gør det muligt at beregne dem meningsfuldt.
- Barens dashboard skal vise Helene Christines årlige salg, omsætning pr. drik og procentfordelingen mellem cocktails og kaffe. Opgaven nævner 20 cocktails og 10 kaffetyper.
- Brugerfladen skal kunne oprette, redigere og slette bookinger gennem backend.
- API'et skal beskrives i OpenAPI og kunne ses i Swagger UI.
- Databasen skal være MySQL, og systemet skal bruge Docker og Docker Compose.

## Det skal afklares i specifikationen eller planen

- Sæsonernes datoer, og om de ændrer sig fra år til år.
- Hvordan belægning beregnes, hvilke værelser der tæller som ledige, og hvordan værelser ude af drift behandles.
- Hvilket år og hvilken tidszone der afgør, hvad "i år" betyder.
- Hvilke bookingfelter og oplysninger om gæsternes lande der findes i eksempeldataene.
- Om der findes tilfredshedsdata, hvordan de vurderes, og hvilke besvarelser der tæller med.
- Hvor værelsespriser kommer fra, og hvordan skatter, aflysninger, refunderinger og tilkøb indgår i omsætningen.
- Hvor barens salgsdata kommer fra, og om de indeholder priser og datoer for de enkelte salg.
- Hvordan Tableau henter og opdaterer data fra API'ets analyseendpoints.

Hvis datagrundlaget ikke giver svar, skal spørgsmålet stå som en afklaring. Vi skal ikke opfinde tal eller forretningsregler.

## Vedligeholdelse

Opgavens faste krav går forud for tekniske bekvemmelighedshensyn. Gruppen skal dokumentere ændringer til disse principper og være enig om dem. Ved den afsluttende gennemgang sammenlignes løsningen med principperne, specifikationerne, planerne, opgaverne og acceptkriterierne. Mangler og ubesvarede spørgsmål skrives på som opgaver.

**Version:** 0.1.0-udkast · **Godkendt:** Afventer gruppens gennemgang · **Senest ændret:** 26. oktober 2026
