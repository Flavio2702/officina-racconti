---
name: racconto-nuovo
description: Avvia un nuovo racconto della raccolta dalla bozza allegata o collegata (Google Doc, .docx, .md, .txt), in qualunque stato - cartella, scheda, stato, primi controlli, al massimo quattro domande e il passo successivo. Da usare quando l'autore vuole iniziare, impostare o aggiungere un racconto («ho un racconto nuovo», «imposta questa bozza»). Non giudica il testo e non scrive prosa.
---

# Racconto nuovo: l'onboarding

Trasforma la bozza del momento in un progetto pronto a lavorare. Non giudica il testo e non comincia il passo successivo.

## Prima di cominciare

Leggi `officina/forma-breve.md`, per la scheda, e `voce/profilo.md`, per non confondere i tratti di voce già noti con le scelte di questo racconto.

## Procedura

1. **Il nome.** Proponi un nome di cartella minuscolo, con trattini, dal titolo (`il-faro`). Senza titolo, chiedilo con le domande del punto 7 e usa un nome provvisorio.
2. **La cartella.** `python -X utf8 strumenti/prosa.py nuovo <nome>`.
3. **Il testo.** Registra il link in `doc:` oppure il file in `fonte_file:` (dalla radice o assoluto), senza spostare l'originale. Acquisisci la fonte e rigenera la copia come in `AGENTS.md`, poi leggi il testo per intero. Da un'idea senza bozza salta numeri e deduzioni dal testo.
4. **I numeri**, in quest'ordine:
   - `python -X utf8 strumenti/prosa.py conta <nome>`: oltre le 6.000 parole circa, `modalita: lunga` e, se ci sono separatori di scena, `python -X utf8 strumenti/prosa.py dividi <nome>`;
   - `python -X utf8 strumenti/prosa.py controlla <nome> --salva`;
   - `python -X utf8 strumenti/prosa.py dialoghi <nome>`, solo per sapere quali convenzioni ci sono: niente `--salva`, niente conversioni.
5. **La scheda.** Solo ciò che il testo dice da sé: un campo vuoto con una domanda è meglio di una deduzione sbagliata.
   - Intestazione: `pov`, `tempo`, `modalita`, `dialoghi`. `dialoghi` è il sistema del testo finito: `caporali`, convenzione della raccolta, salvo scelta diversa dell'autore; quella della bozza va nel commento (`dialoghi: caporali # la bozza usa lineette (dedotto)`).
   - **Nucleo** provvisorio, in un paragrafo.
   - **Il cambiamento**, **Effetto unico**, **Fili**: ciò che il testo lascia osservare, anche una permanenza, un effetto plurale, fili aperti; se non è chiaro, la domanda resta aperta, senza dedurre un difetto.
   - **Scelte di questo racconto**: tema, parole ripetute per scelta (anche in `ricorrenti:`, così lo script non le segnala), cornici, nomi.
6. **Voce: separare subito.** Un tratto che dipende dal punto di vista, dal tema, dal personaggio o dalla forma di questo racconto va nella scheda; gli altri in **Candidati di voce** dello stato, con una citazione.
7. **Le domande.** Al massimo quattro, in un unico messaggio, su ciò che il testo non dice e che cambia il lavoro. In ordine di priorità: destinazione (concorso, rivista, raccolta), limite di battute, scadenza e regola del bando sull'uso dell'IA; a che punto è il racconto per l'autore; cosa deve restare al lettore, se non si deduce; cosa lo preoccupa di più. Metti le risposte nella scheda, togliendo `(dedotto)` dai campi confermati. `ia_bando` dalla risposta: `vietata`, `ammessa`, `da verificare` se la regola non è nota; vuoto senza bando.

## Il risultato

Cartella, scheda e stato compilati, report dei controlli in `revisioni/`. Il passo successivo da proporre:

- testo quasi finito: `$racconto-lettore <nome> <giurato|redattore|editor>`, con la persona della destinazione;
- testo in revisione con dubbi di struttura: `$racconto-revisione strutturale <nome>`;
- bozza iniziale o racconto che non sa cosa vuole essere: `$racconto-nucleo <nome>`.

## Alla fine

In **Fatto** l'onboarding con il percorso del report dei controlli. All'autore, in due o tre frasi: cosa hai impostato, quali campi sono dedotti, la riga da incollare in una chat nuova.

## Cosa non fare

- Non dare giudizi sul testo: il primo giudizio è un passaggio grosso con la sua chat.
- Non scrivere nel Doc e non toccare `voce/`.
- Non cominciare il passo successivo.
