---
name: wps-file-upload
description: Upload files to WPS cloud drive with automatic token management, path resolution, and error handling. Use when uploading files, managing documents, or transferring data to WPS.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Grep
---

# WPS File Upload

## Workflow

When uploading a file to WPS, follow this process:

1. Verify access token is valid (auto-refresh if needed)
2. Validate source file exists
3. Resolve target path to folder ID (create if needed)
4. Execute three-step upload process
5. Return results: file ID, name, size

## Usage

To upload a file, describe your task naturally:
```
Upload e:\Desk\report.pdf to WPS folder CC-datas/gmail-daily
上传 e:\Desk\data.xlsx 到 WPS
上传多个文件到WPS: e:\Desk\file1.docx and e:\Desk\file2.pdf
```

## CLI Interface

The upload uses the bundled CLI in scripts/:
```bash
python scripts/main.py upload --file <file-path> --path <target-path> [--create-path]
```

## Error Handling

- Token expired: Automatically refresh using wps_login.py
- Path not found: Error (or create if --create-path specified)
- File conflict: Uses default 'rename' behavior

## First Time Setup

First-time users need to configure WPS API credentials:

1. Copy `scripts/config/.env.example` to `scripts/config/.env`
2. Fill in your WPS API credentials:
   - WPS_CLIENT_ID: Your application client ID
   - WPS_CLIENT_SECRET: Your application client secret
   - WPS_REDIRECT_URI: Your OAuth redirect URI
   - WPS_SCOPE: Requested OAuth scopes
   - WPS_AUTH_URL: WPS authorization URL
   - WPS_TOKEN_URL: WPS token URL
3. Run the authorization flow: `python scripts/main.py login`
4. Token will be saved to `scripts/data/token.json`

**Note**: If you have an existing `.env` file in the project root with WPS credentials, you can copy it instead:
```
cp e:/Desk/wps/.env e:/Desk/wps/.claude/skills/wps-upload/scripts/config/.env
```

For configuration details, see [references/login/](references/login/).
