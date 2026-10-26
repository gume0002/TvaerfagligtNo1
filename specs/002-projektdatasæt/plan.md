# Plan: Placering af projektets eksempeldata

**Specifikation:** [spec.md](spec.md)  
**Dato:** 26. oktober 2026

## Omfang

Saml de tre leverede datafiler uændret i `data/raw/`, og dokumentér deres indhold, rolle og kendte kvalitetsproblemer i README. Grundprincipperne ligger allerede på deres korrekte projektsti og kopieres ikke.

## Gennemførelse

1. Opret `data/raw/` og kopiér de to hoteldatafiler og barens arbejdsbog dertil med oprindelige filnavne.
2. Bevar filindholdet byte-for-byte; ingen konvertering, rettelse eller import udføres.
3. Opdatér README med filernes anvendelse som eksempel-/referencedata og med de observerede afvigelser.
4. Kontrollér filernes antal, filnavne og checksums mod kilderne, og sammenhold resultatet med acceptkriterierne.

## Begrænsninger

CSV og Excel-filen med hotelposter repræsenterer de samme 1.000 poster, men har datakvalitetsafvigelser. De skal bevares som leveret; valget af autoritativ fil og eventuel oprydning afklares separat. Datafilerne gør ikke CSV til systemets eneste datakilde.
