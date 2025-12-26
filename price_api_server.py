"""
实时价格API服务
提供广期所/CME贵金属价格的HTTP接口
支持手动数据持久化存储
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import akshare as ak
from datetime import datetime
import pandas as pd
import os

# 手动数据存储文件
MANUAL_DATA_FILE = 'manual_prices.json'


class PriceAPIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/prices':
            self.send_price_data()
        elif self.path == '/api/saved-prices':
            self.send_saved_prices()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/save-prices':
            self.save_manual_prices()
        else:
            self.send_response(404)
            self.end_headers()
    
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


def load_saved_prices():
    """加载保存的手动价格数据"""
    if os.path.exists(MANUAL_DATA_FILE):
        with open(MANUAL_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_gfex_prices():
    """获取广期所铂金钯金价格 (新浪期货)"""
    result = {'pt': None, 'pd': None, 'pt_time': None, 'pd_time': None}
    
    try:
        pt = ak.futures_main_sina(symbol='PT0')
        if len(pt) > 0:
            result['pt'] = float(pt['收盘价'].iloc[-1])
            last_date = pd.to_datetime(pt['日期'].iloc[-1])
            result['pt_time'] = last_date.strftime('%Y.%m.%d') + ' 15:00'
    except Exception as e:
        print(f"广期所铂金获取失败: {e}")
    
    try:
        pd_data = ak.futures_main_sina(symbol='PD0')
        if len(pd_data) > 0:
            result['pd'] = float(pd_data['收盘价'].iloc[-1])
            last_date = pd.to_datetime(pd_data['日期'].iloc[-1])
            result['pd_time'] = last_date.strftime('%Y.%m.%d') + ' 15:00'
    except Exception as e:
        print(f"广期所钯金获取失败: {e}")
    
    return result


def get_cme_prices():
    """获取CME铂金钯金期货价格 (新浪外盘)"""
    result = {'pt': None, 'pd': None, 'pt_time': None, 'pd_time': None}
    
    try:
        pt = ak.futures_foreign_hist(symbol='XPT')
        if len(pt) > 0:
            result['pt'] = float(pt['close'].iloc[-1])
            last_date = pd.to_datetime(pt['date'].iloc[-1])
            result['pt_time'] = last_date.strftime('%Y.%m.%d') + ' 06:00'
    except Exception as e:
        print(f"CME铂金获取失败: {e}")
    
    try:
        pd_data = ak.futures_foreign_hist(symbol='XPD')
        if len(pd_data) > 0:
            result['pd'] = float(pd_data['close'].iloc[-1])
            last_date = pd.to_datetime(pd_data['date'].iloc[-1])
            result['pd_time'] = last_date.strftime('%Y.%m.%d') + ' 06:00'
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
    server = HTTPServer(('', 8080), PriceAPIHandler)
    server.serve_forever()
