"""Crea le impostazioni private dai modelli, senza sovrascrivere file esistenti."""

from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent


def prepara(radice=RADICE):
    sorgenti = [(radice / 'modelli' / 'voce' / nome, radice / 'voce' / nome)
                for nome in ('profilo.md', 'esempi.md', 'difetti-personali.md',
                             'scelte-redazionali.md')]
    sorgenti.append((radice / 'modelli' / 'stilemi_extra.txt',
                     radice / 'strumenti' / 'stilemi_extra.txt'))
    creati = []
    for modello, destinazione in sorgenti:
        contenuto = modello.read_bytes()
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destinazione.open('xb') as file:
                file.write(contenuto)
        except FileExistsError:
            continue
        creati.append(destinazione.relative_to(radice).as_posix())
    return creati


if __name__ == '__main__':
    creati = prepara()
    print('Preparazione completata: {} file creati; file esistenti conservati.'.format(len(creati)))
