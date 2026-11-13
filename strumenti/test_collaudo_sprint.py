"""Percorsi integrati dello sprint, sempre su racconti temporanei sintetici."""

import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import prosa


class CollaudoSprint(unittest.TestCase):
    def setUp(self):
        temporanea = tempfile.TemporaryDirectory(prefix="officina-collaudo-")
        self.addCleanup(temporanea.cleanup)
        self.radice = Path(temporanea.name) / "progetto città con spazi"
        self.radice.mkdir()
        self.racconti = self.radice / "racconti"
        self.racconti.mkdir()
        modello = self.racconti / "_modello"
        modello.mkdir()
        originale = Path(prosa.__file__).resolve().parent.parent / "racconti" / "_modello"
        for nome in ("scheda.md", "stato.md"):
            shutil.copyfile(originale / nome, modello / nome)
        for nome, valore in (("RADICE", self.radice), ("RACCONTI", self.racconti),
                             ("MODELLO", modello)):
            modifica = patch.object(prosa, nome, valore)
            modifica.start()
            self.addCleanup(modifica.stop)

    def comando(self, *argomenti):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            prosa.main(["prosa.py", *map(str, argomenti)])
        return output.getvalue()

    def crea(self, nome, modalita, testo):
        self.comando("nuovo", nome)
        cartella = self.racconti / nome
        fonte = self.radice / "bozze con spazi" / f"città {nome}.md"
        fonte.parent.mkdir(exist_ok=True)
        fonte.write_text(testo, encoding="utf-8")
        scheda = cartella / "scheda.md"
        dati = scheda.read_text(encoding="utf-8")
        dati = dati.replace("modalita: breve", f"modalita: {modalita}")
        dati = dati.replace("fonte_file:              #", f'fonte_file: "{fonte.relative_to(self.radice).as_posix()}" #')
        scheda.write_text(dati, encoding="utf-8")
        fonte_dichiarata = json.loads(self.comando("fonte", nome))
        self.assertEqual(fonte_dichiarata["fonte_file"], str(fonte))
        self.assertEqual(fonte_dichiarata["modalita"], modalita)
        self.comando("importa", fonte, nome)
        return cartella, fonte

    def test_quattro_percorsi_locali_e_comandi_pubblici(self):
        self.assertIn("nuovo", self.comando("aiuto"))
        breve, _ = self.crea("bozza-breve", "breve", "# Città\n\nÈ sera.\n\n— Torni?\n")
        self.assertIn("Battute", self.comando("conta", breve))
        self.assertIn("# Controlli", self.comando("controlla", breve))
        self.assertIn("# Dialoghi", self.comando("dialoghi", breve))
        passaggio = self.radice / "passaggio città.md"
        passaggio.write_text("È sera.", encoding="utf-8")
        self.assertIn("# Confronto", self.comando("confronta", passaggio, breve))
        self.assertIn("testo intero", self.comando("dividi", breve))
        self.comando("unisci", breve)
        self.assertEqual((breve / "testo-unito.md").read_bytes(), (breve / "testo.md").read_bytes())

        lunga, _ = self.crea("bozza-lunga", "lunga", "Prima scena.\n\n* * *\n\nSeconda scena.\n")
        self.assertEqual(len(list((lunga / "scene").glob("*.md"))), 2)
        totale = self.comando("conta", lunga)
        self.comando("dividi", lunga)
        self.assertEqual(self.comando("conta", lunga), totale)

        senza, _ = self.crea("lunga-senza-stacchi", "lunga", "Una scena continua.\n\nAncora qui.\n")
        self.assertEqual(list((senza / "scene").glob("*.md")), [])
        self.comando("unisci", senza)
        self.assertEqual((senza / "testo-unito.md").read_bytes(), (senza / "testo.md").read_bytes())

        cambiata, fonte = self.crea("stacchi-variabili", "lunga", "Prima.\n\n* * *\n\nSeconda.\n")
        self.assertEqual(len(list((cambiata / "scene").glob("*.md"))), 2)
        fonte.write_text("Testo continuo.\n", encoding="utf-8")
        self.comando("importa", fonte, cambiata)
        self.assertEqual(list((cambiata / "scene").glob("*.md")), [])
        fonte.write_text("Uno.\n\n* * *\n\nDue.\n\n* * *\n\nTre.\n", encoding="utf-8")
        self.comando("importa", fonte, cambiata)
        self.assertEqual(len(list((cambiata / "scene").glob("*.md"))), 3)

    def test_due_report_due_varianti_e_consegna_rileggibile(self):
        cartella, _ = self.crea("consegna", "breve", "È sera.\n")
        self.comando("controlla", cartella, "--salva")
        self.comando("controlla", cartella, "--salva")
        report = sorted((cartella / "revisioni").glob("*-controlli*.md"))
        self.assertEqual(len(report), 2)
        self.assertEqual(sum(p.stem.endswith("-02") for p in report), 1)
        materiali = cartella / "materiali"
        prima = prosa.salva_univoco(materiali, "2026-09-25-variante.md", "Stato: proposta\nPunto: finale\n\nVariante A.\n")
        seconda = prosa.salva_univoco(materiali, "2026-09-25-variante.md", "Stato: non approvata\nPunto: finale\n\nVariante B.\n")
        self.assertEqual(seconda.stem, "2026-09-25-variante-02")
        stato = cartella / "stato.md"
        testo = stato.read_text(encoding="utf-8")
        riferimenti = [prima.relative_to(cartella), seconda.relative_to(cartella), report[0].relative_to(cartella), report[1].relative_to(cartella)]
        nota = "\n".join(f"- {p.as_posix()}" for p in riferimenti)
        nota += "\n- Terza proposta: testo integrale mancante; richiederlo all'autore, non ricostruirlo.\n"
        stato.write_text(testo.replace("## Prossimo passo", nota + "\n## Prossimo passo"), encoding="utf-8")
        ripresa = stato.read_text(encoding="utf-8")
        self.assertTrue(all(str(p.as_posix()) in ripresa and (cartella / p).exists() for p in riferimenti))
        self.assertIn("testo integrale mancante", ripresa)
        self.assertIn("non ricostruirlo", ripresa)


if __name__ == "__main__":
    unittest.main()
