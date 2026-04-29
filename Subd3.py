#!/usr/bin/env python3
"""
SubD3 - Fast Subdomain Discovery Tool
Active Bruteforce + Passive Enumeration
"""

import asyncio
import aiohttp
import dns.resolver
import dns.asyncresolver
import json
import time
import random
import argparse
import sys
from typing import List, Set, Dict, Optional

VERSION = "1.0.0"
BANNER = """
╔════════════════════════════════════╗
║        SubD3 - v{}                 ║
║     Fast Subdomain Discovery       ║
╚════════════════════════════════════╝
""".format(VERSION)

RESOLVERS = [
    '8.8.8.8', '8.8.4.4',
    '1.1.1.1', '1.0.0.1',
    '9.9.9.9',
    '208.67.222.222', '208.67.220.220',
]

DEFAULT_WORDLIST = [
    'www', 'mail', 'ftp', 'webmail', 'smtp', 'pop', 'ns1', 'ns2',
    'cpanel', 'whm', 'autodiscover', 'm', 'imap', 'test', 'ns',
    'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'vpn',
    'ns3', 'mail2', 'new', 'mysql', 'old', 'lists', 'support', 'mobile',
    'mx', 'static', 'docs', 'beta', 'shop', 'sql', 'secure', 'demo',
    'cp', 'calendar', 'wiki', 'web', 'media', 'email', 'images', 'img',
    'download', 'dns', 'stats', 'dashboard', 'portal', 'manage', 'start',
    'info', 'apps', 'video', 'sip', 'dns2', 'api', 'cdn', 'remote',
    'server', 'vps', 'help', 'go', 'share', 'upload', 'auth', 'login',
    'signin', 'signup', 'register', 'pay', 'billing', 'account', 'user',
    'customer', 'store', 'checkout', 'crm', 'erp', 'hr', 'intranet',
    'office', 'exchange', 'backup', 'storage', 'db', 'database', 'redis',
    'jenkins', 'gitlab', 'docker', 'kubernetes', 'staging', 'production',
    'prod', 'development', 'sandbox', 'qa', 'uat', 'preprod', 'loadtest',
    'analytics', 'monitoring', 'logs', 'metrics', 'grafana', 'prometheus',
    'kibana', 'elastic', 'kafka', 'rabbitmq', 'mongodb', 'postgres',
    'mysql-backup', 'redis-cache', 'api-gateway', 'auth-service'
]


