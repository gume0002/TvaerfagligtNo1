# Manuskript: Hotel Kong Arthur

**Fremlæggelse:** 6. november 2026. **Samlet tid:** 9:30 ud af højst 10 minutter.

Tiderne er anslået ud fra cirka 130 ord i minuttet. De er ikke målt med ur, så læs det igennem samlet og ret til. Skriv navne ind ud for **Taler**, når I har fordelt emnerne. Alle tal fra systemet er demodata.

| Slide | Emne | Tid |
|---|---|---:|
| 1 | Hotellets behov og løsningen | 0:30 |
| 2 | Sådan arbejdede vi | 0:45 |
| 3 | Fra brugerhistorie til bevis | 0:45 |
| 4 | Arkitekturen | 1:00 |
| 5 | En booking gennem systemet | 1:00 |
| 6 | Nøgletal i backenden | 0:45 |
| 7 | API og drift | 1:00 |
| 8 | Tillægsopgaven | 1:00 |
| 9 | Demo | 2:00 |
| 10 | Status og svagheder | 0:45 |

## Slide 1: Hotel Kong Arthur (0:30)

**Taler:** ______

Hotel Kong Arthur vil gerne følge sine bookinger, sin omsætning og salget i baren. I dag ligger data i statiske filer, som hurtigt bliver forældede. Vi har derfor bygget et system, hvor medarbejderne kan registrere bookinger og barsalg i browseren, og hvor ledelsen kan se aktuelle nøgletal i både browseren og Tableau.

## Slide 2: Sådan arbejdede vi (0:45)

**Taler:** ______

Vi har arbejdet spec-drevet med GitHub Spec Kit i de syv trin, I ser her. Først skrev vi, hvad systemet skal gøre, og så brugte vi specifikationen til at styre AI'en. I Clarify afklarede vi fx, hvad live betyder hos os, og hvordan sæsoner og belægning skal beregnes. AI'en har skrevet meget af koden, men det er os, der har besluttet retningen og gennemgået resultatet. Derfor skal vi også selv kunne forklare det.

## Slide 3: Fra brugerhistorie til bevis (0:45)

**Taler:** ______

Her er et eksempel. Som receptionist vil jeg oprette en booking. Et af acceptkriterierne siger, at når der er ét ledigt værelse, og to prøver at booke samtidig, må højst én lykkes. Det har vi en automatisk test af, og i Converge står kriteriet som opfyldt med testen som bevis. Sådan har vi gennemgået alle krav. I hovedforløbet er 32 af 36 acceptkriterier opfyldt, og fire er delvist opfyldt. Dem vender vi tilbage til til sidst.

## Slide 4: Arkitekturen (1:00)

**Taler:** ______

Det her er hele systemet. Alt inde i den store boks kører i Docker. Browseren taler med Nginx, som viser frontenden og sender API-kald videre til backenden. Backenden har tre lag. API-laget modtager HTTP og JSON. Forretningslogikken indeholder reglerne og beregner nøgletallene. Dataadgangen er det eneste lag, der taler med PostgreSQL. Hvert lag må kun kalde laget lige under sig, og det kontrollerer en automatisk arkitekturtest. Tableau og hotellets bookingsystem ligger uden for Docker. Tableau henter kun data gennem API'et og aldrig direkte fra databasen. Bookingsystemet er en mulig fremtidig klient, som kan bruge det samme API.

## Slide 5: En booking gennem systemet (1:00)

**Taler:** ______

Når en medarbejder trykker gem, sender browseren JSON til POST api bookings. Nginx sender det videre til API-laget, som kontrollerer formatet. Forretningslogikken tjekker reglerne og låser værelsestypen. Det betyder, at to samtidige bookinger venter på hinanden, så vi ikke kan overbooke. Dataadgangen gemmer bookingen i PostgreSQL, og svaret kommer tilbage som 201 Created. Browseren sender også en idempotensnøgle, altså en unik nøgle for netop det forsøg. Hvis svaret går tabt, og medarbejderen trykker gem igen, kender vi nøglen og opretter ikke en dobbelt booking.

