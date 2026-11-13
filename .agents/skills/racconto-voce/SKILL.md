---
name: racconto-voce
description: Profilo di voce dell'autore della raccolta - calibrarlo dai racconti consolidati, aggiornarlo quando un racconto si consolida, confrontare un passaggio per vedere dove se ne allontana. Separa i tratti di stile generali dalle scelte di un singolo racconto. Parte solo se l'autore la chiama per nome. Non scrive prosa.
---

# Voce

Il profilo descrive come scrive l'autore in generale, non come è scritto un racconto. Questa skill lo costruisce, lo aggiorna e vi confronta un passaggio; non scrive prosa.

## Prima di cominciare

- Leggi per primi, in ogni caso, `voce/profilo.md`, `voce/esempi.md`, `voce/difetti-personali.md`; poi, per ogni racconto usato, `racconti/<nome>/scheda.md` e i **Candidati di voce** del suo `stato.md`.
- Contano solo i racconti con `stato: consolidato`, letti per intero dopo aver acquisito la fonte e rigenerato la copia come in `AGENTS.md`. Un racconto consolidato è dell'autore per sua dichiarazione, comprese le frasi nate da un raccordo che ha tenuto.
- Eccezione: la calibrazione **provvisoria** su un racconto quasi finito, solo se l'autore la chiede esplicitamente; ciò che ne esce resta candidato.

## Comandi

- **calibra**: costruisce o ricostruisce il profilo dai racconti consolidati. Proponi da tre a sei brani vari per `voce/esempi.md`; entrano solo quelli che l'autore approva.
- **aggiorna** `<nome>`: dopo il consolidamento, passa i **Candidati di voce** del racconto attraverso il filtro; valuta conferme, aggiunte e controevidenze; proponi brani d'esempio e voci per `voce/difetti-personali.md`.
- **deriva** `<passaggio>`: dove un passaggio si allontana dal profilo e dagli esempi, senza dire se è un male; uno scarto funzionale può restare. `prosa.py confronta` paragona al resto del racconto, non certifica la voce dell'autore; sotto le 80 parole è poco affidabile.

### Il filtro: stile o racconto?

Un tratto che dipende dal punto di vista, dal tema o dal personaggio, dalla forma del racconto o da una scelta della scheda è del racconto: va nella sua scheda. Altrimenti è un candidato. Nel dubbio, in **Tratti da verificare** con la ragione.

Un tratto è **confermato** solo con evidenza in almeno due racconti consolidati, meglio se con punto di vista o tema diversi. L'assenza in un nuovo racconto non lo smentisce: annota dove manca, senza farne un «mai». Davanti a controevidenza chiediti se dipende dal racconto, dal narratore o da un ambito più ristretto; rivaluta la fiducia prima di modificarlo o toglierlo, motivando nello **Storico**.

### Cosa osservare

Dai segnali di *voice-match* di unslop e da EveryDay-Writer (`CREDITI.md`): **ritmo** (media e varianza delle frasi con `prosa.py controlla`, dove si accorciano o si allungano); **sintassi** (paratassi o ipotassi, periodi lunghi, frasi nominali); **punteggiatura** usata ed evitata; **registro e lessico** e come si mescolano; **immagini**, di che materia sono e come tornano; **distanza e umorismo** (ironia, pudore, enfasi).

## Il risultato

`voce/profilo.md`, nel suo formato: per ogni tratto fiducia, racconto di provenienza, descrizione in una o due righe, prove citate; nello **Storico** data e cosa è cambiato. Mostra le modifiche all'autore prima di salvarle.

## Alla fine

Nello `stato.md` di ogni racconto usato, i candidati passati al profilo o scartati. All'autore, cosa è cambiato nel profilo.

## Cosa non fare

- Non mettere nel profilo le scelte di un racconto.
