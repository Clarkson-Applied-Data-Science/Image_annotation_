from user import user


u = user()


d = {'name':'Tyler','email':'tconlon@clarkson.edu','role':'admin','password':'123','password2':'123'}
u.set(d)
if u.verify_new():
    u.insert()
    print(f"ID {u.data[0][u.pk]} inserted")
else:
    print(u.errors)

d = {'name':'James','email':'conlontj@clarkson.edu','role':'admin','password':'123','password2':'123'}
u.set(d)
if u.verify_new():
    u.insert()
    print(f"ID {u.data[0][u.pk]} inserted")
else:
    print(u.errors)