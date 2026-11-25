#!/usr/bin/env python3
"""prosa.py: conteggi e controlli per i racconti della raccolta.

Conta e segnala, non corregge. Solo libreria standard di Python (3.8+).

Uso:
  python -X utf8 strumenti/prosa.py nuovo <nome>                 crea racconti/<nome>/ dal modello
  python -X utf8 strumenti/prosa.py fonte <racconto>            solo doc, fonte_file risolta e modalita (JSON)
  python -X utf8 strumenti/prosa.py importa <file> <racconto>    normalizza un testo e lo salva come testo.md
                                       (conserva anche la copia in copie/<sha16>.md)
  python -X utf8 strumenti/prosa.py intestazione <racconto> [--revisione <id>]
                                       blocco d'intestazione dei report: data/ora, fonte, SHA-256,
                                       provenienza se non zero
  python -X utf8 strumenti/prosa.py nome-libero <percorso>       primo nome libero (-02, -03...) senza creare il file
  python -X utf8 strumenti/prosa.py differenze <racconto> <sha>  capoversi cambiati da una copia conservata
  python -X utf8 strumenti/prosa.py provenienza <racconto> [materiale ...] [--salva]
                                       quota di testo.md che coincide con materiali dell'assistente
                                       (senza materiali: quelli marcati «Autore del testo: assistente»)
  python -X utf8 strumenti/prosa.py tappe <racconto> [--battute N]
                                       testo.md -> tappe/NN.md per il lettore (circa 1.800 battute)
  python -X utf8 strumenti/prosa.py conta <racconto>             parole, battute, distanza dai limiti
  python -X utf8 strumenti/prosa.py controlla <racconto> [--salva]
  python -X utf8 strumenti/prosa.py confronta <passaggio> <racconto>
                                       profilo del passaggio contro le bande dello stesso racconto
                                       e del corpus di voce, distanza e parole che la spiegano
  python -X utf8 strumenti/prosa.py voce [--salva]                misure riproducibili del corpus di voce
                                       (racconti consolidati, frasi senza coincidenze) e affidabilità
                                       (con --salva: voce/misure/AAAA-MM-GG-misure.md)
  python -X utf8 strumenti/prosa.py deriva <racconto> [--finestra N]
                                       finestra mobile lungo il racconto contro il corpus di voce
                                       (N parole, 200 se omesso)
  python -X utf8 strumenti/prosa.py dialoghi <racconto> [--salva]
  python -X utf8 strumenti/prosa.py dividi <racconto>            testo.md -> scene/NN.md sui separatori
  python -X utf8 strumenti/prosa.py unisci <racconto>            testo.md -> testo-unito.md (copia)
  python -X utf8 strumenti/prosa.py registra <racconto> "<riga>" accoda «- <riga>» a stato.md senza mostrarlo
  python -X utf8 strumenti/prosa.py verifica <file> <racconto> [--salva]
                                       confronta testo.md con un'esportazione (.docx, .md, .txt)
  python -X utf8 strumenti/prosa.py esporta <racconto>           (fase 2)

<racconto> è il nome della cartella in racconti/ oppure un percorso.
Le fonti delle regole sono in officina/fonti.md.
"""

import datetime
import difflib
import hashlib
import json
import math
import os
import re
import statistics
import sys
import tempfile
import time
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

RADICE = Path(__file__).resolve().parent.parent
RACCONTI = RADICE / "racconti"
MODELLO = RACCONTI / "_modello"

LETTERE = "A-Za-zÀ-ÖØ-öø-ÿ"
RE_PAROLA = re.compile(rf"[{LETTERE}]+")
RE_STACCO = re.compile(r"^[ \t]*\*(?:[ \t]*\*){2,}[ \t]*$")
RE_TITOLO = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+(.*)$")
RE_SEPARATORE = re.compile(r"(?:" + RE_STACCO.pattern + "|" + RE_TITOLO.pattern + ")")
CONVENZIONE_BATTUTE = (
    "Battute locali: caratteri Unicode del testo visibile normalizzato NFC, spazi inclusi; "
    "a capo e separatori strutturali esclusi. Tabulazioni e spazi non separabili "
    "diventano spazi ordinari; gli altri spazi, anche doppi, restano contati."
)

# Parole funzionali, escluse da echi e ricorrenze.
STOPWORDS = set("""
a ad al allo alla ai agli alle anche ancora avere aveva avevo avevano abbiamo ho hai ha hanno
c ce ci che chi cioè come con col coi contro cosa così cui da dal dallo dalla dai dagli dalle
del dello della dei degli delle di dopo dove dunque e ed è era ero erano essere fa fare fatto
fino fra fu già gli ha i il in invece io l la le lei li lo loro lui ma me mentre mi mia mie
miei mio molto ne né nei nel nello nella negli nelle no noi non nostro nostra o od ogni ora
per perché però più poi prima proprio qual quale quando quanto quel quello quella quelli
quelle questo questa questi queste qui se sé sei si sia siamo siete sono sta stato stata
su sua sue suo suoi sul sullo sulla sui sugli sulle tra tu tua tue tuo tuoi tutto tutta
tutti tutte un uno una va vi voi volta essere stare fare dire dice detto quasi solo ancora
sempre mai tanto poco po qualcosa qualcuno niente nulla altro altra altri altre stesso stessa
""".split())

# Verbi di percezione e di pensiero che possono fare da filtro (officina/scena.md, [F23]).
FILTRO = [
    r"vid[ei]", r"vedo", r"vedeva", r"vedevo", r"sent[ìi]", r"sento", r"sentiva", r"sentivo",
    r"ud[ìi]", r"odo", r"not[òo]", r"notava", r"notavo", r"osserv[òo]", r"osservava",
    r"pens[òo]", r"pensava", r"pensavo", r"cap[ìi]", r"capisco", r"capiva", r"sapeva", r"sapevo",
    r"sembr[òo]", r"sembrava", r"sembra", r"percep[ìi]", r"percepisco", r"percepiva",
    r"si accorse", r"mi accorgo", r"mi accorsi", r"si accorge", r"si chiese", r"mi chiedo",
    r"mi chiesi", r"si rese conto", r"mi rendo conto",
]
RE_FILTRO = re.compile(r"\b(" + "|".join(FILTRO) + r")\b", re.IGNORECASE)

# Verbi dichiarativi enfatici (officina/difetti-ai.md, parte 3).
DICHIARATIVI = [
    "sussurr", "sibil", "ringhi", "sbott", "ribatt", "esclam", "mormor", "sogghign",
    "borbott", "grugn", "strill", "tuon", "sospir",
]
RE_DICHIARATIVI = re.compile(
    r"\b(" + "|".join(DICHIARATIVI) + r")(ò|ó|a|ava|ai|avo|ando|é|e|eva|endo)\b", re.IGNORECASE
)

# Formule di repertorio (officina/difetti-ai.md, parte 3: osservazione, non fonte).
STILEMI = [
    r"non raggiungeva gli occhi", r"che non sapev[ao] di trattenere", r"qualcosa dentro di (lui|lei|me) si (ruppe|spezzò)",
    r"brivid[oi] lungo la schiena", r"brivido le percorse", r"brivido gli percorse",
    r"(il )?cuore (che )?batteva all'impazzata", r"cuore (che )?batteva all’impazzata",
    r"nodo alla gola", r"stomaco (che )?si contorce", r"silenzio assordante", r"aria (era )?carica di",
    r"come se il tempo si fosse fermato", r"il peso del mondo", r"in quel momento capì",
    r"per la prima volta (in vita sua|capì)", r"non (è|era) solo\b[^.]{0,80}\b(ma|era|è)\b", r"non solo\b[^.]{0,80}\bma\b",
]

# Tratti dell'italiano generato misurati da `confronta` (officina/difetti-ai.md, parte 1).
# Connettivi di raccordo saggistico [F33]. «quindi», «invece» e «comunque» sono anche connettivi
# del parlato e del periodo per aggiunte: si contano a parte, senza segnale.
CONNETTIVI = [
    "inoltre", "tuttavia", "pertanto", "dunque", "infatti",
    "in questo modo", "in particolare", "allo stesso tempo", "d'altra parte", "d’altra parte",
]
CONNETTIVI_DESCRITTIVI = ["quindi", "invece", "comunque"]
RE_GERUNDIO_CODA = re.compile(
    r",\s*(permettendo|contribuendo|rendendo|consentendo|offrendo|creando|lasciando|facendo)\b", re.IGNORECASE
)

# Refusi di norma (officina/norme-redazionali.md).
REFUSI = [
    (r"\b(perch|poich|bench|affinch|finch|sicch|nonch)è\b", "accento grave dove va acuto: -ché [F9]"),
    (r"\bnè\b", "«nè»: si scrive «né» [F9]"),
    (r"\bpò\b|\bpó\b", "«po'» vuole l'apostrofo, non l'accento [F9]"),
    (r"\bqual['’]è\b", "«qual è» senza apostrofo [F11]"),
    (r"(^|[.!?…»]\s+|\n)E['’]\s", "«E'» a inizio frase: si scrive «È» [F10]"),
    (r"(?<![\d.])\.{2}(?![\d.])|(?<![\d.])\.{4,}(?!\d)", "puntini di sospensione: sempre tre [F7]"),
    (r"\s+[,.;:](?!\.)", "spazio prima della punteggiatura"),
    (r"[^\s\n]  +[^\s\n]", "doppio spazio tra parole"),
    (r"(^|\s)”(?=\w)", "virgoletta di chiusura ” usata in apertura"),
    (r"(?<=\w)“(?=[\s.,;:!?]|$)", "virgoletta di apertura “ usata in chiusura"),
]

# Virgola tra il verbo e la sua oggettiva: norma della raccolta, segnalata come candidato
# (officina/punteggiatura-e-ritmo.md, [F42][F7]). L'elenco dei verbi è dell'officina.
VERBI_OGGETTIVA = (
    r"capit[oaie]|capisco|capiva|capivo|cap[ìi]|so|sai|sa|sapevo|sapeva|seppi|seppe|"
    r"penso|pensa|pensavo|pensava|pensato|pens[òo]|pensai|credo|crede|credevo|credeva|creduto|"
    r"dico|dice|dicevo|diceva|detto|dissi|disse|spero|spera|speravo|sperava|"
    r"ammetto|ammette|ammesso|immagino|immagina|immaginavo|immaginato|scoperto|scoperta|"
    r"accorto|accorta|ricordo|ricorda|ricordavo|temo|temevo|direi|sembra|sembrava|pare|pareva"
)
# Con la ripresa del pronome («lo so, che…», «l'ho capito, che…») la virgola segna una
# dislocazione a destra dell'uso medio [F49], non la virgola nel nucleo: si esclude.
RIPRESA = "".join(rf"(?<!{r})" for r in (
    r"\blo ", r"\bl['’]", r"\bl['’]ho ", r"\bl['’]ha ", r"\bl['’]hai ", r"\bl['’]avevo ", r"\bl['’]aveva ",
))
RE_VIRGOLA_OGGETTIVA = re.compile(RIPRESA + r"\b(?:" + VERBI_OGGETTIVA + r"),[ \t]+che\b", re.IGNORECASE)
REFUSI += [
    (RE_VIRGOLA_OGGETTIVA.pattern,
     "candidato: virgola tra il verbo e la sua oggettiva [F42][F7]"),
    (r"(?:\\?[!?]){2,}", "segni doppi (!!, ?!): enfasi da usare con misura [F44]"),
]

# Antilingua e burocratese nella narrazione (officina/lessico-e-figure.md: Calvino [F53],
# elenco di osservazione). Nelle battute possono caratterizzare chi parla: non si cercano.
ANTILINGUA = [
    r"effettu(?:are|ato|ata|ati|ate|ava|avo|ò|ai|ando|a|o)",
    r"proced(?:ere|uto|eva|evo|o|e|ette|etti) (?:al|allo|alla|all['’]|ai|agli|alle)",
    r"provved(?:ere|uto|eva|evo|o|e|ette|etti) (?:a|al|allo|alla|all['’]|ai|agli|alle)",
    r"nel momento in cui", r"a livello (?:di|del|dello|della|dei|degli|delle)",
    r"in merito (?:a|al|allo|alla|ai|agli|alle)", r"al fine di", r"in ordine (?:a|al|alla)",
    r"risulta(?:va|to|ta|no|vano)? essere", r"(?:il|lo|la|i|gli|le) medesim[oaie]",
    r"suddett[oaie]", r"espleta\w*", r"usufru\w*", r"in data (?:odierna|di)",
    r"nella fattispecie", r"onde (?:evitare|poter|permettere|consentire)",
]
RE_ANTILINGUA = re.compile(r"\b(?:" + "|".join(ANTILINGUA) + r")\b", re.IGNORECASE)
RE_PIUTTOSTO_CHE = re.compile(r"\bpiuttosto che\b", re.IGNORECASE)

# Similitudini esplicite: si segnalano solo gli accumuli (officina/lessico-e-figure.md).
RE_SIMILITUDINE = re.compile(
    r"\bcome se\b|\bcome (?:un|uno|una|il|lo|la|i|gli|le)\b|\bcome (?:un|l)['’]|"
    r"\bsimil[ei] a\b|\b(?:sembra|sembrava|sembravano|pare|pareva) (?:un|uno|una)\b|"
    r"\b(?:sembra|sembrava|pare|pareva) un['’]",
    re.IGNORECASE,
)
RE_COME = re.compile(r"\bcome\b", re.IGNORECASE)
SIMILITUDINI_CAPOVERSO = (3, 120)  # tre similitudini entro 120 parole dello stesso capoverso

# Ritmo locale (officina/punteggiatura-e-ritmo.md): soglie euristiche dell'officina.
UNIFORMI_FRASI = 6       # frasi consecutive di narrazione...
UNIFORMI_SCARTO = 4      # ...la cui lunghezza resta entro questo scarto in parole
ATTACCHI_MINIMO = 3      # frasi consecutive di narrazione con la stessa prima parola
ARTICOLI = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "l"}

# Terne «parola, parola e parola»: segnale di parte 1 di officina/difetti-ai.md.
RE_TERNA = re.compile(rf"\b[{LETTERE}]+, [{LETTERE}]+ e [{LETTERE}]+\b")


# --------------------------------------------------------------------------- utilità

def errore(msg):
    print(f"Errore: {msg}", file=sys.stderr)
    sys.exit(1)


def cartella_racconto(arg):
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    q = RACCONTI / arg
    if q.is_dir():
        return q
    errore(f"racconto non trovato: {arg} (cerco in {RACCONTI})")


def nomi_univoci(cartella, nome):
    """Il primo nome, poi -02, -03... prima dell'estensione."""
    base = Path(nome)
    numero = 1
    while True:
        suffisso = "" if numero == 1 else f"-{numero:02d}"
        yield cartella / f"{base.stem}{suffisso}{base.suffix}"
        numero += 1


def nome_libero(cartella, nome):
    """Il primo percorso che salva_univoco userebbe adesso; non crea niente."""
    return next(p for p in nomi_univoci(cartella, nome) if not p.exists())


def salva_univoco(cartella, nome, contenuto):
    """Mantiene il primo nome e crea -02, -03... senza sovrascrivere."""
    cartella.mkdir(parents=True, exist_ok=True)
    for destinazione in nomi_univoci(cartella, nome):
        try:
            with destinazione.open("x", encoding="utf-8", newline="\n") as file:
                file.write(contenuto)
            return destinazione
        except FileExistsError:
            continue


RIPROVE = 3
PAUSA = 0.5


CONSERVATA = "La versione precedente è conservata."
SCENE_INCOMPLETE = "Le scene possono essere incomplete; testo.md è aggiornato: rieseguire dividi."


def riprova(azione, destinazione, conseguenza=CONSERVATA):
    """Esegue azione; tollera i blocchi brevi della sincronizzazione (OneDrive)."""
    for tentativo in range(RIPROVE + 1):
        try:
            return azione()
        except PermissionError as exc:
            if tentativo == RIPROVE:
                errore(f"{relativo(destinazione)} non aggiornato: file bloccato, forse dalla "
                       f"sincronizzazione di OneDrive ({exc}). {conseguenza} Riprovare tra poco.")
            time.sleep(PAUSA)


def sostituisci(temporaneo, destinazione, conseguenza=CONSERVATA):
    """Pubblica un file temporaneo al posto della destinazione."""
    riprova(lambda: os.replace(temporaneo, destinazione), destinazione, conseguenza)


