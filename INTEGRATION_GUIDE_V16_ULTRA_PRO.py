"""
📚 INTEGRATION GUIDE v16 ULTRA PRO
════════════════════════════════════════════════════════════════

কীভাবে serial_gen_v14.py-তে v16 integrate করবেন:
════════════════════════════════════════════════════════════════
"""

# ✅ Step 1: At top of serial_gen_v14.py
from COOLTURA_CHECKER_V16_ULTRA_PRO import CoolturaDomainCheckerV16

# ✅ Step 2: Replace _ct_start() method with this:

def _ct_start_v16_ultra(self):
    """
    🏫 Cooltura Checker v16 ULTRA PRO
    
    ✨ Features:
      ✦ High logic MX rotation — never block
      ✦ Separate batch per MX — intelligent routing
      ✦ Deep error analysis — actionable hints
      ✦ Intelligent retry — network fail recovery
      ✦ Rate limiting — adaptive delays
      ✦ DNS failover — auto-discover backups
    """
    if self._ct_running:
        messagebox.showinfo("Busy", "আগের check এখনো চলছে।", parent=self)
        return

    raw    = self._ct_input.get("1.0", tk.END)
    emails = list(set(
        e.lower() for e in self._EMAIL_RE.findall(
            self._normalize_raw(raw))
    ))

    if not emails:
        messagebox.showinfo("Empty",
            "কোনো valid email পাওয়া যায়নি।",
            parent=self)
        return

    total   = len(emails)
    max_thr = max(1, min(self._ct_threads_var.get(), 15))
    timeout = max(5, self._ct_timeout_var.get())

    # Reset UI
    for st in (self._ct_st_valid, self._ct_st_invalid, self._ct_st_unknown):
        st.config(state="normal")
        st.delete("1.0", tk.END)
    self._ct_nb.tab(self._ct_tab_valid,   text="✅ Active (0)")
    self._ct_nb.tab(self._ct_tab_invalid, text="❌ Inactive (0)")
    self._ct_nb.tab(self._ct_tab_unknown, text="⚠️ Unknown (0)")
    self._ct_lbl_valid.config(  text="✅ Active: 0")
    self._ct_lbl_invalid.config(text="❌ Inactive: 0")
    self._ct_lbl_unknown.config(text="⚠️ Unknown: 0")
    self._ct_lbl_total.config(  text=f"📊 Done: 0/{total:,}")
    self._ct_pbar.config(maximum=max(total, 1))
    self._ct_pbar["value"] = 0
    self._ct_status_lbl.config(
        text=f"⏳ {total:,} email check হচ্ছে  (MX rotation mode)…",
        fg="#1A237E")

    self._ct_running   = True
    self._ct_stop_flag = False
    self._ct_start_btn.config(state="disabled")
    self._ct_stop_btn.config(state="normal")

    def _progress_callback(done, total_check, email, status, reason):
        """Live progress update"""
        if not self._ct_running:
            return

        icon = "✅" if status == "valid" else \
               "❌" if status == "invalid" else "⚠️"
        fg   = "#1B5E20" if status == "valid" else \
               "#C62828" if status == "invalid" else "#E65100"

        short_reason = reason[:55] if len(reason) > 55 else reason

        self._ct_status_lbl.config(
            text=f"{icon} [{done}/{total}]  {email[:38]}  →  {short_reason}",
            fg=fg)
        self._ct_pbar["value"] = done

        # Add to appropriate tab with full reason
        if status == "valid":
            self._ct_st_valid.insert(tk.END, f"{email}\n")
            v = len([l for l in self._ct_st_valid.get("1.0", tk.END).splitlines() if l.strip()])
            self._ct_lbl_valid.config(text=f"✅ Active: {v:,}")
            self._ct_nb.tab(self._ct_tab_valid, text=f"✅ Active ({v:,})")

        elif status == "invalid":
            self._ct_st_invalid.insert(tk.END, f"{email}\n  → {reason}\n")
            iv = len([l for l in self._ct_st_invalid.get("1.0", tk.END).splitlines() if "→" in l])
            self._ct_lbl_invalid.config(text=f"❌ Inactive: {iv:,}")
            self._ct_nb.tab(self._ct_tab_invalid, text=f"❌ Inactive ({iv:,})")

        else:  # unknown
            self._ct_st_unknown.insert(tk.END, f"{email}\n  → {reason}\n")
            uk = len([l for l in self._ct_st_unknown.get("1.0", tk.END).splitlines() if "→" in l])
            self._ct_lbl_unknown.config(text=f"⚠️ Unknown: {uk:,}")
            self._ct_nb.tab(self._ct_tab_unknown, text=f"⚠️ Unknown ({uk:,})")

        self._ct_lbl_total.config(text=f"📊 Done: {done:,}/{total:,}")
        self.update_idletasks()

    def _worker_thread():
        """Background worker with v16 ULTRA PRO"""
        try:
            # Create v16 checker with MX rotation
            checker = CoolturaDomainCheckerV16(
                num_threads=max_thr,
                timeout=timeout,
                batch_size=100
            )

            # Run parallel check with intelligent MX routing
            results = checker.check_parallel(emails, progress_callback=_progress_callback)

            # Get final stats including MX performance
            summary = checker.get_summary()

            def _final_ui():
                self._ct_running = False
                self._ct_start_btn.config(state="normal")
                self._ct_stop_btn.config(state="disabled")

                v  = summary['valid']
                iv = summary['invalid']
                uk = summary['unknown']

                self._ct_pbar["value"] = total
                self._ct_status_lbl.config(
                    text=f"✅ Finished!  "
                         f"✅Active:{v}  ❌Inactive:{iv}  ⚠️Unknown:{uk}  "
                         f"Speed: {summary['rate']:.0f}/sec  Time: {summary['elapsed']:.1f}s",
                    fg="#1B5E20")

                self.statusbar.config(
                    text=f"🏫 Done — ✅{v} Active  ❌{iv} Inactive  ⚠️{uk} Unknown  "
                         f"Total: {total}  Speed: {summary['rate']:.0f}/sec  Time: {summary['elapsed']:.1f}s")

                if v > 0:
                    self._ct_nb.select(self._ct_tab_valid)

                # MX performance
                mx_stats = ""
                if summary['mx_attempts']:
                    mx_stats = "\n\n🧭 MX Server Performance:\n"
                    for mx_host, attempts in sorted(summary['mx_attempts'].items()):
                        successes = summary['mx_successes'].get(mx_host, 0)
                        success_rate = (successes / attempts * 100) if attempts > 0 else 0
                        mx_stats += f"  • {mx_host}: {success_rate:.0f}% success ({successes}/{attempts})\n"

                messagebox.showinfo(
                    "✅ Check Complete",
                    f"মোট {total:,} email checked:\n\n"
                    f"  ✅ Active (mailbox আছে)    : {v:,}\n"
                    f"  ❌ Inactive (নেই/deleted) : {iv:,}\n"
                    f"  ⚠️  Unknown (uncertain)     : {uk:,}\n\n"
                    f"⏱ Time: {summary['elapsed']:.1f}s\n"
                    f"🚀 Speed: {summary['rate']:.0f} emails/sec"
                    + mx_stats,
                    parent=self)

            self.after(0, _final_ui)

        except Exception as e:
            import traceback
            self.after(0, lambda: messagebox.showerror(
                "Error", f"Check failed:\n\n{str(e)}\n\n{traceback.format_exc()[:200]}", parent=self))
            self._ct_running = False
            self._ct_start_btn.config(state="normal")
            self._ct_stop_btn.config(state="disabled")

    import threading as _threading
    _threading.Thread(target=_worker_thread, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
# 📌 THEN in _build_cooltura_checker_tab(), find:
#
#   self._ct_start_btn = tk.Button(ctrl,
#       text="▶  Check করুন",
#       ...
#       command=self._ct_start)
#
# CHANGE TO:
#   command=self._ct_start_v16_ultra)
#
# ═══════════════════════════════════════════════════════════════

# ✨ KEY FEATURES IN v16 ULTRA PRO:
#
# 1. MX DISCOVERY
#    - Automatic MX record lookup (DNS → nslookup → dig → fallback)
#    - Multiple MX servers per domain
#    - Intelligent rotation on failures
#
# 2. INTELLIGENT RETRY
#    - Each email tries all available MX servers
#    - Never blocks — automatic fallback
#    - Tracks MX success rate
#
# 3. DEEP ERROR ANALYSIS
#    - 550, 551, 553 → invalid user
#    - 421, 450, 451, 452 → temporary (retry later)
#    - timeout, connection refused → network issue
#    - Actionable hints for each error
#
# 4. ADAPTIVE RATE LIMITING
#    - Per-MX rate limiting (0.5s default)
#    - Prevents being blocked by strict servers
#    - Automatic adjustment
#
# 5. BATCH AWARENESS
#    - Separate queue per MX
#    - Connection pooling per MX
#    - Efficient reuse
#
# 6. STATISTICS
#    - MX server success rate
#    - Failure tracking per server
#    - Performance metrics
