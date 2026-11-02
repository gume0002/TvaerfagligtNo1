# Milepæl 3 – barsalg og analyser gennem API'et

**Dato:** 2. november 2026. **Branch:** `milepael-3-barsalg-analyser` fra opdateret `origin/main` (`cbe60b8`). Arbejdstræet var rent ved start. `git config user.name` viste `magnusegemoseornhof`; commits bruger denne konfiguration. Ved afslutningen af implementeringskontrollen var der endnu ikke udført push eller oprettet PR; efterfølgende levering sker efter brugerens særskilte anmodning.

Dette er en afgrænset Implement-kontrol af Milepæl 3, ikke gruppens samlede Converge eller godkendelse af afleveringen. Projektets `hotel-architecture-review`-vejledning er brugt. Begge opgave-PDF'er, constitution, spec, clarify, plan, kontrakt, tasks og eksisterende bookingforløb er læst før implementeringen. Ingen rådata eller opgave-PDF'er er ændret.

## Leverance og taskstatus

- **Færdige i denne milepæl:** T033, resten af T034, T035–T040, T041–T043, T045, T046, T048, T049 og T051. Resterne fra T012, T029 og T032 er afsluttet og testet.
- **Delvist færdige samlet:** T047 og T050. API-delene er implementeret og kontraktkontrolleret; Tableau-delene er ikke påbegyndt her.
- **Ikke påbegyndt her:** T044, T052–T055 og T062–T068. T001/T002 er fortsat menneskelige/designmæssige afklaringer; T003 er fortsat delvis, fordi Tableau-feedets kontrakt mangler. Der ændres ikke ved tidligere milepæles afkrydsninger.

Én nødvendig afklaring blev godkendt af brugeren før implementeringen: rang ved lige omsætning følger konkurrenceplacering (`1, 1, 3`). Det er dokumenteret i `clarify.md` og præciseret i begge ranglistebeskrivelser i OpenAPI. Ingen endpoints eller schemas er tilføjet til den vedtagne REST-kontrakt. Alle implementerede endpoints er fjernet fra `NOT_IMPLEMENTED_YET`, som nu er et tomt set.

## Acceptkriterier og konkrete beviser

Filerne nedenfor er relative til projektets rod. Status for US7–US9 gælder API/beregning; Tableau-visninger er åbne.