def togli(percorso, conseguenza=CONSERVATA):
    riprova(lambda: percorso.unlink(missing_ok=True), percorso, conseguenza)


def pubblica(destinazione, contenuto, conseguenza=CONSERVATA):
    """Scrive i byte in un temporaneo accanto alla destinazione, poi lo sostituisce in un colpo solo."""
    temporaneo = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=destinazione.parent, delete=False) as f:
            temporaneo = Path(f.name)
            f.write(contenuto)
        sostituisci(temporaneo, destinazione, conseguenza)
    finally:
        if temporaneo is not None and temporaneo.exists():
            try:
                temporaneo.unlink()
            except OSError:
                pass


def relativo(percorso):
    try:
        return percorso.resolve().relative_to(RADICE.resolve()).as_posix()
    except ValueError:
        return str(percorso)


def identita_report(cartella, dati, revisione=None):
    """Identifica la copia usata, senza spacciare i metadati per acquisizione fresca."""
    copia = cartella / "testo.md"
    impronta = hashlib.sha256(copia.read_bytes()).hexdigest()
    fonte = dati.get("doc") or dati.get("fonte_file") or "non indicata nella scheda"
    if revisione:
        riga_revisione = (f"- Revisione Docs della copia: `{revisione}`, acquisita insieme al testo "
                          "(dichiarata da chi ha acquisito, non verificata dallo script).\n")
    else:
        riga_revisione = ("- Revisione Docs della copia: non disponibile allo script; "
                          "annotarla se verificata durante l'acquisizione.\n")
    return (f"- Generato: {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}\n"
            f"- Fonte dichiarata: {fonte}\n"
            f"- SHA-256 di testo.md: `{impronta}`\n"
            + riga_revisione +
            "- La fonte dichiarata non certifica che la copia coincida con la versione online corrente.\n")


def separa_metadato(valore, separatore):
    """Sottoinsieme locale: virgolette semplici, commenti e liste su una riga."""
    parti, corrente, quota = [], [], None
    for i, c in enumerate(valore):
        if quota:
            corrente.append(c)
            if c == quota:
                quota = None
        elif c in "\"'" and (not "".join(corrente).strip() or
                                   "".join(corrente).rstrip().endswith(("[", ","))):
            quota = c
            corrente.append(c)
        elif c == separatore and (c != "#" or i == 0 or valore[i - 1].isspace()):
            parti.append("".join(corrente).strip())
            corrente = []
            if c == "#":
                return parti
        else:
            corrente.append(c)
    if quota:
        errore("virgolette non chiuse nell'intestazione della scheda")
    return parti + ["".join(corrente).strip()]


def scalare_scheda(valore):
    if valore.startswith(('"', "'")):
        if len(valore) < 2 or valore[-1] != valore[0] or valore[0] in valore[1:-1]:
            errore("valore tra virgolette non supportato nella scheda")
        return valore[1:-1]
    if valore.startswith(("[", "{", "|", ">", "&", "*", "!")):
        errore("forma di metadato non supportata: usare un valore semplice su una riga")
    return valore


def leggi_scheda(cartella, campi=None):
    """Legge solo l'intestazione semplice; campi limita anche la validazione."""
    f = cartella / "scheda.md"
    dati = {}
    if not f.exists():
        return dati
    testo = f.read_text(encoding="utf-8-sig")
    m = re.match(r"\A---\n(.*?)\n---(?:\n|$)", testo, re.S)
    if not m:
        errore("intestazione della scheda assente o non supportata")
    for riga in m.group(1).splitlines():
        if not riga.strip() or riga.lstrip().startswith("#"):
            continue
        if not re.match(r"^[a-z_]+:", riga):
            errore("intestazione non supportata: usare chiave: valore su una riga")
        k, v = riga.split(":", 1)
        if campi is not None and k not in campi:
            continue
        if k in dati:
            errore(f"campo duplicato nella scheda: {k}")
        v = separa_metadato(v.strip(), "#")[0]
        if k == "ricorrenti":
            dati[k] = v
            lista_scheda(dati, k)  # valida anche quando nessun controllo usa la lista
        else:
            dati[k] = scalare_scheda(v)
    if "modalita" in dati and dati["modalita"] not in ("breve", "lunga"):
        errore("modalita non supportata: usare breve o lunga; (dedotto) va nel commento")
    if "scrittura_assistita" in dati:
        dati["scrittura_assistita"] = unicodedata.normalize("NFC", dati["scrittura_assistita"])
        if dati["scrittura_assistita"] not in ("sì", "si", "no", ""):
            errore("scrittura_assistita non supportata: usare sì, si, no o lasciare vuoto; "
                   "le note vanno nel commento")
    if "ia_bando" in dati:
        dati["ia_bando"] = " ".join(unicodedata.normalize("NFC", dati["ia_bando"]).split())
        if dati["ia_bando"] not in ("vietata", "ammessa", "da verificare", ""):
            errore("ia_bando non supportato: usare vietata, ammessa, da verificare o lasciare vuoto; "
                   "le note vanno nel commento")
    return dati


def lista_scheda(dati, chiave):
    v = dati.get(chiave, "")
    if v.startswith("["):
        if not v.endswith("]"):
            errore("lista non chiusa nella scheda")
        v = v[1:-1]
    return [scalare_scheda(x).lower() for x in separa_metadato(v, ",") if x]


def cmd_fonte(racconto):
    dati = leggi_scheda(cartella_racconto(racconto), {"doc", "fonte_file", "modalita"})
    fonte = dati.get("fonte_file", "")
    if fonte:
        percorso = Path(fonte)
        fonte = str((percorso if percorso.is_absolute() else RADICE / percorso).resolve())
    print(json.dumps({"doc": dati.get("doc", ""), "fonte_file": fonte,
                      "modalita": dati.get("modalita", "breve")}, ensure_ascii=False))


def testo_racconto(cartella):
    """La copia completa è autorevole; le scene non sono originali alternativi."""
    f = cartella / "testo.md"
    if not f.exists():
        errore(f"manca {f}. Rigenera la copia dalla fonte con «importa».")
    return [("testo.md", f.read_text(encoding="utf-8-sig"))]


def parole(testo):
    return RE_PAROLA.findall(testo)


def testo_visibile(testo):
    """Sottoinsieme Markdown locale, non un renderer completo. Mantiene gli a capo."""
    if testo.startswith("\ufeff"):
        testo = testo[1:]
    testo = testo.replace("\r\n", "\n").replace("\r", "\n")
    # Nasconde gli escape prima di interpretare marcatori e link. I segnaposto
    # non possono collidere con caratteri già presenti nell'ingresso.
    protetti = {}
    codice = 0xE000

    def proteggi(m):
        nonlocal codice
        while chr(codice) in testo or chr(codice) in protetti:
            codice += 1
        segno = chr(codice)
        protetti[segno] = m.group(1)
        codice += 1
        return segno

    testo = re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])", proteggi, testo)
    righe = []
    for riga in testo.split("\n"):
        if RE_STACCO.fullmatch(riga):
            righe.append("")
            continue
        titolo = RE_TITOLO.fullmatch(riga)
        if titolo:
            riga = re.sub(r"[ \t]+#+[ \t]*$", "", titolo.group(1))
        righe.append(riga)
    testo = "\n".join(righe)
    # Link inline; destinazioni semplici o con un livello di parentesi.
    testo = re.sub(r"\[([^\[\]\n]*)\]\((?:[^()\n]|\([^()\n]*\))*\)", r"\1", testo)
    # Enfasi abbinata, anche annidata, dentro un solo capoverso; underscore interni
    # alle parole letterali.
    for marcatore in ("***", "___", "**", "__", "*", "_"):
        segno = re.escape(marcatore)
        bordo = r"(?<!\w)" if "_" in marcatore else ""
        fine = r"(?!\w)" if "_" in marcatore else ""
        testo = re.sub(bordo + segno + r"(?=\S)((?:(?!\n[ \t]*\n).)+?)(?<=\S)" + segno + fine,
                       r"\1", testo, flags=re.S)
    testo = "".join(protetti.get(c, c) for c in testo)
    return unicodedata.normalize("NFC", testo).translate(
        str.maketrans({"\t": " ", "\u00a0": " ", "\u202f": " "}))


def conta_parole(testo):
    """Stima locale: token separati da spazi con almeno una lettera o cifra Unicode."""
    return sum(any(c.isalnum() for c in t) for t in testo_visibile(testo).split())


def conta_battute(testo):
    return len(testo_visibile(testo).replace("\n", ""))


def frasi(testo):
    t = re.sub(r"\s+", " ", testo)
    pezzi = re.split(r"(?<=[.!?…])[»”\"]?\s+(?=[«“\"—–\-]?\s?[A-ZÀ-Ý])", t)
    return [p for p in pezzi if RE_PAROLA.search(p)]


def togli_dialoghi(testo):
    """Approssima la sola narrazione: via il testo tra caporali, tra virgolette alte e le righe di battuta."""
    t = re.sub(r"«[^»]*»", " ", testo)
    t = re.sub(r"“[^”]*”", " ", t)
    t = re.sub(r'"[^"\n]*"', " ", t)
    righe = [r for r in t.splitlines() if not re.match(r"^\s*(—|–|-)\s?\S", r)]
    return "\n".join(righe)


def maschera_dialoghi(testo):
    """Come togli_dialoghi, ma a lunghezza costante: le posizioni restano quelle del testo."""
    def vuota(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    t = re.sub(r"«[^»]*»", vuota, testo)
    t = re.sub(r"“[^”]*”", vuota, t)
    t = re.sub(r'"[^"\n]*"', vuota, t)
    return re.sub(r"(?m)^[ \t]*(?:—|–|-)[ \t]?\S.*$", vuota, t)


RE_CONFINE_FRASE = re.compile(r"(?<=[.!?…])[»”\"]?\s+(?=[«“\"—–\-]?\s?[A-ZÀ-Ý])")


def frasi_posizionate(testo):
    """Frasi con la posizione d'inizio nel testo; stessi confini di frasi()."""
    out, inizio = [], 0
    for m in RE_CONFINE_FRASE.finditer(testo):
        out.append((inizio, testo[inizio:m.start()]))
        inizio = m.end()
    out.append((inizio, testo[inizio:]))
    return [(p, f) for p, f in out if RE_PAROLA.search(f)]


def di_dialogo(frase):
    return bool(re.search(r"[«“\"]", frase) or re.match(r"\s*[—–-]", frase))


def ritmo_locale(testo):
    """Tratti di narrazione a lunghezza uniforme e attacchi di frase ripetuti."""
    fr = frasi_posizionate(testo)
    uniformi, attacchi = [], []
    # Le frasi di dialogo interrompono le serie: le battute brevi in fila sono normali.
    serie, corrente = [], []
    for p, f in fr:
        if di_dialogo(f):
            if corrente:
                serie.append(corrente)
            corrente = []
        else:
            corrente.append((p, f))
    if corrente:
        serie.append(corrente)
    for s in serie:
        lung = [len(parole(f)) for _, f in s]
        i = 0
        while i + UNIFORMI_FRASI <= len(s):
            finestra = lung[i:i + UNIFORMI_FRASI]
            if max(finestra) - min(finestra) <= UNIFORMI_SCARTO:
                j = i + UNIFORMI_FRASI
                while j < len(s) and max(lung[i:j + 1]) - min(lung[i:j + 1]) <= UNIFORMI_SCARTO:
                    j += 1
                uniformi.append((s[i][0], j - i, min(lung[i:j]), max(lung[i:j])))
                i = j
            else:
                i += 1
        prime = [parole(f)[0].lower() for _, f in s]
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and prime[j + 1] == prime[i]:
                j += 1
            if j - i + 1 >= ATTACCHI_MINIMO and prime[i] not in ARTICOLI:
                attacchi.append((s[i][0], parole(s[i][1])[0], j - i + 1))
            i = j + 1
    return uniformi, attacchi


def accumuli_similitudini(testo):
    """Similitudini esplicite: totale e luoghi in cui si accumulano."""
    totale = len(RE_SIMILITUDINE.findall(testo))
    luoghi = []
    for p, f in frasi_posizionate(testo):
        trovate = [m.group(0) for m in RE_SIMILITUDINE.finditer(f)]
        if len(trovate) >= 2:
            luoghi.append((p, "nella stessa frase", trovate))
    quante, entro = SIMILITUDINI_CAPOVERSO
    cursore = 0
    for blocco in capoversi(testo):
        inizio = testo.find(blocco, cursore)
        cursore = inizio + len(blocco)
        trovate = [(len(parole(blocco[:m.start()])), m) for m in RE_SIMILITUDINE.finditer(blocco)]
        i = 0
        while i + quante <= len(trovate):
            if trovate[i + quante - 1][0] - trovate[i][0] <= entro:
                j = i + quante
                while j < len(trovate) and trovate[j][0] - trovate[i][0] <= entro:
                    j += 1
                gruppo = trovate[i:j]
                pos = inizio + gruppo[0][1].start()
                luoghi.append((pos, f"{len(gruppo)} entro {entro} parole dello stesso capoverso",
                               [m.group(0) for _, m in gruppo]))
                i = j
            else:
                i += 1
    return totale, sorted(luoghi)


def per_mille(n, tot):
    return round(n * 1000 / tot, 1) if tot else 0.0


def statistiche_ritmo(testo):
    lung = [len(parole(f)) for f in frasi(testo)]
    if not lung:
        return {"frasi": 0, "media": 0, "dev": 0, "max": 0, "brevi": 0}
    return {
        "frasi": len(lung),
        "media": round(statistics.mean(lung), 1),
        "dev": round(statistics.pstdev(lung), 1),
        "max": max(lung),
        "brevi": sum(1 for x in lung if x <= 4),
    }


def radice(parola):
    return parola.lower()[:6]


def stilemi():
    lista = list(STILEMI)
    extra = RADICE / "strumenti" / "stilemi_extra.txt"
    if extra.exists():
        for numero, riga in enumerate(extra.read_text(encoding="utf-8-sig").splitlines(), 1):
            pat = riga.strip()
            if not pat or pat.startswith("#"):
                continue
            try:
                re.compile(pat)
            except re.error as exc:
                errore(f"regex non valida in {extra}, riga {numero}: {exc}")
            lista.append(pat)
    return lista


def riga_di(testo, pos):
    return testo.count("\n", 0, pos) + 1


def estratto(testo, pos, largo=45):
    a = max(0, pos - largo)
    b = min(len(testo), pos + largo)
    return "…" + re.sub(r"\s+", " ", testo[a:b]).strip() + "…"


def oggi():
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------- comandi

def cmd_nuovo(nome):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nome):
        errore("il nome deve essere in minuscolo, con trattini: es. il-faro")
    dest = RACCONTI / nome
    if dest.exists():
        errore(f"esiste già: {dest}")
    dest.mkdir(parents=True)
    for sotto in ("materiali", "revisioni", "letture"):
        (dest / sotto).mkdir()
        (dest / sotto / ".gitkeep").write_text("", encoding="utf-8")
    for f in ("scheda.md", "stato.md"):
        testo = (MODELLO / f).read_text(encoding="utf-8-sig")
        testo = testo.replace("{{nome}}", nome).replace("{{data}}", oggi())
        with (dest / f).open("w", encoding="utf-8", newline="\n") as uscita:
            uscita.write(testo)
    print(f"Creato racconti/{nome}/ con scheda.md, stato.md, materiali/, revisioni/, letture/")


