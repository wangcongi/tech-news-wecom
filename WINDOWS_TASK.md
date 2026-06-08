# Windows Task Scheduler

Use this path if you want to run the project locally instead of GitHub Actions.

## Install

Open PowerShell in the repo root and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\install-windows-task.ps1 -Times '08:57','11:26' -Force
```

## What it does

- Registers a task named `Tech News WeCom`
- Runs `scripts\run-once.ps1`
- Executes `python -m tech_news_wecom.cli run-once`
- Writes logs to `logs\run-once-YYYYMMDD.log`

## Remove

```powershell
.\scripts\uninstall-windows-task.ps1
```

## Notes

- The machine must be on and awake at the trigger time.
- The task runs under the current Windows user.
- If Python is installed in `.venv`, the runner uses that first.
