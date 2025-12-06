from baseObject import baseObject

class label(baseObject):
    def __init__(self):
        self.setup()

    def verify(self):
        self.errors = []

        if self.data[0]['L_Name'] == '':
            self.errors.append("Label name required")

        if 'Description' in self.data[0] and self.data[0]['Description'] == '':
            self.errors.append("Description is required")

        if self.data[0]['UID'] == '':
            self.errors.append("User ID required")

        if self.data[0]['Image_ID'] == '':
            self.errors.append("Image ID required")

        return len(self.errors) == 0


    def top_annotators(self):
        sql = """
            SELECT 
                u.name,
                COUNT(l.Label_ID) AS total_labels
            FROM labels l
            JOIN users u ON l.UID = u.UID
            GROUP BY u.UID
            ORDER BY total_labels DESC
            LIMIT 5
        """
        self.cur.execute(sql)
        return self.cur.fetchall()
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
