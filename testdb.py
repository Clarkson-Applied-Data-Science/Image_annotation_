import pymysql

try:
    conn = pymysql.connect(
        host="mysql.clarksonmsda.org",
        user="metimas",
        passwd="Sumanth331$",
        db="metimas_DD2",
        port=3306,
        connect_timeout=5
    )
    print("Connected OK!")
except Exception as e:
    print("ERROR:", e)
