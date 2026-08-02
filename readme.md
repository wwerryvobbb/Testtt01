# 🔐 Secrets Setup – SuperCR Device Keeper

Below are all the **secrets** you need to add to your GitHub repository for the SuperCR Device Keeper workflow.  
To copy a secret name, simply select and copy the text from the code blocks.

---

## 🔒 Required Secrets

| Secret Name | Description | Required? |
|-------------|-------------|-----------|
| `EMAIL` | Your account email address (used to log in). | ✅ **Yes** |
| `PASSWORD` | Your account password (used to log in). | ✅ **Yes** |

### Copy names:

```text
EMAIL
PASSWORD
```

---

## ⚠️ At Least One of These is Required

| Secret Name | Description | Required? |
|-------------|-------------|-----------|
| `LOCATIONS` | Comma‑separated location substrings to keep (e.g., `Jammu, Himachal`). | ⚠️ Required unless `KEEP_DEVICE_NAMES` is set. |
| `KEEP_DEVICE_NAMES` | Comma‑separated device names/models to keep (e.g., `POCO F5, Chrome on Windows`). | ⚠️ Required unless `LOCATIONS` is set. |

> **Note:** You must provide **at least one** of `LOCATIONS` or `KEEP_DEVICE_NAMES` – otherwise the script will exit with an error.

### Copy names:

```text
LOCATIONS
KEEP_DEVICE_NAMES
```

---

## 🔘 Optional Secrets

| Secret Name | Description | Default / Allowed Values |
|-------------|-------------|---------------------------|
| `PIN` | Your profile PIN (if your account uses one). | (empty) |
| `KEEP_MODE` | Keep logic: `OR` (keep if either location or device name matches) or `AND` (keep if both match). | `OR` (if not set) |
| `MODE` | Run mode: `1` (Normal – slower, configurable delays) or `2` (Extreme – faster). | `2` (if not set) |
| `PREFERRED_PROFILE` | Profile number to use (1‑10) – the script will only try that profile. Set to `0` to cycle through all profiles. | `0` (if not set) |

### Copy names:

```text
PIN
KEEP_MODE
MODE
PREFERRED_PROFILE
```

---

## 📋 All Secret Names – Quick Copy

```text
EMAIL
PASSWORD
PIN
LOCATIONS
KEEP_DEVICE_NAMES
KEEP_MODE
MODE
PREFERRED_PROFILE
```

---

## 🧪 Example Values

| Secret | Example Value |
|--------|---------------|
| `EMAIL` | `youremail@example.com` |
| `PASSWORD` | `your-strong-password` |
| `PIN` | `1234` |
| `LOCATIONS` | `Jammu, Himachal` |
| `KEEP_DEVICE_NAMES` | `POCO F5, Chrome on Windows` |
| `KEEP_MODE` | `OR` |
| `MODE` | `2` |
| `PREFERRED_PROFILE` | `0` |

---

## 📌 How to Add Secrets

1. Go to your GitHub repository.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret**.
4. Enter the secret name (e.g., `EMAIL`) and its value.
5. Click **Add secret**.

Repeat for each secret you need to add.

---

## ✅ Minimum Setup

For the workflow to run successfully, you only need:

```
EMAIL
PASSWORD
LOCATIONS
```

(Or replace `LOCATIONS` with `KEEP_DEVICE_NAMES` if you prefer to keep devices by name.)

---

That’s it – you’re ready to go! 🚀
