# Google Docs: integrazione opzionale

Il percorso locale funziona senza Google Drive. Per usare un Doc, l'assistente deve avere un connettore autorizzato al tuo account e accesso a quel documento. Il progetto non installa connettori e non conserva credenziali.

## Acquisire una bozza

1. Collega Google Drive nell'ambiente AI che usi e verifica che possa leggere il documento richiesto.
2. In una nuova chat richiama `racconto-nuovo` con il link del tuo Doc.
3. L'assistente registra il link nel campo `doc:` della scheda privata e acquisisce il testo. Con `doc:` compilato, il documento online è la fonte principale.
4. Prima dei passaggi successivi, la copia di lavoro viene rigenerata dalla fonte.

La disponibilità di lettura completa, schede multiple, revisione e scrittura dipende dal connettore della sessione. Non assumere che il solo accesso a Drive comprenda tutte queste operazioni.

## Quando la lettura non basta

Se il connettore non legge il testo per intero, l'assistente chiede un'esportazione `.docx` aggiornata e dichiara che la versione online corrente non è verificata. Una vecchia copia locale non diventa automaticamente la fonte.

Per lavorare stabilmente su un file locale, concorda esplicitamente il cambio di fonte e compila `fonte_file:` lasciando vuoto `doc:`. I dettagli operativi sono in [AGENTS.md](../AGENTS.md).

## Scrivere nel documento

La distribuzione pubblica non include un collaudo delle scritture remote. In questo progetto, Claude Code lascia sempre le proposte nei materiali locali. In Codex una modifica remota è ammessa solo se il connettore offre tutte le capacità richieste:

- testo e identificatore della revisione acquisiti insieme;
- anteprima approvata dall'autore;
- scrittura condizionata a quella stessa revisione;
- rilettura e verifica dopo l'intervento.

Se manca una capacità, il testo proposto resta in `materiali/` e viene applicato dall'autore. In caso di conflitto si riacquisisce il Doc e si rivede l'anteprima. `revisionId` non è un punto di ripristino: per recuperare il documento si usa la cronologia di Google Docs.

Non usare documenti reali come prova di scrittura. Un eventuale collaudo richiede un documento dimostrativo dedicato e autorizzato.
