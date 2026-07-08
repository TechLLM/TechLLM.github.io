# Error Handling

Tags: #errors #execution

If a note cannot be read, report the path and continue with other readable Markdown files.
If the available budget is zero or negative, exit with a clear error.
For transient command failures, retry once after checking the exact error message.
