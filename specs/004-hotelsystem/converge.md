# Converge: Hotelsystem

**Dato:** 2. november 2026. **Kontrolleret version:** branchen `milepael-4-converge`.

**Status:** Systemet er implementeret, og alle krav kan kontrolleres mod det. Enkelte krav er kun delvist opfyldt eller ikke afprøvet endnu, og to fortolkningsrisici er åbne. T055 og T063 er udført ifølge gruppens bekræftelse 5. november 2026. Resultatet af bookingprøven og de detaljerede målinger for 48 af refresh-runderne mangler i dokumentationen. Gruppens review og præsentation står åbne.

**Statusopdatering 5. november 2026:** Gruppen har bekræftet, at alle 60 SC-003-refresh-runder og den manuelle bookingprøve er gennemført. Kontrolarket gengiver detaljer for 12 runder. Bookingprøvens varighed/resultat samt resultaterne for de øvrige 48 runder skal føres ind, før SC-001 og SC-003 kan markeres fuldt opfyldt i denne Converge.

**Status før fremlæggelsen, 5. november 2026:** Systemet kører nu på PostgreSQL og viser analyserne i browseren. Se [Converge for tillægsopgaven](../005-tillaeg-uge-2/converge.md). T069–T071 er vurderet som ikke nødvendige, fordi logikken er dækket af automatiske tests, og refresh i Tableau er afprøvet i T054, T055 og T093. De konkrete valg i Tableau er ikke prøvet, så de tilhørende krav står fortsat som delvist opfyldt. Før fremlæggelsen er kun T067 og T068 tilbage her. Vurderingen er foreslået af Mathilde, og gruppen godkender den i pull requesten.

Denne gennemgang er udarbejdet med AI og beskriver det, der faktisk er kørt eller observeret. Den er ikke en godkendelse fra gruppen eller underviseren.

**Status betyder:**

- **Opfyldt:** Kontrolleret og virker.
- **Delvist:** En del er kontrolleret, og begrænsningen står i rækken.
- **Ikke afprøvet:** Kræver en handling, som ikke er udført.
- **Åben:** Fortolkningsrisiko, som gruppen har valgt ikke at afstemme.

## Samlet resultat

| Område | Opfyldt | Delvist | Ikke afprøvet |
|---|---:|---:|---:|
| Acceptkriterier (36) | 32 | 4 | 0 |
| Funktionelle krav (12) | 10 | 2 | 0 |
| Succeskriterier (7) | 3 | 4 | 0 |

## Faktisk kørt

| Kontrol | Resultat |
|---|---|
| `docker compose --profile test run --build --rm test` | 342 tests består, exitkode 0, ingen sprunget over |
| `docker compose --profile test run --rm test python backend/testsupport/check_milestone3_mutations.py` | Alle fem bevidste regelfejl blev fanget |
| Bevidste fejl i feedet (kopi af projektet) | Sæson- og landefilter, år, aflyste salg, metadata og afrunding blev fanget. Kontrolkørslen uden virksom fejl bestod |
| Frisk `git clone` og `docker compose up --build` | Alle tjenester startede, og alle undersøgte adresser svarede 200 |
| Genstart i den friske kopi | Ny booking bevaret, startdata ikke indlæst igen |
| Tableau Public 2026.3 (udført af et gruppemedlem) | Se [`tableau/README.md`](../../tableau/README.md) og [kontrolarket](../../tableau/sc003-kontrolark.md) |

**Bemærk:** Den ene bevidste fejl, der ændrede landeudvalget i `_bookings_by_selection`-trinnet, bestod, fordi `hotel_result` filtrerer igen. Trinnet er kun en optimering. Da filteret blev ændret i selve kaldet til `hotel_result`, fejlede testen.

## Acceptkriterier

Testfilerne ligger i `backend/tests/integration/` og `tests/browser/`.

