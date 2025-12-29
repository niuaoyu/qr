import os
import time
import json
import sqlite3
import threading
from data.sign_in import sign_in
from data.sqlite.db_utils import make_fingerprint, check_if_exists, save_alpha

def prepend_to_file(filepath, content, lock):
    """Thread-safe prepend to file."""
    with lock:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            old_content = ""
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    old_content = f.read()
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content + "\n" + old_content)
            print(f"📝 Result prepended to: {filepath}")
        except Exception as e:
            print(f"❌ Failed to write to file: {e}")

def run_simulation_task(alpha_payload, config):
    """
    Executes the simulation task for a single alpha with DB check and storage.
    """
    user_choice = config['user_choice']
    db_path = config['db_path']
    txt_result_path = config['txt_result_path']
    author_name = config['author_name']
    semaphore = config['semaphore']
    file_lock = config['file_lock']
    
    expression_code = alpha_payload.get('regular', 'N/A')
    settings = alpha_payload.get('settings', {})
    
    # 1. Database Check
    try:
        conn = sqlite3.connect(db_path)
        # Performance tuning for SQLite
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception as e:
        print(f"❌ DB Connection failed: {e}")
        return

    try:
        fingerprint = make_fingerprint(expression_code, settings)
        if check_if_exists(conn, fingerprint):
            print(f"⏭️ Alpha already exists in DB, skipping: {expression_code[:30]}...")
            return
    except Exception as e:
        print(f"❌ DB Check failed: {e}")
        return
    finally:
        # Connection kept open for saving later
        pass

    # 2. Simulation
    sess = sign_in(user_choice)
    if not sess:
        print(f"❌ Login failed for {expression_code[:100]}...")
        conn.close()
        return

    print(f"▶️ Processing Alpha: {expression_code[:100]}...")

    try:
        with semaphore:
            # Submit
            sim_resp = sess.post('https://api.worldquantbrain.com/simulations', json=alpha_payload)
            if sim_resp.status_code == 401:
                sess = sign_in(user_choice)
                sim_resp = sess.post('https://api.worldquantbrain.com/simulations', json=alpha_payload)

            sim_progress_url = sim_resp.headers.get('Location')
            if not sim_progress_url:
                print(f"❌ Submission failed: {sim_resp.text}")
                conn.close()
                return

            # Poll
            alpha_id = None
            while True:
                sim_progress_resp = sess.get(sim_progress_url)
                if sim_progress_resp.status_code == 401:
                    sess = sign_in(user_choice)
                    continue
                
                retry_after = float(sim_progress_resp.headers.get('Retry-After', '0'))
                if retry_after == 0:
                    sim_result = sim_progress_resp.json()
                    if 'alpha' not in sim_result:
                        print(f"❌ Simulation failed: {sim_result}")
                        conn.close()
                        return
                    alpha_id = sim_result['alpha']
                    break
                time.sleep(retry_after)

            # Get Details
            alpha_detail_resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
            if alpha_detail_resp.status_code == 401:
                sess = sign_in(user_choice)
                alpha_detail_resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
            
            alpha_detail = alpha_detail_resp.json()
            
            # 3. Save to DB
            alpha_detail['author'] = author_name
            if save_alpha(conn, alpha_detail, fingerprint):
                conn.commit()
                print(f"✅ Saved to DB: {alpha_id}")
            else:
                print(f"❌ Failed to save to DB: {alpha_id}")

            # 4. Write to Text File (if good)
            grade = alpha_detail.get('grade')
            if grade not in ['INFERIOR', 'UNKNOWN', None]:
                stats = alpha_detail.get('is', {})
                result_entry = (
                    f"{'-'*50}\n"
                    f"Alpha ID: {alpha_id}, author: {author_name}\n"
                    f"Expression: {expression_code}\n"
                    f"Sharpe: {stats.get('sharpe')}\n"
                    f"Turnover: {stats.get('turnover')}\n"
                    f"Fitness: {stats.get('fitness')}\n"
                    f"Grade: {grade}\n"
                    f"{'-'*50}"
                )
                prepend_to_file(txt_result_path, result_entry, file_lock)

    except Exception as e:
        print(f"❌ Error processing {expression_code[:100]}: {e}")
    finally:
        conn.close()
