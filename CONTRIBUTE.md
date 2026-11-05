# Bidrag til Hotel Kong Arthur

## Start med projektgrundlaget

Læs [Spec Kit-overblikket](specs/README.md), [constitution](.specify/memory/constitution.md), [Specify](specs/004-hotelsystem/spec.md), [Clarify](specs/004-hotelsystem/clarify.md), [Plan](specs/004-hotelsystem/plan.md) og den aktuelle [taskliste](specs/004-hotelsystem/tasks.md). Tableau-forbindelsen og dashboardet er delvist afprøvet; resterende prøver og åbne afklaringer står i tasklisten og [Tableau-vejledningen](tableau/README.md).

Følg Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge. Plan vælges før implementering, Tasks organiseres efter brugerhistorier, og OpenAPI-kontrakten skrives og godkendes før endpoints implementeres. Krav og acceptkriterier vedligeholdes i spec.md; afklaringer og begrundelser dokumenteres i clarify.md.

## Git og gennemgang

Arbejd på en branch og læg ændringer ind via en pull request. Mindst ét andet gruppemedlem skal gennemgå og godkende den; der pushes ikke direkte til main. PR’en skal forklare problem, ændring, tilknyttet historie eller dokumentationsopgave og faktisk udført kontrol. Opdatér berørte krav, kontrakt og dokumentation i samme PR.

Dokumentation skrives på dansk. Kode, endpoints, JSON-felter og databasenavne skrives på engelsk. Bevar opgave-PDF’er og rådata uændrede. Spec Kits medfølgende værktøjsfiler vedligeholdes som eksternt værktøj.

## Arkitektur og verifikation

Følg [hotel-architecture-review](project-skills/hotel-architecture-review/SKILL.md) ved arkitektur- og acceptgennemgang. En booking skal følge browser → REST/JSON API → forretningslogik → dataadgang → PostgreSQL. SQL hører til i dataadgangen; domæneregler og officielle nøgletal hører til i logiklaget. Tableau bruger API’et.

Kontrollér dokumentationsændringer med `git diff --check` og kontrollér berørte links. Kør alle tests med én kommando. Den kræver kun Docker:

```sh
docker compose --profile test run --build --rm test
```

Kommandoen kører unit-, arkitektur-, kontrakt-, PostgreSQL- og browsertests mod en separat testdatabase, som ikke rører demoens data. Exitkoden er 0, når alt består. Testdatabasen og dens hjælpetjenester bliver kørende bagefter. Stop kun dem med `docker compose --profile test rm -sf test-db test-backend test-frontend`. Brug ikke `docker compose --profile test down`, for den stopper også en kørende demo. Demoens data bevares dog, så længe `-v` ikke bruges.

Når funktioner implementeres, skal tests kontrollere regler, beregninger, kontrakt og relevante acceptkriterier. Et nyt endpoint skal først stå i `specs/004-hotelsystem/contracts/openapi.yaml`, og det skal fjernes fra listen `NOT_IMPLEMENTED_YET` i `backend/tests/contract/test_api_uses_contract.py`. Ændrede afhængigheder skrives i `backend/requirements.in` eller `backend/requirements-test.in`, og `backend/requirements.lock` opdateres i samme PR. Converge dokumenterer bevis og status for hvert kriterium; mangler bliver til nye Tasks.

## Milepæl 3: målrettet kontrol

De håndberegnede US5–US9-eksempler findes i `backend/tests/unit/test_sale_rules.py`, `test_analytics_rules.py`, integrationsfilerne `test_sales_api.py`, `test_sales_service.py`, `test_analytics_api.py` og `test_analytics_snapshot.py` samt `tests/browser/test_sale_flows.py`. API-svar sammenlignes med den versionsstyrede kontrakt gennem `assert_matches_contract`. En negativ kontrol viser, at et beløb med forkert JSON-type bliver afvist af hjælperen.

Kontrollér, at testene opdager bevidste regelfejl:

```sh
docker compose --profile test run --rm test python backend/testsupport/check_milestone3_mutations.py
```

Scriptet ændrer kun en midlertidig projektkopi inde i testcontaineren. Det kontrollerer medregnet afrejsedag, medregnede aflyste bookinger/salg, gæsteantal ganget på omsætning og manglende konsistent snapshot. En importfejl eller tom testkørsel tæller ikke som en fundet mutation. Det benytter kun testdatabasen.

Demoens browserprøve kan gentages efter `docker compose up -d --build`:

```sh
docker compose --profile test run --rm -e PYTHONPATH=/workspace/backend test python backend/testsupport/smoke_milestone3.py
```

Prøven bruger Chromium i testcontaineren og `host.docker.internal:8080/8081` til demoen på Docker Desktop. `DEMO_URL` og `SWAGGER_URL` kan overskrives med `-e`, hvis værten er en anden. Den opretter en navngivet prøvebooking og et salg, kontrollerer analysernes ændringer og Swagger UI, og aflyser sine egne poster i `finally`. De bevares i historikken; der slettes ingen eksisterende data eller volumes. Kør den uden samtidige demoændringer, da den sammenligner totaler før/efter.

Læs [Milepæl 3-kontrollen](specs/004-hotelsystem/milestone-3.md) som en afgrænset historisk kontrol af backendændringerne. Den dækker ikke senere Tableau-arbejde eller den samlede aflevering. Aktuel status for Tableau, resterende prøver og Converge står i [README](README.md) og [tasklisten](specs/004-hotelsystem/tasks.md).

## Ændringer i brugerfladen

Følg [US16-forløbet](specs/006-enkel-brugerflade/spec.md) ved den visuelle forenkling. Kontrollér alle tre sider på computer og mobil, tastaturnavigation, synligt fokus, fejl uden tab af indtastninger samt reduceret bevægelse. Bevar alle API-forløb og analyseværdier. Den automatiske browserkontrol erstatter ikke testpersonens bookingprøve T063.

## Ejerskab

Hvert gruppemedlem skal kunne forklare og vurdere egne bidrag, også når AI er brugt. Beskriv kun arbejde og tests, der faktisk er udført. Alle medlemmers deltagelse skal kunne underbygges af deres egne commits; tilskriv ikke andres arbejde til dig selv.
