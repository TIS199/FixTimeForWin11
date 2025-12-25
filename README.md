# FixTime

FixTime is a specialized Windows utility designed to reliably synchronize your system time using the NTP protocol, bypassing the standard Windows Time Service when it fails or becomes unreliable.

## Why FixTime?

- **Direct NTP Sync:** Connects directly to NTP servers (UDP port 123) rather than relying on `w32tm`.
- **Advanced Configuration:** Supports setting Timezone, retries, and custom DNS servers for environments with specific network restrictions.
- **Resilient:** Waits for network availability and retries connection before giving up.
- **Silent Operation:** Designed to run in the background (no console window) and exit immediately upon success.

## When to Use

- **Dual Booting:** Corrects the time offset often caused by switching between Windows (Local Time) and Linux/macOS (UTC).
- **Dead CMOS Battery:** Automatically restores the correct time at startup if your hardware clock resets.
- **DNS Issues:** Can use a specific DNS server (e.g., Google or Cloudflare) to resolve the NTP pool if your local ISP DNS is flaky.

## Installation & Setup (Task Scheduler)

For best results, run FixTime at startup with administrative privileges.

1.  **Open Task Scheduler** (`taskschd.msc`).
2.  **Create a New Task** (not basic).
3.  **General:**
    - Name: `FixTime`
    - User Account: `SYSTEM` (Search for "SYSTEM").
    - **Run with highest privileges**: Checked.
4.  **Triggers:**
    - Start the task: **At startup**.
5.  **Actions:**
    - Action: **Start a program**.
    - Program/script: Path to `TimeFix.exe`.
    - **Start in:** The folder containing `TimeFix.exe` and `config.txt` (Critical for loading config).
6.  **Conditions:**
    - Uncheck "Start only if on AC power".
    - Check "Start only if the following network connection is available" (Optional, but recommended).

## Configuration

Settings are controlled via `config.txt` using a `Key=Value` format.

**Key Parameters:**

- `NTPServer`: The NTP server to query (default: `pool.ntp.org`).
- `DNSServer`: (Optional) Specific DNS server IP to use for resolving the NTP host (e.g., `8.8.8.8`).
- `TimeZone`: (Optional) The time zone ID to force set the system to (e.g., `Bangladesh Standard Time`, `UTC`, `Pacific Standard Time`).
- `RetryDelay`: Seconds to wait between retries.
- `MaxRetries`: Maximum number of attempts (0 = infinite, but recommended to set a limit like 10).

**Example `config.txt`:**
```ini
NTPServer = pool.ntp.org
# DNSServer = 1.1.1.1
TimeZone = Bangladesh Standard Time
RetryDelay = 5
MaxRetries = 10
```

## Compilation

To build from source:

1.  Active your virtual environment (if used).
2.  Install requirements: `pip install pyinstaller`.
3.  Run the build script:
    ```cmd
    build.bat
    ```
    Or manually:
    ```cmd
    python -m PyInstaller --onefile --noconsole --name TimeFix src/timefix.py
    ```

## License
MIT License.
