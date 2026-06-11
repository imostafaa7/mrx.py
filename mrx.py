#!/usr/bin/env python3

import os
import subprocess
import sys
import argparse
import time

# For colored output and ASCII art
try:
    from colorama import Fore, Style, init
    import pyfiglet
    init(autoreset=True)
except ImportError:
    print("[*] Installing required modules: colorama, pyfiglet...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama", "pyfiglet"])
    from colorama import Fore, Style, init
    import pyfiglet
    init(autoreset=True)

# --- Global Variables ---
TARGET_DOMAIN = ""
OUTPUT_DIR = "mrx_results"

# --- ASCII Art & Banners ---
def print_banner():
    clear_screen()
    ascii_banner = pyfiglet.figlet_format("MRX", font="slant")
    print(Fore.CYAN + ascii_banner)
    print(Fore.YELLOW + "\t\tAutomated Recon & Vulnerability Scanning Workflow")
    print(Fore.MAGENTA + "\t\t\tCreated by imostafaa9")
    print(Style.RESET_ALL + "\n" + "="*70 + "\n")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Tool Management ---
REQUIRED_TOOLS = {
    "subfinder": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    "amass": "sudo apt install amass -y",
    "httpx": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
    "nmap": "sudo apt install nmap -y",
    "naabu": "go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
    "ffuf": "go install github.com/ffuf/ffuf@latest",
    "gau": "go install github.com/lc/gau/v2/cmd/gau@latest",
    "waybackurls": "go install github.com/tomnomnom/waybackurls@latest",
    "nuclei": "go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest",
    "dalfox": "go install github.com/hahwul/dalfox/v2@latest",
    "sqlmap": "sudo apt install sqlmap -y",
    "qsreplace": "go install github.com/tomnomnom/qsreplace@latest",
    "nikto": "sudo apt install nikto -y",
    "subzy": "go install -v github.com/lukasikic/subzy@latest",
    "gf": "go install github.com/tomnomnom/gf@latest",
}

def check_and_install_tools():
    print(f"\n{Fore.CYAN}[*] Checking dependencies and tools...{Style.RESET_ALL}")
    
    # Check for Go
    if subprocess.run("command -v go", shell=True, capture_output=True).returncode != 0:
        print(f"{Fore.YELLOW}[!] Go is not installed. Installing Go...{Style.RESET_ALL}")
        run_command("sudo apt update && sudo apt install golang -y", "Installing Go")
        # Update PATH for Go
        os.environ["PATH"] += os.pathsep + os.path.join(os.path.expanduser("~"), "go", "bin")

    for tool, install_cmd in REQUIRED_TOOLS.items():
        if subprocess.run(f"command -v {tool}", shell=True, capture_output=True).returncode != 0:
            print(f"{Fore.YELLOW}[!] {tool} is not installed. Installing...{Style.RESET_ALL}")
            run_command(install_cmd, f"Installing {tool}")
        else:
            print(f"{Fore.GREEN}[+] {tool} is already installed.{Style.RESET_ALL}")

    # Special handling for gf patterns
    gf_path = os.path.join(os.path.expanduser("~"), ".gf")
    if not os.path.exists(gf_path):
        os.makedirs(gf_path, exist_ok=True)
        print(f"{Fore.YELLOW}[!] Setting up gf patterns...{Style.RESET_ALL}")
        run_command(f"git clone https://github.com/1ndianl337/Gf-Patterns {gf_path}/patterns", "Cloning GF Patterns")
        run_command(f"cp {gf_path}/patterns/*.json {gf_path}/", "Copying GF Patterns")

# --- Helper Functions ---
def run_command(command, message, output_file=None):
    print(f"\n{Fore.BLUE}[*] {message}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}  Running: {command}{Style.RESET_ALL}")
    
    # Ensure tool is in path (especially for Go tools)
    go_bin = os.path.join(os.path.expanduser("~"), "go", "bin")
    if go_bin not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + go_bin

    try:
        if output_file:
            with open(output_file, "a") as f:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    sys.stdout.write(line)
                    f.write(line)
                process.wait()
        else:
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                print(f"{Fore.YELLOW}[!] Warning during {message}: {process.stderr}{Style.RESET_ALL}")
            else:
                print(process.stdout)
        print(f"{Fore.GREEN}[+] {message} Completed!{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}[-] Error during {message}: {str(e)}{Style.RESET_ALL}")
        return False