class SubD3:
    def __init__(self, domain: str, wordlist: List[str] = None, 
                 concurrency: int = 500, timeout: float = 3.0,
                 stealth: bool = False, output_file: str = None,
                 no_passive: bool = False, no_permutation: bool = False):
        self.domain = domain
        self.wordlist = wordlist or DEFAULT_WORDLIST
        self.concurrency = concurrency
        self.timeout = timeout
        self.stealth = stealth
        self.output_file = output_file
        self.no_passive = no_passive
        self.no_permutation = no_permutation
        
        self.found_subdomains: Set[str] = set()
        self.results: List[Dict] = []
        self.found_ips: Dict[str, List[str]] = {}
        
        self.resolver = dns.asyncresolver.Resolver()
        self.resolver.nameservers = RESOLVERS.copy()
        random.shuffle(self.resolver.nameservers)
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout * 2
        
        self.semaphore = asyncio.Semaphore(concurrency)
        self.queries_sent = 0
        self.queries_success = 0
        self.start_time = None
        self.current_resolver_index = 0
    
    def rotate_resolver(self):
        """Rotate DNS resolver to avoid rate limiting"""
        self.current_resolver_index = (self.current_resolver_index + 1) % len(RESOLVERS)
        self.resolver.nameservers = [RESOLVERS[self.current_resolver_index]]
    
    async def resolve(self, subdomain: str, retry: int = 1) -> Optional[Dict]:
        """Resolve subdomain to IP address"""
        full = f"{subdomain}.{self.domain}"
        
        async with self.semaphore:
            self.queries_sent += 1
            
            # Stealth mode: random delay
            if self.stealth:
                await asyncio.sleep(random.uniform(0.02, 0.15))
            
            # Rotate resolver every 100 queries
            if self.queries_sent % 100 == 0:
                self.rotate_resolver()
            
            try:
                answers = await self.resolver.resolve(full, 'A')
                if answers:
                    self.queries_success += 1
                    ips = [str(a) for a in answers]
                    return {
                        'subdomain': subdomain,
                        'full_domain': full,
                        'ips': ips,
                        'timestamp': time.time()
                    }
            except dns.resolver.NXDOMAIN:
                pass
            except dns.resolver.NoAnswer:
                pass
            except dns.resolver.Timeout:
                if retry > 0:
                    await asyncio.sleep(0.5)
                    return await self.resolve(subdomain, retry - 1)
            except Exception:
                pass
            return None
    
    async def passive_scan(self) -> Set[str]:
        """Passive enumeration from crt.sh"""
        print("[*] Passive scan from crt.sh...")
        found = set()
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://crt.sh/?q=%.{self.domain}&output=json"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data:
                            name = entry.get('name_value', '')
                            if name:
                                for part in name.split('\n'):
                                    part = part.strip().lower()
                                    if part.endswith(f".{self.domain}") and part != self.domain:
                                        sub = part.replace(f".{self.domain}", "")
                                        if '*' not in sub:
                                            found.add(sub)
        except Exception as e:
            print(f"[-] Passive scan error: {e}")
        
        print(f"[+] Found {len(found)} subdomains from passive sources")
        return found
    
    async def active_scan(self, skip: Set[str]) -> List[Dict]:
        """Active bruteforce with wordlist"""
        print(f"[*] Active bruteforce with {len(self.wordlist)} words...")
        
        to_check = list(set(self.wordlist) - skip)
        tasks = [self.resolve(w) for w in to_check]
        
        results = []
        completed = 0
        last_print = 0
        
        for coro in asyncio.as_completed(tasks):
            res = await coro
            completed += 1
            
            # Print progress every 100 or when done
            if completed - last_print >= 100 or completed == len(to_check):
                rate = (self.queries_success / self.queries_sent * 100) if self.queries_sent > 0 else 0
                print(f"  Progress: {completed}/{len(to_check)} | Found: {len(results)} | Success: {rate:.1f}%")
                last_print = completed
            
            if res:
                results.append(res)
                self.found_subdomains.add(res['subdomain'])
                self.found_ips[res['full_domain']] = res['ips']
                print(f"  [+] {res['full_domain']} -> {', '.join(res['ips'])}")
        
        return results
    
    async def permutation_scan(self, found: List[Dict]) -> List[Dict]:
        """Permutation attack based on found subdomains"""
        print("[*] Permutation attack...")
        
        perms = set()
        
        # Suffixes
        suffixes = ['-dev', '-staging', '-test', '-old', '-new', '-backup', '-api', 
                    '-prod', '-uat', '-qa', '-demo', '-beta', '-alpha', '-v1', '-v2']
        
        # Prefixes
        prefixes = ['dev-', 'staging-', 'test-', 'backup-', 'api-', 'admin-',
                    'prod-', 'uat-', 'qa-', 'demo-', 'beta-', 'old-', 'new-']
        
        # Numeric variants
        numbers = ['1', '2', '3', '01', '02', '03']
        
        for item in found:
            sub = item['subdomain']
            
            # Add suffixes
            for s in suffixes:
                perms.add(f"{sub}{s}")
            
            # Add prefixes
            for p in prefixes:
                perms.add(f"{p}{sub}")
            
            # Add numeric variants
            for n in numbers:
                perms.add(f"{sub}{n}")
                perms.add(f"{n}{sub}")
            
            # Handle hyphenated subdomains
            if '-' in sub:
                parts = sub.split('-')
                if len(parts) >= 2:
                    perms.add(f"{parts[0]}{parts[1]}")
                    perms.add(f"{parts[1]}-{parts[0]}")
            
            # Add common combinations
            common = ['api', 'admin', 'backup', 'cdn', 'static', 'media', 'upload']
            for c in common:
                perms.add(f"{sub}-{c}")
                perms.add(f"{c}-{sub}")
        
        to_check = perms - self.found_subdomains
        to_check = list(to_check)[:5000]  # Limit permutations
        
        if not to_check:
            print("[*] No new permutations to check")
            return []
        
        print(f"[*] Checking {len(to_check)} permutations...")
        
        tasks = [self.resolve(w) for w in to_check]
        new_results = []
        
        for coro in asyncio.as_completed(tasks):
            res = await coro
            if res:
                new_results.append(res)
                self.found_subdomains.add(res['subdomain'])
                self.found_ips[res['full_domain']] = res['ips']
                print(f"  [+] [perm] {res['full_domain']} -> {', '.join(res['ips'])}")
        
        return new_results
    
    def print_summary(self, elapsed: float):
        """Print scan summary"""
        print("\n" + "="*50)
        print("SCAN COMPLETE")
        print("="*50)
        print(f"Target: {self.domain}")
        print(f"Subdomains found: {len(self.found_subdomains)}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Queries sent: {self.queries_sent}")
        print(f"Successful queries: {self.queries_success}")
        print(f"Success rate: {(self.queries_success/self.queries_sent*100):.1f}%")
        
        if self.found_subdomains:
            # Group by IP
            ip_count = {}
            for full, ips in self.found_ips.items():
                for ip in ips:
                    ip_count[ip] = ip_count.get(ip, 0) + 1
            
            print(f"\n[+] Discovered subdomains ({len(self.found_subdomains)}):")
            for sub in sorted(self.found_subdomains):
                ips = self.found_ips.get(f"{sub}.{self.domain}", [])
                ip_str = f" -> {', '.join(ips)}" if ips else ""
                print(f"    {sub}.{self.domain}{ip_str}")
            
            if ip_count:
                print(f"\n[+] Unique IP addresses: {len(ip_count)}")
                print(f"    Most common IP: {max(ip_count, key=ip_count.get)} ({max(ip_count.values())} subdomains)")
    
    def save_results(self):
        """Save results to JSON file"""
        if not self.output_file:
            return
        
        report = {
            'target': self.domain,
            'scan_start': self.start_time,
            'scan_end': time.time(),
            'duration_seconds': time.time() - self.start_time,
            'total_found': len(self.found_subdomains),
            'queries_sent': self.queries_sent,
            'queries_success': self.queries_success,
            'subdomains': [],
            'ip_mapping': {}
        }
        
        for full, ips in self.found_ips.items():
            report['subdomains'].append({
                'full_domain': full,
                'ips': ips
            })
            for ip in ips:
                if ip not in report['ip_mapping']:
                    report['ip_mapping'][ip] = []
                report['ip_mapping'][ip].append(full)
        
        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n[+] Results saved to: {self.output_file}")
    
    async def run(self):
        """Main execution"""
        self.start_time = time.time()
        
        print(BANNER)
        print(f"[*] Domain: {self.domain}")
        print(f"[*] Concurrency: {self.concurrency}")
        print(f"[*] Timeout: {self.timeout}s")
        print(f"[*] Stealth mode: {self.stealth}")
        print(f"[*] Wordlist size: {len(self.wordlist)}")
        print(f"[*] DNS resolvers: {len(RESOLVERS)}")
        print()
        
        # Step 1: Passive enumeration
        passive_found = set()
        if not self.no_passive:
            passive_found = await self.passive_scan()
            for sub in passive_found:
                self.found_subdomains.add(sub)
                self.results.append({
                    'subdomain': sub, 
                    'full_domain': f"{sub}.{self.domain}", 
                    'ips': [],
                    'source': 'passive'
                })
        else:
            print("[*] Passive scan disabled")
        
        # Step 2: Active bruteforce
        active_results = await self.active_scan(passive_found)
        self.results.extend(active_results)
        
        # Step 3: Permutation attack
        if not self.no_permutation and self.results:
            perm_results = await self.permutation_scan(self.results)
            self.results.extend(perm_results)
        elif self.no_permutation:
            print("[*] Permutation attack disabled")
        
        # Summary
        elapsed = time.time() - self.start_time
        self.print_summary(elapsed)
        self.save_results()
        
        return self.results


