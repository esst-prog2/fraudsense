# Process log

One row per step: the step, what the tool (Claude Code) did, and what I decided.

| Step | What the tool did | What I decided |
| --- | --- | --- |
| Start the process log | Created PROCESS.md with this table, appended the rule to PLANNING_LOG.md, and committed both. | After each step from now on, the tool commits and adds a row here with the step, what the tool did, and what I decided. |
| Install gstack and run its setup | Cloned https://github.com/garrytan/gstack into ~/.claude/skills/gstack (commit 3c15b72, version 1.99.3.0). Setup needs Bun and it was missing, so installed Bun 1.4.2 with the official installer, then ran `./setup` for Claude Code; it finished with exit 0, built the browse tool, downloaded its Chromium, copied the skills into ~/.claude/skills and added one Stop hook to ~/.claude/settings.json. Nothing in this repo changed apart from this row and the planning log. | Install gstack from that repository and run its setup. |
| Write the promo page content | Ran gstack /office-hours; after two of its questions (demo goal, honest scoreboard) I redirected it to the real task. It then ran score, explain, evaluate and the 82 tests to check every claim, confirmed the Sparkov counts in reports/spike_counts.txt and that the GitHub repo URL answers, and wrote docs/content.md: what it is for, who it is for, how to try it, and the Sparkov results. No code was changed and no design doc was written. | The page is content for a static GitHub Pages promo page, due today 20:00; no new features or code changes; the page links to the GitHub repo because the tool is command-line; it states the Sparkov results (precision 0.136, recall 0.433) openly; nothing personal goes on it; gstack learnings stay project-scoped. |