def leggi_docx(percorso):
    with zipfile.ZipFile(percorso) as z:
        xml = z.read("word/document.xml")
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    radice_xml = ElementTree.fromstring(xml)
    corpo = radice_xml.find(w + "body")
    if corpo is None:
        raise ValueError("DOCX senza corpo Word supportato")
    # I contenitori complessi sono visibili come limite, non come fedeltà garantita.
    supportati = {"document", "body", "p", "r", "rPr", "i", "t", "tab", "br", "cr",
                  "pPr", "sectPr", "pgSz", "pgMar", "cols", "docGrid", "proofErr",
                  "bookmarkStart", "bookmarkEnd", "lang", "rsid", "lastRenderedPageBreak"}
    limiti = sorted({e.tag.rsplit("}", 1)[-1] for e in radice_xml.iter()
                     if e.tag.rsplit("}", 1)[-1] not in supportati})
    print("DOCX: supportati testo, corsivo diretto dei run, tabulazioni e a capo. "
          "Stili ereditati, impaginazione e altre parti del pacchetto non sono riprodotti.", file=sys.stderr)
    if limiti:
        print("Attenzione: strutture/formati DOCX non supportati pienamente: " +
              ", ".join(limiti) + ". Verificare la copia prima di lavorarci.", file=sys.stderr)
    paragrafi = []
    for p in corpo.iter(w + "p"):
        gruppi = []
        # I run del paragrafo, anche in hyperlink, ma non quelli di paragrafi annidati.
        def run(elemento):
            for figlio in elemento:
                if figlio.tag == w + "r":
                    yield figlio
                elif figlio.tag != w + "p":
                    yield from run(figlio)

        for r in run(p):
            i = r.find(w + "rPr/" + w + "i")
            corsivo = i is not None and i.get(w + "val", "true").lower() not in ("0", "false", "off")
            pezzi = []
            for elemento in r:
                if elemento.tag == w + "t":
                    pezzi.append(elemento.text or "")
                elif elemento.tag == w + "tab":
                    pezzi.append("\t")
                elif elemento.tag in (w + "br", w + "cr"):
                    pezzi.append("\n")
            testo = "".join(pezzi)
            if gruppi and gruppi[-1][0] == corsivo:
                gruppi[-1][1] += testo
            else:
                gruppi.append([corsivo, testo])
        grezzo = "".join(testo for _, testo in gruppi)
        if RE_STACCO.fullmatch(grezzo):
            # Un capoverso fatto solo di asterischi è uno stacco di scena, non testo letterale.
            paragrafi.append(grezzo)
            continue
        pezzi = []
        for corsivo, testo in gruppi:
            testo = escape_letterali(testo)
            if corsivo:
                # Gli spazi esterni e le interruzioni restano fuori dai delimitatori.
                testo = re.sub(r"[^\s](?:[^\n]*[^\s])?", lambda m: "*" + m[0] + "*", testo)
            pezzi.append(testo)
        paragrafi.append("".join(pezzi))
    return "\n\n".join(paragrafi)


def escape_letterali(testo):
    """TXT e run Word sono testo letterale, non sorgenti Markdown."""
    return re.sub(r"([\\*_#\[\]`])", r"\\\1", testo)


def normalizza(testo):
    # Non consumare escape, tab, spazi o paragrafi vuoti: possono essere letterali.
    if testo.startswith("\ufeff"):
        testo = testo[1:]
    testo = testo.replace("\r\n", "\n").replace("\r", "\n")
    return testo if testo.endswith("\n") else testo + "\n"


ERRORI_FONTE = (OSError, UnicodeError, ValueError, KeyError, RuntimeError,
                zipfile.BadZipFile, ElementTree.ParseError)


def leggi_fonte(file):
    """Legge .docx, .md o .txt come testo.md normalizzato, senza scrivere niente."""
    src = Path(file)
    if src.suffix.lower() == ".docx":
        testo = leggi_docx(src)
    elif src.suffix.lower() in (".md", ".txt"):
        testo = src.read_text(encoding="utf-8-sig")
        if src.suffix.lower() == ".txt":
            # Una riga fatta solo di asterischi è uno stacco di scena, non testo letterale.
            testo = "\n".join(riga if RE_STACCO.fullmatch(riga) else escape_letterali(riga)
                              for riga in testo.split("\n"))
    else:
        raise ValueError("formato non supportato: usare .docx, .md o .txt")
    return normalizza(testo)


def cmd_importa(file, racconto):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    try:
        testo = leggi_fonte(file)
    except ERRORI_FONTE as exc:
        errore(f"importazione non riuscita ({exc}). Copia precedente conservata ma non aggiornata; "
               "fornire il file aggiornato prima di lavorare sul testo.")
    # Pubblicazione atomica, solo dopo estrazione e normalizzazione complete.
    try:
        pubblica(cartella / "testo.md", testo.encode("utf-8"),
                 "La copia precedente è conservata ma non aggiornata.")
    except OSError as exc:
        errore(f"copia non aggiornata: {exc}")
    if dati.get("modalita") == "lunga":
        dividi(cartella, severo=False)
    else:
        for vecchio in (cartella / "scene").glob("*.md"):
            togli(vecchio, SCENE_INCOMPLETE)
    togli(cartella / "testo-unito.md", "testo.md è aggiornato; non usare testo-unito.md.")
    for vecchia in (cartella / "tappe").glob("*.md"):
        togli(vecchia, "testo.md è aggiornato; le tappe rimaste sono obsolete: rieseguire tappe.")
    dest = cartella / "testo.md"
    try:
        dest = dest.relative_to(RADICE)
    except ValueError:
        pass
    print(f"Scritto {dest}: {conta_parole(testo)} parole (stima), {conta_battute(testo)} battute")
    print(CONVENZIONE_BATTUTE)
    # Ultima: se fallisce, testo.md e i derivati sono già coerenti.
    conserva_copia(cartella, testo.encode("utf-8"))


# Le prime 16 cifre esadecimali (64 bit) bastano a distinguere le versioni di un racconto
# e sono quelle che i report riportano per intero o in parte; meno sarebbero ambigue.
CIFRE_COPIA = 16


def percorso_copia(cartella, impronta):
    return cartella / "copie" / f"{impronta[:CIFRE_COPIA]}.md"


def conserva_copia(cartella, contenuto):
    """Conserva la copia pubblicata per «differenze»; una copia identica non si riscrive."""
    impronta = hashlib.sha256(contenuto).hexdigest()
    dest = percorso_copia(cartella, impronta)
    if dest.is_file() and hashlib.sha256(dest.read_bytes()).hexdigest() == impronta:
        print(f"Copia per le differenze già presente: copie/{dest.name}")
        return
    try:
        dest.parent.mkdir(exist_ok=True)
        pubblica(dest, contenuto, "testo.md è aggiornato; senza questa copia «differenze» "
                 "non potrà partire da questa versione. Rieseguire importa.")
    except OSError as exc:
        errore(f"copia per le differenze non salvata ({exc}). testo.md è aggiornato; "
               "rieseguire importa per conservarla.")
    print(f"Copia per le differenze conservata: copie/{dest.name}")


def cmd_intestazione(racconto, revisione=None):
    cartella = cartella_racconto(racconto)
    testo_racconto(cartella)  # senza copia non c'è impronta da dichiarare
    dati = leggi_scheda(cartella, {"doc", "fonte_file"})
    print(identita_report(cartella, dati, revisione), end="")
    marcati = materiali_marcati(cartella)
    if marcati:
        m = misura_provenienza(cartella, marcati)
        if m["coincidenti"]:
            print(f"- Provenienza: {percentuale(m['coincidenti'], m['totale'])} delle parole coincide con "
                  f"{len(marcati)} materiali marcati dell'assistente (prosa.py provenienza). "
                  + AVVERTENZA_PROVENIENZA)


def cmd_nome_libero(percorso):
    p = Path(percorso)
    if not p.name or not p.suffix:
        errore(f"serve un percorso con nome ed estensione, es. racconti/<nome>/revisioni/{oggi()}-strutturale.md")
    if not p.parent.is_dir():
        print(f"Attenzione: la cartella {p.parent.as_posix()} non esiste ancora; "
              "controllare il nome del racconto.", file=sys.stderr)
    print(nome_libero(p.parent, p.name).as_posix())


def cmd_conta(racconto):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    pezzi = testo_racconto(cartella)
    testo = pezzi[0][1]
    tot_p, tot_b = conta_parole(testo), conta_battute(testo)
    print(f"# Conteggi: {cartella.name}\n")
    print("| Parte | Parole | Battute (spazi inclusi) |")
    print("| --- | ---: | ---: |")
    print(f"| testo.md | {tot_p} | {tot_b} |")
    print()
    print(CONVENZIONE_BATTUTE)
    print("Parole: stima locale dei token separati da spazi con almeno una lettera o cifra Unicode.")
    print("Prima dell'invio verifica il documento finale nello strumento e secondo i criteri "
          "del bando. Non è verificata l'equivalenza con Google Docs.\n")
    modalita = "lunga" if tot_p > 6000 else "breve"
    print(f"Modalità suggerita: **{modalita}** (soglia indicativa 6.000 parole). In scheda: {dati.get('modalita', 'non impostata')}.")
    for chiave, valore, unita in (("limite_battute", tot_b, "battute"), ("parole_obiettivo", tot_p, "parole")):
        lim = re.sub(r"\D", "", dati.get(chiave, ""))
        if lim:
            diff = int(lim) - valore
            stato = f"mancano {diff}" if diff >= 0 else f"**oltre di {-diff}**"
            print(f"{chiave}: {lim} {unita}; {stato} (convenzione locale).")


def controlli(testo, dati):
    """Restituisce un dizionario di risultati dei controlli su un testo."""
    ris = {}
    tutte = parole(testo)
    n = len(tutte)
    narr = togli_dialoghi(testo)
    n_narr = len(parole(narr)) or 1
    ris["parole"] = conta_parole(testo)
    ris["ritmo"] = statistiche_ritmo(testo)

    mente = [w for w in parole(narr) if w.lower().endswith("mente") and len(w) > 7
             and w.lower() not in {"demente", "clemente", "veemente", "sementi", "semente"}]
    ris["mente"] = (len(mente), per_mille(len(mente), n_narr), Counter(w.lower() for w in mente).most_common(6))

    filtro = [(m.group(0), m.start()) for m in RE_FILTRO.finditer(narr)]
    ris["filtro"] = (len(filtro), per_mille(len(filtro), n_narr), Counter(f[0].lower() for f in filtro).most_common(8))

    dich = [(m.group(0), m.start()) for m in RE_DICHIARATIVI.finditer(testo)]
    ris["dichiarativi"] = dich

    scelte = {w.casefold() for w in lista_scheda(dati, "ricorrenti")}
    radici_scelte = {radice(w) for w in scelte}
    minuscole = [w.lower() for w in tutte]
    contenuto = [w for w in minuscole if len(w) >= 4 and w not in STOPWORDS]
    freq = Counter(contenuto)
    ris["ricorrenti"] = [(w, c, per_mille(c, n), w in scelte) for w, c in freq.most_common(12)]

    # Echi: stessa radice (6 lettere) entro 30 parole, parole di 5+ lettere, non funzionali, non scelte.
    echi = Counter()
    esempi_echi = {}
    ultima = {}
    for i, w in enumerate(tutte):
        wl = w.lower()
        if len(wl) < 5 or wl in STOPWORDS or radice(wl) in radici_scelte or w[0].isupper():
            continue
        r = radice(wl)
        if r in ultima and i - ultima[r] <= 30:
            echi[r] += 1
            esempi_echi.setdefault(r, wl)
        ultima[r] = i
    ris["echi"] = [(esempi_echi[r], c) for r, c in echi.most_common(10)]

    # Sequenze di 4 parole ripetute (almeno una parola non funzionale).
    ngr = Counter()
    for i in range(len(minuscole) - 3):
        g = tuple(minuscole[i:i + 4])
        if any(x not in STOPWORDS for x in g):
            ngr[g] += 1
    ris["sequenze"] = [(" ".join(g), c) for g, c in ngr.most_common(10) if c >= 3]

    stil = []
    for pat in stilemi():
        for m in re.finditer(pat, testo, re.IGNORECASE):
            stil.append((m.group(0), riga_di(testo, m.start()), estratto(testo, m.start())))
    ris["stilemi"] = stil

    ref = []
    for pat, spiegazione in REFUSI:
        flag = re.MULTILINE if "E['’]" in pat else re.MULTILINE | re.IGNORECASE
        for m in re.finditer(pat, testo, flag):
            ref.append((spiegazione, riga_di(testo, m.start()), estratto(testo, m.start(), 30)))
    apos = (testo.count("'"), testo.count("’"))
    if apos[0] and apos[1]:
        ref.append((f"apostrofi misti: {apos[0]} dritti e {apos[1]} tipografici", 0, ""))
    ris["refusi"] = ref

    # Nomi propri candidati: parole maiuscole non a inizio frase, ripetute.
    candidati = Counter()
    minuscole_set = set(w for w in tutte if w[0].islower())
    for f in frasi(testo):
        ps = parole(f)
        for w in ps[1:]:
            if w[0].isupper() and w.lower() not in STOPWORDS and w.lower() not in minuscole_set:
                candidati[w] += 1
    nomi = [w for w, c in candidati.items() if c >= 2 and len(w) >= 3]
    simili = []
    for i, a in enumerate(nomi):
        for b in nomi[i + 1:]:
            if a != b and (a[:3].lower() == b[:3].lower() or distanza(a.lower(), b.lower()) <= 1):
                simili.append((a, b))
    ris["nomi_simili"] = simili

    ris["dialoghi"] = conta_convenzioni(testo)

    # Controlli di lingua (officina/punteggiatura-e-ritmo.md, officina/lessico-e-figure.md),
    # sul testo visibile: stessi a capo del file, quindi stessi numeri di riga.
    vis = testo_visibile(testo)
    blocchi = [conta_parole(b) for b in capoversi(vis) if parole(b)]
    ris["capoversi"] = (len(blocchi), round(statistics.mean(blocchi), 1) if blocchi else 0,
                        max(blocchi, default=0))
    uniformi, attacchi = ritmo_locale(vis)
    ris["uniformi"] = [(riga_di(vis, p), n, a, b, estratto(vis, p + 40)) for p, n, a, b in uniformi]
    ris["attacchi"] = [(riga_di(vis, p), w, n, estratto(vis, p + 40)) for p, w, n in attacchi]
    narr_vis = maschera_dialoghi(vis)
    lessico = [(m.group(0), riga_di(vis, m.start()), estratto(vis, m.start()), "antilingua")
               for m in RE_ANTILINGUA.finditer(narr_vis)]
    lessico += [(m.group(0), riga_di(vis, m.start()), estratto(vis, m.start()), "piuttosto che")
                for m in RE_PIUTTOSTO_CHE.finditer(narr_vis)]
    ris["lessico"] = sorted(lessico, key=lambda x: x[1])
    totale, luoghi = accumuli_similitudini(vis)
    ris["similitudini"] = (totale, [(riga_di(vis, p), dove, trovate, estratto(vis, p))
                                    for p, dove, trovate in luoghi])
    return ris


def distanza(a, b):
    if abs(len(a) - len(b)) > 2:
        return 3
    prec = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prec[j] + 1, cur[j - 1] + 1, prec[j - 1] + (ca != cb)))
        prec = cur
    return prec[-1]


def conta_convenzioni(testo):
    aperture_lineette = {m.start(1) for m in re.finditer(r"(?m)^[ \t]*([—–])", testo)}
    aperture_trattini = {m.start(1) for m in re.finditer(r"(?m)^[ \t]*(-)\s?\S", testo)}
    interni_lineette = {m.start() + 1 for m in re.finditer(r"\s[—–]\s", testo)}
    interni_trattini = {m.start() + 1 for m in re.finditer(r"\s-(?=\s?[A-ZÀ-Ý])", testo)}
    return {
        "caporali": testo.count("«"),
        "virgolette alte": testo.count("“") + len(re.findall(r'(^|\s)"', testo)),
        "lineette": len(aperture_lineette | interni_lineette),
        "trattini": len(aperture_trattini | interni_trattini),
    }


