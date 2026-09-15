# UI Sync Reminder

When the user requests a change to how the site works (e.g., backend logic, schedules, data structures, or system behaviors):
1. Always check if there is a corresponding UI element that might be impacted by this change.
2. If so, proactively remind the user that the UI may need updating to reflect the new behavior.
3. Suggest the necessary UI changes or ask the user for clarification if the UI design needs to be adapted.
4. Do not assume the user only wants the backend changed if the UI explicitly depends on it.

# Git Push Rejection Auto-Correct

When a `git push` fails because the remote contains work that you do not have locally (e.g., from an automated pipeline or cron job), do not stop or ask for help immediately. Instead, automatically run `git pull --rebase` to seamlessly integrate the remote changes, and then retry the `git push`.

# Local Server Link Formatting

Whenever you start a local HTTP or development server, always provide a clickable link to the user formatted with a pointing emoji, exactly like this: 👉 [http://localhost:8080](http://localhost:8080)
