To check for **Out of Memory (OOM)** errors on a Linux system, you can use a few different methods. OOM errors are logged by the Linux kernel when the system kills a process due to insufficient memory. Here’s how you can investigate them:

### 1. **Using `dmesg`**:
   The `dmesg` command can display recent kernel logs, which often include OOM-related messages.
   ```bash
   dmesg | grep -i "oom"
   ```
   Look for messages like "Out of memory" or "OOM killer," indicating that the kernel killed a process to free up memory.

### 2. **Checking System Logs**:
   System logs like `/var/log/syslog` or `/var/log/messages` usually contain OOM events if they were logged. Use `grep` to find OOM-related entries.
   ```bash
   grep -i "oom" /var/log/syslog
   # or
   grep -i "oom" /var/log/messages
   ```
   If your system uses `journalctl`, you can use it to search for OOM events as well:
   ```bash
   journalctl | grep -i "oom"
   ```

### 3. **Checking the `oom_score` for Processes**:
   The OOM killer decides which process to terminate based on each process's `oom_score`. You can check the current `oom_score` of running processes to see which ones are more likely to be killed if memory runs out.
   ```bash
   cat /proc/<pid>/oom_score
   ```
   Replace `<pid>` with the process ID of the process you want to inspect.

### 4. **Inspecting `/var/log/kern.log`** (if available):
   On some systems, OOM events are specifically logged in the kernel logs. Check `/var/log/kern.log` for OOM events:
   ```bash
   grep -i "oom" /var/log/kern.log
   ```

### 5. **Viewing Historical OOM Events with `journalctl`**:
   If you want to see a history of OOM events, `journalctl` is especially useful on systems with `systemd`:
   ```bash
   journalctl -k | grep -i "oom"
   ```

By checking these logs and scores, you can identify recent OOM events and processes affected by the OOM killer, as well as monitor processes that might be at risk if memory becomes constrained.