# --- Workflow Phases ---
def phase_subdomain_enumeration():
    print(f"\n{Fore.CYAN}--- [1] SUBDOMAIN ENUMERATION ---{Style.RESET_ALL}")
    subs_file = os.path.join(OUTPUT_DIR, "subs.txt")
    run_command(f"subfinder -d {TARGET_DOMAIN} -o {subs_file}", "Subfinder Enumeration")
    run_command(f"amass enum -passive -d {TARGET_DOMAIN} >> {subs_file}", "Amass Passive Enumeration")
    run_command(f"sort -u {subs_file} -o {subs_file}", "Sorting Subdomains")

def phase_check_live_hosts():
    print(f"\n{Fore.CYAN}--- [2] CHECK LIVE HOSTS ---{Style.RESET_ALL}")
    subs_file = os.path.join(OUTPUT_DIR, "subs.txt")
    live_file = os.path.join(OUTPUT_DIR, "live.txt")
    run_command(f"httpx -l {subs_file} -o {live_file} -status-code -title -tech-detect", "Checking Live Hosts")

def phase_port_scanning():
    print(f"\n{Fore.CYAN}--- [3] PORT SCANNING ---{Style.RESET_ALL}")
    live_file = os.path.join(OUTPUT_DIR, "live.txt")
    ports_file = os.path.join(OUTPUT_DIR, "ports.txt")
    run_command(f"nmap -iL {live_file} -sV -T4 --open -oN {ports_file}", "Nmap Port Scanning")
    # Fast scan alternative
    ports_fast_file = os.path.join(OUTPUT_DIR, "ports_fast.txt")
    run_command(f"naabu -list {live_file} -o {ports_fast_file}", "Naabu Fast Port Scanning")

def phase_directory_fuzzing():
    print(f"\n{Fore.CYAN}--- [4] DIRECTORY & PATH FUZZING ---{Style.RESET_ALL}")
    dirs_file = os.path.join(OUTPUT_DIR, "dirs.txt")
    # Common directory fuzzing
    run_command(f"ffuf -u https://{TARGET_DOMAIN}/FUZZ -w /usr/share/wordlists/dirb/common.txt -mc 200,301,302,403 -o {dirs_file}", "FFUF Directory Fuzzing")
    # Sensitive files fuzzing
    run_command(f"ffuf -u https://{TARGET_DOMAIN}/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt -o {os.path.join(OUTPUT_DIR, 'sensitive_files.txt')}", "FFUF Sensitive Files Fuzzing")

def phase_collect_historical_urls():
    print(f"\n{Fore.CYAN}--- [5] COLLECT HISTORICAL URLS ---{Style.RESET_ALL}")
    urls_gau = os.path.join(OUTPUT_DIR, "urls_gau.txt")
    urls_wb = os.path.join(OUTPUT_DIR, "urls_wb.txt")
    all_urls = os.path.join(OUTPUT_DIR, "all_urls.txt")
    run_command(f"gau {TARGET_DOMAIN} | tee {urls_gau}", "GAU URL Collection")
    run_command(f"waybackurls {TARGET_DOMAIN} | tee {urls_wb}", "Waybackurls Collection")
    run_command(f"cat {urls_gau} {urls_wb} | sort -u | tee {all_urls}", "Merging and Sorting URLs")

