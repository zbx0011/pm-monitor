import json
import os
import time
import requests
from datetime import datetime, timedelta

CONFIG_FILE = 'alert_config.json'
STATE_FILE = 'alert_state.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading alert config: {e}")
        return None

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving alert state: {e}")

def check_and_alert(metal, pair_name, spread_pct, current_gfex, current_cme):
    config = load_config()
    if not config or not config.get('enabled', True):
        return

    thresholds = config.get('thresholds', {}).get(metal)
    if not thresholds:
        return

    min_val = thresholds.get('min', -999)
    max_val = thresholds.get('max', 999)
    webhook_url = config.get('webhook_url')

    if not webhook_url:
        return

    # Check violation
    violation = None
    if spread_pct > max_val:
        violation = f"高于上限 {max_val}%"
    elif spread_pct < min_val:
        violation = f"低于下限 {min_val}%"

    if violation:
        state = load_state()
        last_time_str = state.get(pair_name)
        
        should_alert = True
        if last_time_str:
            last_time = datetime.fromisoformat(last_time_str)
            cooldown = config.get('cooldown_minutes', 60)
            if datetime.now() - last_time < timedelta(minutes=cooldown):
                should_alert = False
                print(f"  [Alert] {pair_name} 触发 {violation}，但在冷却期内 (上次: {last_time_str})")

        if should_alert:
            message = (
                f"🚨 **价差警报 - {metal.title()}**\n"
                f"合约: {pair_name}\n"
                f"当前价差: {spread_pct:.2f}%\n"
                f"状态: {violation}\n"
                f"广期所: {current_gfex}\n"
                f"CME折算: {current_cme:.2f}\n"
                f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            try:
                # Send webhook (assuming standard JSON payload structure, adjusting for fwalert if needed)
                # fwalert usually accepts raw body or JSON
                payload = {"text": message} 
                response = requests.post(webhook_url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"  [Alert] ✅ 警报已发送: {pair_name} {spread_pct:.2f}%")
                    state[pair_name] = datetime.now().isoformat()
                    save_state(state)
                else:
                    print(f"  [Alert] ❌ 发送失败: {response.status_code} {response.text}")
            except Exception as e:
                print(f"  [Alert] ❌ 发送出错: {e}")
