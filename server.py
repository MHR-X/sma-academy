from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import time

DB_FILE = "db.json"
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/register":
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                student = json.loads(post_data.decode('utf-8'))
                
                # قراءة الداتابيز بشكل آمن
                db = {"students": [], "certificates": []}
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, "r", encoding="utf-8") as f:
                        try:
                            db = json.load(f)
                        except json.JSONDecodeError:
                            pass # لو الملف تالف، هنبدأ من جديد
                
                # التأكد من وجود المفاتيح الأساسية
                if "students" not in db:
                    db["students"] = []
                if "certificates" not in db:
                    db["certificates"] = []

                # منع تكرار التسجيل بنفس الإيميل
                if any(s.get('email') == student.get('email') for s in db["students"]):
                    self.send_response(409)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "Email already exists"}).encode())
                    return

                # ✅ تعيين الحالة بشكل صريح وآمن
                student["status"] = "pending"
                student["id"] = student.get("id", int(time.time() * 1000))
                student["is_verified"] = False
                student["profile_image"] = ""
                
                db["students"].append(student)
                
                # حفظ البيانات فوراً
                with open(DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/db.json":
            try:
                if not os.path.exists(DB_FILE):
                    with open(DB_FILE, "w", encoding="utf-8") as f:
                        json.dump({"students": [], "certificates": []}, f)
                
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        elif self.path.startswith("/uploads/"):
            super().do_GET()
        else:
            super().do_GET()

print("🚀 Server running on http://localhost:8000")
HTTPServer(("", 8000), Handler).serve_forever()