| Krav | Bevis | Status |
|---|---|---|
| US1.1 Gem og genfind | `test_bookings_api.py::TestUS1Create`, `test_booking_flows.py::test_created_booking_is_still_there_after_reload` | Opfyldt |
| US1.2 Afvis ugyldigt input | `test_invalid_input_is_rejected_and_nothing_is_created`, `test_too_many_guests_show_an_understandable_error` | Opfyldt |
| US1.3 Sidste enhed | `test_booking_concurrency.py::test_two_requests_for_the_last_room_never_overbook`, `test_arrival_on_departure_day_is_allowed` | Opfyldt |
| US2.1 Navnesøgning | `TestUS2Search::test_name_search_ignores_case_and_shows_all_booking_details` | Opfyldt |
| US2.2 Opholdsinterval | `test_date_interval_shows_stays_with_at_least_one_common_night`, `test_name_and_dates_can_be_combined` | Opfyldt |
| US2.3 Tom tilstand og historik | `test_no_match_shows_the_empty_state`, `test_cancelled_bookings_are_only_shown_when_chosen` | Opfyldt |
| US3.1 Ret alle felter | `TestUS3Update::test_all_fields_are_saved_on_the_same_identity` | Opfyldt |
| US3.2 Afvis overbooking | `test_change_that_overbooks_is_rejected_and_the_booking_is_preserved`, `test_unchanged_dates_do_not_count_the_booking_twice` | Opfyldt |
| US3.3 Aftalt natpris | `test_agreed_rate_is_kept_unless_it_is_changed` | Opfyldt |
| US4.1 Sletning med historik | `TestUS4Delete`, `test_confirmed_delete_moves_the_booking_to_history` | Opfyldt |
| US4.2 Frigiver kapacitet, intet analysebidrag | `test_delete_frees_capacity`, `test_us4_2_cancelled_booking_contributes_nothing` | Opfyldt |
| US4.3 Gentaget sletning | `test_repeated_delete_changes_nothing`, `test_unknown_booking_gives_404_and_others_are_untouched` | Opfyldt |
| US5.1 Registrér salg | `test_sales_api.py::test_us5_creation_and_replay`, `test_form_uses_catalog_and_saves` | Opfyldt |
| US5.2 Afvis ugyldigt salg | `test_us5_invalid_input`, `test_backend_errors_keep_form` | Opfyldt |
| US5.3 Fastfrosset pris | `test_sales_service.py::test_creation_freezes_price_and_checks_references` | Opfyldt |
| US6.1 Ret salg | `test_read_update_cancel_and_history`, `test_all_sale_fields_can_be_changed` | Opfyldt |
| US6.2 Aflys salg | `test_saved_sale_survives_reload_and_can_be_edited_cancelled`, `test_us9_2_year_employee_and_us6_2_cancelled_excluded` | Opfyldt |
| US6.3 Ugyldig rettelse | `test_update_cancel_and_atomic_errors` | Opfyldt |
| US7.1 Årsskifte | `test_us7_1_year_boundary`, `test_odata_feed.py::test_us7_1_new_year_split` | Opfyldt |
| US7.2 Summer og ranglister | `test_us7_2_tied_firsts_and_next_is_third`, Tableau mod REST (`tableau/README.md`) | Opfyldt |
| US7.3 Gæster og nætter | `test_us7_3_guests_and_revenue`, `test_us7_3_guests_nights_and_revenue` | Opfyldt |
| US7.4 Kombinerede filtre | `test_hotel_totals_match_rest`. I Tableau er land og sæson kun kontrolleret hver for sig mod REST, ikke kombineret | Delvist |
| US7.5 Type pr. sæson | `test_us7_5_season_boundary`, `test_us7_5_room_type_split_on_season`, Tableau | Opfyldt |
| US8.1 50 % og ADR | `test_us8_1_two_rooms_two_nights`. ADR og belægning er også kontrolleret i Tableau med andre tal | Opfyldt |
| US8.2 Opdeling og skudår | `test_us8_2_leap_year`, `test_past_and_upcoming_are_separate`, Tableau | Opfyldt |
| US8.3 Nulgrundlag | `test_us8_3_no_bookings`, Tableau viste »Intet datagrundlag« med Denmark | Opfyldt |
| US9.1 Barens tal | `test_us9_1_bar_amounts_categories_and_drinks`, `test_us9_1_totals_and_shares`, Tableau mod REST | Opfyldt |
| US9.2 Medarbejder og år | `test_us9_2_year_employee_and_us6_2_cancelled_excluded`. Dropdown for medarbejder og andre år er ikke prøvet i Tableau | Delvist |
| US9.3 Nulgrundlag | `test_us9_3_no_sales`, `test_odata_feed.py::test_us9_3_no_sales`. Ikke set i Tableau | Delvist |
| US9.4 Alle 30 drikke | `test_us9_4_seed_catalog_includes_twenty_cocktails_ten_coffees`, Tableau viser drikke med 0,00 | Opfyldt |
| US10.1 Refresh | T054 og `tableau/sc003-kontrolark.md` | Opfyldt |
| US10.2 Afvist ændring og fejl | Fejl og uændret snapshot er observeret i T054. Afvist ændring er testet i API'et, men ikke med refresh i Tableau | Delvist |
| US10.3 Kun API | `tableau/hotel-and-bar.twbx` forbinder kun til `/api/odata/`, og feedet genbruger `hotel_result` og `bar_result` | Opfyldt |
| US11.1 Én kommando | Frisk kopi, se ovenfor | Opfyldt |
| US11.2 Startdata og volume | Frisk kopi og `test_schema_and_seed.py::TestRepeatedStart` | Opfyldt |
| US11.3 Swagger og dokumentation | Swagger UI viser kontrakten, inklusive `/api/odata/`. `README.md` og `CONTRIBUTE.md` er opdateret | Opfyldt |

