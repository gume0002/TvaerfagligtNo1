# Spec Kit-forløb for Hotel Kong Arthur

Opgaven angiver rækkefølgen **Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge**. Den foreskriver ikke bestemte mappenavne. Projektet bruger Spec Kits filnavne og én aktiv mappe, `004-hotelsystem`, til hotelsystemets samlede forløb. Nummeret er en historisk identitet, ikke et fasenummer.

| Fase | Dokument eller resultat | Status og ansvar |
|---|---|---|
| Constitution | [constitution.md](../.specify/memory/constitution.md) | Fælles principper og faste krav; afventer gruppens PR-godkendelse. Én fælles fil. |
| Specify | [spec.md](004-hotelsystem/spec.md) | Funktioner, brugere, domæneregler, krav, brugerhistorier og acceptkriterier. Dette er den gældende kravbeskrivelse. |
| Clarify | [clarify.md](004-hotelsystem/clarify.md) | Afklaringer, begrundelser, kontrol mod opgaven og åbne punkter. Ændrede krav er indarbejdet i spec.md. |
| Plan | `004-hotelsystem/plan.md` | Næste fase; endnu ikke udarbejdet. Teknologier, arkitektur, datamodel, kontrakt, Docker og Tableau-afprøvning. |
| Tasks | `004-hotelsystem/tasks.md` | Oprettes efter Plan; konkrete opgaver pr. brugerhistorie med afhængigheder. |
| Implement | Applikationskode, kontrakt og Docker-tjenester | Udføres ud fra Tasks; endnu ikke implementeret. |
| Converge | `004-hotelsystem/converge.md` | Oprettes ved gennemgang af implementeringen; bevis og status pr. acceptkriterium samt mangler til Tasks. |

## Filernes rolle

`checklists/requirements.md` er kvalitetschecklisten til Specify. Den er ikke en ekstra specifikation eller Clarify. Der oprettes ikke tomme Plan-, Tasks- eller Converge-dokumenter, som kan forveksles med udført arbejde.

Constitution ligger på Spec Kits eksisterende placering i `.specify/memory/`; den kopieres ikke til `specs/`. De tidligere dokumentationsopgaver ligger direkte under `specs/`:

- [001 – Dansk projektdokumentation](001-dansk-projektdokumentation/spec.md)
- [002 – Projektdatasæt](002-projektdatasæt/spec.md)
- [003 – Opgavebeskrivelse](003-opgavebeskrivelse/spec.md)

Deres planer, opgaver og Converge-resultater vedrører de enkelte dokumentationsopgaver og er ikke implementeringsbevis for hotelsystemet.

## Næste trin

Læs constitution, spec og clarify i den rækkefølge. Udarbejd derefter Plan med de åbne afklaringer om kundetilfredshed og Tableau-systemgrænse samt en tidlig afprøvning af opdateringskravet. OpenAPI-kontrakten skal skrives og godkendes før endpointimplementering.

Ved brug af de medfølgende Spec Kit-scripts kan den aktive mappe angives eksplicit fra projektroden:

```sh
SPECIFY_FEATURE_DIRECTORY=specs/004-hotelsystem bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

Kommandoen viser de forventede stier og opretter ikke Plan eller Tasks. Den kontrollerer ikke, at faserne er færdige.
