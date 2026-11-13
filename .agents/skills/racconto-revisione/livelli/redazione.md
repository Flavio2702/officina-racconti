<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Livello di redazione

La domanda: il testo è corretto e coerente? Riferimento: `officina/norme-redazionali.md`, con le fonti in `officina/fonti.md`.

## Metodo

1. Leggi le scelte locali in `voce/scelte-redazionali.md` e le norme generali in `officina/norme-redazionali.md` e le deroghe della scheda. Se una scelta è ancora «da decidere» e il testo la tocca (la virgola dopo il caporale, *sé stesso*), chiedi all'autore di deciderla ora, prima di applicare, e scrivila nel file locale `voce/scelte-redazionali.md`.
2. Usa il report di `prosa.py controlla` per i candidati di superficie: accenti, apostrofi, puntini, spazi, virgolette rovesciate. I conteggi dei segni di dialogo non dimostrano convenzioni miste: verifica nel testo e nelle deroghe della scheda.
3. Leggi il testo per quello che lo script non vede.

## Controlli del modello

- **Tempi verbali**: lo stesso episodio passato ora al passato prossimo ora al remoto; passaggi tra presente e passato senza funzione; sequenze tutte all'imperfetto dove si perde l'ordine dei fatti.
- **Pronomi**: *gli* per *le*.
- **d eufonica** davanti a vocale diversa: segnala, non correggere.
- **Consecutio** e concordanze.
- **Coerenza delle scelte**: *sé stesso* o *se stesso*, apostrofo, virgolette per le citazioni dentro le battute.

## La conversione dei dialoghi

Solo dopo che l'autore ha visto l'anteprima.

1. `python -X utf8 strumenti/prosa.py dialoghi <nome> --salva` crea l'anteprima in `materiali/`.
2. Mostra all'autore il riepilogo: proposte semplici da verificare, casi ambigui con originale e motivo, capoversi da spezzare. I casi da controllare e i capoversi da spezzare li decide lui, uno per uno.
3. Prima di una redazione estesa salva in file distinti di `materiali/` il testo precedente delle parti interessate e l'anteprima approvata, con l'intestazione di `AGENTS.md`, e collegali in `stato.md`. Il documento completo si ripristina dalla cronologia Docs, riconoscendo la versione da data/ora o da un nome.
4. Con `doc:` compilato e scrittura con controllo sulla revisione disponibile (`AGENTS.md`, «Google Docs nei due strumenti»), applica le conversioni approvate a gruppi, con il `revisionId` acquisito insieme al testo dell'anteprima, rileggendo dopo ogni gruppo. Altrimenti, e sempre con originale locale, l'anteprima approvata resta in `materiali/`: l'autore applica gli interventi, poi si riacquisisce la fonte.

## Nel report

Qui serve l'elenco: ogni caso con la riga, la forma presente, la forma della norma e la sigla della fonte, raggruppati per tipo. Distingui gli errori (norma) dalle incoerenze (scelte della raccolta) e dalle segnalazioni da valutare (d eufonica, formule).
