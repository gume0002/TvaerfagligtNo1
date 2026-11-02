# Specifikation: Tillægsopgave uge 2

**Specifikationsmappe:** `specs/005-tillaeg-uge-2/`
**Oprettet:** 2. november 2026
**Grundlag:** `opgavebeskrivelse/Tillægsopgave_uge_2.pdf`, [constitution](../../.specify/memory/constitution.md) og [hotelsystemets specifikation](../004-hotelsystem/spec.md)
**Status:** Implementeret på branchen `tillaegsopgave-uge-2`. Afventer gruppens gennemgang i en pull request. Se [converge.md](converge.md).

## Formål

Hotellet vil kunne læse dataanalyserne direkte gennem API'et og i browserfronten, ikke kun i Tableau, og ønsker ikke længere MySQL. Kravene i specifikationen for hotelsystemet gælder fortsat, medmindre dette dokument ændrer dem. Alle regler for beregninger, kapacitet og aflysning er uændrede.

## Omfang

**Med:**

- Sikring af den nuværende version i Git.
- Kontrol af, at API'et leverer de beregninger, Tableau viser.
- En side i browserfronten, der viser beregningerne fra API'et.
- Skift fra MySQL til PostgreSQL.

**Ikke med:**

- Nye nøgletal eller nye forretningsregler.
- Flytning af eksisterende data fra MySQL.
- Fjernelse af Tableau. Opgaven skriver "ikke kun som nu gennem Tableau", så dashboardet bevares.
- Login og andre ændringer af brugerfladen.

## Beslutninger

| Beslutning | Begrundelse | Grundlag |
|---|---|---|
| Databasen skiftes til **PostgreSQL** | Gruppens valg. Det kræver mindst ombygning og viser, at kun dataadgang og drift skal ændres | Besluttet af gruppen 2. november 2026 |
| Nuværende version er sikret med tagget `v1-mysql-tableau` | Opgaven kræver, at arbejdet er tilgængeligt til præsentationen via Git | Tagget peger på `d38e39b` |
| Eksisterende data flyttes ikke | Databasen er ny og får startdata ved første start. Ændringer i en lokal MySQL-demo går tabt | Besluttet 2. november 2026 |
| Frontenden viser både grafer og tabeller | Ledelsen skal kunne aflæse tallene uden Tableau. Tabellerne gør alle værdier læsbare uden farver og uden at holde musen over | Besluttet 2. november 2026 |

**Tolkningsrisiko:** Opgaven skriver "en anden type end den nuværende MySql". PostgreSQL er en anden database, men også relationel. Hvis opgaven menes som en anden slags database, fx NoSQL, opfylder valget det ikke bogstaveligt. Gruppen har valgt ikke at afstemme med underviseren og skal kunne begrunde valget.

## Brugerhistorier og acceptkriterier

### US12 – Sikr version til præsentationen (P1)

Som gruppe ønsker vi at bevare den nuværende løsning i Git, så den kan vises til præsentationen, uanset hvordan det nye arbejde går.

1. Når tagget `v1-mysql-tableau` hentes fra GitHub, indeholder det den version med MySQL, frontend og Tableau-dashboard, der lå på `main` før tillægsopgaven.
2. Det nye arbejde kommer ikke ind på `main`, før gruppen har godkendt det i en pull request.

### US13 – Læs analyser direkte i API'et (P1)

Som hotelledelse ønsker jeg at læse analyserne direkte i API'et, så jeg ikke er afhængig af Tableau.

1. Alle tal, som opgaven kræver for hotellet og baren, kan hentes med `GET /api/analytics/hotel` og `GET /api/analytics/bar`.
2. Kontrakten beskriver endpoints, filtre og felter, og Swagger UI viser dem.
3. Tallene er de samme som i US7–US9 for samme data og filtre.

### US14 – Se analyser i browseren (P1)

Som hotelledelse ønsker jeg at se analyserne i browseren, så jeg kan følge nøgletallene uden Tableau.

1. Siden viser gæstelande, omsætning pr. type og sæson, omsætning pr. land, ranglister, årets omsætning, belægning og ADR for hotellet.
2. Siden viser årets salg, omsætning pr. drik og cocktail/kaffe-fordeling efter antal og omsætning for baren.
3. År, sæson, land, værelsestype og medarbejder kan vælges, og siden henter nye tal fra API'et, når valget ændres.
4. Alle tal kommer fra API'et, og siden beregner ikke selv nøgletal. Med tre cocktails til 100 DKK og to kaffer til 50 DKK vises 400 DKK og andelene 60/40 % og 75/25 %.
5. Efter oprettelse, rettelse eller aflysning af en booking eller et salg viser siden de nye tal, når den hentes igen.
6. Siden viser hotellets og barens tal som grafer og giver adgang til de samme værdier som tabeller.
7. Siden viser tidspunkt for datagrundlaget, mærket »Demodata« og »Intet datagrundlag«, hvor et forholdstal mangler.
8. Hvis API'et ikke kan nås, viser siden en forståelig fejl og ingen gamle tal som aktuelle.

### US15 – Skift database (P1)

Som hotel ønsker jeg, at løsningen ikke bruger MySQL, så den følger vores krav.

1. `docker compose up` starter systemet med PostgreSQL og uden MySQL.
2. Alle funktioner og alle eksisterende tests består mod PostgreSQL, bortset fra tests, der var bundet til MySQL og er rettet til samme formål.
3. To samtidige forsøg på sidste ledige enhed kan stadig ikke give overbooking.
4. Navnesøgning skelner stadig ikke mellem store og små bogstaver, og `%` og `_` behandles bogstaveligt.
5. Ændringer i koden sker kun i dataadgang, migrationer og drift. API og forretningslogik er uændrede, medmindre en ændring er begrundet i pull requesten.
6. Startdata indlæses én gang, og data overlever genstart i en navngivet volume.
7. Tableau kan stadig hente og opdatere data gennem det samme feed.

## Funktionelle krav

| ID | Krav | Historie |
|---|---|---|
| FR-013 | API'et leverer alle krævede beregninger, og kontrakten beskriver dem | US13 |
| FR-014 | Browserfronten viser beregningerne fra API'et uden egne formler | US14 |
| FR-015 | Systemets database er PostgreSQL, og MySQL er fjernet fra løsningen | US15 |

## Succeskriterier

- **SC-008:** Tagget `v1-mysql-tableau` kan hentes og startes fra en frisk kopi.
- **SC-009:** For samme data og filtre viser API, browserfront og Tableau ens tal.
- **SC-010:** Den samlede testkommando består mod PostgreSQL, også 20 gentagelser af samtidige forsøg på sidste enhed.
- **SC-011:** En frisk kopi starter med `docker compose up` på PostgreSQL, og data overlever en genstart.

## Åbne punkter

Skal præsentationen vise begge versioner, eller kun den nye? Beslutningen er udskudt.
