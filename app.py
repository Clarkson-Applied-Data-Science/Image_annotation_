from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
from flask_session import Session
from datetime import timedelta
import datetime
import time
import os
from werkzeug.utils import secure_filename

from user import user
from images import images
from label import label


UPLOAD_FOLDER = "static/uploads"

# ---------------------------------------------------------
#   APP SETUP
# ---------------------------------------------------------
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config["SECRET_KEY"] = "sdfvbgfdjeR5y5r"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=5)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

Session(app)


# ---------------------------------------------------------
#   SESSION + HOME
# ---------------------------------------------------------
@app.route("/")
def home():
    return redirect("/login")


@app.context_processor
def inject_user():
    return dict(me=session.get("user"))


# ---------------------------------------------------------
#   LOGIN
# ---------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    un = request.form.get("name")
    pw = request.form.get("password")

    if un and pw:
        u = user()
        if u.tryLogin(un, pw):
            session["user"] = u.data[0]
            session["active"] = time.time()
            return redirect("/main")
        else:
            return render_template("login.html", msg="Incorrect username or password.")

    return render_template("login.html", msg="Welcome Back")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html", msg="You have logged out.")


# ---------------------------------------------------------
#   USERS CRUD
# ---------------------------------------------------------
@app.route("/users/manage", methods=["GET", "POST"])
def manage_user():
    if not checkSession(): return redirect("/login")

    o = user()
    action = request.args.get("action")
    pkval = request.args.get("pkval")

    # DELETE
    if action == "delete":
        o.deleteById(pkval)
        return render_template("ok_dialog.html", msg=f"Record ID {pkval} deleted.")

    # INSERT
    if action == "insert":
        d = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "role": request.form.get("role"),
            "password": request.form.get("password"),
            "password2": request.form.get("password2")
        }
        o.set(d)
        if o.verify_new():
            o.insert()
            return render_template("ok_dialog.html", msg="User added.")
        else:
            return render_template("users/add.html", obj=o)

    # UPDATE
    if action == "update":
        o.getById(pkval)
        o.data[0]["name"] = request.form.get("name")
        o.data[0]["email"] = request.form.get("email")
        o.data[0]["role"] = request.form.get("role")
        o.data[0]["password"] = request.form.get("password")
        o.data[0]["password2"] = request.form.get("password2")

        if o.verify_update():
            o.update()
            return render_template("ok_dialog.html", msg="User updated.")
        else:
            return render_template("users/manage.html", obj=o)

    # LIST
    if pkval is None:
        o.getAll()
        return render_template("users/list.html", obj=o)

    # ADD NEW
    if pkval == "new":
        o.createBlank()
        return render_template("users/add.html", obj=o)

    # EDIT
    o.getById(pkval)
    return render_template("users/manage.html", obj=o)


# ---------------------------------------------------------
#   MAIN PAGE
# ---------------------------------------------------------
@app.route("/main")
def main():
    if not checkSession(): return redirect("/login")
    return render_template("main.html")


# ---------------------------------------------------------
#   STATIC ROUTE
# ---------------------------------------------------------
@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


