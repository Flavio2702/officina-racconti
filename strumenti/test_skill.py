"""Allineamento tra le skill di .agents/skills/ (Codex) e i rimandi di .claude/skills/ (Claude Code).

Eseguire: python -X utf8 -m unittest discover -s strumenti -p "test_*.py"
Il testo delle skill vive solo in .agents/skills/; i rimandi ripetono name e description
e aggiungono disable-model-invocation solo dove openai.yaml esclude l'invocazione implicita.
"""

from pathlib import Path
import re
import tempfile
import unittest

RADICE = Path(__file__).resolve().parent.parent


def intestazione(percorso):
    """Righe chiave: valore tra i due --- iniziali; nessun YAML generale."""
    testo = percorso.read_text(encoding="utf-8-sig")
    m = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", testo, re.S)
    if not m:
        return None, testo
    dati = {}
    for riga in m.group(1).splitlines():
        if ":" in riga and not riga.startswith((" ", "#")):
            chiave, valore = riga.split(":", 1)
            dati[chiave.strip()] = valore.strip()
    return dati, testo[m.end():]


def solo_esplicita(cartella):
    yaml = cartella / "agents" / "openai.yaml"
    return yaml.exists() and re.search(r"(?m)^\s*allow_implicit_invocation:\s*false\s*(#.*)?$",
                                       yaml.read_text(encoding="utf-8-sig")) is not None


def problemi_allineamento(radice):
    originali = radice / ".agents" / "skills"
    rimandi = radice / ".claude" / "skills"
    nomi_o = {p.parent.name for p in originali.glob("*/SKILL.md")}
    nomi_r = {p.parent.name for p in rimandi.glob("*/SKILL.md")} if rimandi.exists() else set()
    problemi = [f"{n}: manca il rimando in .claude/skills/" for n in sorted(nomi_o - nomi_r)]
    problemi += [f"{n}: rimando senza skill in .agents/skills/" for n in sorted(nomi_r - nomi_o)]
    for nome in sorted(nomi_o):
        dati_o, _ = intestazione(originali / nome / "SKILL.md")
        if dati_o is None:
            problemi.append(f"{nome}: intestazione dell'originale assente")
            continue
        if "disable-model-invocation" in (originali / nome / "SKILL.md").read_text(encoding="utf-8-sig"):
            problemi.append(f"{nome}: disable-model-invocation nell'originale (va solo nel rimando)")
        if nome not in nomi_r:
            continue
        dati_r, corpo_r = intestazione(rimandi / nome / "SKILL.md")
        if dati_r is None:
            problemi.append(f"{nome}: intestazione del rimando assente")
            continue
        for chiave in ("name", "description"):
            if dati_r.get(chiave) != dati_o.get(chiave):
                problemi.append(f"{nome}: {chiave} diverso tra originale e rimando")
        percorso = f".agents/skills/{nome}/SKILL.md"
        if f"`{percorso}`" not in corpo_r:
            problemi.append(f"{nome}: il rimando non cita `{percorso}`")
        manuale = dati_r.get("disable-model-invocation") == "true"
        if solo_esplicita(originali / nome) != manuale:
            problemi.append(f"{nome}: disable-model-invocation non corrisponde a "
                            "allow_implicit_invocation di agents/openai.yaml")
    return problemi


# Codex unisce gli AGENTS.md fino a 32 KiB (project_doc_max_bytes) e oltre smette di aggiungerli:
# 24 KiB lasciano margine a un AGENTS.md globale (regola C4 dello sprint mestiere).
LIMITE_AGENTS = 24 * 1024

# Nomi che valgono in un solo strumento (regola C1): le differenze stanno nelle tabelle di AGENTS.md.
# «/racconto-» è l'invocazione di Claude Code; non conta quando segue una lettera, un punto o una
# barra, come nei percorsi «.agents/skills/racconto-…».
NOMI_DI_UNO_STRUMENTO = [
    (r"(?<![\w./])/racconto-", "/racconto-"),
    (r"WebFetch", "WebFetch"),
    (r"strumento (Agent|Skill)\b", "strumento Agent o Skill"),
    (r"subagente di Claude", "subagente di Claude"),
    (r"Claude Code", "Claude Code"),
    (r"\bCodex\b", "Codex"),
]