def load_wordlist(filepath: str) -> List[str]:
    """Load wordlist from file"""
    try:
        with open(filepath, 'r') as f:
            words = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
        return words
    except Exception as e:
        print(f"[-] Error loading wordlist: {e}")
        return DEFAULT_WORDLIST


def main():
    parser = argparse.ArgumentParser(
        description="SubD3 - Fast Subdomain Discovery Tool",
        epilog="Example: python subd3.py -d example.com -o results.json --stealth"
    )
    
    parser.add_argument("-d", "--domain", required=True, help="Target domain")
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file (one per line)")
    parser.add_argument("-c", "--concurrency", type=int, default=500, 
                        help="Concurrent queries (default: 500)")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("-t", "--timeout", type=float, default=3.0, 
                        help="DNS timeout in seconds (default: 3.0)")
    parser.add_argument("--stealth", action="store_true", 
                        help="Enable stealth mode (random delays)")
    parser.add_argument("--no-passive", action="store_true", 
                        help="Disable passive enumeration from crt.sh")
    parser.add_argument("--no-permutation", action="store_true", 
                        help="Disable permutation attack")
    parser.add_argument("--version", action="version", version=f"SubD3 {VERSION}")
    
    args = parser.parse_args()
    
    # Validate domain
    if not args.domain or '.' not in args.domain:
        print("[-] Invalid domain format")
        sys.exit(1)
    
    # Load wordlist
    wordlist = DEFAULT_WORDLIST
    if args.wordlist:
        wordlist = load_wordlist(args.wordlist)
        print(f"[*] Loaded {len(wordlist)} words from {args.wordlist}")
    
    # Run scanner
    scanner = SubD3(
        domain=args.domain.lower(),
        wordlist=wordlist,
        concurrency=args.concurrency,
        timeout=args.timeout,
        stealth=args.stealth,
        output_file=args.output,
        no_passive=args.no_passive,
        no_permutation=args.no_permutation
    )
    
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        print("\n[-] Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