| Kriterium | Kontrol / fil | Resultat |
|---|---|---|
| US5.1 | `backend/tests/integration/test_sales_api.py::test_us5_creation_and_replay` og `tests/browser/test_sale_flows.py::test_form_uses_catalog_and_saves` | 3 enheder og 300,00 DKK; oprettet i browser/API |
| US5.2 | Parametriserede `test_us5_invalid_input`, `backend/tests/unit/test_sale_rules.py` og browserens `test_backend_errors_keep_form` | Antal, pris, referencer og fremtidsdato afvises; formularværdier bevares |
| US5.3 | `test_sales_service.py::test_creation_freezes_price_and_checks_references` og `test_sales_api.py::test_frozen_price_replay_after_changes_and_invalid_writes_leave_no_rows` | Katalogpris ændrer ikke salgets pris; gentagelser opretter ikke dubletter |
| US6.1 | `test_sales_api.py::test_read_update_cancel_and_history` og `test_all_sale_fields_can_be_changed` | 3 → 2 giver 200,00 DKK; alle redigerbare felter kontrolleret |
| US6.2–6.3 | Samme tests, `test_update_cancel_and_atomic_errors`, browserens `test_saved_sale_survives_reload_and_can_be_edited_cancelled`, `test_analytics_api.py::test_us9_2_year_employee_and_us6_2_cancelled_excluded` | Historik, idempotent aflysning, ingen genaktivering, afvist rettelse uændret og intet analysebidrag |
| Idempotens, US5/US6 | `test_sales_api.py::test_simultaneous_creation_with_same_key_commits_once` og browserens `test_lost_response_reuses_key` | To uafhængige forespørgsler gemmer én post; tabt svar kan gentages |
| US7.1 | Unit- og API-testen `test_us7_1_year_boundary` | 30/12–2/1 til 1.000 DKK giver 2.000/1.000 DKK over årsskiftet |
| US7.2 | `test_analytics_api.py::test_us7_2_tied_firsts_and_next_is_third` og unit-testen `test_us7_2_competition_rank_for_countries_and_types` | 3.000/3.000/2.000 DKK giver rang 1/1/3 for typer og lande |
| US7.3 | `test_analytics_api.py::test_us7_3_guests_and_revenue` | 2 gæsteophold, 3 værelsesnætter, 3.000 DKK |
| US7.4 | `test_us7_5_season_type_breakdown_and_combined_filters`, unit-testen `test_filters_combine_and_cancelled_bookings_are_excluded` | År/sæson/land/type kombineres; aflysninger udelades |
| US7.5 | Unit-testen `test_us7_5_season_boundary` og API-testen ovenfor | 28/2–2/3 2026 giver 1.000 DKK i lav og 1.000 i mellem for samme type |
| US8.1 | `test_analytics_rules.py::test_us8_1_two_rooms_two_nights` | 2 bookede / 4 tilgængelige nætter = 50,00 %; ADR 1.000,00 DKK. API'et tilbyder år/sæson, ikke et vilkårligt todagesfilter |
| US8.2 | `test_analytics_api.py::test_us8_2_leap_year`, `test_us8_2_past_and_upcoming_use_frozen_business_date` | 366 døgn pr. værelse; 28/10–31/10 giver 1.000 passeret og 2.000 kommende pr. frosset 29/10 |
| US8.3 | `test_us8_3_no_data_and_country_denominator`, unit-testen `test_us8_3_zero_bookings_and_zero_capacity` | Nulomsætning, ADR null/no_data, 0 % ved positiv kapacitet, tilfredshed kun no_data |
| US9.1 | Unit-testen `test_us9_1_bar_mix` og API-testen `test_us9_1_bar_amounts_categories_and_drinks` | 400 DKK, 5 drikke, antalandele 60/40 %, omsætningsandele 75/25 % |
| US9.2 | `test_us9_2_year_employee_and_us6_2_cancelled_excluded` | Helene er standard; år og medarbejder afgrænser alle opdelinger |
| US9.3 | `test_us9_3_no_sales`, aflysningstesten og unit-testen `test_us9_3_no_sales_keeps_catalog_and_both_categories` | Nulsummer og null/no_data for andele; alle katalogdrikke og begge kategorier bevares |
| US9.4 | `test_us9_4_seed_catalog_includes_twenty_cocktails_ten_coffees` | De faktiske seedkataloger giver 20 cocktails/10 kaffe i byDrink, også uden salg |
| US4.2 / T029/T032 | `test_us4_2_cancelled_booking_contributes_nothing` og de eksisterende bookingtests | Aflysning fjerner omsætning, nætter, gæsteophold og ranglistebidrag; kapacitet og idempotens består |
| T012 / konsistent grundlag | `backend/tests/integration/test_analytics_snapshot.py` | Samtidigt committede ændringer blander ikke katalog og driftsdata i samme analyse; skriveisolation forbliver READ COMMITTED |
| FR-003–FR-006 | Salgs- og analysetests ovenfor | Backend/API-delen dækket; Tableau-kravet er ikke godkendt |
| FR-009–FR-012 | `backend/tests/contract/`, `test_architecture.py`, browser-/integrationstests og demo-prøven | REST-kontrakt, laggrænser, JSON-fejl og automatiske kontroller består; samlet Converge er stadig åben |

## Faktisk kørt