def phase_extract_js_endpoints():
    print(f"\n{Fore.CYAN}--- [6] EXTRACT JS ENDPOINTS ---{Style.RESET_ALL}")
    live_file = os.path.join(OUTPUT_DIR, "live.txt")
    js_files = os.path.join(OUTPUT_DIR, "js_files.txt")
    endpoints = os.path.join(OUTPUT_DIR, "endpoints.txt")
    # Note: getJS and linkfinder might need manual installation or specific paths
    run_command(f"cat {live_file} | getJS --complete | tee {js_files}", "Extracting JS Files")
    # Assuming linkfinder.py is in the current directory or PATH
    run_command(f"python3 linkfinder.py -i {js_files} -d -o {endpoints}", "Extracting Endpoints from JS")

def phase_filter_parameters():
    print(f"\n{Fore.CYAN}--- [7] FILTER PARAMETERS ---{Style.RESET_ALL}")
    all_urls = os.path.join(OUTPUT_DIR, "all_urls.txt")
    params = os.path.join(OUTPUT_DIR, "params.txt")
    run_command(f"cat {all_urls} | grep '=' | tee {params}", "Extracting Parameters")
    
    # GF Filtering
    run_command(f"cat {all_urls} | gf xss | tee {os.path.join(OUTPUT_DIR, 'params_xss.txt')}", "Filtering XSS Parameters")
    run_command(f"cat {all_urls} | gf sqli | tee {os.path.join(OUTPUT_DIR, 'params_sqli.txt')}", "Filtering SQLi Parameters")
    run_command(f"cat {all_urls} | gf ssrf | tee {os.path.join(OUTPUT_DIR, 'params_ssrf.txt')}", "Filtering SSRF Parameters")
    run_command(f"cat {all_urls} | gf redirect | tee {os.path.join(OUTPUT_DIR, 'params_redirect.txt')}", "Filtering Redirect Parameters")

def phase_automated_vulnerability_scanning():
    print(f"\n{Fore.CYAN}--- [8] NUCLEI SCANNING ---{Style.RESET_ALL}")
    live_file = os.path.join(OUTPUT_DIR, "live.txt")
    nuclei_results = os.path.join(OUTPUT_DIR, "nuclei_results.txt")
    run_command(f"nuclei -l {live_file} -t cves/ -t exposures/ -t misconfigurations/ -o {nuclei_results}", "Nuclei CVEs/Exposures/Misconfigs Scan")
    run_command(f"nuclei -l {live_file} -t vulnerabilities/ -severity medium,high,critical", "Nuclei Vulnerabilities Scan")

def phase_xss_scanning():
    print(f"\n{Fore.CYAN}--- [9] XSS SCANNING ---{Style.RESET_ALL}")
    params_xss = os.path.join(OUTPUT_DIR, "params_xss.txt")
    xss_results = os.path.join(OUTPUT_DIR, "xss_results.txt")
    run_command(f"dalfox file {params_xss} -o {xss_results}", "Dalfox XSS Scan")
    # KXSS alternative
    run_command(f"cat {params_xss} | kxss", "KXSS Parameter Testing")

def phase_sql_injection():
    print(f"\n{Fore.CYAN}--- [10] SQL INJECTION ---{Style.RESET_ALL}")
    params_sqli = os.path.join(OUTPUT_DIR, "params_sqli.txt")
    sqlmap_dir = os.path.join(OUTPUT_DIR, "sqlmap_results")
    run_command(f"sqlmap -m {params_sqli} --batch --level=3 --risk=2 --dbs --output-dir={sqlmap_dir}", "SQLMap Injection Testing")

def phase_ssrf_testing():
    print(f"\n{Fore.CYAN}--- [11] SSRF TESTING ---{Style.RESET_ALL}")
    params_ssrf = os.path.join(OUTPUT_DIR, "params_ssrf.txt")
    # User needs to provide Burp Collaborator or similar for meaningful results
    print(f"{Fore.YELLOW}[!] SSRF testing requires a listener (e.g., Burp Collaborator). Skipping interactive part.{Style.RESET_ALL}")
    run_command(f"cat {params_ssrf} | qsreplace 'http://mrx-ssrf-test.com' | httpx -silent", "SSRF Parameter Replacement Test")