# ---------------------------------------------------------
#   IMAGE UPLOAD
# ---------------------------------------------------------
# ---------------------------------------------------------
#   MULTIPLE IMAGE UPLOAD
# ---------------------------------------------------------
# ---------------------------------------------------------
#   MULTIPLE IMAGE UPLOAD (NO LABELS HERE)
# ---------------------------------------------------------
@app.route("/images/upload", methods=["GET", "POST"])
def upload_image():
    if not checkSession():
        return redirect("/login")

    logged_user = session["user"]

    if request.method == "POST":

        # MULTIPLE FILES
        files = request.files.getlist("images")
        project_name = request.form.get("project_name")

        # VALIDATION
        if len(files) == 0:
            return render_template("error.html", msg="No files selected")

        if not project_name or project_name.strip() == "":
            return render_template("error.html", msg="Project name is required")

        # LOOKUP OR CREATE PROJECT
        from project import project
        proj = project()
        proj.getByField("Project_name", project_name)

        if len(proj.data) > 0:
            project_id = proj.data[0]["Project_ID"]
        else:
            proj.set({"Project_name": project_name})
            proj.insert()
            project_id = proj.data[0]["Project_ID"]

        # CREATE PROJECT FOLDER
        project_folder = os.path.join(UPLOAD_FOLDER, str(project_id))
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)

        # SAVE ALL FILES
        saved_count = 0

        for file in files:
            if not file or file.filename.strip() == "":
                continue

            filename = secure_filename(file.filename)
            filepath = os.path.join(project_folder, filename).replace("\\", "/")
            file.save(filepath)

            # insert image record
            img = images()
            img.set({
                "Image_path": filepath,
                "Date_added": datetime.datetime.now(),
                "Project_ID": project_id
            })
            img.insert()

            saved_count += 1

        return render_template("ok_dialog.html", msg=f"{saved_count} images uploaded!")

    return render_template("images/upload.html")




# ---------------------------------------------------------
#   PROJECT SEARCH (AUTOCOMPLETE)
# ---------------------------------------------------------
@app.route("/projects/search")
def project_search():
    term = request.args.get("term", "").strip()

    from project import project
    p = project()

    if term == "":
        return []

    sql = "SELECT Project_name FROM project WHERE Project_name LIKE %s LIMIT 10"
    p.cur.execute(sql, [f"%{term}%"])

    from flask import jsonify
    return jsonify([row["Project_name"] for row in p.cur])


# ---------------------------------------------------------
#   PROJECT LIST
# ---------------------------------------------------------
@app.route("/images/list")
def images_list():
    if not checkSession(): 
        return redirect("/login")

    from project import project
    from images import images

    proj = project()
    proj.getAll()

    stats = []

    for p in proj.data:
        pid = p["Project_ID"]

        db = images()
        sql = """
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN l.Label_ID IS NULL THEN 1 ELSE 0 END) AS unlabeled
            FROM images i
            LEFT JOIN labels l ON i.Image_ID = l.Image_ID
            WHERE i.Project_ID = %s
        """
        db.cur.execute(sql, [pid])
        row = db.cur.fetchone()

        stats.append({
            "Project_ID": pid,
            "Project_name": p["Project_name"],
            "total": row["total"],
            "unlabeled": row["unlabeled"]
        })

    return render_template("images/project_list.html", projects=stats)



# ---------------------------------------------------------
#   VIEW IMAGES WITH ANNOTATION STATUS
# ---------------------------------------------------------
@app.route("/images/view/<pid>")
def images_view(pid):
    if not checkSession():
        return redirect("/login")

    from project import project
    from images import images

    # Get project info
    proj = project()
    proj.getById(pid)

    # Pagination parameters
    page = request.args.get("page", default=1, type=int)
    per_page = 12  # how many images per page (change if you want)

    db = images()

    # Total images for this project
    count_sql = "SELECT COUNT(*) AS total FROM images WHERE Project_ID = %s"
    db.cur.execute(count_sql, [pid])
    total_row = db.cur.fetchone()
    total_images = total_row["total"] if total_row and "total" in total_row else 0

    # Total pages (at least 1 so template doesn't break)
    total_pages = max(1, (total_images + per_page - 1) // per_page)

    # Clamp page into valid range
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page

    # Fetch only images for this page, with label status
    sql = """
        SELECT
            i.*,
            l.Label_ID,
            CASE WHEN l.Label_ID IS NULL THEN 0 ELSE 1 END AS has_label
        FROM images i
        LEFT JOIN labels l ON i.Image_ID = l.Image_ID
        WHERE i.Project_ID = %s
        ORDER BY i.Image_ID
        LIMIT %s OFFSET %s
    """
    db.cur.execute(sql, [pid, per_page, offset])
    images_list = db.cur.fetchall()

    return render_template(
        "images/view_images.html",
        project=proj.data[0],
        images=images_list,
        page=page,
        total_pages=total_pages,
    )




# ---------------------------------------------------------
#   REGISTER USER
# ---------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        o = user()

        d = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "role": "customer",
            "password": request.form.get("password"),
            "password2": request.form.get("password2")
        }

        o.set(d)

        if o.verify_new():
            o.insert()
            return render_template("ok_dialog.html", msg="Account created! Login now.")
        else:
            return render_template("register.html", obj=o)

    return render_template("register.html")


