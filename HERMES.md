# Hermes Agent integration

This repo packages `projectsmd` as a standalone CLI plus agent skill for Hermes Agent. Use it when a project has multiple tasks, spans sessions, or needs durable agent-human context.

## Install from GitHub

```bash
source "$HOME/.cargo/env"
cargo install --git https://github.com/am423/projectsmd-hermes.git
projectsmd --version
```

## Install the Hermes skill

```bash
projectsmd skill install --framework hermes
```

That installs the embedded skill to:

```text
~/.hermes/skills/projectsmd/
```

The source skill text is also committed at `agent-skill.md` and embedded in the Rust crate under `src/skill/SKILL.md`.

## Test workflow with Hermes

In a project directory:

```bash
projectsmd init \
  --name "Hermes Test" \
  --owner "Adam" \
  --agent "Hermes" \
  --tags "hermes,agent" \
  --description "A test project for validating ProjectsMD with Hermes Agent." \
  --core-value "Keep project context durable across Hermes sessions."
projectsmd status
projectsmd next
projectsmd validate
```

For existing codebases:

```bash
projectsmd init --brownfield
projectsmd status
```

At the end of a Hermes session:

```bash
projectsmd session
```

Hermes should keep `project.md` updated as the source of truth:

- mark tasks complete only after verification
- log decisions as they happen
- update Current State before stopping
- append session notes instead of overwriting history

## Included files

- `README.md` — user documentation and command reference
- `agent-skill.md` — agent-facing workflow instructions
- `template.md` — canonical `project.md` template
- `specification.md` — project.md format specification
- `validate.py` — standalone validator helper
- `workflow-diagram.html` — visual workflow overview

## Local development checks

```bash
source "$HOME/.cargo/env"
cargo fmt --check
cargo test
cargo build --release
./target/release/projectsmd --version
```