## Funktionelle krav

| Krav | Bevis | Status |
|---|---|---|
| FR-001 Booking-CRUD | US1–US4 | Opfyldt |
| FR-002 Regler og samtidighed | `test_booking_concurrency.py`, `test_booking_rules.py` | Opfyldt |
| FR-003 Barsalg | US5–US6 | Opfyldt |
| FR-004 Omsætning og ranglister | US7. Kombinerede filtre i Tableau er ikke set | Delvist |
| FR-005 Belægning og ADR | US8 | Opfyldt |
| FR-006 Baranalyser | US9. Medarbejderskift i Tableau er ikke set | Delvist |
| FR-007 Refresh | T054, T055 | Opfyldt |
| FR-008 MySQL som datakilde | `test_schema_and_seed.py`, frisk kopi | Opfyldt |
| FR-009 OpenAPI og Swagger UI | `backend/tests/contract/`, `assert_matches_contract` på svar | Opfyldt |
| FR-010 Regler i logiklaget | `test_architecture.py` | Opfyldt |
| FR-011 Ensartede JSON-fejl | `TestErrors`, `TestEmptyFormFields` | Opfyldt |
| FR-012 Automatiske tests og Converge | Testkommandoen og dette dokument | Opfyldt |

## Succeskriterier

| Krav | Bevis | Status |
|---|---|---|
| SC-001 Testperson på to minutter | Bookingprøven er udført ifølge gruppens bekræftelse. Varighed og resultat er ikke registreret | Delvist |
| SC-002 Kontrollerede eksempler | Automatiske tests af US1–US9 | Opfyldt |
| SC-003 Refresh-prøver | Gruppen bekræfter 60 gennemførte runder. Kontrolarket viser detaljer for 12; resultaterne for 48 runder mangler i dokumentationen. | Delvist |
| SC-004 Sidste enhed | 20 gentagelser mod MySQL, og testen fejler uden låsen | Opfyldt |
| SC-005 Frisk start | Frisk kopi og genstart. Tableau er dokumenteret særskilt | Opfyldt |
| SC-006 Ens tal | API og Tableau er sammenlignet. Frontenden viste ikke analyser ved denne gennemgang. Det gør den nu, og API, browser og Tableau er sammenlignet for to filtervalg i [tillægsopgavens Converge](../005-tillaeg-uge-2/converge.md) | Delvist |
| SC-007 Visninger og dokumentation | Alle visninger, `README.md`, `CONTRIBUTE.md` og Swagger UI findes, men er ikke fremvist for gruppen | Delvist |

## Opgavens krav

| Krav | Status |
|---|---|
| Tre lag, REST/JSON, OpenAPI og Swagger UI i Docker | Opfyldt. `$metadata` er XML, fordi OData kræver det. Alle data er JSON |
| MySQL og Docker Compose | Opfyldt |
| Browserfrontend til bookinger | Opfyldt |
| Løbende opdatering | Opfyldt gennem API'et. Tableau viser nye tal efter manuel refresh, ikke automatisk |
| Hotelvisninger og ekstra nøgletal (ADR, belægning) | Opfyldt |
| Cocktailbar | Opfyldt |
| **Kundetilfredshed** | **Åben.** Der findes ingen data, så der vises »Intet datagrundlag«. Opgaven nævner nøgletallet, og det er ikke afstemt |
| **"Alt i jeres system" i `docker-compose up`** | **Åben.** Tableau Public kører uden for Docker. Det er ikke afstemt |
| Spec Kit-artefakter og user stories | Opfyldt |
| Alle medlemmers commits | Kræver gruppens vurdering, se nedenfor |

## En forespørgsel gennem systemet

**Oprettelse af en booking:**

1. `frontend/js/app.js` (`submitBooking`) sender JSON og en idempotensnøgle gennem `frontend/js/api.js`.
2. Nginx sender `/api/` videre (`frontend/nginx.conf`).
3. `backend/app/api/bookings.py` (`create_booking`) kontrollerer formatet med `BookingBody` og laver et domæneobjekt.
4. `backend/app/business/booking_service.py` (`create`) kontrollerer felter, låser værelsestypen og tæller kapacitet med `first_overbooked_night` fra `rules.py`.
5. `backend/app/data_access/repositories.py` gemmer booking og idempotensresultat i samme transaktion i `unit_of_work.py`.
6. API'et svarer `201` med `Location`, og browseren viser bookingen.

