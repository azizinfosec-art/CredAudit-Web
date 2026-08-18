# CredAudit Web

A local web interface for the CredAudit scanning engine.

## Run

```sh
python app.py
```

Open http://127.0.0.1:8000 and enter a local folder path, choose a browser folder,
upload files, upload a ZIP, or paste evidence to scan.

The app uses the cloned `engine/` package directly and returns redacted findings by default.
