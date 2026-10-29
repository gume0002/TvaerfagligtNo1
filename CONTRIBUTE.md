# Bidrag til Hotel Kong Arthur

## Start med projektgrundlaget

Læs [Spec Kit-overblikket](specs/README.md), [constitution](.specify/memory/constitution.md), [Specify](specs/004-hotelsystem/spec.md) og [Clarify](specs/004-hotelsystem/clarify.md) og [Plan](specs/004-hotelsystem/plan.md). Projektets aktuelle fase er gennemgang af Plan med åbne Tableau-afklaringer.

Følg Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge. Plan vælges før implementering, Tasks organiseres efter brugerhistorier, og OpenAPI-kontrakten skrives og godkendes før endpoints implementeres. Krav og acceptkriterier vedligeholdes i spec.md; afklaringer og begrundelser dokumenteres i clarify.md.

## Git og gennemgang

Arbejd på en branch og læg ændringer ind via en pull request. Mindst ét andet gruppemedlem skal gennemgå og godkende den; der pushes ikke direkte til main. PR’en skal forklare problem, ændring, tilknyttet historie eller dokumentationsopgave og faktisk udført kontrol. Opdatér berørte krav, kontrakt og dokumentation i samme PR.

Dokumentation skrives på dansk. Kode, endpoints, JSON-felter og databasenavne skrives på engelsk. Bevar opgave-PDF’er og rådata uændrede. Spec Kits medfølgende værktøjsfiler vedligeholdes som eksternt værktøj.

## Arkitektur og verifikation

Følg [hotel-architecture-review](project-skills/hotel-architecture-review/SKILL.md) ved arkitektur- og acceptgennemgang. En booking skal følge browser → REST/JSON API → forretningslogik → dataadgang → MySQL. SQL hører til i dataadgangen; domæneregler og officielle nøgletal hører til i logiklaget. Tableau bruger API’et.

Kontrollér dokumentationsændringer med `git diff --check` og kontrollér berørte links. Der findes endnu ingen kørende applikation eller testopsætning. Plan vælger `docker compose --profile test run --build --rm test` som kommende fælles testkommando; den kan først køres, når Compose og runner er implementeret. Når funktioner implementeres, skal tests kontrollere regler, beregninger, kontrakt og relevante acceptkriterier. Converge dokumenterer bevis og status for hvert kriterium; mangler bliver til nye Tasks.

## Ejerskab

Hvert gruppemedlem skal kunne forklare og vurdere egne bidrag, også når AI er brugt. Beskriv kun arbejde og tests, der faktisk er udført. Alle medlemmers deltagelse skal kunne underbygges af deres egne commits; tilskriv ikke andres arbejde til dig selv.
