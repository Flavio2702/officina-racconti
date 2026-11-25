# Crediti

L'officina adatta, traduce e riscrive in italiano idee e procedure da quattro progetti open source. Le licenze originali sono nella cartella `LICENZE/`. Le fonti delle nozioni di lingua e di mestiere sono in `officina/fonti.md`.

## creative-writing-skills

- Autore: haowjy · https://github.com/haowjy/creative-writing-skills
- Licenza: Apache 2.0 (`LICENZE/creative-writing-skills-APACHE-2.0.txt`)
- Materiale adattato:
  - i canali di lettura, «fidarsi del lettore» ed «economia» → `officina/principi.md` (tradotti e riscritti, con fonti di ricerca aggiunte);
  - il catalogo dei difetti narrativi dei modelli → `officina/difetti-ai.md`, parte 2 (tradotto e condensato);
  - la simulazione di lettore → `.agents/skills/racconto-lettore/` (riscritta con personas legate alle destinazioni della raccolta);
  - i livelli di revisione e il *line edit* → `.agents/skills/racconto-revisione/` (ridotti e adattati al racconto e alle norme italiane);
  - le modalità di scrittura → `.agents/skills/racconto-scrittura/` (ridotte a raccordo, variante, abbozzo, lucidatura);
  - le domande prima di ogni passaggio (*muse*) → `AGENTS.md`.
- Modifiche principali: traduzione in italiano; eliminazione della regola contro la lineetta, incompatibile con la punteggiatura dei dialoghi in italiano; eliminazione di knowledge base, canone e orchestrazione multi-agente.

## story-skills

- Autore: Daniel Dewhurst · https://github.com/danjdewhurst/story-skills
- Licenza: MIT (`LICENZE/story-skills-MIT.txt`)
- Materiale adattato:
  - la forma breve (cambiamento unico, effetto unico, perimetro, fili MICE) → `officina/forma-breve.md`;
  - il nucleo in un paragrafo e la scaletta inversa → `.agents/skills/racconto-nucleo/`, `.agents/skills/racconto-nuovo/`;
  - riferimenti di scena (distanza psichica, sottotesto, esposizione, flashback, scena e sequel) → `officina/scena.md`;
  - l'idea di uno strumento che «conta e non giudica» → `strumenti/prosa.py` (riscritto da zero, con liste italiane).

## unslop

- Autore: Mohamed Abdallah · https://github.com/MohamedAbdallah-14/unslop
- Licenza: MIT (`LICENZE/unslop-MIT.txt`)
- Materiale adattato: il principio «sottrai, non aggiungere» e i segnali del *voice-match* → `.agents/skills/racconto-voce/`, `modelli/voce/profilo.md`.

## EveryDay-Writer

- Autore: KAGUURA · https://github.com/Deupaxx/EveryDay-Writer
- Licenza: MIT (`LICENZE/everyday-writer-MIT.txt`)
- Materiale adattato: il formato della *failure library* → `modelli/voce/difetti-personali.md`; la sezione «cosa non fai mai» del profilo → `modelli/voce/profilo.md`.

## Metodi di stilometria

Le misure di `confronta`, `deriva` e `voce` in `strumenti/prosa.py` riprendono metodi pubblicati: Delta di Burrows con il *culling* e l'esclusione dei pronomi, Cosine Delta, finestre mobili, AUC. Sono **riscritte da zero** con la sola libreria standard: da questi progetti **non è stato copiato codice**. Le fonti dei metodi sono in `officina/fonti.md` ([F58]–[F66]).

- **stylo**, di M. Eder, J. Rybicki, M. Kestemont, S. Pielström (https://github.com/computationalstylistics/stylo, GPL-3). Idee riprese: distanze Delta, *culling*, *rolling stylometry* (`rolling.delta`, `rolling.classify`), lettura dei risultati come variazione e non come verdetto.
- **faststylometry**, di Fast Data Science (https://github.com/fastdatascience/faststylometry, MIT). Idee riprese: il Delta calcolato su un corpus di riferimento e letto contro una distribuzione invece che contro una soglia fissa.
- **ruzicka**, di M. Kestemont (https://github.com/mikekestemont/ruzicka, MIT). Consultato per la verifica d'autore con gli impostori e la distanza minmax; non adottato, perché attribuisce, e qui non si attribuisce.
- **pyzeta**, del gruppo CLiGS (https://github.com/cligs/pyzeta, GPL-3). Consultato per lo Zeta di Burrows e Craig sulle parole distintive; non adottato.

## Codex

La struttura del progetto (`.agents/skills/`, `agents/openai.yaml`, `AGENTS.md`) segue la documentazione di Codex:

- https://developers.openai.com/codex/skills
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Plugin Google Drive: https://github.com/openai/plugins/tree/main/plugins/google-drive

## Distribuzione pubblica

I contributi originali sono sotto Apache-2.0, come indicato in `LICENSE` e `NOTICE`. Le licenze dei materiali di terzi restano in `LICENZE/`. I modelli di voce distribuiti sono vuoti; i file compilati dagli utenti restano locali.