def cmd_controlla(racconto, salva=False):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    testo = "\n\n".join(t for _, t in testo_racconto(cartella))
    r = controlli(testo, dati)
    out = []
    w = out.append
    w(f"# Controlli: {cartella.name} ({oggi()})\n")
    w(identita_report(cartella, dati))
    w("Numeri e candidati da verificare, non diagnosi. Divisione in frasi, separazione tra narrazione e dialoghi, filtri e nomi simili sono approssimazioni; possono omettere casi o segnalare usi legittimi. Le fonti delle regole sono in `officina/fonti.md`.\n")
    rt = r["ritmo"]
    w("## Ritmo")
    w(f"- {r['parole']} parole, {rt['frasi']} frasi. Media {rt['media']} parole per frase, deviazione {rt['dev']}, "
      f"la più lunga {rt['max']}, {rt['brevi']} frasi di quattro parole o meno.")
    if rt["frasi"] >= 20 and rt["dev"] < 5:
        w("- **Segnale**: varianza bassa. Le frasi hanno quasi tutte la stessa lunghezza: rischio di prosa piatta.")
    nc, mc, xc = r["capoversi"]
    w(f"- {nc} capoversi, in media {mc} parole, il più lungo {xc}." if nc != 1
      else f"- Un solo capoverso, di {xc} parole.")
    if r["parole"] > 1000 and xc > 0.6 * r["parole"]:
        w("- **Segnale**: un solo capoverso porta più di metà del testo. Se non è una scelta di forma, "
          "il lettore non ha dove riprendere fiato (officina/punteggiatura-e-ritmo.md).")
    w("")
    if r["uniformi"] or r["attacchi"]:
        w("## Ritmo locale (officina/punteggiatura-e-ritmo.md)")
        w("Solo narrazione; le battute interrompono le serie. Candidati: una serie può essere voluta "
          "(un'anafora, un elenco, uno *style coupé*).")
        for riga, n, a, b, est in r["uniformi"]:
            w(f"- riga {riga}: {n} frasi di fila tra {a} e {b} parole · {est}")
        for riga, parola, n, est in r["attacchi"]:
            w(f"- riga {riga}: {n} frasi di fila cominciano con «{parola}» · {est}")
        w("")
    n, pm, top = r["mente"]
    w("## Avverbi in -mente (narrazione)")
    w(f"- {n}, cioè {pm} ogni mille parole. Più frequenti: " + (", ".join(f"{a} ({b})" for a, b in top) or "nessuno"))
    if pm > 10:
        w("- **Segnale**: frequenza alta; spesso un avverbio sostiene un verbo debole.")
    w("")
    n, pm, top = r["filtro"]
    w("## Verbi di percezione e pensiero (possibili filtri, officina/scena.md)")
    w(f"- {n}, cioè {pm} ogni mille parole di narrazione. Più frequenti: " + (", ".join(f"{a} ({b})" for a, b in top) or "nessuno"))
    w("- Conteggio grezzo: include usi legittimi (quando percepire è il punto) e omografi come «noto» aggettivo.")
    w("")
    w("## Dichiarativi enfatici")
    if r["dichiarativi"]:
        w("- " + ", ".join(sorted({d[0].lower() for d in r["dichiarativi"]})) + f" ({len(r['dichiarativi'])} in tutto)")
    else:
        w("- Nessuno.")
    w("")
    w("## Frequenze descrittive (parole di 4+ lettere, non funzionali)")
    w("Queste frequenze descrivono il testo: anche le parole per scelta restano visibili, senza diventare segnalazioni correttive.")
    for parola, c, pmille, scelta in r["ricorrenti"]:
        w(f"- {parola}: {c} ({pmille}‰)" + (" · **per scelta** (scheda)" if scelta else ""))
    w("")
    w("## Echi ravvicinati (stesso prefisso di sei lettere entro 30 parole)")
    w("Confronto di prefissi, non analisi morfologica: può non accostare casa/case. Le ricorrenze dichiarate nella scheda sono escluse.")
    w("- " + (", ".join(f"{a} ({c})" for a, c in r["echi"]) or "Nessuno."))
    w("")
    if r["sequenze"]:
        w("## Sequenze di quattro parole ripetute")
        for s, c in r["sequenze"]:
            w(f"- «{s}» × {c}")
        w("")
    w("## Formule di repertorio (officina/difetti-ai.md, parte 3)")
    if r["stilemi"]:
        for s, riga, est in r["stilemi"]:
            w(f"- riga {riga}: «{s}»: {est}")
    else:
        w("- Nessuna.")
    w("")
    if r["lessico"]:
        w("## Lessico da guardare (narrazione, officina/lessico-e-figure.md)")
        w("Antilingua: parola d'ufficio dove basterebbe quella comune [F53]. «piuttosto che»: "
          "verificare che non stia per «o» [F51]. Nelle battute non si cerca: lì può caratterizzare.")
        for s, riga, est, tipo in r["lessico"]:
            w(f"- riga {riga}: «{s}» ({tipo}) · {est}")
        w("")
    tot, luoghi = r["similitudini"]
    if luoghi:
        w("## Accumuli di similitudini (officina/lessico-e-figure.md)")
        w(f"Similitudini esplicite candidate nel testo: {tot}. Il conteggio non è un segnale: "
          "segnala solo dove si accumulano, e una similitudine può stare per «come» comparativo.")
        for riga, dove, trovate, est in luoghi:
            w(f"- riga {riga}: {dove} (" + ", ".join(f"«{t}»" for t in trovate) + f") · {est}")
        w("")
    w("## Norma e superficie (officina/norme-redazionali.md)")
    if r["refusi"]:
        for spieg, riga, est in r["refusi"]:
            w(f"- {'riga ' + str(riga) + ': ' if riga else ''}{spieg}{' · ' + est if est else ''}")
    else:
        w("- Nessuna segnalazione.")
    w("")
    w("## Dialoghi")
    conv = r["dialoghi"]
    w("- " + ", ".join(f"{k}: {v}" for k, v in conv.items()))
    w("- Conteggio di segni candidati, non di battute né prova di convenzioni miste: incisi e citazioni possono coesistere con il sistema scelto [F4]. Vedi `prosa.py dialoghi` e la scheda.")
    if r["nomi_simili"]:
        w("")
        w("## Nomi simili")
        w("- " + "; ".join(f"{a} / {b}" for a, b in r["nomi_simili"]))
    testo_out = "\n".join(out) + "\n"
    print(testo_out)
    if salva:
        dest = salva_univoco(cartella / "revisioni", f"{oggi()}-controlli.md", testo_out)
        print(f"Salvato in {dest}")


# --------------------------------------------------------------------------- voce misurata
# Misure descrittive della voce, lette contro la variazione dei testi dell'autore
# (officina/stilometria.md). Non attribuiscono un testo e non dicono se è buono.

# Gruppi del profilo numerico: la voce dell'autore, i segnali dell'italiano generato
# discussi in officina/difetti-ai.md (parte 1) e ritmo e punteggiatura.
GRUPPO_RITMO = "Ritmo e punteggiatura"
GRUPPO_VOCE = "Tratti di voce (descrittivi)"
GRUPPO_SEGNALI = "Segnali dell'italiano generato [F32][F33][F34]"

# Pronomi personali e clitici esclusi dalla distanza: dipendono dal punto di vista del
# racconto, non dallo stile (Hoover 2004 [F59]). Non si tolgono gli omografi degli articoli.
PRONOMI = set("""
io tu lui lei noi voi loro egli ella esso essa essi esse me te sé se mi ti ci vi
""".split())

MFW = 100                 # parole più frequenti del riferimento usate dalla distanza
MFW_MINIMO = 3            # occorrenze minime nel riferimento per entrare fra le parole
CULLING = 0.7             # una parola concentrata per oltre il 70% in un solo racconto esce [F59]
CULLING_PAROLE = 500      # il culling vale solo fra racconti di almeno 500 parole di riferimento
MIN_FINESTRE = 8          # sotto questo numero di finestre non si calcola una banda
MIN_CONTRASTO = 5         # finestre minime di contrasto per l'affidabilità
BANDA = (0.05, 0.95)      # la banda: dal 5° al 95° percentile delle finestre dell'autore
SOGLIA_INTERO = 0.9       # racconto che coincide oltre il 90%: escluso dal corpus (vedi corpus_voce)
LUNGHEZZE_AFFIDABILITA = (50, 100, 200, 400, 800)
FINESTRA_DERIVA = 200


def fmt(x, cifre=1):
    return f"{x:.{cifre}f}".replace(".", ",")


def quantile(valori, p):
    """Quantile con interpolazione lineare; valori non vuoti."""
    s = sorted(valori)
    if len(s) == 1:
        return s[0]
    pos = p * (len(s) - 1)
    i = int(pos)
    if i + 1 >= len(s):
        return s[-1]
    return s[i] + (s[i + 1] - s[i]) * (pos - i)


def marcatori_voce():
    """Espressioni di strumenti/marcatori_voce.txt, una per riga; vuoto se il file manca."""
    f = RADICE / "strumenti" / "marcatori_voce.txt"
    lista = []
    if not f.exists():
        return lista
    for numero, riga in enumerate(f.read_text(encoding="utf-8-sig").splitlines(), 1):
        pat = riga.strip()
        if not pat or pat.startswith("#"):
            continue
        try:
            lista.append(re.compile(r"\b(?:" + pat + r")\b", re.IGNORECASE))
        except re.error as exc:
            errore(f"regex non valida in {f}, riga {numero}: {exc}")
    return lista


def conta_marcatori(testo, marcatori):
    return sum(len(m.findall(testo)) for m in marcatori)


def domande_narrazione(testo):
    """Frasi di narrazione che finiscono con un punto interrogativo."""
    return sum(1 for f in frasi(togli_dialoghi(testo)) if re.search(r"\?[»”\"]*\s*$", f))


def profilo_testo(testo, marcatori=None):
    """Profilo numerico di un testo: chiave -> valore. I gruppi sono in GRUPPI_PROFILO."""
    marcatori = marcatori_voce() if marcatori is None else marcatori
    ws = parole(testo)
    n = len(ws) or 1
    lung = [len(parole(f)) for f in frasi(testo)] or [0]
    rt = statistiche_ritmo(testo)
    low = testo.lower()
    narr = togli_dialoghi(testo)
    p = {
        "media frase": rt["media"],
        "deviazione frase": rt["dev"],
        "frase: 10° percentile": round(quantile(lung, 0.1), 1),
        "frase: mediana": round(quantile(lung, 0.5), 1),
        "frase: 90° percentile": round(quantile(lung, 0.9), 1),
        "frasi brevi %": round(100 * rt["brevi"] / rt["frasi"], 1) if rt["frasi"] else 0,
        "virgole ‰": per_mille(testo.count(","), n),
        "due punti ‰": per_mille(testo.count(":"), n),
        "interrogativi ‰": per_mille(testo.count("?"), n),
        "parentesi ‰": per_mille(testo.count("("), n),
        "punto e virgola nella narrazione ‰": per_mille(narr.count(";"), n),
        "esclamativi nella narrazione ‰": per_mille(narr.count("!"), n),
        "puntini nella narrazione ‰": per_mille(narr.count("…") + narr.count("..."), n),
        "lineette nella narrazione ‰": per_mille(len(re.findall(r"\s[—–]\s", narr)), n),
        "lunghezza media parola": round(statistics.mean(len(w) for w in ws), 2) if ws else 0,
        "avverbi -mente ‰": per_mille(sum(1 for w in ws if w.lower().endswith("mente") and len(w) > 7), n),
    }
    if marcatori:
        p["marcatori di voce ‰"] = per_mille(conta_marcatori(testo, marcatori), n)
    p.update({
        "domande nella narrazione ‰": per_mille(domande_narrazione(testo), n),
        "similitudini strette ‰": per_mille(len(RE_SIMILITUDINE.findall(testo)), n),
        "«come» ‰": per_mille(len(RE_COME.findall(testo)), n),
        "gerundi ‰": per_mille(len(re.findall(r"\b\w+(ando|endo)\b", low)), n),
        "quindi, invece, comunque ‰": per_mille(
            sum(len(re.findall(r"\b" + c + r"\b", low)) for c in CONNETTIVI_DESCRITTIVI), n),
        "gerundi in coda ‰": per_mille(len(RE_GERUNDIO_CODA.findall(testo)), n),
        "connettivi di raccordo ‰": per_mille(
            sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in CONNETTIVI), n),
        "terne ‰": per_mille(len(RE_TERNA.findall(testo)), n),
        "«non (è) solo… ma» ‰": per_mille(len(re.findall(r"\bnon (?:è |era )?solo\b[^.]{0,80}\bma\b", low)), n),
    })
    return p


GRUPPI_PROFILO = {
    GRUPPO_VOCE: ("marcatori di voce ‰", "domande nella narrazione ‰", "similitudini strette ‰",
                  "«come» ‰", "gerundi ‰", "quindi, invece, comunque ‰"),
    GRUPPO_SEGNALI: ("gerundi in coda ‰", "connettivi di raccordo ‰", "terne ‰", "«non (è) solo… ma» ‰"),
}


def gruppo_di(chiave):
    for g, chiavi in GRUPPI_PROFILO.items():
        if chiave in chiavi:
            return g
    return GRUPPO_RITMO


# ---- frasi, provenienza e corpus

def frasi_racconto(cartella, materiali=None):
    """Frasi di testo.md con capoverso, stacco e quota di parole coincidenti con i materiali.

    La coincidenza è quella di «provenienza» (sequenze di 8 parole), riportata alla frase.
    """
    testo = testo_racconto(cartella)[0][1]
    materiali = materiali_marcati(cartella) if materiali is None else materiali
    m = misura_provenienza(cartella, materiali) if materiali else None
    blocchi = m["blocchi"] if m else capoversi(testo)
    coperte = m["coperte"] if m else None
    out, k, stacco = [], 0, False
    for i, blocco in enumerate(blocchi):
        norm = parole_normalizzate(blocco)
        flag = [bool(c) for c in coperte[k:k + len(norm)]] if coperte else [False] * len(norm)
        k += len(norm)
        tipo, vis = visibile_capoverso(blocco)
        if tipo == "stacco" or RE_TITOLO.fullmatch(blocco.strip()) or not norm:
            stacco = True
            continue
        pezzi = [f for _, f in frasi_posizionate(vis)]
        conti = [len(parole_normalizzate(f)) for f in pezzi]
        if sum(conti) != len(flag):  # tokenizzazione diversa: si riporta la quota del capoverso
            quota = sum(flag) / len(flag)
            quote = [quota] * len(pezzi)
        else:
            quote, j = [], 0
            for c in conti:
                quote.append(sum(flag[j:j + c]) / c if c else 0.0)
                j += c
        for j, (f, q) in enumerate(zip(pezzi, quote)):
            out.append({"racconto": cartella.name, "indice": len(out), "capoverso": i + 1,
                        "testo": f.strip(), "parole": len(parole(f)), "quota": q,
                        "nuovo_capoverso": j == 0, "stacco_prima": stacco and j == 0})
        stacco = False
    return out


def frasi_da_testo(testo, racconto="testo"):
    """Frasi di un testo semplice, senza provenienza: un solo segmento per capoverso consecutivo."""
    out = []
    for i, blocco in enumerate(capoversi(testo_visibile(testo))):
        for j, (_, f) in enumerate(frasi_posizionate(blocco)):
            out.append({"racconto": racconto, "indice": len(out), "capoverso": i + 1, "testo": f.strip(),
                        "parole": len(parole(f)), "quota": 0.0, "nuovo_capoverso": j == 0,
                        "stacco_prima": False})
    return out


def segmenti(frasi_, tieni):
    """Sequenze di frasi consecutive che soddisfano tieni, spezzate da stacchi e frasi escluse."""
    out, corrente = [], []
    for f in frasi_:
        if f["stacco_prima"] and corrente:
            out.append(corrente)
            corrente = []
        if tieni(f):
            corrente.append(f)
        elif corrente:
            out.append(corrente)
            corrente = []
    if corrente:
        out.append(corrente)
    return out


def unisci_frasi(seq):
    parti = []
    for j, f in enumerate(seq):
        if j:
            parti.append("\n" if f["nuovo_capoverso"] else " ")
        parti.append(f["testo"])
    return "".join(parti)


def testo_segmenti(segs):
    return "\n\n".join(unisci_frasi(s) for s in segs)


def parole_segmenti(segs):
    return sum(f["parole"] for s in segs for f in s)


def sequenze_di(testo, n=None):
    n = n or SEQUENZA_PROVENIENZA
    p = parole_normalizzate(testo)
    return {tuple(p[i:i + n]) for i in range(len(p) - n + 1)}


def coperta_da(frase, sequenze, n=None):
    """Quota delle parole della frase che stanno in una sequenza di n parole presente altrove."""
    n = n or SEQUENZA_PROVENIENZA
    p = parole_normalizzate(frase)
    if not p or not sequenze:
        return 0.0
    coperte = [False] * len(p)
    for i in range(len(p) - n + 1):
        if tuple(p[i:i + n]) in sequenze:
            for j in range(i, i + n):
                coperte[j] = True
    return sum(coperte) / len(p)


