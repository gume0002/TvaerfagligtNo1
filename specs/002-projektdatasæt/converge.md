# Afsluttende gennemgang: Placering af projektets eksempeldata

**Dato:** 26. oktober 2026

## Acceptkriterier

| Kriterium | Status | Fund |
|---|---|---|
| Tre datafiler findes samlet med oprindelige navne og indhold | Opfyldt | Alle tre ligger i `data/raw/`. SHA-256 for hver destinationsfil matcher kilden. |
| README forklarer indhold og rolle | Opfyldt | README angiver 1.000 hotelposter, 20 cocktails og 10 kaffetyper og præciserer, at filerne er eksempel-/referencedata. |
| Kendte dataproblemer fremgår | Opfyldt | README nævner 54 erstatningstegn i hotel-CSV'en og den ekstra værdi `5379` i `E1002` i hotelarbejdsbogen. |
| Grundprincipperne er ikke kopieret | Opfyldt | `.specify/memory/constitution.md` fandtes allerede på sin projektsti og er ikke ændret. |

## Arkitektur og afgrænsning

Placeringen indfører ingen importkode eller ændring af dataflow. Eksempelfilerne bliver derfor ikke en alternativ kilde til aktuelle driftsdata; kravet om, at data kan opdateres gennem API'et og lagres i MySQL, står uændret.

Der er ikke en kørende browser, API, forretningslogik, dataadgang, MySQL, OpenAPI-kontrakt eller dashboard at gennemgå i denne ændring. Den eksisterende README beskriver fortsat disse dele som planlagte, så ingen af dem fremstilles som implementeret.

## Datakvalitet

Hotel-CSV'en og Excel-filen dækker de samme 1.000 gæsteposter, men er ikke helt ens: 54 navne i CSV'en indeholder `�`, mens Excel-filen har den ekstra værdi `5379` i `E1002`. Filerne er kopieret byte-for-byte, og ingen afvigelse er rettet eller skjult. Afklaring og oprydning hører til en senere opgave.