## Slide 6: Nøgletal i backenden (0:45)

**Taler:** ______

Vi kunne have beregnet nøgletallene i Tableau, men vi har lagt dem i forretningslogikken. Så findes hver regel kun ét sted, og API, browser og Tableau får de samme tal. Belægning er bookede værelsesnætter delt med tilgængelige værelsesnætter. Vores ekstra nøgletal er ADR, altså omsætning delt med bookede nætter. Valget betalte sig i tillægsopgaven, for browseren kunne vise tallene uden en ny beregning.

## Slide 7: API og drift (1:00)

**Taler:** ______

API'et er bygget op om ressourcer som bookinger og barsalg, med HTTP-metoder og statuskoder, som fx 201 ved oprettelse og 409, hvis der ikke er plads. Kontrakten er skrevet i OpenAPI og vises i Swagger UI. Vores tests kontrollerer svarene mod kontrakten, så en forskel får testen til at fejle. Med docker compose up starter databasen først. Når den er klar, kører et engangsjob migrationer og startdata, og derefter starter backend, frontend og Swagger. Data ligger i en navngivet volume og overlever en genstart. I seneste testkørsel bestod alle 366 tests.

## Slide 8: Tillægsopgaven (1:00)

**Taler:** ______

Tillægsopgaven havde to krav. For det første skulle analyserne kunne læses direkte i API'et og vises i frontenden. Endpoints fandtes allerede, så vi kontrollerede, at de dækkede kravene, og byggede analysesiden med grafer og tabeller. For det andet skulle MySQL skiftes ud, og vi valgte PostgreSQL. API-laget blev slet ikke ændret, og i forretningslogikken rettede vi kun to kommentarer. Ændringerne lå i dataadgang, migration, drift og tests. Det viser, at lagdelingen virker. Opgaven siger en anden type database, og PostgreSQL er også relationel. Det er vores tolkning, og vi har ikke afstemt den med jer.

## Slide 9: Demo (2:00)

**Taler:** ______

**Inden I går i gang:** Systemet kører med `docker compose up`, siderne er åbne i faner, og Tableau er åben med år 2026 og alle sæsoner.

1. **Analysesiden (15 sek.):** »Her er årets omsætning lige nu. Det er demodata.« Peg på tallet.
2. **Bookingsiden (40 sek.):** Opret en booking: Germany, Junior Suite, 10.-12. december 2026, én gæst, 1.000 DKK pr. nat. »To nætter til 1.000 kroner, så omsætningen bør stige med 2.000.«
3. **Analysesiden (15 sek.):** Genindlæs siden. »Tallet er steget med 2.000 kroner.«
4. **API'et (15 sek.):** Åbn `http://127.0.0.1:8080/api/analytics/hotel`. »Det er det samme tal direkte fra API'et.«
5. **Tableau (35 sek.):** Vælg **Data → HotelTotals → Refresh**. »Tableau opdaterer ikke selv. Vi trykker refresh for hver datakilde, og her viser vi én af de syv.«

**Efter demoen:** Aflys testbookingen. Luk Tableau med **Don't Save**.

**Plan B:** Hvis noget driller, så gå videre med skærmbillederne på slidet, og sig, at de er fra en tidligere kørsel. Brug ikke tid på at fejlsøge.

## Slide 10: Status og svagheder (0:45)

**Taler:** ______

Systemet virker, og de centrale krav er opfyldt. Nogle ting er kun delvist opfyldt. Vi har testet refresh i Tableau med en stikprøve og har ikke prøvet alle filterkombinationer, og kundetilfredshed viser intet datagrundlag, fordi der ikke findes data. Tableau Public kører uden for Docker og kræver manuel refresh. Den største svaghed før produktion er, at der ikke er noget login, så alle, der kan nå API'et, kan læse og ændre data. Det var et bevidst valg i en prototype. Tak for ordet. Har I nogen spørgsmål?
