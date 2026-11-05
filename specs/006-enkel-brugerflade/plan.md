# Plan

1. Bevar HTML/CSS/JavaScript, REST/JSON, OpenAPI og de tre backendlag med PostgreSQL.
2. Opdel bookingformularen med semantiske fieldsets. Brug fælles navigation, introduktion, designvariabler, responsiv afstand og tydeligt fokus på alle tre sider.
3. Tilføj korte CSS-animationer til velkomst og succes, og respekter prefers-reduced-motion. Giv bookingfejl tilknyttede beskrivelser og flyt fokus til første ugyldige felt.
4. Kør eksisterende testpakke i Docker mod isoleret PostgreSQL. Kontrollér desktop/mobil, tastatur og reduceret bevægelse i Chromium; gem screenshots til visuel kontrol.
5. Vedligehold README, CONTRIBUTE og Converge. Kontrakten kræver ingen ændring, fordi endpoints og JSON er uændrede.

## Fugleanimation

Erstat buerne med lokal inline-SVG på alle tre sider. Animér fuglens placering og vinge med CSS i cirka to sekunder, én gang ved indlæsning. Bevar aria-hidden, mobilafgrænsning og prefers-reduced-motion. Byg kun frontend igen og kontrollér illustration, slutposition, animationens varighed, reduceret bevægelse og mobilbredde i Chromium. API og bookingkode berøres ikke.
