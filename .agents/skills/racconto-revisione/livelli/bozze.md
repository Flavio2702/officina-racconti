<!-- Materiale adattato e modificato per Officina Racconti; fonti, modifiche e licenze in CREDITI.md. -->

# Livello di bozze

La domanda: cosa è sfuggito? L'ultima passata, sul testo che sta per partire.

## Metodo

1. `python -X utf8 strumenti/prosa.py controlla <nome>`: nessuna segnalazione di superficie aperta.
2. Leggi lentamente, una frase alla volta, cercando solo errori di superficie: refusi, parole doppie o mancanti, maiuscole, punteggiatura, spazi.
3. Controlla titolo, stacchi di scena, prima e ultima riga.

## Consegna

Per un concorso o una rivista, una lista di controllo con l'esito di ciascuna voce:

- **Limite di battute**: `python -X utf8 strumenti/prosa.py conta <nome>`, confrontato con `limite_battute`.
- **Anonimato**: niente nome dell'autore nel testo, se il bando lo chiede.
- **Modulo o formato** richiesto dal bando (file, carattere, impaginazione, titolo); se non lo conosci, chiedilo all'autore.
- **Regola sull'IA**: `ia_bando` e, se nota, la regola del bando, accanto a `python -X utf8 strumenti/prosa.py provenienza <nome>`: quota totale e capoversi principali. È una coincidenza testuale con i materiali marcati, non un'attribuzione né un giudizio di ammissibilità.
- **Copia verificata**: con il .docx scaricato dal Doc, `python -X utf8 strumenti/prosa.py verifica "<file>" <nome>`; senza, la voce resta aperta.

## Nel report

Solo l'elenco dei casi, con la riga, e la lista di consegna con i fatti. Nessun commento di stile: a questo punto la prosa non cambia più. Chiudi scrivendo che la decisione di inviare è dell'autore.