def senza(segs, testo):
    """I segmenti senza le frasi che coincidono per metà o più con testo (il passaggio, i brani).

    Con un testo più corto di una sequenza, la sequenza è il testo intero.
    """
    n = min(SEQUENZA_PROVENIENZA, len(parole_normalizzate(testo)))
    if not n:
        return segs
    seq = sequenze_di(testo, n)
    return [s for seg in segs for s in segmenti(seg, lambda f: coperta_da(f["testo"], seq, n) < 0.5)]


def zona_autore(frasi_):
    return segmenti(frasi_, lambda f: f["quota"] == 0)


def zona_contrasto(frasi_):
    return segmenti(frasi_, lambda f: f["quota"] >= 0.5)


def quota_racconto(frasi_):
    tot = sum(f["parole"] for f in frasi_)
    return sum(f["parole"] * f["quota"] for f in frasi_) / tot if tot else 0.0


def racconti_con_testo():
    if not RACCONTI.is_dir():
        return []
    return [c for c in sorted(RACCONTI.iterdir())
            if c.is_dir() and not c.name.startswith("_") and (c / "testo.md").exists()]


def consolidato(cartella):
    return leggi_scheda(cartella, {"stato"}).get("stato") == "consolidato"


def racconti_consolidati():
    return [c for c in racconti_con_testo() if consolidato(c)]


def corpus_voce():
    """Il corpus di voce: racconti consolidati, solo frasi senza coincidenze con i materiali.

    Il contrasto sono le frasi coincidenti per metà o più, di ogni racconto: servono a misurare
    l'affidabilità, mai come riferimento. Un racconto coincidente oltre SOGLIA_INTERO si esclude
    da entrambi: di solito un materiale lo riporta per intero, e la coincidenza non distingue più.
    """
    corpus = {"autore": {}, "contrasto": {}, "esclusi": []}
    for c in racconti_con_testo():
        fr = frasi_racconto(c)
        quota = quota_racconto(fr)
        if quota > SOGLIA_INTERO:
            corpus["esclusi"].append((c.name, f"coincide per il {percentuale(quota, 1)} con i materiali: "
                                      "probabile materiale che riporta il testo intero"))
            continue
        if consolidato(c):
            autore = zona_autore(fr)
            if autore:
                corpus["autore"][c.name] = autore
        contrasto = zona_contrasto(fr)
        if contrasto:
            corpus["contrasto"][c.name] = contrasto
    return corpus


def brani_esempi():
    """Il testo dei brani di voce/esempi.md (sezioni con la riga «- Racconto:»)."""
    f = RADICE / "voce" / "esempi.md"
    if not f.exists():
        return ""
    testo = re.sub(r"(?ms)^```.*?^```[ \t]*$", "", f.read_text(encoding="utf-8-sig"))
    brani = []
    for sezione in re.split(r"(?m)^## ", testo)[1:]:
        righe = sezione.splitlines()[1:]
        piene = [r for r in righe if r.strip()]
        if not piene or not piene[0].lstrip().startswith("- Racconto:"):
            continue
        corpo = "\n".join(righe[righe.index(piene[0]) + 1:]).strip()
        if corpo:
            brani.append(corpo)
    return "\n\n".join(brani)


# ---- finestre, bande e distanza

def finestre(segs, n):
    """Finestre di almeno n parole a frasi intere; partono ogni mezza finestra circa."""
    out = []
    for seg in segs:
        cum = [0]
        for f in seg:
            cum.append(cum[-1] + f["parole"])
        ultimo = None
        for i in range(len(seg)):
            if ultimo is not None and cum[i] - cum[ultimo] < n / 2:
                continue
            j = i
            while j < len(seg) and cum[j] - cum[i] < n:
                j += 1
            if cum[j] - cum[i] < n:
                break
            out.append({"testo": unisci_frasi(seg[i:j]), "parole": cum[j] - cum[i],
                        "chiave": (seg[i]["racconto"], seg[i]["indice"], seg[j - 1]["indice"]),
                        "frasi": seg[i:j]})
            ultimo = i
    return out


def sovrapposte(a, b):
    return a[0] == b[0] and a[1] <= b[2] and b[1] <= a[2]


def banda(valori, x):
    """Posizione di x fra i valori: (etichetta, rango 0-1, 5° percentile, 95° percentile)."""
    if len(valori) < MIN_FINESTRE:
        return ("poche finestre", None, None, None)
    basso, alto = quantile(valori, BANDA[0]), quantile(valori, BANDA[1])
    rango = (sum(1 for v in valori if v < x) + 0.5 * sum(1 for v in valori if v == x)) / len(valori)
    if x > max(valori):
        e = "oltre il massimo osservato"
    elif x < min(valori):
        e = "sotto il minimo osservato"
    elif x > alto:
        e = "oltre il 95° percentile"
    elif x < basso:
        e = "sotto il 5° percentile"
    else:
        e = "dentro"
    return (e, rango, basso, alto)


def fuori(etichetta):
    return etichetta not in ("dentro", "poche finestre")


def scegli_parole(testi_per_racconto, quante=MFW):
    """Parole più frequenti del riferimento, senza pronomi personali e nomi propri, con culling."""
    tot, maiuscole, per = Counter(), Counter(), {}
    for racconto, testo in testi_per_racconto.items():
        c = per.setdefault(racconto, Counter())
        for w in parole(testo):
            lw = w.lower()
            tot[lw] += 1
            c[lw] += 1
            if w[0].isupper():
                maiuscole[lw] += 1
    lunghi = {r: sum(c.values()) for r, c in per.items() if sum(c.values()) >= CULLING_PAROLE}
    scelte = []
    for w, c in tot.most_common():
        if c < MFW_MINIMO or len(scelte) >= quante:
            break
        if w in PRONOMI or maiuscole[w] > c / 2:
            continue
        if len(lunghi) >= 2:
            rel = [per[r][w] / lunghi[r] for r in lunghi]
            if max(rel) > CULLING * sum(rel):
                continue
        scelte.append(w)
    return scelte


def vettore(testo, vocabolario):
    ws = [w.lower() for w in parole(testo)]
    n = len(ws) or 1
    c = Counter(ws)
    return [c[w] / n for w in vocabolario]


def medie_dev(vettori):
    if not vettori:
        return [], []
    k = len(vettori[0])
    media = [sum(v[i] for v in vettori) / len(vettori) for i in range(k)]
    dev = [math.sqrt(sum((v[i] - media[i]) ** 2 for v in vettori) / len(vettori)) for i in range(k)]
    return media, dev


def zeta(v, media, dev):
    return [(x - m) / d if d else 0.0 for x, m, d in zip(v, media, dev)]


def delta(v, media, dev):
    """Delta di Burrows rispetto alle finestre: media degli scarti assoluti in z-score [F58][F59]."""
    z = [abs(x) for x, d in zip(zeta(v, media, dev), dev) if d]
    return sum(z) / len(z) if z else 0.0


def coseno(a, b):
    """Distanza coseno fra due vettori di z-score (Cosine Delta [F60])."""
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    if not na or not nb:
        return 0.0
    return 1 - sum(x * y for x, y in zip(a, b)) / (na * nb)


def statistiche_senza(vettori, chiavi, chiave):
    """Medie e deviazioni delle finestre che non si sovrappongono a chiave."""
    altri = [v for v, c in zip(vettori, chiavi) if not sovrapposte(c, chiave)]
    return medie_dev(altri), len(altri)


class Riferimento:
    """Finestre di riferimento di una lunghezza, con le parole e le distanze delle finestre stesse."""

    def __init__(self, segs, n, vocabolario=None):
        self.n = n
        self.finestre = finestre(segs, n)
        per = {}
        for s in segs:
            per.setdefault(s[0]["racconto"], []).append(unisci_frasi(s))
        self.vocabolario = vocabolario or scegli_parole({r: "\n\n".join(t) for r, t in per.items()})
        self.vettori = [vettore(f["testo"], self.vocabolario) for f in self.finestre]
        self.chiavi = [f["chiave"] for f in self.finestre]
        self.media, self.dev = medie_dev(self.vettori)
        self._propri = None

    def basta(self):
        return len(self.finestre) >= MIN_FINESTRE and bool(self.vocabolario)

    def delta_di(self, testo, chiave=None):
        v = vettore(testo, self.vocabolario)
        if chiave is None:
            return delta(v, self.media, self.dev)
        (media, dev), quante = statistiche_senza(self.vettori, self.chiavi, chiave)
        return delta(v, media, dev) if quante >= MIN_FINESTRE else None

    def delta_propri(self):
        """Distanza di ogni finestra dalle altre che non la toccano (lasciata fuori una alla volta)."""
        if self._propri is None:
            self._propri = []
            for v, c in zip(self.vettori, self.chiavi):
                (media, dev), quante = statistiche_senza(self.vettori, self.chiavi, c)
                if quante >= MIN_FINESTRE:
                    self._propri.append(delta(v, media, dev))
        return self._propri

    def spiega(self, testo, quante=5):
        """Le parole che più pesano nella distanza: in eccesso e mancanti, con i conteggi attesi."""
        ws = parole(testo)
        n = len(ws) or 1
        c = Counter(w.lower() for w in ws)
        voci = []
        for w, z, m in zip(self.vocabolario, zeta(vettore(testo, self.vocabolario), self.media, self.dev),
                           self.media):
            voci.append((z, w, c[w], m * n))
        eccesso = [v for v in sorted(voci, reverse=True) if v[0] > 1.5][:quante]
        mancanti = [v for v in sorted(voci) if v[0] < -1.5 and v[3] >= 1.5][:quante]
        return eccesso, mancanti


def descrivi_parole(voci):
    return ", ".join(f"«{w}» {c} (attese {fmt(a)})" for _, w, c, a in voci) or "nessuna"


def auc(positivi, negativi):
    """Probabilità che un positivo superi un negativo (area sotto la curva ROC, come in PAN [F65])."""
    if not positivi or not negativi:
        return None
    vinte = sum((p > q) + 0.5 * (p == q) for p in positivi for q in negativi)
    return vinte / (len(positivi) * len(negativi))


def descrivi_banda(b, cifre=1):
    e, rango, basso, alto = b
    if rango is None:
        return e
    return f"{e} ({fmt(100 * rango, 0)}°; banda {fmt(basso, cifre)}–{fmt(alto, cifre)})"


def oltre(etichetta):
    """Per le distanze conta solo lo scarto verso l'alto: sotto la banda vuol dire più vicino alla
    media delle finestre dell'autore, e la calibrazione non lo distingue (officina/stilometria.md)."""
    return etichetta in ("oltre il 95° percentile", "oltre il massimo osservato")


def colonna_profilo(nome, segs, n, marcatori, valori_passaggio):
    """Per ogni misura, la banda delle finestre del riferimento; None se non basta testo."""
    fin = finestre(segs, n)
    if len(fin) < MIN_FINESTRE:
        return None, len(fin)
    profili = [profilo_testo(f["testo"], marcatori) for f in fin]
    return {k: banda([p[k] for p in profili], v) for k, v in valori_passaggio.items()}, len(fin)


def cmd_confronta(passaggio, racconto):
    cartella = cartella_racconto(racconto)
    p = Path(passaggio)
    if not p.exists():
        errore(f"passaggio non trovato: {passaggio}")
    nuovo = testo_visibile(p.read_text(encoding="utf-8-sig"))
    marcatori = marcatori_voce()
    a = profilo_testo(nuovo, marcatori)
    n = len(parole(nuovo))
    fr = frasi_racconto(cartella)
    quota = quota_racconto(fr)
    stesso = senza(zona_autore(fr), nuovo) if quota <= SOGLIA_INTERO else []
    corpus = corpus_voce()
    corpo = senza([s for segs in corpus["autore"].values() for s in segs], nuovo)
    brani = brani_esempi()
    out = []
    w = out.append
    w(f"# Confronto: {p.name} contro {cartella.name} e i testi dell'autore\n")
    w("Le bande sono la variazione dei testi dell'autore su finestre della stessa lunghezza del passaggio "
      "(dal 5° al 95° percentile). Dicono dove il passaggio esce da quella variazione, non che cosa "
      "correggere: non c'è un valore da raggiungere, e la misura non dice chi ha scritto il testo "
      "(officina/stilometria.md).\n")
    w(f"- Passaggio: {n} parole.")
    if quota > SOGLIA_INTERO:
        w(f"- Stesso racconto: coincide per il {percentuale(quota, 1)} con i materiali dell'assistente; "
          "nessuna zona di riferimento.")
    else:
        w(f"- Stesso racconto: {parole_segmenti(stesso)} parole senza coincidenze con i materiali "
          "(le frasi del passaggio sono tolte).")
    w(f"- Corpus di voce: {parole_segmenti(corpo)} parole da {len(corpus['autore'])} racconti consolidati"
      + (f"; esclusi: {'; '.join(f'{r} ({m})' for r, m in corpus['esclusi'])}" if corpus["esclusi"] else "")
      + ".")
    if not marcatori:
        w("- Marcatori di voce: strumenti/marcatori_voce.txt è vuoto o assente; non contati.")
    w("")
    col_r, fin_r = colonna_profilo("racconto", stesso, n, marcatori, a)
    col_c, fin_c = colonna_profilo("corpus", corpo, n, marcatori, a)
    w(f"Finestre di almeno {n} parole: {fin_r} nello stesso racconto, {fin_c} nel corpus"
      f" (servono almeno {MIN_FINESTRE} per una banda).\n")
    scarti = {}
    for gruppo in (GRUPPO_VOCE, GRUPPO_SEGNALI, GRUPPO_RITMO):
        chiavi = [k for k in a if gruppo_di(k) == gruppo]
        w(f"## {gruppo}\n")
        w("| Misura | Passaggio | Stesso racconto | Corpus |")
        w("| --- | ---: | --- | --- |")
        for k in chiavi:
            celle = []
            for nome, col in (("stesso racconto", col_r), ("corpus", col_c)):
                if col is None:
                    celle.append("non abbastanza testo")
                    continue
                celle.append(descrivi_banda(col[k]))
                if fuori(col[k][0]):
                    scarti.setdefault(f"{k}: {col[k][0]}", []).append(nome)
            w(f"| {k} | {fmt(a[k], 2 if k == 'lunghezza media parola' else 1)} | {celle[0]} | {celle[1]} |")
        w("")
    w("## Distanza (Delta sulle parole più frequenti)\n")
    w("Media degli scarti in z-score sulle parole più frequenti del riferimento, senza pronomi personali "
      "e nomi propri [F58][F59]; la banda viene dalle finestre dell'autore lasciate fuori una alla volta.\n")
    for nome, segs in (("Stesso racconto", stesso), ("Corpus", corpo)):
        rif = Riferimento(segs, n)
        if not rif.basta() or len(rif.delta_propri()) < MIN_FINESTRE:
            w(f"- {nome}: non abbastanza testo ({len(rif.finestre)} finestre).")
            continue
        d = rif.delta_di(nuovo)
        b = banda(rif.delta_propri(), d)
        if oltre(b[0]):
            scarti.setdefault(f"distanza: {b[0]}", []).append(nome.lower())
        eccesso, mancanti = rif.spiega(nuovo)
        w(f"- {nome}: {fmt(d, 2)}, {descrivi_banda(b, 2)}; {len(rif.vocabolario)} parole.")
        w(f"  - più presenti del solito: {descrivi_parole(eccesso)}")
        w(f"  - meno presenti del solito: {descrivi_parole(mancanti)}")
    if brani:
        # Se il passaggio è uno dei brani, o li cita, quelle frasi escono dal termine di confronto.
        seq = sequenze_di(nuovo)
        brani = " ".join(f for _, f in frasi_posizionate(brani) if coperta_da(f, seq) < 0.5)
    if brani:
        filtrato = senza(corpo, brani)
        rif = Riferimento(filtrato, n)
        if rif.basta():
            zb = zeta(vettore(brani, rif.vocabolario), rif.media, rif.dev)
            propri = [coseno(zeta(v, rif.media, rif.dev), zb) for v in rif.vettori]
            d = coseno(zeta(vettore(nuovo, rif.vocabolario), rif.media, rif.dev), zb)
            b = banda(propri, d)
            w(f"- Brani approvati (voce/esempi.md), distanza coseno [F60]: {fmt(d, 2)}, {descrivi_banda(b, 2)}; "
              "la banda viene dalle finestre del corpus senza i brani.")
            if oltre(b[0]):
                scarti.setdefault(f"distanza dai brani: {b[0]}", []).append("brani approvati")
        else:
            w("- Brani approvati: non abbastanza testo nel corpus per una banda.")
    else:
        w("- Brani approvati: voce/esempi.md non ha brani, o il passaggio li contiene tutti.")
    stil = [m.group(0) for pat in stilemi() for m in re.finditer(pat, nuovo, re.IGNORECASE)]
    w("")
    if stil:
        w("Formule di repertorio nel passaggio: " + ", ".join(f"«{s}»" for s in stil))
    resto = testo_segmenti(stesso)
    fa = Counter(x.lower() for x in parole(nuovo) if len(x) >= 5 and x.lower() not in STOPWORDS)
    fb = Counter(x.lower() for x in parole(resto))
    estranee = [x for x, c in fa.items() if c >= 2 and fb[x] == 0]
    if estranee:
        w("Parole ripetute nel passaggio e assenti nel resto: " + ", ".join(estranee[:10]))
    w("")
    w("## Esito\n")
    if scarti or stil:
        w("Fuori dalla variazione dell'autore a questa lunghezza:")
        for voce, dove in scarti.items():
            w(f"- {voce} ({', '.join(dove)})")
        if stil:
            w(f"- formule di repertorio: {len(stil)}")
    else:
        w("Nessuna misura fuori dalla variazione dell'autore a questa lunghezza.")
    w("\nUno scarto non è un errore: dice dove il passaggio suona diverso. Non si riscrive per riportare "
      "un numero dentro la banda; quanto la misura distingue a questa lunghezza lo dice "
      "`prosa.py voce` (affidabilità).")
    print("\n".join(out))


