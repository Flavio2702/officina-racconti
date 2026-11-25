# Lessico e figure

Il riferimento per la revisione di riga e per la scrittura. Le sigle tra parentesi quadre rimandano a `officina/fonti.md`. Come in `punteggiatura-e-ritmo.md`, ogni indicazione è **norma**, **scelta** o **segnale**.

Il successo sbagliato, qui più che altrove: una lingua più ricca, più varia, più corretta, e meno dell'autore. Se la sua voce mescola registri, per esempio il colto e il parlato (`voce/profilo.md`), la revisione non la porta verso un italiano medio e levigato.

## Lessico

### La parola esatta

Calvino indica nell'esattezza un valore della scrittura e chiama «peste del linguaggio» l'uso approssimativo e generico delle parole [F54]. Nella pratica: una parola generica dove il lettore avrebbe bisogno di vedere (*cosa*, *roba*, *situazione*, *fare*, *mettere*, *molto*, *particolare*) è un **segnale** della categoria «poca specificità» della tavola LAMP [F38]. La domanda è quale oggetto, quale gesto, quale qualità quella scena avrebbe. Nel parlato del narratore la parola generica può essere voce: *insomma*, *tipo*, *una cosa del genere* servono al pensiero in diretta.

### L'antilingua

Calvino chiama *antilingua* l'italiano d'ufficio che fugge davanti alle parole concrete: *effettuare* per *fare*, la pratica al posto della cosa. Ne vede l'origine in un «terrore semantico» [F53]. In un racconto l'antilingua nella narrazione è un **segnale**: un registro burocratico, a volte calcato dalla prosa generata (vedi `difetti-ai.md`, parte 1), che allontana il lettore. In battuta, o nell'indiretto libero di un personaggio che parla così, è caratterizzazione: si lascia.

`prosa.py controlla` cerca nella sola narrazione un elenco di osservazione: *effettuare*, *procedere a*, *provvedere a*, *nel momento in cui*, *a livello di*, *in merito a*, *al fine di*, *risultare essere*, *il medesimo*, *suddetto*, *espletare*, *usufruire*, *in data*, *nella fattispecie*, *onde* + infinito.

### *Piuttosto che* per «o»

**Norma.** *Piuttosto che* vuol dire preferenza (*in treno piuttosto che in aereo*: meglio il treno). Usato al posto di *o* per elencare alternative equivalenti è giudicato inammissibile dalla Crusca, perché può creare ambiguità; le alternative sono *o*, *oppure*, *anziché*, *invece che* [F51]. In battuta può caratterizzare un parlante [F51]. Lo script lo segnala nella narrazione; il modello decide se è preferenza o disgiunzione.

### Ripetizione e sinonimi

La *variatio*, cioè variare le parole per evitare la monotonia, è un principio retorico, opposto alla ripetizione [F55]. È uno strumento, non un obbligo. La scuola insegna a evitare le ripetizioni con i sinonimi; in narrativa il sinonimo messo per evitare un'eco cambia spesso registro o sfumatura e attira l'attenzione su di sé (*il gatto… il felino… il micio*).

