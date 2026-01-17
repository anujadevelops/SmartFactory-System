import os
import random
import json
import time
from datetime import datetime
from threading import Lock
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURATION ---
current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=current_dir, static_folder=current_dir)
app.config['SECRET_KEY'] = 'hackathon_super_secret'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
thread = None
thread_lock = Lock()

DATA_FILE = os.path.join(current_dir, 'master_manufacturing_data.json')

# --- GLOBAL FACTORY STATE ---
simulation_state = {
    "target_rpm": 1200,
    "current_rpm": 1200,
    "temp": 65.0,
    "temp_offset": 0.0,
    "health": 100.0,
    "efficiency": 95.0,
    "yield_count": 1450,
    "status": "RUNNING",
    "is_locked": False, 
    "active_orders": [],   
    "client_orders": [],   
    "reports": [], 
    "notifications": []
}

# --- HELPERS ---
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, 'r') as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=2)

def add_report(content, type="INFO", author="System AI"):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": type,
        "content": content,
        "author": author
    }
    simulation_state['reports'].insert(0, entry)
    if len(simulation_state['reports']) > 50: simulation_state['reports'].pop()
    
    full_data = load_data()
    if 'production_hub' in full_data:
        full_data['production_hub']['reports'] = simulation_state['reports']
        save_data(full_data)
    return entry

# --- SECURITY DECORATOR ---
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                return "Access Denied: You do not have permission to view this page.", 403
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Load initial state
initial_data = load_data()
if 'production_hub' in initial_data:
    simulation_state['active_orders'] = initial_data['production_hub'].get('orders', [])
    simulation_state['reports'] = initial_data['production_hub'].get('reports', [])

