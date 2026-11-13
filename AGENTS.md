<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Officina dei racconti

Lavori con chi scrive su racconti in italiano. L'autore ha l'ultima parola. Rispondi e scrivi sempre in italiano.

## Preparazione e dati privati

Prima di usare le skill, esegui `python -X utf8 strumenti/prepara.py` se mancano i file locali di voce. Crea solo modelli vuoti, non sostituisce file esistenti. Non farlo durante una lettura a freddo già avviata.

Racconti, fonti locali, profili di voce, preferenze e materiali sono privati. Salvali in `racconti/`, `bozze/` o `voce/`, escluse da Git; non inserirli nei modelli pubblici, nella documentazione o nei messaggi di commit. Non forzare l'aggiunta di file ignorati. Il fatto che un file sia escluso da Git non impedisce a un assistente AI autorizzato di leggerlo.

Le preferenze editoriali personali si salvano in `voce/scelte-redazionali.md`; `officina/norme-redazionali.md` rimane un riferimento generale.

## Dove sta cosa

- `racconti/<nome>/`: un racconto. `scheda.md` (scelte del racconto e fonte), `stato.md` (consegne tra le chat), `stato-archivio.md` (voci vecchie di **Fatto**, se esiste), `testo.md` (copia della fonte), `materiali/`, `revisioni/`, `letture/`; locali e rigenerate dallo script: `copie/` (versioni importate, per `differenze`) e `tappe/` (porzioni per il lettore).
- `officina/`: conoscenza di mestiere e norme, con le fonti in `officina/fonti.md`.
- `voce/`: profilo di voce generale dell'autore, brani d'esempio, tic ricorrenti.
- `strumenti/prosa.py`: conteggi e controlli. `python -X utf8 strumenti/prosa.py aiuto` per l'elenco dei comandi.
- `.agents/skills/`: le sei skill `racconto-*`. `.claude/skills/`: i loro rimandi per Claude Code.

## Due strumenti

- Il progetto si usa con Codex e con Claude Code. Le skill si chiamano con `$racconto-…` in Codex e `/racconto-…` in Claude Code; negli stati e nelle consegne si scrive sempre `$racconto-…`.
- In Claude Code una riga incollata che comincia con `$racconto-<nome>` vale come invocazione di quella skill: leggi `.agents/skills/racconto-<nome>/SKILL.md` e seguila con gli argomenti della riga. Per `racconto-scrittura` e `racconto-voce` la riga incollata dall'autore vale come richiesta esplicita.
- Il testo delle skill si modifica solo in `.agents/skills/`. I rimandi in `.claude/skills/` ripetono soltanto `name` e `description`, da tenere identici (`strumenti/test_skill.py` lo controlla).
- Non usare i due strumenti in contemporanea sullo stesso racconto. Se usi una cartella sincronizzata: prima di un commit cerca in `git status` copie in conflitto (con il nome del computer o `(1)` aggiunto al nome) e segnalale all'autore senza cancellarle.

## Il testo

