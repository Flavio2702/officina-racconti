<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Difetti tipici della prosa generata

Catalogo per `racconto-scrittura` (da evitare), `racconto-revisione` (da segnalare) e `prosa.py` (da contare). Le sigle tra parentesi quadre rimandano a `officina/fonti.md`.

Il catalogo ha tre parti, con basi diverse. La prima raccoglie osservazioni sull'italiano da un saggio d'autore e da una recensione [F32][F33], accanto a una ricerca sugli schemi sintattici generati che non riguarda specificamente i racconti italiani [F34]. Nessuna delle tre fonti convalida le soglie o l'elenco degli stilemi dello script. La parte 4 non aggiunge un elenco: confronta il catalogo con la tassonomia di uno studio sugli scrittori professionisti [F38].

Nessuna voce di questo catalogo è un errore in sé. Un testo umano può contenerle tutte per scelta. Servono a trovare i punti in cui un passaggio suona generato, cioè scritto per inerzia.

## 1. Segnali discussi nelle fonti sull'italiano generato

Tratti discussi per i testi in italiano prodotti da modelli linguistici [F32][F33], con uno studio più generale sugli schemi sintattici ricorrenti [F34]:

- **Paratassi e strutture binarie o ternarie**: frasi coordinate in serie, coppie e terne di elementi con lo stesso peso.
- **Coppie di aggettivi coordinati**: *un silenzio denso e pesante*, *una luce fredda e distante*.
- **Opposizioni del tipo *non solo… ma*** e, per estensione, *non era X, era Y*.
- **Verbosità e ridondanza**: informazioni ripetute, esplicitazione di ciò che il contesto rende già chiaro.
- **Connettivi poveri o in eccesso**: pochi tipi di connettivo, oppure un ricorso generoso a connettivi di raccordo (*inoltre*, *tuttavia*, *in questo modo*).
- **Gerundi astratti in coda alla frase**: *…permettendo di*, *…contribuendo a*, *…rendendo possibile*. Danno un tono procedurale e saggistico.
- **Anglicismi non adattati e calchi dall'inglese**.
- **Virgola seriale anche prima della *e***.
- **Ripetitività**: le stesse strutture di frase tornano più spesso che in un testo umano.

`prosa.py confronta` misura alcuni di questi segnali (gerundi astratti in coda, connettivi di raccordo, terne del tipo *parola, parola e parola*, *non solo… ma*) accanto ai tratti di voce e al ritmo. Il passaggio si legge contro la variazione dei testi dell'autore su finestre della stessa lunghezza, nello stesso racconto e nel corpus dei racconti consolidati, invece che contro soglie fisse (`stilometria.md`). «quindi», «invece» e «comunque» non sono fra i segnali: sono anche connettivi del parlato. Il registro d'ufficio, le figure di repertorio e la punteggiatura estranea alla voce sono trattati in `lessico-e-figure.md` e `punteggiatura-e-ritmo.md`. Una banda dice dove il passaggio esce dalla variazione osservata: non certifica la voce dell'autore e non attribuisce il testo. Quanto le misure distinguono a ogni lunghezza è nella calibrazione di `stilometria.md`. Uno scarto può servire al passaggio.

## 2. Difetti narrativi dei modelli (mestiere)

Tradotti e adattati da creative-writing-skills (vedi `CREDITI.md`). Nascono tutti dalla stessa tendenza: l'addestramento premia la risposta completa e chiara, la narrativa premia lo spazio lasciato al lettore (vedi `principi.md`).

- **Allargare il compito**: chiesto un confronto, arriva il confronto più le conseguenze, una riflessione e un'anticipazione. Rimedio: fermarsi al compito.
- **Appiattire la voce**: tutto nello stesso registro competente e un po' formale; i momenti forti e quelli banali trattati allo stesso modo. Rimedio: la voce del punto di vista decide ogni frase, non solo quelle «di carattere».
- **Spiegare il mondo**: un blocco che si ferma a spiegare come funziona qualcosa. Rimedio: far passare l'informazione dalla reazione del personaggio (vedi `scena.md`, Esposizione).
- **Nominare le emozioni**: *Era furiosa. Provò una profonda tristezza.* Rimedio: un comportamento che solo quel personaggio avrebbe. Attenzione ai gesti di repertorio (pugni stretti, mascella serrata, sguardo basso): sono etichette travestite.
- **Chiudere la tensione in fretta**: dopo il litigio la riconciliazione, dopo la caduta il lato positivo. Rimedio: chiedersi se la tensione deve durare. Di solito sì.
- **Voci tutte uguali**: ogni personaggio articolato, lucido, emotivamente competente. Rimedio: differenze di lessico, di lunghezza, di cosa ciascuno evita di dire.
- **Commento emotivo**: dopo il fatto, una metafora che spiega cosa significa e quanto pesa. Rimedio: il fatto, la reazione specifica, stop.
- **Sciogliere l'ambiguità**: una frase aggiunta che risolve ciò che la scena lasciava aperto. Rimedio: controllare la sezione **Taciuto** della scheda.
- **La frase che spiega la scena**: il testo fa il lavoro, poi una frase dice cosa ha fatto. È il difetto di riga più comune nella prosa generata. Rimedio: toglierla e rileggere.

