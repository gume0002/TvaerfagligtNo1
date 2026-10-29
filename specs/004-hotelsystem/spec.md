# Specifikation: Hotelsystem

**Specifikationsmappe:** `specs/004-hotelsystem/`
**Oprettet:** 26. oktober 2026 · **Opdateret:** 29. oktober 2026  
**Status:** Specify og Clarify gennemgået; [Plan](plan.md) er udarbejdet til gruppens gennemgang med åbne Tableau- og fortolkningsrisici. Ingen funktioner er implementeret.

## Formål og grundlag

Hotel Kong Arthur skal kunne vedligeholde bookinger og barsalg og bruge aktuelle data til beslutninger i Tableau. Receptionisten bruger en browser; hotelledelsen bruger analyserne. Hotellets fremtidige bookingsystem er også klient til API'et.

Grundlaget er opgave-PDF'erne i `opgavebeskrivelse/`, `.specify/memory/constitution.md`, de oprindelige filer i `data/raw/` og interviewets bekræftede svar. Den 29. oktober bad brugeren om at færdiggøre Specify med de mest oplagte valg. Disse supplerende valg er dokumenteret nedenfor og er ikke fremstillet som tidligere interviewsvar. Teknologivalg og detaljeret API-kontrakt hører til Plan, før implementering.

## Omfang

Prototypen omfatter bookingoversigt og booking-CRUD, registrering, rettelse og aflysning af barsalg, hotel- og baranalyser med manuel datakilde-refresh i Tableau, førstegangsindlæsning samt dokumentation. MySQL er den aktuelle datakilde. Backend har præsentation/API, forretningslogik og dataadgang; hvert lag kalder kun laget lige under sig. Klienter bruger REST/JSON, og de officielle regler og nøgletal ligger i forretningslogikken.

Login, betaling, fakturering, refundering, fysisk værelsestildeling, rengøring, dynamisk prisoptimering og integration til et rigtigt hotelbookingsystem er uden for prototypen. Tableau er en ekstern klient uden for Docker og læser udelukkende gennem API'et.

## Beslutninger og domæneregler

### Bekræftet i interviewet

- En booking har gæstens navn, land, ankomst, afrejse, antal gæster, værelsestype og aftalt pris pr. nat. Den reserverer én enhed af en værelsestype, ikke et bestemt værelse.
- Afrejse skal være efter ankomst; gæsteantallet skal passe til typen. Bookingen afvises, når typen er fuldt booket på mindst én nat. Afrejse og næste ankomst samme dag er tilladt.
- Alle bookingfelter kan redigeres med samme kontrol af kapacitet og tilgængelighed. Den aftalte natpris fastholdes under hele opholdet uanset senere standardpriser.
- Bookingoversigten understøtter navnesøgning og filtrering efter opholdsdato.
- Sletning bevarer bookingen som aflyst og frigiver kapacitet. Aflyste bookinger indgår ikke i belægning eller omsætning.
- Barsalg registreres med drik, antal, salgspris, salgsdato og medarbejder og kan rettes eller aflyses. Aflyste salg bevares, men tæller ikke i analyserne.
- Interviewets oprindelige mål var automatisk Tableau-opdatering inden fem sekunder. Brugeren har efterfølgende accepteret manuel refresh i Tableau; den gældende regel står under Analyser og filtre og i US10.
- Baren viser cocktail/kaffe-fordeling både efter antal og efter omsætning.
- Rapporteringsåret er et valgbart kalenderår. Bookingomsætning fordeles efter overnatningsdato: ankomst tæller med, afrejse tæller ikke. Den 30. december til 2. januar giver to nætter i det gamle år og én i det nye.

### Supplerende valg ved færdiggørelse af Specify

**Tid og omsætning**

