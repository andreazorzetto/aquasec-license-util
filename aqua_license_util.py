#!/usr/bin/env python3
"""
Aqua License Utility
A focused tool for extracting license utilization from Aqua Security platform

Usage:
    python aqua_license_util.py setup                  # Interactive setup
    python aqua_license_util.py show                   # Show license info (JSON)
    python aqua_license_util.py breakdown              # Show breakdown (JSON)
"""

import argparse
import json
import sys
import os
from prettytable import PrettyTable

# Import aquasec library modules
from aquasec import (
    authenticate,
    get_licences,
    get_app_scopes,
    get_repo_count_by_scope,
    get_enforcer_count_by_scope,
    get_code_repo_count_by_scope,
    api_get_dta_license,
    api_post_dta_license_utilization,
    write_json_to_file,
    generate_csv_for_license_breakdown,
    # Configuration management
    load_profile_credentials,
    interactive_setup,
    list_profiles
)

# Version
__version__ = "0.2.0"


def license_show(server, token, verbose=False, debug=False):
    """Show license information"""
    # get the license information
    licenses = get_licences(server, token, debug)

    if verbose:
        # Human-readable table format
        table = PrettyTable(["License", "Value"])
        for key, value in licenses.items():
            table.add_row([key, value])
        print(table)
    else:
        # JSON output by default
        print(json.dumps(licenses, indent=2))


def license_breakdown(server, token, verbose=False, debug=False, csv_file=None, json_file=None):
    """Provide license usage breakdown per application scope"""
    # get the license information
    licenses = get_licences(server, token, debug)
    if debug:
        print("DEBUG: License info:", json.dumps(licenses), "\n")

    # dta
    dta_license = api_get_dta_license(server, token, debug)
    if debug:
        print("DEBUG: DTA License:", dta_license)
    
    dta_license_utilization = None
    if dta_license["enabled"]:
        dta_license_utilization = api_post_dta_license_utilization(server, token, dta_license["token"], dta_license["url"]).json()
        if debug:
            print("DEBUG: DTA License Utilization:", dta_license_utilization, "\n")

    # get all application scopes
    scopes_list = []
    scopes_result = get_app_scopes(server, token)
    for scope in scopes_result:
        scopes_list.append(scope["name"])
    if debug:
        print("DEBUG: Scopes:", scopes_list, "\n")

    # get the count of scopes per repo
    repo_count_by_scope = get_repo_count_by_scope(server, token, scopes_list)
    if debug:
        print("DEBUG: Repo count by scope:", json.dumps(repo_count_by_scope), "\n")

    # get enforcers count by scope
    enforcer_count_by_scope = get_enforcer_count_by_scope(server, token, scopes_list)
    if debug:
        print("DEBUG: Enforcer count by scope:", json.dumps(enforcer_count_by_scope), "\n")

    # get code repositories count by scope
    code_repo_count_by_scope = get_code_repo_count_by_scope(server, token, scopes_list, debug)
    if debug:
        print("DEBUG: Code repo count by scope:", json.dumps(code_repo_count_by_scope), "\n")

    # put scopes, repos, code repos and enforcers data together
    breakdown_data = {}
    for key, value in repo_count_by_scope.items():
        if key in enforcer_count_by_scope:
            breakdown_data[key] = {
                "scope name": key, 
                "repos": value,
                "code_repos": code_repo_count_by_scope.get(key, 0),
                **enforcer_count_by_scope[key]
            }

    # write csv - silent unless verbose
    if csv_file:
        generate_csv_for_license_breakdown(breakdown_data, csv_file)
        if verbose:
            print(f"License breakdown exported to CSV: {csv_file}")

    # write json - silent unless verbose
    if json_file:
        write_json_to_file(json_file, breakdown_data)
        if verbose:
            print(f"License breakdown exported to JSON: {json_file}")

    if verbose:
        # Human-readable table format
        table = PrettyTable()
        table.field_names = ["Scope", "Images", "Code", "Agents",
                            "Kube", "Host", "Micro", "Nano", "Pod"]
        
        for scope, details in breakdown_data.items():
            row = [details["scope name"],
                    details["repos"],
                    details.get("code_repos", 0),
                    details["agent"]["connected"],
                    details["kube_enforcer"]["connected"],
                    details["host_enforcer"]["connected"],
                    details["micro_enforcer"]["connected"],
                    details["nano_enforcer"]["connected"],
                    details["pod_enforcer"]["connected"]]
            table.add_row(row)
        
        print(table)
    else:
        # JSON output by default
        print(json.dumps(breakdown_data, indent=2))