- Se `doc:` è compilato, il Google Doc è l'originale. Altrimenti il campo facoltativo `fonte_file:` indica l'originale locale: percorso relativo alla radice del progetto oppure assoluto. Non spostarlo né duplicarlo automaticamente. Se entrambi sono vuoti, è un'idea senza testo oppure occorre identificare la fonte prima di lavorare sul testo.
- `testo.md` è una copia: rigenerala all'inizio di ogni passaggio, non modificarla mai a mano.
- **Testo incollato in chat.** Se l'autore incolla un testo più recente della fonte, salvalo per intero in `materiali/AAAA-MM-GG-fonte-chat.md` (nome univoco) con data/ora e perimetro, cioè quale parte del racconto. In `stato.md` registra lo SHA-256 del file e dichiaralo fonte più recente per quel perimetro, fino alla prossima acquisizione. Se è parziale non importarlo come `testo.md`; i report su di esso dichiarano il perimetro. Se l'intero racconto è ormai più aggiornato fuori dal Doc, chiedi all'autore di aggiornare il Doc o di cambiare la fonte nella scheda: non cambiarla in silenzio.
- Non modificare il Doc senza l'approvazione dell'autore. Prima mostra l'anteprima.
- Quando scrivi nel Doc usa il controllo sulla revisione, così la scrittura fallisce se il documento è cambiato nel frattempo. Dopo ogni scrittura rileggi e verifica.
- Usa il `revisionId` acquisito insieme al testo mostrato nell'anteprima: è un token temporaneo per rifiutare scritture concorrenti, non un punto di ripristino. Dopo un conflitto rileggi il Doc e rivaluta l'anteprima; non sostituire alla cieca il token. Per ripristinare il documento completo usa la cronologia di Google Docs.
- Quando scrivi prosa nel testo non lasciare segni, note o commenti: il passaggio deve essere indistinguibile dal testo che lo circonda. È una scelta dell'autore.

### Google Docs nei due strumenti

Lo strumento Google Docs dell'ambiente è il plugin Google Drive in Codex (skill `google-docs`) e il connettore Google Drive di claude.ai in Claude Code. Il flusso dipende da queste capacità; se una manca, dichiaralo e segui l'ultima colonna.

Prima di usare un connettore verifica le capacità disponibili nella sessione, senza modificare documenti come prova:

| Capacità | Condizione necessaria | Se manca |
| --- | --- | --- |
| Lettura completa | Tutto il testo, incluse eventuali schede | Chiedi un'esportazione .docx aggiornata |
| Identità della revisione | `revisionId` acquisito con il testo | Nessuna scrittura remota |
| Scrittura condizionata | Rifiuto della modifica se la revisione cambia | Proposta completa in `materiali/`, applicata dall'autore |
| Acquisizione delegata per lettura a freddo | Subagente disponibile e con accesso alla fonte | Acquisisci direttamente e dichiara che il testo è passato nel contesto |

In questo progetto, **in Claude Code non scrivere nel Doc**, né testo né commenti: le proposte restano locali. Non rinominare, spostare, condividere o cestinare la fonte. In Codex la scrittura richiede tutte le capacità sopra, anteprima approvata e verifica successiva. La versione pubblica non certifica un collaudo delle scritture remote. Dettagli: `docs/google-docs.md`.

### Rigenerare la copia dalla fonte

Quando una skill dice «acquisisci la fonte e rigenera la copia come in `AGENTS.md`», intende questi passi; la skill indica solo le sue deviazioni.

1. Esegui `python -X utf8 strumenti/prosa.py fonte <nome>`. Restituisce soltanto `doc`, `fonte_file` (percorso assoluto risolto) e `modalita`, senza intenzioni narrative. Non acquisisce la fonte e non ne certifica l'esistenza o l'aggiornamento.
2. **Con `doc` compilato:** con lo strumento Google Docs dell'ambiente leggi il Doc per intero, tutte le schede, controllando la completezza della risposta. Salva in `racconti/<nome>/.doc-grezzo.md`: capoversi separati da una riga vuota, a capo interni e tabulazioni conservati, corsivo tra asterischi se restituito. Proteggi con backslash i caratteri letterali Markdown (in particolare `*`, `_`, `#`, parentesi quadre, backtick e backslash). Non confondere gli asterischi del testo con quelli di formattazione. Un capoverso composto solo da asterischi (`* * *`, `***`) è uno stacco di scena: scrivilo senza backslash. Poi esegui `python -X utf8 strumenti/prosa.py importa racconti/<nome>/.doc-grezzo.md <nome>`.
3. **Senza `doc`, con `fonte_file`:** acquisisci quel file `.docx`, `.md` o `.txt` e usa `python -X utf8 strumenti/prosa.py importa "<percorso assoluto restituito>" <nome>`. Non importare la vecchia cache come originale. Se il file manca o non è leggibile, chiedi all'autore il file aggiornato e fermati sul lavoro testuale: la copia precedente è conservata ma non aggiornata.
4. **Senza entrambe le fonti:** per un'idea senza bozza prosegui sulla scheda e salta lettura e controlli del testo. Se è previsto un testo, identifica prima la fonte con l'autore.
5. Dopo un'importazione riuscita registra in `stato.md` data/ora, provenienza (URL o percorso acquisito) ed eventuali limiti segnalati. Se disponibile, registra anche la revisione Docs. Per `racconto-lettore`, conserva questi dati durante l'acquisizione e aggiungili al registro solo dopo il resoconto, senza leggere lo stato. Per la prima lettura strutturale indipendente, conserva i dati e registrali dopo aver annotato l'impressione sul testo e letto lo stato. Lo script rigenera le scene in modalità lunga ed elimina quelle obsolete in modalità breve; invalida `testo-unito.md`.

