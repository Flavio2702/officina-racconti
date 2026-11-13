---
name: racconto-scrittura
description: Scrive prosa per un racconto della raccolta - raccordi, varianti (al massimo due), abbozzi, lucidature - nella voce del racconto, senza segni nel testo e con le regole del bando sull'IA. Parte solo se l'autore la chiama per nome; una richiesta generica di migliorare un passaggio non basta. Non dà pareri (racconto-revisione) e non lavora sulla struttura (racconto-nucleo).
---

<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Scrittura: raccordi, varianti, abbozzi

L'autore scrive il racconto. Questa skill scrive solo quello che lui chiede, dove lo chiede, e non lascia segni nel testo. Parte solo se l'autore la chiama con `$racconto-scrittura`: se sei arrivato qui da una richiesta generica («puoi migliorare questo paragrafo?»), non scrivere e non chiedere conferme; dagli la riga `$racconto-scrittura lucidatura <nome> …` e offri `$racconto-revisione riga <nome>`, che indica la direzione senza riscrivere.

## Prima di cominciare

1. Leggi `racconti/<nome>/scheda.md`: punto di vista, tempo, dialoghi, **Taciuto**, **Scelte di questo racconto**. Con `scrittura_assistita: no` non scrivere prosa di nessun tipo: spiega all'autore che per questo racconto ha scelto di scriverla lui, con il motivo nel commento del campo, e fermati. Il campo lo cambia lui.
2. **Il bando.** Leggi `ia_bando` e `destinazione`. Con `vietata` o `da verificare`, e con campo vuoto e `destinazione: concorso`, non bloccarti: prima di scrivere dai all'autore un avviso breve e fattuale (il campo, la regola del bando se nota, che la conferma andrà nello stato e il materiale sarà marcato) e chiedi una conferma esplicita, una per compito, non per frase. Registra la conferma in `stato.md`, **Decisioni**, con data, compito e perimetro; mai nella scheda.
3. Acquisisci la fonte e rigenera la copia come in `AGENTS.md`; per un abbozzo senza testo salta acquisizione, ancora e confronti, dichiarandone il limite.
4. Il punto esatto lo indica l'autore citando una frase del testo; se la citazione non si trova o è ambigua, chiedi.
5. Leggi i tre o quattro capoversi prima e dopo il punto (tempo, distanza, fatti), poi `voce/profilo.md` (se provvisorio o sottile conta poco) e `officina/difetti-ai.md`, per sapere cosa evitare.
6. **L'ancora di voce.** I brani approvati in `voce/esempi.md` hanno la precedenza. Finché il file non ne ha, scegli due o tre capoversi dello stesso racconto vicini al punto o dello stesso tipo (dialogo, svolta, descrizione), con provenienza zero: esegui `python -X utf8 strumenti/prosa.py provenienza <nome>` ed escludi i capoversi che elenca (la misura vede solo i materiali marcati: dichiaralo). Un capoverso vicino al punto che coincide con prosa dell'assistente vale come contesto, non come voce. Dichiara all'autore quali capoversi hai usato (numero e prime parole).

## Modi

Chiedi quale, se l'autore non lo dice.

- **raccordo**: collega due punti, comprime un passaggio di tempo, cambia registro tra due scene. Va nel Doc, dopo l'approvazione.
- **variante**: un'altra esecuzione dello stesso momento, in `materiali/AAAA-MM-GG-variante-<breve>.md`. Al massimo due per richiesta, ciascuna con la sua strategia dichiarata in una riga, che differisce su un asse solo: distanza, ritmo, cosa si tace, punto d'ingresso. Una terza solo dopo che l'autore ne ha scelta una o ha indicato una direzione nuova; se ne chiede di più in una volta, scrivine due e diglielo.
- **abbozzo**: prosa esplorativa, dichiaratamente provvisoria, in `materiali/AAAA-MM-GG-abbozzo-<breve>.md`.
- **lucidatura**: su un passaggio indicato dall'autore, la versione nuova accanto all'originale, frase per frase se serve, con una riga per intervento su cosa guadagna. Mai applicata senza approvazione.

### Regole di scrittura

- **Fermati al compito.** Un raccordo non aggiunge una scena, una riflessione finale o un'anticipazione.
- **Non chiudere quello che il testo lascia aperto** (**Taciuto**).
- **Niente commento emotivo**, né emozioni nominate dove il testo intorno le mostra (`officina/difetti-ai.md`, parte 2).
- **Stessa grammatica del testo**: tempo, persona, distanza psichica, la convenzione dei dialoghi che la bozza usa in quel punto (in stesura anche la lineetta).
- **Lunghezza**: quella chiesta, altrimenti la più breve che fa il lavoro.

### Il controllo prima di mostrare

1. Scrivi il passaggio in `racconti/<nome>/materiali/_passaggio.md` ed esegui `python -X utf8 strumenti/prosa.py confronta racconti/<nome>/materiali/_passaggio.md <nome>`.
2. Valuta gli scarti (ritmo, gerundi in coda, connettivi, formule) rispetto alla funzione del passaggio e all'ancora: `confronta` paragona al resto del racconto, non certifica la voce dell'autore, e sotto le 80 parole conta soprattutto il contesto. Conserva uno scarto motivato (un finale che cambia ritmo); riscrivi solo se contraddice il compito o l'effetto.
3. **Passata di sottrazione.** Rileggi con la tavola LAMP (`officina/difetti-ai.md`, parte 4) [F38] e con **Taciuto**. Puoi solo togliere, o sostituire con qualcosa di più semplice: niente aggiunte, nessun ornamento al posto di un cliché. Al massimo due giri.
4. Mostra all'autore il passaggio, il punto esatto, l'ancora usata e, in una riga ciascuno, gli scarti conservati o rivisti e cosa la sottrazione ha tolto e perché.

## Il risultato

Ogni proposta ancora utile va per intero in un materiale permanente, anche se mostrata solo in chat, con stato, punto d'intervento, ancora usata e l'intestazione di `AGENTS.md`, fuori dalla prosa. Nell'intestazione di ogni materiale con prosa dell'assistente metti il marcatore `- Autore del testo: assistente (racconto-scrittura, <modo>)`: serve a `strumenti/prosa.py provenienza`. Varianti e abbozzi si dichiarano nel materiale come spunti, non come modelli a cui il testo debba conformarsi. `_passaggio.md` è solo un file di lavoro.

Inserimento, solo per raccordi e lucidature approvate:

- con originale locale (`fonte_file`) la proposta resta in `materiali/`: l'autore la applica al file, poi si riacquisisce la fonte;
- con `doc:`, solo se la scrittura con controllo sulla revisione è disponibile (`AGENTS.md`, «Google Docs nei due strumenti»): prima salva per intero il testo da inserire nel materiale marcato, con stato «approvata, da inserire»; inserisci solo la prosa nel punto esatto, con il `revisionId` acquisito insieme al testo dell'anteprima approvata; rileggi il Doc e verifica il passaggio e il testo intorno; rigenera la copia, porta il materiale a «inserita» e cancella `_passaggio.md`;
- se la scrittura non è disponibile o fallisce, non forzare: il testo resta nel materiale e spieghi all'autore come riprendere.

## Alla fine

Nessuna deviazione da `AGENTS.md`.

## Cosa non fare

- Non scrivere niente che l'autore non abbia chiesto; non toccare il resto del Doc.
- Non segnare in alcun modo il testo del racconto come scritto dall'AI: è una scelta dell'autore. Marcatore, avviso del bando e conferme stanno solo nei materiali, in chat e nello stato.