- Kalenderår og dagsgrænser følger hotellets lokale tid, Europe/Copenhagen. Bookingdatoer er kalenderdatoer. Standardåret i dashboardet er indeværende år.
- Alle beløb er i DKK med to decimaler. Hotelomsætning er summen af aftalt natpris pr. inkluderet nat. Baromsætning er antal gange den faktisk registrerede salgspris pr. enhed. Prisændringer i kataloger ændrer ikke tidligere bookinger eller salg.
- Dashboardet viser passeret bookingomsætning, forventet bookingomsætning og summen for året med tydelige betegnelser. Passerede nætter har overnatningsdato før dags dato; dags dato og senere er forventede. Dette er en datobaseret opgørelse, ikke dokumentation for betaling eller faktisk check-in.
- Opgavens ord »indtjening« fortolkes som omsætning, da omkostninger ikke foreligger. Der beregnes ikke profit eller særskilt moms. Aflysning fjerner hele bookingens eller salgets bidrag, også fra historiske rapporter; der modelleres ikke afbestillingsgebyrer.

**Sæsoner**

- Lavsæson: januar og februar. Mellemsæson: marts–maj og september–november. Højsæson: juni–august og december. Dette er prototypens valgte kalender, ikke dokumenterede faktiske hotelregler.
- Hver nat tilhører præcis én sæson ud fra sin dato. Et ophold over en sæsongrænse fordeles på sæsonerne uden at ændre bookingens aftalte natpris. Skuddag er lavsæson.

**Kapacitet og validering**

- Hotellet har otte typer og i alt 214 værelser. Antal værelser pr. type og maks. personer pr. type er nødvendige stamdata; de findes ikke præcist i opgaven og må ikke fremstilles som hotellets faktiske fordeling. En tydeligt mærket demofordeling fastlægges i Plan og skal summere til 214; hver types personkapacitet skal være 1–4.
- Gæsteantal og salgsantal er positive heltal. Priser skal være positive med højst to decimaler. Navn og medarbejder skal være udfyldt; land, type og drik vælges fra kendte værdier. Fejl ændrer ingen gemte data.
- Tilgængelighed kontrolleres for alle nætter i intervallet [ankomst, afrejse). Ved redigering tælles den redigerede booking ikke dobbelt. Samtidige forespørgsler må ikke kunne overbooke den sidste ledige enhed.
- Nye bookinger og rettelser må have historiske datoer til efterregistrering. Nye barsalg må højst have dags dato; efterregistrering er tilladt.
- Sletning gennem API'ets DELETE betyder logisk sletning/aflysning. Den aktive ressource forsvinder fra normal oversigt og normale enkeltopslag, men bevares i historikken. Gentaget sletning ændrer ikke noget. Aflyste poster kan ses med et særskilt historikfilter og kan ikke redigeres eller genaktiveres i prototypen. HTTP-svar fastlægges i OpenAPI.

**Analyser og filtre**

