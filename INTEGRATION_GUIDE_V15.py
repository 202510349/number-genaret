"""
INTEGRATION GUIDE — How to use v15 ULTRA in your GUI
════════════════════════════════════════════════════════

মূল পয়েন্ট:
1. COOLTURA_CHECKER_V15_ULTRA.py import করুন
2. _ct_start() method replace করুন (নিচে দেওয়া আছে)
3. Progress callback সেট করুন UI update-এর জন্য
4. Results populate করুন 3 tabs-এ

════════════════════════════════════════════════════════
"""

# ✅ At top of serial_gen_v14.py:
from COOLTURA_CHECKER_V15_ULTRA import CoolturaDomainChecker

# ✅ Replace _ct_start() with this:

def _ct_start_v15(self):
    """Start SMTP mailbox existence check — V15 ULTRA (100x faster)"""
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
            "কোনো valid email পাওয়া যায়নি।\n"
            "উদাহরণ:\n  teacher1@cooltura.com\n  student2@cooltura.com",
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
        text=f"⏳ {total:,} email check হচ্ছে  (threads: {max_thr})…",
        fg="#1A237E")

    self._ct_running   = True
    self._ct_stop_flag = False
    self._ct_start_btn.config(state="disabled")
    self._ct_stop_btn.config(state="normal")

    # ═══════════════════════════════════════════════════════════════
    # 🚀 V15 ULTRA CHECKER — parallel, batched, fast
    # ═══════════════════════════════════════════════════════════════

    def _progress_callback(done, total_check, email, status, reason):
        """Live progress update for UI"""
        if not self._ct_running:
            return

        icon = "✅" if status == "valid" else \
               "❌" if status == "invalid" else "⚠️"
        fg   = "#1B5E20" if status == "valid" else \
               "#C62828" if status == "invalid" else "#E65100"

        self._ct_status_lbl.config(
            text=f"{icon} [{done}/{total}]  {email[:38]}  —  {reason[:55]}",
            fg=fg)
        self._ct_pbar["value"] = done

        # Add to appropriate tab
        if status == "valid":
            self._ct_st_valid.insert(tk.END, f"{email}\n")
            v = len([l for l in self._ct_st_valid.get("1.0", tk.END).splitlines() if l.strip()])
            self._ct_lbl_valid.config(text=f"✅ Active: {v:,}")
            self._ct_nb.tab(self._ct_tab_valid, text=f"✅ Active ({v:,})")

        elif status == "invalid":
            self._ct_st_invalid.insert(tk.END, f"{email}\n  ↳ {reason}\n")
            iv = len([l for l in self._ct_st_invalid.get("1.0", tk.END).splitlines() if "↳" in l])
            self._ct_lbl_invalid.config(text=f"❌ Inactive: {iv:,}")
            self._ct_nb.tab(self._ct_tab_invalid, text=f"❌ Inactive ({iv:,})")

        else:  # unknown
            self._ct_st_unknown.insert(tk.END, f"{email}\n  ↳ {reason}\n")
            uk = len([l for l in self._ct_st_unknown.get("1.0", tk.END).splitlines() if "↳" in l])
            self._ct_lbl_unknown.config(text=f"⚠️ Unknown: {uk:,}")
            self._ct_nb.tab(self._ct_tab_unknown, text=f"⚠️ Unknown ({uk:,})")

        self._ct_lbl_total.config(text=f"📊 Done: {done:,}/{total:,}")
        self.update_idletasks()

    def _worker_thread():
        """Background worker"""
        try:
            # Create v15 checker
            checker = CoolturaDomainChecker(
                num_threads=max_thr,
                timeout=timeout,
                batch_size=100  # 100 emails per SMTP session
            )

            # Run parallel check with progress
            results = checker.check_parallel(emails, progress_callback=_progress_callback)

            # Get final stats
            summary = checker.get_summary()

            # Update UI when done
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
                         f"Total: {total}  Speed: {summary['rate']:.0f}/sec")

                if v > 0:
                    self._ct_nb.select(self._ct_tab_valid)

                # Success message
                messagebox.showinfo(
                    "✅ Check Complete",
                    f"মোট {total:,} email checked:\n\n"
                    f"  ✅ Active (mailbox আছে)    : {v:,}\n"
                    f"  ❌ Inactive (নেই/deleted) : {iv:,}\n"
                    f"  ⚠️  Unknown (uncertain)     : {uk:,}\n\n"
                    f"⏱ Time: {summary['elapsed']:.1f}s\n"
                    f"🚀 Speed: {summary['rate']:.0f} emails/sec",
                    parent=self)

            self.after(0, _final_ui)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", f"Check failed:\n\n{str(e)}", parent=self))
            self._ct_running = False
            self._ct_start_btn.config(state="normal")
            self._ct_stop_btn.config(state="disabled")

    # Start worker thread
    import threading as _threading
    _threading.Thread(target=_worker_thread, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════
# 📌 THEN in serial_gen_v14.py, find the _ct_start method
# and REPLACE it with _ct_start_v15() defined above
#
# Change:
#    self._ct_start_btn.command = self._ct_start
# To:
#    self._ct_start_btn.command = lambda: self._ct_start_v15()
# ═══════════════════════════════════════════════════════════════════
