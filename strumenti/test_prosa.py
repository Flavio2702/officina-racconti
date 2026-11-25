"""Regressioni dello sprint, solo con fixture sintetiche temporanee.

Eseguire: python -X utf8 -m unittest discover -s strumenti -p "test_*.py"
I difetti ancora aperti sono FAIL, non expectedFailure: una correzione deve
far passare il test senza cambiarne l'aspettativa. Vedi il registro dello sprint.
"""

import contextlib
import hashlib
import io
import json
import os
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import prosa


class ProsaTest(unittest.TestCase):
    def setUp(self):
        temporanea = tempfile.TemporaryDirectory(prefix="officina-test-")
        self.addCleanup(temporanea.cleanup)
        self.radice = Path(temporanea.name)
        self.cartella = self.radice / "racconti" / "città di prova"
        self.cartella.mkdir(parents=True)
        # Anche risoluzioni per nome e risorse opzionali restano nella fixture.
        for nome, valore in (("RADICE", self.radice),
                             ("RACCONTI", self.radice / "racconti")):
            modifica = patch.object(prosa, nome, valore)
            modifica.start()
            self.addCleanup(modifica.stop)
        self.scheda("breve")
        self.scrivi("testo.md", "È sera. «Già qui?»\n")

    def scrivi(self, nome, testo):
        percorso = self.cartella / nome
        percorso.parent.mkdir(parents=True, exist_ok=True)
        percorso.write_text(testo, encoding="utf-8")
        return percorso

    def scheda(self, modalita):
        self.scrivi("scheda.md", f"---\nmodalita: {modalita}\n---\n")

    def cattura(self, funzione, *args, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            funzione(*args, **kwargs)
        return out.getvalue()

    def totali(self):
        output = self.cattura(prosa.cmd_conta, str(self.cartella))
        righe = []
        for riga in output.splitlines():
            celle = [c.strip().replace("**", "") for c in riga.split("|")]
            if len(celle) == 5 and celle[2].isdigit() and celle[3].isdigit():
                righe.append((celle[1], int(celle[2]), int(celle[3])))
        self.assertTrue(righe, "Nessuna riga numerica nel report conta")
        totali = [r[1:] for r in righe if r[0].casefold() == "totale"]
        if totali:
            self.assertEqual(len(totali), 1)
            return totali[0]
        self.assertEqual(len(righe), 1, "Più parti senza totale esplicito")
        return righe[0][1:]

    def docx(self, corpo):
        # Pacchetto minimo per il lettore XML locale, non fixture di impaginazione Word.
        percorso = self.radice / "bozza città.docx"
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
               'wordprocessingml/2006/main"><w:body>' + corpo +
               '</w:body></w:document>')
        with zipfile.ZipFile(percorso, "w") as archivio:
            archivio.writestr("word/document.xml", xml.encode("utf-8"))
        return percorso

    def leggi_docx(self, percorso):
        # Gli avvisi DOCX fanno parte del contratto: si verificano invece di stamparli.
        with contextlib.redirect_stderr(io.StringIO()) as err:
            testo = prosa.leggi_docx(percorso)
        self.assertIn("corsivo diretto dei run", err.getvalue())
        return testo

    def importa(self, percorso):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        if Path(percorso).suffix == ".docx":
            self.assertIn("corsivo diretto dei run", err.getvalue())
        return (self.cartella / "testo.md").read_text(encoding="utf-8")

    def test_conta_testo_semplice(self):
        self.scrivi("testo.md", "È sera.")
        self.assertEqual(self.totali(), (2, 7))

    def test_conta_intero_e_scene_stesso_totale(self):
        self.scrivi("testo.md", "Prima scena.\n\n* * *\n\nSeconda scena.\n")
        intero = self.totali()
        self.scheda("lunga")
        self.cattura(prosa.dividi, self.cartella)
        self.assertEqual(self.totali(), intero)  # 2.3

    def test_conta_ignora_scene_obsolete(self):
        self.scrivi("testo.md", "È sera.")
        self.scheda("lunga")
        self.scrivi("scene/01.md", "Vecchia copia molto più lunga.")
        self.assertEqual(self.totali(), (2, 7))  # 2.3

    def test_conta_marcatori_markdown(self):
        self.scrivi("testo.md", "# Titolo\n\n*È sera.* [Qui](https://example.test)\n\n* * *\n")
        self.assertEqual(self.totali(), (4, 17))  # 2.1–2.2: Titolo (6) + È sera. Qui (11)

    def test_conta_asterischi_letterali(self):
        self.scrivi("testo.md", r"Il segno \* resta.")
        self.assertEqual(self.totali(), (3, 17))  # 1.6, 2.1

    def test_conta_a_capo_esclusi(self):
        self.scrivi("testo.md", "Uno.\n\nDue.\n")
        self.assertEqual(self.totali(), (2, 8))  # 2.2

    def test_conta_unicode_spazi_e_tabulazioni(self):
        self.scrivi("testo.md", "E\u0300\tqui.\u00a0 A\u202fB  \r\n")
        self.assertEqual(self.totali(), (4, len("È qui.  A B  ")))
        self.assertEqual(prosa.conta_battute("🙂"), 1)

    def test_conta_enfasi_titoli_link(self):
        casi = [
            ("*È* **sera** ***qui***", "È sera qui"),
            ("_È_ __sera__ ___qui___", "È sera qui"),
            ("**Una *sera* bella**", "Una sera bella"),
            ("# Un titolo ###\n## Altro", "Un titolo\nAltro"),
            ("[Una **sera**](https://example.test/a_(b))", "Una sera"),
            ("nome_file e 2 * 3", "nome_file e 2 * 3"),
            ("* * *\n****\n*  *  *  *\nFine", "\n\n\nFine"),
        ]
        for origine, atteso in casi:
            with self.subTest(origine=origine):
                self.assertEqual(prosa.testo_visibile(origine), atteso)

    def test_conta_escape_letterali_non_reinterpretati(self):
        casi = [(r"\*sera\*", "*sera*"),
                (r"\# Titolo", "# Titolo"),
                (r"\[qui\](url)", "[qui](url)"),
                (r"\* \* \*", "* * *"),
                (r"a\_b \\ \` \q", "a_b \\ ` \\q"),
                ("\ue000 " + r"\*", "\ue000 *")]
        for origine, atteso in casi:
            with self.subTest(origine=origine):
                self.assertEqual(prosa.testo_visibile(origine), atteso)
                self.assertEqual(prosa.conta_battute(origine), len(atteso))

    def test_conta_titolo_solo_in_scheda_e_limite_locale(self):
        self.scrivi("scheda.md", "---\ntitolo: Titolo non nel corpo\nmodalita: breve\nlimite_battute: 5\n---\n")
        self.scrivi("testo.md", "È sera.")
        self.assertEqual(self.totali(), (2, 7))
        report = self.cattura(prosa.cmd_conta, str(self.cartella))
        self.assertIn("oltre di 2", report)
        self.assertIn("convenzione locale", report)
        self.assertIn("NFC", report)
        self.assertIn("bando", report)
        self.assertIn("Non è verificata l'equivalenza con Google Docs", report)

    def test_conta_intero_con_titoli_spazi_e_scene_manomesse(self):
        testo = "  Prima.  \n\n# Seconda scena\n*È* qui.\n* * *\n  Fine.  \n"
        self.scrivi("testo.md", testo)
        atteso = (6, len("  Prima.  Seconda scenaÈ qui.  Fine.  "))
        self.assertEqual(self.totali(), atteso)
        self.cattura(prosa.dividi, self.cartella)
        for modalita in ("breve", "lunga"):
            self.scheda(modalita)
            self.scrivi("scene/01.md", "Alterata.")
            self.scrivi("scene/99.md", "Obsoleta.")
            self.assertEqual(self.totali(), atteso)
            self.assertEqual(prosa.testo_racconto(self.cartella), [("testo.md", testo)])

    def test_conta_vuoto_e_soli_separatori(self):
        for testo in ("", "\n\n", "***\n\n* * *\n"):
            self.scrivi("testo.md", testo)
            self.assertEqual(self.totali(), (0, 0))

    def test_dividi_lungo_senza_stacchi_non_blocca(self):
        self.scheda("lunga")
        self.scrivi("scene/01.md", "Vecchia.")
        report = self.cattura(prosa.cmd_dividi, str(self.cartella))
        self.assertEqual(list((self.cartella / "scene").glob("*.md")), [])
        self.assertNotIn("Aggiungili", report)
        self.assertEqual(prosa.testo_racconto(self.cartella)[0][1], "È sera. «Già qui?»\n")

    def test_dividi_escape_non_creano_scene(self):
        self.scrivi("testo.md", "Prima\n\\* \\* \\*\n\\# Titolo\nFine")
        self.cattura(prosa.dividi, self.cartella)
        self.assertEqual(list((self.cartella / "scene").glob("*.md")), [])

    def test_unisci_ignora_scene_e_conserva_byte(self):
        originale = "# Titolo\r\n\r\n  È *sera*.  \r\n* * *\r\nFine".encode("utf-8")
        (self.cartella / "testo.md").write_bytes(originale)
        self.scrivi("scene/01.md", "Alterata.")
        self.scrivi("scene/99.md", "Obsoleta.")
        self.cattura(prosa.cmd_unisci, str(self.cartella))
        self.assertEqual((self.cartella / "testo-unito.md").read_bytes(), originale)

    def test_unisci_senza_copia_non_usa_scene(self):
        (self.cartella / "testo.md").unlink()
        self.scrivi("scene/01.md", "Obsoleta.")
        self.scrivi("testo-unito.md", "Derivato precedente.")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.cattura(prosa.cmd_unisci, str(self.cartella))
        self.assertEqual((self.cartella / "testo-unito.md").read_text(encoding="utf-8"),
                         "Derivato precedente.")

    def test_lineette_contate_una_volta(self):
        self.assertEqual(prosa.conta_convenzioni("— Ciao.\n— Addio.")["lineette"], 2)  # 3.1

    def test_trattini_contati_una_volta(self):
        self.assertEqual(prosa.conta_convenzioni("- Ciao.\n- Addio.")["trattini"], 2)  # 3.1

    def test_inciso_ambiguo(self):
        _, semplice, motivo = prosa.converti_riga_lineette("— Era — forse — troppo tardi.")
        self.assertFalse(semplice, "L'inciso deve restare da valutare (3.2–3.3)")
        self.assertTrue(motivo)

    def test_citazione_annidata_da_valutare(self):
        _, semplice, motivo = prosa.converti_riga_lineette("— Ha detto «torna».")
        self.assertFalse(semplice)
        self.assertTrue(motivo)

    def test_dialoghi_interni_e_scelte_restano_da_valutare(self):
        for riga in ("— Lo so — disse. — Torno.", "— Era — forse — troppo tardi."):
            with self.subTest(riga=riga):
                _, semplice, motivo = prosa.converti_riga_lineette(riga)
                self.assertFalse(semplice)
                self.assertIn("separatore interno", motivo)
        proposta, _, _ = prosa.converti_riga_lineette("— Vieni, — disse.")
        self.assertIn("Vieni,»", proposta)  # virgola originale non eliminata
        self.scrivi("scheda.md", "---\ndialoghi: lineette\n---\n## Scelte di questo racconto\nLineette mantenute.\n")
        self.scrivi("testo.md", "— Vieni.\n")
        originale = (self.cartella / "testo.md").read_bytes()
        report = self.cattura(prosa.cmd_dialoghi, str(self.cartella))
        self.assertIn("Lineette mantenute", report)
        self.assertIn("Proposte semplici da verificare (0)", report)
        self.assertIn("originale: — Vieni.", report)
        self.assertEqual((self.cartella / "testo.md").read_bytes(), originale)
        self.assertFalse((self.cartella / "materiali").exists())
        self.scrivi("scheda.md", "---\ndialoghi: caporali\n---\n## Scelte di questo racconto\nDeroga: lineette mantenute.\n")
        report = self.cattura(prosa.cmd_dialoghi, str(self.cartella))
        self.assertIn("Proposte semplici da verificare (0)", report)

    def test_convenzioni_contano_segni_ma_non_diagnosticano_misto(self):
        self.scrivi("testo.md", "«Vai?» — disse.\n— Torno.\n- Forse.\n")
        conv = prosa.conta_convenzioni((self.cartella / "testo.md").read_text(encoding="utf-8"))
        self.assertEqual((conv["caporali"], conv["lineette"], conv["trattini"]), (1, 2, 1))
        report = self.cattura(prosa.cmd_controlla, str(self.cartella))
        self.assertIn("non di battute né prova di convenzioni miste", report)
        self.assertNotIn("convenzioni nello stesso testo", report)

    def test_virgolette_dritte_e_puntini(self):
        self.assertEqual(prosa.togli_dialoghi('Lei disse "torno" e camminò.\n«Ciao»'),
                         "Lei disse   e camminò.\n ")
        refusi = prosa.controlli("Aspetta.. Il valore è 3.14. Basta....", {})["refusi"]
        self.assertEqual(sum("puntini" in spieg for spieg, _, _ in refusi), 2)

    def test_ricorrenti_escluse_dagli_echi_e_frequenze_descrittive(self):
        testo = "camminava camminando. casa case. corrente correnti."
        dati = {"ricorrenti": "Camminava"}
        risultato = prosa.controlli(testo, dati)
        self.assertNotIn("camminava", [w for w, _ in risultato["echi"]])
        self.assertIn("correnti", [w for w, _ in risultato["echi"]])
        self.assertNotIn("casa", [w for w, _ in risultato["echi"]])
        self.scrivi("testo.md", testo)
        self.scrivi("scheda.md", "---\nricorrenti: Camminava\n---\n")
        report = self.cattura(prosa.cmd_controlla, str(self.cartella))
        self.assertIn("Frequenze descrittive", report)
        self.assertIn("Confronto di prefissi", report)

    def test_stilemi_extra_in_confronta_e_regex_non_valida(self):
        self.scrivi("testo.md", "Resto del racconto senza la formula.\n")
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("Un cielo opaco. Un cielo opaco.", encoding="utf-8")
        extra = self.radice / "strumenti" / "stilemi_extra.txt"
        extra.parent.mkdir()
        extra.write_text("cielo opaco\n", encoding="utf-8")
        report = self.cattura(prosa.cmd_confronta, str(passaggio), str(self.cartella))
        self.assertIn("«cielo opaco»", report)
        extra.write_text("[\n", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            prosa.controlli("Testo.", {})
        self.assertIn("regex non valida", err.getvalue())
        self.assertIn("riga 1", err.getvalue())

    # Controlli di lingua: officina/punteggiatura-e-ritmo.md e officina/lessico-e-figure.md.

    def refusi_di(self, testo):
        return [spieg for spieg, _, _ in prosa.controlli(testo, {})["refusi"]]

    def test_virgola_tra_verbo_e_oggettiva(self):
        self.assertTrue(any("oggettiva" in s for s in self.refusi_di("Così ho capito, che era tardi.")))
        self.assertFalse(any("oggettiva" in s for s in self.refusi_di("Così ho capito che era tardi.")))
        self.assertFalse(any("oggettiva" in s for s in self.refusi_di("Penso che, se vuoi, sia tardi.")))
        # Dislocazione a destra con ripresa del pronome: uso medio, non virgola nel nucleo.
        for frase in ("Lo so, che sei stanco.", "L'ho capito, che era tardi.", "Non lo so, che dire."):
            self.assertFalse(any("oggettiva" in s for s in self.refusi_di(frase)), frase)
        self.assertFalse(any("oggettiva" in s for s in self.refusi_di("Penso, e lo dico, che sia tardi.")))
        # Limite dichiarato in officina/punteggiatura-e-ritmo.md: un inciso che si chiude su un
        # verbo dell'elenco («è lui, dice, che…») resta un candidato da leggere.
        self.assertTrue(any("oggettiva" in s for s in self.refusi_di("È lui, dice, che ha cominciato.")))
        self.assertFalse(any("oggettiva" in s for s in self.refusi_di("Lo vedo spesso, che peccato.")))

    def test_segni_doppi(self):
        self.assertTrue(any("segni doppi" in s for s in self.refusi_di("Davvero?! Sì!!")))
        self.assertTrue(any("segni doppi" in s for s in self.refusi_di("Cosa importa\\!\\! basta.")))
        self.assertFalse(any("segni doppi" in s for s in self.refusi_di("Davvero? Sì! Basta.")))

    def test_antilingua_e_piuttosto_che_solo_in_narrazione(self):
        r = prosa.controlli("Effettuò una telefonata. Prendo il treno piuttosto che l'auto.\n\n"
                            "«Abbiamo effettuato il controllo nel momento in cui è arrivato.»\n", {})
        trovate = [(s.lower(), riga, tipo) for s, riga, _, tipo in r["lessico"]]
        self.assertEqual(trovate, [("effettuò", 1, "antilingua"), ("piuttosto che", 1, "piuttosto che")])
        self.assertEqual(prosa.controlli("Fece una telefonata.\n— Effettuò il controllo.\n", {})["lessico"], [])

    def test_maschera_dialoghi_conserva_posizioni(self):
        testo = "Uno «due» tre.\n— Quattro.\nCinque."
        mascherato = prosa.maschera_dialoghi(testo)
        self.assertEqual(len(mascherato), len(testo))
        self.assertEqual(mascherato.count("\n"), 2)
        self.assertNotIn("due", mascherato)
        self.assertNotIn("Quattro", mascherato)
        self.assertIn("Cinque", mascherato)

    def test_tratto_uniforme_e_attacchi(self):
        uniforme = " ".join("Il cane corre nel prato verde." for _ in range(6))
        uniformi, _ = prosa.ritmo_locale(uniforme)
        self.assertEqual([(n, a, b) for _, n, a, b in uniformi], [(6, 6, 6)])
        variato = ("Il cane corre. Il cane corre nel prato verde sotto la pioggia fitta di novembre. "
                   "Corre. Il cane corre nel prato. Poi si ferma. Il cane corre ancora.")
        self.assertEqual(prosa.ritmo_locale(variato)[0], [])
        _, attacchi = prosa.ritmo_locale("Poi venne. Poi andò via. Poi tornò. Ma dopo tacque.")
        self.assertEqual([(w, n) for _, w, n in attacchi], [("Poi", 3)])
        # Gli articoli in testa non fanno anafora; una battuta interrompe la serie.
        self.assertEqual(prosa.ritmo_locale("Il sole. Il mare. Il vento.")[1], [])
        self.assertEqual(prosa.ritmo_locale("Poi venne. «Poi?» Poi andò. Poi tornò.")[1], [])

    def test_accumuli_di_similitudini(self):
        totale, luoghi = prosa.accumuli_similitudini("Era come un muro, come se aspettasse qualcuno.")
        self.assertEqual((totale, [d for _, d, _ in luoghi]), (2, ["nella stessa frase"]))
        sparse = ("Era come un muro. " + "Poi la sera passò lenta sulla piazza vuota. " * 30 +
                  "Rideva come un bambino. " + "Poi la sera passò lenta sulla piazza vuota. " * 30 +
                  "Correva come se fosse tardi.")
        self.assertEqual(prosa.accumuli_similitudini(sparse), (3, []))
        vicine = "Era come un muro. Rideva come un bambino. Correva come se fosse tardi."
        self.assertIn("3 entro 120 parole dello stesso capoverso",
                      [d for _, d, _ in prosa.accumuli_similitudini(vicine)[1]])

    def test_sezioni_nuove_solo_con_risultati(self):
        self.scrivi("testo.md", "La sera era calda. Lei aprì la finestra e guardò la strada.\n")
        report = self.cattura(prosa.cmd_controlla, str(self.cartella))
        for sezione in ("Ritmo locale", "Lessico da guardare", "Accumuli di similitudini"):
            self.assertNotIn(sezione, report)
        self.assertIn("Un solo capoverso", report)
        self.scrivi("testo.md", "Poi venne. Poi andò. Poi tornò. Effettuò un giro, come un cane, "
                                "come se avesse fretta.\n\nDopo.\n")
        report = self.cattura(prosa.cmd_controlla, str(self.cartella))
        for sezione in ("Ritmo locale", "Lessico da guardare", "Accumuli di similitudini"):
            self.assertIn(sezione, report)
        self.assertIn("2 capoversi", report)

    def test_terne_in_confronta(self):
        self.scrivi("testo.md", "Resto del racconto, senza elenchi.\n")
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("Pane, vino e sale. Luce, ombra e vento.", encoding="utf-8")
        report = self.cattura(prosa.cmd_confronta, str(passaggio), str(self.cartella))
        self.assertIn("| terne ‰ |", report)
        self.assertEqual(len(prosa.RE_TERNA.findall("Pane, vino e sale. Luce, ombra e vento.")), 2)

    def test_docx_corsivo_attivo(self):
        percorso = self.docx('<w:p><w:r><w:t xml:space="preserve">È </w:t></w:r>'
                             '<w:r><w:rPr><w:i/></w:rPr><w:t>sera</w:t></w:r>'
                             '<w:r><w:t>.</w:t></w:r></w:p>')
        self.assertEqual(self.leggi_docx(percorso), "È *sera*.")  # 1.5

    def test_docx_corsivo_disattivato(self):
        percorso = self.docx('<w:p><w:r><w:rPr><w:i w:val="0"/></w:rPr>'
                             '<w:t>Normale.</w:t></w:r></w:p>')
        self.assertEqual(self.leggi_docx(percorso), "Normale.")

    def test_docx_interruzioni_e_tabulazioni(self):
        percorso = self.docx('<w:p><w:r><w:t>Uno</w:t><w:br/><w:t>Due</w:t>'
                             '<w:tab/><w:t>Tre</w:t><w:cr/><w:t>Quattro</w:t>'
                             '</w:r></w:p><w:p><w:r><w:t>Fine.</w:t></w:r></w:p>')
        self.assertEqual(self.leggi_docx(percorso), "Uno\nDue\tTre\nQuattro\n\nFine.")  # 1.5

    def test_importa_docx_preserva_corsivo(self):
        percorso = self.docx('<w:p><w:r><w:rPr><w:i/></w:rPr><w:t>Città</w:t>'
                             '</w:r></w:p>')
        self.importa(percorso)
        self.assertEqual((self.cartella / "testo.md").read_text(encoding="utf-8"), "*Città*\n")

    def test_importa_senza_stacchi_elimina_scene_obsolete(self):
        self.scheda("lunga")
        self.scrivi("scene/01.md", "Vecchia scena.")
        sorgente = self.radice / "bozza città.txt"
        sorgente.write_text("È sera.\n", encoding="utf-8")
        self.cattura(prosa.cmd_importa, str(sorgente), str(self.cartella))
        self.assertEqual(list((self.cartella / "scene").glob("*.md")), [])
        self.assertEqual(prosa.testo_racconto(self.cartella), [("testo.md", "È sera.\n")])

    def test_unisci_senza_scene(self):
        self.scheda("lunga")
        originale = (self.cartella / "testo.md").read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                self.cattura(prosa.cmd_unisci, str(self.cartella))
            except SystemExit as exc:
                self.fail(f"unisci deve usare testo.md anche senza scene (2.6); uscita {exc.code}")
        self.assertEqual((self.cartella / "testo-unito.md").read_bytes(), originale)

    def verifica_collisioni(self, comando, sottocartella, suffisso):
        with patch.object(prosa, "oggi", return_value="2026-09-24"):
            self.cattura(comando, str(self.cartella), salva=True)
            primo = self.cartella / sottocartella / f"2026-09-24-{suffisso}.md"
            precedente = primo.read_bytes()
            self.scrivi("testo.md", "— Un'altra battuta.\n")
            self.cattura(comando, str(self.cartella), salva=True)
            self.cattura(comando, str(self.cartella), salva=True)
        attesi = {primo.name, f"2026-09-24-{suffisso}-02.md", f"2026-09-24-{suffisso}-03.md"}
        self.assertEqual({p.name for p in primo.parent.glob("*.md")}, attesi)  # 4.3
        self.assertEqual(primo.read_bytes(), precedente)

    def test_collisioni_report_controlli(self):
        self.verifica_collisioni(prosa.cmd_controlla, "revisioni", "controlli")

    def test_collisioni_anteprime_dialoghi(self):
        self.verifica_collisioni(prosa.cmd_dialoghi, "materiali", "dialoghi-anteprima")

    def test_report_identifica_la_copia_e_non_inventa_la_revisione(self):
        self.scrivi("scheda.md", "---\ndoc: https://example.test/doc\nmodalita: breve\n---\n")
        primo = self.cartella / "testo.md"
        impronta = hashlib.sha256(primo.read_bytes()).hexdigest()
        self.cattura(prosa.cmd_controlla, str(self.cartella), salva=True)
        report = (self.cartella / "revisioni" / f"{prosa.oggi()}-controlli.md").read_text(encoding="utf-8")
        self.assertIn(f"SHA-256 di testo.md: `{impronta}`", report)
        self.assertIn("https://example.test/doc", report)
        self.assertIn("Revisione Docs della copia: non disponibile", report)
        self.assertIn("Generato: ", report)
        anteprima = self.cattura(prosa.cmd_dialoghi, str(self.cartella), salva=True)
        self.assertIn(f"SHA-256 di testo.md: `{impronta}`", anteprima)
        self.scrivi("testo.md", "Testo cambiato.\n")
        self.cattura(prosa.cmd_controlla, str(self.cartella), salva=True)
        secondo = (self.cartella / "revisioni" / f"{prosa.oggi()}-controlli-02.md").read_text(encoding="utf-8")
        self.assertIn(f"SHA-256 di testo.md: `{impronta}`", report)
        self.assertNotIn(f"SHA-256 di testo.md: `{impronta}`", secondo)

    def test_salvataggio_esclusivo_supera_nomi_occupati(self):
        cartella = self.cartella / "materiali"
        cartella.mkdir()
        (cartella / "proposta.md").write_text("precedente", encoding="utf-8")
        (cartella / "proposta-02.md").write_text("altra", encoding="utf-8")
        creato = prosa.salva_univoco(cartella, "proposta.md", "nuova")
        self.assertEqual(creato.name, "proposta-03.md")
        self.assertEqual((cartella / "proposta.md").read_text(encoding="utf-8"), "precedente")

    def test_main_con_flussi_sostituiti(self):
        with contextlib.redirect_stderr(io.StringIO()):
            output = self.cattura(prosa.main, ["prosa.py", "aiuto"])
        self.assertIn("è", output)

    def test_fonte_solo_metadati_e_sola_lettura(self):
        self.scrivi("scheda.md", '---\ndoc: "https://example.test/doc#tab"\n'
                    'fonte_file: "bozze/città nuova.docx"\nmodalita: "lunga" # (dedotto)\n'
                    'pov: segreto\n---\n## Taciuto\nNon divulgare.\n')
        prima = {p.name: p.read_bytes() for p in self.cartella.iterdir() if p.is_file()}
        output = self.cattura(prosa.main, ["prosa.py", "fonte", str(self.cartella)])
        self.assertEqual(json.loads(output), {
            "doc": "https://example.test/doc#tab", "modalita": "lunga",
            "fonte_file": str((self.radice / "bozze/città nuova.docx").resolve())})
        self.assertEqual(prima, {p.name: p.read_bytes() for p in self.cartella.iterdir() if p.is_file()})

    def test_fonte_assoluta_e_senza_fonti(self):
        percorso = self.radice / "città nuova.txt"
        self.scrivi("scheda.md", f"---\nfonte_file: '{percorso}'\nmodalita: breve\n---\n")
        self.assertEqual(json.loads(self.cattura(prosa.cmd_fonte, str(self.cartella)))["fonte_file"], str(percorso.resolve()))
        self.scheda("breve")
        self.assertEqual(json.loads(self.cattura(prosa.cmd_fonte, str(self.cartella))),
                         {"doc": "", "fonte_file": "", "modalita": "breve"})

    def test_nuovo_modello_con_fonte_facoltativa(self):
        self.cattura(prosa.cmd_nuovo, "nuova-bozza")
        cartella = self.radice / "racconti/nuova-bozza"
        dati = prosa.leggi_scheda(cartella)
        self.assertEqual(dati["titolo"], "nuova-bozza")
        self.assertEqual(dati["fonte_file"], "")
        self.assertEqual(dati["scrittura_assistita"], "")
        self.assertEqual(json.loads(self.cattura(prosa.cmd_fonte, "nuova-bozza")),
                         {"doc": "", "fonte_file": "", "modalita": "breve"})
        self.assertFalse((cartella / "testo.md").exists())

    def test_scheda_virgolette_commenti_e_liste(self):
        for valore in ('casa, mare', '[casa, mare]', '["Casa", \'Mare\']', '"Casa", \'Mare\''):
            with self.subTest(valore=valore):
                self.scrivi("scheda.md", f'---\nmodalita: "breve" # (dedotto)\n'
                            f'ricorrenti: {valore} # intenzionali\n'
                            'doc: https://example.test/#scheda\n'
                            'titolo: "Una # città" # nota\n---\n')
                dati = prosa.leggi_scheda(self.cartella)
                self.assertEqual(dati["modalita"], "breve")
                self.assertEqual(dati["titolo"], "Una # città")
                self.assertEqual(dati["doc"], "https://example.test/#scheda")
                self.assertEqual(prosa.lista_scheda(dati, "ricorrenti"), ["casa", "mare"])
        self.scrivi("scheda.md", '---\nricorrenti: ["a # b", "c,d", d\'oro]\n---\n')
        self.assertEqual(prosa.lista_scheda(prosa.leggi_scheda(self.cartella), "ricorrenti"),
                         ["a # b", "c,d", "d'oro"])

    def test_scheda_rifiuta_forme_non_supportate(self):
        for riga in ('modalita: breve (dedotto)', 'modalita: media', 'modalita: "breve',
                     'modalita: [breve]', 'ricorrenti: [casa', 'pov: |\n  segreto',
                     'ricorrenti:\n  - casa', 'modalita: breve\nmodalita: lunga'):
            with self.subTest(riga=riga), contextlib.redirect_stderr(io.StringIO()) as err:
                self.scrivi("scheda.md", f"---\n{riga}\n---\n")
                with self.assertRaises(SystemExit):
                    prosa.leggi_scheda(self.cartella)
                self.assertIn("Errore:", err.getvalue())

    def test_scheda_scrittura_assistita(self):
        for riga, atteso in (("scrittura_assistita: no # l'autore: prosa dell'autore; bando", "no"),
                             ("scrittura_assistita: sì", "sì"), ("scrittura_assistita: si", "si"),
                             ("scrittura_assistita: sì", "sì"), ('scrittura_assistita: "no"', "no"),
                             ("scrittura_assistita:     # sì | no", ""), ("scrittura_assistita:", "")):
            with self.subTest(riga=riga):
                self.scrivi("scheda.md", f"---\nmodalita: breve\n{riga}\n---\n")
                self.assertEqual(prosa.leggi_scheda(self.cartella)["scrittura_assistita"], atteso)
        self.assertNotIn("scrittura_assistita", prosa.leggi_scheda(self.cartella, {"modalita"}))
        for valore in ("No", "yes", "falso", "no (autore)", "sì, no"):
            with self.subTest(valore=valore), contextlib.redirect_stderr(io.StringIO()) as err:
                self.scrivi("scheda.md", f"---\nscrittura_assistita: {valore}\n---\n")
                with self.assertRaises(SystemExit):
                    prosa.leggi_scheda(self.cartella)
                self.assertIn("scrittura_assistita non supportata", err.getvalue())

    def test_docx_run_adiacenti_e_corsivo_con_spazi(self):
        percorso = self.docx('<w:p><w:r><w:rPr><w:i w:val="on"/></w:rPr>'
                             '<w:t> Una </w:t></w:r><w:r><w:rPr><w:i/></w:rPr>'
                             '<w:t>città </w:t><w:br/><w:t>nuova</w:t></w:r></w:p>')
        self.assertEqual(self.leggi_docx(percorso), " *Una città* \n*nuova*")
        for valore in ("false", "off", "0"):
            with self.subTest(valore=valore):
                percorso = self.docx(f'<w:p><w:r><w:rPr><w:i w:val="{valore}"/></w:rPr>'
                                     '<w:t>Normale</w:t></w:r></w:p>')
                self.assertEqual(self.leggi_docx(percorso), "Normale")

    def test_docx_letterali_distinti_dal_corsivo(self):
        percorso = self.docx('<w:p><w:r><w:t>*segno* </w:t></w:r>'
                             '<w:r><w:rPr><w:i/></w:rPr><w:t>sera</w:t></w:r></w:p>')
        self.importa(percorso)
        self.assertEqual((self.cartella / "testo.md").read_text(encoding="utf-8"),
                         r"\*segno\* *sera*" + "\n")

    def test_docx_avvisa_strutture_non_supportate(self):
        percorso = self.docx('<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Cella</w:t>'
                             '<w:footnoteReference w:id="1"/></w:r></w:p></w:tc></w:tr></w:tbl>')
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(prosa.leggi_docx(percorso), "Cella")
        self.assertIn("tbl", err.getvalue())
        self.assertIn("footnoteReference", err.getvalue())
        self.assertIn("Stili ereditati", err.getvalue())

    def test_importa_preserva_spazi_interruzioni_e_paragrafi_vuoti(self):
        percorso = self.docx('<w:p><w:r><w:t> Uno </w:t><w:tab/><w:br/><w:cr/>'
                             '<w:t>Due</w:t></w:r></w:p><w:p/>'
                             '<w:p><w:r><w:t>Fine</w:t></w:r></w:p>')
        self.importa(percorso)
        self.assertEqual((self.cartella / "testo.md").read_text(encoding="utf-8"),
                         " Uno \t\n\nDue\n\n\n\nFine\n")

    def test_importa_markdown_preserva_escape_e_formattazione(self):
        testo = r"\# letterale \*stella\* e *corsivo*, \_x\_, \\fine" + "  \n\n\n"
        percorso = self.radice / "bozza.md"
        percorso.write_text(testo, encoding="utf-8")
        self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        self.assertEqual((self.cartella / "testo.md").read_text(encoding="utf-8"), testo)

    def test_importa_txt_protegge_letterali(self):
        percorso = self.radice / "bozza.txt"
        percorso.write_text("*sera*\n\n# titolo\n", encoding="utf-8")
        self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        self.assertEqual((self.cartella / "testo.md").read_text(encoding="utf-8"),
                         "\\*sera\\*\n\n\\# titolo\n")

    def test_importa_illeggibile_conserva_copia_e_derivati(self):
        self.scheda("lunga")
        self.scrivi("scene/01.md", "Vecchia scena.")
        self.scrivi("testo-unito.md", "Vecchio derivato.")
        prima = {str(p.relative_to(self.cartella)): p.read_bytes()
                 for p in self.cartella.rglob("*") if p.is_file()}
        for nome, contenuto in (("manca.txt", None), ("rotto.docx", b"non zip"),
                                 ("codifica.txt", b"\xff"), ("altro.pdf", b"x")):
            with self.subTest(nome=nome), contextlib.redirect_stderr(io.StringIO()) as err:
                percorso = self.radice / nome
                if contenuto is not None:
                    percorso.write_bytes(contenuto)
                with self.assertRaises(SystemExit):
                    prosa.cmd_importa(str(percorso), str(self.cartella))
                self.assertIn("non aggiornata", err.getvalue())
                self.assertEqual(prima, {str(p.relative_to(self.cartella)): p.read_bytes()
                                        for p in self.cartella.rglob("*") if p.is_file()})

    def test_importa_xml_rotto_conserva_copia(self):
        prima = (self.cartella / "testo.md").read_bytes()
        percorso = self.docx("<w:p>")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            prosa.cmd_importa(str(percorso), str(self.cartella))
        self.assertEqual((self.cartella / "testo.md").read_bytes(), prima)

    def test_importa_pubblicazione_fallita_conserva_copia(self):
        percorso = self.radice / "bozza.txt"
        percorso.write_text("Nuovo testo.", encoding="utf-8")
        prima = (self.cartella / "testo.md").read_bytes()
        with patch.object(prosa.os, "replace", side_effect=PermissionError("occupato")) as sostituto, \
                patch.object(prosa.time, "sleep"), \
                contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            prosa.cmd_importa(str(percorso), str(self.cartella))
        self.assertEqual(sostituto.call_count, prosa.RIPROVE + 1)
        self.assertIn("OneDrive", err.getvalue())
        self.assertIn("copia precedente è conservata", err.getvalue())
        self.assertEqual((self.cartella / "testo.md").read_bytes(), prima)
        self.assertEqual({p.name for p in self.cartella.iterdir()}, {"testo.md", "scheda.md"})

    def blocco(self, volte):
        """Sostituto di os.replace che fallisce le prime volte con PermissionError."""
        vero, chiamate = os.replace, []

        def sostituto(a, b):
            chiamate.append(Path(b).name)
            if len(chiamate) <= volte:
                raise PermissionError("in uso da OneDrive")
            vero(a, b)
        return sostituto, chiamate

    def test_importa_tollera_il_blocco_breve(self):
        self.scheda("lunga")
        percorso = self.radice / "bozza.md"
        percorso.write_bytes(b"Uno.\n\n* * *\n\nDue.\n")
        sostituto, chiamate = self.blocco(2)
        with patch.object(prosa.time, "sleep") as pausa, \
                patch.object(prosa.os, "replace", side_effect=sostituto):
            self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        copia = hashlib.sha256(percorso.read_bytes()).hexdigest()[:16] + ".md"
        self.assertEqual(chiamate, ["testo.md"] * 3 + ["01.md", "02.md", copia])
        self.assertEqual(pausa.call_count, 2)
        self.assertEqual((self.cartella / "testo.md").read_bytes(), percorso.read_bytes())
        self.assertEqual((self.cartella / "scene/02.md").read_text(encoding="utf-8"), "Due.\n")
        self.assertFalse([p for p in self.cartella.rglob("*") if p.name.startswith("tmp")])
        self.scheda("breve")

    def test_dividi_scena_bloccata(self):
        self.scrivi("testo.md", "Uno.\n\n* * *\n\nDue.\n")
        self.scrivi("scene/01.md", "Vecchia.")
        prima = (self.cartella / "testo.md").read_bytes()
        sostituto, chiamate = self.blocco(99)
        with patch.object(prosa.time, "sleep"), \
                patch.object(prosa.os, "replace", side_effect=sostituto), \
                contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            prosa.dividi(self.cartella)
        self.assertEqual(len(chiamate), prosa.RIPROVE + 1)
        self.assertIn("OneDrive", err.getvalue())
        self.assertIn("rieseguire dividi", err.getvalue())
        self.assertEqual((self.cartella / "testo.md").read_bytes(), prima)
        self.assertEqual((self.cartella / "scene/01.md").read_text(encoding="utf-8"), "Vecchia.")
        self.assertEqual({p.name for p in (self.cartella / "scene").iterdir()}, {"01.md"})

    def test_rimozione_scene_tollera_il_blocco_breve(self):
        self.scrivi("scene/01.md", "Vecchia.")
        percorso = self.radice / "bozza.txt"
        percorso.write_text("Nuovo testo.", encoding="utf-8")
        vero, chiamate = Path.unlink, []

        def unlink(p, *args, **kwargs):
            if p.name == "01.md":
                chiamate.append(p.name)
                if len(chiamate) <= 2:
                    raise PermissionError("in uso da OneDrive")
            return vero(p, *args, **kwargs)

        with patch.object(prosa.time, "sleep") as pausa, patch.object(Path, "unlink", unlink):
            self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        self.assertEqual(len(chiamate), 3)
        self.assertEqual(pausa.call_count, 2)
        self.assertEqual(list((self.cartella / "scene").iterdir()), [])

    def test_importa_rigenera_scene_e_invalida_unito(self):
        self.scheda("lunga")
        self.scrivi("scene/01.md", "Vecchia scena.")
        self.scrivi("scene/03.md", "Scena rimossa.")
        self.scrivi("testo-unito.md", "Vecchia unione.")
        percorso = self.radice / "bozza.md"
        percorso.write_text("Uno.\n\n* * *\n\nDue.\n", encoding="utf-8")
        self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        self.assertEqual({p.name for p in (self.cartella / "scene").iterdir()}, {"01.md", "02.md"})
        self.assertEqual((self.cartella / "scene/02.md").read_text(encoding="utf-8"), "Due.\n")
        self.assertFalse((self.cartella / "testo-unito.md").exists())
        self.scheda("breve")
        self.cattura(prosa.cmd_importa, str(percorso), str(self.cartella))
        self.assertEqual(list((self.cartella / "scene").glob("*.md")), [])

    def test_percorso_file_fino_ai_controlli_revisione(self):
        percorso = self.radice / "bozza città.md"
        percorso.write_text("È sera.\n", encoding="utf-8")
        self.scrivi("scheda.md", '---\ndoc:\nfonte_file: "bozza città.md"\nmodalita: breve\n---\n')
        fonte = json.loads(self.cattura(prosa.cmd_fonte, str(self.cartella)))
        self.cattura(prosa.cmd_importa, fonte["fonte_file"], str(self.cartella))
        self.cattura(prosa.cmd_controlla, str(self.cartella), salva=True)
        self.assertTrue(list((self.cartella / "revisioni").glob("*-controlli.md")))
        self.assertEqual(percorso.read_text(encoding="utf-8"), "È sera.\n")

    def test_stacchi_importati_contano_e_dividono(self):
        self.scheda("lunga")
        atteso = "Uno.\n\n* * *\n\nDue *qui*.\n\n***\n\nTre.\n"
        sorgenti = {
            "docx": self.docx('<w:p><w:r><w:t>Uno.</w:t></w:r></w:p>'
                              '<w:p><w:r><w:t>* * *</w:t></w:r></w:p>'
                              '<w:p><w:r><w:t xml:space="preserve">Due </w:t></w:r>'
                              '<w:r><w:rPr><w:i/></w:rPr><w:t>qui</w:t></w:r>'
                              '<w:r><w:t>.</w:t></w:r></w:p>'
                              '<w:p><w:r><w:t>*</w:t></w:r><w:r><w:rPr><w:i/></w:rPr>'
                              '<w:t>**</w:t></w:r></w:p>'
                              '<w:p><w:r><w:t>Tre.</w:t></w:r></w:p>'),
            "txt": self.radice / "bozza.txt",
            "doc grezzo": self.radice / ".doc-grezzo.md",
        }
        sorgenti["txt"].write_text("Uno.\n\n* * *\n\nDue qui.\n\n***\n\nTre.\n", encoding="utf-8")
        sorgenti["doc grezzo"].write_text(atteso, encoding="utf-8")
        for nome, percorso in sorgenti.items():
            with self.subTest(fonte=nome):
                testo = self.importa(percorso)
                if nome != "txt":
                    self.assertEqual(testo, atteso)
                self.assertEqual(len(list((self.cartella / "scene").glob("*.md"))), 3)
                self.assertEqual(self.totali(), (4, 16))  # «Uno.» + «Due qui.» + «Tre.»

    def test_asterischi_non_isolati_restano_letterali(self):
        percorso = self.docx('<w:p><w:r><w:t>***</w:t></w:r><w:r><w:rPr><w:i/></w:rPr>'
                             '<w:t>Fine</w:t></w:r></w:p>'
                             '<w:p><w:r><w:t>Riga</w:t><w:br/><w:t>* * *</w:t></w:r></w:p>')
        self.assertEqual(self.importa(percorso), "\\*\\*\\**Fine*\n\nRiga\n\\* \\* \\*\n")
        testo_txt = self.radice / "bozza.txt"
        testo_txt.write_text("** nota * a margine\n", encoding="utf-8")
        self.assertEqual(self.importa(testo_txt), "\\*\\* nota \\* a margine\n")

    def test_enfasi_non_attraversa_capoversi(self):
        self.assertEqual(prosa.testo_visibile("Costo 2*3 euro.\n\nPoi 4*5 euro."),
                         "Costo 2*3 euro.\n\nPoi 4*5 euro.")
        self.assertEqual(prosa.testo_visibile("*Uno\ndue*"), "Uno\ndue")

    def test_nuovo_e_dividi_scrivono_lf(self):
        self.cattura(prosa.cmd_nuovo, "fine-riga")
        for nome in ("scheda.md", "stato.md"):
            self.assertNotIn(b"\r", (self.radice / "racconti/fine-riga" / nome).read_bytes())
        self.scrivi("testo.md", "Uno.\nAncora.\n\n* * *\n\nDue.\n")
        self.cattura(prosa.dividi, self.cartella)
        for scena in (self.cartella / "scene").glob("*.md"):
            self.assertNotIn(b"\r", scena.read_bytes())

    def test_dialoghi_senza_scheda(self):
        (self.cartella / "scheda.md").unlink()
        self.scrivi("testo.md", "— Vieni.\n")
        report = self.cattura(prosa.cmd_dialoghi, str(self.cartella))
        self.assertIn("Scheda assente", report)
        self.assertIn("Proposte semplici da verificare (1)", report)

    STATO = "# Stato\n\n## Fatto\n- voce riservata dello stato\n"
    RIGA = ("2026-10-06 lettura a freddo (giurato), fonte C:\\Esempi\\Il faro.docx, "
            "d'oro, «città», revisione non disponibile: letture/2026-10-06-giurato.md")

    def registra(self, riga):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                output = self.cattura(prosa.main, ["prosa.py", "registra", str(self.cartella), riga])
            except SystemExit:
                return None, err.getvalue()
        return output, err.getvalue()

    def file_cartella(self):
        return {p.name: p.read_bytes() for p in self.cartella.iterdir() if p.is_file()}

    def test_registra_accoda_senza_mostrare_lo_stato(self):
        prima = self.scrivi("stato.md", self.STATO).read_bytes()
        output, _ = self.registra(self.RIGA)
        self.assertEqual(output, "Registrato in racconti/città di prova/stato.md\n")
        self.assertNotIn("riservata", output)
        self.assertEqual((self.cartella / "stato.md").read_bytes(),
                         prima + ("- " + self.RIGA + "\n").encode("utf-8"))
        self.assertEqual({p.name for p in self.cartella.iterdir()}, {"scheda.md", "testo.md", "stato.md"})

    def test_registra_aggiunge_a_capo_e_conserva_i_byte(self):
        for prima in (b"## Fatto\n- uno", b"\xef\xbb\xbf## Fatto\r\n- uno\r\n", b""):
            with self.subTest(prima=prima):
                (self.cartella / "stato.md").write_bytes(prima)
                self.registra("  due  ")
                attesa = prima + (b"" if not prima or prima.endswith(b"\n") else b"\n") + b"- due\n"
                self.assertEqual((self.cartella / "stato.md").read_bytes(), attesa)

    def test_registra_rifiuta_righe_vuote_o_multiple(self):
        self.scrivi("stato.md", self.STATO)
        prima = self.file_cartella()
        for riga in ("", "   ", "uno\ndue", "uno\r\ndue", "uno\rdue", "uno\u2028due"):
            with self.subTest(riga=riga):
                output, err = self.registra(riga)
                self.assertIsNone(output)
                self.assertIn("Errore:", err)
                self.assertNotIn("riservata", err)
                self.assertEqual(self.file_cartella(), prima)

    def test_registra_senza_stato(self):
        prima = self.file_cartella()
        output, err = self.registra(self.RIGA)
        self.assertIsNone(output)
        self.assertIn("manca racconti/città di prova/stato.md", err)
        self.assertEqual(self.file_cartella(), prima)

    def test_registra_tollera_il_blocco_breve(self):
        self.scrivi("stato.md", self.STATO)
        vero, chiamate = os.replace, []

        def bloccato(volte):
            def sostituto(a, b):
                chiamate.append(b)
                if len(chiamate) <= volte:
                    raise PermissionError("in uso da un altro processo")
                vero(a, b)
            return sostituto

        with patch.object(prosa.time, "sleep") as pausa, \
                patch.object(prosa.os, "replace", side_effect=bloccato(2)):
            output, _ = self.registra("dopo due blocchi")
        self.assertEqual(len(chiamate), 3)
        self.assertEqual(pausa.call_count, 2)
        self.assertIn("Registrato", output)
        self.assertTrue((self.cartella / "stato.md").read_text(encoding="utf-8").endswith("- dopo due blocchi\n"))
        prima, chiamate[:] = self.file_cartella(), []
        with patch.object(prosa.time, "sleep"), \
                patch.object(prosa.os, "replace", side_effect=bloccato(99)):
            output, err = self.registra("mai")
        self.assertIsNone(output)
        self.assertEqual(len(chiamate), prosa.RIPROVE + 1)
        self.assertIn("OneDrive", err)
        self.assertIn("versione precedente è conservata", err)
        self.assertEqual(self.file_cartella(), prima)

    def test_registra_da_riga_di_comando(self):
        self.scrivi("stato.md", self.STATO)
        risultato = subprocess.run(
            [sys.executable, "-X", "utf8", str(Path(prosa.__file__).resolve()), "registra",
             str(self.cartella), self.RIGA],
            capture_output=True, check=False)
        self.assertEqual(risultato.returncode, 0, risultato.stderr.decode("utf-8"))
        self.assertNotIn("riservata", risultato.stdout.decode("utf-8"))
        self.assertTrue((self.cartella / "stato.md").read_text(encoding="utf-8")
                        .endswith("- " + self.RIGA + "\n"))

    def test_scheda_con_bom(self):
        self.scrivi("scheda.md", "\ufeff---\ndoc: https://example.test/doc\nmodalita: breve\n"
                    "limite_battute: 5\ndialoghi: caporali\n---\n"
                    "## Scelte di questo racconto\nLineette mantenute.\n")
        self.scrivi("testo.md", "— Vieni.\n")
        self.assertEqual(json.loads(self.cattura(prosa.cmd_fonte, str(self.cartella)))["doc"],
                         "https://example.test/doc")
        self.assertIn("oltre di 3", self.cattura(prosa.cmd_conta, str(self.cartella)))
        self.assertIn("https://example.test/doc", self.cattura(prosa.cmd_controlla, str(self.cartella)))
        report = self.cattura(prosa.cmd_dialoghi, str(self.cartella))
        self.assertIn("Lineette mantenute", report)
        self.assertIn("Scheda, dialoghi: caporali", report)

    def test_altri_file_con_bom(self):
        self.scrivi("testo.md", "\ufeffUno due tre. Passaggio scelto qui.\n\n* * *\n\nFine.\n")
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("\ufeffPassaggio scelto qui.", encoding="utf-8")
        extra = self.radice / "strumenti" / "stilemi_extra.txt"
        extra.parent.mkdir()
        extra.write_text("\ufeffscelto qui\n", encoding="utf-8")
        report = self.cattura(prosa.cmd_confronta, str(passaggio), str(self.cartella))
        self.assertIn("Stesso racconto: 4 parole senza coincidenze", report)
        self.assertIn("«scelto qui»", report)
        self.assertFalse(prosa.testo_racconto(self.cartella)[0][1].startswith("\ufeff"))
        self.cattura(prosa.dividi, self.cartella)
        self.assertEqual((self.cartella / "scene/01.md").read_text(encoding="utf-8"),
                         "Uno due tre. Passaggio scelto qui.\n")
        modello = self.radice / "modello"
        modello.mkdir()
        for nome in ("scheda.md", "stato.md"):
            (modello / nome).write_text("\ufeff---\ntitolo: {{nome}}\n---\n", encoding="utf-8")
        with patch.object(prosa, "MODELLO", modello):
            self.cattura(prosa.cmd_nuovo, "con-bom")
        self.assertFalse((self.radice / "racconti/con-bom/scheda.md").read_bytes().startswith(b"\xef\xbb\xbf"))

    def verifica(self, testo_copia, nome_file, contenuto, *opzioni):
        """Esito e report di verifica; contenuto è testo (scritto in UTF-8) o un percorso già pronto."""
        (self.cartella / "testo.md").write_bytes(testo_copia.encode("utf-8"))
        if isinstance(contenuto, Path):
            percorso = contenuto
        else:
            percorso = self.radice / nome_file
            percorso.write_text(contenuto, encoding="utf-8", newline="\n")
        with contextlib.redirect_stderr(io.StringIO()):
            report = self.cattura(prosa.main, ["prosa.py", "verifica", str(percorso),
                                               str(self.cartella), *opzioni])
        return report.split("Esito: ", 1)[1].split("\n", 1)[0], report

    TESTO = "Uno *due* tre.\n\n* * *\n\nQuattro cinque.\n\nSei sette.\n"

    def test_verifica_file_identico(self):
        esito, report = self.verifica(self.TESTO, "bozza città.md", self.TESTO)
        self.assertEqual(esito, "coincide")
        self.assertIn("| Battute | 37 | 37 |", report)
        self.assertNotIn("## Differenze", report)
        for copia in (self.TESTO.replace("\n", "\r\n"), "﻿" + self.TESTO):
            with self.subTest(copia=copia):
                esito, report = self.verifica(copia, "bozza città.md", self.TESTO)
                self.assertEqual(esito, "coincide nel testo, differisce nella formattazione")
                self.assertIn("cambiano solo righe vuote, fine riga o BOM", report)

    def test_verifica_parola_diversa(self):
        esito, report = self.verifica(self.TESTO, "bozza.md", self.TESTO.replace("cinque", "sei"))
        self.assertEqual(esito, "differisce")
        self.assertIn("Capoversi diversi: 1; aggiunti in testo.md: 0; mancanti in testo.md: 0.", report)
        self.assertIn("**Capoverso 3 del file, 3 di testo.md: diverso**", report)
        self.assertIn("- file: Quattro sei.", report)
        self.assertIn("- testo.md: Quattro cinque.", report)
        self.assertIn("| Parole | 7 | 7 |", report)
        self.assertIn("non si usa come evidenza", report)

    def test_verifica_capoverso_mancante_e_stacco(self):
        esito, report = self.verifica(self.TESTO, "bozza.md",
                                      "Uno *due* tre.\n\nQuattro  cinque.\n\nSei sette.\n\nOtto.\n")
        self.assertEqual(esito, "differisce")
        self.assertIn("Capoversi diversi: 1; aggiunti in testo.md: 1; mancanti in testo.md: 1.", report)
        self.assertIn("**Capoverso — del file, 2 di testo.md: aggiunto in testo.md**\n"
                      "- testo.md: [stacco di scena]", report)
        self.assertIn("**Capoverso 2 del file, 3 di testo.md: diverso (solo spazi)**", report)
        self.assertIn("**Capoverso 4 del file, — di testo.md: mancante in testo.md**\n- file: Otto.", report)

    def test_verifica_solo_formattazione(self):
        for altro in ("Uno due tre.\n\n* * *\n\nQuattro cinque.\n\nSei sette.\n",
                      "Uno *due* tre.\n\n***\n\n\n\nQuattro cinque.\n\nSei sette.\n",
                      "Uno *due* tre.\n\n* * *\n\nQuattro cinque\\.\n\nSei sette.\n"):
            with self.subTest(altro=altro):
                esito, report = self.verifica(self.TESTO, "bozza.md", altro)
                self.assertEqual(esito, "coincide nel testo, differisce nella formattazione")
                self.assertIn("## Differenze di formattazione", report)
                self.assertNotIn("## Differenze nel testo visibile", report)
        _, report = self.verifica(self.TESTO, "bozza.md", self.TESTO.replace("*due*", "due"))
        self.assertIn("- file: Uno due tre.\n- testo.md: Uno *due* tre.", report)
        _, report = self.verifica(self.TESTO, "bozza.md", self.TESTO.replace("\n\n", "\n\n\n"))
        self.assertIn("cambiano solo righe vuote, fine riga o BOM", report)

    def test_verifica_spazi_fuori_dai_capoversi_contano(self):
        esito, report = self.verifica(self.TESTO, "bozza.md", self.TESTO.replace("\n\nSei", "\n  \nSei"))
        self.assertEqual(esito, "differisce")
        self.assertIn("righe di soli spazi", report)

    def test_verifica_letterali_con_escape(self):
        copia = "Il segno \\*stella\\* e \\#7.\n"
        self.assertEqual(self.verifica(copia, "bozza.txt", "Il segno *stella* e #7.\n")[0], "coincide")
        esito, report = self.verifica(copia, "bozza.md", "Il segno *stella* e #7.\n")
        self.assertEqual(esito, "differisce")
        self.assertIn("- file: Il segno stella e #7.\n- testo.md: Il segno *stella* e #7.", report)
        self.assertEqual(self.verifica(copia, "bozza.md", copia)[0], "coincide")

    def test_verifica_docx_e_txt(self):
        docx = self.docx('<w:p><w:r><w:t xml:space="preserve">È </w:t></w:r>'
                         '<w:r><w:rPr><w:i/></w:rPr><w:t>sera</w:t></w:r></w:p>'
                         '<w:p><w:r><w:t>* * *</w:t></w:r></w:p>'
                         '<w:p><w:r><w:t>Fine.</w:t></w:r></w:p>')
        self.assertEqual(self.verifica("È *sera*\n\n* * *\n\nFine.\n", "", docx)[0], "coincide")
        self.assertEqual(self.verifica("È sera\n\n* * *\n\nFine.\n", "", docx)[0],
                         "coincide nel testo, differisce nella formattazione")
        txt = self.radice / "bozza città.txt"
        txt.write_bytes("È sera\r\n\r\n* * *\r\n\r\nFine.".encode("utf-8"))
        self.assertEqual(self.verifica("È sera\n\n* * *\n\nFine.\n", "", txt)[0], "coincide")

    def test_leggi_fonte_come_importa(self):
        for nome, contenuto in (("a.md", "*Uno*\r\n\r\n\\# due"), ("b.txt", "*Uno*\n\n***\n# due")):
            with self.subTest(nome=nome):
                percorso = self.radice / nome
                percorso.write_text(contenuto, encoding="utf-8", newline="")
                self.assertEqual(prosa.leggi_fonte(percorso), self.importa(percorso))

    def test_verifica_non_scrive_nel_racconto(self):
        self.scrivi("stato.md", self.STATO)
        self.scrivi("scene/01.md", "Scena.")
        percorso = self.radice / "bozza.md"
        percorso.write_text("Altro testo.\n", encoding="utf-8")
        prima = {str(p.relative_to(self.radice)): p.read_bytes() for p in self.radice.rglob("*") if p.is_file()}
        with contextlib.redirect_stderr(io.StringIO()):
            self.cattura(prosa.main, ["prosa.py", "verifica", str(percorso), str(self.cartella)])
        dopo = {str(p.relative_to(self.radice)): p.read_bytes() for p in self.radice.rglob("*") if p.is_file()}
        self.assertEqual(prima, dopo)
        self.assertFalse((self.cartella / "revisioni").exists())

    def test_verifica_illeggibile_non_modifica_niente(self):
        prima = self.file_cartella()
        for nome, contenuto in (("manca.docx", None), ("rotto.docx", b"non zip"),
                                 ("codifica.md", b"\xff"), ("altro.pdf", b"x")):
            with self.subTest(nome=nome), contextlib.redirect_stderr(io.StringIO()) as err:
                percorso = self.radice / nome
                if contenuto is not None:
                    percorso.write_bytes(contenuto)
                with self.assertRaises(SystemExit):
                    self.cattura(prosa.cmd_verifica, str(percorso), str(self.cartella))
                self.assertIn("verifica non riuscita", err.getvalue())
                self.assertIn("Nessun file è stato modificato", err.getvalue())
                self.assertEqual(self.file_cartella(), prima)

    def test_verifica_salva_report_univoco(self):
        self.scrivi("scheda.md", "---\ndoc: https://example.test/doc\nmodalita: breve\n---\n")
        impronta = hashlib.sha256(self.TESTO.encode("utf-8")).hexdigest()
        with patch.object(prosa, "oggi", return_value="2026-10-06"):
            for _ in range(2):
                _, output = self.verifica(self.TESTO, "bozza città.md", self.TESTO, "--salva")
        self.assertIn("Salvato in racconti/città di prova/revisioni/2026-10-06-verifica-02.md", output)
        self.assertEqual({p.name for p in (self.cartella / "revisioni").iterdir()},
                         {"2026-10-06-verifica.md", "2026-10-06-verifica-02.md"})
        report = (self.cartella / "revisioni/2026-10-06-verifica.md").read_text(encoding="utf-8")
        self.assertIn("Esito: coincide\n", report)
        self.assertIn(f"SHA-256 di testo.md: `{impronta}`", report)
        self.assertIn("Fonte dichiarata: https://example.test/doc", report)
        self.assertIn(f"File confrontato: {(self.radice / 'bozza città.md').resolve()}", report)
        self.assertIn(f"SHA-256 del file confrontato: `{impronta}`", report)

    def test_verifica_molte_differenze_ne_mostra_dieci(self):
        copia = "".join(f"Capoverso numero {n}.\n\n" for n in range(15))
        esito, report = self.verifica(copia, "bozza.md", copia.replace("numero", "n."))
        self.assertEqual(esito, "differisce")
        self.assertIn("Prime dieci differenze su 15", report)
        self.assertEqual(report.count(": diverso**"), 10)

    # Sprint mestiere, sottotappa 1.1–1.4.

    def errore_di(self, *argomenti):
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            self.cattura(prosa.main, ["prosa.py", *argomenti])
        return err.getvalue()

    def test_intestazione_come_i_report_e_con_revisione(self):
        self.scrivi("scheda.md", "---\ndoc: https://example.test/doc\nmodalita: breve\n---\n")
        impronta = hashlib.sha256((self.cartella / "testo.md").read_bytes()).hexdigest()
        blocco = self.cattura(prosa.main, ["prosa.py", "intestazione", str(self.cartella)])
        senza_ora = lambda t: [r for r in t.splitlines() if not r.startswith("- Generato:")]
        self.assertEqual(senza_ora(blocco),
                         senza_ora(prosa.identita_report(self.cartella, {"doc": "https://example.test/doc"})))
        self.assertIn(f"SHA-256 di testo.md: `{impronta}`", blocco)
        self.assertIn("Revisione Docs della copia: non disponibile", blocco)
        self.assertRegex(blocco, r"Generato: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d")
        blocco = self.cattura(prosa.main, ["prosa.py", "intestazione", str(self.cartella),
                                           "--revisione", "ALm3-x_9"])
        self.assertIn("Revisione Docs della copia: `ALm3-x_9`, acquisita insieme al testo", blocco)
        self.assertNotIn("non disponibile", blocco)
        self.assertEqual(len(blocco.splitlines()), 5)

    def test_intestazione_rifiuta_revisione_malformata_e_copia_assente(self):
        self.assertIn("revisionId", self.errore_di("intestazione", str(self.cartella), "--revisione"))
        self.assertIn("backtick", self.errore_di("intestazione", str(self.cartella), "--revisione", "a`b"))
        self.assertIn("solo con «intestazione»",
                      self.errore_di("conta", str(self.cartella), "--revisione", "abc"))
        (self.cartella / "testo.md").unlink()
        self.assertIn("importa", self.errore_di("intestazione", str(self.cartella)))

    def test_nome_libero_come_salva_univoco_senza_creare(self):
        cartella = self.cartella / "revisioni"
        cartella.mkdir()
        richiesta = cartella / "2026-10-13-strutturale.md"
        self.assertEqual(self.cattura(prosa.main, ["prosa.py", "nome-libero", str(richiesta)]).strip(),
                         richiesta.as_posix())
        richiesta.write_text("primo", encoding="utf-8")
        (cartella / "2026-10-13-strutturale-02.md").write_text("secondo", encoding="utf-8")
        libero = self.cattura(prosa.main, ["prosa.py", "nome-libero", str(richiesta)]).strip()
        self.assertEqual(libero, (cartella / "2026-10-13-strutturale-03.md").as_posix())
        self.assertFalse(Path(libero).exists())
        self.assertEqual(prosa.salva_univoco(cartella, richiesta.name, "terzo").as_posix(), libero)
        self.assertIn("estensione", self.errore_di("nome-libero", str(cartella / "senza-estensione")))

    def test_nome_libero_avvisa_se_la_cartella_manca(self):
        richiesta = self.cartella / "revisoni" / "report.md"
        with contextlib.redirect_stderr(io.StringIO()) as err:
            libero = self.cattura(prosa.main, ["prosa.py", "nome-libero", str(richiesta)]).strip()
        self.assertEqual(libero, richiesta.as_posix())
        self.assertIn("non esiste ancora", err.getvalue())
        self.assertFalse(richiesta.parent.exists())

    def copie(self):
        return sorted(p.name for p in (self.cartella / "copie").glob("*"))

    def test_importa_conserva_una_copia_per_versione(self):
        sorgente = self.radice / "bozza città.md"
        sorgente.write_text("Prima versione.\n", encoding="utf-8")
        self.importa(sorgente)
        self.importa(sorgente)
        impronta = hashlib.sha256((self.cartella / "testo.md").read_bytes()).hexdigest()
        self.assertEqual(self.copie(), [impronta[:16] + ".md"])
        copia = self.cartella / "copie" / self.copie()[0]
        self.assertEqual(copia.read_bytes(), (self.cartella / "testo.md").read_bytes())
        sorgente.write_text("Seconda versione.\n", encoding="utf-8")
        self.importa(sorgente)
        self.assertEqual(len(self.copie()), 2)
        self.assertEqual(copia.read_text(encoding="utf-8"), "Prima versione.\n")
        # Una copia guasta con lo stesso nome non vale come conservata: si riscrive.
        sorgente.write_text("Prima versione.\n", encoding="utf-8")
        copia.write_text("troncata", encoding="utf-8")
        self.importa(sorgente)
        self.assertEqual(copia.read_text(encoding="utf-8"), "Prima versione.\n")

    def test_importa_fallita_non_crea_copie(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            prosa.cmd_importa(str(self.radice / "manca.md"), str(self.cartella))
        self.assertFalse((self.cartella / "copie").exists())

    def versioni(self, prima, dopo):
        """Importa due versioni e restituisce lo SHA-256 della prima."""
        sorgente = self.radice / "bozza città.md"
        sorgente.write_text(prima, encoding="utf-8")
        self.importa(sorgente)
        impronta = hashlib.sha256((self.cartella / "testo.md").read_bytes()).hexdigest()
        sorgente.write_text(dopo, encoding="utf-8")
        self.importa(sorgente)
        return impronta

    def differenze(self, sha):
        return self.cattura(prosa.main, ["prosa.py", "differenze", str(self.cartella), sha])

    VERSIONE = "Uno apre.\n\nDue continua.\n\n* * *\n\nTre scena.\n\nQuattro chiude.\n"

    def test_differenze_aggiunti_tolti_modificati(self):
        dopo = self.VERSIONE.replace("Uno apre.\n\n", "").replace("Tre scena", "Tre scena cambiata")
        dopo += "\nCinque nuovo.\n"
        sha = self.versioni(self.VERSIONE, dopo)
        for richiesta in (sha, sha[:16], sha[:20].upper(), f"`{sha}`"):
            with self.subTest(richiesta=richiesta):
                out = self.differenze(richiesta)
                self.assertIn("**Capoverso — di testo.md, 1 della copia: tolto**", out)
                self.assertIn("- prima: Uno apre.", out)
                self.assertIn("**Capoverso 3 di testo.md, 4 della copia: modificato**", out)
                self.assertIn("- dopo: Tre scena cambiata.", out)
                self.assertIn("**Capoverso 5 di testo.md, — della copia: aggiunto**", out)
                self.assertNotIn("Due continua", out)
                self.assertIn("Capoversi cambiati: 2 su 5 di testo.md (modificati 1, aggiunti 1); "
                              "tolti dalla copia: 1 su 5.", out)
                self.assertIn("Primo capoverso: cambiato. Ultimo capoverso: cambiato.", out)
                self.assertIn(f"SHA-256 `{sha}`", out)

    def test_differenze_solo_in_mezzo_e_solo_formattazione(self):
        sha = self.versioni(self.VERSIONE, self.VERSIONE.replace("Tre scena", "Tre *scena*"))
        out = self.differenze(sha)
        self.assertIn("modificato (solo formattazione)", out)
        self.assertIn("Primo capoverso: invariato. Ultimo capoverso: invariato.", out)
        self.assertIn("Capoversi cambiati: 1 su 5", out)

    def test_differenze_stacco_tolto_e_testo_identico(self):
        sha = self.versioni(self.VERSIONE, self.VERSIONE.replace("* * *\n\n", ""))
        self.assertIn("[stacco di scena]", self.differenze(sha))
        sha = self.versioni(self.VERSIONE, self.VERSIONE)
        self.assertIn("Nessuna differenza", self.differenze(sha))

    def test_differenze_copia_assente_impronta_non_valida_o_diversa(self):
        sha = self.versioni(self.VERSIONE, "Altro.\n")
        assente = "0" * 64
        messaggio = self.errore_di("differenze", str(self.cartella), assente)
        self.assertIn("0" * 16, messaggio)
        self.assertIn("revisione intera", messaggio)
        for sbagliata in (sha[:15], "z" * 16, sha + "0"):
            with self.subTest(sbagliata=sbagliata):
                self.assertIn("impronta non valida", self.errore_di("differenze", str(self.cartella), sbagliata))
        # Stesse prime 16 cifre, impronta completa diversa: non è la versione del report.
        diversa = sha[:16] + ("0" if sha[16] != "0" else "1") + sha[17:]
        self.assertIn("non è la versione", self.errore_di("differenze", str(self.cartella), diversa))

    def test_differenze_non_scrive_nel_racconto(self):
        sha = self.versioni(self.VERSIONE, self.VERSIONE.replace("Due", "Dieci"))
        prima = {str(p.relative_to(self.cartella)): p.read_bytes()
                 for p in self.cartella.rglob("*") if p.is_file()}
        self.differenze(sha)
        self.assertEqual(prima, {str(p.relative_to(self.cartella)): p.read_bytes()
                                 for p in self.cartella.rglob("*") if p.is_file()})

    def test_aiuto_elenca_i_comandi_nuovi(self):
        aiuto = self.cattura(prosa.main, ["prosa.py", "aiuto"])
        for comando in ("intestazione", "--revisione", "nome-libero", "differenze", "copie/",
                        "provenienza", "tappe", "--battute"):
            self.assertIn(comando, aiuto)

    # Sprint mestiere, sottotappa 1.5–1.7.

    def test_scheda_ia_bando(self):
        for valore, atteso in (("vietata", "vietata"), ("ammessa # art. 4", "ammessa"),
                               ("da  verificare", "da verificare"), ("", "")):
            with self.subTest(valore=valore):
                self.scrivi("scheda.md", f"---\nia_bando: {valore}\n---\n")
                self.assertEqual(prosa.leggi_scheda(self.cartella)["ia_bando"], atteso)
        for valore in ("no", "vietata (dedotto)", "sì"):
            with self.subTest(valore=valore), contextlib.redirect_stderr(io.StringIO()) as err:
                self.scrivi("scheda.md", f"---\nia_bando: {valore}\n---\n")
                with self.assertRaises(SystemExit):
                    prosa.leggi_scheda(self.cartella)
                self.assertIn("vietata, ammessa, da verificare", err.getvalue())

    def test_fonte_non_restituisce_ia_bando(self):
        self.scrivi("scheda.md", "---\ndoc:\nia_bando: vietata\nmodalita: breve\n---\n")
        dati = json.loads(self.cattura(prosa.cmd_fonte, str(self.cartella)))
        self.assertEqual(set(dati), {"doc", "fonte_file", "modalita"})

    def test_modello_scheda_ha_ia_bando_valido(self):
        modello = Path(prosa.__file__).resolve().parent.parent / "racconti" / "_modello" / "scheda.md"
        testo = modello.read_text(encoding="utf-8").replace("{{nome}}", "prova")
        self.assertRegex(testo, r"(?m)^ia_bando: +# vietata \| ammessa \| da verificare")
        (self.cartella / "scheda.md").write_text(testo, encoding="utf-8")
        self.assertEqual(prosa.leggi_scheda(self.cartella)["ia_bando"], "")

    FRASE_ASSISTENTE = ("La camicia la sistemo domani mattina prima di uscire, "
                        "quando la luce sarà diversa e io pure.")

    def materiale(self, nome, corpo, marcato=True):
        intestazione = "# Variante\n\n- Stato: proposta\n"
        if marcato:
            intestazione += "- Autore del testo: assistente (racconto-scrittura, variante)\n"
        return self.scrivi(f"materiali/{nome}", intestazione + "\n" + corpo + "\n")

    def provenienza(self, *argomenti):
        return self.cattura(prosa.main, ["prosa.py", "provenienza", str(self.cartella), *argomenti])

    def test_provenienza_senza_materiali_marcati(self):
        self.materiale("2026-10-01-idea.md", self.FRASE_ASSISTENTE, marcato=False)
        out = self.provenienza()
        self.assertIn("Nessun materiale con il marcatore", out)
        self.assertIn("Passare i file", out)
        self.assertFalse((self.cartella / "revisioni").exists())

    def test_provenienza_marcati_quota_e_capoversi(self):
        mio = "Io sono rimasto fermo davanti alla porta senza sapere bene cosa dire a nessuno."
        self.scrivi("testo.md", mio + "\n\n" + self.FRASE_ASSISTENTE + "\n")
        self.materiale("2026-10-02-variante.md", self.FRASE_ASSISTENTE.replace("’", "'"))
        self.materiale("_passaggio.md", mio)  # file di lavoro: mai usato in automatico
        out = self.provenienza()
        totale = len(prosa.parole_normalizzate(mio + " " + self.FRASE_ASSISTENTE))
        coincidenti = len(prosa.parole_normalizzate(self.FRASE_ASSISTENTE))
        self.assertIn(f"({coincidenti} parole su {totale})", out)
        self.assertIn("capoverso 2: 100,0%", out)
        self.assertNotIn("capoverso 1:", out)
        self.assertNotIn("_passaggio.md", out)
        self.assertIn(prosa.AVVERTENZA_PROVENIENZA, out)
        self.assertIn("SHA-256 di testo.md", out)

    def test_provenienza_ritocco_e_frasi_brevi(self):
        # Una parola cambiata: resta riconoscibile il tratto di 13 parole prima; le 3 dopo,
        # meno di 8, non bastano da sole.
        ritoccata = self.FRASE_ASSISTENTE.replace("diversa", "nuova")
        self.scrivi("testo.md", ritoccata + "\n\nPrima di uscire la sistemo.\n")
        self.materiale("2026-10-02-variante.md", self.FRASE_ASSISTENTE + "\n\nPrima di uscire.")
        m = prosa.misura_provenienza(self.cartella, [self.cartella / "materiali/2026-10-02-variante.md"])
        parole_ritoccata = len(prosa.parole_normalizzate(ritoccata))
        self.assertEqual(m["per_capoverso"][0], (parole_ritoccata, parole_ritoccata - 4))
        self.assertEqual(m["per_capoverso"][1][1], 0)  # meno di 8 parole uguali: non conta

    def test_provenienza_materiali_espliciti_e_salva(self):
        self.scrivi("testo.md", self.FRASE_ASSISTENTE + "\n")
        self.materiale("2026-10-02-a.md", self.FRASE_ASSISTENTE, marcato=False)
        self.materiale("2026-10-03-b.md", "Altro testo che non c'entra.", marcato=False)
        out = self.provenienza("materiali/2026-10-02-a.md",
                               str(self.cartella / "materiali/2026-10-03-b.md"), "--salva")
        self.assertIn("Quota coincidente: 100,0%", out)
        self.assertIn("2026-10-03-b.md: 0 parole (0,0%)", out)
        self.assertIn("contributi possono", out)
        report = self.cartella / "revisioni" / f"{prosa.oggi()}-provenienza.md"
        self.assertIn("Quota coincidente: 100,0%", report.read_text(encoding="utf-8"))
        self.provenienza("materiali/2026-10-02-a.md", "--salva")
        self.assertTrue((self.cartella / "revisioni" / f"{prosa.oggi()}-provenienza-02.md").exists())
        self.assertIn("materiale non trovato", self.errore_di("provenienza", str(self.cartella), "manca.md"))
        self.assertIn("almeno il racconto", self.errore_di("provenienza"))

    def test_intestazione_mostra_la_provenienza_solo_se_non_zero(self):
        self.materiale("2026-10-02-variante.md", "Niente in comune con la copia di questo racconto qui.")
        self.assertNotIn("Provenienza", self.cattura(prosa.main, ["prosa.py", "intestazione", str(self.cartella)]))
        self.scrivi("testo.md", self.FRASE_ASSISTENTE + "\n")
        self.materiale("2026-10-03-variante.md", self.FRASE_ASSISTENTE)
        blocco = self.cattura(prosa.main, ["prosa.py", "intestazione", str(self.cartella)])
        self.assertIn("- Provenienza: 100,0% delle parole coincide con 2 materiali marcati", blocco)
        self.assertIn(prosa.AVVERTENZA_PROVENIENZA, blocco)

    def frase(self, n):
        return f"Frase numero {n} con qualche parola in più per fare misura."

    def tappe(self, *argomenti):
        return self.cattura(prosa.main, ["prosa.py", "tappe", str(self.cartella), *argomenti])

    def file_tappe(self):
        return [p.read_text(encoding="utf-8") for p in sorted((self.cartella / "tappe").glob("*.md"))]

    def stesso_testo(self, tappe, testo):
        normale = lambda t: " ".join(prosa.testo_visibile(t).split())
        self.assertEqual(normale("\n\n".join(tappe)), normale(testo))

    def test_tappe_capoversi_e_stacchi(self):
        capoverso = " ".join(self.frase(n) for n in range(8))  # circa 480 battute
        testo = "\n\n".join([capoverso] * 5 + ["* * *", "Breve scena dopo lo stacco."]) + "\n"
        self.scrivi("testo.md", testo)
        out = self.tappe("--battute", "1000")
        tappe = self.file_tappe()
        self.assertEqual(len(tappe), 4)
        self.assertTrue(tappe[2].rstrip().endswith("* * *"))  # lo stacco chiude la tappa
        self.assertEqual(tappe[3], "Breve scena dopo lo stacco.\n")
        self.stesso_testo(tappe, testo)
        self.assertIn("Tappe: 4", out)
        self.assertNotIn("Frase numero", out)  # mai il testo nell'output

    def test_tappe_capoverso_unico_lunghissimo(self):
        testo = " ".join(self.frase(n) for n in range(100)) + "\n"  # un capoverso, ~6.000 battute
        self.scrivi("testo.md", testo)
        self.tappe()
        tappe = self.file_tappe()
        self.assertGreater(len(tappe), 2)
        for tappa in tappe[:-1]:
            self.assertTrue(tappa.rstrip().endswith("misura."))  # taglio a fine frase
            self.assertLess(abs(prosa.conta_battute(tappa) - prosa.BATTUTE_TAPPA), 70)
        self.assertEqual("".join(t.rstrip("\n") + " " for t in tappe).strip() + "\n", testo)

    def test_tappe_capoverso_poco_oltre_la_misura_resta_intero(self):
        capoverso = " ".join(self.frase(n) for n in range(40))  # ~2.400 battute < 1,5 × 1.800
        inizio = " ".join(self.frase(n) for n in range(25))  # ~1.500: tagliare prima è più vicino
        self.scrivi("testo.md", inizio + "\n\n" + capoverso + "\n")
        self.tappe()
        self.assertEqual(self.file_tappe(), [inizio + "\n", capoverso + "\n"])

    def test_tappe_titolo_apre_tappa_e_stacco_dopo_taglio(self):
        capoverso = " ".join(self.frase(n) for n in range(30))  # ~1.800 battute
        self.scrivi("testo.md", f"Breve.\n\n# Due\n\n{capoverso}\n\n* * *\n\nFine.\n")
        self.tappe()
        tappe = self.file_tappe()
        self.assertEqual(tappe[0], "Breve.\n")
        self.assertTrue(tappe[1].startswith("# Due\n\n"))
        self.assertTrue(tappe[1].rstrip().endswith("* * *"))
        self.assertEqual(tappe[2], "Fine.\n")

    def test_tappe_ricostruite_da_zero_e_tolte_da_importa(self):
        self.scrivi("testo.md", "\n\n".join(" ".join(self.frase(n) for n in range(30)) for _ in range(3)) + "\n")
        self.tappe()
        self.assertEqual(len(self.file_tappe()), 3)
        self.scrivi("testo.md", "Solo questo.\n")
        self.tappe()
        self.assertEqual(self.file_tappe(), ["Solo questo.\n"])
        sorgente = self.radice / "bozza.md"
        sorgente.write_text("Nuovo.\n", encoding="utf-8")
        self.importa(sorgente)
        self.assertEqual(self.file_tappe(), [])

    def test_tappe_opzione_battute(self):
        for valore in ("abc", "50", "-3"):
            with self.subTest(valore=valore):
                self.assertIn("--battute vuole", self.errore_di("tappe", str(self.cartella), "--battute", valore))
        self.assertIn("solo con «tappe»", self.errore_di("conta", str(self.cartella), "--battute", "900"))

    def test_cli_output_utf8_anche_con_codifica_legacy(self):
        ambiente = dict(os.environ, PYTHONIOENCODING="cp1252")
        risultato = subprocess.run(
            [sys.executable, str(Path(prosa.__file__).resolve()), "controlla", str(self.cartella)],
            capture_output=True, env=ambiente, check=False,
        )
        self.assertEqual(risultato.returncode, 0, risultato.stderr)
        output = risultato.stdout.decode("utf-8")
        self.assertIn("più", output)
        self.assertIn("«noto»", output)


def prosa_sintetica(seme, quante=60, coda_extra=()):
    """Prosa italiana inventata per i test: frasi brevi da piccoli elenchi, ripetibili col seme."""
    r = random.Random(seme)
    soggetti = ["Il cane", "La vicina", "Mio fratello", "Il postino", "Una ragazza", "Il barista"]
    verbi = ["attraversa la piazza", "guarda il muro", "apre la finestra", "aspetta il tram",
             "conta le monete", "chiude la porta"]
    code = ["e poi si ferma", "senza dire niente", "come ogni sera", "anche se piove",
            "ebbene come sempre", "con le mani in tasca"] + list(coda_extra)
    return " ".join(f"{r.choice(soggetti)} {r.choice(verbi)} {r.choice(code)}." for _ in range(quante))


class VoceTest(unittest.TestCase):
    """Misure di voce (officina/stilometria.md), solo con testi sintetici."""

    def setUp(self):
        temporanea = tempfile.TemporaryDirectory(prefix="officina-voce-")
        self.addCleanup(temporanea.cleanup)
        self.radice = Path(temporanea.name)
        for nome, valore in (("RADICE", self.radice), ("RACCONTI", self.radice / "racconti")):
            modifica = patch.object(prosa, nome, valore)
            modifica.start()
            self.addCleanup(modifica.stop)

    def racconto(self, nome, testo, stato="consolidato", materiali=()):
        cartella = self.radice / "racconti" / nome
        (cartella / "materiali").mkdir(parents=True)
        (cartella / "scheda.md").write_text(f"---\nstato: {stato}\nmodalita: breve\n---\n", encoding="utf-8")
        (cartella / "testo.md").write_text(testo, encoding="utf-8")
        for i, corpo in enumerate(materiali, 1):
            (cartella / "materiali" / f"2026-01-0{i}-variante.md").write_text(
                "# Variante\n\n- Autore del testo: assistente (racconto-scrittura, variante)\n\n" + corpo + "\n",
                encoding="utf-8")
        return cartella

    def marcatori(self, contenuto):
        f = self.radice / "strumenti" / "marcatori_voce.txt"
        f.parent.mkdir(exist_ok=True)
        f.write_text(contenuto, encoding="utf-8")

    def cattura(self, funzione, *args, **kwargs):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            funzione(*args, **kwargs)
        return out.getvalue()

    def frasi_finte(self, lunghezze, racconto="r", stacco_a=None):
        out = []
        for i, n in enumerate(lunghezze):
            out.append({"racconto": racconto, "indice": i, "capoverso": i + 1,
                        "testo": " ".join(["parola"] * n) + ".", "parole": n, "quota": 0.0,
                        "nuovo_capoverso": True, "stacco_prima": i == stacco_a})
        return out

    # Finestre, bande, distanze.

    def test_finestre_a_frasi_intere_mezzo_passo_e_stacchi(self):
        fr = self.frasi_finte([5] * 8, stacco_a=4)
        segs = prosa.segmenti(fr, lambda f: True)
        self.assertEqual([len(s) for s in segs], [4, 4])
        fin = prosa.finestre(segs, 10)
        self.assertTrue(all(f["parole"] >= 10 for f in fin))
        # due frasi per finestra, una nuova ogni frase (mezza finestra), mai attraverso lo stacco
        self.assertEqual([f["chiave"][1:] for f in fin], [(0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7)])
        self.assertEqual(prosa.finestre(segs, 100), [])

    def test_segmenti_spezzati_dalle_frasi_escluse(self):
        fr = self.frasi_finte([3, 3, 3, 3])
        fr[1]["quota"] = 1.0
        self.assertEqual([[f["indice"] for f in s] for s in prosa.zona_autore(fr)], [[0], [2, 3]])
        self.assertEqual([[f["indice"] for f in s] for s in prosa.zona_contrasto(fr)], [[1]])

    def test_banda_poche_finestre_dentro_e_fuori(self):
        self.assertEqual(prosa.banda([1, 2, 3], 2)[0], "poche finestre")
        valori = list(range(1, 21))
        self.assertEqual(prosa.banda(valori, 10)[0], "dentro")
        self.assertEqual(prosa.banda(valori, 25)[0], "oltre il massimo osservato")
        self.assertEqual(prosa.banda(valori, 0)[0], "sotto il minimo osservato")
        self.assertEqual(prosa.banda(valori, 19.9)[0], "oltre il 95° percentile")
        self.assertTrue(prosa.oltre("oltre il 95° percentile"))
        self.assertFalse(prosa.oltre("sotto il minimo osservato"))
        self.assertAlmostEqual(prosa.quantile([0, 10], 0.5), 5)

    def test_delta_e_coseno(self):
        media, dev = [0.1, 0.2, 0.3], [0.05, 0.1, 0.0]
        self.assertEqual(prosa.delta(media, media, dev), 0)
        self.assertAlmostEqual(prosa.delta([0.15, 0.2, 0.9], media, dev), 0.5)  # la parola senza varianza non conta
        a, b = [1.0, -2.0, 0.5], [0.3, 1.0, -1.0]
        self.assertAlmostEqual(prosa.coseno(a, b), prosa.coseno(b, a))
        self.assertAlmostEqual(prosa.coseno(a, a), 0)
        self.assertAlmostEqual(prosa.coseno(a, [-x for x in a]), 2)
        voc = ["il", "cane", "piazza"]
        uno = "Il cane attraversa la piazza."
        self.assertEqual(prosa.vettore(uno, voc), prosa.vettore(uno + " " + uno, voc))

    def test_scegli_parole_senza_pronomi_nomi_e_con_culling(self):
        comune = "Io e Bruno e il cane e il gatto sulla strada. "
        a = (comune + "Il treno parte presto. ") * 40
        b = (comune + "Il mare resta calmo. ") * 40
        parole_ = prosa.scegli_parole({"a": a, "b": b})
        self.assertNotIn("io", parole_)      # pronome personale
        self.assertNotIn("bruno", parole_)    # quasi sempre maiuscola: nome proprio
        self.assertIn("e", parole_)
        self.assertNotIn("treno", parole_)   # concentrata in un solo racconto: esce col culling
        self.assertIn("il", parole_)
        self.assertIn("treno", prosa.scegli_parole({"a": a}))  # un racconto solo: niente culling

    def test_spiega_parole_in_eccesso_e_mancanti(self):
        testo = prosa_sintetica(1, 120)
        rif = prosa.Riferimento([prosa.frasi_da_testo(testo)], 40)
        self.assertTrue(rif.basta())
        eccesso, mancanti = rif.spiega("La vicina guarda il muro. " * 4 + "Il tram e il tram e il tram.")
        self.assertIn("tram", [w for _, w, _, _ in eccesso])
        self.assertTrue(all(z < -1.5 and attese >= 1.5 for z, _, _, attese in mancanti))
        self.assertTrue(rif.delta_propri())

    def test_auc(self):
        self.assertEqual(prosa.auc([3, 4], [1, 2]), 1.0)
        self.assertEqual(prosa.auc([1, 2], [1, 2]), 0.5)
        self.assertIsNone(prosa.auc([], [1]))

    # Profilo numerico.

    def test_similitudini_strette_e_come_contati_a_parte(self):
        p = prosa.profilo_testo("Pesa come un mattone. Come stai? Lo dico come penso.", [])
        n = 10
        self.assertEqual(p["similitudini strette ‰"], prosa.per_mille(1, n))
        self.assertEqual(p["«come» ‰"], prosa.per_mille(3, n))

    def test_connettivi_di_raccordo_senza_quindi(self):
        self.assertNotIn("quindi", prosa.CONNETTIVI)
        self.assertIn("tuttavia", prosa.CONNETTIVI)
        p = prosa.profilo_testo("Quindi resto. Tuttavia esco.", [])
        self.assertEqual(p["connettivi di raccordo ‰"], prosa.per_mille(1, 4))
        self.assertEqual(p["quindi, invece, comunque ‰"], prosa.per_mille(1, 4))
        self.assertEqual(prosa.gruppo_di("gerundi in coda ‰"), prosa.GRUPPO_SEGNALI)
        self.assertEqual(prosa.gruppo_di("gerundi ‰"), prosa.GRUPPO_VOCE)

    def test_punteggiatura_e_domande_solo_nella_narrazione(self):
        p = prosa.profilo_testo("Resto qui; aspetto. «Vieni; dai!» Perché resto? Ebbene, resto.", [])
        self.assertEqual(p["punto e virgola nella narrazione ‰"], prosa.per_mille(1, 9))
        self.assertEqual(p["esclamativi nella narrazione ‰"], 0)
        self.assertEqual(p["domande nella narrazione ‰"], prosa.per_mille(1, 9))

    def test_marcatori_assenti_vuoti_validi_e_regex_non_valida(self):
        self.assertEqual(prosa.marcatori_voce(), [])
        self.assertNotIn("marcatori di voce ‰", prosa.profilo_testo("Ebbene, sì.", None))
        self.marcatori("# solo commenti\n\n")
        self.assertEqual(prosa.marcatori_voce(), [])
        self.marcatori("ebbene\ntutto sommato\n")
        m = prosa.marcatori_voce()
        self.assertEqual(prosa.conta_marcatori("Ebbene, resto. Tutto sommato credo. Ebbenezer no.", m), 2)
        self.assertEqual(prosa.profilo_testo("Ebbene, resto.", m)["marcatori di voce ‰"], prosa.per_mille(1, 2))
        self.marcatori("(\n")
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            prosa.marcatori_voce()
        self.assertIn("regex non valida", err.getvalue())

    # Provenienza alla frase e corpus.

    MATERIALE = "La lampada del corridoio resta accesa tutta la notte senza che nessuno la spenga."

    def test_frasi_racconto_riportano_la_coincidenza_alla_frase(self):
        mio = "Torno a casa presto stasera. "
        c = self.racconto("uno", mio + self.MATERIALE + "\n\n* * *\n\nFine del giro.\n", materiali=[self.MATERIALE])
        fr = prosa.frasi_racconto(c)
        self.assertEqual([f["quota"] for f in fr], [0.0, 1.0, 0.0])
        self.assertEqual([f["stacco_prima"] for f in fr], [False, False, True])
        self.assertEqual(prosa.parole_segmenti(prosa.zona_autore(fr)), len(prosa.parole(mio + "Fine del giro.")))

    def test_corpus_solo_consolidati_esclude_coincidenze_quasi_totali(self):
        self.racconto("mio", prosa_sintetica(2, 30) + "\n\n" + self.MATERIALE + "\n", materiali=[self.MATERIALE])
        self.racconto("bozza", prosa_sintetica(3, 30) + "\n\n" + self.MATERIALE + "\n",
                      stato="stesura", materiali=[self.MATERIALE])
        self.racconto("copiato", self.MATERIALE + "\n", materiali=[self.MATERIALE])
        (self.radice / "racconti" / "_modello").mkdir()
        corpus = prosa.corpus_voce()
        self.assertEqual(list(corpus["autore"]), ["mio"])
        self.assertEqual(sorted(corpus["contrasto"]), ["bozza", "mio"])
        self.assertEqual([r for r, _ in corpus["esclusi"]], ["copiato"])
        testo_autore = prosa.testo_segmenti(corpus["autore"]["mio"])
        self.assertNotIn("lampada", testo_autore)

    def test_brani_esempi_salta_formato_e_metadati(self):
        voce = self.radice / "voce"
        voce.mkdir()
        self.assertEqual(prosa.brani_esempi(), "")
        (voce / "esempi.md").write_text(
            "# Brani\n\n```\n## <titolo>\n- Racconto: <nome>\n\n<il brano>\n```\n\n## Brani\n\nIntro.\n\n"
            "## Uno\n- Racconto: a · Perché è qui: prova\n\nIl primo brano.\n\n"
            "## Due\n- Racconto: b · Perché è qui: prova\n\nIl secondo brano.\n", encoding="utf-8")
        self.assertEqual(prosa.brani_esempi(), "Il primo brano.\n\nIl secondo brano.")

    # Comandi.

    def test_confronta_esclude_dal_riferimento_le_frasi_coincidenti(self):
        mio = prosa_sintetica(4, 40)
        c = self.racconto("uno", mio + "\n\n" + self.MATERIALE + "\n", stato="stesura", materiali=[self.MATERIALE])
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("Una barca rossa scivola lenta sul lago grigio.", encoding="utf-8")
        report = self.cattura(prosa.cmd_confronta, str(passaggio), str(c))
        self.assertIn(f"Stesso racconto: {len(prosa.parole(mio))} parole senza coincidenze", report)
        self.assertIn("Corpus di voce: 0 parole da 0 racconti consolidati", report)
        self.assertIn("| terne ‰ |", report)
        self.assertIn("non dice chi ha scritto", report)
        for parola in ("IA", "umano", "intelligenza artificiale"):
            self.assertNotIn(parola, report)

    def test_confronta_segnala_cio_che_esce_dalla_banda(self):
        self.marcatori("ebbene\n")
        frasi_ = prosa_sintetica(5, 200).split(". ")
        c = self.racconto("uno", ". ".join("Ebbene " + f[0].lower() + f[1:] for f in frasi_) + "\n")
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("Tuttavia il tram arriva; inoltre la piazza resta vuota, permettendo di "
                             "attraversare. Tuttavia nessuno parla; inoltre il postino aspetta.", encoding="utf-8")
        report = self.cattura(prosa.cmd_confronta, str(passaggio), str(c))
        self.assertIn("marcatori di voce ‰: sotto il minimo osservato (stesso racconto, corpus)", report)
        self.assertIn("connettivi di raccordo ‰: oltre il massimo osservato", report)
        self.assertIn("Non si riscrive per riportare un numero dentro la banda", report)

    def test_voce_con_corpus_vuoto_come_nel_modello_pubblico(self):
        report = self.cattura(prosa.main, ["prosa.py", "voce"])
        self.assertIn("non c'è ancora un corpus di voce", report)
        self.assertIn("marcatori_voce.txt è vuoto o assente", report)

    def test_voce_misure_affidabilita_e_salva(self):
        self.marcatori("ebbene\n")
        contrasto = prosa_sintetica(9, 60, coda_extra=["tuttavia in modo diverso"])
        self.racconto("primo", prosa_sintetica(6, 150) + "\n\n" + contrasto + "\n", materiali=[contrasto])
        self.racconto("secondo", prosa_sintetica(7, 150) + "\n")
        report = self.cattura(prosa.main, ["prosa.py", "voce", "--salva"])
        for sezione in ("Profilo per racconto", "Similitudini: due conteggi diversi",
                        "Affidabilità per lunghezza", "Variazione tra racconti", "Definizioni"):
            self.assertIn(sezione, report)
        self.assertIn("| primo | 100 |", report)
        self.assertIn("Contrasto per racconto: primo", report)
        salvati = list((self.radice / "voce" / "misure").glob("*-misure.md"))
        self.assertEqual(len(salvati), 1)

    def test_deriva_senza_riferimento_e_con_finestra(self):
        c = self.racconto("solo", self.MATERIALE + "\n", stato="stesura", materiali=[self.MATERIALE])
        self.assertIn("Non abbastanza testo di riferimento", self.cattura(prosa.cmd_deriva, str(c), 20))
        self.racconto("base", prosa_sintetica(8, 150) + "\n")
        report = self.cattura(prosa.main, ["prosa.py", "deriva", str(c), "--finestra", "20"])
        self.assertIn("contro le finestre del corpus di voce", report)
        self.assertIn("Finestre oltre la banda:", report)
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            self.cattura(prosa.main, ["prosa.py", "conta", str(c), "--finestra", "20"])
        self.assertIn("solo con «deriva»", err.getvalue())

    def test_testo_intero_dichiarato_entra_nel_corpus_e_non_nel_contrasto(self):
        testo = prosa_sintetica(12, 40) + "\n\n" + self.MATERIALE + "\n"
        c = self.racconto("dichiarato", testo, materiali=[self.MATERIALE, testo])
        self.assertEqual([r for r, _ in prosa.corpus_voce()["esclusi"]], ["dichiarato"])
        scheda = c / "scheda.md"
        scheda.write_text(scheda.read_text(encoding="utf-8").replace(
            "modalita: breve\n", "modalita: breve\nvoce_testo_intero: sì # lo dichiaro mio\n"), encoding="utf-8")
        corpus = prosa.corpus_voce()
        self.assertEqual(corpus["esclusi"], [])
        self.assertEqual(corpus["dichiarati"], ["dichiarato"])
        self.assertEqual(corpus["contrasto"], {})
        self.assertIn("lampada", prosa.testo_segmenti(corpus["autore"]["dichiarato"]))
        report = self.cattura(prosa.cmd_voce)
        self.assertIn("dichiarato: testo intero dichiarato dall'autore", report)
        passaggio = self.radice / "passaggio.md"
        passaggio.write_text("Una barca rossa scivola lenta sul lago grigio.", encoding="utf-8")
        confronto = self.cattura(prosa.cmd_confronta, str(passaggio), str(c))
        self.assertIn(f"Stesso racconto: {len(prosa.parole(testo))} parole, testo intero dichiarato", confronto)
        self.assertIn("testo intero dichiarato dall'autore: dichiarato", confronto)

    def test_voce_testo_intero_valori_ammessi(self):
        c = self.racconto("valori", "Testo.\n")
        scheda = c / "scheda.md"
        for valore, atteso in (("sì", True), ("si", True), ("no", False), ("", False)):
            scheda.write_text(f"---\nstato: consolidato\nvoce_testo_intero: {valore}\n---\n", encoding="utf-8")
            self.assertEqual(prosa.testo_intero_dichiarato(c), atteso)
        scheda.write_text("---\nvoce_testo_intero: tutto\n---\n", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
            prosa.testo_intero_dichiarato(c)
        self.assertIn("voce_testo_intero non supportato", err.getvalue())

    def test_deriva_senza_corpus_usa_le_zone_del_racconto(self):
        c = self.racconto("bozza", prosa_sintetica(11, 150) + "\n", stato="stesura")
        report = self.cattura(prosa.cmd_deriva, str(c), 20)
        self.assertIn("contro le finestre delle zone senza coincidenze dello stesso racconto", report)
        self.assertNotIn("del zone", report)

    def test_aiuto_elenca_voce_e_deriva(self):
        aiuto = self.cattura(prosa.main, ["prosa.py", "aiuto"])
        for comando in ("voce [--salva]", "deriva <racconto>", "--finestra", "voce/misure/"):
            self.assertIn(comando, aiuto)


if __name__ == "__main__":
    unittest.main()
