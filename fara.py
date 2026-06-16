import requests
import json
import threading
import time
import concurrent.futures
from datetime import datetime
import os
from dotenv import load_dotenv
from config import Config

# Load environment variables from .env file
load_dotenv()

# Validate configuration
Config.validate()

# Get configuration
url = Config.API_URL
headers = Config.get_headers()
base_payload = Config.get_base_payload()


# Initialize with first request test (optional - comment out if not needed)
# print("=" * 60)
# print("🔍 Testing API connection...")
# print("=" * 60)


# Statistics
success_count = 0
error_count = 0
rate_limit_count = 0
timeout_count = 0
lock = threading.Lock()

class RateLimiter:
    def __init__(self, rate_per_sec):
        self.rate_per_sec = rate_per_sec
        self.interval = 1.0 / rate_per_sec if rate_per_sec > 0 else 0
        self.last_time = time.time()
        self.lock = threading.Lock()
    
    def wait(self):
        if self.rate_per_sec <= 0:
            return
        with self.lock:
            now = time.time()
            wait_time = self.last_time + self.interval - now
            if wait_time > 0:
                time.sleep(wait_time)
            self.last_time = time.time()

def send_request(request_id, rate_limiter, timeout_sec):
    """Send a single request"""
    global success_count, error_count, rate_limit_count, timeout_count
    
    if rate_limiter:
        rate_limiter.wait()
    
    # Create unique payload
    payload = base_payload.copy()
    payload["clientTag"] = f"Falcon-Offline-{request_id}-{int(time.time()*1000)}"
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
        
        with lock:
            if response.status_code == 200:
                success_count += 1
                print(f"[✓] Req {request_id} - 200")
            elif response.status_code == 429:
                rate_limit_count += 1
                error_count += 1
                print(f"[⚠️] Req {request_id} - Rate Limit (429)")
            else:
                error_count += 1
                print(f"[✗] Req {request_id} - {response.status_code}")
                
    except requests.exceptions.Timeout:
        with lock:
            timeout_count += 1
            error_count += 1
            print(f"[⌛] Req {request_id} - Timeout")
    except Exception as e:
        with lock:
            error_count += 1
            print(f"[✗] Req {request_id} - {str(e)[:30]}")

