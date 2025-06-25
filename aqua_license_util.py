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
    api_get_dta_license,
    api_post_dta_license_utilization,
    write_json_to_file,
    generate_csv_for_license_breakdown,
    # Configuration management
    load_profile_credentials,
    interactive_setup,
    list_profiles
)

# Try to import get_code_repo_count_by_scope if available
try:
    from aquasec import get_code_repo_count_by_scope
except ImportError:
    # Function not available in this version
    get_code_repo_count_by_scope = None

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
    if get_code_repo_count_by_scope is not None:
        code_repo_count_by_scope = get_code_repo_count_by_scope(server, token, scopes_list, debug)
        if debug:
            print("DEBUG: Code repo count by scope:", json.dumps(code_repo_count_by_scope), "\n")
    else:
        code_repo_count_by_scope = {}
        if debug:
            print("DEBUG: Code repo count by scope: Not available in this version\n")

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
    
    # Custom argument parsing to support global options anywhere
    # First, let's identify if we have a command and extract global args
    raw_args = sys.argv[1:]
    
    # Extract global arguments regardless of position
    global_args = {
        'verbose': False,
        'debug': False,
        'profile': 'default'
    }
    
    # Check for version first
    if '--version' in raw_args:
        print(f'aqua_license_util {__version__}')
        sys.exit(0)
    
    # Extract global flags from anywhere in the command line
    filtered_args = []
    i = 0
    while i < len(raw_args):
        arg = raw_args[i]
        if arg in ['-v', '--verbose']:
            global_args['verbose'] = True
        elif arg in ['-d', '--debug']:
            global_args['debug'] = True
        elif arg in ['-p', '--profile']:
            if i + 1 < len(raw_args):
                global_args['profile'] = raw_args[i + 1]
                i += 1  # Skip the profile value
        else:
            filtered_args.append(arg)
        i += 1
    
    # Now parse with the filtered args
    parser = argparse.ArgumentParser(
        description='Aqua License Utility - Extract license utilization from Aqua Security platform',
        prog='aqua_license_util',
        epilog='Global options can be placed before or after the command:\n'
               '  -v, --verbose        Show human-readable output instead of JSON\n'
               '  -d, --debug          Show debug output including API calls\n'
               '  -p, --profile        Configuration profile to use (default: default)\n'
               '  --version            Show program version',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Interactive setup wizard')
    
    # Profiles command
    profiles_parser = subparsers.add_parser('profiles', help='List available profiles')
    
    # License show command
    show_parser = subparsers.add_parser('show', help='Show license information (JSON by default, use -v for table)')
    
    # License breakdown command
    breakdown_parser = subparsers.add_parser('breakdown', help='Show license breakdown by application scope (JSON by default, use -v for table)')
    breakdown_parser.add_argument('--csv-file', dest='csv_file', action='store', 
                                help='Export to CSV file')
    breakdown_parser.add_argument('--json-file', dest='json_file', action='store', 
                                help='Export to JSON file')
    
    # Parse the filtered arguments
    args = parser.parse_args(filtered_args)
    
    # Add global args to the namespace
    args.verbose = global_args['verbose']
    args.debug = global_args['debug']
    args.profile = global_args['profile']
    
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
            from aquasec import ConfigManager
            config_mgr = ConfigManager()
            profiles = config_mgr.list_profiles()
            if not profiles:
                print(json.dumps([], indent=2))
            else:
                for profile in profiles:
                    config = config_mgr.load_config(profile)
                    profile_info = {
                        "name": profile,
                        "auth_method": config.get('auth_method', 'unknown'),
                        "csp_endpoint": config.get('csp_endpoint', 'unknown')
                    }
                    # Add api_endpoint if it exists (for SaaS deployments)
                    if 'api_endpoint' in config:
                        profile_info['api_endpoint'] = config['api_endpoint']
                    profile_data.append(profile_info)
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
    has_creds = os.environ.get('AQUA_USER')
    
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
    
    # Print version info in debug mode
    if args.debug:
        import aquasec
        print(f"DEBUG: Aqua License Utility version: {__version__}")
        print(f"DEBUG: Aquasec library version: {aquasec.__version__}")
        print(f"DEBUG: Aquasec library location: {aquasec.__file__}")
        print()
    
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
            # Debug: Show which endpoint we're using
            if args.debug:
                print(f"DEBUG: Using CSP endpoint for license API: {csp_endpoint}")
                api_endpoint = os.environ.get('AQUA_ENDPOINT')
                if api_endpoint:
                    print(f"DEBUG: API endpoint available: {api_endpoint}")
            
            license_show(csp_endpoint, token, args.verbose, args.debug)
        elif args.command == 'breakdown':
            if args.debug:
                print(f"DEBUG: Using CSP endpoint for license API: {csp_endpoint}")
            
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