# Codex accorcia per prime le descrizioni quando l'elenco delle skill supera il suo spazio;
# Anthropic ammette 1.024 caratteri: vale il vincolo più stretto (regola C3 dello sprint mestiere).
LIMITE_DESCRIZIONE = 400


def problemi_descrizioni(radice):
    """Descrizioni troppo lunghe, o che un lettore YAML non leggerebbe come testo semplice."""
    problemi = []
    for percorso in sorted((radice / ".agents" / "skills").glob("*/SKILL.md"), key=lambda p: p.as_posix()):
        nome = percorso.parent.name
        dati, _ = intestazione(percorso)
        descrizione = (dati or {}).get("description", "")
        if not descrizione:
            problemi.append(f"{nome}: descrizione assente")
        elif len(descrizione) > LIMITE_DESCRIZIONE:
            problemi.append(f"{nome}: descrizione di {len(descrizione)} caratteri (al massimo {LIMITE_DESCRIZIONE})")
        # In YAML «: » e « #» dentro un valore senza virgolette lo spezzano o lo troncano.
        if ": " in descrizione or " #" in descrizione:
            problemi.append(f"{nome}: «: » o « #» nella descrizione; usa un trattino")
    return problemi


def nomi_di_strumento(radice):
    """Occorrenze vietate nei .md di .agents/skills/, fuori dalle righe di citazione («>»)."""
    trovati = []
    # Ordine per stringa: su Windows il confronto fra Path ignora le maiuscole.
    for percorso in sorted((radice / ".agents" / "skills").rglob("*.md"), key=lambda p: p.as_posix()):
        righe = percorso.read_text(encoding="utf-8-sig").splitlines()
        for n, riga in enumerate(righe, 1):
            if riga.lstrip().startswith(">"):
                continue
            for modello, nome in NOMI_DI_UNO_STRUMENTO:
                if re.search(modello, riga):
                    relativo = percorso.relative_to(radice).as_posix()
                    trovati.append(f"{relativo}:{n}: {nome}")
    return trovati


class CompatibilitaTest(unittest.TestCase):
    def test_agents_sotto_il_limite_di_codex(self):
        dimensione = (RADICE / "AGENTS.md").stat().st_size
        self.assertLessEqual(dimensione, LIMITE_AGENTS,
                             f"AGENTS.md è di {dimensione} byte: sposta qualcosa nelle skill o in officina/")

    def test_descrizioni_brevi(self):
        self.assertEqual(problemi_descrizioni(RADICE), [])

    def test_guardia_descrizioni(self):
        with tempfile.TemporaryDirectory(prefix="officina-c3-") as cartella:
            radice = Path(cartella)
            for nome, descrizione in [("a", "x" * LIMITE_DESCRIZIONE), ("b", "x" * (LIMITE_DESCRIZIONE + 1)),
                                      ("c", "Fa C: con due punti."), ("d", "Fa D #1.")]:
                skill = radice / ".agents" / "skills" / nome
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {nome}\ndescription: {descrizione}\n---\n",
                                                encoding="utf-8")
            self.assertEqual(problemi_descrizioni(radice), [
                f"b: descrizione di {LIMITE_DESCRIZIONE + 1} caratteri (al massimo {LIMITE_DESCRIZIONE})",
                "c: «: » o « #» nella descrizione; usa un trattino",
                "d: «: » o « #» nella descrizione; usa un trattino",
            ])

    def test_skill_senza_nomi_di_uno_strumento(self):
        self.assertEqual(nomi_di_strumento(RADICE), [])

    def test_guardia_trova_i_nomi(self):
        with tempfile.TemporaryDirectory(prefix="officina-c1-") as cartella:
            radice = Path(cartella)
            skill = radice / ".agents" / "skills" / "prova"
            (skill / "livelli").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "Usa `/racconto-prova`.\n"
                "Leggi `.agents/skills/racconto-prova/SKILL.md` e `$racconto-prova`.\n"
                "> Oggi non in Claude Code: citazione ammessa.\n"
                "Con lo strumento Agent.\n", encoding="utf-8")
            (skill / "livelli" / "a.md").write_text("Solo in Codex.\n", encoding="utf-8")
            self.assertEqual(nomi_di_strumento(radice), [
                ".agents/skills/prova/SKILL.md:1: /racconto-",
                ".agents/skills/prova/SKILL.md:4: strumento Agent o Skill",
                ".agents/skills/prova/livelli/a.md:1: Codex",
            ])


