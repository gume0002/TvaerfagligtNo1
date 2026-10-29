# Spec Kit-forløb for Hotel Kong Arthur

Opgaven angiver rækkefølgen **Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge**. Den foreskriver ikke bestemte mappenavne. Projektet bruger Spec Kits filnavne og én aktiv mappe, `004-hotelsystem`, til hotelsystemets samlede forløb. Nummeret er en historisk identitet, ikke et fasenummer.

| Fase | Dokument eller resultat | Status og ansvar |
|---|---|---|
| Constitution | [constitution.md](../.specify/memory/constitution.md) | Fælles principper og faste krav; afventer gruppens PR-godkendelse. Én fælles fil. |
| Specify | [spec.md](004-hotelsystem/spec.md) | Funktioner, brugere, domæneregler, krav, brugerhistorier og acceptkriterier. Dette er den gældende kravbeskrivelse. |
| Clarify | [clarify.md](004-hotelsystem/clarify.md) | Afklaringer, begrundelser, kontrol mod opgaven og åbne punkter. Ændrede krav er indarbejdet i spec.md. |
| Plan | [plan.md](004-hotelsystem/plan.md) | Teknisk plan udarbejdet til gennemgang; Tableau Public er bekræftet; manuel refresh er accepteret; praktisk afprøvning og fortolkningsrisici er åbne. |
| Tasks | [tasks.md](004-hotelsystem/tasks.md) | Første udførelsesudkast er udarbejdet efter Plan; opgaverne er grupperet efter brugerhistorie og viser designporte og afhængigheder. |
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

Læs constitution, spec, clarify og [plan](004-hotelsystem/plan.md) i den rækkefølge. Gennemgå Plan og task-udkastet med gruppen. Udfør den tidlige prøve af manuel datakilde-refresh i Tableau Public, og skriv/gennemgå OpenAPI-kontrakten før endpointimplementering. Task-udkastet markerer disse som designporte og skal justeres, hvis Tableau-prøven ændrer integrationsdesignet.

Ved brug af de medfølgende Spec Kit-scripts kan den aktive mappe angives eksplicit fra projektroden:

```sh
SPECIFY_FEATURE_DIRECTORY=specs/004-hotelsystem bash .specify/scripts/bash/check-prerequisites.sh --paths-only --json
```

Kommandoen viser de forventede stier og opretter ikke Plan eller Tasks. Den kontrollerer ikke, at faserne er færdige.
