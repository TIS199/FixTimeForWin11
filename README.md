# FixTime

FixTime is a specialized Windows utility designed to reliably synchronize your system time using the NTP protocol, bypassing the standard Windows Time Service when it fails or becomes unreliable.

## Why FixTime?

- **Direct NTP Sync:** Connects directly to NTP servers (UDP port 123).
- **Advanced Configuration:** Supports setting Timezone, retries, and custom DNS servers.
- **Resilient:** Waits for network availability and retries connection before giving up.
- **Silent Operation:** Runs in the background (no console window).

## Installation

### 1. Extract Files & Create Folder
1.  Create a folder named **`C:\FixTimeForWin11`**.
    > **Note:** Ideally, use this exact path because the included launcher script (`timefix.bat`) is pre-configured for it. If you use a different path, you must edit `timefix.bat` with Notepad.
2.  Extract the contents of the zip (`TimeFix.exe`, `config.txt`, `timefix.bat`) into this folder.

### 2. Configure Task Scheduler (The "Set and Forget" Method)
To ensure FixTime runs at startup with the highest privileges and *without* any user prompts:

1.  Press `Win + R`, type `taskschd.msc`, and press Enter.
2.  Click **"Create Task..."** (❌ NOT "Create Basic Task").

#### 🔐 General Tab
- **Name:** `FixTime` (or `MyBackgroundAdminTask`)
- **User Account:** Click "Change User or Group...", type `SYSTEM`, and click OK.
    - ✅ **Why?** Running as SYSTEM completely bypasses UAC prompts.
- **Run with highest privileges:** ☑ Checked.
- **Configure for:** Windows 10 or Windows 11.

#### ⚡ Triggers Tab
- Click **New...**
- **Begin the task:** At startup.
- **Enabled:** ☑ Checked.

#### ▶ Actions Tab
- Click **New...**
- **Action:** Start a program.
- **Program/script:** Browse and select **`C:\FixTimeForWin11\timefix.bat`**.
    - *Using the bat file ensures the working directory is set correctly every time.*

#### ⚙ Conditions Tab
- **Start only if on AC power:** ☐ Uncheck (important for laptops).

#### 🛠 Settings Tab
- **Allow task to be run on demand:** ☑ Checked.

### 🔒 Final Step
Click **OK**. That's it! Windows will never ask for permission, and your time will sync automatically at every boot.

## Configuration (`config.txt`)

You can customize behavior by checking `config.txt` in the installation folder:

```ini
NTPServer = pool.ntp.org
# DNSServer = 8.8.8.8  <-- Uncomment to force Google DNS for NTP resolution
TimeZone = Bangladesh Standard Time
RetryDelay = 5
MaxRetries = 10
```

## Compilation (Optional)

If you want to build from source:
1.  `pip install pyinstaller`
2.  Run `build.bat`