class SkillProgettoTest(unittest.TestCase):
    def test_progetto_allineato(self):
        self.assertTrue(list((RADICE / ".agents" / "skills").glob("*/SKILL.md")))
        self.assertEqual(problemi_allineamento(RADICE), [])

    def test_manuali_attese(self):
        manuali = {p.parent.name for p in (RADICE / ".agents" / "skills").glob("*/SKILL.md")
                   if solo_esplicita(p.parent)}
        self.assertEqual(manuali, {"racconto-scrittura", "racconto-voce"})


class SkillFixtureTest(unittest.TestCase):
    """Il controllo deve accorgersi di ogni disallineamento, non solo passare sul progetto."""

    def setUp(self):
        temporanea = tempfile.TemporaryDirectory(prefix="officina-skill-")
        self.addCleanup(temporanea.cleanup)
        self.radice = Path(temporanea.name)
        self.originale("prova-a", "Fa A: con due punti e l'apostrofo.")
        self.originale("prova-b", "Fa B.", manuale=True)
        self.rimando("prova-a", "Fa A: con due punti e l'apostrofo.")
        self.rimando("prova-b", "Fa B.", manuale=True)

    def scrivi(self, percorso, testo):
        percorso.parent.mkdir(parents=True, exist_ok=True)
        percorso.write_text(testo, encoding="utf-8")

    def originale(self, nome, descrizione, manuale=False, extra=""):
        base = self.radice / ".agents" / "skills" / nome
        self.scrivi(base / "SKILL.md",
                    f"---\nname: {nome}\ndescription: {descrizione}\n{extra}---\n\n# {nome}\n")
        if manuale:
            self.scrivi(base / "agents" / "openai.yaml",
                        "interface:\n  display_name: \"X\"\npolicy:\n  allow_implicit_invocation: false\n")

    def rimando(self, nome, descrizione, manuale=False, percorso=None):
        chiave = "disable-model-invocation: true\n" if manuale else ""
        percorso = percorso or f".agents/skills/{nome}/SKILL.md"
        self.scrivi(self.radice / ".claude" / "skills" / nome / "SKILL.md",
                    f"---\nname: {nome}\ndescription: {descrizione}\n{chiave}---\n\n"
                    f"# {nome}\n\nQuesta skill vive in `{percorso}`.\n")

    def problemi(self):
        return problemi_allineamento(self.radice)

    def test_allineata(self):
        self.assertEqual(self.problemi(), [])

    def test_rimando_mancante(self):
        self.originale("prova-c", "Fa C.")
        self.assertEqual(self.problemi(), ["prova-c: manca il rimando in .claude/skills/"])

    def test_rimando_orfano(self):
        self.rimando("prova-d", "Fa D.")
        self.assertEqual(self.problemi(), ["prova-d: rimando senza skill in .agents/skills/"])

    def test_descrizione_diversa_di_un_carattere(self):
        self.rimando("prova-a", "Fa A: con due punti e l’apostrofo.")
        self.assertEqual(self.problemi(), ["prova-a: description diverso tra originale e rimando"])

    def test_percorso_non_citato(self):
        self.rimando("prova-a", "Fa A: con due punti e l'apostrofo.",
                     percorso=".agents/skills/altra/SKILL.md")
        self.assertEqual(self.problemi(),
                         ["prova-a: il rimando non cita `.agents/skills/prova-a/SKILL.md`"])

    def test_manuale_senza_chiave(self):
        self.rimando("prova-b", "Fa B.")
        self.assertIn("prova-b: disable-model-invocation non corrisponde", self.problemi()[0])

    def test_chiave_su_skill_automatica(self):
        self.rimando("prova-a", "Fa A: con due punti e l'apostrofo.", manuale=True)
        self.assertIn("prova-a: disable-model-invocation non corrisponde", self.problemi()[0])

    def test_chiave_nell_originale(self):
        self.originale("prova-a", "Fa A: con due punti e l'apostrofo.",
                       extra="disable-model-invocation: true\n")
        self.assertEqual(self.problemi(),
                         ["prova-a: disable-model-invocation nell'originale (va solo nel rimando)"])


if __name__ == "__main__":
    unittest.main()