# --- BACKGROUND ENGINE ---
def background_thread():
    last_prediction_yield = 0
    while True:
        socketio.sleep(1) 
        
        if simulation_state["is_locked"]:
            emit_telemetry(locked=True)
            continue 

        if simulation_state["status"] == "RUNNING":
            current_yield = simulation_state["yield_count"]
            if current_yield - last_prediction_yield >= 50:
                last_prediction_yield = current_yield
                
                # FIXED: AI Prediction now suggests diverse materials
                materials = ["Steel Sheets", "Copper Wire", "Lubricant", "Microchips"]
                suggested = random.choice(materials)
                
                notif_payload = {
                    "from": "CORTEX_AI",
                    "type": "PREDICTION",
                    "message": f"DEMAND SURGE PREDICTED. Suggested: Restock {suggested}. Action: Order Now.",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                simulation_state['notifications'].append(notif_payload)
                socketio.emit('new_notification', notif_payload) # Emits to Operator

        if simulation_state["status"] == "STOPPED":
            simulation_state["target_rpm"] = 0
            if simulation_state["current_rpm"] > 0:
                decay = max(10, simulation_state["current_rpm"] * 0.15) 
                simulation_state["current_rpm"] -= decay
                if simulation_state["current_rpm"] < 1: simulation_state["current_rpm"] = 0
            
            if simulation_state["temp"] > 0:
                simulation_state["temp"] -= 2.0
                if simulation_state["temp"] < 0: simulation_state["temp"] = 0
            simulation_state["efficiency"] = 0
        else:
            target = simulation_state["target_rpm"]
            current = simulation_state["current_rpm"]
            if current < target: simulation_state["current_rpm"] += random.randint(20, 50)
            elif current > target: simulation_state["current_rpm"] -= random.randint(20, 50)
            simulation_state["current_rpm"] = max(0, simulation_state["current_rpm"] + random.randint(-5, 5))
            
            if simulation_state["current_rpm"] > 100:
                deviation = abs(simulation_state["current_rpm"] - 1200)
                base_temp = 60 + (deviation / 30) + simulation_state["temp_offset"]
                simulation_state["temp"] = round(base_temp + random.uniform(-0.5, 0.5), 1)
            else:
                if simulation_state["temp"] > 20: simulation_state["temp"] -= 0.5

            eff_loss = 0
            if abs(simulation_state["current_rpm"] - 1200) > 100: eff_loss += 5
            if simulation_state["temp"] > 80: eff_loss += 10
            simulation_state["efficiency"] = max(50, 100 - eff_loss - (100 - simulation_state["health"]) * 0.2)

            if simulation_state["efficiency"] > 80:
                simulation_state["yield_count"] += random.randint(1, 3)

            stress = 0
            if simulation_state["current_rpm"] > 1800: stress += 0.2
            if simulation_state["temp"] > 85: stress += 0.3
            if simulation_state["current_rpm"] > 0: stress += 0.05 
            simulation_state["health"] -= stress
            if simulation_state["health"] < 0: simulation_state["health"] = 0

            if simulation_state["health"] < 80:
                simulation_state["health"] = 100.0
                simulation_state["temp_offset"] = 0.0 
                simulation_state["target_rpm"] = 1200 
                msg = "CRITICAL HEALTH DETECTED. AI Auto-Repair Executed."
                add_report(msg, "MAINTENANCE")
                socketio.emit('maintenance_alert', {
                    "message": "AI AUTO-REPAIR COMPLETED. System Stabilized.",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

        updated_orders = False
        if simulation_state["status"] == "RUNNING":
            for order in simulation_state['active_orders']:
                if order.get('status') == 'In Progress' and not order.get('paused', False):
                    progress_speed = (simulation_state["current_rpm"] / 1200) * 8 
                    if simulation_state["temp"] > 90: progress_speed *= 0.5
                    current_prog = order.get('progress', 0)
                    if current_prog < 100:
                        order['progress'] = min(100, int(current_prog + progress_speed))
                        updated_orders = True
        
        if updated_orders:
            socketio.emit('order_update', simulation_state['active_orders'])

        emit_telemetry(locked=False)

def emit_telemetry(locked):
    data = load_data()
    inventory = data.get('inventory', [])
    financials = data.get('financials', {'revenue':0, 'cost':0}) 

    socketio.emit('system_update', {
        'rpm': int(simulation_state["current_rpm"]),
        'temp': round(simulation_state["temp"], 1),
        'health': int(simulation_state["health"]),
        'efficiency': int(simulation_state["efficiency"]),
        'yield': simulation_state["yield_count"],
        'status': simulation_state["status"],
        'locked': locked,
        'client_orders': simulation_state['client_orders'], 
        'inventory': inventory,
        'financials': financials 
    })

# --- AUTH ROUTES ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    full_data = load_data()
    users = full_data.get('users', [])
    if any(u['email'] == email for u in users):
        return jsonify({"status": "error", "message": "User already exists"}), 400
    hashed_pw = generate_password_hash(password)
    new_user = {"email": email, "password": hashed_pw, "role": role}
    if 'users' not in full_data: full_data['users'] = []
    full_data['users'].append(new_user)
    save_data(full_data)
    return jsonify({"status": "success", "message": "Registration successful"})

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_data = load_data()
    users = full_data.get('users', [])
    user = next((u for u in users if u['email'] == email), None)
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['email']
        session['role'] = user['role']
        return jsonify({"status": "success", "role": user['role']})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROUTES ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/login.html')
def login(): return render_template('login.html')

@app.route('/operator')
@login_required(role='Operator')
def operator(): return render_template('dashboard.html') 

@app.route('/manager-dashboard')
@login_required(role='Manager')
def manager(): 
    data = load_data()
    return render_template('manager.html', production=data.get('production_hub', {}), logistics=data.get('logistics_and_sustainability', {}))

@app.route('/analyst')
@login_required(role='Analyst')
def analyst(): return render_template('analyst.html')

# --- API ENDPOINTS ---
@app.route('/api/system/lock', methods=['POST'])
def system_lock():
    data = request.json
    simulation_state['is_locked'] = data.get('locked', False)
    return jsonify({"status": "success", "locked": simulation_state['is_locked']})

@app.route('/api/create_order', methods=['POST'])
def create_order():
    data = request.json
    new_id = f"#ORD-{random.randint(1000, 9999)}"
    product = data.get('product', "Hydraulic Valve")
    qty = int(data.get('quantity', 100))
    deadline = data.get('deadline') # Receive deadline
    estimated_cost = qty * 15 
    full_data = load_data()
    if 'financials' not in full_data: full_data['financials'] = {'revenue': 0, 'cost': 0}
    full_data['financials']['cost'] += estimated_cost
    save_data(full_data)
    p_label, p_color = calculate_ai_priority(deadline)
    new_order = { 
"id": new_id, 
        "product": product, 
        "quantity": qty,
        "deadline": deadline, # Default if not provided
"priority": p_label,       # Correctly tagged
        "priority_color": p_color, # Correctly colored
        "progress": 0, 
        "status": "Pending", 
        "paused": False,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")                }
    simulation_state['active_orders'].append(new_order)
    full_data['production_hub']['orders'] = simulation_state['active_orders']
    save_data(full_data)
    notif_payload = {
        "from": "MANAGER",
        "type": "ORDER",
        "message": f"New Work Order Received: {new_id} ({product} x{qty})",
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    simulation_state['notifications'].append(notif_payload) 
    socketio.emit('new_notification', notif_payload)        
    add_report(f"PRODUCTION ORDER: {new_id} ({product} x{qty}) created. Cost: ${estimated_cost}", "INFO")
    socketio.emit('order_update', simulation_state['active_orders'])
    return jsonify({"status": "success"})

# Add this helper to app.py
def calculate_ai_priority(deadline_str):
    """Centralized Priority Engine for 2026 System Time"""
    try:
        # System time is Jan 17, 2026
        today = datetime.strptime("2026-01-17", "%Y-%m-%d") 
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
        diff_days = (deadline - today).days

        # Priority Thresholds
        if diff_days <= 2: 
            return ("CRITICAL", "#ff4757") # Bright Red
        if diff_days <= 5: 
            return ("HIGH", "#ffb700")     # Yellow
        if diff_days <= 10: 
            return ("MEDIUM", "#00f3ff")   # Cyan
        return ("LOW", "#94a3b8")          # Gray
    except:
        return ("NORMAL", "#94a3b8")

# Update your shop_order route to include this priority
@app.route('/api/shop/order', methods=['POST'])
# --- Updated shop_order route in app.py ---
@app.route('/api/shop/order', methods=['POST'])
def shop_order():
    data = request.json
    deadline = data.get('deadline', '2026-01-25')
    p_label, p_color = calculate_ai_priority(deadline)
    
    # 1. GENERATE THE ID FIRST
    new_id = f"SLS-{random.randint(10000, 99999)}"
    
    # 2. NOW CREATE THE ORDER ENTRY
    order_entry = {
        "id": new_id,
        "customer": data.get('customer_name'), # This matches your index.html update
        "product": data.get('product'),
        "qty": int(data.get('quantity')),
        "amt": int(data.get('total')),
        "deadline": deadline,
        "priority": p_label,
        "priority_color": p_color,
        "status": "New",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    simulation_state['client_orders'].insert(0, order_entry)
    socketio.emit('new_client_order', order_entry)
    return jsonify({"status": "success", "order_id": new_id})
    simulation_state['client_orders'].insert(0, order_entry)
    socketio.emit('new_client_order', order_entry)
    return jsonify({"status": "success", "order_id": new_id})
@app.route('/api/order/control', methods=['POST'])
def order_control():
    data = request.json
    order_id = data.get('id')
    action = data.get('action') 
    target = next((o for o in simulation_state['active_orders'] if o['id'] == order_id), None)
    if not target: return jsonify({"status": "error"})
    if action == 'delete':
        simulation_state['active_orders'].remove(target)
        add_report(f"Order {order_id} removed.", "WARN")
    elif action == 'pause':
        target['paused'] = True
        add_report(f"DEFECT FLAG: {order_id} Paused.", "QA")
    elif action == 'resume':
        target['paused'] = False
        add_report(f"RESUMED: {order_id}.", "INFO")
    full_data = load_data()
    full_data['production_hub']['orders'] = simulation_state['active_orders']
    save_data(full_data)
    socketio.emit('order_update', simulation_state['active_orders'])
    return jsonify({"status": "success"})

@app.route('/api/workflow/move', methods=['POST'])
def move_workflow():
    data = request.json
    order_id = data.get('id')
    new_status = data.get('status')
    
    target = next((o for o in simulation_state['active_orders'] if o['id'] == order_id), None)
    if not target: return jsonify({"status": "error"})
    
    target['status'] = new_status
    
    if new_status == "Completed":
        revenue_gain = target['quantity'] * 50
        full_data = load_data()
        if 'financials' not in full_data: full_data['financials'] = {'revenue': 0, 'cost': 0}
        full_data['financials']['revenue'] += revenue_gain
        
        # FIXED: Inventory & Yield reflect in Manager when Operator completes task
        raw_material = next((i for i in full_data.get('inventory', []) if i['name'] == 'Steel Sheets'), None)
        if raw_material:
            raw_material['stock'] = max(0, raw_material['stock'] - (target['quantity'] // 2))
        
        simulation_state["yield_count"] += target['quantity'] # Increase total yield count
        save_data(full_data)
        add_report(f"OPERATOR: Completed {order_id}. Revenue generated: ${revenue_gain}", "SUCCESS")

    full_data = load_data()
    full_data['production_hub']['orders'] = simulation_state['active_orders']
    save_data(full_data)

    socketio.emit('order_update', simulation_state['active_orders'])
    emit_telemetry(locked=simulation_state['is_locked']) # Force sync with Manager UI
    return jsonify({"status": "success"})

@app.route('/api/get_notifications', methods=['GET'])
def get_notifs(): return jsonify(simulation_state['notifications'])

@app.route('/api/send_report', methods=['POST'])
def receive_report():
    data = request.json or {}
    content = data.get('content', "Manual Shift Report: Systems Nominal.")
    entry = add_report(content, "OPERATOR", "Operator Node")
    socketio.emit('report_update', simulation_state['reports'])
    socketio.emit('new_notification', {"from": "OPERATOR", "message": "New Shift Report Filed", "type": "REPORT"})
    return jsonify({"status": "success", "message": "Report filed."})

@app.route('/api/reports', methods=['GET'])
def get_reports(): return jsonify(simulation_state['reports'])

@app.route('/api/analyst/history', methods=['GET'])
def get_analyst_history():
    base_yield = simulation_state["yield_count"]
    return jsonify({
        "production": [base_yield - (x*100) for x in range(7)],
        "inventory": [4500, 4600, 4200, 4800, 4700, 4900, 5000],
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    })

@app.route('/api/analytics/snapshot', methods=['GET'])
def get_analytics_snapshot():
    data = load_data()
    return jsonify({
        "orders": simulation_state['active_orders'],
        "inventory": data.get('logistics_and_sustainability', {}).get('inventory', []),
        "reports": simulation_state['reports']
    })

@app.route('/api/system/reset', methods=['POST'])
def reset_system():
    global simulation_state
    existing_users = load_data().get('users', []) 
    simulation_state["active_orders"] = []
    simulation_state["client_orders"] = []
    simulation_state["reports"] = []
    simulation_state["yield_count"] = 0
    simulation_state["efficiency"] = 100
    clean_data = {
        "production_hub": { "orders": [], "efficiency_history": [], "yield_total": 0, "reports": [] },
        "inventory": [
            {"name": "Steel Sheets", "stock": 2000, "max": 2000, "burnRate": 15},
            {"name": "Copper Wire", "stock": 2000, "max": 2000, "burnRate": 5},
            {"name": "Lubricant", "stock": 1000, "max": 1000, "burnRate": 8},
            {"name": "Microchips", "stock": 1000, "max": 1000, "burnRate": 2},
            {"name": "Hydraulic Valve", "stock": 500, "max": 1000, "burnRate": 10},
            {"name": "Piston Ring", "stock": 800, "max": 1500, "burnRate": 5},
            {"name": "Neural Chip", "stock": 200, "max": 500, "burnRate": 1},
            {"name": "Circuit Board", "stock": 600, "max": 1200, "burnRate": 3},
            {"name": "Sensor Unit", "stock": 400, "max": 800, "burnRate": 2},
            {"name": "Nano-Fiber Chassis", "stock": 150, "max": 300, "burnRate": 1}
        ],
        "logs": [],
        "financials": { "revenue": 0, "cost": 0 },
        "users": existing_users 
    }
    try:
        with open(DATA_FILE, 'w') as f: json.dump(clean_data, f, indent=4)
        socketio.emit('order_update', [])
        socketio.emit('report_update', [])
        return jsonify({"status": "success", "message": "Factory System Reset Complete"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('ai_command')
def handle_ai(data):
    cmd = data.get('cmd', '').lower()
    if data.get('notification_to_operator'):
        msg = data.get('message', 'Alert from Manager')
        notif = {
            "from": "MANAGER",
            "message": msg,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        simulation_state['notifications'].append(notif)
        socketio.emit('new_notification', notif) # Emits to Operator HUD
        return
    if simulation_state['is_locked'] and ("speed" in cmd or "temp" in cmd or "start" in cmd or "stop" in cmd):
        emit('ai_ack', {'response': "LOCKED: Controls Disabled.", 'cmd': cmd})
        return
    if "start" in cmd: simulation_state["status"] = "RUNNING"
    if "stop" in cmd: simulation_state["status"] = "STOPPED"
    if "repair" in cmd or "stabilize" in cmd: 
        simulation_state["health"] = 100
        simulation_state["temp_offset"] = 0
    if "increase speed" in cmd: simulation_state["target_rpm"] += 100
    if "decrease speed" in cmd: simulation_state["target_rpm"] -= 100
    if "increase temp" in cmd: simulation_state["temp_offset"] += 5
    if "decrease temp" in cmd: simulation_state["temp_offset"] -= 5
    response = f"Executed: {cmd}"
    emit('ai_ack', {'response': response, 'cmd': cmd})

@socketio.on('connect')
def connect():
    global thread
    with thread_lock:
        if thread is None: thread = socketio.start_background_task(background_thread)
    data = load_data()
    inventory = data.get('inventory', [])
    emit('system_update', {
        'rpm': int(simulation_state["current_rpm"]),
        'temp': simulation_state["temp"],
        'status': simulation_state["status"],
        'health': simulation_state['health'],
        'efficiency': simulation_state['efficiency'],
        'yield': simulation_state['yield_count'],
        'locked': simulation_state["is_locked"],
        'client_orders': simulation_state['client_orders'],
        'inventory': inventory
    })
    emit('order_update', simulation_state['active_orders'])
    emit('report_update', simulation_state['reports'])

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(current_dir, filename)

if __name__ == '__main__':
    print("SYSTEM ONLINE: http://127.0.0.1:5000/login.html")
    socketio.run(app, debug=True, port=5000)