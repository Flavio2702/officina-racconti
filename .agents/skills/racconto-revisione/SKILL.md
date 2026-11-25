---
name: racconto-revisione
description: Diagnosi di un racconto già scritto, un livello alla volta (strutturale, scena, riga, redazione, bozze) - report con cosa funziona, da zero a cinque questioni con esempi citati e direzione; rivede solo ciò che è cambiato. Da usare per «dammi un parere», «rileggi», «cosa non funziona», la redazione con i dialoghi ai caporali, la consegna a un concorso. Non riscrive il testo.
---

<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Revisione

Diagnosi di un livello alla volta, in un report: indica la direzione, non riscrive. Invocazione: `$racconto-revisione <livello> <nome> "<domanda>"`; livello e domande dell'autore (fino a tre, tra virgolette) sono facoltativi.

## Prima di cominciare

1. **Strutturale indipendente, o livello non indicato.** Se la chat contiene già le intenzioni del racconto, chiedi una chat nuova o, se l'autore vuole proseguire qui, dichiara la revisione informata. Acquisisci solo fonte e testo; prima di aprire scheda, stato, letture o report annota effetto percepito, cambiamento e domande suscitate dal testo, senza leggere il **Taciuto** per anticipare ciò che il testo dovrebbe tacere. Le domande dell'autore possono rivelare intenzioni: usale solo dopo le note. Negli altri livelli scheda e materiali si possono leggere prima.
2. Acquisisci la fonte e rigenera la copia come in `AGENTS.md`; senza bozza proponi `$racconto-nucleo`. Leggi `testo.md` per intero, alla velocità di un lettore.
3. **Ripetere o no.** Confronta lo SHA-256 della copia con l'ultimo report dello stesso livello e perimetro (nella strutturale indipendente, dopo le note). Si ripete solo se il testo è cambiato in quel perimetro o se una questione è `risolto da verificare`; altrimenti niente report: di' che il livello non ha materiale nuovo e proponi di intervenire sul testo o il livello dopo. Se l'autore insiste, si ripete e il report lo dichiara.
4. **Differenze.** Con uno SHA diverso, `python -X utf8 strumenti/prosa.py differenze <nome> <sha>`: rivedi i capoversi cambiati con il loro contorno e verifica le questioni aperte del report; l'intestazione lo dichiara, con l'impronta precedente e il perimetro. Revisione intera se cambia il primo o l'ultimo capoverso, più di un terzo dei capoversi, o se la copia non è conservata.
5. Leggi `racconti/<nome>/scheda.md`, `officina/principi.md`, `officina/risposta-critica.md` e i file del livello, poi letture e report precedenti pertinenti. Valuta anche le scelte della scheda, **Taciuto** compreso: l'effetto osservabile e la distanza dall'intenzione, senza farne automaticamente un errore né sottrarle alla valutazione.
6. `python -X utf8 strumenti/prosa.py controlla <nome> --salva`: un indizio, non un verdetto.

## Livelli

Il livello lo sceglie l'autore. Se non lo dice, dopo la prima impressione consulta **Questioni aperte**, impronta e perimetro dei report e **Fatto**, e proponi il livello più alto che chiede ancora attenzione; un livello stabile non si ripropone finché il testo non cambia. I file `livelli/…` sono in questa skill.

| Livello | File | Da leggere anche |
| --- | --- | --- |
| strutturale | `livelli/strutturale.md` | `officina/forma-breve.md` |
| scena | `livelli/scena.md` | `officina/scena.md` |
| riga | `livelli/riga.md` | `officina/difetti-ai.md`, `officina/punteggiatura-e-ritmo.md`, `officina/lessico-e-figure.md`, `voce/profilo.md`, `voce/difetti-personali.md` |
| redazione | `livelli/redazione.md` | `officina/norme-redazionali.md`, `officina/punteggiatura-e-ritmo.md`, `officina/fonti.md` |
| bozze | `livelli/bozze.md` | — |

I livelli bassi presuppongono che gli alti reggano: un problema di struttura serio trovato a un livello basso si dice, e ci si ferma lì.

## Il risultato

`racconti/<nome>/revisioni/AAAA-MM-GG-<livello>.md`, con l'intestazione stampata da `python -X utf8 strumenti/prosa.py intestazione <nome>` (con `--revisione <id>` se disponibile). Le sezioni seguono l'ordine della risposta critica [F36], che non attenua le questioni:

1. **In breve**: tre righe su come sta il testo a questo livello.
2. **Cosa funziona**: due o tre cose da non toccare, specifiche, con il passaggio citato e perché agisce sul lettore.
3. **Risposte alle domande dell'autore**, se ci sono: sul tema, con un parere.
4. **Questioni**, da zero a cinque, per priorità; zero è un esito valido. Per ognuna: un nome («la frase che spiega la scena»); cosa costa al lettore, nei canali di `officina/principi.md`; due o tre esempi citati con la posizione; la direzione della correzione. In redazione e bozze le questioni sono l'elenco dei casi del livello e **Cosa funziona** si omette.
5. **Domande neutre**: dove non sai se è una scelta o un errore. Ognuna supera la prova di `officina/risposta-critica.md`.

Prima delle questioni puoi fare in chat fino a tre domande neutre, solo se la risposta cambia la diagnosi. Nella strutturale indipendente le note della prima lettura restano separate dal confronto con scheda e consegne.

**Prosa dell'assistente.** Se l'intestazione riporta una provenienza, `python -X utf8 strumenti/prosa.py provenienza <nome>` dice quali capoversi coincidono. Se toccano il perimetro, dichiaralo in apertura (un modello tende a preferire i propri testi [F40]), segna «(prosa dell'assistente)» gli esempi di **Cosa funziona** che ne vengono e proponi una seconda lettura di quei passaggi con lo strumento diverso da quello in uso, in una chat nuova: `$racconto-revisione <livello> <nome> "<domanda sui passaggi>"`.

**Commenti nel Doc**, solo se l'autore li chiede e la scrittura è disponibile (`AGENTS.md`, «Google Docs nei due strumenti»), altrimenti le citazioni restano nel report: uno per questione, con la frase citata per esteso, perché i commenti via API possono restare non ancorati.

## Alla fine

- In **Questioni aperte** aggiorna gli esiti; se la passata non ha trovato questioni nuove di priorità alta, scrivi che il livello è **stabile** su quel perimetro e quella impronta.
- Un report vale per la sua impronta e il suo perimetro: un report sul finale non certifica le altre scene, una riscrittura sostanziale può riaprire questioni esaminate. Un livello in **Fatto** non dice che le questioni siano risolte e non basta per avanzare.
- Di solito il passo dopo è l'autore che riscrive; poi si verifica l'esito e si sceglie il livello successivo in una chat nuova.

## Cosa non fare

- Non riscrivere passaggi. Per una proposta di testo c'è `$racconto-scrittura` (lucidatura), non con `scrittura_assistita: no`.
- Non normalizzare la voce dell'autore verso una prosa «corretta e generica».
- Non ammorbidire le questioni perché **Cosa funziona** viene prima.
- Non modificare il Doc, tranne la conversione dei dialoghi approvata (`livelli/redazione.md` in questa skill) e i commenti richiesti.
