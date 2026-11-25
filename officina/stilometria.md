# Misurare la voce

Come `prosa.py` misura lo stile di un passaggio contro i testi dell'autore, e che cosa le misure non dicono. Riguarda i comandi `confronta`, `deriva` e `voce`. Le sigle tra parentesi quadre rimandano a `officina/fonti.md`.

## Che cosa dicono e che cosa no

Le misure dicono dove un passaggio esce dalla variazione che i testi dell'autore mostrano su pezzi della stessa lunghezza. Non dicono:

- **chi ha scritto il passaggio**: la stilometria attribuisce con affidabilità solo su campioni di qualche migliaio di parole, e anche così la soglia cambia da testo a testo [F61]. Qui i passaggi sono di decine o centinaia di parole;
- **se il passaggio è buono**: uno scarto può essere la ragione stessa del passaggio, per esempio un finale che rallenta;
- **che cosa correggere**: non c'è un valore da raggiungere.

Il rischio da evitare è il **successo sbagliato**: usare le misure per spingere la prosa verso la media dei testi dell'autore. Scrivere con i modelli linguistici tarati sul feedback umano rende i testi di autori diversi più simili fra loro [F68] e li avvicina allo stile dominante [F69]. Uno strumento che premiasse la vicinanza alla media farebbe lo stesso lavoro dall'interno.

## Le misure

- **Tratti di voce**: i marcatori di voce di `strumenti/marcatori_voce.txt`, per esempio i connettivi del parlato presi dalle prove del profilo; poi domande nella narrazione, similitudini, gerundi e «quindi, invece, comunque». Sono descrittivi: nessuno è un difetto.
- **Segnali dell'italiano generato**: gerundi astratti in coda, connettivi di raccordo saggistico, terne, *non solo… ma* [F32][F33][F34]. «quindi», «invece» e «comunque» non stanno qui: sono anche connettivi del parlato e del periodo per aggiunte.
- **Ritmo e punteggiatura**: media, deviazione e percentili della lunghezza delle frasi; punto e virgola, esclamativi e puntini contati nella sola narrazione.
- **Distanza**: il Delta di Burrows, cioè la media degli scarti in z-score sulle parole più frequenti del riferimento [F58][F59]. Sono parole funzionali per lo più, che si usano senza pensarci e dipendono poco dal tema [F63]. Si tolgono i pronomi personali, che dipendono dal punto di vista del racconto, e le parole quasi sempre maiuscole, che sono nomi propri. Con almeno due racconti abbastanza lunghi esce anche la parola concentrata per oltre il 70% in uno solo [F59]. Il report mostra le parole che più pesano nella distanza, in eccesso e mancanti: il profilo di scarto spiega la distanza meglio del numero [F60]. Verso i brani approvati di `voce/esempi.md` la distanza è il coseno fra i due profili di scarto (Cosine Delta [F60]).

## Bande, non soglie

Ogni misura si legge contro le **finestre** dei testi dell'autore: pezzi di frasi intere consecutive, lunghi almeno quanto il passaggio, che partono ogni mezza finestra e non attraversano stacchi di scena. È l'idea della *rolling stylometry* [F62]. La **banda** va dal 5° al 95° percentile delle finestre.

Il report dice soltanto dove cade il passaggio: «dentro», «oltre il 95° percentile» oppure «oltre il massimo osservato» (e i loro opposti). Con meno di otto finestre non c'è banda e il report dice «non abbastanza testo». Le soglie fisse di prima (un rapporto di 1,3, dodici punti percentuali, il doppio dell'atteso) non sapevano quanto l'autore stesso vari su un pezzo di quella lunghezza; su ottanta parole la variazione è molto grande.

Per la distanza, la banda viene dalle finestre dell'autore lette contro le altre, una alla volta, escluse quelle che le si sovrappongono. Conta solo lo scarto verso l'alto. Una distanza sotto la banda vuol dire un passaggio più vicino alla media di quasi tutti i pezzi dell'autore: non è una prova di voce, e di solito la calibrazione non lo distingue.

