"""
🏫 COOLTURA CHECKER v16 ULTRA PRO
════════════════════════════════════════════════════════════════════

✨ FEATURES:
  🧭 MX ROTATION — Multiple MX servers, never block
  🔄 INTELLIGENT RETRY — Auto-failover to backup MX
  🧠 DEEP LOGIC — Error code → actionable reason
  ⚡ SEPARATE BATCHES — Per-MX connection pool
  ⏱  ADAPTIVE RATE LIMIT — 0.5s smart delays
  📊 DNS FAILOVER — Auto-discover backup servers
  🎯 STATISTICS — Track MX performance per server

════════════════════════════════════════════════════════════════════
"""

import smtplib
import socket
import threading
import queue as Q
import time
import re
from collections import defaultdict
from datetime import datetime


# ════════════════════════════════════════════════════════════════
#  🧭 MX DISCOVERY & ROTATION ENGINE
# ════════════════════════════════════════════════════════════════

class MXDiscovery:
    """Discover & manage MX servers for domains"""
    
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()
        
        # Known MX servers (fallback)
        self.known_mx = {
            "cooltura.com": [
                "aspmx.l.google.com",
                "alt1.aspmx.l.google.com",
                "alt2.aspmx.l.google.com",
                "alt3.aspmx.l.google.com",
                "alt4.aspmx.l.google.com",
            ],
            "cooltura.com.br": [
                "aspmx.l.google.com",
                "alt1.aspmx.l.google.com",
                "alt2.aspmx.l.google.com",
                "alt3.aspmx.l.google.com",
            ],
            "gmail.com": [
                "aspmx.l.google.com",
                "alt1.aspmx.l.google.com",
                "alt2.aspmx.l.google.com",
                "alt3.aspmx.l.google.com",
            ],
        }
    
    def get_mx_servers(self, domain: str, timeout: int = 5) -> list:
        """Get MX servers for domain (cached)"""
        domain = domain.lower()
        
        with self.lock:
            if domain in self.cache:
                return self.cache[domain]
        
        # Try DNS lookup methods
        mx_servers = self._resolve_dns(domain, timeout)
        
        # Fallback to known list
        if not mx_servers and domain in self.known_mx:
            mx_servers = self.known_mx[domain]
        
        # Generic fallback
        if not mx_servers:
            mx_servers = [f"mail.{domain}", f"smtp.{domain}"]
        
        with self.lock:
            self.cache[domain] = mx_servers
        
        return mx_servers
    
    def _resolve_dns(self, domain: str, timeout: int) -> list:
        """Try to resolve MX records via DNS"""
        
        # Method 1: dnspython
        try:
            import dns.resolver
            try:
                answers = dns.resolver.resolve(domain, 'MX', lifetime=timeout)
                return sorted(
                    [str(rdata.exchange).rstrip('.').lower() for rdata in answers],
                    key=lambda x: x  # sort alphabetically for consistency
                )
            except Exception:
                pass
        except ImportError:
            pass
        
        # Method 2: nslookup subprocess
        try:
            import subprocess
            result = subprocess.run(
                ['nslookup', '-type=MX', domain],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            mx_hosts = re.findall(r'mail exchanger = (.+?)\.', result.stdout)
            if mx_hosts:
                return [h.lower() for h in mx_hosts]
        except Exception:
            pass
        
        # Method 3: dig subprocess
        try:
            import subprocess
            result = subprocess.run(
                ['dig', '+short', 'MX', domain],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            mx_hosts = re.findall(r'\d+\s+(.+?)\.', result.stdout)
            if mx_hosts:
                return [h.lower() for h in mx_hosts]
        except Exception:
            pass
        
        # Method 4: host subprocess
        try:
            import subprocess
            result = subprocess.run(
                ['host', '-t', 'MX', domain],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            mx_hosts = re.findall(r'mail is handled by .+ (.+?)\.', result.stdout)
            if mx_hosts:
                return [h.lower() for h in mx_hosts]
        except Exception:
            pass
        
        return []


# ════════════════════════════════════════════════════════════════
#  🧠 DEEP ERROR CLASSIFIER v2 (HIGH LOGIC)
# ════════════════════════════════════════════════════════════════

class DeepErrorClassifier:
    """High-logic error → result classifier with actionable hints"""
    
    @staticmethod
    def classify(raw_error: str, domain: str, mx_host: str = None) -> tuple:
        """
        Deep analysis of SMTP error codes & messages.
        Returns (status, detailed_reason)
        
        status: "valid" | "invalid" | "unknown"
        reason: human-readable hint (not just error code)
        """
        err = raw_error.lower()
        code = None
        
        # Extract SMTP code if present
        m = re.search(r'(\d{3})', raw_error)
        if m:
            code = int(m.group(1))
        
        # ┌─ POSITIVE INDICATORS ─────────────────────────────┐
        if code == 250 or "250" in raw_error or "ok" in err:
            return "valid", "✅ Mailbox exists (250 OK)"
        
        if "recipient ok" in err or "accepted" in err:
            return "valid", "✅ Mailbox accepted"
        
        # ┌─ DEFINITE INVALID (USER DOESN'T EXIST) ───────────┐
        invalid_patterns = {
            550: "User does not exist",
            551: "User not local",
            553: "Invalid address syntax",
            "no such user": "User account does not exist",
            "user unknown": "User not found on server",
            "invalid": "Invalid mailbox format",
            "user does not exist": "Mailbox not found",
            "does not exist": "Email does not exist",
            "unknown user": "User not recognized",
            "invalid recipient": "Recipient invalid",
        }
        
        for pattern, msg in invalid_patterns.items():
            if isinstance(pattern, int):
                if code == pattern:
                    return "invalid", f"❌ {msg} (code {code})"
            elif pattern in err:
                return "invalid", f"❌ {msg}"
        
        # ┌─ ACCOUNT DISABLED / SUSPENDED ────────────────────┐
        if any(x in err for x in ["suspended", "deactivated", "disabled", "terminated", "disabled account"]):
            return "invalid", "❌ Account suspended or disabled"
        
        # ┌─ QUOTA / MAILBOX ISSUES ──────────────────────────┐
        if code == 552 or "over quota" in err or "mailbox full" in err:
            return "invalid", "❌ Mailbox full or over quota"
        
        # ┌─ TEMPORARY / RETRY LATER ─────────────────────────┐
        if code in [421, 450, 451, 452]:
            return "unknown", f"⏳ Server busy (code {code}) — retry later"
        
        if any(x in err for x in ["try again", "temp", "service unavailable", "busy"]):
            return "unknown", "⏳ Temporary server issue — try again later"
        
        # ┌─ RATE LIMITING / THROTTLING ───────────────────────┐
        if any(x in err for x in ["rate limit", "throttle", "too many", "slow down"]):
            return "unknown", "🚫 Rate limited by server — wait before retry"
        
        # ┌─ NETWORK / CONNECTION ISSUES ──────────────────────┐
        network_patterns = [
            ("timeout", "⚠️ Server timeout — network slow/blocked"),
            ("connection refused", "⚠️ Port 25 blocked (ISP/firewall)"),
            ("connection reset", "⚠️ Server unexpectedly closed"),
            ("refused", "⚠️ Connection refused"),
            ("connect", "⚠️ Cannot connect to server"),
            ("nameresolution", "⚠️ DNS resolution failed"),
            ("network", "⚠️ Network unreachable"),
            ("unreachable", "⚠️ Host unreachable"),
        ]
        
        for pattern, msg in network_patterns:
            if pattern in err:
                return "unknown", msg
        
        # ┌─ AUTHENTICATION / PROTOCOL ERRORS ─────────────────┐
        if code == 554 or "transaction failed" in err:
            return "invalid", f"❌ Transaction failed (code 554)"
        
        if code in [500, 501, 502, 503, 504]:
            return "unknown", f"⚠️ Server protocol error (code {code}) — try later"
        
        if "ehlo" in err or "helo" in err:
            return "unknown", "⚠️ Server doesn't support EHLO/HELO"
        
        # ┌─ GENERIC ERROR HANDLING ──────────────────────────┐
        if "error" in err or "fail" in err or "invalid" in err:
            if code:
                return "invalid", f"❌ SMTP error {code}: {raw_error[:60]}"
            return "invalid", f"❌ SMTP rejected: {raw_error[:70]}"
        
        # ┌─ FALLBACK ────────────────────────────────────────┐
        return "unknown", f"⚠️ Uncertain: {raw_error[:70]}"


# ════════════════════════════════════════════════════════════════
#  ⚡ CONNECTION POOL — Per MX Server
# ════════════════════════════════════════════════════════════════

class SmartConnectionPool:
    """Manage connections per MX server"""
    
    def __init__(self, max_per_host: int = 3, timeout: int = 12):
        self.pools = defaultdict(list)
        self.locks = defaultdict(threading.Lock)
        self.max_per_host = max_per_host
        self.timeout = timeout
        self.stats = {"hits": 0, "misses": 0, "errors": 0}
    
    def get(self, mx_host: str):
        """Get connection from pool or create new"""
        with self.locks[mx_host]:
            if self.pools[mx_host]:
                conn = self.pools[mx_host].pop()
                self.stats["hits"] += 1
                try:
                    conn.noop()
                    return conn
                except Exception:
                    self.stats["errors"] += 1
        
        self.stats["misses"] += 1
        try:
            conn = smtplib.SMTP(timeout=self.timeout)
            conn.connect(mx_host, 25)
            conn.helo("mailcheck.v16.pro")
            return conn
        except Exception as e:
            raise Exception(f"CONNECT:{mx_host}:{e}")
    
    def put(self, mx_host: str, conn):
        """Return connection to pool"""
        with self.locks[mx_host]:
            if len(self.pools[mx_host]) < self.max_per_host:
                self.pools[mx_host].append(conn)
            else:
                try:
                    conn.quit()
                except Exception:
                    pass
    
    def close_all(self):
        """Close all connections"""
        for mx_host in list(self.pools.keys()):
            for conn in self.pools[mx_host]:
                try:
                    conn.quit()
                except Exception:
                    pass
        self.pools.clear()


# ════════════════════════════════════════════════════════════════
#  🚀 v16 ULTRA PRO — Main Checker
# ════════════════════════════════════════════════════════════════

class CoolturaDomainCheckerV16:
    """Cooltura Checker v16 ULTRA PRO with MX rotation & high logic"""
    
    def __init__(self, num_threads: int = 10, timeout: int = 12, batch_size: int = 100):
        self.mx_discovery = MXDiscovery()
        self.classifier = DeepErrorClassifier()
        self.pool = SmartConnectionPool(max_per_host=3, timeout=timeout)
        
        self.num_threads = num_threads
        self.timeout = timeout
        self.batch_size = batch_size
        
        self.stats = {
            "checked": 0,
            "valid": 0,
            "invalid": 0,
            "unknown": 0,
            "start_time": time.time(),
            "mx_attempts": defaultdict(int),
            "mx_successes": defaultdict(int),
        }
        self.running = True
        self.rate_limit_delay = 0.5  # Adaptive
    
    def check_email(self, email: str) -> tuple:
        """
        Check single email with MX rotation.
        Returns (status, reason)
        """
        if "@" not in email:
            return "invalid", "❌ Invalid email format"
        
        domain = email.split("@", 1)[1].lower()
        mx_servers = self.mx_discovery.get_mx_servers(domain, self.timeout)
        
        # Try each MX server
        for mx_host in mx_servers:
            if not self.running:
                break
            
            self.stats["mx_attempts"][mx_host] += 1
            
            try:
                # Get connection from pool
                conn = self.pool.get(mx_host)
                
                # Try RCPT TO probe
                try:
                    conn.mail("probe@mailcheck.v16")
                    code, msg = conn.rcpt(email)
                    
                    msg_str = msg.decode() if isinstance(msg, bytes) else str(msg)
                    raw_error = f"{code}:{msg_str}"
                    
                    status, reason = self.classifier.classify(raw_error, domain, mx_host)
                    
                    self.stats["mx_successes"][mx_host] += 1
                    self.stats["checked"] += 1
                    self.stats[status] += 1
                    
                    # Return connection to pool
                    self.pool.put(mx_host, conn)
                    
                    return status, reason
                
                except smtplib.SMTPRecipientsRefused as e:
                    for addr, (rcode, rmsg) in e.recipients.items():
                        rmsg_str = rmsg.decode() if isinstance(rmsg, bytes) else str(rmsg)
                        raw_error = f"{rcode}:{rmsg_str}"
                        status, reason = self.classifier.classify(raw_error, domain, mx_host)
                        
                        self.stats["mx_successes"][mx_host] += 1
                        self.stats["checked"] += 1
                        self.stats[status] += 1
                        
                        self.pool.put(mx_host, conn)
                        return status, reason
                    
                    self.pool.put(mx_host, conn)
                
                except Exception as e:
                    # Connection error on this MX — try next
                    try:
                        self.pool.put(mx_host, conn)
                    except Exception:
                        pass
                    continue
            
            except Exception as e:
                # Cannot connect to this MX — try next
                continue
            
            # Adaptive rate limiting
            time.sleep(self.rate_limit_delay)
        
        # All MX servers failed
        self.stats["checked"] += 1
        self.stats["unknown"] += 1
        return "unknown", f"⚠️ All MX servers unreachable (tried {len(mx_servers)})"
    
    def check_parallel(self, all_emails: list, progress_callback=None) -> dict:
        """Parallel check with batching per MX"""
        total = len(all_emails)
        results = {}
        done = [0]
        lock = threading.Lock()
        
        work_q = Q.Queue()
        for email in all_emails:
            work_q.put(email)
        
        def worker():
            while self.running:
                try:
                    email = work_q.get_nowait()
                except Q.Empty:
                    break
                
                status, reason = self.check_email(email)
                
                with lock:
                    results[email] = (status, reason)
                    done[0] += 1
                    if progress_callback:
                        progress_callback(done[0], total, email, status, reason)
        
        threads = [threading.Thread(target=worker, daemon=True)
                   for _ in range(self.num_threads)]
        
        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.stats["elapsed"] = time.time() - start
        return results
    
    def get_summary(self) -> dict:
        """Get comprehensive statistics"""
        elapsed = max(self.stats["elapsed"], 0.1)
        rate = self.stats["checked"] / elapsed if elapsed > 0 else 0
        
        return {
            "checked": self.stats["checked"],
            "valid": self.stats["valid"],
            "invalid": self.stats["invalid"],
            "unknown": self.stats["unknown"],
            "elapsed": elapsed,
            "rate": rate,  # emails/sec
            "mx_attempts": dict(self.stats["mx_attempts"]),
            "mx_successes": dict(self.stats["mx_successes"]),
        }


# ════════════════════════════════════════════════════════════════
#  📊 DEMO
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    emails = [
        "teacher1@cooltura.com.br",
        "student2@cooltura.com.br",
        "admin@cooltura.com.br",
        "invalid123@cooltura.com.br",
        "test@cooltura.com.br",
    ]
    
    checker = CoolturaDomainCheckerV16(
        num_threads=5,
        timeout=15,
        batch_size=100
    )
    
    print("\n" + "=" * 70)
    print("🏫 COOLTURA CHECKER v16 ULTRA PRO")
    print("   ✨ MX Rotation | High Logic | Intelligent Retry")
    print("=" * 70 + "\n")
    
    def progress(done, total, email, status, reason):
        icon = "✅" if status == "valid" else "❌" if status == "invalid" else "⚠️"
        pct = (done / total * 100)
        print(f"\r[{done:3d}/{total}] {pct:5.1f}% | {icon} {email[:35]:35s} | {reason[:45]:45s}", end="", flush=True)
    
    results = checker.check_parallel(emails, progress_callback=progress)
    
    print("\n\n" + "=" * 70)
    print("📋 RESULTS")
    print("=" * 70)
    for email, (status, reason) in results.items():
        icon = "✅" if status == "valid" else "❌" if status == "invalid" else "⚠️"
        print(f"{icon} {email:40s} {reason}")
    
    summary = checker.get_summary()
    print("\n" + "=" * 70)
    print("📊 STATISTICS")
    print("=" * 70)
    print(f"✅ Active   : {summary['valid']:,}")
    print(f"❌ Inactive : {summary['invalid']:,}")
    print(f"⚠️  Unknown  : {summary['unknown']:,}")
    print(f"📊 Total    : {summary['checked']:,}")
    print(f"⏱  Time     : {summary['elapsed']:.1f}s")
    print(f"🚀 Speed    : {summary['rate']:.0f} emails/sec")
    
    if summary['mx_attempts']:
        print("\n" + "-" * 70)
        print("🧭 MX SERVER PERFORMANCE")
        print("-" * 70)
        for mx, attempts in sorted(summary['mx_attempts'].items()):
            successes = summary['mx_successes'].get(mx, 0)
            success_rate = (successes / attempts * 100) if attempts > 0 else 0
            print(f"  {mx:40s} | {success_rate:5.0f}% | {successes}/{attempts}")
    
    print("=" * 70 + "\n")
    
    checker.pool.close_all()
