# Fresh-agent portability test prompt

Give the following prompt verbatim to a fresh Codex agent whose starting working
directory is the disposable example repository. Do not provide prior conversation
history or access to the template or originating repository.

```text
You are entering this repository as a fresh successor agent. Use only the files
and git state available inside this repository. Do not search for, inspect, or rely
on any parent, sibling, template-origin, or unrelated repository.

Perform a read-only portability and succession assessment. Do not modify files,
run external actions, access any data source, or invent research authority.

1. Follow the repository's prescribed orientation procedure exactly. Independently
   reload authoritative state; treat HANDOFF.md only according to the authority it
   actually has.
2. Inspect repository status and the relevant local source, tests, configuration,
   and supported commands.
3. Report, with file-based evidence:
   - the founding research intent and whether it has been adopted or remains a
     placeholder;
   - the currently adopted decisions;
   - the research evidence and its status;
   - the roadmap maturity, active work, blockers, and permitted next actions;
   - what HANDOFF.md contributes and every kind of authority it cannot grant;
   - whether any experiment, protected-data access, external action, validation,
     or deployment is currently authorized.
4. Run only the documented local static/unit checks that require no network or
   external data. Report their exact outcomes. A passing check is implementation
   evidence only; do not call it proof of scientific validity or portability.
5. Identify any contradiction between HANDOFF.md and authoritative repository
   state. If there is none, say so explicitly.
6. Produce a proposed replacement successor handoff, following the repository's
   standard, as a fenced Markdown block. Do not write it to disk. It must preserve
   hot context while explicitly remaining non-authoritative.
7. End with the repository's successor acknowledgment fields completed.

Your final response must also state whether you needed knowledge or files from
outside this repository. Successful completion is evidence for a human reviewer;
do not declare the succession/portability test proven merely because you performed
it.
```