- Hotelanalyser kan filtreres på år, sæson, land og værelsestype; filtrene kombineres, og aktive filtre vises. Standard er hele året, alle lande, alle typer og alle sæsoner. Ranglister anvender samme filtrerede grundlag; alle delte førstepladser vises.
- Land er bookingens registrerede gæsteland. Antal gæster pr. land er summen af antal gæster på de inkluderede bookinger, hvor hver booking tælles én gang, selv om flere nætter ligger i perioden. Det er registrerede gæsteophold, ikke unikke personer eller dokumenteret nationalitet for alle medrejsende.
- Belægningsgrad er bookede, ikke-aflyste værelsesnætter divideret med tilgængelige værelsesnætter gange 100. Nævneren er antal værelser i valgte typer gange antal datoer i den valgte periode. Landevalg påvirker tælleren, mens nævneren fortsat er hotellets valgte kapacitet. Tallet mærkes som landets bidrag til belægningen, når land er filtreret.
- Ekstra nøgletal er gennemsnitlig pris pr. booket værelsesnat (ADR): bookingomsætning divideret med bookede værelsesnætter på samme grundlag. Belægning og ADR vises særskilt for passerede og kommende nætter samt samlet, så prognose og historik ikke blandes skjult.
- Baranalyser filtreres på kalenderår og medarbejder, med Helene Christine valgt som standard. Årets samlede salg vises både i DKK og antal. Omsætning pr. drik samt begge kategoriandele bruger præcis samme udvalg. Kategoriandelene er henholdsvis kategoriens antal / samlet antal og kategoriens omsætning / samlet omsætning gange 100.
- Ved nul nævner vises »Intet datagrundlag« for forholdstal; summer vises som 0. Procenter afrundes til to decimaler, og mindre afrundingsafvigelser fra 100 % accepteres. Gæstetilfredshed vises som »Intet datagrundlag« og får ingen opdigtet score, da ingen vurderinger foreligger. Indsamling af tilfredshed ligger uden for prototypen.
- Bookingændringer samt oprettelser, rettelser og aflysninger af barsalg skal fremgå i relevante Tableau-visninger, når brugeren gennemfører manuel refresh af datakilden inde i Tableau. Refresh skal hente nye data gennem API’et og opdatere udtrækket; genvisning af et gammelt udtræk er utilstrækkelig. Tidspunktet for datagrundlaget vises tydeligt. Ved fejlet refresh gives en forståelig fejl, og sidste vellykkede datatidspunkt bevares; eksisterende tal vises som et tidligere snapshot. Der kræves ikke automatisk opdatering eller en femsekundersgrænse. Den konkrete Tableau Public-refresh skal stadig afprøves.

## Brugerhistorier og acceptkriterier

Historierne er prioriteret som afgrænsede, testbare forløb. Analysehistorier kan demonstreres med et kontrolleret datagrundlag uden at afvente alle skrivefunktioner. Afhængigheder til stamdata og fælles API beskrives i Plan/Tasks.

### US1 – Opret booking (P1)

Som receptionist ønsker jeg at oprette en booking i browseren, så hotellet kan reservere kapacitet til gæsten.

**Værdi og selvstændig prøve:** Et gyldigt ophold kan gemmes og genfindes uden analysefunktioner.

1. Givet ledig kapacitet, når alle gyldige felter gemmes, så får bookingen en identitet og kan genfindes efter genindlæsning.
2. Givet en type med maks. to personer, når tre gæster angives, så afvises bookingen med en forståelig fejl, og ingen booking oprettes. Det samme gælder afrejse senest på ankomstdagen og ugyldig pris.
3. Givet én ledig enhed, når to overlappende bookinger forsøges gemt samtidig, så lykkes højst én. En ankomst på en eksisterende bookings afrejsedag tillades.

### US2 – Find booking (P1)

Som receptionist ønsker jeg at søge og filtrere bookinger, så jeg hurtigt kan finde det ophold, jeg skal håndtere.

**Værdi og selvstændig prøve:** En kendt booking findes blandt et sæt gemte bookinger.

1. Når en del af gæstens navn søges uden hensyn til store/små bogstaver, vises matchende aktive bookinger med alle bookingoplysninger.
2. Når opholdsintervallet 10.–12. juni vælges, vises ophold med mindst én fælles nat; en booking med afrejse den 10. eller ankomst den 12. vises ikke. Dato- og navnefilter kan kombineres.
3. Når ingen matcher, vises en tom tilstand. Aflyste poster fremgår kun ved valg af historikfilter og er tydeligt markeret.

### US3 – Ret booking (P1)

Som receptionist ønsker jeg at rette en booking, så ændrede gæsteoplysninger og ophold registreres korrekt.

**Værdi og selvstændig prøve:** En eksisterende booking kan ændres og læses igen.

1. Når navn, land, datoer, gæsteantal, type eller natpris rettes gyldigt, gemmes ændringen på samme bookingidentitet.
2. Når en ændring overskrider kapacitet eller tilgængelighed, afvises hele ændringen, og den tidligere booking bevares. Uændrede datoer afvises ikke ved at tælle egen booking dobbelt.
3. Når standardprisen ændres, bevarer en eksisterende booking sin aftalte natpris, medmindre receptionisten selv retter den.

