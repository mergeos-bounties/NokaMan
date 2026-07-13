import { execSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const REPO = 'mergeos-bounties/NokaMan';

function sh(cmd) {
  return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
}

function ensureLabel(name, color, description) {
  try {
    sh(
      `gh label create ${JSON.stringify(name)} --repo ${REPO} --color ${color} --description ${JSON.stringify(description)}`,
    );
  } catch {
    try {
      sh(
        `gh label edit ${JSON.stringify(name)} --repo ${REPO} --color ${color} --description ${JSON.stringify(description)}`,
      );
    } catch {
      // ignore
    }
  }
}

function createIssue(title, body, labels) {
  const dir = mkdtempSync(join(tmpdir(), 'nokaman-issue-'));
  const file = join(dir, 'body.md');
  try {
    writeFileSync(file, body, 'utf8');
    const labelFlags = labels.map((l) => `--label ${JSON.stringify(l)}`).join(' ');
    const out = sh(
      `gh issue create --repo ${REPO} --title ${JSON.stringify(title)} --body-file ${JSON.stringify(file)} ${labelFlags}`,
    );
    console.log(out);
    return out;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

const labels = [
  ['bounty', '5319E7', 'Eligible for MergeOS MRG bounty'],
  ['bounty: feature', 'A2EEEF', 'Feature bounty'],
  ['bounty: bug', 'D73A4A', 'Bug bounty'],
  ['ml', 'B60205', 'Models / scoring / calibration'],
  ['data', 'C5DEF5', 'Samples / rubrics / datasets'],
  ['language', '0E8A16', 'Language pack / localization'],
  ['api', '1D76DB', 'HTTP / SDK for apps'],
  ['nlp', 'D93F0B', 'NLP / ASR / LLM grading'],
  ['reward:25-mrg', 'FEF2C0', 'Target 25 MRG'],
  ['reward:50-mrg', 'FEF2C0', 'Target 50 MRG'],
  ['reward:100-mrg', 'FEF2C0', 'Target 100 MRG'],
  ['reward:200-mrg', 'FEF2C0', 'Target 200 MRG'],
  ['good first issue', '7057FF', 'Good for newcomers'],
  ['documentation', '0075CA', 'Documentation improvements'],
];

for (const [name, color, description] of labels) {
  ensureLabel(name, color, description);
}

const footer = `

## Claim (MergeOS MRG)

1. Follow https://github.com/mergeos-bounties  
2. Star https://github.com/mergeos-bounties/mergeos  
3. Star https://github.com/mergeos-bounties/mergeos-contracts
4. Comment on **this issue**: \`I claim this bounty\`  
5. Comment on MergeOS [Claim Token #1](https://github.com/mergeos-bounties/mergeos/issues/1) with a link to this issue  
6. Open a PR to **NokaMan** (public product repo) with \`Fixes #<this-issue>\`

Policy: [docs/BOUNTY.md](../blob/master/docs/BOUNTY.md)

## Important

Work lands on **https://github.com/mergeos-bounties/NokaMan** — the public product repository.

## Payout

Maintainer reviews PR → merge on NokaMan → **MRG credit** on MergeOS ledger to \`github:<author>\` (25/50/100/200 scale).
`;

const issues = [
  {
    title: '[25 MRG] Docs: LANGUAGES.md catalog of supported langs + exam frameworks',
    labels: ['bounty', 'bounty: feature', 'documentation', 'language', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Document supported languages, CEFR/JLPT/TOPIK/HSK mappings, and how to add a new language pack.

## Acceptance

- [ ] \`docs/LANGUAGES.md\` merged + README link
${footer}`,
  },
  {
    title: '[25 MRG] CLI: nokaman eval batch — score all samples to JSON report',
    labels: ['bounty', 'bounty: feature', 'ml', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Add \`nokaman eval batch --out data/out/batch.json\` that scores every sample file and summarizes CEFR hits.

## Acceptance

- [ ] Command + unit test
- [ ] README example
${footer}`,
  },
  {
    title: '[25 MRG] Expand sample fixtures for EN/KO/JA to 20+ labeled items',
    labels: ['bounty', 'bounty: feature', 'data', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Add synthetic or openly licensed short learner texts with \`expected_cefr\` labels across A1–B2.

## Acceptance

- [ ] ≥20 samples total
- [ ] No private student PII
- [ ] License notes in PR
${footer}`,
  },
  {
    title: '[25 MRG] Rubric schema validation with pydantic',
    labels: ['bounty', 'bounty: feature', 'data', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Validate sample + rubric JSON with pydantic models and clear errors.

## Acceptance

- [ ] Invalid payloads raise helpful errors
- [ ] Existing fixtures validate
${footer}`,
  },
  {
    title: '[50 MRG] Writing scorer: cohesion, grammar error proxies, length norms',
    labels: ['bounty', 'bounty: feature', 'ml', 'nlp', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Improve writing skill scoring beyond token heuristics. Document features and keep offline-safe defaults.

## Acceptance

- [ ] Module + tests
- [ ] Toy model still works without optional deps
${footer}`,
  },
  {
    title: '[50 MRG] Speaking path: score from ASR transcript JSON',
    labels: ['bounty', 'bounty: feature', 'ml', 'nlp', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Accept \`skill=speaking\` inputs that are transcripts (with optional confidence), produce speaking score + feedback bullets.

## Acceptance

- [ ] CLI + fixture
- [ ] Docs for app integration
${footer}`,
  },
  {
    title: '[50 MRG] JLPT band adapter for Japanese assessments',
    labels: ['bounty', 'bounty: feature', 'language', 'ml', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Map NokaMan scores to JLPT N5–N1 style bands for Japanese, alongside CEFR.

## Acceptance

- [ ] Adapter + tests
- [ ] Demo output includes jlpt field for \`ja\`
${footer}`,
  },
  {
    title: '[50 MRG] TOPIK band adapter for Korean assessments',
    labels: ['bounty', 'bounty: feature', 'language', 'ml', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Map scores to TOPIK I/II levels for Korean assessments.

## Acceptance

- [ ] Adapter + tests
- [ ] Demo output includes topik field for \`ko\`
${footer}`,
  },
  {
    title: '[50 MRG] Optional LLM rubric grader (httpx extra)',
    labels: ['bounty', 'bounty: feature', 'nlp', 'ml', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Optional LLM-backed grader behind an interface; default remains ToyAbilityModel. Prefer SpaceXAI / configurable base URL patterns for apps.

## Acceptance

- [ ] Interface + stub/live client
- [ ] CI green without API keys
- [ ] No secrets committed
${footer}`,
  },
  {
    title: '[50 MRG] FastAPI: POST /assess and GET /languages',
    labels: ['bounty', 'bounty: feature', 'api', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Ship optional FastAPI under \`src/nokaman/api/\` for language-learning apps.

## Acceptance

- [ ] Endpoints documented
- [ ] TestClient tests (api extra)
${footer}`,
  },
  {
    title: '[50 MRG] App SDK: TypeScript types + JSON schema for assess response',
    labels: ['bounty', 'bounty: feature', 'api', 'documentation', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Publish stable contract under \`schemas/\` and optional \`sdk/typescript\` types for mobile/web apps.

## Acceptance

- [ ] JSON Schema matches Python payload
- [ ] README integration section
${footer}`,
  },
  {
    title: '[50 MRG] Listening proxy: score comprehension from MCQ + short answer packs',
    labels: ['bounty', 'bounty: feature', 'ml', 'data', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Add listening assessment fixtures (no large audio required): questions + answers → skill score.

## Acceptance

- [ ] Loader + scorer + samples
- [ ] Tests offline
${footer}`,
  },
  {
    title: '[100 MRG] Adaptive testing: next-item selection by ability estimate',
    labels: ['bounty', 'bounty: feature', 'ml', 'reward:100-mrg'],
    body: `## Bounty: 100 MRG

Simple IRT-like or heuristic adaptive loop that picks next prompt based on running ability estimate.

## Acceptance

- [ ] CLI or API session mode
- [ ] Unit tests for selection logic
${footer}`,
  },
  {
    title: '[100 MRG] Fairness pack: score stability across EN/KO/JA length-matched texts',
    labels: ['bounty', 'bounty: feature', 'ml', 'documentation', 'reward:100-mrg'],
    body: `## Bounty: 100 MRG

Eval suite comparing length-matched samples across languages; report bias notes and mitigation ideas.

## Acceptance

- [ ] Metrics script + report fixture
- [ ] Docs/FAIRNESS.md
${footer}`,
  },
  {
    title: '[100 MRG] Calibration pipeline: YAML config, seeds, report dashboard JSON',
    labels: ['bounty', 'bounty: feature', 'ml', 'reward:100-mrg'],
    body: `## Bounty: 100 MRG

Production-shaped calibration loop with config files and export for app dashboards.

## Acceptance

- [ ] configs/example.yaml
- [ ] Resume/idempotent runs
- [ ] Docs
${footer}`,
  },
  {
    title: '[100 MRG] Web demo: paste text → multi-skill radar for language teachers',
    labels: ['bounty', 'bounty: feature', 'api', 'reward:100-mrg'],
    body: `## Bounty: 100 MRG

Lightweight web UI under \`web/\` that calls local NokaMan API and shows skill radar + CEFR.

## Acceptance

- [ ] Local dev README
- [ ] Screenshots in PR
${footer}`,
  },
  {
    title: '[200 MRG] End-to-end product path: multi-lang placement test pack for apps',
    labels: ['bounty', 'bounty: feature', 'ml', 'api', 'language', 'reward:200-mrg'],
    body: `## Bounty: 200 MRG

Ship a polished placement-test pack (EN+KO+JA minimum): prompts, scoring, report suitable for embedding in a language app.

## Acceptance

- [ ] Single CLI/API path
- [ ] Evidence: sample reports for 3 languages
- [ ] License-safe content only
${footer}`,
  },
  {
    title: '[25 MRG] CONTRIBUTING.md + good-first-issue path',
    labels: ['bounty', 'bounty: feature', 'documentation', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Write CONTRIBUTING with setup, tests, and claim flow. Emphasize PRs target public NokaMan only.

## Acceptance

- [ ] File + README link
${footer}`,
  },
  {
    title: '[25 MRG] CI: coverage + ruff format check',
    labels: ['bounty', 'bounty: feature', 'documentation', 'reward:25-mrg', 'good first issue'],
    body: `## Bounty: 25 MRG

Improve CI with pytest-cov threshold and ruff format --check.

## Acceptance

- [ ] CI green
${footer}`,
  },
  {
    title: '[50 MRG] Dataset index: public learner corpora with licenses',
    labels: ['bounty', 'bounty: feature', 'data', 'documentation', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

\`docs/DATASETS.md\` listing public ESL/learner corpora (no redistributing restricted media).

## Acceptance

- [ ] ≥8 rows with license + link
${footer}`,
  },
  {
    title: '[50 MRG] Metrics: band accuracy, adjacent-band accuracy, MAE on score',
    labels: ['bounty', 'bounty: feature', 'ml', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Eval metrics module + CLI export for labeled samples.

## Acceptance

- [ ] \`nokaman eval report\`
- [ ] Unit tests for metrics
${footer}`,
  },
  {
    title: '[50 MRG] Vietnamese + Spanish language packs with rubrics and samples',
    labels: ['bounty', 'bounty: feature', 'language', 'data', 'reward:50-mrg'],
    body: `## Bounty: 50 MRG

Expand VI/ES (or FR/DE) packs: rubrics, samples, demo texts, framework notes.

## Acceptance

- [ ] Rubrics + ≥4 samples each for two languages
- [ ] Tests cover new codes
${footer}`,
  },
];

for (const issue of issues) {
  createIssue(issue.title, issue.body, issue.labels);
}

console.log(`Created ${issues.length} issues on ${REPO}`);
