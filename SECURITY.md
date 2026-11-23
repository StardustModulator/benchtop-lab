<!-- SPDX-FileCopyrightText: 2026 Benchtop Lab contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Security policy

Benchtop Lab is a teaching project that runs on learners' laptops and, for some projects, moves a real robot arm.
We take reports seriously and fix confirmed problems in the open.

## Reporting a vulnerability

**Please do not open a public issue, discussion or pull request for a security problem.**

Report it privately through GitHub:

1. Go to the repository's [Security tab](https://github.com/StardustModulator/benchtop-lab/security).
2. Choose **Report a vulnerability**
   ([direct link](https://github.com/StardustModulator/benchtop-lab/security/advisories/new)).
3. Describe the problem, the affected version or commit, and the steps to reproduce it. A minimal proof of concept
   helps; please do not include real credentials or other people's data.

Only the maintainers can read the report. GitHub's documentation explains the process:
[Privately reporting a security vulnerability](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).

## What to expect

| Step | Target |
| --- | --- |
| We acknowledge your report | within 3 working days |
| We confirm or decline it, with reasons | within 10 working days |
| We release a fix for a confirmed problem | as soon as practical, normally within 30 days |

Benchtop Lab is maintained by volunteers, so these are targets, not guarantees. We will keep you informed, credit you
in the advisory unless you prefer otherwise, and agree a disclosure date with you. There is no bug bounty.

## Supported versions

The project is pre-release. Security fixes land on `main` only. After v1.0 this table will list the supported
release lines.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| anything older | No |

## What counts

In scope:

- Code execution, file overwrite or path traversal when Benchtop Lab opens a dataset, checkpoint, rubric, report or
  environment export from an untrusted source.
- Leaks of credentials (for example a Hugging Face token) into logs, reports, datasets or exports.
- A way to move a real arm without the explicit `--allow-motion` flag, or past its configured safety limits.
- Weaknesses in this repository's CI or release setup that would let someone tamper with what learners install.

Out of scope:

- Vulnerabilities in LeRobot, MuJoCo, PyTorch or other dependencies: please report those upstream. Tell us too if
  Benchtop Lab makes one of them easier to reach.
- Loading a policy checkpoint you do not trust. Checkpoints can run arbitrary code by design in the wider
  ecosystem; only load ones from sources you trust.
- A policy scoring higher than it should on the grader. That is a grading bug, and a normal issue is welcome.

## How we protect the project

- No secrets are stored in the repository; `gitleaks` scans every commit locally and the full history in CI.
- CI workflows use actions pinned to full commit SHAs and a read-only token by default.
- Dependencies are locked (`uv.lock`), limited to permissive licences, and updated through reviewed pull requests.
- Benchtop Lab has no telemetry, analytics or tracking of any kind.
