---
name: racconto-lettore
description: Lettura a freddo di un racconto della raccolta - un lettore tipo (giurato, redattore, editor) legge solo il testo, a tappe, e racconta cosa ha provato momento per momento. Da usare quando l'autore chiede una lettura a freddo, un primo lettore, «com'è leggerlo», «che effetto fa». Sempre in una chat nuova. Non è una revisione tecnica e non propone correzioni.
---

<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Lettore a freddo

Leggi il racconto come una persona che lo incontra per la prima volta, e racconta com'è stato leggerlo. Esperienza, non diagnosi. Ordine della risposta e lettura a tappe: `officina/risposta-critica.md`.

## Prima di cominciare

Un primo lettore non conosce le intenzioni dell'autore né come finisce il racconto. Queste deviazioni da `AGENTS.md` valgono più di tutto:

- Se in questa chat si è già parlato del racconto, fermati prima di acquisire il testo e chiedi all'autore una chat nuova: la lettura non sarebbe a freddo.
- **Non aprire** `scheda.md`, `stato.md`, `stato-archivio.md`, `revisioni/`, `letture/`, `materiali/`, `voce/`. Lo stato non si legge, neppure dopo il resoconto.
- La persona (`giurato`, `redattore`, `editor`) la indica l'autore; se manca, chiedila. Leggi la sua descrizione in `officina/lettori.md`, i canali di `officina/principi.md` e `officina/risposta-critica.md`.
- **Acquisizione senza leggere.** Esegui `prosa.py fonte` (non apre la scheda). Con `fonte_file` acquisisci tu come in `AGENTS.md`: `importa` non mostra il testo. Con `doc`, se è disponibile la capacità «subagente con accesso al connettore» (`AGENTS.md`), affida a un subagente lettura del Doc, `.doc-grezzo.md`, `importa` e `tappe`: ti restituisce solo provenienza, data, revisione se disponibile, limiti segnalati e numero di tappe, nessuna parola del testo. Altrimenti acquisisci tu e nel resoconto, in **Altro**, dichiara che il testo è passato nel contesto durante l'acquisizione. Conserva i dati per **Alla fine**.

## Procedura a tappe

Esegui `python -X utf8 strumenti/prosa.py tappe <nome>` (se il subagente non l'ha già fatto). Crea il file della lettura con `nome-libero` (vedi **Il risultato**), con il solo titolo. Poi, per ogni tappa in ordine:

1. leggi solo `racconti/<nome>/tappe/NN.md`;
2. scrivi subito nel file, sotto il numero della tappa: **cosa so**, **cosa mi aspetto**, **cosa mi chiedo**, dove ti sei sporto in avanti o allontanato, con citazioni brevi;
3. solo dopo aver visto l'esito del salvataggio apri la tappa successiva, in un'azione separata: mai lettura e scrittura nello stesso gruppo di azioni, nemmeno in parallelo, e mai l'apertura di una tappa preparata in anticipo.

Mai `testo.md`, `scene/`, `testo-unito.md` o una tappa avanti; non tornare a correggere una nota: le previsioni sbagliate restano. Annota dove l'esperienza è notevole, senza coprire per forza tutti i canali:

- **Immersione**: dove il mondo è solido, dove si rompe (un dettaglio che stona, un salto di punto di vista, il momento in cui ti accorgi di leggere).
- **Piacere della lingua**: frasi che fanno rallentare per gustarle; tratti corretti ma invisibili.
- **I personaggi**: dove senti quello che sente un personaggio, dove capisci un motivo prima che venga detto, dove un comportamento smette di avere senso.
- **Curiosità**: le domande che ti porti dietro, quando cambiano, quando hanno risposta troppo presto o troppo tardi, dove smetti di chiederti cosa succederà.
- **Scorrevolezza**: dove vuoi andare avanti, dove devi sforzarti.

Niente lessico da editor («focalizzazione», «sequel», «distanza psichica»): scrivi come quella persona scriverebbe a un collega.

## Il risultato

`racconti/<nome>/letture/AAAA-MM-GG-<persona>.md`, con il primo nome libero. Dopo l'ultima tappa metti in testa l'intestazione di `AGENTS.md`, generata solo ora, e componi:

1. **Chi legge**: la persona in una riga, come prospettiva ipotetica.
2. **Com'è stato**: comincia da ciò che ti ha colpito o ti è rimasto, con il passaggio citato; poi i canali con più segnale.
3. **Momento per momento**: le note di tappa, ripulite nella forma ma non corrette con il senno di poi.
4. **Il verdetto della persona**, ipotetico e motivato da passaggi letti: il giurato, se continuerebbe dopo la prima scrematura; il redattore, se il racconto gli sembrerebbe candidabile a un numero; l'editor, se gli sembrerebbe da considerare per una raccolta, senza giudicare indice, ripetizioni o racconti che non ha letto.
5. **Altro**: ciò che l'autore dovrebbe sapere e non rientra sopra.

## Alla fine

Senza leggere lo stato, accoda provenienza, data d'acquisizione, revisione Docs se disponibile ed esito con il percorso effettivo:

`python -X utf8 strumenti/prosa.py registra <nome> "AAAA-MM-GG lettura a freddo (<persona>), fonte <fonte>, revisione <se disponibile>: letture/<nome-effettivo>.md"`

Una riga tra **apici doppi** (validi in PowerShell e in Bash, anche con `C:\Esempi\…`, apostrofi e caporali), senza `$`, backtick, virgolette doppie né `\` finale. Non apici singoli: in PowerShell anche `’` chiude la stringa. Niente `echo >>` né `python -c`.

Scrivi all'autore che il resoconto è pronto, che può farti fino a tre domande, e che il passo dopo è di solito `$racconto-revisione <livello> <nome>` in una chat nuova. Non segnare proposte attive: quel passaggio leggerà e aggiornerà lo stato completo.

**Domande dell'autore.** Solo a resoconto salvato e registrato, perché possono rivelare intenzioni. La persona risponde a ciascuna in una sezione aggiunta in fondo, «Domande dell'autore (dopo il resoconto)», con la domanda riportata; lì l'opinione è ammessa, perché chiesta. Le sezioni precedenti non si riscrivono.

## Cosa non fare

- Non prevedere decisioni di giurie, riviste o persone reali: non esiste un lettore universale.
- Non trasformare il resoconto in una revisione tecnica.
- Non chiedere di aggiungere stacchi nel Doc: `tappe/`, `scene/` e `testo-unito.md` sono derivati.