| Kommando / prøve | Resultat |
|---|---|
| `git status --short --branch`, `git config user.name`, `git fetch origin` | Rent udgangspunkt; forfatterkontrol; branch fra opdateret main |
| `docker compose --profile test run --build --rm test` før ændringer | Exit 0: 207 bestået |
| Målrettede pytest-kørsler under T033–T051 | Bestået før task-afkrydsning; se commits med tasknumre |
| Samme fulde Docker-testkommando efter implementering | Exit 0: **292 bestået**, én eksisterende Starlette/httpx-deprecation-advarsel; ingen tests sprunget over |
| `docker compose --profile test run --rm test python backend/testsupport/check_milestone3_mutations.py` | Exit 0: alle fem mutationer gav en forventet assertion-fejl i den relevante test |
| `docker compose up -d --build` | Exit 0: database sund, init afsluttet, backend sund, frontend og Swagger startet |
| `docker compose --profile test run --rm -e PYTHONPATH=/workspace/backend -e EVIDENCE_DIR=/evidence -v /private/tmp/hotel-milestone3-evidence:/evidence test python backend/testsupport/smoke_milestone3.py` | Exit 0: browseroprettelse/aflysning, begge analyse-JSON-sider, barsalg, mobilbredde og Swagger UI kontrolleret |
| `git diff --check` | Exit 0 |

Demoens observerede hotelomsætning var **128250.00 → 130250.00 → 128250.00 DKK** efter oprettelse og aflysning af prøvebooking nr. 25. Baromsætningen var **1663.47 → 1963.47 DKK** efter salg nr. 13 (3 × 100 DKK). Prøvens egne poster blev aflyst, og begge analysetotaler blev kontrolleret tilbage på udgangspunktet. Aflyste poster forbliver i historikken. Screenshots af mobilformular og Swagger blev gemt og visuelt inspiceret i `/private/tmp/hotel-milestone3-evidence/`; de er lokale kontrolartefakter, ikke versionsstyrede krav.

Den interaktive browservært var utilgængelig. Browserkontrollen er derfor kørt automatiseret i Chromium via Playwright, ikke som en menneskelig acceptprøve. Testpersonens prøve, Tableau/Public-refresh, underviserafklaring, gruppens review og den samlede Converge er **ikke afprøvet/godkendt** her.

## Kontrol af testenes følsomhed

Mutationsscriptet kopierer projektet til en midlertidig mappe inde i testcontaineren og genopretter originalkilden mellem forsøg. Der ændres aldrig regler i arbejdsbranchens løsning for at udføre prøven. Det kræver exitkode 1 og navnet på den fejlende test; en importfejl tæller ikke.

| Midlertidig forkert regel | Test der faktisk fejlede |
|---|---|
| Afrejsedag tælles med | `test_us7_1_year_boundary` |
| Aflyste bookinger tælles med | `test_us4_2_cancelled_booking_contributes_nothing` |
| Aflyste salg tælles med | `test_us9_2_year_employee_and_us6_2_cancelled_excluded` |
| Gæsteantal ganges på natomsætningen | `test_us7_3_guests_and_revenue` |
| Konsistent snapshot erstattes med READ COMMITTED | `test_both_analyses_read_rows_from_their_catalog_snapshot` |

Desuden består `test_contract_assertion_rejects_wrong_metric_type` kun, hvis kontrakthjælperen faktisk afviser et manipuleret svar med numerisk omsætning. Endpointkontrollen kræver fundne routes og præcis lighed med kontraktens operationer; et tomt eller ikke-gennemløbet resultat giver ikke et falsk bevis.

## Arkitektur og forklaring til fremlæggelsen

Et barsalg følger `frontend/sales.html` / `js/sales.js` → Nginx → `api/sales.py` → `business/sale_service.py` → `SqlSaleRepository` / `SqlUnitOfWork` → MySQL. API-laget oversætter formater og HTTP. Businesslaget validerer regler, vælger statusskift og ejer idempotensforløbet. Dataadgangen låser og gemmer salg og idempotensresultat i én transaktion. En fejl ruller begge tilbage. Backendens beregnede `totalAmount` vises direkte i browseren.

Et analysekald følger `api/analytics.py` → `business/analytics_service.py` → Unit of Work og katalog-/booking-/salgsrepositories → MySQL. Dataadgangen leverer almindelige domæneobjekter. Den foretager datoafgrænsede opslag, men beregner ingen officielle summer, andele eller nøgletal i SQL. Businesslaget udelader aflyste poster, splitter nætter og beregner alle grupper fra samme udvalg. API-laget formaterer Decimal og datoer uden egne formler.

