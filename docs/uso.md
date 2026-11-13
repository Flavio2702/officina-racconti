# Comandi e percorso di lavoro

Esegui i comandi dalla radice del progetto. `python -X utf8 strumenti/prosa.py aiuto` elenca tutti quelli disponibili. Gli esempi seguenti presuppongono l'avvio rapido del [README](../README.md).

| Comando dopo `python -X utf8 strumenti/prosa.py` | Risultato |
| --- | --- |
| `fonte il-faro` | Mostra la fonte dichiarata, senza leggerla online |
| `conta il-faro` | Parole, battute e confronto con i limiti della scheda |
| `controlla il-faro --salva` | Controlli euristici e report locale |
| `dialoghi il-faro --salva` | Anteprima delle convenzioni e dei casi da verificare |
| `tappe il-faro` | Porzioni per una lettura progressiva |
| `verifica esempi/il-faro.md il-faro` | Confronto tra il file e la copia importata |
| `intestazione il-faro` | Fonte dichiarata, data e impronta della copia |
| `differenze il-faro <sha>` | Confronto con una copia conservata da una precedente importazione |
| `provenienza il-faro` | Coincidenze con materiali marcati come prosa dell'assistente |

`importa` aggiorna `testo.md`, conserva una copia per impronta e rigenera o invalida i derivati. Non modifica il file originale. Per provare versioni diverse, usa una fonte in `bozze/` e aggiornane il percorso nella scheda. Non modificare `testo.md` a mano.

## Dall'analisi alla revisione

In chat separate, usando `$` in Codex o `/` in Claude Code:

```text
$racconto-nucleo il-faro scaletta inversa
$racconto-lettore il-faro redattore
$racconto-revisione strutturale il-faro
$racconto-revisione riga il-faro
```

Scegli i passaggi che servono; il nucleo non è obbligatorio prima di una lettura a freddo. Il lettore non deve conoscere scheda, intenzioni o revisioni precedenti. Le sue impressioni sono ipotesi motivate, non misure della qualità.

Scrittura e calibrazione della voce richiedono invocazioni esplicite. Non calibrare la tua voce sull'esempio sintetico. Per usarle con i tuoi racconti, indica il compito e il perimetro.

## Impostazioni personali

`strumenti/prepara.py` crea i file locali di `voce/` e `strumenti/stilemi_extra.txt`. Eseguirlo nuovamente non sovrascrive le impostazioni. Le formule aggiuntive sono espressioni regolari Python: il comando segnala quelle non valide. Le scelte editoriali personali si salvano in `voce/scelte-redazionali.md`; le deroghe di un racconto nella sua scheda.

## Prove manuali delle skill

Le prove seguenti si eseguono solo su testi dimostrativi. Il loro elenco non attesta un collaudo del modello:

| Scenario | Comportamento da osservare |
| --- | --- |
| Nuova bozza locale | Fonte registrata, copia importata, scheda e stato creati; nessuna riscrittura automatica |
| Richiesta generica di migliorare una frase | Distinzione tra revisione e invocazione esplicita della scrittura |
| Lettura a freddo in una nuova chat | Nessuna apertura di intenzioni o report precedenti; note prima della tappa successiva |
| Revisione senza cambiamenti al testo | Confronto con impronta e questioni aperte prima di ripetere il lavoro |
| Ripresa in un'altra chat | Stato e proposte recuperabili; prossimo passo coerente con i file |
| Connettore senza controllo della revisione | Proposta locale, nessuna modifica al Doc |

Registra lo strumento e la versione usati, il caso, l'esito osservato e gli eventuali limiti. Non trasformare un comportamento osservato in una garanzia su tutti i modelli.
