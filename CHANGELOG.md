# Changelog

All notable changes to Benchtop Lab are listed here, newest first. The file is generated from the commit history
with [git-cliff](https://git-cliff.org/); do not edit it by hand. Versions follow
[PEP 440](https://peps.python.org/pep-0440/) and the six packages always share one version.


## Unreleased

### Fixes

- **cli:** Make NO_COLOR strip every ANSI code and treat FORCE_COLOR=0 as off
- **cli:** Apply one colour policy to help screens and isolate CLI tests

### Documentation

- Phase 2 plan, architecture, milestones and Claude Code setup
- Add UI excellence standing rule, ui-excellence skill and reviewer checks
- **adr:** Accept ADR-004 and record ADR-010 on copyleft dev tools
- Record S01 in PROGRESS and update CONTRIBUTING setup note

### Build and CI

- Add uv workspace with six src-layout packages and the benchtop CLI
- Add GitHub Actions gate, nightly matrix and repository hygiene files
- Address review of workflows, templates and config tests

### Maintenance

- Add pre-commit hooks, REUSE licensing metadata and Makefile
- Address review of tooling config
- Clarify duplicate-conftest hint and complete S01 licence record