Eksempel: ét værelse booket begge nætter til 1.000 DKK giver 2.000 DKK og to bookede værelsesnætter. To værelser til rådighed begge nætter giver fire tilgængelige værelsesnætter. Belægningen er 2/4 × 100 = 50 %, ADR er 2.000/2 = 1.000 DKK. Antal gæster ændrer gæsteophold, men ikke værelsesnætter eller omsætning. Kalenderårets/sæsonens datoer bestemmer nævneren i API'et; landefilteret reducerer ikke hotellets kapacitet.

**SWA-spørgsmål:** 1 dækkes af README-diagrammet; 2–3 af de konkrete requestforløb og den uændrede arkitekturtest; **4** af alle nøgletal i businesslaget med håndberegnede testbeviser. Flyttes formler til SQL eller Tableau, bliver dataadgang/klienter afhængige af hotelregler og kan levere andre tal. 5 dækkes af domæneobjekter og repositorygrænsen ved databaseskift; 6–7 af CRUD/statuskoder og den styrende OpenAPI-kontrakt; 8 af Compose og snapshot-/skrivetransaktioner; 9 understøttes af aktuelle API-resultater efter ændringer, men Tableau er fortsat åben. 10 kræver gruppens egen vurdering og reelle bidrag; AI har ikke fordelt eller tilskrevet arbejde til medlemmer.

## Afvigelser, risici og næste handlinger

Ingen teknologiafvigelser eller nye domænekrav. Rangreglen er den brugerautoriserede præcisering. T043 blev klargjort først, men kunne først godkendes efter T046/T047, fordi den eksisterende kontrakt kræver belægning, ADR og tilfredshedsstatus i samme hotelrespons. Tasknoter blev først fjernet efter bestået fuld kontraktkontrol.

Snapshot giver konsistente læsninger pr. forespørgsel; to separate kald kan naturligt se forskellige committede data. Gennemskuelig beregning i hukommelsen er planens valg til prototypens størrelse. Der er fortsat ingen adgangskontrol eller cache, og aflysning ændrer også historiske analyser. Tilfredshed kan ikke beregnes uden vurderingsdata. Tableau-forbindelse, filtre og refresh skal fortsat afprøves i T002/T052–T055. Gruppen skal gennemgå PR'en og tage stilling til de åbne fortolkningsrisici; T062–T068 er ikke afkrydset af denne milepæl.

## Forslag til PR-tekst

**Titel:** Milepæl 3: barsalg og aktuelle hotel- og baranalyser gennem API'et

**Problem:** Bookinger kunne vedligeholdes, men barsalg og de vedtagne nøgletal var endnu ikke tilgængelige gennem REST API'et.

**Ændring:** Implementér US5/US6 med browserforløb, fastfrosset pris, idempotent oprettelse, rettelse og logisk aflysning. Lever API-delene af US7–US9 med natfordelt omsætning, gæstelande, ranglister med 1/1/3, belægning, ADR og barandele. Alle tal beregnes i businesslaget fra ét konsistent MySQL-snapshot pr. analyse. Afslut snapshot-/analyseudeladelsesrester fra Milepæl 2, og opdatér README, CONTRIBUTE, OpenAPI og taskstatus. Tableau og den samlede Converge er uden for PR'en.

**Kontrol:** Den fulde Docker-testkommando giver 292 beståede tests og exit 0. Fem bevidste regelfejl i en midlertidig projektkopi opdages af relevante tests. En automatiseret Chromium-prøve mod demoen kontrollerer barsalg, begge analyser, Swagger UI og omsætningsændring efter booking/aflysning. Testperson, Tableau-refresh og gruppens review er ikke udført. Prøvens egne poster er aflyst; ingen volumes er slettet.

## Overdragelse til næste milepæl

Brug [prompten til Milepæl 4](prompt-milestone-4.md) efter gruppens review og merge af Milepæl 3. Den fastholder de åbne designporte, de vedtagne regler og kravet om faktiske Tableau- og menneskelige acceptbeviser. Prompten er forberedelse, ikke en påbegyndt implementering af Milepæl 4.