def clear_screen():
    """Clear console screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_config():
    """Get configuration from user"""
    clear_screen()
    print("=" * 60)
    print("       Concurrent Request Sender - Configuration")
    print("=" * 60)
    
    print("\n📊 Main Settings:")
    print("-" * 40)
    
    while True:
        try:
            total = int(input("🔢 Total number of requests (e.g., 100): "))
            if total > 0:
                break
            print("❌ Please enter a positive number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    while True:
        try:
            rate = float(input("⚡ Request rate (requests per second) - 0 for unlimited (e.g., 10): "))
            if rate >= 0:
                break
            print("❌ Please enter a positive number or zero")
        except ValueError:
            print("❌ Please enter a valid number")
    
    while True:
        try:
            workers = int(input("🧵 Number of concurrent threads (e.g., 20): "))
            if workers > 0:
                break
            print("❌ Please enter a positive number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    while True:
        try:
            timeout = int(input("⏱️ Request timeout (seconds) - e.g., 5: "))
            if timeout > 0:
                break
            print("❌ Please enter a positive number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print("\n🎯 Advanced Settings:")
    print("-" * 40)
    
    show_detail = input("📝 Show detailed output for each request? (y/n) - default: n: ").lower() == 'y'
    
    save_result = input("💾 Save results to file? (y/n) - default: n: ").lower() == 'y'
    
    print("\n" + "=" * 60)
    print("📋 Configuration Summary:")
    print(f"   Total requests: {total}")
    print(f"   Request rate: {rate} req/sec" + (" (unlimited)" if rate == 0 else ""))
    print(f"   Concurrent threads: {workers}")
    print(f"   Timeout: {timeout} seconds")
    print(f"   Show details: {'Yes' if show_detail else 'No'}")
    print(f"   Save results: {'Yes' if save_result else 'No'}")
    print("=" * 60)
    
    confirm = input("\n✅ Proceed with these settings? (y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ Execution cancelled.")
        return None
    
    return {
        'total': total,
        'rate': rate,
        'workers': workers,
        'timeout': timeout,
        'show_detail': show_detail,
        'save_result': save_result
    }

def send_requests(config):
    """Send requests with user configuration"""
    global success_count, error_count, rate_limit_count, timeout_count
    
    # Reset statistics
    success_count = 0
    error_count = 0
    rate_limit_count = 0
    timeout_count = 0
    
    print("\n" + "=" * 60)
    print("🚀 Starting request sending...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Create RateLimiter
    rate_limiter = RateLimiter(config['rate']) if config['rate'] > 0 else None
    
    # Disable detailed output if user doesn't want it
    original_print = print
    if not config['show_detail']:
        def custom_print(*args, **kwargs):
            if args[0].startswith("[✓]") or args[0].startswith("[✗]") or args[0].startswith("[⚠️]") or args[0].startswith("[⌛]"):
                return
            original_print(*args, **kwargs)
        globals()['print'] = custom_print
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=config['workers']) as executor:
            futures = []
            for i in range(config['total']):
                future = executor.submit(send_request, i+1, rate_limiter, config['timeout'])
                futures.append(future)
                
                # Show progress every 10% or every 100 requests
                if (i + 1) % max(1, config['total'] // 10) == 0 or (i + 1) % 100 == 0:
                    progress = (i + 1) / config['total'] * 100
                    elapsed = time.time() - start_time
                    print(f"⏱️ Progress: {i+1}/{config['total']} ({progress:.1f}%) - Time: {elapsed:.1f}s")
            
            # Wait for all to complete
            concurrent.futures.wait(futures)
    
    finally:
        # Restore original print
        globals()['print'] = original_print
    
    # Final calculations
    elapsed_time = time.time() - start_time
    success_rate = (success_count / config['total']) * 100 if config['total'] > 0 else 0
    actual_rate = config['total'] / elapsed_time if elapsed_time > 0 else 0
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 Final Report:")
    print("=" * 60)
    print(f"   ✅ Successful requests (200): {success_count}")
    print(f"   ❌ Failed requests: {error_count}")
    print(f"   🚫 Rate limited (429): {rate_limit_count}")
    print(f"   ⌛ Timeouts: {timeout_count}")
    print(f"   📈 Actual rate: {actual_rate:.2f} requests/second")
    print(f"   ⏱️ Total time: {elapsed_time:.2f} seconds")
    print(f"   📊 Success rate: {success_rate:.1f}%")
    print("=" * 60)
    
    # Save to file
    if config['save_result']:
        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Request Sending Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Total requests: {config['total']}\n")
            f.write(f"Request rate: {config['rate']} requests/second\n")
            f.write(f"Concurrent threads: {config['workers']}\n")
            f.write(f"Timeout: {config['timeout']} seconds\n")
            f.write("-" * 50 + "\n")
            f.write(f"Successful: {success_count}\n")
            f.write(f"Failed: {error_count}\n")
            f.write(f"Rate limited: {rate_limit_count}\n")
            f.write(f"Timeouts: {timeout_count}\n")
            f.write(f"Actual rate: {actual_rate:.2f} requests/second\n")
            f.write(f"Total time: {elapsed_time:.2f} seconds\n")
            f.write(f"Success rate: {success_rate:.1f}%\n")
        print(f"\n💾 Results saved to '{filename}'")

def main():
    """Main function"""
    while True:
        config = get_user_config()
        if config is None:
            break
        
        send_requests(config)
        
        print("\n" + "=" * 60)
        again = input("🔄 Do you want to run again? (y/n): ")
        if again.lower() != 'y':
            print("\n👋 Goodbye!")
            break
        print("\n" * 2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Execution stopped by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")