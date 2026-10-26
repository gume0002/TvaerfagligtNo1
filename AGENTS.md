# Retningslinjer for Hotel Kong Arthur-projektet

## Arbejdsgang

Brug GitHub Spec Kit, når projektet ændres. Følg rækkefølgen: grundprincipper → specifikation → afklaringer → plan → opgaver → implementering → afsluttende gennemgang. Læs projektets eksisterende dokumenter, før du ændrer løsningen.

Ved gennemgang af arkitektur eller acceptkriterier skal du også læse og følge `project-skills/hotel-architecture-review/SKILL.md`.

## Krav til opgaven

- Backend skal bestå af tre tydelige lag: REST/API, forretningslogik og dataadgang.
- API'et skal bruge REST og JSON. Beskriv det i OpenAPI, og gør Swagger UI tilgængelig i Docker.
- Brug MySQL. Hele systemet skal kunne startes med én kommando: `docker compose up`.
- Lav en brugerflade i browseren, hvor bookinger kan oprettes, redigeres og slettes gennem backend.
- API'et skal kunne opdatere aktuelle data. Eksempeldata i CSV må ikke være systemets eneste datakilde.
- Hotellets analyser skal vise gæsternes lande, omsætning fordelt på værelsestype, sæson og land, de bedst indtjenende værelsestyper og lande, årets samlede omsætning samt mindst ét ekstra nøgletal.
- Barens analyser for Helene Christine skal vise årets samlede salg, omsætning pr. drik og fordelingen mellem cocktails og kaffe.
- Vedligehold `README.md` med et arkitekturdiagram, `CONTRIBUTE.md` og OpenAPI-kontrakten.
- Hver brugerhistorie skal have acceptkriterier. Kontrollér dem i den afsluttende gennemgang.

## Gennemgang og bidrag

Når du gennemgår løsningen, skal du følge en typisk forespørgsel fra browseren gennem API'et, forretningslogikken og dataadgangen til MySQL. Kontrollér, at API-kontrakten svarer til den faktiske løsning, og at dashboardet kan hente sine data fra API'et. Beskriv fund med filstier og konkrete eksempler.

Beskriv kun arbejde, der faktisk er udført. Hvert gruppemedlem skal kunne stå inde for sit eget bidrag; tilskriv ikke andre personers arbejde til dig selv.
