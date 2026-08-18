# CredAudit Web

CredAudit Web is a local browser interface for the CredAudit secret-scanning
engine. It helps security reviewers, auditors, and developers find exposed
credentials in files and folders without uploading evidence to an external
service.

The web app runs on your machine, calls the bundled `engine/` package, and shows
redacted findings by default.

## What It Finds

CredAudit scans for common credential and secret patterns, including:

- API keys and cloud tokens
- Password assignments and password-like values
- Username/password pairs
- Private keys
- JWTs and high-entropy strings
- Service tokens such as GitHub, GitLab, OpenAI, Slack, Stripe, Twilio, SendGrid,
  Telegram, npm, AWS, Google, and Azure patterns

## Requirements

- Python 3.10 or newer
- A modern browser
- Chrome or Edge if you want to choose an entire folder from the browser

The current project includes the CredAudit engine under `engine/`.

## Run The Web App

From the project root:

```sh
python app.py
```

If `python` is not on your PATH on Windows, use the installed Python path:

```powershell
& 'C:\Users\Dell\AppData\Local\Programs\Python\Python312\python.exe' app.py
```

Then open:

```text
http://127.0.0.1:8000
```

To use another port:

```sh
python app.py --port 8080
```

## Ways To Scan

CredAudit Web supports several input methods:

- **Local folder path**: enter a path such as
  `C:\Users\Dell\Desktop\evidence`. This scans the folder and its contents from
  the machine running the server.
- **Choose folder from browser**: select a folder directly in Chrome or Edge.
  This uploads the selected files to the local server for scanning.
- **Upload files**: select one or more files.
- **Upload ZIP**: upload a ZIP archive; the app extracts it safely into a
  temporary scan folder.
- **Paste text**: paste logs, configuration snippets, credentials dumps, or
  other evidence directly into the text box.

For large audits, the local folder path option is usually best because the
engine scans the folder directly.

## Scan Options

- **Mode**
  - `Fast`: safer first-pass default. For folders, it focuses on small `.txt`
    files.
  - `Full`: scans the broader extension set configured by the CredAudit engine.
- **Sensitivity**
  - `1`: lower sensitivity
  - `2`: balanced default
  - `3`: higher sensitivity
- **Min confidence**
  - Optional percentage filter from `0` to `100`.
  - Use this to hide low-confidence matches.
- **Redact secrets in results**
  - Enabled by default.
  - Keep this enabled for normal review and sharing.
  - Turning it off can expose raw secret values in the browser and downloaded
    JSON.

## Results

After a scan, the page shows:

- Number of files scanned
- Total findings
- Elapsed scan time
- Severity totals for Critical, High, Medium, and Low
- A findings table with severity, rule name, confidence, file, line, and
  redacted value

Use **Download JSON** to save the displayed scan result.

## Safety Notes

- The app is designed for local use and binds to `127.0.0.1`.
- Findings are redacted by default.
- Uploaded files and pasted text are scanned in a temporary local folder.
- Treat downloaded JSON as sensitive if redaction is disabled.
- Always rotate or revoke exposed credentials. Removing them from files is not
  enough once they have been exposed.

## Project Structure

```text
CredAudit-Web/
  app.py              Local HTTP server and API
  static/             Browser UI
  engine/             CredAudit scanning engine
```

## Troubleshooting

If the app starts but the scan fails, make sure the bundled engine dependencies
are installed:

```sh
python -m pip install -r engine/requirements.txt
```

If `pytest` is not installed, engine tests will not run until you install the
development dependency:

```sh
python -m pip install pytest
```