def phase_open_redirect():
    print(f"\n{Fore.CYAN}--- [12] OPEN REDIRECT ---{Style.RESET_ALL}")
    params_redirect = os.path.join(OUTPUT_DIR, "params_redirect.txt")
    run_command(f"cat {params_redirect} | qsreplace 'https://evil.com' | httpx -silent -location", "Open Redirect Testing")

def phase_nikto_scan():
    print(f"\n{Fore.CYAN}--- [13] NIKTO SCAN ---{Style.RESET_ALL}")
    nikto_file = os.path.join(OUTPUT_DIR, "nikto.txt")
    run_command(f"nikto -h https://{TARGET_DOMAIN} -output {nikto_file}", "Nikto Web Server Scan")

def phase_cors_misconfiguration():
    print(f"\n{Fore.CYAN}--- [14] CORS MISCONFIGURATION ---{Style.RESET_ALL}")
    live_file = os.path.join(OUTPUT_DIR, "live.txt")
    # Assuming corsy.py is available
    run_command(f"python3 corsy.py -i {live_file} -t 10 --headers 'Origin: https://evil.com'", "CORS Misconfiguration Testing")

def phase_subdomain_takeover():
    print(f"\n{Fore.CYAN}--- [15] SUBDOMAIN TAKEOVER ---{Style.RESET_ALL}")
    subs_file = os.path.join(OUTPUT_DIR, "subs.txt")
    run_command(f"subzy run --targets {subs_file} --concurrency 100 --hide-fails", "Subdomain Takeover Check")

# --- Main Function ---
def main():
    global TARGET_DOMAIN, OUTPUT_DIR

    parser = argparse.ArgumentParser(description="MRX: Automated Recon & Vulnerability Scanning Workflow")
    parser.add_argument("-d", "--domain", required=True, help="Target domain (e.g., example.com)")
    parser.add_argument("-o", "--output", default="mrx_results", help="Output directory for results (default: mrx_results)")
    args = parser.parse_args()

    TARGET_DOMAIN = args.domain
    OUTPUT_DIR = args.output

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print_banner()
    print(f"{Fore.GREEN}[*] Starting MRX scan for: {TARGET_DOMAIN}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[*] Results will be saved in: {OUTPUT_DIR}{Style.RESET_ALL}")
    time.sleep(2)

    # Ensure all tools are installed
    check_and_install_tools()

    # Execute workflow phases
    phase_subdomain_enumeration()
    phase_check_live_hosts()
    phase_port_scanning()
    phase_directory_fuzzing()
    phase_collect_historical_urls()
    phase_extract_js_endpoints()
    phase_filter_parameters()
    phase_automated_vulnerability_scanning()
    phase_xss_scanning()
    phase_sql_injection()
    phase_ssrf_testing()
    phase_open_redirect()
    phase_nikto_scan()
    phase_cors_misconfiguration()
    phase_subdomain_takeover()

    print_summary()

def print_summary():
    print(f"\n{Fore.MAGENTA}" + "="*70)
    print(f"{Fore.CYAN}                 MRX SCAN SUMMARY")
    print(f"{Fore.MAGENTA}" + "="*70 + Style.RESET_ALL)
    
    summary_data = [
        ("Subdomains Found", "subs.txt"),
        ("Live Hosts", "live.txt"),
        ("Open Ports", "ports.txt"),
        ("Historical URLs", "all_urls.txt"),
        ("Nuclei Findings", "nuclei_results.txt"),
        ("XSS Potential", "xss_results.txt"),
    ]
    
    for label, filename in summary_data:
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            try:
                count = sum(1 for line in open(filepath, 'r', errors='ignore'))
                print(f"{Fore.WHITE}{label:<25}: {Fore.GREEN}{count}{Style.RESET_ALL}")
            except:
                print(f"{Fore.WHITE}{label:<25}: {Fore.YELLOW}Checked{Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE}{label:<25}: {Fore.RED}Not Found{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}[+] MRX scan completed for {TARGET_DOMAIN}!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[*] All results are saved in: {os.path.abspath(OUTPUT_DIR)}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}" + "="*70 + Style.RESET_ALL)

if __name__ == "__main__":
    main()
