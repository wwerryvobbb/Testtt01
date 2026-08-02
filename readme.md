# 🔐 Secrets Setup – SuperCR Device Keeper

This repository contains a GitHub Actions workflow (`.github/workflows/supercr.yml`) that runs `supercrheadless.py` to automatically manage device sessions for the SuperCR streaming service. 

To allow the automated script to log in and evaluate device sessions securely, you must configure GitHub Repository Secrets.

---

## 📌 Required Credentials

These credentials are required for the workflow to authenticate with your account.

| Secret Name | Required | Description |
| :--- | :---: | :--- |
| ```EMAIL``` | **Yes** | The email address associated with your SuperCR account. |
| ```PASSWORD``` | **Yes** | The password associated with your SuperCR account. |

---

## 🎯 Device Selection Criteria (At Least One Required)

To prevent the script from revoking sessions on devices you actively use, you must specify at least one retention criterion.

| Secret Name | Required | Description |
| :--- | :---: | :--- |
| ```LOCATIONS``` | *Conditional* | Comma-separated list of location substrings to keep (e.g., `New York, Chrome`). |
| ```KEEP_DEVICE_NAMES``` | *Conditional* | Comma-separated list of specific device names or models to keep (e.g., `Living Room TV, iPhone 15`). |

> **Note:** At least **one** of ```LOCATIONS``` or ```KEEP_DEVICE_NAMES``` must be provided for the script to safely identify which device sessions to retain.

---

## ⚙️ Optional Configuration Secrets

Custom settings to fine-tune workflow behavior and session management.

| Secret Name | Default | Options / Description |
| :--- | :---: | :--- |
| ```PIN``` | *None* | Profile PIN code (if your account profile is PIN-protected). |
| ```KEEP_MODE``` | `OR` | `OR` / `AND` — Determines logic when both `LOCATIONS` and `KEEP_DEVICE_NAMES` are set. |
| ```MODE``` | `2` | `1` (Normal) or `2` (Extreme) cleaning strategy. |
| ```PREFERRED_PROFILE``` | `0` | Profile index to use: `1`–`10` for a specific profile, or `0` to cycle. |

---

## 📋 Quick Copy Secret Names

Copy these exact keys when setting up your repository secrets:

```text
EMAIL
PASSWORD
LOCATIONS
KEEP_DEVICE_NAMES
PIN
KEEP_MODE
MODE
PREFERRED_PROFILE
