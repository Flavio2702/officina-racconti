# La risposta critica

Come rispondere a un racconto in modo che l'autore torni al lavoro con più chiarezza, non con un verdetto. Vale per `racconto-lettore` e `racconto-revisione`. Le sigle tra parentesi quadre rimandano a `officina/fonti.md`.

## L'ordine

Il Critical Response Process di Liz Lerman [F36] dà a chi risponde quattro tappe, in quest'ordine. Nato per un confronto dal vivo, qui è adattato a un resoconto scritto (adattamento dell'officina):

1. **Significato.** Cosa ha colpito, emozionato, incuriosito: in modo specifico, con il passaggio citato. Mai la lode generica («bella prosa», «finale potente»): se non si sa dire *dove* e *perché*, non si scrive.
2. **Domande dell'autore.** Se l'autore ha fatto domande invocando la skill, si risponde a quelle, sul tema, prima di ogni altra cosa. Lì si può esprimere un'opinione, perché è stata chiesta.
3. **Domande neutre.** Le domande che il testo lascia aperte a chi risponde, senza un giudizio dentro (vedi sotto). Nel resoconto scritto restano domande per l'autore: non si risponde da soli.
4. **Opinioni.** Solo quelle che l'autore ha chiesto. Invocare la revisione è già la richiesta di un parere sul livello scelto; per il lettore, il verdetto della persona è l'opinione prevista dalla skill. Fuori da questo, nessuna opinione non richiesta.

L'ordine non attenua: le questioni restano intere, arrivano solo dopo che si è detto cosa funziona e cosa si è capito.

## La prova della domanda neutra

Una domanda è neutra se non contiene un'opinione [F36]. La prova: togliendo il punto interrogativo, resta un giudizio? Se sì, non è neutra.

| Non neutra | Neutra |
| --- | --- |
| Perché il finale è così lungo? | Che cosa ti ha guidato nella lunghezza del finale? |
| Non pensi che la madre sia troppo fredda? | Che cosa volevi che il lettore sentisse verso la madre? |
| Serve davvero la scena del bar? | Quale lavoro fa per te la scena del bar? |
| Non sarebbe meglio cominciare dalla telefonata? | Come hai scelto da dove cominciare? |

Le parole spia: *troppo*, *davvero*, *non pensi che*, *non sarebbe meglio*, i condizionali che suggeriscono una soluzione.

## La lettura a tappe

Chi legge per la prima volta non sa cosa verrà: è questa ignoranza che il resoconto deve conservare. Saunders legge il primo racconto del suo libro una pagina alla volta, fermandosi sulle attese del lettore [F37] (fonte secondaria). L'officina ne ricava una procedura propria (euristica, non presa dalla fonte):

- il testo si legge in tappe di circa 1.800 battute, una cartella editoriale (euristica dell'officina; `prosa.py tappe`);
- a ogni fermata, prima di leggere oltre, si annota **cosa so**, **cosa mi aspetto**, **cosa mi chiedo**;
- le previsioni sbagliate restano scritte. Non sono un errore del lettore: dicono dove il testo ha guidato le attese e dove le ha sorprese o deluse;
- il resoconto finale si scrive dalle note, non dal ricordo del testo intero.

## I limiti del giudizio del modello

Tre risultati di ricerca, nessuno sui racconti italiani:

- i giudizi dei modelli sulla qualità creativa di racconti non concordano con quelli degli esperti [F39];
- i modelli trovano i passaggi difettosi di un testo con precisione inferiore all'accordo fra esperti [F38];
- un modello valutatore tende a preferire i testi che riconosce come propri [F40].

Conseguenze pratiche:

- **Verdetti come ipotesi.** Un giudizio di qualità dell'assistente si scrive come lettura motivata da passaggi citati, non come misura. La decisione è dell'autore.
- **Dichiarare la provenienza.** Quando un passaggio giudicato coincide con prosa dell'assistente (`prosa.py provenienza`), il report lo dice accanto al giudizio: su quel passaggio il valutatore può essere di parte [F40].
- **Seconda lettura con l'altro strumento.** Se un giudizio pesa su prosa scritta dall'assistente, conviene una seconda lettura con l'altro strumento del progetto, in una chat nuova. Non elimina il problema: lo riduce, perché il secondo modello riconosce meno quei testi come propri (deduzione dell'officina da [F40], non verificata).
