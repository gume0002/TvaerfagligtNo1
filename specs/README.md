# Spec Kit-forløb for Hotel Kong Arthur

Opgaven angiver rækkefølgen **Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge**. Den foreskriver ikke bestemte mappenavne. Projektet bruger Spec Kits filnavne og én aktiv mappe, `004-hotelsystem`, til hotelsystemets samlede forløb. Nummeret er en historisk identitet, ikke et fasenummer.

| Fase | Dokument eller resultat | Status og ansvar |
|---|---|---|
| Constitution | [constitution.md](../.specify/memory/constitution.md) | Fælles principper og faste krav. PR #2 er merged, men GitHub viser ingen formel reviewgodkendelse; gruppens godkendelse er ikke dokumenteret. Én fælles fil. |
| Specify | [spec.md](004-hotelsystem/spec.md) | Funktioner, brugere, domæneregler, krav, brugerhistorier og acceptkriterier. Dette er den gældende kravbeskrivelse, ikke bevis på at alle kriterier er kontrolleret. |
| Clarify | [clarify.md](004-hotelsystem/clarify.md) | Afklaringer, begrundelser, kontrol mod opgaven og åbne punkter. Ændrede krav er indarbejdet i spec.md. |
| Plan | [plan.md](004-hotelsystem/plan.md) | Teknisk design fra 29. oktober 2026. Nogle statusnoter i planen beskriver forholdene på det tidspunkt; den aktuelle status står i [tasks.md](004-hotelsystem/tasks.md) og [tableau/README.md](../tableau/README.md). |
| Tasks | [tasks.md](004-hotelsystem/tasks.md) | Opgaverne er grupperet efter brugerhistorie og viser designporte, afhængigheder og status. |
| Implement | Applikationskode, kontrakt og Docker-tjenester | Hovedfunktionerne, OData-feedet og Tableau-dashboardet er implementeret. Resterende prøver og status pr. task står i [tasks.md](004-hotelsystem/tasks.md). |
| Converge | [converge.md](004-hotelsystem/converge.md) | Gennemført 2. november 2026 med status og bevis pr. krav. Åbne punkter står i dokumentet og i Tasks. |

## Filernes rolle

`checklists/requirements.md` er kvalitetschecklisten til Specify. Den er ikke en ekstra specifikation eller Clarify. Der oprettes ikke tomme Plan-, Tasks- eller Converge-dokumenter, som kan forveksles med udført arbejde.

Constitution ligger på Spec Kits eksisterende placering i `.specify/memory/`; den kopieres ikke til `specs/`. De tidligere dokumentationsopgaver ligger direkte under `specs/`:

- [001 – Dansk projektdokumentation](001-dansk-projektdokumentation/spec.md)
- [002 – Projektdatasæt](002-projektdatasæt/spec.md)
- [003 – Opgavebeskrivelse](003-opgavebeskrivelse/spec.md)

Deres planer, opgaver og Converge-resultater vedrører de enkelte dokumentationsopgaver og er ikke implementeringsbevis for hotelsystemet.

## Næste trin

Læs constitution, spec, clarify og [plan](004-hotelsystem/plan.md) i den rækkefølge. De vigtigste rester står i [tasks.md](004-hotelsystem/tasks.md): underviserafklaringer, resterende Tableau-refresh-prøver, samlet test- og acceptgennemgang, Converge, gruppereview og præsentationsforberedelse.

Ved brug af de medfølgende Spec Kit-scripts kan den aktive mappe angives eksplicit fra projektroden:

```sh
SPECIFY_FEATURE_DIRECTORY=specs/004-hotelsystem bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

Kommandoen viser de forventede stier og opretter ikke Plan eller Tasks. Den kontrollerer ikke, at faserne er færdige.