# ---- voce: misure riproducibili del corpus

def affidabilita(corpus, marcatori):
    """Per ogni lunghezza: quanto la distanza e i marcatori separano il contrasto dalle zone dell'autore."""
    autore = [s for segs in corpus["autore"].values() for s in segs]
    contrasto = [s for segs in corpus["contrasto"].values() for s in segs]
    righe = []
    for n in LUNGHEZZE_AFFIDABILITA:
        rif = Riferimento(autore, n)
        fc = finestre(contrasto, n)
        propri = rif.delta_propri() if rif.basta() else []
        if len(propri) < MIN_FINESTRE or len(fc) < MIN_CONTRASTO:
            righe.append((n, len(rif.finestre), len(fc), None, None, None))
            continue
        dc = [rif.delta_di(f["testo"]) for f in fc]
        a_delta = auc(dc, propri)
        a_marc = None
        if marcatori:
            ma = [-per_mille(conta_marcatori(f["testo"], marcatori), f["parole"]) for f in rif.finestre]
            mc = [-per_mille(conta_marcatori(f["testo"], marcatori), f["parole"]) for f in fc]
            a_marc = auc(mc, ma)
        fuori_banda = sum(1 for d in dc if fuori(banda(propri, d)[0])) / len(dc)
        righe.append((n, len(rif.finestre), len(fc), a_delta, a_marc, fuori_banda))
    return righe


def variazione_tra_racconti(corpus):
    """Quota delle finestre di un racconto fuori dalla banda costruita sugli altri (attesa: ~10%)."""
    righe = []
    for nome, segs in corpus["autore"].items():
        altri = [s for r, ss in corpus["autore"].items() if r != nome for s in ss]
        if not altri:
            continue
        for n in LUNGHEZZE_AFFIDABILITA:
            rif = Riferimento(altri, n)
            propri = rif.delta_propri() if rif.basta() else []
            fs = finestre(segs, n)
            if len(propri) < MIN_FINESTRE or not fs:
                righe.append((nome, n, len(fs), None))
                continue
            quota = sum(1 for f in fs if fuori(banda(propri, rif.delta_di(f["testo"]))[0])) / len(fs)
            righe.append((nome, n, len(fs), quota))
    return righe


def cmd_voce(salva=False):
    corpus = corpus_voce()
    marcatori = marcatori_voce()
    out = []
    w = out.append
    w(f"# Misure di voce ({oggi()})\n")
    w(f"- Generato: {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}")
    w("- Misure descrittive dei testi dell'autore. Non attribuiscono un testo e non dicono se è buono "
      "(officina/stilometria.md).")
    w("- Corpus: racconti con `stato: consolidato`; contano solo le frasi senza coincidenze con i materiali "
      f"marcati dell'assistente (sequenze di {SEQUENZA_PROVENIENZA} parole, come «provenienza»).")
    w("- Contrasto, solo per l'affidabilità e mai come riferimento: le frasi coincidenti per metà o più, di "
      "tutti i racconti. È testo coincidente, non testo dell'assistente: può contenere frasi dell'autore "
      "citate in un materiale (allora la separazione misurata è prudente) e può differire per forma, per "
      "esempio più dialogo (allora la separazione è gonfiata).")
    if corpus["contrasto"]:
        w("- Contrasto per racconto: " + ", ".join(
            f"{r} {parole_segmenti(s)} parole" for r, s in corpus["contrasto"].items()) + ".")
    for r, m in corpus["esclusi"]:
        w(f"- Escluso: {r}, {m}.")
    if not marcatori:
        w("- strumenti/marcatori_voce.txt è vuoto o assente: i marcatori di voce non si contano.")
    w("")
    if not corpus["autore"]:
        w("Nessun racconto consolidato con frasi senza coincidenze: non c'è ancora un corpus di voce.")
        testo_out = "\n".join(out) + "\n"
        print(testo_out)
        return
    nomi = list(corpus["autore"])
    profili = {r: profilo_testo(testo_segmenti(corpus["autore"][r]), marcatori) for r in nomi}
    w("## Profilo per racconto (zone senza coincidenze)\n")
    w("| Misura | " + " | ".join(nomi) + " | intervallo |")
    w("| --- | " + " | ".join("---:" for _ in nomi) + " | --- |")
    w("| parole | " + " | ".join(str(parole_segmenti(corpus["autore"][r])) for r in nomi) + " | |")
    for k in profili[nomi[0]]:
        valori = [profili[r][k] for r in nomi]
        w(f"| {k} | " + " | ".join(fmt(v, 2 if k == 'lunghezza media parola' else 1) for v in valori)
          + f" | {fmt(min(valori))}–{fmt(max(valori))} |")
    w("")
    w("## Similitudini: due conteggi diversi\n")
    w("- **similitudini strette**: «come se», «come» seguito da articolo, «simile a», «sembra/pare un…» "
      "(RE_SIMILITUDINE); prende anche alcuni paragoni semplici (*come gli altri*).")
    w("- **«come»**: ogni occorrenza della parola, comprese le interrogative e i comparativi.\n")
    w("| Racconto | Parole | Similitudini strette ‰ | «come» ‰ |")
    w("| --- | ---: | ---: | ---: |")
    for c in racconti_consolidati():
        t = testo_visibile(testo_racconto(c)[0][1])
        nw = len(parole(t))
        w(f"| {c.name}, testo intero | {nw} | {fmt(per_mille(len(RE_SIMILITUDINE.findall(t)), nw))} | "
          f"{fmt(per_mille(len(RE_COME.findall(t)), nw))} |")
    for r in nomi:
        t = testo_segmenti(corpus["autore"][r])
        nw = len(parole(t))
        w(f"| {r}, zone senza coincidenze | {nw} | {fmt(per_mille(len(RE_SIMILITUDINE.findall(t)), nw))} | "
          f"{fmt(per_mille(len(RE_COME.findall(t)), nw))} |")
    w("")
    w("## Affidabilità per lunghezza\n")
    w("Finestre dell'autore (lasciate fuori una alla volta) contro finestre di contrasto della stessa "
      "lunghezza. AUC: probabilità che una finestra di contrasto risulti più lontana di una dell'autore "
      "(0,5 = la misura non distingue; 1 = separa sempre; sotto 0,5 il contrasto risulta più vicino alla "
      "media dell'autore delle finestre dell'autore stesse) [F65]. Per i marcatori: probabilità che una "
      "finestra di contrasto ne abbia meno. Le finestre si sovrappongono per metà: quelle indipendenti "
      "sono circa la metà delle contate.\n")
    w("| Parole | Finestre autore | Finestre contrasto | AUC distanza | AUC marcatori | Contrasto fuori banda |")
    w("| ---: | ---: | ---: | ---: | ---: | ---: |")
    for n, fa, fc, a_d, a_m, fb in affidabilita(corpus, marcatori):
        if a_d is None:
            w(f"| {n} | {fa} | {fc} | non abbastanza testo | | |")
        else:
            w(f"| {n} | {fa} | {fc} | {fmt(a_d, 2)} | {fmt(a_m, 2) if a_m is not None else '—'} | "
              f"{percentuale(fb, 1)} |")
    w("")
    w("## Variazione tra racconti\n")
    w("Finestre di un racconto lette contro la banda costruita sugli altri. Se la banda descrivesse bene "
      "la variazione dell'autore, ne cadrebbe fuori circa il 10%: molto di più vuol dire che i racconti "
      "differiscono fra loro più di quanto le finestre di uno solo mostrino, e conta di più il confronto "
      "con lo stesso racconto.\n")
    righe = variazione_tra_racconti(corpus)
    if not righe:
        w("Un solo racconto nel corpus: la variazione tra racconti non si misura.")
    else:
        w("| Racconto | Parole | Finestre | Fuori banda |")
        w("| --- | ---: | ---: | ---: |")
        for nome, n, nf, q in righe:
            w(f"| {nome} | {n} | {nf} | {percentuale(q, 1) if q is not None else 'non abbastanza testo'} |")
    w("")
    w("## Definizioni\n")
    w("- Parole: sequenze di lettere; frasi: divise a punto, punto esclamativo o interrogativo e puntini "
      "seguiti da maiuscola. La narrazione esclude il testo tra caporali o virgolette e le righe di battuta.")
    w("- ‰: occorrenze ogni mille parole del testo misurato.")
    w("- Marcatori di voce: le espressioni di strumenti/marcatori_voce.txt, come parole intere.")
    w(f"- Distanza: Delta di Burrows sulle {MFW} parole più frequenti del riferimento con almeno "
      f"{MFW_MINIMO} occorrenze, senza pronomi personali né parole quasi sempre maiuscole; con almeno due "
      f"racconti di {CULLING_PAROLE} parole, esce la parola concentrata per oltre il {int(CULLING * 100)}% in "
      "uno solo [F58][F59].")
    w(f"- Finestre: frasi intere consecutive fino ad almeno N parole, una ogni mezza finestra circa, senza "
      f"attraversare stacchi di scena o frasi escluse; banda dal 5° al 95° percentile, con almeno "
      f"{MIN_FINESTRE} finestre [F62].")
    testo_out = "\n".join(out) + "\n"
    print(testo_out)
    if salva:
        dest = salva_univoco(RADICE / "voce" / "misure", f"{oggi()}-misure.md", testo_out)
        print(f"Salvato in {relativo(dest)}")


# ---- deriva: finestra mobile lungo un racconto

def cmd_deriva(racconto, n=FINESTRA_DERIVA):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    fr = frasi_racconto(cartella)
    corpus = corpus_voce()
    marcatori = marcatori_voce()
    corpo = [s for segs in corpus["autore"].values() for s in segs]
    rif = Riferimento(corpo, n)
    origine = "corpus di voce"
    if not rif.basta() or len(rif.delta_propri()) < MIN_FINESTRE:
        rif = Riferimento(zona_autore(fr) if quota_racconto(fr) <= SOGLIA_INTERO else [], n)
        origine = "zone senza coincidenze dello stesso racconto"
    out = []
    w = out.append
    w(f"# Deriva: {cartella.name} ({oggi()})\n")
    w(identita_report(cartella, dati))
    w(f"Finestra mobile di almeno {n} parole a frasi intere, una ogni mezza finestra circa, lungo tutto il "
      f"testo (rolling stylometry [F62]). Ogni finestra si legge contro le finestre del {origine}, "
      "senza quelle che la toccano. Non dice chi ha scritto una finestra: dice dove la prosa esce dalla "
      "variazione osservata (officina/stilometria.md).\n")
    if not rif.basta() or len(rif.delta_propri()) < MIN_FINESTRE:
        w("Non abbastanza testo di riferimento per una banda: nessun racconto consolidato con frasi "
          "senza coincidenze, e nemmeno nel racconto stesso.")
        print("\n".join(out))
        return
    propri = rif.delta_propri()
    fs = finestre(segmenti(fr, lambda f: True), n)
    w(f"Riferimento: {len(rif.finestre)} finestre, {len(rif.vocabolario)} parole; banda della distanza "
      f"{fmt(quantile(propri, BANDA[0]), 2)}–{fmt(quantile(propri, BANDA[1]), 2)}.\n")
    w("| N. | Capoversi | Parole | Coincidenza | Distanza | Posizione"
      + (" | Marcatori ‰" if marcatori else "") + " | Più presenti / meno presenti |")
    w("| ---: | --- | ---: | ---: | ---: | --- |" + (" ---: |" if marcatori else "") + " --- |")
    quante_fuori = coincidenti_fuori = 0
    for i, f in enumerate(fs, 1):
        d = rif.delta_di(f["testo"], f["chiave"])
        if d is None:
            continue
        b = banda(propri, d)
        coinc = sum(x["parole"] * x["quota"] for x in f["frasi"]) / f["parole"]
        if oltre(b[0]):
            quante_fuori += 1
            coincidenti_fuori += coinc >= 0.5
        eccesso, mancanti = rif.spiega(f["testo"], 3)
        cap = f"{f['frasi'][0]['capoverso']}–{f['frasi'][-1]['capoverso']}"
        segno = f"**{b[0]}**" if oltre(b[0]) else b[0]
        marc = (f" | {fmt(per_mille(conta_marcatori(f['testo'], marcatori), f['parole']))}"
                if marcatori else "")
        spieg = (", ".join(x[1] for x in eccesso) or "—") + " / " + (", ".join(x[1] for x in mancanti) or "—")
        w(f"| {i} | {cap} | {f['parole']} | {percentuale(coinc, 1)} | {fmt(d, 2)} | {segno}{marc} | {spieg} |")
    w("")
    w(f"Finestre oltre la banda: {quante_fuori} su {len(fs)}, di cui {coincidenti_fuori} in zone coincidenti "
      "per metà o più. Sotto la banda vuol dire più vicina alla media delle finestre dell'autore: non si conta. "
      "Oltre la banda in una zona dell'autore è variazione da rispettare, salvo un effetto diverso "
      "dall'intenzione; quanto la misura distingue a questa lunghezza lo dice `prosa.py voce`.")
    print("\n".join(out))


RE_DASH_INIZIO = re.compile(r"^\s*(?:\\)?[—–-]\s?")
DICENDI = set("""
dice disse dico dissi chiede chiese chiedo chiesi domanda domandò risponde rispose rispondo risposi
esclama esclamò aggiunge aggiunse riprende riprese continua continuò conclude concluse replica replicò
ribatte ribatté insiste insistette fa fece mormora mormorò sussurra sussurrò grida gridò urla urlò
spiega spiegò osserva osservò ammette ammise corregge corresse
""".split())


def converti_riga_lineette(riga):
    """Converte una battuta con lineette o trattini a inizio riga in caporali.

    Ritorna (ipotesi, semplice, motivo). Anche le proposte semplici vanno verificate.
    """
    corpo = RE_DASH_INIZIO.sub("", riga, count=1)
    # Separatori interni: lineetta o trattino tra spazi, attaccato a punteggiatura,
    # oppure lineetta (non trattino) attaccata alla parola precedente.
    sep = r"\s[—–-]\s?|(?<=[.,!?…])\s?[—–-](?=\s|$)|\s[—–-](?=[A-ZÀ-Ýa-zà-ý])|(?<=\w)[—–](?=\s)"
    pezzi = [x.strip() for x in re.split(sep, corpo)]
    while pezzi and not pezzi[-1]:
        pezzi.pop()
    if not pezzi:
        return riga, False, "riga vuota"
    motivi = []
    if len(pezzi) > 1:
        motivi.append("separatore interno: confine tra battuta, inciso e narrazione da valutare")
    if len(pezzi) == 1 and len(parole(pezzi[0])) > 50:
        motivi.append("battuta lunga senza lineetta di chiusura: forse dentro c'è anche narrazione")
    if len(pezzi) > 3:
        motivi.append("più di due cambi tra battuta e narrazione")
    for i in range(0, len(pezzi), 2):
        if "«" in pezzi[i] or "»" in pezzi[i]:
            pezzi[i] = pezzi[i].replace("«", "“").replace("»", "”")
            motivi.append("citazione dentro la battuta: caporali interni resi con virgolette alte [F1]")
    for i in range(1, len(pezzi), 2):
        primo = pezzi[i].split(" ", 1)[0].strip(",.;:").lower()
        if primo in DICENDI:
            pezzi[i] = pezzi[i][0].lower() + pezzi[i][1:]
            if pezzi[i - 1].endswith(".") and not pezzi[i - 1].endswith("..."):
                pezzi[i - 1] = pezzi[i - 1][:-1]
    risultato = [f"«{x}»" if i % 2 == 0 else x for i, x in enumerate(pezzi) if x]
    nuova = " ".join(risultato)
    if re.search(r"[—–]|\s-\s", nuova.replace("«", "").replace("»", "")):
        motivi.append("resta una lineetta o un trattino non interpretato")
    return nuova, not motivi, "; ".join(motivi)