## 3. Formule di repertorio (osservazione)

**Questa parte non viene da una fonte.** È un elenco costruito dall'uso, da verificare e arricchire con casi veri trovati nei racconti della raccolta (i casi personali vanno in `voce/difetti-personali.md`). Sono formule frequenti nella narrativa di consumo e nella prosa generata; trovarne una non dice chi ha scritto il testo, dice solo che quel punto merita uno sguardo.

- Calchi dall'inglese: *un sorriso che non raggiungeva gli occhi*; *un respiro che non sapeva di trattenere*; *qualcosa dentro di lei si ruppe*.
- Fisiologia di repertorio: *un brivido lungo la schiena*; *il cuore che batteva all'impazzata*; *un nodo alla gola*; *lo stomaco che si contorce*.
- Enfasi vuota: *un silenzio assordante*; *l'aria carica di*; *come se il tempo si fosse fermato*; *il peso del mondo*.
- Chiuse che spiegano: *In quel momento capì che…*; *E per la prima volta…*; *Forse, pensò, era proprio questo…*
- Dichiarativi enfatici in serie: *sussurrò*, *sibilò*, *mormorò*, *sbottò* al posto di *disse* o di un gesto.

Le formule di questa parte sono anche nell'elenco `STILEMI` di `strumenti/prosa.py`. Se ne aggiungi, aggiungile in `strumenti/stilemi_extra.txt`, una per riga.

## 4. Corrispondenza con la tassonomia LAMP

Scrittori professionisti che correggevano paragrafi generati, in inglese, hanno concordato su sette categorie di difetti [F38]. La tavola dice dove questo catalogo le copre già; le voci brevi sotto la tavola valgono solo per ciò che restava scoperto.

| Categoria LAMP | Dove è già coperta |
| --- | --- |
| Cliché | parte 3 (formule di repertorio); parte 2, gesti di repertorio in «Nominare le emozioni» |
| Esposizione superflua | parte 2: «Spiegare il mondo», «La frase che spiega la scena», «Sciogliere l'ambiguità»; `scena.md`, Esposizione |
| Prosa ridondante e ornata | parte 1: verbosità, coppie di aggettivi; parte 2: «Commento emotivo»; parte 3: enfasi vuota |
| Frase mal costruita | parte 1, gerundi in coda (in parte); voce sotto |
| Poca specificità e dettaglio | parte 2, «Nominare le emozioni» (in parte); voce sotto |
| Parola goffa | parte 1, anglicismi e calchi (in parte); voce sotto |
| Tempi incoerenti | `norme-redazionali.md`, Tempi verbali nella narrazione; `scena.md`, Ricordi e salti di tempo |

- **Frase mal costruita**: periodi contorti o lunghi senza una ragione di ritmo, passaggi fra frasi senza legame. Distinguerla dal periodo lungo voluto: la domanda è se il lettore deve tornare indietro per capire chi fa cosa.
- **Poca specificità**: affermazioni generali dove il lettore avrebbe bisogno di vedere (*la stanza era in disordine* invece di un oggetto fuori posto). Rimedio: un dettaglio che solo quella scena avrebbe.
- **Parola goffa**: parola imprecisa o fuori registro, pronome dal riferimento ambiguo, passivo che nasconde chi agisce.

**Avvertenza.** Nello stesso studio i modelli, chiamati a trovare i passaggi difettosi, lo fanno con precisione inferiore all'accordo fra gli esperti, e ancora meno quando devono indicarne la categoria [F38]. Una segnalazione di queste categorie fatta dall'assistente resta un candidato da guardare, come quelle dello script.
