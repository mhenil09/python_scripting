import datetime
import requests
import openpyxl
import database_operations as dc

curr_timestamp = datetime.datetime.now().replace(microsecond=0)
file_name = 'excel_files/hs_codes.xlsx'


db = dc.connect_db()


def write_exceptional_data(data_string):
    ex_file_name = "excel_files/exceptions/exception_entries.txt"
    f = open(ex_file_name, 'a')
    f.write(str(curr_timestamp) + " -> " + data_string + "\n")
    f.close()


def download_excel_file():
    hs_link = "http://unstats.un.org/unsd/tradekb/Attachment439.aspx?AttachmentType=1"
    resp = requests.get(hs_link)
    output = open(file_name, 'wb')
    output.write(resp.content)
    output.close()


# def fetch_classification_id(classification):
#     mycursor = db.cursor()
#     mycursor.execute("SELECT * from hs_classification where code = %s", (classification,))
#     result = mycursor.fetchone()
#     return result[0]


def fetch_hs_codes_id(code, classification_id):
    mycursor = db.cursor()
    mycursor.execute("SELECT * from hs_codes where code = %s", (code,))
    result = mycursor.fetchone()
    if result is None:
        return None
    else:
        return result[0]


# def store_classifications(classification_set):
#     classification_insert = "INSERT INTO hs_classification(code, updated_on, deleted_on) VALUES (%s, %s, %s)"
#     classification_check = "SELECT * from hs_classification where code = %s"
#     for c in classification_set:
#         if not check_for_duplication(classification_check, (c,)):
#             val = (c, curr_timestamp, None)
#             result = execute_query_single(classification_insert, val)
#             print(result)


def store_hs_codes(code, description, parent):
    # classification_id = fetch_classification_id(classification)
    hs_code_check = "SELECT * from hs_codes where code = %s and description = %s"
    hs_code_insert = "INSERT INTO hs_codes(code, description, parent_hs, classification_id, updated_on, deleted_on) VALUES (%s,%s,%s,%s,%s,%s)"
    hs_check_val = (code, description)
    if not dc.check_for_duplication(hs_code_check, hs_check_val):
        if parent == "TOTAL":
            parent_hs = None
        else:
            parent_hs = fetch_hs_codes_id(parent, None)
            if parent_hs is None:
                phs_insert_val = (parent, "", None, None, curr_timestamp, None)
                write_exceptional_data("HS Code " + parent + " not found in excel, entered via code")
                result1 = dc.execute_query_single(hs_code_insert, phs_insert_val)
                print(result1)
                parent_hs = fetch_hs_codes_id(parent, None)
        hs_insert_val = (code, description, parent_hs, None, curr_timestamp, None)
        result1 = dc.execute_query_single(hs_code_insert, hs_insert_val)
        print(result1)


# def process_classifications(worksheet):
#     classification_list = list()
#     for index, row in enumerate(worksheet.rows):
#         if index != 0 and row[0].value not in classification_list:
#             classification_list.append(row[0].value)
#     store_classifications(classification_list)


def process_hs_codes(worksheet):
    for index, row in enumerate(worksheet.rows):
        if index != 0:
            classification = row[0].value
            code = row[1].value
            description = row[2].value
            parent = row[3].value
            if parent is not None and classification == "H5":
                store_hs_codes(code, description, parent)


def read_excel_file():
    # To open the Workbook
    workbook = openpyxl.load_workbook(file_name)
    worksheet = workbook.active
    # process_classifications(worksheet)
    process_hs_codes(worksheet)


# read_excel_file()
read_excel_file()