def cmd_dialoghi(racconto, salva=False):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    testo = "\n\n".join(t for _, t in testo_racconto(cartella))
    conv = conta_convenzioni(testo)
    out = [f"# Dialoghi: {cartella.name} ({oggi()})\n",
           identita_report(cartella, dati),
           "Convenzioni presenti: " + ", ".join(f"{k} {v}" for k, v in conv.items()) + "\n",
           "Sistema della raccolta: caporali, una battuta per capoverso (officina/norme-redazionali.md).",
           f"Scheda, dialoghi: {dati.get('dialoghi') or 'non indicato'}.",
           "Virgola dopo il caporale prima della frase citante: da decidere in redazione; l'anteprima non la corregge.",
           "Questa è un'anteprima da verificare: niente viene modificato. Le conversioni si applicano al Doc solo dopo approvazione.\n"]
    f_scheda = cartella / "scheda.md"
    if not f_scheda.exists():
        out.append("Scheda assente: si usa la convenzione della raccolta, senza deroghe note.\n")
    scheda = f_scheda.read_text(encoding="utf-8-sig") if f_scheda.exists() else ""
    sezione = re.search(r"(?ms)^## Scelte di questo racconto\s*\n(.*?)(?=^## |\Z)", scheda)
    deroga_dialoghi = bool(sezione and re.search(
        r"\b(dialogh\w*|caporal\w*|lineett\w*|trattin\w*|virgol\w*|citazion\w*)\b",
        sezione.group(1), re.IGNORECASE))
    if sezione and sezione.group(1).strip():
        out.extend(["Deroghe e scelte del racconto da considerare:", sezione.group(1).strip(), ""])
    semplici, da_vedere, lunghi = [], [], []
    for n, riga in enumerate(testo.splitlines(), 1):
        if not riga.strip():
            continue
        if RE_DASH_INIZIO.match(riga) and len(riga) < 1500:
            nuova, ok, motivo = converti_riga_lineette(riga)
            if ok and (dati.get("dialoghi") or "caporali").casefold() == "caporali" and not deroga_dialoghi:
                semplici.append((n, riga.strip(), nuova))
            else:
                dubbio = motivo or "la scheda contiene una scelta sui dialoghi da interpretare"
                da_vedere.append((n, riga.strip(), nuova, dubbio))
        elif len(parole(riga)) > 120 and len(re.findall(r"(?:^|\s)[—–-]\s?[A-ZÀ-Ý]", riga)) >= 2:
            lunghi.append((n, len(parole(riga))))
        elif "“" in riga or re.search(r'(^|\s)"[A-ZÀ-Ý]', riga):
            da_vedere.append((n, riga.strip(), "", "virgolette alte: dialogo o citazione? Decidi a mano"))
    out.append(f"## Proposte semplici da verificare ({len(semplici)})\n")
    for n, prima, dopo in semplici:
        out += [f"**Riga {n}**", f"- prima: {prima}", f"- dopo: {dopo}", ""]
    out.append(f"## Da controllare a mano ({len(da_vedere)})\n")
    for n, prima, dopo, motivo in da_vedere:
        out += [f"**Riga {n}**", f"- originale: {prima}", f"- perché: {motivo}"]
        if dopo:
            out.append(f"- ipotesi da valutare: {dopo}")
        out.append("")
    out.append(f"## Capoversi lunghi con battute dentro ({len(lunghi)})\n")
    out.append("Battute di più personaggi dentro un capoverso narrativo: vanno separate a mano, una per capoverso.\n")
    for n, np in lunghi:
        out.append(f"- riga {n}: capoverso di {np} parole")
    testo_out = "\n".join(out) + "\n"
    print(testo_out)
    if salva:
        dest = salva_univoco(cartella / "materiali", f"{oggi()}-dialoghi-anteprima.md", testo_out)
        print(f"Salvato in {dest}")


def cmd_dividi(racconto):
    dividi(cartella_racconto(racconto), severo=True)


def dividi(cartella, severo=True):
    # severo rimane accettato per compatibilità: l'assenza di stacchi è valida.
    f = cartella / "testo.md"
    if not f.exists():
        errore("manca testo.md")
    scene, corrente = [], []
    for riga in f.read_text(encoding="utf-8-sig").splitlines():
        if RE_SEPARATORE.match(riga):
            if any(r.strip() for r in corrente):
                scene.append(corrente)
            corrente = [riga] if riga.lstrip().startswith("#") else []
        else:
            corrente.append(riga)
    if any(r.strip() for r in corrente):
        scene.append(corrente)
    if len(scene) < 2:
        msg = "nessuna divisione in più scene (* * * oppure un titolo #): si usa il testo intero."
        for vecchio in (cartella / "scene").glob("*.md"):
            togli(vecchio, SCENE_INCOMPLETE)
        print("Attenzione: " + msg + " Le vecchie copie in scene/ sono state tolte: il testo viene letto intero da testo.md.")
        return
    d = cartella / "scene"
    d.mkdir(exist_ok=True)
    nuove = set()
    for i, righe in enumerate(scene, 1):
        nuove.add(f"{i:02d}.md")
        pubblica(d / f"{i:02d}.md", ("\n".join(righe).strip("\n") + "\n").encode("utf-8"),
                 SCENE_INCOMPLETE)
    for vecchio in d.glob("*.md"):
        if vecchio.name not in nuove:
            togli(vecchio, SCENE_INCOMPLETE)
    nota = "" if leggi_scheda(cartella).get("modalita") == "lunga" else " Ricorda di impostare «modalita: lunga» nella scheda."
    print(f"Scene aggiornate: {len(scene)} file in scene/.{nota}")


def cmd_unisci(racconto):
    cartella = cartella_racconto(racconto)
    testo_racconto(cartella)  # verifica la presenza della copia completa
    pubblica(cartella / "testo-unito.md", (cartella / "testo.md").read_bytes())
    print("Scritto testo-unito.md: copia di testo.md. Le modifiche manuali in scene/ non vengono usate.")


def capoversi(testo):
    """Blocchi di righe non vuote; righe vuote o di soli spazi li separano."""
    blocchi, corrente = [], []
    for riga in testo.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if riga.strip():
            corrente.append(riga)
        elif corrente:
            blocchi.append("\n".join(corrente))
            corrente = []
    if corrente:
        blocchi.append("\n".join(corrente))
    return blocchi


def visibile_capoverso(blocco):
    # Gli stacchi si confrontano come tali: il loro testo visibile è vuoto.
    if RE_STACCO.fullmatch(blocco):
        return ("stacco", "")
    return ("testo", testo_visibile(blocco))


def mostra_capoverso(voce, inizio=0, largo=60):
    tipo, testo = voce
    if tipo == "stacco":
        return "[stacco di scena]"
    pezzo = testo[inizio:inizio + largo].replace("\n", "↵")
    return ("…" if inizio else "") + pezzo + ("…" if inizio + largo < len(testo) else "")


