import streamlit as st
import json
import os
from datetime import date
import uuid

st.set_page_config(page_title="SMA Admin System", page_icon="🏥", layout="wide")

DB_FILE = "db.json"
UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = {"students": [], "certificates": []}
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False)
        return initial_data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "certificates" not in data:
        data["certificates"] = []
    return data

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- نظام تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 نظام تحكم أكاديمية الطب الرياضي")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        
        if st.button("تسجيل الدخول", width='stretch', type="primary"):
            if email == "admin@sma.com" and password == "admin123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ بيانات خاطئة (جرب: admin@sma.com / admin123)")

# --- لوحة التحكم الرئيسية ---
def admin_dashboard():
    st.sidebar.title("👋 مرحباً دكتور")
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "📋 طلبات التسجيل", 
        "✅ الطلاب المقبولين وإدارة الحسابات", 
        "🎓 إصدار وإدارة الشهادات",
    ])
    
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    db = load_db()
    students = db.get("students", [])
    
    # 1️⃣ طلبات التسجيل
    if menu == "📋 طلبات التسجيل":
        st.header("📋 طلبات التسجيل المعلقة")
        pending = [s for s in students if s.get("status") == "pending"]
        
        if not pending:
            st.info("✨ لا توجد طلبات جديدة حالياً")
        else:
            for s in pending:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    full_name = f"{s['firstName']} {s['lastName']}"
                    c1.write(f"**الاسم:** {full_name}")
                    c2.write(f"**الإيميل:** {s['email']}")
                    
                    btn_col = c3.columns(3)
                    if btn_col[0].button("✅ قبول", key=f"acc_{s['id']}"):
                        idx = next(j for j, st_ in enumerate(students) if st_["id"] == s["id"])
                        students[idx]["status"] = "approved"
                        db["students"] = students
                        save_db(db)
                        st.success(f"تم قبول {full_name}")
                        st.rerun()
                        
                    if btn_col[1].button("❌ رفض", key=f"rej_{s['id']}"):
                        idx = next(j for j, st_ in enumerate(students) if st_["id"] == s["id"])
                        students[idx]["status"] = "rejected"
                        db["students"] = students
                        save_db(db)
                        st.warning(f"تم رفض {full_name}")
                        st.rerun()

                    if btn_col[2].button("🗑️ حذف", key=f"del_{s['id']}", type="secondary"):
                        students = [st_ for st_ in students if st_["id"] != s["id"]]
                        db["students"] = students
                        save_db(db)
                        st.error(f"تم حذف حساب {full_name} نهائياً!")
                        st.rerun()

    # 2️⃣ الطلاب المقبولين وإدارة الحسابات
    elif menu == "✅ الطلاب المقبولين وإدارة الحسابات":
        st.header("✅ إدارة الطلاب المقبولين")
        approved = [s for s in students if s.get("status") == "approved"]
        
        if not approved:
            st.info("لا يوجد طلاب مقبولين بعد")
        else:
            for s in approved:
                student_id = str(s['id'])
                
                # تهيئة حالة الصورة المؤقتة لهذا الطالب إذا لم تكن موجودة
                if f"temp_img_path_{student_id}" not in st.session_state:
                    st.session_state[f"temp_img_path_{student_id}"] = None

                with st.expander(f"👤 {s['firstName']} {s['lastName']} ({s['email']})", expanded=False):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader("صورة البروفايل")
                        
                        # ✅ عرض الصورة: إما المؤقتة المختارة حديثاً أو المحفوظة سابقاً
                        display_img = st.session_state[f"temp_img_path_{student_id}"] or s.get('profile_image')
                        if display_img and os.path.exists(display_img):
                            st.image(display_img, width=150)
                        else:
                            st.write("لا توجد صورة")
                            
                        uploaded_file = st.file_uploader("اختر صورة جديدة", type=["png", "jpg", "jpeg"], key=f"up_img_{student_id}")
                        
                        # عند اختيار ملف، نحفظه مؤقتاً في مجلد uploads ونخزن مساره في الجلسة
                        if uploaded_file is not None:
                            file_ext = uploaded_file.name.split('.')[-1]
                            temp_filename = f"temp_profile_{student_id}.{file_ext}"
                            temp_path = os.path.join(UPLOAD_DIR, temp_filename)
                            
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                                
                            st.session_state[f"temp_img_path_{student_id}"] = temp_path
                            st.caption("✅ تم اختيار الصورة. اضغط 'حفظ التغييرات' لتثبيتها نهائياً.")

                    with col2:
                        st.subheader("تعديل بيانات الحساب والتوثيق")
                        
                        new_fname = st.text_input("الاسم الأول", value=s.get("firstName", ""), key=f"fname_{student_id}")
                        new_lname = st.text_input("اسم العائلة", value=s.get("lastName", ""), key=f"lname_{student_id}")
                        new_email = st.text_input("البريد الإلكتروني", value=s.get("email", ""), key=f"email_{student_id}")
                        new_pass = st.text_input("كلمة المرور الجديدة", type="password", placeholder="اتركه فارغاً لعدم التغيير", key=f"pass_{student_id}")
                        
                        is_verified = s.get("is_verified", False)
                        new_verified = st.checkbox("✅ توثيق الحساب (علامة زرقاء)", value=is_verified, key=f"ver_{student_id}")
                        
                        # ✅ زر الحفظ الشامل الذي يثبت كل شيء دفعة واحدة
                        if st.button("💾 حفظ التغييرات", key=f"save_{student_id}", type="primary"):
                            idx = next(j for j, st_ in enumerate(students) if st_["id"] == s["id"])
                            
                            # 1. تحديث النصوص والحالة
                            students[idx]["firstName"] = new_fname
                            students[idx]["lastName"] = new_lname
                            students[idx]["email"] = new_email
                            students[idx]["is_verified"] = new_verified
                            
                            # 2. تحديث الباسورد فقط لو تم إدخال قيمة جديدة
                            if new_pass.strip():
                                students[idx]["password"] = new_pass
                            
                            # 3. تثبيت الصورة المؤقتة وتسميتها بالاسم النهائي
                            temp_key = f"temp_img_path_{student_id}"
                            if st.session_state[temp_key]:
                                final_filename = f"profile_{student_id}.jpg"
                                final_path = os.path.join(UPLOAD_DIR, final_filename)
                                
                                try:
                                    # نقل الملف من المسار المؤقت للمسار النهائي
                                    os.replace(st.session_state[temp_key], final_path)
                                    students[idx]["profile_image"] = final_path
                                except Exception as e:
                                    st.error(f"حدث خطأ أثناء حفظ الصورة: {e}")
                                finally:
                                    # تنظيف المسار المؤقت من الجلسة
                                    st.session_state[temp_key] = None
                            
                            # حفظ البيانات في ملف JSON وإعادة تحميل الصفحة لعرض التعديلات
                            db["students"] = students
                            save_db(db)
                            st.success("✅ تم حفظ جميع التغييرات والتوثيق والصورة بنجاح!")
                            st.rerun()
                            
                        st.divider()
                        
                        # ✅ زر حذف الحساب النهائي (الوحيد المتبقي)
                        if st.button("🗑️ حذف هذا الحساب نهائياً", type="primary", key=f"del_stud_{student_id}"):
                            # مسح بيانات الطالب من القائمة
                            students = [st_ for st_ in students if st_["id"] != s["id"]]
                            # مسح شهاداته المرتبطة
                            db["certificates"] = [c for c in db["certificates"] if c["studentEmail"] != s["email"]]
                            db["students"] = students
                            save_db(db)
                            
                            st.error(f"🚫 تم حذف حساب {s['firstName']} {s['lastName']} نهائياً! سيتم توجيهه إلى الصفحة الرئيسية.")
                            st.rerun()

    # 3️⃣ إصدار وإدارة الشهادات
    elif menu == "🎓 إصدار وإدارة الشهادات":
        st.header("🎓 إدارة الشهادات الإلكترونية")
        tab1, tab2 = st.tabs(["إصدار شهادة جديدة", "عرض وحذف الشهادات"])
        
        with tab1:
            st.subheader("إصدار شهادة لطالب مقبول")
            approved_students = [s for s in students if s.get("status") == "approved"]
            
            if not approved_students:
                st.warning("لا يوجد طلاب مقبولين لإصدار شهادات لهم")
            else:
                with st.form("cert_issue_form"):
                    selected_student = st.selectbox("اختر الطالب", [f"{s['firstName']} {s['lastName']} ({s['email']})" for s in approved_students])
                    course_name = st.text_input("اسم الكورس/الشهادة (يدوي)", placeholder="مثال: دبلوم التأهيل الرياضي المتقدم")
                    
                    auto_cert_id = str(uuid.uuid4()).split('-')[0].upper()
                    cert_id = st.text_input("رقم الشهادة (تلقائي)", value=auto_cert_id, disabled=True)
                    
                    issue_date = st.date_input("تاريخ الإصدار", value=date.today())
                    cert_file = st.file_uploader("رفع ملف الشهادة (PDF أو صورة)", type=["pdf", "png", "jpg", "jpeg"])
                    
                    submitted = st.form_submit_button("💾 حفظ وإصدار الشهادة", width='stretch')
                    
                    if submitted and cert_file and course_name.strip():
                        file_ext = cert_file.name.split('.')[-1]
                        student_email = selected_student.split('(')[-1][:-1]
                        file_name = f"cert_{student_email}_{uuid.uuid4().hex}.{file_ext}"
                        file_path = os.path.join(UPLOAD_DIR, file_name)
                        
                        with open(file_path, "wb") as f:
                            f.write(cert_file.getbuffer())
                        
                        new_cert = {
                            "id": str(uuid.uuid4()),
                            "studentEmail": student_email,
                            "courseName": course_name,
                            "certId": auto_cert_id,
                            "issueDate": str(issue_date),
                            "filePath": file_path
                        }
                        db.setdefault("certificates", []).append(new_cert)
                        save_db(db)
                        st.success(f"✅ تم إصدار الشهادة بنجاح للطالب المختار!")
                        st.balloons()

        with tab2:
            st.subheader("قائمة جميع الشهادات الصادرة")
            all_certs = db.get("certificates", [])
            
            if not all_certs:
                st.info("لا توجد شهادات صادرة حتى الآن")
            else:
                all_certs.reverse()
                
                for cert in all_certs:
                    student = next((s for s in students if s["email"] == cert["studentEmail"]), None)
                    student_name = f"{student['firstName']} {student['lastName']}" if student else "طالب محذوف"
                    
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                        c1.write(f"**{student_name}**")
                        c2.write(f" {cert['courseName']}")
                        c3.write(f"🆔 {cert['certId']}")
                        
                        if c4.button("🗑️ حذف", key=f"del_cert_{cert['id']}", type="secondary"):
                            db["certificates"] = [c for c in db["certificates"] if c["id"] != cert["id"]]
                            save_db(db)
                            st.success("تم حذف الشهادة!")
                            st.rerun()

if not st.session_state.logged_in:
    login()
else:
    admin_dashboard()