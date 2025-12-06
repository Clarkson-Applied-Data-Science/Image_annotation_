
from pathlib import Path
import pymysql
import datetime
from baseObject import baseObject
import hashlib

class user(baseObject):
    def __init__(self):
        self.setup()
        self.roles = [{'value':'admin','text':'admin'},{'value':'customer','text':'customer'}]
    def hashPassword(self,pw):
        pw = pw+'xyz'
        return hashlib.md5(pw.encode('utf-8')).hexdigest()
    def role_list(self):
        rl = []
        for item in self.roles:
            rl.append(item['value'])
        return rl
    def verify_new(self):
        self.errors = []
        #
        if '@' not in self.data[0]['email']:
            self.errors.append('Email must contain @')
        u = user()
        u.getByField('email',self.data[0]['email'])
        if len(u.data) > 0:
            self.errors.append(f"Email address is already in use. ({self.data[0]['email']})")
        
        if len(self.data[0]['password']) < 3:
            self.errors.append('Password should be greater than 3 chars.')
        if self.data[0]['password'] != self.data[0]['password2']:
            self.errors.append('Retyped password must match.')
        self.data[0]['password'] = self.hashPassword(self.data[0]['password'])
        del self.data[0]['password2']
        if self.data[0]['role'] not in self.role_list():
            self.errors.append(f"Role must be one of {self.role_list()}")
        #
       
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    def verify_update(self):
        self.errors = []
        #
        if '@' not in self.data[0]['email']:
            self.errors.append('Email must contain @')
        u = user()
        u.getByField('email',self.data[0]['email'])
        if len(u.data) > 0 and u.data[0][u.pk] != self.data[0][self.pk]:
            self.errors.append(f"Email address is already in use. ({self.data[0]['email']})")
        
        if 'password2' in self.data[0].keys() and len(self.data[0]['password2']) > 0:
            if len(self.data[0]['password']) < 3:
                self.errors.append('Password should be greater than 3 chars.')
            if self.data[0]['password'] != self.data[0]['password2']:
                self.errors.append('Retyped password must match.')
        
            self.data[0]['password'] = self.hashPassword(self.data[0]['password'])
        else:
            del self.data[0]['password']
        if self.data[0]['role'] not in self.role_list():
            self.errors.append(f"Role must be one of {self.role_list()}")
        #
        
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    
    def tryLogin(self,un, pw):
        #print(un,pw)
        pw = self.hashPassword(pw)
        #print(un,pw)
        self.data = []
        sql = f'''SELECT * FROM `{self.tn}` WHERE `email` = %s AND `password` = %s;'''
        #print(sql,[un,pw])
        self.cur.execute(sql,[un,pw])
        for row in self.cur:
            self.data.append(row)
        if len(self.data) == 1:
            return True
        return False
            