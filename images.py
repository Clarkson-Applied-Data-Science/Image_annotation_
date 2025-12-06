from baseObject import baseObject

class images(baseObject):
    def __init__(self):
        self.setup()

    def verify(self):
        self.errors = []
        if self.data[0]['Image_path'] == '':
            self.errors.append("Image path required")
        if self.data[0]['Project_ID'] == '':
            self.errors.append("Project ID required")
        return len(self.errors) == 0
