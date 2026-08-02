# 🔐 Secrets Setup – SuperCR Device Keeper

[![Workflow Status](https://img.shields.io/badge/Workflow-supercr.yml-blue.svg)](#) [![Script](https://img.shields.io/badge/Script-supercrheadless.py-green.svg)](#)

Welcome to the **SuperCR Device Keeper** secrets guide. This repository utilizes a GitHub Actions workflow (`.github/workflows/supercr.yml`) to run the `supercrheadless.py` script. 

To allow the automated script to securely authenticate and manage your device sessions without hardcoding sensitive data, you must configure **GitHub Repository Secrets**.

---

## 📌 Required Credentials

These core secrets are absolutely necessary for the workflow to authenticate with your SuperCR account. 

### Account Email
The email address associated with your account.
```text
EMAIL
```

### Account Password
The password associated with your account.
```text
PASSWORD
```

---

## 🎯 Device Selection Criteria

> ⚠️ **IMPORTANT:** You must configure **at least one** of the following secrets. 
> These tell the script which sessions to *keep* so it doesn't log you out of your active devices.

### Locations 
*(Optional if `KEEP_DEVICE_NAMES` is set)*  
A comma-separated list of location substrings to protect.
```text
LOCATIONS
```

### Keep Device Names 
*(Optional if `LOCATIONS` is set)*  
A comma-separated list of exact device names or models to protect.
```text
KEEP_DEVICE_NAMES
```

---

## ⚙️ Optional Configuration Secrets

Fine-tune the workflow's behavior. If omitted, the script will fall back to its default settings.

### Profile PIN
Your profile PIN code (only required if your specific profile is PIN-protected).
```text
PIN
```

### Keep Mode
Determines the logic used when *both* `LOCATIONS` and `KEEP_DEVICE_NAMES` are provided.  
**Options:** `OR` (default) | `AND`
```text
KEEP_MODE
```

### Cleaning Mode
Defines the strictness of the session cleanup strategy.  
**Options:** `1` (Normal) | `2` (Extreme - default)
```text
MODE
```

### Preferred Profile
The specific profile number to utilize.  
**Options:** `1` through `10` (Specific profile) | `0` (Cycle through all - default)
```text
PREFERRED_PROFILE
```

---

## 📋 Quick Copy Block

Need to copy them all at once? Use the block below to grab the exact key names for your GitHub settings.

```text
EMAIL
PASSWORD
LOCATIONS
KEEP_DEVICE_NAMES
PIN
KEEP_MODE
MODE
PREFERRED_PROFILE
```

---

## 💡 Example Values Table

Use this reference table to ensure your values are formatted correctly before saving them to GitHub.

| Secret Name | Example Value | Description |
| :--- | :--- | :--- |
| `EMAIL` | `user@example.com` | Standard email format. |
| `PASSWORD` | `SuperSecretPass123!` | Case-sensitive password. |
| `LOCATIONS` | `New York, Chrome` | Comma-separated strings. |
| `KEEP_DEVICE_NAMES` | `Living Room TV, iPhone 15` | Comma-separated strings. |
| `PIN` | `1234` | 4-digit numeric PIN. |
| `KEEP_MODE` | `OR` | Must be `OR` or `AND`. |
| `MODE` | `2` | Numeric integer (`1` or `2`). |
| `PREFERRED_PROFILE` | `1` | Numeric integer (`0` to `10`). |

---

## 🛠️ Step-by-Step Setup Guide

Follow these steps to securely inject your secrets into the GitHub Action:

1. Navigate to your repository's main page on **GitHub**.
2. Click on the ⚙️ **Settings** tab near the top.
3. In the left sidebar, scroll down to the **Security** section.
4. Click on **Secrets and variables**, then click **Actions**.
5. Click the green **New repository secret** button at the top right.
6. Under **Name**, paste the secret key (e.g., `EMAIL`) using the copy buttons above.
7. Under **Secret**, enter your corresponding personal value.
8. Click **Add secret**.
9. **Repeat** this process until all required secrets (and any desired optional ones) are added.

---

## 🚀 Minimum Setup Example

Want the fastest path to getting this running? You only need to add these **three** secrets to your repository to successfully protect a single location:

1. ```text
   EMAIL
   ``` 
   *(Value: `your_email@example.com`)*
2. ```text
   PASSWORD
   ``` 
   *(Value: `your_secure_password`)*
3. ```text
   LOCATIONS
   ``` 
   *(Value: `Home`)*

Once these three are saved in your repository settings, the `supercr.yml` workflow will be fully operational!