def allinea_simili(a, b, da, db):
    """Abbina i capoversi simili di un tratto cambiato; gli altri restano senza corrispondente."""
    n, m = len(a), len(b)
    if n * m > 2500:
        # Tratti molto lunghi: abbinamento per posizione, per non rallentare.
        k = min(n, m)
        return ([(da + x, db + x) for x in range(k)] + [(da + x, None) for x in range(k, n)] +
                [(None, db + y) for y in range(k, m)])

    def costo(x, y):
        # Simili: costo sotto 0,5; diversi: 1,5, meno di un capoverso tolto e uno aggiunto.
        if x[0] != y[0]:
            return 1.5
        confronto = difflib.SequenceMatcher(None, x[1], y[1], autojunk=False)
        if confronto.real_quick_ratio() < 0.5 or confronto.quick_ratio() < 0.5:
            return 1.5
        simile = confronto.ratio()
        return 1 - simile if simile >= 0.5 else 1.5

    costi = [[costo(x, y) for y in b] for x in a]
    tot = [[float(i + j) if not i or not j else 0.0 for j in range(m + 1)] for i in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            tot[i][j] = min(tot[i - 1][j - 1] + costi[i - 1][j - 1], tot[i - 1][j] + 1, tot[i][j - 1] + 1)
    coppie, i, j = [], n, m
    while i or j:
        if i and j and tot[i][j] == tot[i - 1][j - 1] + costi[i - 1][j - 1]:
            i, j = i - 1, j - 1
            coppie.append((da + i, db + j))
        elif i and tot[i][j] == tot[i - 1][j] + 1:
            i -= 1
            coppie.append((da + i, None))
        else:
            j -= 1
            coppie.append((None, db + j))
    return coppie[::-1]


def differenze_capoversi(a, b):
    """Allinea due liste di capoversi; restituisce conteggi e voci (tipo, n. in a, n. in b, estratti)."""
    chiavi = [[(tipo, " ".join(testo.split())) for tipo, testo in lista] for lista in (a, b)]
    coppie = []
    confronto = difflib.SequenceMatcher(None, *chiavi, autojunk=False)
    for operazione, i1, i2, j1, j2 in confronto.get_opcodes():
        if operazione == "equal":
            coppie += zip(range(i1, i2), range(j1, j2))
        else:
            coppie += allinea_simili(a[i1:i2], b[j1:j2], i1, j1)
    conteggi = {"diversi": 0, "aggiunti": 0, "mancanti": 0}
    voci = []
    for i, j in coppie:
        if j is None:
            voci.append(("mancante in testo.md", i + 1, None, mostra_capoverso(a[i]), None))
            conteggi["mancanti"] += 1
        elif i is None:
            voci.append(("aggiunto in testo.md", None, j + 1, None, mostra_capoverso(b[j])))
            conteggi["aggiunti"] += 1
        elif a[i] != b[j]:
            x, y = a[i], b[j]
            inizio = max(0, len(os.path.commonprefix([x[1], y[1]])) - 25)
            nota = " (solo spazi)" if chiavi[0][i] == chiavi[1][j] else ""
            voci.append((f"diverso{nota}", i + 1, j + 1,
                         mostra_capoverso(x, inizio), mostra_capoverso(y, inizio)))
            conteggi["diversi"] += 1
    return conteggi, voci


def cmd_verifica(file, racconto, salva=False):
    """Confronta testo.md con un'esportazione della fonte; scrive solo con --salva."""
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    copia = testo_racconto(cartella)[0][1]
    src = Path(file)
    try:
        esportazione = leggi_fonte(src)
        impronta = hashlib.sha256(src.read_bytes()).hexdigest()
    except ERRORI_FONTE as exc:
        errore(f"verifica non riuscita: file non leggibile ({exc}). Nessun file è stato modificato.")
    grezzi_a, grezzi_b = capoversi(esportazione), capoversi(copia)
    a = [visibile_capoverso(c) for c in grezzi_a]
    b = [visibile_capoverso(c) for c in grezzi_b]
    numeri = [(conta_parole(t), conta_battute(t)) for t in (esportazione, copia)]
    # «coincide» vale sui byte: la stessa impronta che darebbe una nuova importazione.
    if esportazione.encode("utf-8") == (cartella / "testo.md").read_bytes():
        esito = "coincide"
    elif a == b and numeri[0] == numeri[1]:
        esito = "coincide nel testo, differisce nella formattazione"
    else:
        esito = "differisce"
    out = []
    w = out.append
    w(f"# Verifica: {cartella.name} ({oggi()})\n")
    w(f"Esito: {esito}\n")
    w(identita_report(cartella, dati))
    w(f"- File confrontato: {src.resolve()}")
    w(f"- SHA-256 del file confrontato: `{impronta}`")
    w("- Il file è letto come da `importa`: .md come Markdown, .txt e testo DOCX come testo letterale.\n")
    w("| | File | testo.md |")
    w("| --- | ---: | ---: |")
    w(f"| Capoversi | {len(a)} | {len(b)} |")
    w(f"| Parole | {numeri[0][0]} | {numeri[1][0]} |")
    w(f"| Battute | {numeri[0][1]} | {numeri[1][1]} |\n")
    w(CONVENZIONE_BATTUTE + "\n")
    if esito == "differisce":
        conteggi, voci = differenze_capoversi(a, b)
        w("## Differenze nel testo visibile\n")
        if not voci:
            w("- Capoversi uguali, battute diverse: la differenza sta in righe di soli spazi tra i capoversi.")
        else:
            w(f"- Capoversi diversi: {conteggi['diversi']}; aggiunti in testo.md: {conteggi['aggiunti']}; "
              f"mancanti in testo.md: {conteggi['mancanti']}.")
            w("- Numeri di capoverso contati senza righe vuote; ↵ indica un a capo interno.")
            if len(voci) > 10:
                w(f"- Prime dieci differenze su {len(voci)}:")
            for tipo, n_a, n_b, da_a, da_b in voci[:10]:
                w(f"\n**Capoverso {n_a or '—'} del file, {n_b or '—'} di testo.md: {tipo}**")
                if da_a is not None:
                    w(f"- file: {da_a}")
                if da_b is not None:
                    w(f"- testo.md: {da_b}")
        w("\nUna copia che non coincide non si usa come evidenza: si rigenera dalla fonte.")
    elif esito != "coincide":
        diversi = [(i + 1, x, y) for i, (x, y) in enumerate(zip(grezzi_a, grezzi_b)) if x != y]
        w("## Differenze di formattazione\n")
        w("Stesso testo visibile, Markdown diverso: corsivo, escape, stile degli stacchi o dei titoli, "
          "righe vuote, fine riga, BOM.\n")
        if not diversi:
            w("- I capoversi coincidono anche nel Markdown: cambiano solo righe vuote, fine riga o BOM.")
        else:
            w(f"- Capoversi con Markdown diverso: {len(diversi)}." +
              (" I primi dieci:" if len(diversi) > 10 else ""))
            for n, x, y in diversi[:10]:
                inizio = max(0, len(os.path.commonprefix([x, y])) - 25)
                w(f"\n**Capoverso {n}**")
                w(f"- file: {mostra_capoverso(('testo', x), inizio)}")
                w(f"- testo.md: {mostra_capoverso(('testo', y), inizio)}")
    testo_out = "\n".join(out) + "\n"
    print(testo_out)
    if salva:
        dest = salva_univoco(cartella / "revisioni", f"{oggi()}-verifica.md", testo_out)
        print(f"Salvato in {relativo(dest)}")


def blocchi_markdown(testo):
    """Capoversi della copia nel loro Markdown: anche un corsivo cambiato è una differenza."""
    return [("stacco", "") if RE_STACCO.fullmatch(c) else ("testo", c) for c in capoversi(testo)]


ESITI_DIFFERENZE = {"mancante in testo.md": "tolto", "aggiunto in testo.md": "aggiunto"}


def cmd_differenze(racconto, sha):
    """Capoversi cambiati fra una copia conservata da importa e testo.md attuale."""
    cartella = cartella_racconto(racconto)
    attuale = testo_racconto(cartella)[0][1]
    sha = sha.strip().strip("`").lower()
    if not re.fullmatch(rf"[0-9a-f]{{{CIFRE_COPIA},64}}", sha):
        errore(f"impronta non valida: {sha}. Usare lo SHA-256 di testo.md riportato nel report, "
               f"intero o nelle prime {CIFRE_COPIA} cifre.")
    copia = percorso_copia(cartella, sha)
    if not copia.is_file():
        errore(f"manca la copia {sha[:CIFRE_COPIA]} in {relativo(copia.parent)}/: la versione del report "
               "non è stata conservata (importata prima delle copie, o cartella pulita). "
               "Occorre una revisione intera.")
    impronta = hashlib.sha256(copia.read_bytes()).hexdigest()
    if not impronta.startswith(sha):
        errore(f"la copia {copia.name} ha impronta {impronta}, diversa da {sha}: non è la versione "
               "del report. Occorre una revisione intera.")
    attuale_sha = hashlib.sha256((cartella / "testo.md").read_bytes()).hexdigest()
    prima = blocchi_markdown(copia.read_text(encoding="utf-8-sig"))
    dopo = blocchi_markdown(attuale)
    print(f"# Differenze: {cartella.name}\n")
    print(f"- Copia di riferimento: copie/{copia.name}, SHA-256 `{impronta}`")
    print(f"- testo.md attuale: SHA-256 `{attuale_sha}`")
    print("- Capoversi contati senza righe vuote, stacchi di scena inclusi; ↵ indica un a capo interno.\n")
    if impronta == attuale_sha:
        print("Nessuna differenza: testo.md è identico alla copia di riferimento.")
        return
    conteggi, voci = differenze_capoversi(prima, dopo)
    cambiati_prima, cambiati_dopo = set(), set()
    for tipo, n_a, n_b, da_a, da_b in voci:
        esito = ESITI_DIFFERENZE.get(tipo, "modificato")
        if tipo.endswith("(solo spazi)"):
            esito += " (solo spazi)"
        elif esito == "modificato" and prima[n_a - 1][0] == dopo[n_b - 1][0] == "testo" and \
                testo_visibile(prima[n_a - 1][1]) == testo_visibile(dopo[n_b - 1][1]):
            esito += " (solo formattazione)"
        if n_a:
            cambiati_prima.add(n_a)
        if n_b:
            cambiati_dopo.add(n_b)
        print(f"**Capoverso {n_b or '—'} di testo.md, {n_a or '—'} della copia: {esito}**")
        if da_a is not None:
            print(f"- prima: {da_a}")
        if da_b is not None:
            print(f"- dopo: {da_b}")
        print()
    if not voci:
        print("Capoversi identici: cambiano solo righe vuote, fine riga o BOM.\n")
    print("## Riepilogo\n")
    print(f"- Capoversi cambiati: {conteggi['aggiunti'] + conteggi['diversi']} su {len(dopo)} di testo.md "
          f"(modificati {conteggi['diversi']}, aggiunti {conteggi['aggiunti']}); "
          f"tolti dalla copia: {conteggi['mancanti']} su {len(prima)}.")
    primo = 1 in cambiati_dopo or 1 in cambiati_prima
    ultimo = len(dopo) in cambiati_dopo or len(prima) in cambiati_prima
    print(f"- Primo capoverso: {'cambiato' if primo else 'invariato'}. "
          f"Ultimo capoverso: {'cambiato' if ultimo else 'invariato'}.")


# Con 8 parole consecutive le coincidenze casuali fra frasi comuni sono rare, e una frase
# dell'assistente ritoccata in un punto resta riconoscibile nei tratti prima e dopo il ritocco.
SEQUENZA_PROVENIENZA = 8
RE_MARCATORE = re.compile(r"(?m)^[ \t]*-?[ \t]*Autore del testo:[ \t]*assistente\b", re.IGNORECASE)
AVVERTENZA_PROVENIENZA = ("Coincidenza testuale con materiali dell'assistente: "
                          "non è un'attribuzione né un giudizio sul bando.")


def parole_normalizzate(testo):
    """Minuscole, apostrofi e virgolette unificati, punteggiatura tolta."""
    t = testo_visibile(testo).casefold()
    t = re.sub(r"[’‘`'´«»“”„\"]", " ", t)
    return re.findall(r"[^\W_]+", t)


def materiali_marcati(cartella):
    marcati = []
    for f in sorted((cartella / "materiali").glob("*.md")):
        if f.name.startswith("_"):
            continue  # file di lavoro, come _passaggio.md
        if RE_MARCATORE.search(f.read_text(encoding="utf-8-sig")):
            marcati.append(f)
    return marcati


def misura_provenienza(cartella, materiali):
    """Quota delle parole di testo.md coperte da sequenze di N parole presenti in un materiale."""
    n = SEQUENZA_PROVENIENZA
    blocchi = capoversi(testo_racconto(cartella)[0][1])
    parole_copia, capoverso_di = [], []
    for i, blocco in enumerate(blocchi):
        p = parole_normalizzate(blocco)
        parole_copia += p
        capoverso_di += [i] * len(p)
    sequenze = {}
    for k, f in enumerate(materiali):
        p = parole_normalizzate(f.read_text(encoding="utf-8-sig"))
        for i in range(len(p) - n + 1):
            sequenze.setdefault(tuple(p[i:i + n]), set()).add(k)
    coperte = [set() for _ in parole_copia]
    for i in range(len(parole_copia) - n + 1):
        for k in sequenze.get(tuple(parole_copia[i:i + n]), ()):
            for j in range(i, i + n):
                coperte[j].add(k)
    totale = len(parole_copia)
    coincidenti = sum(1 for c in coperte if c)
    per_capoverso = {}
    for i, c in enumerate(coperte):
        tot, coin = per_capoverso.get(capoverso_di[i], (0, 0))
        per_capoverso[capoverso_di[i]] = (tot + 1, coin + bool(c))
    contributi = [sum(1 for c in coperte if k in c) for k in range(len(materiali))]
    return {"totale": totale, "coincidenti": coincidenti, "blocchi": blocchi,
            "per_capoverso": per_capoverso, "contributi": contributi, "coperte": coperte}


def percentuale(parte, tutto):
    return f"{100 * parte / tutto:.1f}%".replace(".", ",") if tutto else "0,0%"


def risolvi_materiale(cartella, arg):
    p = Path(arg)
    for candidato in (p, cartella / p):
        if candidato.is_file():
            return candidato
    errore(f"materiale non trovato: {arg} (cerco dalla cartella corrente e da {relativo(cartella)}).")


def cmd_provenienza(racconto, *materiali, salva=False):
    cartella = cartella_racconto(racconto)
    dati = leggi_scheda(cartella)
    testo_racconto(cartella)
    if materiali:
        file = [risolvi_materiale(cartella, m) for m in materiali]
    else:
        file = materiali_marcati(cartella)
        if not file:
            print(f"Nessun materiale con il marcatore «- Autore del testo: assistente (…)» in "
                  f"{relativo(cartella / 'materiali')}/. Passare i file da confrontare: "
                  f"prosa.py provenienza {cartella.name} materiali/<file>.md …")
            return
    m = misura_provenienza(cartella, file)
    out = [f"# Provenienza: {cartella.name} ({oggi()})\n", identita_report(cartella, dati),
           AVVERTENZA_PROVENIENZA + "\n",
           f"Metodo: parole normalizzate (minuscole, senza punteggiatura, apostrofi e virgolette); "
           f"una parola coincide se sta in una sequenza di almeno {SEQUENZA_PROVENIENZA} parole "
           "consecutive presente in un materiale. Conta tutto il materiale, anche il testo dell'autore "
           "che vi fosse citato.\n",
           f"**Quota coincidente: {percentuale(m['coincidenti'], m['totale'])}** "
           f"({m['coincidenti']} parole su {m['totale']}).\n", "## Materiali\n"]
    for f, c in zip(file, m["contributi"]):
        out.append(f"- {relativo(f)}: {c} parole ({percentuale(c, m['totale'])})")
    if len(file) > 1:
        out.append("- Una parola presente in più materiali conta per ciascuno: i contributi possono "
                   "sommare più della quota.")
    out.append("\n## Capoversi con coincidenze\n")
    sopra = [(i, t, c) for i, (t, c) in sorted(m["per_capoverso"].items()) if c]
    if not sopra:
        out.append("- Nessuno.")
    for i, t, c in sopra:
        out.append(f"- capoverso {i + 1}: {percentuale(c, t)} ({c}/{t} parole): "
                   f"{mostra_capoverso(visibile_capoverso(m['blocchi'][i]))}")
    testo_out = "\n".join(out) + "\n"
    print(testo_out)
    if salva:
        dest = salva_univoco(cartella / "revisioni", f"{oggi()}-provenienza.md", testo_out)
        print(f"Salvato in {relativo(dest)}")


# Circa una cartella editoriale (una pagina di dattiloscritto): la misura di D7 nello sprint mestiere.
BATTUTE_TAPPA = 1800
# Un capoverso oltre una volta e mezza la misura si spezza a fine frase; sotto, resta intero.
SOGLIA_SPEZZA = 1.5
RE_FINE_FRASE = re.compile(r"[.!?…][»”\"*_)]*\s+(?=[«“\"—–\-*_(]?\s?[A-ZÀ-Ý])")


def unita_tappe(blocchi, misura):
    """Unità di lettura: (testo, capoverso, chiude_scena). I capoversi lunghi diventano frasi."""
    unita = []
    for i, blocco in enumerate(blocchi):
        if RE_SEPARATORE.fullmatch(blocco) and not RE_TITOLO.fullmatch(blocco):
            unita.append((blocco, i, True))
            continue
        if RE_TITOLO.fullmatch(blocco.split("\n", 1)[0]):
            unita.append((None, i, True))  # un titolo apre sempre una tappa nuova
        if conta_battute(blocco) <= misura * SOGLIA_SPEZZA:
            unita.append((blocco, i, False))
            continue
        inizio = 0
        for fine in RE_FINE_FRASE.finditer(blocco):
            unita.append((blocco[inizio:fine.end()], i, False))
            inizio = fine.end()
        unita.append((blocco[inizio:], i, False))
    return unita


def componi_tappa(pezzi):
    testo, ultimo = "", None
    for pezzo, capoverso in pezzi:
        if ultimo is not None:
            testo += "" if capoverso == ultimo else "\n\n"
        testo += pezzo
        ultimo = capoverso
    return testo.strip() + "\n"


def calcola_tappe(testo, misura=BATTUTE_TAPPA):
    tappe, corrente, battute = [], [], 0

    def chiudi():
        nonlocal corrente, battute
        if any(conta_battute(p) for p, _ in corrente):
            tappe.append(componi_tappa(corrente))
        corrente, battute = [], 0

    for pezzo, capoverso, separatore in unita_tappe(capoversi(testo), misura):
        if separatore:
            if pezzo is not None and not corrente and tappe:
                tappe[-1] += "\n" + pezzo + "\n"  # stacco subito dopo un taglio: resta visibile
            elif pezzo is not None:
                corrente.append((pezzo, capoverso))  # lo stacco chiude la tappa in cui si legge
            chiudi()
            continue
        b = conta_battute(pezzo)
        # Si taglia dove la tappa resta più vicina alla misura: prima o dopo questo pezzo.
        if corrente and battute + b > misura and misura - battute <= battute + b - misura:
            chiudi()
        corrente.append((pezzo, capoverso))
        battute += b
        if battute >= misura:
            chiudi()
    chiudi()
    return tappe


def cmd_tappe(racconto, misura=BATTUTE_TAPPA):
    """Scrive tappe/NN.md da testo.md; stampa solo numeri, mai il testo (lettore a freddo)."""
    cartella = cartella_racconto(racconto)
    tappe = calcola_tappe(testo_racconto(cartella)[0][1], misura)
    d = cartella / "tappe"
    d.mkdir(exist_ok=True)
    conseguenza = "Le tappe possono essere incomplete: rieseguire tappe."
    nuove = set()
    for i, tappa in enumerate(tappe, 1):
        nuove.add(f"{i:02d}.md")
        pubblica(d / f"{i:02d}.md", tappa.encode("utf-8"), conseguenza)
    for vecchia in d.glob("*.md"):
        if vecchia.name not in nuove:
            togli(vecchia, conseguenza)
    print(f"Tappe: {len(tappe)} in {relativo(d)}/ (misura {misura} battute).")
    for i, tappa in enumerate(tappe, 1):
        print(f"- {i:02d}.md: {conta_battute(tappa)} battute")


def cmd_registra(racconto, riga):
    """Accoda «- <riga>» a stato.md senza mostrarne il contenuto (racconto-lettore)."""
    cartella = cartella_racconto(racconto)
    stato = cartella / "stato.md"
    riga = riga.strip()
    if not riga:
        errore("riga vuota: niente da registrare.")
    if riga.splitlines() != [riga]:
        errore("la riga contiene degli a capo: registrare una voce su una riga sola.")
    if not stato.is_file():
        errore(f"manca {relativo(stato)}: niente è stato registrato.")
    # I byte esistenti restano identici; si aggiunge solo l'a capo mancante e la voce.
    try:
        contenuto = stato.read_bytes()
    except OSError as exc:
        errore(f"{relativo(stato)} non leggibile ({exc}): niente è stato registrato.")
    if contenuto and not contenuto.endswith(b"\n"):
        contenuto += b"\n"
    contenuto += f"- {riga}\n".encode("utf-8")
    try:
        pubblica(stato, contenuto)
    except OSError as exc:
        errore(f"{relativo(stato)} non aggiornato ({exc}). {CONSERVATA}")
    print(f"Registrato in {relativo(stato)}")


def opzione(args, cmd, nome, comando, forma, descrizione):
    """Toglie da args «nome valore» e restituisce il valore; None se l'opzione manca."""
    if nome not in args:
        return None
    if cmd != comando:
        errore(f"{nome} vale solo con «{comando}».")
    i = args.index(nome)
    if i + 1 >= len(args) or not re.fullmatch(forma, args[i + 1]):
        errore(f"{nome} vuole {descrizione}.")
    valore = args[i + 1]
    del args[i:i + 2]
    return valore


def main(argv):
    # I flussi catturati nei test (es. StringIO) non hanno reconfigure.
    for flusso in (sys.stdout, sys.stderr):
        reconfigure = getattr(flusso, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    if len(argv) < 2 or argv[1] in ("-h", "--help", "aiuto"):
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    salva = "--salva" in args
    args = [a for a in args if a != "--salva"]
    revisione = opzione(args, cmd, "--revisione", "intestazione", r"[^\s`]+",
                        "il revisionId acquisito insieme al testo, senza spazi né backtick")
    battute = opzione(args, cmd, "--battute", "tappe", r"[1-9]\d{2,5}",
                      "un numero intero di battute, almeno 100")
    finestra = opzione(args, cmd, "--finestra", "deriva", r"[1-9]\d{1,4}",
                       "un numero intero di parole, almeno 10")
    comandi = {
        "fonte": (cmd_fonte, 1),
        "nuovo": (cmd_nuovo, 1), "importa": (cmd_importa, 2), "conta": (cmd_conta, 1),
        "controlla": (lambda r: cmd_controlla(r, salva), 1), "confronta": (cmd_confronta, 2),
        "dialoghi": (lambda r: cmd_dialoghi(r, salva), 1), "dividi": (cmd_dividi, 1), "unisci": (cmd_unisci, 1),
        "registra": (cmd_registra, 2), "verifica": (lambda f, r: cmd_verifica(f, r, salva), 2),
        "intestazione": (lambda r: cmd_intestazione(r, revisione), 1),
        "nome-libero": (cmd_nome_libero, 1), "differenze": (cmd_differenze, 2),
        "provenienza": (lambda r, *m: cmd_provenienza(r, *m, salva=salva), None),
        "tappe": (lambda r: cmd_tappe(r, int(battute) if battute else BATTUTE_TAPPA), 1),
        "voce": (lambda: cmd_voce(salva), 0),
        "deriva": (lambda r: cmd_deriva(r, int(finestra) if finestra else FINESTRA_DERIVA), 1),
    }
    if cmd == "esporta":
        print("«esporta» arriverà nella fase 2: impaginazione secondo il bando.")
        return
    if cmd not in comandi:
        errore(f"comando sconosciuto: {cmd}. Usa «python -X utf8 strumenti/prosa.py aiuto».")
    funz, n = comandi[cmd]
    if n is None and not args:
        errore(f"«{cmd}» vuole almeno il racconto. Usa «python -X utf8 strumenti/prosa.py aiuto».")
    if n is not None and len(args) != n:
        errore(f"«{cmd}» vuole {n} argomento/i. Usa «python -X utf8 strumenti/prosa.py aiuto».")
    funz(*args)


if __name__ == "__main__":
    main(sys.argv)