def main():
    """Main function"""
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Create parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--verbose', action='store_true', help='Show human-readable output instead of JSON')
    parent_parser.add_argument('-d', '--debug', action='store_true', help='Show debug output including API calls')
    parent_parser.add_argument('-p', '--profile', default='default', help='Configuration profile to use')
    
    parser = argparse.ArgumentParser(
        description='Aqua License Utility - Extract license utilization from Aqua Security platform',
        prog='aqua_license_util',
        parents=[parent_parser]
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Interactive setup wizard', parents=[parent_parser])
    
    # Profiles command
    profiles_parser = subparsers.add_parser('profiles', help='List available profiles', parents=[parent_parser])
    
    # License show command
    show_parser = subparsers.add_parser('show', help='Show license information (JSON by default, use -v for table)', parents=[parent_parser])
    
    # License breakdown command
    breakdown_parser = subparsers.add_parser('breakdown', help='Show license breakdown by application scope (JSON by default, use -v for table)', parents=[parent_parser])
    breakdown_parser.add_argument('--csv-file', dest='csv_file', action='store', 
                                help='Export to CSV file')
    breakdown_parser.add_argument('--json-file', dest='json_file', action='store', 
                                help='Export to JSON file')
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Handle setup command
    if args.command == 'setup':
        profile = args.profile if hasattr(args, 'profile') and args.profile else 'default'
        success = interactive_setup(profile)
        sys.exit(0 if success else 1)
    
    # Handle profiles command
    if args.command == 'profiles':
        if not args.verbose:
            # JSON output by default
            profile_data = []
            from aqua import ConfigManager
            config_mgr = ConfigManager()
            profiles = config_mgr.list_profiles()
            if not profiles:
                print(json.dumps([], indent=2))
            else:
                for profile in profiles:
                    config = config_mgr.load_config(profile)
                    profile_data.append({
                        "name": profile,
                        "auth_method": config.get('auth_method', 'unknown'),
                        "endpoint": config.get('csp_endpoint', 'unknown')
                    })
                print(json.dumps(profile_data, indent=2))
        else:
            # Verbose mode shows human-readable output
            list_profiles(verbose=True)
        sys.exit(0)
    
    # For other commands, we need authentication
    # First try to load from profile
    profile_loaded = False
    if hasattr(args, 'profile'):
        profile_loaded = load_profile_credentials(args.profile)
    
    # Check if credentials are available (either from profile or environment)
    has_creds = (
        (os.environ.get('AQUA_KEY') and os.environ.get('AQUA_SECRET')) or
        os.environ.get('AQUA_USER')
    )
    
    if not has_creds:
        if args.verbose:
            print("No credentials found.")
            print("\nYou can:")
            print("1. Run 'python aqua_license_util.py setup' to configure credentials")
            print("2. Set environment variables (AQUA_KEY, AQUA_SECRET, etc.)")
            print("3. Create an .env file with credentials")
        else:
            # JSON error output
            print(json.dumps({"error": "No credentials found. Run 'setup' command or set environment variables."}))
        sys.exit(1)
    
    # Authenticate
    try:
        if profile_loaded and args.verbose:
            print(f"Using profile: {args.profile}")
        if args.verbose:
            print("Authenticating with Aqua Security platform...")
        token = authenticate(verbose=args.debug)
        if args.verbose:
            print("Authentication successful!\n")
    except Exception as e:
        if args.verbose:
            print(f"Authentication failed: {e}")
        else:
            print(json.dumps({"error": f"Authentication failed: {str(e)}"}))
        sys.exit(1)
    
    # Get CSP endpoint from environment
    csp_endpoint = os.environ.get('CSP_ENDPOINT')
    
    if not csp_endpoint:
        if args.verbose:
            print("Error: CSP_ENDPOINT environment variable not set")
        else:
            print(json.dumps({"error": "CSP_ENDPOINT environment variable not set"}))
        sys.exit(1)
    
    # Execute commands
    try:
        if args.command == 'show':
            license_show(csp_endpoint, token, args.verbose, args.debug)
        elif args.command == 'breakdown':
            license_breakdown(csp_endpoint, token, args.verbose, args.debug, 
                            args.csv_file, args.json_file)
    except KeyboardInterrupt:
        if args.verbose:
            print('\nExecution interrupted by user')
        sys.exit(0)
    except Exception as e:
        if args.verbose:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        else:
            print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    # Check for required dependencies
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        print("Missing required dependency: cryptography")
        print("Install with: pip install cryptography")
        sys.exit(1)
    
    main()