### US4 – Slet booking (P1)

Som receptionist ønsker jeg at slette en aflyst booking, så kapacitet og analyser afspejler de gældende reservationer.

**Værdi og selvstændig prøve:** En gemt booking aflyses og frigiver sin kapacitet.

1. Når sletning bekræftes i browseren, aflyses bookingen via DELETE, fjernes fra aktive visninger og bevares markeret i historikken.
2. Derefter kan en ny booking bruge den frigivne kapacitet; den aflyste bidrager ikke til omsætning, gæsteophold eller belægning.
3. Gentaget sletning giver ingen ekstra ændringer. Manglende identitet giver et forståeligt svar; andre bookinger påvirkes ikke.

### US5 – Registrer barsalg (P1)

Som receptionist ønsker jeg at registrere barsalg, så medarbejderens salg og barens omsætning kan følges løbende.

**Værdi og selvstændig prøve:** Et salg gemmes med drik, kategori, antal, enhedspris, dato og medarbejder.

1. Når Helene Christine sælger tre cocktails til 100 DKK pr. stk., registreres tre enheder og 300 DKK på salgsdatoen.
2. Nul/negativt antal, ukendt drik, manglende medarbejder, ugyldig pris eller fremtidig dato afvises uden at oprette et salg.
3. Når drikkens katalogpris ændres senere, beholder det gemte salg sin oprindelige enhedspris.

### US6 – Ret eller aflys barsalg (P2)

Som receptionist ønsker jeg at rette og aflyse barsalg, så fejlregistreringer ikke forvrænger analyserne.

**Værdi og selvstændig prøve:** Et eksisterende salg kan korrigeres uden hoteldata.

1. Når antal ændres fra tre til to til 100 DKK, bliver bidraget 200 DKK og to enheder; alle salgsfelter kan rettes med reglerne fra US5.
2. Når salget aflyses, bevares det i historikken og udelades fra alle salgssummer og andele. Gentaget aflysning har ingen yderligere effekt.
3. Ugyldig rettelse bevarer de tidligere værdier. Aflyste salg kan ikke rettes eller genaktiveres.

### US7 – Hotellets omsætning og gæstelande (P1)

Som hotelledelse ønsker jeg at se omsætning og gæsternes lande i Tableau, så jeg kan se hvilke markeder og værelsestyper der bidrager mest.

**Værdi og selvstændig prøve:** Kendte bookinger giver håndberegnelige analyser gennem API'et.

1. Et ophold 30. december–2. januar til 1.000 DKK giver 2.000 DKK i det gamle år og 1.000 DKK i det nye. Sæsonfordeling følger hver nat, også ved skift mellem lav-, mellem- og højsæson.
2. Dashboardet viser samlet bookingomsætning, passeret og forventet del, fordeling pr. type/sæson/land samt bedst indtjenende typer og lande. Ranglister har tydelige beløb og håndterer lighed.
3. En booking med to gæster og tre nætter giver to registrerede gæsteophold på landet, tre værelsesnætter og tre gange natprisen; gæster tælles ikke én gang pr. nat.
4. År, sæson, land og type kan kombineres; API-tal og visning svarer til samme udvalg. Aflyste bookinger udelades.
5. Omsætning kan vises pr. værelsestype opdelt på sæson, ikke kun som to separate totaler. Et ophold 28. februar–2. marts 2026 til 1.000 DKK pr. nat giver for samme type 1.000 DKK i lavsæson og 1.000 DKK i mellemsæson. Et sæsonfilter skal give samme beløb i API og Tableau.

### US8 – Belægning og ekstra nøgletal (P1)

Som hotelledelse ønsker jeg at se belægning og gennemsnitlig værelsespris, så jeg kan vurdere kapacitetsudnyttelse sammen med omsætning.

**Værdi og selvstændig prøve:** Et lille datagrundlag demonstrerer begge formler.

