# Specifikation: Placering af projektets eksempeldata

**Oprettet:** 26. oktober 2026  
**Status:** Klar til gruppens gennemgang

## Brugerhistorie – Find de medfølgende data

**Som gruppemedlem vil jeg have opgavens datafiler samlet i projektet og beskrevet, så jeg kan finde dem uden at forveksle dem med systemets aktuelle datakilde.**

**Acceptkriterier**

1. De tre medfølgende datafiler findes samlet i projektets `data/raw/`-mappe med deres oprindelige filnavne og indhold.
2. README beskriver kort, hvad datafilerne indeholder, og at de er eksempel-/referencedata frem for systemets eneste eller aktuelle datakilde.
3. Kendte datakvalitetsproblemer nævnes, så eksempelfilerne ikke bruges ukritisk i indlæsning eller analyser.
4. Projektets grundprincipper på `.specify/memory/constitution.md` forbliver på deres eksisterende placering; der oprettes ikke en ekstra kopi.

## Afklaringer

- De to hoteldatafiler beholdes begge, fordi brugeren har leveret begge formater, selv om de beskriver de samme 1.000 poster.
- Filerne lægges under `data/raw/`, da de er oprindelige inputfiler og endnu ikke er del af en implementeret indlæsningsproces.
- Filerne ændres ikke under kopieringen. Hotel-CSV'en indeholder 54 erstatningstegn i navne, og hotelarbejdsbogen har en ekstra værdi i celle E1002. Det dokumenteres, og værdierne ændres ikke uden afklaring.
- Grundprincipperne findes allerede på den angivne projektsti; det er den samme fil som den taggede fil.

## Uden for denne ændring

Der bygges ingen importproces, database, API eller analysefunktion. Det besluttes heller ikke, hvilken hoteldatarepræsentation der skal være autoritativ, eller hvordan de kendte datakvalitetsproblemer skal rettes.