# ---------------------------------------------------------
#   SEARCH LABELS + IMAGES + PROJECTS
# ---------------------------------------------------------
@app.route("/search", methods=["GET", "POST"])
def search():
    if not checkSession(): return redirect("/login")

    results = []
    query = request.form.get("query", "").strip()

    if request.method == "POST" and query != "":
        like_term = f"%{query}%"

        sql = """
        SELECT 
            l.Label_ID, l.L_Name, l.Description,
            l.UID,
            i.Image_ID, i.Image_path,
            p.Project_ID, p.Project_name,
            u.name AS user_name
        FROM labels l
        JOIN images i ON l.Image_ID = i.Image_ID
        JOIN project p ON i.Project_ID = p.Project_ID
        JOIN users u ON l.UID = u.UID
        WHERE 
            l.L_Name LIKE %s
            OR l.Description LIKE %s
            OR i.Image_path LIKE %s
            OR p.Project_name LIKE %s
        """

        from project import project
        db = project()

        db.cur.execute(sql, [like_term, like_term, like_term, like_term])

        for row in db.cur:
            results.append(row)

    return render_template("search/search.html",
                           results=results,
                           query=query,
                           me=session["user"])


# ---------------------------------------------------------
#   EDIT LABEL
# ---------------------------------------------------------
@app.route("/labels/edit/<int:lid>", methods=["GET", "POST"])
def edit_label(lid):
    if not checkSession(): return redirect("/login")

    uid = session["user"]["UID"]
    role = session["user"]["role"]

    from images import images
    from project import project

    lbl = label()
    lbl.getById(lid)

    if len(lbl.data) == 0:
        return render_template("error.html", msg="Label not found.")

    if role != "admin" and lbl.data[0]["UID"] != uid:
        return render_template("error.html", msg="You cannot edit another user's label.")

    img = images()
    img.getById(lbl.data[0]["Image_ID"])

    proj = project()
    proj.getById(img.data[0]["Project_ID"])

    if request.method == "POST":
        lbl.data[0]["L_Name"] = request.form.get("L_Name")
        lbl.data[0]["Description"] = request.form.get("Description")
        lbl.update()
        return render_template("ok_dialog.html", msg="Label updated!")

    return render_template(
        "labels/edit.html",
        label={
            **lbl.data[0],
            "Image_path": img.data[0]["Image_path"],
            "Project_name": proj.data[0]["Project_name"]
        }
    )


# ---------------------------------------------------------
#   DELETE LABEL (ADMIN)
# ---------------------------------------------------------
@app.route("/labels/delete/<int:lid>")
def delete_label(lid):
    if not checkSession(): return redirect("/login")

    if session["user"]["role"] != "admin":
        return render_template("error.html", msg="Admin only.")

    lbl = label()
    lbl.deleteById(lid)

    return render_template("ok_dialog.html", msg="Label deleted.")