1. Givet to værelser over to nætter og én booking på begge nætter til 1.000 DKK, vises 50 % belægning og ADR på 1.000 DKK.
2. Perioder med både passerede og kommende nætter vises opdelt og samlet på samme grundlag som omsætningen. Et skudår har 366 tilgængelige døgn pr. værelse.
3. Uden bookede nætter vises omsætning 0 og ADR som »Intet datagrundlag«; med positiv kapacitet er belægningen 0 %. Tilfredshed vises som manglende datagrundlag.

### US9 – Helene Christines baranalyser (P1)

Som hotelledelse ønsker jeg at se Helene Christines salg og salgsmiks, så jeg kan vurdere barens omsætning og efterspørgsel.

**Værdi og selvstændig prøve:** Et kontrolleret sæt barsalg kan analyseres uafhængigt af hotelbookinger.

1. Med tre cocktails til 100 DKK og to kaffer til 50 DKK i samme år vises 400 DKK, fem drikke, 300/100 DKK pr. drik/kategori, antalandele 60/40 % og omsætningsandele 75/25 %.
2. Salg fra andre år eller medarbejdere tæller ikke med i Helene Christines valgte år. Medarbejderfilter kan ændres; standard er Helene Christine.
3. Aflyste salg udelades. Uden salg vises 0 DKK og 0 enheder samt »Intet datagrundlag« for andele, uden division med nul.
4. Startkataloget indeholder de 20 cocktails og 10 kaffetyper fra barfilen. Omsætning vises pr. navngiven drik; kategorisummer alene opfylder ikke dette kriterium.

### US10 – Aktuelle data i dashboardet (P1)

Som hotelledelse ønsker jeg at kunne hente aktuelle analyser ved at trykke refresh i Tableau, så jeg kan se gemte ændringer uden at genimportere råfiler.

**Værdi og selvstændig prøve:** En gemt ændring bliver synlig i det åbne Tableau-dashboard efter manuel datakilde-refresh, og tallene svarer til API’et for samme filtre.

1. Efter oprettelse, rettelse eller aflysning af booking eller barsalg, når brugeren gennemfører datakilde-refresh inde i Tableau, viser relevante visninger de opdaterede API-tal for samme filtre. Der kræves ikke ny filimport eller manuel genopbygning af dashboardet.
2. En afvist ændring påvirker ikke tallene efter refresh. Hvis API’et ikke kan nås under refresh, får brugeren en forståelig fejl; gamle tal beholder sidste vellykkede datatidspunkt og er tydeligt et snapshot frem for aktuelle tal.
3. Dashboardet får alle analysedata via REST/JSON API'et og har ingen direkte MySQL- eller råfilforbindelse eller egne forretningsregler.

### US11 – Start og bevar prototype (P1)

Som gruppemedlem ønsker jeg at starte prototypen med én kommando, så den kan demonstreres og genstartes med vedvarende data.

**Værdi og selvstændig prøve:** Fra en frisk kopi og kun Docker kan løsningen startes og genstartes.

1. `docker compose up` starter MySQL, backend, browserfrontend og Swagger UI uden manuelle klargøringstrin; backenden bliver først klar, når databasen er klar. Tableau-delen forbindes som dokumenteret ekstern klient.
2. Tom database får startdata automatisk efter reglerne nedenfor; genstart genindlæser ikke råfiler eller overskriver ændringer. Gemte bookinger og salg bevares i navngivet volume.
3. Swagger UI viser den gældende OpenAPI-kontrakt. README beskriver start, adresser, arkitektur og Tableau-forbindelse; CONTRIBUTE beskriver bidrag, tests og review.

## Funktionelle krav