Se lo strumento non riesce a leggere il Doc per intero, chiedi all'autore di scaricarlo (File → Scarica → .docx) e importa il file fornito. Con `doc:` compilato, anche un eventuale `fonte_file:` è solo un'esportazione sostitutiva: non usarla automaticamente come ripiego. Registra esplicitamente **«esportazione sostitutiva; versione online corrente non verificata»**, percorso e data di acquisizione. Una lettura fallita non autorizza a presentare la cache come corrente.

**Verifica della copia.** Quando l'autore fornisce un .docx scaricato dal Doc, e prima di una redazione o di un invio (chiedigli il .docx), esegui `python -X utf8 strumenti/prosa.py verifica "<file>" <nome>` e registra l'esito in `stato.md`. Una copia che differisce non si usa come evidenza: si rigenera. Se differisce solo nella formattazione, dichiaralo quando il passaggio riguarda corsivi o impaginazione. Non serve a ogni passaggio.

Il lettore DOCX conserva la prosa ordinaria e il corsivo diretto dei run, non ricostruisce gli stili ereditati o l'impaginazione Word. Leggi gli avvisi sulle strutture non supportate e dichiara i limiti prima del passaggio editoriale. In Markdown conserva gli escape letterali; i file TXT sono testo letterale. Le annotazioni come `(dedotto)` vanno nei commenti (`modalita: breve # (dedotto)`) o nel corpo della scheda, mai dentro i valori enumerati.

## Chat e consegne

- **Un passaggio grosso per chat.** Passaggi grossi: onboarding, nucleo, revisione di un livello sull'intero testo, lettura a freddo, calibrazione o aggiornamento della voce, redazione con conversione dei dialoghi.
- Se in questa chat è già stato fatto un passaggio grosso e l'autore ne chiede un altro, non cominciarlo: aggiorna `stato.md` e scrivigli la riga da incollare in una chat nuova, per esempio `$racconto-revisione riga il-faro`.
- Se la chat è diventata lunga anche per un passaggio piccolo, proponi di spostarsi in una chat nuova.
- All'inizio di ogni passaggio leggi `racconti/<nome>/stato.md`; alla fine aggiornalo con le sezioni del modello (`racconti/_modello/stato.md`): **Proposte attive** con percorso e stato, **Questioni aperte** con esito e report, **Decisioni** prese con l'autore, **Prossimo passo** con la riga da incollare e cosa leggere, **Fatto** con passaggio, perimetro e percorso. **Eccezioni**: `racconto-lettore` non lo legge prima del resoconto, e non legge mai `stato-archivio.md`; nella prima lettura di una revisione strutturale indipendente, acquisisci solo fonte e testo e annota effetto percepito, cambiamento e domande prima di leggere `stato.md`, scheda e letture precedenti. Se la chat contiene già le intenzioni del racconto, usa una chat nuova per quella prima impressione indipendente oppure dichiara che la revisione è informata.
- **Stati brevi e attuali.** «A che punto siamo», «Proposte attive» e «Prossimo passo» si sostituiscono, non si accodano: poche righe su ciò che vale adesso; la storia va in **Fatto**. Quando **Fatto** supera circa quindici voci o lo stato circa 8 KB, sposta testualmente, senza riassumerle, le voci più vecchie in `stato-archivio.md` e lascia in **Fatto** una riga che lo indica. L'archivio si legge solo quando serve la storia.
- Prima di chiudere la chat salva in `materiali/` ogni proposta testuale ancora utile, per intero, con stato (proposta, non approvata, approvata) e punto di intervento. Usa nomi univoci: primo `AAAA-MM-GG-<tipo>.md`, poi `-02`, `-03` prima di `.md`; `python -X utf8 strumenti/prosa.py nome-libero <percorso>` stampa il primo libero senza creare il file. Metti percorso e stato in `stato.md`; se il testo di una vecchia proposta non è disponibile, dichiara che manca senza ricostruirlo.
- Ogni nuovo report o lettura comincia con l'intestazione stampata da `python -X utf8 strumenti/prosa.py intestazione <nome>` (data/ora, fonte, SHA-256 di `testo.md`); aggiungi `--revisione <id>` se la revisione Docs è disponibile. I vecchi report privi di impronta restano storici; non attribuire loro l'impronta attuale. Anche report, letture e anteprime usano nomi univoci con la stessa regola.
- Passaggi piccoli, nella stessa chat: un raccordo, una variante, discutere un report appena prodotto, aggiornare la scheda, i conteggi.