# ---------------------------------------------------------
#   ANNOTATE (GET)
# ---------------------------------------------------------
@app.route('/annotate/project/<pid>')
def annotate_project(pid):
    if not checkSession():
        return redirect('/login')

    from images import images
    from project import project

    # Get project details
    proj = project()
    proj.getById(pid)

    # Find next unlabeled image
    db = images()
    sql = """
        SELECT i.* FROM images i
        LEFT JOIN labels l ON i.Image_ID = l.Image_ID
        WHERE i.Project_ID = %s AND l.Image_ID IS NULL
        ORDER BY i.Image_ID
        LIMIT 1
    """
    db.cur.execute(sql, [pid])
    result = db.cur.fetchall()

    if len(result) == 0:
        return render_template("ok_dialog.html", msg="All images annotated!")

    image = result[0]

    return render_template(
        "annotation/annotate.html",
        image=image,
        project_id=pid,
        project_name=proj.data[0]["Project_name"]
    )




# ---------------------------------------------------------
#   ANNOTATE SAVE (POST)
# ---------------------------------------------------------
@app.route('/annotate/save', methods=['POST'])
def annotate_save():
    if not checkSession():
        return redirect('/login')

    from label import label

    image_id = request.form.get("image_id")
    project_id = request.form.get("project_id")
    label_name = request.form.get("label_name")
    description = request.form.get("description")
    uid = session["user"]["UID"]

    # Create NEW label only (annotation workflow)
    lbl = label()
    lbl.set({
        "L_Name": label_name,
        "Description": description,
        "UID": uid,
        "Image_ID": image_id
    })
    lbl.insert()

    # Load next image automatically
    return redirect(f"/annotate/project/{project_id}")


# ---------------------------------------------------------
#   GLOBAL ANNOTATION DASHBOARD
# ---------------------------------------------------------
@app.route("/annotate")
def annotate_dashboard():
    if not checkSession(): 
        return redirect("/login")

    from project import project
    from images import images

    p = project()
    p.getAll()
    projects = p.data

    stats = []

    for proj in projects:
        pid = proj["Project_ID"]

        db = images()
        sql = """
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN l.Label_ID IS NULL THEN 1 ELSE 0 END) AS unlabeled
            FROM images i
            LEFT JOIN labels l ON i.Image_ID = l.Image_ID
            WHERE i.Project_ID = %s
        """
        db.cur.execute(sql, [pid])
        row = db.cur.fetchone()

        stats.append({
            "Project_ID": pid,
            "Project_name": proj["Project_name"],
            "total": row["total"],
            "unlabeled": row["unlabeled"]
        })

    return render_template("annotation/dashboard.html", stats=stats)

import csv
from flask import make_response, jsonify
#__________ ------------------------------------------------
@app.route("/export/all/csv")
def export_all_csv():
    if not checkSession():
        return redirect("/login")

    import io, csv
    from label import label

    sql = """
        SELECT l.Label_ID, l.L_Name, l.Description,
               i.Image_path,
               p.Project_name,
               u.name AS user_name
        FROM labels l
        JOIN images i ON l.Image_ID = i.Image_ID
        JOIN project p ON i.Project_ID = p.Project_ID
        JOIN users u ON l.UID = u.UID
    """

    db = label()
    db.cur.execute(sql)
    rows = db.cur.fetchall()

    # WRITE CSV TO MEMORY
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Label_ID", "Label", "Description", "Image", "Project", "User"])

    for r in rows:
        writer.writerow([
            r["Label_ID"],
            r["L_Name"],
            r["Description"],
            r["Image_path"],
            r["Project_name"],
            r["user_name"]
        ])

    csv_data = output.getvalue()
    output.close()

    # SEND AS DOWNLOAD
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=all_labels.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


@app.route("/export/project/<pid>/csv")
def export_project_csv(pid):
    if not checkSession():
        return redirect("/login")

    import io, csv
    from label import label

    sql = """
        SELECT l.Label_ID, l.L_Name, l.Description,
               i.Image_path,
               p.Project_name,
               u.name AS user_name
        FROM labels l
        JOIN images i ON l.Image_ID = i.Image_ID
        JOIN project p ON i.Project_ID = p.Project_ID
        JOIN users u ON l.UID = u.UID
        WHERE p.Project_ID = %s
    """

    db = label()
    db.cur.execute(sql, [pid])
    rows = db.cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Label_ID", "Label", "Description", "Image", "Project", "User"])

    for r in rows:
        writer.writerow([
            r["Label_ID"],
            r["L_Name"],
            r["Description"],
            r["Image_path"],
            r["Project_name"],
            r["user_name"]
        ])

    csv_data = output.getvalue()
    output.close()

    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename=project_{pid}.csv"
    response.headers["Content-Type"] = "text/csv"
    return response



