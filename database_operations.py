import mysql.connector

# get DB Connection
def connect_db():
    mydb = mysql.connector.connect(host="localhost", user="root", password="", database="ccc_check2")
    return mydb

db = connect_db()

# general method for checking duplication on a given entity
def check_for_duplication(sql, values_tpl):
    mycursor = db.cursor()
    mycursor.execute(sql, values_tpl)
    result = mycursor.fetchone()
    return False if not result else True


# method to execute query with single entry
def execute_query_single(sql, val_tuple):
    mycursor = db.cursor()
    mycursor.execute(sql, val_tuple)
    db.commit()


# method to execute query with multiple entries
def execute_query_multiple(sql, val_tuple_list):
    mycursor = db.cursor()
    mycursor.executemany(sql, val_tuple_list)
    db.commit()


# method helps in accessing recently added entity's id
def get_entity_id(sql, val):
    mycursor = db.cursor()
    mycursor.execute(sql, val)
    result = mycursor.fetchone()
    return result[0]


def get_entity(sql, val):
    mycursor = db.cursor()
    mycursor.execute(sql, val)
    result = mycursor.fetchone()
    return result


def execute_select_query(sql, val):
    mycursor = db.cursor()
    mycursor.execute(sql, val)
    result = mycursor.fetchall()
    return result