from baseObject import baseObject

class project(baseObject):
    def __init__(self):
        self.setup()

    def label_frequency(self):
        sql = """
            SELECT 
                L_Name,
                COUNT(*) AS count
            FROM labels
            GROUP BY L_Name
            ORDER BY count DESC
        """
        self.cur.execute(sql)
        return self.cur.fetchall()

    def project_stats(self):
        sql = """
            SELECT 
                p.Project_ID,
                p.Project_name,
                COUNT(i.Image_ID) AS total_images,
                SUM(CASE WHEN l.Label_ID IS NULL THEN 1 ELSE 0 END) AS unlabeled,
                MAX(i.Date_added) AS last_upload
            FROM project p
            LEFT JOIN images i ON p.Project_ID = i.Project_ID
            LEFT JOIN labels l ON i.Image_ID = l.Image_ID
            GROUP BY p.Project_ID, p.Project_name
            ORDER BY total_images DESC
        """
        self.cur.execute(sql)
        return self.cur.fetchall()
