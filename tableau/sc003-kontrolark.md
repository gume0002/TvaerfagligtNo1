# Kontrolark: SC-003 (T055)

**Dato for de dokumenterede runder:** 2. november 2026. **Værktøj:** Tableau Public 2026.3 med `tableau/hotel-and-bar.twbx`. **Program:** `tableau/sc003.py`.

**Status opdateret 5. november 2026:** Gruppen har bekræftet, at alle 60 krævede refresh-runder er gennemført. Tabellen nedenfor dokumenterer de 12 runder fra den oprindelige stikprøve; de øvrige 48 målinger er ikke gengivet enkeltvis her.

**Resultat for de 12 dokumenterede runder:** Alle gav de forventede tal. Den tidligere beslutning om at nøjes med 12 runder står som historik i [`clarify.md`](../specs/004-hotelsystem/clarify.md); gruppen har efterfølgende gennemført alle 60.

## Sådan er prøven udført

Prøven kørte i et isoleret Compose-projekt med 1.000 bookinger og 1.000 barsalg, der er oprettet gennem API'et. Demoens database blev ikke brugt. Ændringerne blev lavet af `sc003.py` gennem API'et, og den forventede værdi er API'ets svar for samme filtre lige efter ændringen. Værdierne i Tableau blev aflæst fra skærmbilleder efter manuel refresh.

**Filtre:** Hotel: 2026 og Højsæson, med land og værelsestype på Alle. Bar: 2026 og Helene Christine.

**Afgrænsninger:**

- I runde 4–6 blev kun `HotelTotals` og `HotelRoomTypeSeason` opdateret, så ranglisterne ikke indgår i de runder.
- Runderne ændrede kun de viste felter nedenfor. Øvrige felter er ikke sammenlignet ét for ét.
- Tidspunktet i runde 6 var ikke synligt i skærmbilledet.
- Kaffe-rækken var afskåret i skærmbillederne af baren, så kun cocktail-andelene er aflæst.
- Fejlet refresh er ikke gentaget på dette datasæt. Den er afprøvet med demodata i T054.

## Udgangspunkt

| Visning | Filter | API og Tableau | Datagrundlag (UTC) |
|---|---|---|---|
| Hotel | Højsæson | Samlet 885.900,00, 393 nætter og ADR 2.254,20 | 15.05.42 |
| Bar | Helene Christine | 535 drikke, 51.915,00 DKK og cocktail 69,16 / 82,81 % | 15.05.25 |

## Hotel

| Runde | Ændring | Forventet og vist: samlet omsætning, nætter og ADR | Standard Single | Datagrundlag (UTC) | Resultat |
|---:|---|---|---:|---|---|
| 1 | Oprettelse af booking 1 | 887.900,00, 395 og 2.247,85 | 41.300,00 | 15.06.50 | Ens |
| 2 | Oprettelse af booking 2 | 889.900,00, 397 og 2.241,56 | 43.300,00 | 15.07.34 | Ens |
| 3 | Rettelse af booking 1 | 890.900,00, 397 og 2.244,08 | 44.300,00 | 15.08.43 | Ens |
| 4 | Rettelse af booking 2 | 891.900,00, 397 og 2.246,60 | 45.300,00 | 15.09.27 | Ens |
| 5 | Aflysning af booking 1 | 888.900,00, 395 og 2.250,38 | 42.300,00 | 15.10.07 | Ens |
| 6 | Aflysning af booking 2 | 885.900,00, 393 og 2.254,20 | Ikke aflæst | Ikke synligt | Ens |

## Bar

| Runde | Ændring | Forventet og vist: drikke og DKK | Cocktail: antal, DKK og andele | Mojito | Datagrundlag (UTC) | Resultat |
|---:|---|---|---|---:|---|---|
| 7 | Oprettelse af salg 1 | 537 og 52.115,00 | 372, 43.189,08 og 69,27 / 82,87 % | 3.332,36 | 15.12.26 | Ens |
| 8 | Oprettelse af salg 2 | 539 og 52.315,00 | 374, 43.389,08 og 69,39 / 82,94 % | Afskåret: 3.532,… | 15.13.11 | Ens |
| 9 | Rettelse af salg 1 | 538 og 52.215,00 | 373, 43.289,08 og 69,33 / 82,91 % | 3.432,36 | 15.13.50 | Ens |
| 10 | Rettelse af salg 2 | 537 og 52.115,00 | 372, 43.189,08 og 69,27 / 82,87 % | 3.332,36 | 15.14.30 | Ens |
| 11 | Aflysning af salg 1 | 536 og 52.015,00 | 371, 43.089,08 og 69,22 / 82,84 % | 3.232,36 | 15.15.08 | Ens |
| 12 | Aflysning af salg 2 | 535 og 51.915,00 | 370, 42.989,08 og 69,16 / 82,81 % | 3.132,36 | 15.15.55 | Ens |

Efter runde 6 og 12 var hotellet og baren tilbage på udgangspunktet.

## Gentag prøven

Demoen skal være stoppet, fordi Tableau bruger port 8080.

```sh
docker compose stop
COMPOSE_PROJECT_NAME=hotelsc003 docker compose up -d --build
python3 tableau/sc003.py load
python3 tableau/sc003.py round 1
```

Ryd op bagefter med `docker compose -p hotelsc003 down -v`, og start demoen igen med `docker compose up -d`.
