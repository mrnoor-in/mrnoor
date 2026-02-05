#!/usr/bin/env python3
"""
MrNooR - Social Media Username Availability Checker
Check username availability across popular platforms
"""

import argparse
import requests
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os

class SocialMediaChecker:
    def __init__(self, username, timeout=5):
        self.username = username.strip().lower()
        self.timeout = timeout
        self.results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Platform configurations
        self.platforms = {
            'instagram': {
                'url': f'https://www.instagram.com/{self.username}/',
                'available_text': ['page not found', 'not found'],
                'error_text': ['sorry', 'error']
            },
            'twitter': {
                'url': f'https://twitter.com/{self.username}',
                'available_text': ['this account doesn'],
                'error_text': ['rate limit']
            },
            'facebook': {
                'url': f'https://www.facebook.com/{self.username}',
                'available_text': ['page not found', 'not available'],
                'error_text': []
            },
            'github': {
                'url': f'https://api.github.com/users/{self.username}',
                'available_http': 404,
                'taken_http': 200
            },
            'reddit': {
                'url': f'https://www.reddit.com/user/{self.username}',
                'available_text': ['page not found', 'nobody on reddit'],
                'error_text': []
            },
            'pinterest': {
                'url': f'https://www.pinterest.com/{self.username}/',
                'available_text': ['sorry, we couldn'],
                'error_text': []
            },
            'tiktok': {
                'url': f'https://www.tiktok.com/@{self.username}',
                'available_text': ['couldn\'t find this account'],
                'error_text': []
            },
            'youtube': {
                'url': f'https://www.youtube.com/@{self.username}',
                'available_text': [],
                'error_text': []
            },
            'twitch': {
                'url': f'https://www.twitch.tv/{self.username}',
                'available_text': [],
                'error_text': []
            },
            'linkedin': {
                'url': f'https://www.linkedin.com/in/{self.username}',
                'available_text': [],
                'error_text': []
            },
            'discord': {
                'url': f'https://discord.com/users/{self.username}',
                'available_text': [],
                'error_text': [],
                'check_method': 'discord'
            },
            'spotify': {
                'url': f'https://open.spotify.com/user/{self.username}',
                'available_text': ['page not found'],
                'error_text': []
            },
            'telegram': {
                'url': f'https://t.me/{self.username}',
                'available_text': [],
                'error_text': []
            }
        }
    
    def check_instagram(self, platform_data):
        """Check Instagram username"""
        try:
            response = self.session.get(platform_data['url'], timeout=self.timeout)
            if response.status_code == 404:
                return 'Available'
            elif response.status_code == 200:
                return 'Taken'
            return 'Unknown'
        except:
            return 'Error'
    
    def check_twitter(self, platform_data):
        """Check Twitter/X username"""
        try:
            response = self.session.get(platform_data['url'], timeout=self.timeout)
            if any(text in response.text.lower() for text in platform_data['available_text']):
                return 'Available'
            elif response.status_code == 200:
                return 'Taken'
            return 'Unknown'
        except:
            return 'Error'
    
    def check_github(self, platform_data):
        """Check GitHub username via API"""
        try:
            response = self.session.get(platform_data['url'], timeout=self.timeout)
            if response.status_code == platform_data.get('available_http', 404):
                return 'Available'
            elif response.status_code == platform_data.get('taken_http', 200):
                return 'Taken'
            return 'Unknown'
        except:
            return 'Error'
    
    def check_generic(self, platform_name, platform_data):
        """Generic check for most platforms"""
        try:
            response = self.session.get(platform_data['url'], 
                                      timeout=self.timeout, 
                                      allow_redirects=True)
            
            # Check for "not found" patterns
            if any(text in response.text.lower() for text in platform_data.get('available_text', [])):
                return 'Available'
            
            # Check for error patterns
            if any(text in response.text.lower() for text in platform_data.get('error_text', [])):
                return 'Error'
            
            # If we get a 200, it's likely taken (except for redirects)
            if response.status_code == 200:
                return 'Taken'
            elif response.status_code == 404:
                return 'Available'
            elif 300 <= response.status_code < 400:
                return 'Taken (Redirect)'
            
            return 'Unknown'
        except requests.exceptions.Timeout:
            return 'Timeout'
        except:
            return 'Error'
    
    def check_discord(self, platform_data):
        """Check Discord user ID (Discord doesn't have public username checking)"""
        # Discord requires API token for checking, so we'll just show URL
        return 'Check URL'
    
    def check_all(self, platforms_to_check=None):
        """Check all platforms concurrently"""
        if platforms_to_check is None:
            platforms_to_check = self.platforms.keys()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_platform = {}
            
            for platform in platforms_to_check:
                if platform in self.platforms:
                    if platform == 'github':
                        future = executor.submit(self.check_github, self.platforms[platform])
                    elif platform == 'instagram':
                        future = executor.submit(self.check_instagram, self.platforms[platform])
                    elif platform == 'twitter':
                        future = executor.submit(self.check_twitter, self.platforms[platform])
                    elif platform == 'discord':
                        future = executor.submit(self.check_discord, self.platforms[platform])
                    else:
                        future = executor.submit(self.check_generic, platform, self.platforms[platform])
                    future_to_platform[future] = platform
            
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    self.results[platform] = future.result()
                except Exception as e:
                    self.results[platform] = f'Error: {str(e)}'
        
        return self.results
    
    def generate_report(self):
        """Generate a formatted report"""
        report = []
        report.append("=" * 60)
        report.append(f"SOCIAL MEDIA USERNAME CHECK: @{self.username}")
        report.append(f"Checked on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        # Sort results: Available first, then Taken, then others
        sorted_results = sorted(self.results.items(), 
                              key=lambda x: (x[1] != 'Available', x[1] != 'Taken', x[0]))
        
        for platform, status in sorted_results:
            emoji = "✅" if status == 'Available' else "❌" if status == 'Taken' else "⚠️"
            report.append(f"{emoji} {platform.title():<15} : {status:<20} | {self.platforms[platform]['url']}")
        
        # Summary
        available_count = sum(1 for s in self.results.values() if s == 'Available')
        taken_count = sum(1 for s in self.results.values() if s == 'Taken')
        
        report.append("\n" + "=" * 60)
        report.append(f"SUMMARY: {available_count} Available | {taken_count} Taken | "
                     f"{len(self.results)-available_count-taken_count} Unknown/Error")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_results(self, filename=None):
        """Save results to JSON file"""
        if filename is None:
            filename = f"mrnoor_{self.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'username': self.username,
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'urls': {p: self.platforms[p]['url'] for p in self.platforms}
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename

def main():
    parser = argparse.ArgumentParser(
        description='MrNooR - Social Media Username Availability Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mrnoor check username123            # Check all platforms
  mrnoor check username123 -p instagram twitter github  # Check specific platforms
  mrnoor check username123 -o report.txt  # Save to file
  mrnoor check username123 -j          # Output JSON
  mrnoor check username123 --all      # Check all platforms (default)
  mrnoor list                         # List all supported platforms
        
Available platforms:
  • instagram    • twitter     • facebook    • github
  • reddit       • pinterest   • tiktok      • youtube
  • twitch       • linkedin    • discord     • spotify
  • telegram
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check username availability')
    check_parser.add_argument('username', help='Username to check')
    check_parser.add_argument('-p', '--platforms', nargs='+', 
                            help='Specific platforms to check')
    check_parser.add_argument('-o', '--output', help='Save results to file')
    check_parser.add_argument('-j', '--json', action='store_true', 
                            help='Output in JSON format')
    check_parser.add_argument('-t', '--timeout', type=int, default=5,
                            help='Timeout in seconds (default: 5)')
    check_parser.add_argument('--all', action='store_true', default=True,
                            help='Check all platforms (default)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all supported platforms')
    
    # Bulk command
    bulk_parser = subparsers.add_parser('bulk', help='Check multiple usernames')
    bulk_parser.add_argument('usernames', nargs='+', help='Usernames to check')
    bulk_parser.add_argument('-o', '--output', help='Save results to file')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        checker = SocialMediaChecker(args.username, args.timeout)
        
        if args.platforms:
            platforms = [p.lower() for p in args.platforms]
            invalid = [p for p in platforms if p not in checker.platforms]
            if invalid:
                print(f"Warning: Unsupported platforms: {', '.join(invalid)}")
                platforms = [p for p in platforms if p in checker.platforms]
        else:
            platforms = None
        
        print(f"\n🔍 Checking username: @{args.username}", flush=True)
        print("⏳ This may take a few seconds...\n", flush=True)
        
        results = checker.check_all(platforms)
        
        if args.json:
            output = {
                'username': args.username,
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'urls': {p: checker.platforms[p]['url'] for p in results}
            }
            print(json.dumps(output, indent=2))
        else:
            print(checker.generate_report())
        
        if args.output:
            filename = checker.save_results(args.output)
            print(f"\n📁 Results saved to: {filename}")
    
    elif args.command == 'list':
        print("\n📋 Supported Social Media Platforms:")
        print("=" * 40)
        platforms = list(SocialMediaChecker('test').platforms.keys())
        for i, platform in enumerate(sorted(platforms), 1):
            print(f"{i:2}. {platform.title():<12} - https://.../{platform}/username")
        print(f"\nTotal: {len(platforms)} platforms supported")
    
    elif args.command == 'bulk':
        print(f"\n🔍 Bulk checking {len(args.usernames)} usernames...")
        print("=" * 60)
        
        all_results = {}
        for username in args.usernames:
            checker = SocialMediaChecker(username)
            results = checker.check_all()
            all_results[username] = results
            
            # Show quick summary
            available = sum(1 for s in results.values() if s == 'Available')
            print(f"@{username:<20}: {available:2} available | "
                  f"{len(results)-available:2} taken/unknown")
        
        if args.output:
            filename = f"mrnoor_bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"\n📁 Results saved to: {filename}")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
