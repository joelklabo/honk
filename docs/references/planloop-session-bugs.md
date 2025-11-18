- doesn't seem like the agents.md was updated but the agent did read the document
- we need a way to visualize what the tasks are in planloop, need the web
- is there a reason it's always 10 tasks?
- there was an error syncing uv dependencies right after the agent had to update Rust for pydantic-core, then edited the pyproject.toml
- its not doing tdd or mentioning it
- whatever project you are in needs to setup the venv
- We need logs from planloop, I want a clear transcript of the messages back and forth (it looks like notes are being used for valuable information. For example: 

"Installed 48 packages total",                                 │
   │ 18  +      "Note: Had to resolve Rust version issues for pydantic-core    │
   │        compilation

- the agents stops after the first task. but is on the right track
- planloop knows when the agent finishes something, so maybe we can use that to poke the agent somehow and pick up the next task
- The webview could show like a pipeline with a row for each task. Then it goes from in progress to in review I guess or something and then done with the commit hash