| ID | Krav | Historie |
|---|---|---|
| FR-001 | Opret, læs, søg, ret og logisk slet bookinger gennem browser og REST/JSON API | US1–US4 |
| FR-002 | Håndhæv datoer, personkapacitet, aftalt pris og natlig tilgængelighed, også ved samtidige skrivninger | US1, US3 |
| FR-003 | Registrer, læs, ret og aflys barsalg med historisk enhedspris og medarbejder | US5–US6 |
| FR-004 | Lever bookingomsætning pr. år, sæson, type og land, gæsteophold og ranglister | US7 |
| FR-005 | Lever belægningsgrad og ADR med dokumenterede nævnere og særskilt historik/prognose | US8 |
| FR-006 | Lever årligt barsalg, omsætning pr. drik og begge kategoriandele for valgt medarbejder | US9 |
| FR-007 | Hent opdaterede API-tal ved manuel datakilde-refresh i Tableau og synliggør snapshot-tidspunkt samt fejl ved refresh | US10 |
| FR-008 | Gem aktuelle data i MySQL; indlæs startdata kun ved tom database og bevar ændringer | US11 |
| FR-009 | Lever OpenAPI før endpoints implementeres og Swagger UI i Docker; kontrakt og adfærd skal stemme | US1–US11 |
| FR-010 | Saml regler og beregninger i logiklaget; SQL kun i dataadgang; ingen klientgenveje | US1–US11 |
| FR-011 | Returner ensartede JSON-fejl med passende HTTP-status, fx 400, 404 og 409; frontend viser forståelig fejl | US1–US6 |
| FR-012 | Test forretningsregler og nøgletal automatisk med én testkommando og kontrollér alle acceptkriterier i Converge | Alle |

## Startdata og datakvalitet

Filerne er undersøgt direkte den 29. oktober 2026. Originalerne ændres ikke.

| Kilde | Faktisk indhold | Begrænsning og behandling |
|---|---|---|
| Hotel-CSV | 1.000 poster: navn, land, værelsestype, antal dage, sæson og `Price` | Ingen opholdsdato, rapporteringsår eller gæsteantal; 54 erstatningstegn i navne. Må ikke alene blive til aktive bookinger. |
| Hotel-Excel | Samme kolonner og 1.000 poster samt ekstra værdi `5379` i E1002 | Foretrækkes som navnekilde ved import. Den løse ekstracelle udelades med importbemærkning. Ingen dobbeltimport af CSV og Excel. |
| Bar-Excel | 30 drikke: navn, kategori, pris og samlet antal solgte | 20 cocktails og 10 kaffe; ingen salgsdato, år eller medarbejder. Summer må ikke udlægges som faktiske salg fra Helene Christine i et bestemt år. |

- Kendte rådata kan ved førstegangsindlæsning gemmes som særskilt mærkede historiske referenceposter i MySQL og bruges til kataloger. Udaterede summer holdes uden for de officielle kalenderårsrapporter, belægning og aktuelle bookinger.
- `Price`-feltets betydning (natpris eller samlet opholdspris) er ikke dokumenteret. Der udledes ikke faktisk bookingomsætning af feltet, før betydningen er underbygget. Feltet bevares som rå referenceværdi.
- Prototypen skal starte med et lille deterministisk sæt tydeligt mærkede demobookinger og demosalg med datoer, gæsteantal og medarbejder. Det gør år, kapacitet og analyser demonstrerbare uden at udgive konstruerede data for hotellets historik. Demodata må indgå i prototypens rapporter, som tydeligt mærkes »Demodata«.
- Den konkrete demofordeling af værelser, katalogpriser og importmapping beskrives i Plan. Ugyldige eller ufuldstændige rækker må ikke stiltiende importeres som driftsdata; antal indlæste og udeladte rækker med begrundelser dokumenteres. Genstart må ikke skabe dubletter.

## Centrale entiteter