**En analyse i Tableau:**

1. Tableau kalder fx `/api/odata/HotelTotals` ved refresh.
2. `backend/app/api/odata.py` kalder `backend/app/business/analytics_feed_service.py`.
3. Servicen læser ét snapshot og beregner hver kombination med `hotel_result` fra `analytics_service.py`, ligesom `GET /api/analytics/hotel`.
4. Dashboardets dropdowns vælger præcis én kombination.

**Kontrakt mod adfærd:** Alle endpoints i kontrakten er implementeret, `NOT_IMPLEMENTED_YET` er tom, og `assert_matches_contract` kontrollerer statuskoder, headers og schemas i testene. `$metadata` kontrolleres felt for felt mod kontrakten.

## Fund

| Fund | Konsekvens | Handling |
|---|---|---|
| Hver datakilde opdateres for sig, og Tableau Public har ingen **Refresh All Extracts** | Demo kræver op til syv klik, og visninger kan midlertidigt vise forskellige tidspunkter | Gruppen har accepteret det. Et samlet feed er muligt |
| Dashboardet er ikke låst mod ændringer | Et klik på ✕ fjerner et dropdown-felt, og **Save** kan ændre filen | Dokumenteret i `tableau/README.md`. Brug **Don't Save** |
| Parametrenes liste er fast i filen | Et nyt år eller land kan først vælges, når filen bygges igen. Filen har 2025 og 2026, mens T055-datasættet også havde bookinger i 2027 | Dokumenteret |
| Port 8080 kan være optaget af andre programmer | `localhost:8080` kan ramme et andet program | Dokumenteret. Tableau bruger `127.0.0.1` |
| Ingen formelle godkendelser på de fleste PR'er | Constitution kræver godkendelse fra et andet gruppemedlem | Se T067. Kun PR #12 og #15 har reviews på GitHub |
| Ingen adgangskontrol | Største svaghed før produktion | Bevidst valgt, se constitution |

## Nye tasks

Disse er tilføjet i `tasks.md` og er vurderet som ikke nødvendige 5. november 2026, se status øverst:

- **T069:** Afprøv dropdown for medarbejder, andre år, kombinerede hotelfiltre og salg uden data i Tableau (US7.4, US9.2, US9.3).
- **T070:** Afprøv, at en afvist ændring ikke ændrer tallene efter refresh i Tableau (US10.2).
- **T071:** Åbn `tableau/hotel-and-bar.twbx` på et andet gruppemedlems maskine, og gennemfør refresh.

## Gruppens egne handlinger

- **T063:** Bookingprøven er gennemført ifølge gruppens bekræftelse 5. november. Varighed og resultat skal registreres for at afgøre SC-001.
- **T067:** Andre gruppemedlemmer skal gennemgå PR'erne, og hvert medlem skal kunne dokumentere og forklare sit eget bidrag. Git viser commits fra fire konti, men fordelingen er ujævn. Denne gennemgang vurderer ikke, hvem der har bidraget med hvad.
- **T068:** Præsentationen fredag den 6. november 2026 skal forberedes og øves.

## De 10 SWA-spørgsmål

| Nr. | Hvor svaret findes |
|---:|---|
| 1 Arkitekturdiagram | `README.md` |
| 2 Følg et request | Afsnittet ovenfor |
| 3 Tre lag | `backend/app/api`, `business`, `data_access` og `test_architecture.py`. Eksempel: kapacitetsreglen ligger i `rules.py`, ikke i SQL |
| 4 Nøgletal | `analytics_service.py`. Flyttes de til Tableau eller SQL, kan klienter få forskellige tal, og filtre ville lægge forkert sammen, som T002 viste |
| 5 Udskiftelighed | `business/ports.py`. Et databaseskift rører dataadgang, migrationer og drift. Et frontendskift rører ikke backenden |
| 6 REST-design | `contracts/openapi.yaml`, fx `POST /api/bookings` med `201` og `409` |
| 7 API-kontrakten | Kontrakten er styrende, og `assert_matches_contract` kontrollerer den |
| 8 Docker | `compose.yaml`: database → init → backend → frontend og Swagger. Data ligger i `mysql_data` |
| 9 Fra statisk til live | Data ændres gennem API'et og vises efter manuel refresh, se T054 |
| 10 Ejerskab | Skal besvares af gruppen. Et muligt eksempel er filterdesignet, som blev ændret efter prøven i T002. Største svaghed er manglende adgangskontrol |