## Il riferimento: stesso racconto prima del corpus

- **Stesso racconto**: le frasi del racconto senza coincidenze con i materiali dell'assistente, senza il passaggio stesso.
- **Corpus di voce**: i racconti con `stato: consolidato`, solo le frasi senza coincidenze. La coincidenza è quella di `provenienza` (sequenze di otto parole), riportata alla frase. Un racconto che coincide oltre il 90% si esclude: di solito vuol dire che un materiale lo riporta per intero, e la coincidenza non distingue più niente.
- **Contrasto**: le frasi coincidenti per metà o più, di tutti i racconti. Serve solo a misurare l'affidabilità, mai come riferimento. È testo coincidente, non testo dell'assistente: può contenere frasi dell'autore citate in un materiale.

La colonna dello stesso racconto vale di più. I racconti di uno stesso autore possono differire molto fra loro, per esempio nella lunghezza delle frasi, e una banda costruita su un racconto può descriverne male un altro (vedi sotto).

## Quanto distingue: la prova di calibrazione

`prosa.py voce` misura da sé quanto le misure distinguono, sul corpus di chi usa l'officina. Si rifà quando un racconto si consolida o cambiano i materiali (`$racconto-voce`).

- **Affidabilità per lunghezza**: a 50, 100, 200, 400 e 800 parole, le finestre di contrasto contro quelle dell'autore. L'AUC è la probabilità che una finestra di contrasto si separi da una dell'autore (0,5 = non distingue) [F65]. Le finestre si sovrappongono per metà, quindi quelle indipendenti sono circa la metà. Sotto 0,5 il contrasto risulta più vicino alla media dell'autore delle finestre dell'autore stesse: la prosa generata può essere più media [F68], e una distanza dal centro allora non la distingue.
- **Variazione tra racconti**: le finestre di un racconto lette contro la banda costruita sugli altri. L'atteso è circa il 10%; molto di più vuol dire che i racconti differiscono fra loro più di quanto una banda sola mostri, e conta di più la colonna dello stesso racconto.
- **Senza contrasto o con un solo racconto** il report lo dice e non stima nulla.

Che cosa aspettarsi, dalle fonti:

- fino a qualche centinaio di parole la distanza distingue poco o nulla [F61];
- i marcatori di voce misurano direttamente un tratto del profilo, ma sono pochi: in un passaggio breve la loro assenza non dice niente (osservazione dell'officina, da verificare con la tabella);
- nei passaggi lunghi la prosa generata tende ad appiattire la lunghezza delle frasi [F67]: deviazione e 90° percentile possono cadere sotto la banda.

## Limiti noti

- **Finestre**: a frasi intere, quindi alcune sono più lunghe di N; le misure sono ogni mille parole e reggono questa differenza.
- **Frasi e narrazione**: divise come in `controlla`, con le stesse approssimazioni.
- **Similitudini strette**: catturano anche paragoni semplici (*come gli altri*). Il conteggio di ogni «come» è un'altra misura, da non confondere con la prima.
- **«certo» fra i marcatori**: conta anche l'aggettivo.
- **Parole più frequenti**: con un corpus di cinquemila parole comprendono anche parole di contenuto e del punto di vista, come i verbi di percezione in prima persona. Un passaggio in terza persona si allontana per questo, non per lo stile.
- **Coincidenze**: la provenienza vede solo i materiali marcati. Il contrasto può contenere frasi dell'autore, e il dialogo pesa più nel contrasto che nel corpus.

## Nelle skill

- `racconto-scrittura`, prima di mostrare un passaggio: marcatori, ritmo e segnali, poi la colonna dello stesso racconto. Non si riscrive per riportare un numero nella banda e non si aggiungono marcatori per farli comparire.
- `racconto-revisione`, livello di riga: `deriva` indica dove rileggere per primo, soprattutto le finestre oltre la banda in zone coincidenti.
- `racconto-voce`: ogni numero del profilo viene dal report di `voce`, con la sua definizione e l'affidabilità a quella lunghezza.
