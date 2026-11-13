"""Prove di avvio da una copia pulita e protezione dei file locali."""

from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import prepara

RADICE = Path(__file__).resolve().parent.parent


class DistribuzioneTest(unittest.TestCase):
    def setUp(self):
        temporanea = tempfile.TemporaryDirectory(prefix='officina-distribuzione-')
        self.addCleanup(temporanea.cleanup)
        self.radice = Path(temporanea.name)
        for cartella in ('modelli', 'esempi', 'racconti/_modello'):
            shutil.copytree(RADICE / cartella, self.radice / cartella)
        (self.radice / 'strumenti').mkdir()
        for nome in ('prosa.py', 'prepara.py'):
            shutil.copyfile(RADICE / 'strumenti' / nome, self.radice / 'strumenti' / nome)

    def comando(self, *argomenti):
        risultato = subprocess.run([sys.executable, '-X', 'utf8', *argomenti],
                                   cwd=self.radice, capture_output=True, encoding='utf-8')
        self.assertEqual(risultato.returncode, 0, risultato.stderr + risultato.stdout)
        return risultato.stdout

    def test_avvio_rapido_e_fonte_immutata(self):
        self.comando('strumenti/prepara.py')
        originale = (self.radice / 'esempi/il-faro.md').read_bytes()
        self.comando('strumenti/prosa.py', 'nuovo', 'il-faro')
        scheda = self.radice / 'racconti/il-faro/scheda.md'
        scheda.write_text(re.sub(r'(?m)^fonte_file:.*$', 'fonte_file: esempi/il-faro.md',
                                scheda.read_text(encoding='utf-8')), encoding='utf-8')
        fonte = json.loads(self.comando('strumenti/prosa.py', 'fonte', 'il-faro'))
        self.assertEqual(Path(fonte['fonte_file']), (self.radice / 'esempi/il-faro.md').resolve())
        self.comando('strumenti/prosa.py', 'importa', 'esempi/il-faro.md', 'il-faro')
        self.assertIn('Battute', self.comando('strumenti/prosa.py', 'conta', 'il-faro'))
        self.assertIn('# Controlli', self.comando('strumenti/prosa.py', 'controlla', 'il-faro'))
        self.assertEqual(originale, (self.radice / 'esempi/il-faro.md').read_bytes())
        self.assertTrue((self.radice / 'racconti/il-faro/testo.md').is_file())

    def test_preparazione_non_sovrascrive_e_completa_file_mancanti(self):
        self.assertEqual(len(prepara.prepara(self.radice)), 5)
        profilo = self.radice / 'voce/profilo.md'
        privato = b'Profilo locale da conservare\r\n'
        profilo.write_bytes(privato)
        (self.radice / 'voce/esempi.md').unlink()
        self.assertEqual(prepara.prepara(self.radice), ['voce/esempi.md'])
        self.assertEqual(profilo.read_bytes(), privato)
        self.assertEqual(prepara.prepara(self.radice), [])

    @unittest.skipUnless(shutil.which('git'), 'Git non disponibile')
    def test_git_esclude_materiali_privati_ma_include_modelli(self):
        shutil.copyfile(RADICE / '.gitignore', self.radice / '.gitignore')
        ambiente = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        subprocess.run(['git', 'init', '--quiet', str(self.radice)], check=True,
                       capture_output=True, env=ambiente)
        privati = ['racconti/inedito/testo.md', 'racconti/inedito/materiali/proposta.md',
                   'racconti/_modello/appunti-privati.md', 'bozze/inedito.txt',
                   'voce/profilo.md', 'voce/esempi.md', 'voce/scelte-redazionali.md',
                   'strumenti/stilemi_extra.txt', '.claude/settings.local.json',
                   '.claude/settings.json', '.codex/config.toml', '.env',
                   'credentials.json', 'esportazione.docx', 'archivio/registro.md']
        pubblici = ['racconti/_modello/scheda.md', 'racconti/_modello/stato.md',
                    'modelli/voce/profilo.md', 'esempi/il-faro.md',
                    '.agents/skills/racconto-nuovo/SKILL.md',
                    '.claude/skills/racconto-nuovo/SKILL.md', 'strumenti/prosa.py']
        for percorso in privati + pubblici:
            with self.subTest(percorso=percorso):
                esito = subprocess.run(['git', '-C', str(self.radice), 'check-ignore',
                                        '--quiet', percorso], env=ambiente)
                self.assertEqual(esito.returncode, 0 if percorso in privati else 1)


if __name__ == '__main__':
    unittest.main()
