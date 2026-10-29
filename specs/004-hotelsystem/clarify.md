# Clarify: Hotelsystem

**Dato:** 29. oktober 2026

**Status:** Gennemgået mod opgavebeskrivelsen; klar til Plan med dokumenterede fortolkningsrisici og gruppens gennemgang.

**Grundlag:** [Specify](spec.md), [constitution](../../.specify/memory/constitution.md), opgave-PDF’erne i `opgavebeskrivelse/` og [projektets arkitekturvejledning](../../project-skills/hotel-architecture-review/SKILL.md).

Dokumentet samler afklaringer, gennemgangen mod opgavekravene, overdragelsen til Plan og kvalitetskontrollen. Brugerhistorier, domæneregler og de rettede acceptkriterier vedligeholdes i [spec.md](spec.md).

## Session 2026-10-29

Clarify er gennemført på brugerens anmodning med udgangspunkt i de eksisterende svar og de supplerende valg i Specify. Nedenstående er en sammenhængskontrol og præcisering af gældende valg, ikke nye interviewsvar. Der er ikke stillet nye spørgsmål, fordi de resterende åbne punkter er tekniske undersøgelser eller allerede afgrænset som demovalg. Ingen kræver, at interviewet gentages før Plan. Gennemgangen mod opgave-PDF’erne nedenfor viser dog to fortolkningsrisici, som ikke kan erklæres godkendt alene af gruppen.

Afklaringerne nedenfor henviser til de gældende regler i Specify, så regler og formler vedligeholdes ét sted.

