"""
实时价格API服务
提供广期所/CME贵金属价格的HTTP接口
支持手动数据持久化存储
支持从数据库读取配对数据
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import akshare as ak
from datetime import datetime
import pandas as pd
import os
from database import get_all_pairs, get_pair_history
import subprocess
import platform
import threading
import time

# 手动数据存储文件
# 手动数据存储文件
MANUAL_DATA_FILE = 'manual_prices.json'

def run_data_sync():
    """执行数据同步（Windows运行脚本，Linux拉取代码）"""
    global last_refresh_time
    
    is_windows = platform.system() == 'Windows'
    python_cmd = 'python' if is_windows else 'python3'
    
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] 开始执行数据同步...")
    
    try:
        if is_windows:
            # Windows本地：运行数据采集脚本
            print("  [Windows] 运行数据采集脚本...")
            
            # 1. 更新铂金
            p1 = subprocess.run([python_cmd, 'generate_all_pairs.py'], capture_output=True, text=True)
            if p1.returncode != 0:
                print(f"铂金更新失败: {p1.stderr}")
                raise Exception(f"铂金更新失败: {p1.stderr}")
            
            # 2. 更新钯金
            p2 = subprocess.run([python_cmd, 'generate_palladium_pairs.py'], capture_output=True, text=True)
            if p2.returncode != 0:
                print(f"钯金更新失败: {p2.stderr}")
                raise Exception(f"钯金更新失败: {p2.stderr}")
            
            # 3. 独立存储CME数据（不依赖广期所交易时间）
            p3 = subprocess.run([python_cmd, 'fetch_2026_contracts.py'], capture_output=True, text=True)
            if p3.returncode != 0:
                print(f"CME独立存储失败: {p3.stderr}")
                # 不抛异常，CME存储失败不阻断整体流程
                
            message = '数据已更新（本地采集）'
        else:
            # Linux/VPS：从GitHub拉取最新数据
            print("  [Linux/VPS] 从GitHub拉取最新数据...")
            
            p = subprocess.run(['git', 'pull', 'origin', 'master'], capture_output=True, text=True)
            if p.returncode != 0:
                print(f"git pull 失败: {p.stderr}")
                raise Exception(f"git pull 失败: {p.stderr}")
            
            # print(f"  git pull 输出: {p.stdout}")
            message = '数据已同步（从GitHub拉取）'
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 同步成功: {message}")
        return True, message
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 同步失败: {e}")
        return False, str(e)

def auto_refresh_scheduler(interval=600):
    """后台定时刷新任务"""
    print(f"启动自动刷新调度器，间隔 {interval} 秒")
    while True:
        try:
            time.sleep(interval)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 触发定时自动更新...")
            run_data_sync()
        except Exception as e:
            print(f"定时更新出错: {e}")



class PriceAPIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/prices':
            self.send_price_data()
        elif self.path == '/api/saved-prices':
            self.send_saved_prices()
        elif self.path == '/api/platinum-pairs':
            self.send_pairs_data('platinum')
        elif self.path == '/api/palladium-pairs':
            self.send_pairs_data('palladium')
        elif self.path.startswith('/api/pair-history'):
            self.send_pair_history()
        elif self.path == '/api/alert-config':
            self.send_alert_config()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/save-prices':
            self.save_manual_prices()
        elif self.path == '/api/refresh-data':
            self.trigger_data_refresh()
        elif self.path == '/api/alert-config':
            self.save_alert_config()
        else:
            self.send_response(404)
            self.end_headers()

    def trigger_data_refresh(self):
        """触发后台数据更新"""
        try:
            success, message = run_data_sync()
            
            if success:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'message': message}).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': message}).encode('utf-8'))
            
        except Exception as e:
            print(f"更新过程出错: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def send_alert_config(self):
        """发送警报配置"""
        try:
            config_file = 'alert_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    'webhook_url': '',
                    'thresholds': {'platinum': {'min': 5, 'max': 25}, 'palladium': {'min': 5, 'max': 25}},
                    'cooldown_minutes': 60,
                    'enabled': False
                }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def save_alert_config(self):
        """保存警报配置"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            new_config = json.loads(post_data.decode('utf-8'))
            
            # 读取现有配置以保留 webhook_url（前端不应修改）
            config_file = 'alert_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                # 保留 webhook_url
                new_config['webhook_url'] = existing.get('webhook_url', '')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'message': '配置已保存'}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_price_data(self):
        """获取并返回实时价格数据"""
        try:
            data = get_all_prices()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def send_saved_prices(self):
        """返回保存的手动价格数据"""
        try:
            data = load_saved_prices()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def save_manual_prices(self):
        """保存手动输入的价格数据"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # 添加保存时间
            data['save_time'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            
            # 保存到文件
            with open(MANUAL_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 手动数据已保存")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'save_time': data['save_time']}).encode('utf-8'))
        except Exception as e:
            print(f"保存失败: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def send_pairs_data(self, metal):
        """返回配对数据（从数据库读取）"""
        try:
            pairs = get_all_pairs(metal)
            data = {
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pairs': pairs
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def send_pair_history(self):
        """返回指定配对的历史数据"""
        try:
            # 解析参数: /api/pair-history?metal=platinum&pair=2610-2601
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            metal = params.get('metal', ['platinum'])[0]
            pair_name = params.get('pair', [''])[0]
            
            history = get_pair_history(metal, pair_name)
            data = {
                'pair_name': pair_name,
                'metal': metal,
                'history': history
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))


def load_saved_prices():
    """加载保存的手动价格数据"""
    if os.path.exists(MANUAL_DATA_FILE):
        with open(MANUAL_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_gfex_prices():
    """获取广期所铂金钯金实时价格 (新浪实时行情)"""
    import requests
    result = {'pt': None, 'pd': None, 'pt_time': None, 'pd_time': None}
    
    # 使用新浪实时行情接口
    try:
        url = 'https://hq.sinajs.cn/list=nf_PT2610,nf_PD2606'
        headers = {'Referer': 'https://finance.sina.com.cn'}
        resp = requests.get(url, headers=headers, timeout=5)
        resp.encoding = 'gbk'
        
        for line in resp.text.strip().split('\n'):
            if 'PT2610' in line:
                match = line.split('"')[1] if '"' in line else ''
                if match:
                    parts = match.split(',')
                    # parts[8] = 最新价, parts[6] = 买一价, parts[7] = 卖一价
                    if len(parts) > 8:
                        price = float(parts[8]) if parts[8] and float(parts[8]) > 0 else float(parts[6]) if parts[6] and float(parts[6]) > 0 else None
                        if price:
                            result['pt'] = price
                            result['pt_time'] = datetime.now().strftime('%Y.%m.%d %H:%M')
            elif 'PD2606' in line:
                match = line.split('"')[1] if '"' in line else ''
                if match:
                    parts = match.split(',')
                    if len(parts) > 8:
                        price = float(parts[8]) if parts[8] and float(parts[8]) > 0 else float(parts[6]) if parts[6] and float(parts[6]) > 0 else None
                        if price:
                            result['pd'] = price
                            result['pd_time'] = datetime.now().strftime('%Y.%m.%d %H:%M')
    except Exception as e:
        print(f"广期所实时行情获取失败: {e}")
        # 降级到日K线数据
        try:
            pt = ak.futures_main_sina(symbol='PT0')
            if len(pt) > 0:
                result['pt'] = float(pt['收盘价'].iloc[-1])
                result['pt_time'] = pd.to_datetime(pt['日期'].iloc[-1]).strftime('%Y.%m.%d') + ' 15:00'
        except:
            pass
        try:
            pd_data = ak.futures_main_sina(symbol='PD0')
            if len(pd_data) > 0:
                result['pd'] = float(pd_data['收盘价'].iloc[-1])
                result['pd_time'] = pd.to_datetime(pd_data['日期'].iloc[-1]).strftime('%Y.%m.%d') + ' 15:00'
        except:
            pass
    
    return result


def get_cme_prices():
    """获取CME铂金钯金价格 (优先从本地数据库获取爬虫数据)"""
    result = {'pt': None, 'pd': None, 'pt_time': None, 'pd_time': None}
    
    # 1. 获取铂金 (从数据库读取最新的爬虫数据)
    try:
        conn = sqlite3.connect('precious_metals.db')
        cursor = conn.cursor()
        
        # 获取最新的 PLJ2026 或其他活跃合约
        # 这里取最近更新的一条数据的合约
        cursor.execute('''
            SELECT close, datetime, contract 
            FROM cme_platinum_contracts 
            ORDER BY datetime DESC, created_at DESC 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        
        if row:
            result['pt'] = float(row[0])
            result['pt_time'] = row[1]
            print(f"  [DB] 铂金({row[2]}): ${result['pt']} ({result['pt_time']})")
        
        conn.close()
    except Exception as e:
        print(f"  [DB] 数据库读取铂金失败: {e}")

    # 如果数据库没有数据，回退到 akshare (虽然可能不准)
    if result['pt'] is None:
        try:
            pt = ak.futures_foreign_hist(symbol='XPT')
            if len(pt) > 0:
                result['pt'] = float(pt['close'].iloc[-1])
                last_date = pd.to_datetime(pt['date'].iloc[-1])
                result['pt_time'] = last_date.strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            print(f"CME铂金(Akshare)获取失败: {e}")
    
    # 2. 获取钯金 (暂时仍用 Akshare，除非有数据库表)
    try:
        pd_data = ak.futures_foreign_hist(symbol='XPD')
        if len(pd_data) > 0:
            result['pd'] = float(pd_data['close'].iloc[-1])
            last_date = pd.to_datetime(pd_data['date'].iloc[-1])
            result['pd_time'] = last_date.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"CME钯金获取失败: {e}")
    
    return result


def get_exchange_rate():
    """获取美元人民币汇率"""
    try:
        df = ak.currency_boc_sina(symbol="美元")
        rate = float(df['中行折算价'].iloc[-1])
        return rate
    except Exception as e:
        print(f"汇率获取失败: {e}")
        return 7.03


def get_all_prices():
    """获取所有价格数据"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取价格数据...")
    
    gfex = get_gfex_prices()
    cme = get_cme_prices()
    rate = get_exchange_rate()
    
    print(f"  广期所: Pt={gfex['pt']} ({gfex['pt_time']}), Pd={gfex['pd']} ({gfex['pd_time']})")
    print(f"  CME: Pt=${cme['pt']} ({cme['pt_time']}), Pd=${cme['pd']} ({cme['pd_time']})")
    print(f"  汇率: {rate}")
    
    return {
        'update_time': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
        'exchange_rate': rate,
        'gfex': gfex,
        'cme': cme,
        'bybit': {'pt': cme['pt'], 'pd': cme['pd'], 'pt_time': cme['pt_time'], 'pd_time': cme['pd_time']}
    }


if __name__ == '__main__':
    print("=" * 50)
    print("测试获取价格...")
    print("=" * 50)
    data = get_all_prices()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 50)
    print("启动价格API服务器 http://localhost:8080")
    print("API端点:")
    print("  GET  /api/prices       - 获取实时价格")
    print("  GET  /api/saved-prices - 获取保存的手动价格")
    print("  POST /api/save-prices  - 保存手动输入的价格")
    print("=" * 50)
    print("=" * 50)
    
    # 启动自动刷新线程 (每1分钟=60秒)
    refresh_thread = threading.Thread(target=auto_refresh_scheduler, args=(60,), daemon=True)
    refresh_thread.start()
    
    server = HTTPServer(('', 8080), PriceAPIHandler)
    server.serve_forever()
