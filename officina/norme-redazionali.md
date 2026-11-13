# Norme redazionali della raccolta

Riferimento per il livello di **redazione** e di **bozze**. Le sigle tra parentesi quadre rimandano a `officina/fonti.md`.

Un principio sopra tutti: sulla punteggiatura dei dialoghi non esiste una norma unica, esistono scuole editoriali diverse. Quello che non deve mai mancare è la coerenza interna: scelto un sistema, lo si applica in tutto il testo [F4]. Per questo le scelte della raccolta sono scritte qui sotto, e la revisione controlla la coerenza con queste, non con un'idea astratta di correttezza.

## Scelte della raccolta

Le scelte personali sono in `voce/scelte-redazionali.md`, creato da `strumenti/prepara.py` e ignorato da Git. Un racconto può derogare nella sua scheda. Le sezioni seguenti illustrano convenzioni possibili; non sono un profilo stilistico dell'autore.

## Dialoghi

### Con i caporali (convenzione predefinita del modello)

- Le battute stanno tra caporali. Le virgolette alte “ ” servono per una citazione dentro una battuta, o per una parola usata a distanza, ironica o riportata [F1].
- Quando cambia chi parla, si va a capo. Il capoverso rende leggibile il cambio di turno [F5]; una battuta di un altro personaggio dentro un capoverso narrativo lungo costringe il lettore a ricostruire chi parla.
- La punteggiatura che appartiene alla battuta (punto interrogativo, esclamativo, puntini) sta dentro i caporali: `«Vieni?» chiese.`
- Se la battuta finisce con un punto e subito dopo viene la frase citante, il punto cade e la frase citante comincia in minuscolo: `«Lo so» disse.` (convenzione da confermare).
- La frase citante può stare prima, dopo o in mezzo alla battuta [F2]. Se sta in mezzo, la battuta riprende con un nuovo caporale: `«Non serve» disse «davvero.»`
- Il discorso diretto libero, senza segni grafici e senza verbo introduttivo, è una scelta legittima [F2]: se il testo lo usa con coerenza, non va convertito.

### Con le lineette (ammesso in stesura)

- Per distinguere i turni bastano la lineetta di apertura e l'a capo [F5].
- La lineetta di chiusura serve solo quando dopo la battuta riprende la narrazione: `— Lo so — dice. — Te la offro lo stesso.` A fine capoverso non si chiude [F5][F6].
- La lineetta (—) non è il trattino (-): il trattino è più corto e serve a unire parole [F5]. Il trattino al posto della lineetta nei dialoghi è un'approssimazione da tastiera, che la conversione sistema.

### Conversione in redazione

`python -X utf8 strumenti/prosa.py dialoghi <racconto>` conta segni candidati e mostra un'anteprima; con `--salva` la scrive in `materiali/`. Conta i segni, non le battute: un inciso o una citazione non prova una convenzione incoerente. Anche le proposte semplici vanno verificate. Tutte le battute con separatori interni e le virgolette che potrebbero essere citazioni restano da valutare, con l'originale e il motivo del dubbio. L'anteprima riporta la scelta `dialoghi` e le deroghe della scheda; non decide la virgola dopo il caporale finché l'autore non ha fissato la scelta in redazione. Nessuna conversione entra nel Doc senza approvazione.

## Ortografia

| Caso | Forma corretta | Fonte |
| --- | --- | --- |
| perché, poiché, affinché, benché, finché, né, sé | accento acuto | [F9] |
| è (verbo) | accento grave | [F9] |
| È maiuscola | *È*, non *E'* | [F10] |
| po' (poco) | apostrofo, mai accento: *un po'* | [F9] |
| qual è | senza apostrofo | [F11] |
| sé stesso / se stesso | entrambe corrette, scegline una | [F12] |
| d eufonica | solo davanti alla stessa vocale: *ed ecco*, *ad andare*; *e anche*, *a una* | [F8] |
| puntini di sospensione | sempre tre | [F7] |
| gli / le | *gli* per *a loro* va bene; *gli* per *a lei* no | [F13] |

La d eufonica davanti a vocale diversa (*ad esempio*, *ed io*) è diffusa: la Crusca raccomanda di limitarla [F8], ma in narrativa può essere una scelta di ritmo. La revisione la segnala, non la corregge.

## Tempi verbali nella narrazione

- **Passato remoto e imperfetto** si dividono il lavoro: il remoto porta gli eventi in primo piano, l'imperfetto lo sfondo. Alternarli è tecnica, non errore [F14].
- **Passato remoto e passato prossimo** hanno una forte variazione regionale: al Sud il remoto è preferito anche nel racconto personale, al Nord prevale il prossimo [F14]. Nello stesso episodio passato, però, mescolarli senza ragione confonde la collocazione nel tempo. La revisione segnala i passaggi dove lo stesso ricordo cambia tempo, e chiede.
- **Presente narrativo**: attualizza i fatti e crea un primo piano improvviso. I passaggi tra presente e passato devono avere una funzione, per esempio un punto di svolta o un ricordo [F15].
- **Imperfetto narrativo**: se una sequenza di eventi usa solo l'imperfetto, il lettore perde l'ordine dei fatti [F16].

## Superficie

- Nessuno spazio prima di virgola, punto, punto e virgola, due punti.
- Un solo spazio tra le parole.
- Un solo tipo di apostrofo e di virgolette in tutto il testo.
- Corsivo per le parole straniere non adattate e per l'enfasi; con misura.

## Cosa controlla lo script e cosa il modello

Lo script (`prosa.py controlla`) segnala forme che corrispondono ai suoi modelli: alcuni accenti dell'elenco, *po'* accentato, *qual'è*, *E'*, due puntini isolati o quattro e più, e certi spazi. I numeri decimali non sono trattati come sospensioni. La divisione in frasi, l'esclusione dei dialoghi, i possibili filtri, gli echi e i nomi simili sono approssimazioni: possono perdere casi e generare falsi positivi. Il conteggio dei segni di dialogo non certifica la coerenza della convenzione. Gli echi confrontano prefissi di sei lettere, non forme morfologiche: `casa/case` può sfuggire. Le parole ricorrenti dichiarate nella scheda restano nelle frequenze descrittive ma sono escluse dalle segnalazioni di eco.

Il modello, al livello di redazione, controlla quello che le espressioni regolari sbaglierebbero: tempi verbali, *gli* per *le*, consecutio, d eufonica in contesto, coerenza delle scelte di questa pagina.
