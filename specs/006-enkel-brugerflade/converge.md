# Afsluttende gennemgang – US16

5. november 2026. Gennemført efter `project-skills/hotel-architecture-review/SKILL.md`. Grundprincipper og krav fra 004 og 005 gælder fortsat.

## Acceptkriterier

| Kriterium | Resultat og bevis |
|---|---|
| US16.1 Fælles navigation | Opfyldt: alle tre HTML-sider har samme navigation og `aria-current="page"`. Kontrolleret i Chromium. |
| US16.2 Bookingfunktioner | Opfyldt: `frontend/index.html` har tre fieldsets; eksisterende formular-id'er og API-kald bevares. Alle 21 bookingbrowsertests består, inklusive opret, søg, historik, ret, bekræftet aflysning, validering og gentagelse ved netværksfejl. |
| US16.3 Barsalg og analyser | Opfyldt: alle 8 salgsbrowsertests og 21 analysebrowsertests består. Ingen ændringer i `api.js`, `sales.js`, `analytics.js` eller backend. Grafer og tabelvisninger bevares. |
| US16.4 Mobil og tastatur | Opfyldt i Chromium ved 1440, 768 og 390 px: ingen vandret sidescroll på nogen af de tre sider. Bred tabel ruller internt. Skip-link, markering af aktuel side og tastaturfokus kontrolleret; fokusregler findes i `frontend/css/styles.css`. |
| US16.5 Animation og fejl | Opfyldt: CSS-animeret SVG-fugl og succesmarkering, animationer slås fra med `prefers-reduced-motion`. Fejl knyttes til bookingfelter med `aria-describedby`, første ugyldige felt får fokus. Afviste rettelser bevarer værdier i eksisterende browsertest. |

## Udført kontrol

- `docker compose --profile test run --build --rm test`: **366 bestået**, én deprecation-advarsel fra Starlette/httpx; exit 0. Isoleret PostgreSQL-testdatabase, ingen nulstilling af demodata.
- Supplerende Playwright-kontrol af alle tre sider på den lokale Docker-demo: navigation, bredder 390/768/1440 px, skip-link, fejlfokus, reduceret bevægelse og ingen JavaScript-fejl. Screenshots gemt midlertidigt under `/private/tmp/hotel-design-evidence/` og visuelt gennemgået for booking på desktop/mobil samt barsalg og analyser på desktop.
- Demo opdateret med `docker compose up -d --build`. README, CONTRIBUTE og Spec Kit-overblik er opdateret. `git diff --check` består.

## Arkitektur og kontrakt

Bookingformularen kalder fortsat `createBooking` i `frontend/js/api.js`, som sender JSON og Idempotency-Key til `POST /api/bookings`. `backend/app/api/bookings.py:create_booking` kalder `BookingService.create` i `backend/app/business/booking_service.py`. Servicen validerer input, låser værelsestypen, kontrollerer kapacitet og gemmer gennem Unit of Work og `SqlBookingRepository.add` i `backend/app/data_access/repositories.py`. SQLAlchemy-forbindelsen i `backend/app/data_access/database.py` bruger PostgreSQL. Lagansvaret er bevaret; arkitektur- og kontrakttests består.

Analyser hentes af `frontend/js/analytics.js` gennem `api.js` fra `/api/analytics/hotel` og `/api/analytics/bar`. `backend/app/api/analytics.py` kalder analytics-servicen, som beregner tallene ud fra repositorydata. Designændringen indfører ingen egne nøgletal eller direkte databaseadgang. Den versionsstyrede OpenAPI-kontrakt og Swagger-opsætning er uændrede, fordi transporten er uændret; kontrakttestene består.

## Begrænsninger

Dette dokument verificerer UI-ændringen og regressionspakken. Det erklærer ikke hele afleveringen færdig. Testpersonens to-minutters bookingprøve T063, gruppereview og tidligere åbne Tableau-punkter er fortsat åbne. Safari og Firefox er ikke afprøvet. Ingen andre gruppemedlemmers arbejde tilskrives denne ændring.

## Opfølgning: fugl i velkomstfeltet

Efter brugerens ønske erstatter en lokal SVG-fugl de oprindelige buer i `frontend/index.html`, `sales.html` og `analytics.html`. `bird-arrive` varer 2,4 sekunder én gang; vingen slår fem gange og falder derefter til ro. Illustrationen er fortsat dekorativ og skjult for skærmlæsere.

Demoen er genbygget. Målrettet Playwright-kontrol består på alle tre sider: fuglen ender synligt på sin endelige position, animationen gentages ikke, fugl og vinge har ingen animation ved reduceret bevægelse, ingen vandret sidescroll ved 390 px og ingen JavaScript-fejl. Slutillustrationen er visuelt kontrolleret i `/private/tmp/hotel-design-evidence/bird-welcome.png`. `git diff --check` består. Den tidligere kørsel med 366 tests er ikke gentaget for denne dekorative ændring; API, business, dataadgang, PostgreSQL og OpenAPI er uændrede.