| Afklaring | Resultat og begrundelse | Gældende krav i Specify |
|---|---|---|
| Hvilke rådata kan bruges til årsrapporter? | Udaterede referenceposter holdes adskilt fra daterede drifts- og demodata. `Price` fortolkes ikke uden dokumentation. | [Startdata og datakvalitet](spec.md#startdata-og-datakvalitet) |
| Hvad betyder årets indtjening? | Fortolkes som bookingomsætning; historik og prognose skal fremgå særskilt. Fordeling følger overnatningsdato. | [Tid og omsætning](spec.md#supplerende-valg-ved-færdiggørelse-af-specify), US7 |
| Hvad er sæsonerne? | Den valgte kalender præciserer opgavens omtrentlige sæsoner; ophold fordeles pr. nat. Det er en prototypebeslutning. | [Sæsonregler](spec.md#supplerende-valg-ved-færdiggørelse-af-specify), US7.5 |
| Hvad betyder sletning? | Logisk aflysning opfylder prototypens brugerforløb. Historikken bevares, mens analysebidrag fjernes, også for tidligere perioder. | [Kapacitet og validering](spec.md#supplerende-valg-ved-færdiggørelse-af-specify), US4, US6 |
| Hvordan bruges gæsteantal og kapacitet i analyser? | Gæsteophold og værelsesnætter er forskellige mål. Filtrene skal anvendes på samme grundlag; kapacitet er tydeligt mærkede demostamdata. | [Analyser og filtre](spec.md#supplerende-valg-ved-færdiggørelse-af-specify), US7–US8 |
| Hvilket ekstra nøgletal er obligatorisk? | ADR er valgt og indgår i P1. Tilfredshed mangler beregningsgrundlag og er fortsat en fortolkningsrisiko. | [US8](spec.md#us8--belægning-og-ekstra-nøgletal-p1) |
| Hvad betyder live? | Brugeren har efterfølgende accepteret manuel datakilde-refresh i Tableau. Femsekundersmålet er erstattet; databasen og API’et indeholder aktuelle data. | [US10](spec.md#us10--aktuelle-data-i-dashboardet-p1), FR-007, SC-003 |
| Hvad dækker én kommando? | Constitution afgrænser Docker-tjenesterne og behandler Tableau som ekstern klient. Denne fortolkning skal afstemmes mod opgaven. | [US11](spec.md#us11--start-og-bevar-prototype-p1), SC-005 |

## Kontrol af uklarheder

| Område | Resultat af Clarify | Grundlag |
|---|---|---|
| Roller, omfang og fravalg | Afklaret; ingen login, betaling eller fysisk værelsestildeling | Omfang, US1–US6 |
| Booking, kapacitet og samtidighed | Afklaret; én typeenhed pr. nat, ingen overbooking og atomiske ændringer | Domæneregler, US1–US4, SC-004 |
| Søgning, historik og fejl | Afklaret; natligt overlap, kombinerede filtre og forståelige fejl uden delvis gemning | US2–US6, FR-011 |
| Hotel- og barberegninger | Afklaret; DKK, lokale kalenderdatoer, definerede formler og nulgrundlag | US7–US9 |
| Rådata og demodata | Afklaret afgrænsning; præcis importmapping og demosæt udskydes til Plan | Startdata og datakvalitet |
| Aktualitet og Tableau | Kravet er entydigt; teknisk gennemførlighed er stadig uafprøvet | US10, FR-007, SC-003 |
| Arkitektur, API og opstart | Faste rammer afklaret; teknisk udformning til Plan | Constitution, FR-008–FR-010, US11 |
| Accept og aflevering | Alle historier har kriterier; implementeringsbeviser mangler fortsat | US1–US11, SC-001–SC-007 |

## Sammenhold med opgavebeskrivelsen · gennemgang 2026-10-29

Kilderne er `opgavebeskrivelse/E26 Tværfaglig Opgave Hotel Kong Arthur.pdf` (Systemkrav, Krav Forretningsdesign og analytics, Krav Systemudvikling og Krav Softwarearkitektur) og `opgavebeskrivelse/Tillægsspørgsmål_swa.pdf` (spørgsmål 1–10). Status nedenfor gælder kravdækning i dokumentationen; ingen række beviser fungerende kode.

| Opgavens krav | Dækning i specifikationen | Vurdering og præcisering |
|---|---|---|
| Tre lag, REST/JSON og MySQL | Omfang, FR-008–FR-010 | Beskrevet. Plan skal vise laggrænser og udskiftelighed; Converge skal følge en konkret forespørgsel gennem alle lag. |
| Browserfrontend med opret, ret og slet booking; POST/PUT/DELETE til andre klienter | US1–US4, FR-001, FR-009 | Beskrevet. OpenAPI skal eksplicit dække de tre skrivemetoder; logisk DELETE opfylder prototypens sletteforløb. |
| Aktuelle data og interaktivt Tableau-dashboard gennem REST API | US7, US9–US10 | Beskrevet og revideret til manuel datakilde-refresh efter brugerens accept. Opgaven angiver ingen tidsgrænse; den konkrete Public-forbindelse skal afprøves. |
| Gæstelande, omsætning pr. type og sæson samt pr. land; bedst indtjenende typer og lande; årets omsætning | US7 | Beskrevet. Tilføjet eksplicit kriterium for type fordelt på sæson. Omsætning bruges som fortolkning af indtjening; prognosedelen skal fremgå særskilt. |
| Mindst ét selvvalgt ekstra nøgletal og belægningsgrader | US8, FR-005 | ADR er obligatorisk som det valgte ekstra nøgletal. US8 er derfor hævet fra P2 til P1. Belægning beregnes med dokumenteret demokapacitet. |
| Kundetilfredshed nævnes under Systemkrav | US8.3, dataafgrænsning | **Fortolkningsrisiko:** »Intet datagrundlag« er ærlig visning af en mangel, men er ikke en beregning. Den nuværende afgrænsning kan derfor ikke erklæres fuldt dækkende for denne formulering. |
| Helene Christines årssalg, omsætning pr. drik og cocktail/kaffe-fordeling | US5, US9 | Beskrevet. Begge andele vises; navngivne drikke og katalogets 20 cocktails/10 kaffetyper er gjort eksplicitte i US9.4. |
| Alt i Docker med én Compose-kommando | US11, SC-005, constitution: Systemets grænser | **Fortolkningsrisiko:** Projektet undtager Tableau som ekstern klient, mens opgaven skriver »Alt i jeres system«. Afgrænsningen er en projekttolkning, ikke en udtrykkelig undtagelse i opgaven. SC-005 er præciseret, så den ikke lover Tableau-opstart med kun Docker. |
| OpenAPI og Swagger UI i Docker; README med diagram og CONTRIBUTE | US11, FR-009, SC-007 | Beskrevet; OpenAPI-kontrakten mangler fortsat. CONTRIBUTE beskriver arbejdsgangen, og README-diagrammet viser målarkitekturen. |
| Spec Kit, INVEST, acceptkriterier og afsluttende Converge | US1–US11, FR-012, SC-006 | Dokumentationsforløbet er beskrevet. Plan/Tasks for hotelsystemet og implementeringsbeviser mangler fortsat. |
| Alle medlemmers bidrag i Git og ejerskab ved præsentationen | Constitution, afsluttende gennemgang | Kravet skal kontrolleres ved aflevering med faktiske commits og forklaring af egne bidrag. Det kan ikke verificeres ved denne Clarify. |

**Håndtering af fortolkningsrisici:** Plan skal synliggøre både Tableau-systemgrænsen og den manglende tilfredshedsberegning som punkter til afstemning med underviseren. Indtil da fastholdes de eksisterende projektvalg, men kravene må ikke markeres ubetinget opfyldt. Hvis tilfredshedsberegning kræves, skal spec udvides med datakilde, skala, beregningsregel, brugerhistorie og acceptkriterier før implementering. Hvis Tableau skal indgå i den fælles opstart, skal systemgrænsen og opstartsaccepten revideres. Afklaringen kræver ikke en ny teknologistakbeslutning fra brugeren nu.

Opgavens cirka 428 gæster er et omtrentligt tal uden fordeling på typer. Det anvendes ikke som en ekstra global kapacitetsregel oven i de dokumenterede typekapaciteter. De originale data er inspiration ifølge opgaven; adskillelsen mellem rå referenceposter og daterede demodata er derfor fastholdt.

## Overdragelse til Plan

1. Afprøv Tableau-forbindelsen tidligt med API-data og manuel datakilde-refresh. Dokumentér Public-version, connector, trin, snapshot-tidspunkt og fejlforløb mod den reviderede US10/SC-003. Brugerens accept erstatter det tidligere femsekunderskrav; refresh skal hente nye data, ikke blot genvise et gammelt udtræk.
2. Vælg teknologier og konkret datamodel inden for de tre lag. Beskriv transaktioner og samtidighed, så sidste ledige enhed ikke overbookes, og håndtér gentagne skrivninger efter forbindelsesfejl uden dubletter.
3. Udform OpenAPI-kontrakten før implementering: POST/PUT/DELETE til bookinger, læse- og analysefunktioner, felter, filtre, validering, fejlsvar, aflyste ressourcer og idempotent DELETE. Kontrakten skal gennemgås og godkendes som fastlagt i constitution.
4. Fastlæg demokapacitet, katalogpriser, deterministisk demosæt og importmapping. Dokumentér oprindelse, udeladte rækker og genstart uden dobbeltimport. Ingen konstruerede værdier udlægges som hotellets fakta.
5. Beskriv Docker-opstart, vedvarende data, Tableau-forudsætninger og teststrategi. Knyt verifikation til alle acceptkriterier, herunder årsskifte, filtrerede nævnere, samtidighed og dashboardets fejltilstand.
6. Overfør de to fortolkningsrisici ovenfor til Plan med en konkret afklaringsaktivitet og efterfølgende opgaver i Tasks. Knyt også dokumentation og gennemgang til SWA-spørgsmålene: requestforløb, lagansvar, nøgletal, udskiftelighed, REST, kontrakt, opstart, live data og gruppens begrundede vurdering af AI-forslag.

## Afsluttende dokumentationsgennemgang

Clarify er kontrolleret mod begge opgave-PDF’er, constitution, projektets arkitekturvejledning og specifikationens krav. Domænevalgene er beskrevet, men kundetilfredshed og Tableau uden for Docker er åbne fortolkningsrisici. Manuel API-baseret datakilde-refresh i Tableau Public er desuden en uafprøvet teknisk risiko. Plan kan påbegyndes med disse punkter synlige; fuld overensstemmelse med opgaven er ikke dokumenteret. Dette er ikke en godkendelse fra de øvrige gruppemedlemmer eller en verifikation af implementeret funktionalitet.

Ved den senere afsluttende gennemgang følges en booking fra browser gennem API, logik og dataadgang til MySQL. Kontrakten sammenholdes med faktisk adfærd, og Tableau kontrolleres mod API'et. Fund skal have filstier og konkrete eksempler. Ingen person tilskrives bidrag, som vedkommende ikke har udført.

## Clarify-kontrol · 29. oktober 2026

- [x] Eksisterende svar og supplerende valg er gennemgået uden at fremstille dem som nye interviewsvar.
- [x] Omsætning, aflysning, filtre, kapacitet og manglende datagrundlag er gennemgået her med henvisninger til de gældende regler i spec.md.
- [x] Tekniske valg er overdraget til Plan frem for at blive besluttet i Clarify.
- [x] Det tidligere femsekunderskrav er ændret til manuel datakilde-refresh efter brugerens udtrykkelige accept og kræver en tidlig teknisk afprøvning.
- [x] Ingen væsentlige uafklarede brugerbeslutninger forhindrer Plan.

**Aktuel status efter genlæsning af opgaven:** Clarify er gennemgået og klar til Plan med åbne fortolkningsrisici om kundetilfredshed og Tableau uden for Docker samt teknisk risiko om API-baseret datakilde-refresh i Tableau Public. Ingen applikationsacceptkriterier er verificeret som implementeret.

## Kontrol mod opgave-PDF’erne · 29. oktober 2026

- [x] Kravene er sammenholdt direkte med begge PDF’er i dette dokuments kravtabel.
- [x] US7.5 kræver omsætning pr. type opdelt på sæson med konkret testeksempel.
- [x] US8 er P1, så det valgte ekstra nøgletal ADR indgår i minimumsafleveringen.
- [x] US9.4 præciserer omsætning pr. navngiven drik og startkatalogets 20 cocktails/10 kaffetyper.
- [x] SC-005 skelner mellem Compose-opstart og ekstern Tableau-klient.
- [x] Fem sekunder var et projektmål, ikke et eksplicit tidskrav fra opgaven; det er nu erstattet af brugerens valg om manuel refresh.
- [ ] Det er afstemt med underviseren, om manglende tilfredshedsberegning accepteres.
- [ ] Det er afstemt med underviseren, om Tableau uden for Docker accepteres som systemgrænse.

De to åbne punkter er aktiviteter til Plan og efterfølgende Tasks. De er ikke godkendt ved denne dokumentationsgennemgang.

## Dokumentstruktur efter gruppens ønske

Det aktive forløb er samlet via [specs/README.md](../README.md) i opgavens faserækkefølge. Specify er den gældende kravbeskrivelse; Clarify beskriver afklaringer og deres begrundelser med henvisninger til kravene. Tidligere dokumentationsopgaver er bevaret uændret direkte under `specs/` i mapperne 001, 002 og 003. Plan, Tasks og Converge for hotelsystemet er fortsat kommende faser.

**Kontrol af omlægningen:** Filerne i 001, 002 og 003 er bevaret byte-for-byte ved tilbageflytningen. Lokale Markdown-links og Spec Kits stiopløsning kontrolleres. README viser de tre backendlag, API-klienterne, MySQL og den planlagte førstegangsindlæsning gennem dataadgangen. Der er fortsat ingen kørende forespørgsel at følge eller OpenAPI-adfærd at funktionsteste.

## Videreført til Plan

Den tekniske [Plan](plan.md) er nu udarbejdet med valgte teknologier, laggrænser, datamodel, transaktioner, API-design, demokapacitet, import, Docker og teststrategi. Gruppen har efterfølgende bekræftet Tableau Public. Den praktiske Tableau-afprøvning, valideringen af den manuelle datakilde-refresh og afstemningen om tilfredshed/systemgrænse er fortsat åbne; planens afsnit 7 og 12 beskriver næste handling. De tidligere statusangivelser ovenfor beskriver afslutningen af Clarify.

## Godkendt ændring: manuel refresh i Tableau

Brugeren har bekræftet Tableau Public og accepteret: »Det er fint hvis man trykker refresh inde på tableau«. Det erstatter projektets tidligere automatikkrav; det kræver ikke en ny godkendelse fra brugeren. Ændringen er indarbejdet i Specify under Analyser og filtre, US10, FR-007 og SC-003 og i Plan, afsnit 7 og teststrategien.

En vellykket refresh skal hente aktuelle analyser gennem API’et, omfatte oprettelser, rettelser og aflysninger samt vise datagrundlagets tidspunkt. Fejlet refresh må ikke mærke et gammelt snapshot som nyt. Det tidligere krav om synlig opdatering inden fem sekunder efter gemning gælder ikke længere. Der er endnu ikke udført en praktisk refreshprøve i Public.