- **Booking:** Identitet, gæstenavn, land, ankomst/afrejse, gæsteantal, værelsestype, aftalt natpris og aktiv/aflyst status samt markering af demooprindelse.
- **Værelsestype:** En af de otte typer, antal tilgængelige værelser og maks. personer; eventuel vejledende pris er adskilt fra aftalt bookingpris.
- **Land:** Ensartet landeidentitet og visningsnavn til bookinger og filtre.
- **Drik:** Identitet, navn, cocktail/kaffe og vejledende enhedspris.
- **Barsalg:** Identitet, drik, antal, faktisk enhedspris, dato, medarbejder, aktiv/aflyst status og demooprindelse.
- **Medarbejder:** Identitet og navn; Helene Christine er tilgængelig som valg. Registrering af medarbejder er ikke login.
- **Historisk referencepost:** Oprindelig kilde og værdier samt kendte mangler; adskilt fra daterede driftsdata.
- **Analyseresultat:** Periode, aktive filtre, aktualitet, summer og beregnede nøgletal; beregnes af logiklaget fra gemte data.

## Grænsetilfælde

- Nætter over årsskifte, sæsonskifte og skuddag fordeles pr. dato; tomme perioder og ugyldige datointervaller håndteres uden division med nul.
- Ingen overlap på afrejsedagen; overbooking på én nat afviser hele opholdet; redigering og samtidige reservationer følger samme regler.
- Dublerede gæstenavne er tilladt og skelnes via bookingidentitet. Landenavne og typer normaliseres, så stavevarianter ikke skaber nye analysegrupper.
- Aflyste eller ikke-eksisterende identiteter må ikke ændre andre poster. Fejl midt i en skrivning må ikke efterlade delvise ændringer.
- Genstart under førstegangsindlæsning skal kunne fuldføre uden dubletter eller halvfærdige aktive data.
- Forbindelsesfejl ved gemning må ikke vises som en succes. Automatiske gentagelser må ikke oprette dobbelte bookinger eller salg; konkret håndtering fastlægges i Plan.

## Målbare succeskriterier

- **SC-001:** En testperson kan oprette en gyldig booking i browseren på højst to minutter og finde, rette og aflyse den uden at bruge Swagger eller databasen.
- **SC-002:** Alle kontrollerede eksempler i US1–US9 giver de beskrevne beløb, antal og procenter; ugyldige skrivninger ændrer ingen data.
- **SC-003:** Ti gentagelser for hver af oprettelse, rettelse og aflysning på både booking og barsalg gennemføres i lokal demoopsætning med 1.000 bookinger og 1.000 barsalg. Efter hver bekræftet gemning gennemfører brugeren datakilde-refresh i Tableau; ved vellykket afslutning skal dashboardet svare til API’ets forventede resultat for samme filtre. Registrér forventet/faktisk værdi, datatidspunkt og refresh-resultat. En særskilt prøve med afbrudt API skal give fejl uden falsk nyt datatidspunkt. Ingen femsekundersgrænse gælder.
- **SC-004:** To samtidige forsøg på sidste ledige enhed kan ikke medføre overbooking; dette kontrolleres gentagne gange med en automatisk integrationstest.
- **SC-005:** Prototypens Docker-tjenester starter fra en frisk kopi med `docker compose up` uden andre lokale installationer end Docker. Dette omfatter ikke Tableau-klienten; dens adgang, opsætning og forbindelse dokumenteres og demonstreres særskilt. Oprettede og rettede poster overlever stop/start uden genimport eller dubletter.
- **SC-006:** API, frontend og Tableau viser ens tal for samme data og filtre. Automatisk testkommando dækker regler, nøgletal og kontraktens centrale forløb; Converge angiver bevis og status for hvert acceptkriterium.
- **SC-007:** Alle påkrævede hotel- og barvisninger, README-arkitekturdiagram, CONTRIBUTE og Swagger UI kan demonstreres ved aflevering. Manglende grundlag fremgår tydeligt, herunder tilfredshed og udaterede rådata.

## Afklaringer

Clarify findes i [clarify.md](clarify.md). Dokumentet indeholder afklaringerne, sammenholdet med opgavebeskrivelsen, de åbne fortolkningsrisici, overdragelsen til Plan og kvalitetskontrollen. De afklaringer, som ændrede krav og acceptkriterier, er indarbejdet ovenfor.
