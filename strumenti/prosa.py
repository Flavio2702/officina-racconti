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
CONNETTIVI = [
    "inoltre", "tuttavia", "pertanto", "dunque", "quindi", "infatti", "comunque", "invece",
    "in questo modo", "in particolare", "allo stesso tempo", "d'altra parte", "d’altra parte",
]
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


def profilo_testo(testo):
    n = len(parole(testo)) or 1
    rt = statistiche_ritmo(testo)
    low = testo.lower()
    return {
        "parole": n,
        "media frase": rt["media"],
        "deviazione frase": rt["dev"],
        "frasi brevi %": round(100 * rt["brevi"] / rt["frasi"], 1) if rt["frasi"] else 0,
        "virgole ‰": per_mille(testo.count(","), n),
        "punto e virgola ‰": per_mille(testo.count(";"), n),
        "due punti ‰": per_mille(testo.count(":"), n),
        "esclamativi ‰": per_mille(testo.count("!"), n),
        "interrogativi ‰": per_mille(testo.count("?"), n),
        "puntini ‰": per_mille(testo.count("…") + testo.count("..."), n),
        "parentesi ‰": per_mille(testo.count("("), n),
        "lineette nella narrazione ‰": per_mille(len(re.findall(r"\s[—–]\s", togli_dialoghi(testo))), n),
        "avverbi -mente ‰": per_mille(sum(1 for w in parole(testo) if w.lower().endswith("mente") and len(w) > 7), n),
        "gerundi ‰": per_mille(len(re.findall(r"\b\w+(ando|endo)\b", low)), n),
        "gerundi in coda ‰": per_mille(len(RE_GERUNDIO_CODA.findall(testo)), n),
        "connettivi ‰": per_mille(sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in CONNETTIVI), n),
        "«non (è) solo… ma» ‰": per_mille(len(re.findall(r"\bnon (?:è |era )?solo\b[^.]{0,80}\bma\b", low)), n),
        "lunghezza media parola": round(statistics.mean(len(w) for w in parole(testo)), 2) if parole(testo) else 0,
    }


def cmd_confronta(passaggio, racconto):
    cartella = cartella_racconto(racconto)
    p = Path(passaggio)
    if not p.exists():
        errore(f"passaggio non trovato: {passaggio}")
    nuovo = p.read_text(encoding="utf-8-sig")
    resto = "\n\n".join(t for _, t in testo_racconto(cartella))
    # Se il passaggio è già nel testo, lo si toglie dal termine di confronto.
    resto = resto.replace(nuovo.strip(), "")
    a, b = profilo_testo(nuovo), profilo_testo(resto)
    print(f"# Confronto: {p.name} contro il resto di {cartella.name}\n")
    print(f"Passaggio: {a['parole']} parole · resto del racconto: {b['parole']} parole.")
    if a["parole"] < 80:
        print("Attenzione: sotto le 80 parole le frequenze sono poco affidabili; guarda soprattutto ritmo e formule.\n")
    print("| Misura | Passaggio | Resto | Segnale |")
    print("| --- | ---: | ---: | --- |")
    segnali = 0
    for k in a:
        if k == "parole":
            continue
        va, vb = a[k], b[k]
        segnale = ""
        if k in ("media frase", "deviazione frase", "lunghezza media parola"):
            if vb and (va / vb > 1.3 or va / vb < 0.7):
                segnale = "scarto"
        elif k == "frasi brevi %":
            if abs(va - vb) > 12:
                segnale = "scarto"
        else:
            # Confronto sui conteggi attesi nel passaggio, per non segnalare assenze normali in un testo breve.
            atteso = round(vb * a["parole"] / 1000, 1)
            osservato = round(va * a["parole"] / 1000, 1)
            if (osservato >= 2 and osservato > 2 * max(atteso, 0.5)) or (atteso >= 3 and osservato < atteso / 3):
                segnale = "scarto"
        if segnale:
            segnali += 1
        print(f"| {k} | {va} | {vb} | {segnale} |")
    stil = [m.group(0) for pat in stilemi() for m in re.finditer(pat, nuovo, re.IGNORECASE)]
    print()
    if stil:
        print("Formule di repertorio nel passaggio: " + ", ".join(f"«{s}»" for s in stil))
        segnali += len(stil)
    # Parole frequenti nel passaggio e assenti o rare nel resto.
    fa = Counter(w.lower() for w in parole(nuovo) if len(w) >= 5 and w.lower() not in STOPWORDS)
    fb = Counter(w.lower() for w in parole(resto))
    estranee = [w for w, c in fa.items() if c >= 2 and fb[w] == 0]
    if estranee:
        print("Parole ripetute nel passaggio e assenti nel resto: " + ", ".join(estranee[:10]))
    print()
    print(f"Esito: {'nessuno scarto evidente' if segnali == 0 else str(segnali) + ' segnali da guardare'}. "
          "Uno scarto non è un errore: dice dove il passaggio suona diverso dal racconto.")


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
            "per_capoverso": per_capoverso, "contributi": contributi}


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
