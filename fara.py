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
    """Send a single request (legacy/single-user mode)"""
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


def send_request_user(user_index, seq, user_conf, timeout_sec):
    """Send a request for a specific user configuration.

    user_conf: dict with keys 'token', 'instrument', 'quantity', 'price'
    seq: sequence number for this user's request
    """
    global success_count, error_count, rate_limit_count, timeout_count

    # Build headers (override Authorization if provided per-user)
    local_headers = headers.copy() if headers is not None else {}
    token = user_conf.get('token')
    if token:
        # If token already contains Bearer prefix, keep it; otherwise add
        if token.lower().startswith('bearer '):
            local_headers['Authorization'] = token
        else:
            local_headers['Authorization'] = f"Bearer {token}"
    # Ensure Content-Type header
    if 'Content-Type' not in local_headers and 'content-type' not in local_headers:
        local_headers['Content-Type'] = 'application/json'

    # Prepare payload
    payload = base_payload.copy()
    # Override instrument/quantity/price if provided
    if 'instrument' in user_conf and user_conf['instrument']:
        payload['instrumentIdentification'] = user_conf['instrument']
    if 'quantity' in user_conf and user_conf['quantity'] is not None:
        # API examples sometimes expect quantity as string
        payload['quantity'] = str(user_conf['quantity'])
    if 'price' in user_conf and user_conf['price']:
        payload['price'] = user_conf['price']

    # validateAssetOnSell (default False) - allow override
    if 'validateAssetOnSell' in user_conf:
        payload['validateAssetOnSell'] = bool(user_conf['validateAssetOnSell'])
    else:
        # keep base_payload default if present
        payload.setdefault('validateAssetOnSell', False)

    # validityDate: optional ISO string (if provided)
    if 'validityDate' in user_conf and user_conf['validityDate']:
        payload['validityDate'] = user_conf['validityDate']

    payload['clientTag'] = f"User{user_index}-Seq{seq}-{int(time.time()*1000)}"

    try:
        response = requests.post(url, headers=local_headers, json=payload, timeout=timeout_sec)
        with lock:
            if response.status_code == 200:
                success_count += 1
                print(f"[✓] U{user_index} S{seq} - 200")
            elif response.status_code == 429:
                rate_limit_count += 1
                error_count += 1
                print(f"[⚠️] U{user_index} S{seq} - Rate Limit (429)")
            else:
                error_count += 1
                print(f"[✗] U{user_index} S{seq} - {response.status_code}")

    except requests.exceptions.Timeout:
        with lock:
            timeout_count += 1
            error_count += 1
            print(f"[⌛] U{user_index} S{seq} - Timeout")
    except Exception as e:
        with lock:
            error_count += 1
            print(f"[✗] U{user_index} S{seq} - {str(e)[:30]}")

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
    
    # Multi-user support
    multi = input("\n👥 Use multiple users? (y/n) - default: n: ").lower() == 'y'

    users = []
    rate_limit_ms = 300
    if multi:
        while True:
            try:
                num_users = int(input("Number of users to configure (e.g., 3): "))
                if num_users > 0:
                    break
                print("❌ Please enter a positive number")
            except ValueError:
                print("❌ Please enter a valid number")

        print("\nEnter per-user settings. Leave token empty to use the global API_TOKEN from .env.")
        for i in range(num_users):
            print(f"\n--- User {i+1} ---")
            token = input("API Token (Bearer ... ) [leave empty for global]: ").strip()
            instrument = input(f"Instrument ID [default {os.getenv('INSTRUMENT_IDENTIFICATION','IRO3PRIZ0001')}]: ").strip() or os.getenv('INSTRUMENT_IDENTIFICATION','IRO3PRIZ0001')
            while True:
                try:
                    qty = int(input(f"Quantity [default {os.getenv('QUANTITY','1289')}]: ") or os.getenv('QUANTITY','1289'))
                    break
                except ValueError:
                    print("❌ Please enter a valid integer quantity")
            while True:
                try:
                    price = int(input(f"Price [default {os.getenv('PRICE','29900')}]: ") or os.getenv('PRICE','29900'))
                    break
                except ValueError:
                    print("❌ Please enter a valid integer price")
            while True:
                try:
                    count = int(input("Number of requests for this user (e.g., 10): "))
                    if count >= 0:
                        break
                    print("❌ Please enter zero or a positive number")
                except ValueError:
                    print("❌ Please enter a valid number")

            users.append({
                'token': token,
                'instrument': instrument,
                'quantity': qty,
                'price': price,
                'count': count
            })

        while True:
            try:
                rate_limit_ms = int(input("Rate limit window in milliseconds (default 300): ") or "300")
                if rate_limit_ms > 0:
                    break
                print("❌ Please enter a positive number")
            except ValueError:
                print("❌ Please enter a valid number")

    confirm = input("\n✅ Proceed with these settings? (y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ Execution cancelled.")
        return None

    cfg = {
        'total': total,
        'rate': rate,
        'workers': workers,
        'timeout': timeout,
        'show_detail': show_detail,
        'save_result': save_result,
    }
    if multi:
        cfg['multi'] = True
        cfg['users'] = users
        cfg['rate_limit_ms'] = rate_limit_ms

    return cfg

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
    
    # Create RateLimiter (used for single-user mode)
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
        # Multi-user mode: orchestrate round-robin with a rate-limit window (ms)
        if config.get('multi') and config.get('users'):
            users = config['users']
            num_users = len(users)
            # per-user delta to stagger requests inside the rate-limit window
            rate_limit_ms = config.get('rate_limit_ms', 300)
            delta_ms = rate_limit_ms / max(1, num_users)

            # total expected requests (sum of per-user counts)
            total_expected = sum(u.get('count', 0) for u in users)
            sent_counter = 0

            # track per-user sent counts
            user_sent = [0] * num_users

            with concurrent.futures.ThreadPoolExecutor(max_workers=config['workers']) as executor:
                futures = []
                round_index = 0
                # continue until all users have sent their requested counts
                while sent_counter < total_expected:
                    for ui in range(num_users):
                        u = users[ui]
                        if user_sent[ui] >= u.get('count', 0):
                            # this user is done
                            continue
                        seq = user_sent[ui] + 1
                        futures.append(executor.submit(send_request_user, ui+1, seq, u, config['timeout']))
                        user_sent[ui] += 1
                        sent_counter += 1

                        # progress report
                        if total_expected > 0 and (sent_counter % max(1, total_expected // 10) == 0 or sent_counter % 100 == 0):
                            progress = sent_counter / total_expected * 100
                            elapsed = time.time() - start_time
                            print(f"⏱️ Progress: {sent_counter}/{total_expected} ({progress:.1f}%) - Time: {elapsed:.1f}s")

                        # stagger next user's request
                        time.sleep(delta_ms / 1000.0)

                # wait for all futures to complete
                concurrent.futures.wait(futures)

        else:
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
    if config.get('multi') and config.get('users'):
        total_sent = sum(u.get('count', 0) for u in config['users'])
    else:
        total_sent = config['total']

    success_rate = (success_count / total_sent) * 100 if total_sent > 0 else 0
    actual_rate = total_sent / elapsed_time if elapsed_time > 0 else 0
    
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
    
    # Save to file inside `results/` folder (ignored by git)
    if config['save_result']:
        results_dir = 'results'
        try:
            os.makedirs(results_dir, exist_ok=True)
        except Exception:
            pass

        filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(results_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("Request Sending Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Total requests: {total_sent}\n")
            f.write(f"Request rate: {config.get('rate', 0)} requests/second\n")
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
        print(f"\n💾 Results saved to '{filepath}'")

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