#_--------------------------------------------------------
@app.route("/export/project/<pid>/json")
def export_project_json(pid):
    from label import label

    sql = """
        SELECT l.Label_ID, l.L_Name, l.Description,
               i.Image_path,
               p.Project_name,
               u.name AS user_name
        FROM labels l
        JOIN images i ON l.Image_ID = i.Image_ID
        JOIN project p ON i.Project_ID = p.Project_ID
        JOIN users u ON l.UID = u.UID
        WHERE p.Project_ID = %s
    """

    db = label()
    db.cur.execute(sql, [pid])
    rows = db.cur.fetchall()

    return jsonify(rows)


#_______________download JSON for all labels--------------------------
import zipfile
import io
import csv
from flask import send_file

@app.route("/export/project/<pid>/zip")
def export_project_zip(pid):
    from project import project
    from images import images
    from label import label

    # Get project name
    proj = project()
    proj.getById(pid)
    proj_name = proj.data[0]["Project_name"]

    # FETCH IMAGE + LABEL DATA
    sql = """
        SELECT l.Label_ID, l.L_Name, l.Description,
               i.Image_ID, i.Image_path,
               p.Project_name,
               u.name AS user_name
        FROM labels l
        JOIN images i ON l.Image_ID = i.Image_ID
        JOIN project p ON i.Project_ID = p.Project_ID
        JOIN users u ON l.UID = u.UID
        WHERE p.Project_ID = %s
    """

    db = label()
    db.cur.execute(sql, [pid])
    rows = db.cur.fetchall()

    # Memory buffer for ZIP
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:

        # -------------------------------
        # 1. ADD CSV FILE
        # -------------------------------
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Label_ID", "Label", "Description", "Image", "Project", "User"])

        for r in rows:
            writer.writerow([
                r["Label_ID"],
                r["L_Name"],
                r["Description"],
                r["Image_path"].split("/")[-1],  # filename only
                r["Project_name"],
                r["user_name"]
            ])

        zf.writestr("labels.csv", csv_buffer.getvalue())

        # -------------------------------
        # 2. ADD IMAGES
        # -------------------------------
        for r in rows:
            img_path = r["Image_path"]

            if os.path.exists(img_path):
                with open(img_path, "rb") as img_file:
                    image_bytes = img_file.read()
                filename_only = img_path.split("/")[-1]

                # Save inside /images/ folder in ZIP
                zf.writestr(f"images/{filename_only}", image_bytes)

    memory_file.seek(0)

    return send_file(
        memory_file,
        download_name=f"{proj_name}_dataset.zip",
        as_attachment=True
    )
#---------------------------------------------------------
#   dashboard admin
#---------------------------------------------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not checkSession():
        return redirect("/login")

    if session["user"]["role"] != "admin":
        return render_template("error.html", msg="Admin only")

    from project import project
    from label import label

    p = project()
    project_stats = p.project_stats()

    l = label()
    top_users = l.top_annotators()
    freq = l.label_frequency()

    return render_template(
        "admin/dashboard.html",
        project_stats=project_stats,
        top_users=top_users,
        freq=freq
    )

# ---------------------------------------------------------
#   SESSION CHECK
# ---------------------------------------------------------
def checkSession():
    if "active" in session:
        if time.time() - session["active"] > 500:
            return False
        session["active"] = time.time()
        return True
    return False


# ---------------------------------------------------------
#   RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
