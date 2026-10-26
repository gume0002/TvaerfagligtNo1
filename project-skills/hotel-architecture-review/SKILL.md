---
name: "hotel-architecture-review"
description: "Gennemgå projektændringer i forhold til opgaven, arkitekturen, API'et, analyserne, Docker, dokumentationen og bidragskravene."
compatibility: "Bruges i arbejdsområdet for Hotel Kong Arthur-projektet."
metadata:
  author: "project-team"
---

# Gennemgang af Hotel Kong Arthurs arkitektur

Brug denne vejledning, når du gennemgår en funktion, projektets struktur eller den afsluttende status.

## Projektets kilder

- Læs opgave-PDF'en og de supplerende SWA-spørgsmål, når de indeholder relevante oplysninger.
- Læs de aktuelle grundprincipper, specifikationer, planer og opgaver fra Spec Kit, før du vurderer løsningen.
- Brug bekræftede beslutninger i dokumenterne som projektets gældende aftaler. Beskriv, hvis projektmaterialet er i konflikt med opgavekravene.

## Krav, der skal kontrolleres

- Backend skal have tre tydelige lag: præsentation/API, forretningslogik og dataadgang.
- REST API'et skal bruge JSON. OpenAPI-kontrakten skal passe til løsningen, og Swagger UI skal være tilgængelig i Docker.
- Brug MySQL, og sørg for at hele prototypen kan startes med én `docker compose up`-kommando.
- Brugerfladen i browseren skal oprette, redigere og slette bookinger gennem API'et.
- Aktuelle data skal kunne ændres gennem API'et. CSV-filer må ikke være eneste datakilde.
- Dashboardet skal vise gæsternes lande, hotellets omsætning fordelt på værelsestype, sæson og land, de bedst indtjenende værelsestyper og lande, årets samlede omsætning og mindst ét ekstra nøgletal.
- Belægning og gæstetilfredshed skal med, hvis der er data og klare definitioner nok til at beregne dem.
- Barens analyser skal vise Helene Christines årlige salg, omsætning pr. drik og fordelingen mellem cocktails og kaffe.
- `README.md` skal have et arkitekturdiagram. Projektet skal også have `CONTRIBUTE.md` og API-kontrakten.
- Brugerhistorierne skal være små og værdifulde, og deres acceptkriterier skal kontrolleres i den afsluttende gennemgang.

## Sådan gennemføres en gennemgang

1. Find ud af, hvad der er ændret, og hvilken brugerhistorie eller opgave ændringen løser.
2. Følg en typisk anmodning gennem browseren, API-/præsentationslaget, forretningslogikken, dataadgangen og MySQL, hvor det er relevant.
3. Kontrollér, at hvert lag har det rigtige ansvar, og at OpenAPI beskriver API'ets faktiske opførsel.
4. Find ud af, hvor nøgletallene beregnes, og om Tableau kan hente de aktuelle data gennem API'et.
5. Sammenhold ændringen med acceptkriterierne og kravene til Docker, README og bidragsvejledning.
6. Beskriv fund med filstier og konkrete eksempler. Angiv for hvert krav, om det er opfyldt, mangler eller stadig skal afklares. Opret opgaver for mangler.
7. Forklar arkitekturens fordele og ulemper i et sprog, gruppen kan bruge til at præsentere løsningen.