## Prima di ogni passaggio

Chiediti, e rispondi a te stesso in poche righe prima di lavorare:

- Che effetto deve avere questo passaggio sul lettore, o sul lavoro dell'autore?
- Cosa deve restare non detto? (sezione **Taciuto** della scheda; nella prima lettura strutturale indipendente rispondi provvisoriamente dal solo testo e confronta la scheda dopo le note iniziali)
- Quale sarebbe il successo sbagliato? Per esempio una revisione che rende la prosa più corretta e meno sua.

Chiedi all'autore solo quando la risposta cambia il lavoro. Altrimenti dichiara la tua lettura e procedi.

## Voce

- `voce/profilo.md` contiene solo tratti generali dello stile dell'autore. Le scelte di un racconto vanno nella sua scheda.
- Il profilo si modifica solo con `$racconto-voce`, su richiesta esplicita dell'autore. La calibrazione provvisoria può usare un racconto quasi finito solo se l'autore la chiede esplicitamente: i risultati restano candidati. Un tratto si conferma con evidenza in almeno due racconti consolidati. L'assenza in un nuovo racconto non lo cancella; una controevidenza richiede di riesaminare ambito e fiducia e motivare nello storico l'eventuale modifica.

## Mappa delle skill

| Richiesta | Skill |
| --- | --- |
| nuovo racconto da una bozza o da un Doc | `racconto-nuovo` |
| idea, struttura, direzioni, scaletta | `racconto-nucleo` |
| raccordi, varianti, abbozzi, lucidature | `racconto-scrittura`, solo se l'autore la chiama con `$racconto-scrittura`: «puoi migliorare…» non basta |
| parere, revisione, redazione, bozze | `racconto-revisione` |
| lettura a freddo | `racconto-lettore` (sempre in una chat nuova) |
| profilo di voce | `racconto-voce`, solo se l'autore la chiama con `$racconto-voce` |
| conteggi e controlli | `python -X utf8 strumenti/prosa.py` |

## Fonti

Le nozioni di tecnica e di norma stanno in `officina/` con le fonti in `officina/fonti.md`. Quando citi una regola all'autore, indica la sigla della fonte. Se una cosa non è coperta da una fonte, dillo.

## Versioni

Prima di un commit verifica i file inclusi. Versiona solo codice, istruzioni, modelli ed esempi destinati al pubblico. I testi personali richiedono una copia di sicurezza separata: Git li ignora. Non caricare materiale privato per dimostrare il funzionamento.