- Un'eco ravvicinata non voluta (vedi `voce/difetti-personali.md`) si risolve di solito **togliendo** una delle due parole, cambiando la costruzione o usando un pronome. Il sinonimo è l'ultima scelta.
- Una ripetizione che lavora (anafora, ritorno di un'immagine, parola chiave del racconto) si lascia; se la scheda la dichiara in `ricorrenti`, lo script non la segnala.

### Registro e italiano dell'uso medio

L'italiano di oggi ha accolto nello standard tratti che un tempo erano solo del parlato. È quello che i linguisti chiamano *italiano dell'uso medio* o *neo-standard* [F49]. Nella voce di un narratore in prima persona che parla e nelle battute, questi tratti **non sono errori** e la revisione non li corregge:

- *lui*, *lei*, *loro* come soggetto;
- dislocazioni (*i giornali li leggo*; a destra, *lo so, che sei stanco*, dove la virgola è corretta: vedi `punteggiatura-e-ritmo.md`);
- frasi scisse (*è lui che ha cominciato*);
- *che* polivalente nel parlato (*la sera che sono uscito*);
- imperfetto di cortesia e ipotetico (*volevo chiederti*, *se lo sapevo non venivo*);
- *ci* con *avere* nel parlato (*ci ho fame*);
- *gli* come dativo plurale (*gli ho detto*, a loro) [F13][F49];
- *ma però* rafforzativo.

Restano norma *gli* per *a lei* [F13] e le forme di `norme-redazionali.md`. Se un tratto dell'uso medio compare nella narrazione di un narratore esterno e sorvegliato, è un **segnale** di registro: chiedi se il salto è voluto.

## Figure

Una figura lavora quando fa vedere o sentire qualcosa che la parola diretta non darebbe, nel modo in cui lo vedrebbe chi guarda. Costa quando decora, spiega o stona con il punto di vista. Le definizioni vengono dal Vocabolario Treccani [F56]; i criteri d'uso sono indicazioni di mestiere dell'officina.

### Cinque criteri

1. **Dal mondo di chi guarda.** In focalizzazione interna la figura appartiene all'esperienza del personaggio (vedi `scena.md`). Un narratore che misura gli affetti con le parole del commercio o della gara lo fa perché è così che pensa: la figura dice chi è. Una similitudine presa da un mondo che il personaggio non conosce rompe l'immersione.
2. **Non spiegare.** Una similitudine che dopo il fatto dice cosa significa e quanto pesa è il «commento emotivo» di `difetti-ai.md`, parte 2. La figura deve fare il lavoro al posto della spiegazione, non dopo di essa.
3. **Coerenza dell'immagine.** La metafora mista mette insieme due immagini incompatibili nella stessa frase (*un fiume di parole che prende fuoco*). Se il lettore se le rappresenta, inciampa.
4. **Non di repertorio.** L'ossimoro e l'iperbole di consumo (*silenzio assordante*, *il peso del mondo*) sono formule, non figure: `difetti-ai.md`, parte 3, e la lista dello script.
5. **Non in fila.** Due similitudini nella stessa frase o tre in poche righe si contendono l'attenzione e ciascuna indebolisce l'altra. Lo script segnala solo questi accumuli, non il numero: le similitudini con *come* e *come se* possono essere un tratto della voce (`voce/profilo.md`).

Le metafore spente nell'uso (*la gamba del tavolo*, *il braccio della lampada*), cioè le catacresi, non sono figure da valutare: sono il nome della cosa [F56].

### Tavola

| Figura | Che cosa fa | Quando serve al racconto | Quando costa |
| --- | --- | --- | --- |
| Similitudine | paragona con un nesso esplicito, *come*, *come se* [F56] | rende concreto uno stato interiore con un oggetto del mondo del personaggio | spiega dopo il fatto; viene da fuori del punto di vista; si accumula |
| Metafora | trasferisce un termine a un concetto diverso, con la similitudine sottintesa [F56] | condensa un'immagine in una parola; caratterizza chi la pensa | mista, decorativa, di repertorio |
| Sinestesia | unisce due sfere sensoriali (*un grido giallo*) | percezione alterata, ricordo, ebbrezza | quando è un vezzo e non una percezione |
| Anafora | ripete una parola in testa a più frasi | insistenza, ossessione, preghiera, elenco che cresce | quando nessuno l'ha voluta: è il segnale «attacchi ripetuti» di `punteggiatura-e-ritmo.md` |
| Climax | dispone gli elementi in intensità crescente | accumulo di pressione verso una svolta | come terna automatica in coda alla frase (`difetti-ai.md`, parte 1) |
| Asindeto e polisindeto | elenco senza congiunzioni oppure con *e… e… e* | accelerazione oppure respiro lungo, parlato, stupore | quando l'elenco non porta nulla di nuovo |
| Ellissi | omette ciò che il lettore ricostruisce | il taciuto, il salto di tempo, la battuta tronca | quando il lettore non ha gli elementi per ricostruire |
| Litote | afferma negando il contrario (*non era stupido*) | ironia trattenuta, pudore, understatement | quando diventa il modo fisso di dire le cose |
| Iperbole | esagera (*ci ho messo un secolo*) | voce parlata, autoironia, sfogo | di repertorio; in una voce sobria stona |
| Ironia | dice altro da ciò che intende, e il lettore lo vede | lo scarto tra narratore e autore, la conclusione frettolosa del narratore che il testo smentisce | quando viene spiegata |
| Ossimoro | accosta due termini contrari | una contraddizione vera del personaggio | quando è di repertorio |

## Cosa misura lo script e cosa resta al modello

`prosa.py controlla` mostra le sezioni solo quando trova qualcosa:

- **Lessico da guardare**: antilingua e *piuttosto che* nella sola narrazione, con riga ed estratto;
- **Accumuli di similitudini**: due similitudini esplicite nella stessa frase, o tre entro 120 parole dello stesso capoverso, con il totale come contesto. Il riconoscimento è grezzo: *come il*, *come la* catturano anche i paragoni semplici (*come gli altri*).

Restano al modello la parola generica, la metafora mista, la figura fuori dal punto di vista, la figura che spiega, il registro e ogni giudizio su ciò che lo script trova.
