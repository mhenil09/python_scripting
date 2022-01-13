import datetime
import urllib.request
from bs4 import BeautifulSoup as bs
import database_operations as dc
import lxml
import usml_utilities as u

curr_timestamp = datetime.datetime.now().replace(microsecond=0)
today = str(datetime.date.today())  # - datetime.timedelta(days=1))
usml_url = "https://www.ecfr.gov/current/title-22/chapter-I/subchapter-M/part-121/subject-group-ECFR6cf5c989d9a8d36/section-121.1"

db = dc.connect_db()

# call the URL & collect response
def fetch_data_from_url(url):
    file = urllib.request.urlopen(url)
    data = file.read()
    file.close()
    string = str(data).encode('utf-8')
    return str(string, "UTF-8")


# method to sanitize string & remove unnecessary characters
def clean_string(string):
    return string.replace('\\xe2\\x80\\x9c', '"').replace('\\xe2\\x80\\x9d', '"').replace("\\n", "")\
        .replace("\\xc2\\xa7", "§").replace("\\xe2\\x80\\x98", "‘").replace("\\xc3\\x97", "×")\
        .replace("\\xe2\\x80\\x99", "’").replace("\\'", "'").replace("\\xc2\\xb0", "°").replace("\\xc2\\xb1", "±")\
        .replace("\\xe2\\x86\\x91", "").replace("\\xe2\\x86\\x93", "").replace("\\xe2\\x88\\x92", "").strip()


# store the response into an XML file in string format
def do_file_operations(path):
    file_name = "xml_files/" + path + today + ".xml"
    f = open(file_name, "w")
    f.write(clean_string(fetch_data_from_url(usml_url)))
    f.close()
    return file_name


file_name = do_file_operations("usml/")


# reading the XML file that we just stored
def fetch_xml_content(file):
    with open(file, 'r') as f:
        xml_data = f.readlines()
        xml_data = "".join(xml_data)
        _bs_data = bs(xml_data.replace("\\n", ""), "lxml")
    return _bs_data


bs_data = fetch_xml_content(file_name)


def store_category(identifier, title):
    cat_insert = "INSERT INTO usml_categories(identifier, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    cat_history_insert = "INSERT INTO usml_category_histories(identifier, title, created_on, version_id, usml_category_id) VALUES (%s, %s, %s, %s, %s)"
    cat_check_identifier = "SELECT * from usml_categories where identifier = %s"
    cat_check_title_id = "SELECT * from usml_categories where title = %s and identifier = %s"
    cat_update_title = "UPDATE usml_categories set title = %s and updated_on = %s where id = %s"
    cat_insert_val = (identifier, title, curr_timestamp, None)
    if dc.check_for_duplication(cat_check_identifier, (identifier,)):
        cat_id = dc.get_entity_id(cat_check_identifier, (identifier,))
        if not dc.check_for_duplication(cat_check_title_id, (title, identifier)):
            dc.execute_query_single(cat_update_title, (title, curr_timestamp, cat_id))
            dc.execute_query_single(cat_history_insert, (identifier, title, curr_timestamp, None, cat_id))
    else:
        dc.execute_query_single(cat_insert, cat_insert_val)
        cat_id = dc.get_entity_id(cat_check_title_id, (title, identifier))
        dc.execute_query_single(cat_history_insert, (identifier, title, curr_timestamp, None, cat_id))


def store_note(note_text, category_id, item_id):
    note_insert = "INSERT INTO usml_notes(usml_category_id, usml_item_id, description, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    note_hist_insert = "INSERT INTO usml_note_histories(usml_category_id, usml_item_id, usml_note_id, description, version_id, created_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    note_ci_check = "SELECT * from usml_notes where usml_category_id = %s and usml_item_id = %s and description like %s"
    note_insert_val = (category_id, item_id, note_text, curr_timestamp, None)
    if not dc.check_for_duplication(note_ci_check, (category_id, item_id, note_text)):
        dc.execute_query_single(note_insert, note_insert_val)
        print((category_id, item_id, note_text))
        note_id = dc.get_entity_id(note_ci_check, (category_id, item_id, note_text))
        note_hist_insert_val = (category_id, item_id, note_id, note_text, None, curr_timestamp, None)
        dc.execute_query_single(note_hist_insert, note_hist_insert_val)


def store_item(identifier, text, is_sme, is_mtcr, category_id, parent):
    text = text.strip()
    parent = parent.strip()
    item_insert = "INSERT INTO usml_items(identifier, parent_identifier, description, usml_category_id, is_sme, is_mtcr," \
                  " updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    item_hist_insert = "INSERT INTO usml_item_histories(identifier, parent_identifier, description, usml_category_id, " \
                       "is_sme, is_mtcr, version_id, created_on, usml_item_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    whole_item_check = "SELECT * from usml_items where identifier = %s and description = %s " \
                       "and usml_category_id = %s and is_sme = %s and is_mtcr = %s"
    get_parent_id = "SELECT * from usml_items where identifier = %s and usml_category_id = %s"
    item_update = "UPDATE usml_items SET description = %s, is_sme = %s, is_mtcr = %s, updated_on = %s where id = %s"
    if dc.check_for_duplication(get_parent_id, (identifier, category_id)):
        item_id = dc.get_entity_id(get_parent_id, (identifier, category_id))
        if parent is None or parent == "":
            parent_id = None
        else:
            print("Parent: " + parent)
            print("Cat: " + str(category_id))
            parent_id = dc.get_entity_id(get_parent_id, (parent, category_id))
        # print((identifier, text, category_id, is_sme, is_mtcr, item_id))
        if not dc.check_for_duplication(whole_item_check, (identifier, text, category_id, is_sme, is_mtcr)):
            dc.execute_query_single(item_update, (text, is_sme, is_mtcr, curr_timestamp, item_id))
            dc.execute_query_single(item_hist_insert, (identifier, parent_id, text, category_id, is_sme, is_mtcr, None, curr_timestamp, item_id))
    else:
        if parent != "":
            parent_id = dc.get_entity_id(get_parent_id, (parent, category_id))
        else:
            parent_id = None
        dc.execute_query_single(item_insert, (identifier, parent_id, text, category_id, is_sme, is_mtcr, curr_timestamp, None))
        item_id = dc.get_entity_id(get_parent_id, (identifier, category_id))
        dc.execute_query_single(item_hist_insert, (identifier, parent_id, text, category_id, is_sme, is_mtcr, None, curr_timestamp, item_id))


def next_element(lower):
    if str(lower).isdigit():
        return int(lower) + 1
    else:
        return chr(ord(lower.strip()) + 1)


def generate_items_from_range(clean_range):
    lower = clean_range.split("-")[0].replace("(", "").replace(")", "").strip()
    higher = clean_range.split("-")[1].replace("(", "").replace(")", "").strip()
    item_list = list()
    if str(lower).isdigit():
        higher = int(higher)
    while next_element(lower) != higher:
        item_list.append("(" + str(lower) + ")")
        lower = next_element(lower)
    item_list.append("(" + str(lower) + ")")
    item_list.append("(" + str(higher) + ")")
    return item_list

def generate_notes_from_range(clean_range):
    lower = clean_range.split("and")[0].replace("(", "").replace(")", "").strip()
    higher = clean_range.split("and")[1].replace("(", "").replace(")", "").strip()
    item_list = list()
    item_list.append("(" + str(lower) + ")")
    item_list.append("(" + str(higher) + ")")
    return item_list

def process_items(cat_item_dict):
    for key in cat_item_dict.keys():
        if key != "XIII" and key != "XVIII":
            category_id = dc.get_entity_id("select id from usml_categories where identifier = %s", (key.strip(),))
            brac_less_lst = list()
            for p in cat_item_dict[key][0]:
                brac_less_lst.append(p.replace("(", "").replace(")", "").strip())
            new_list = u.process_indexes(brac_less_lst)
            for index, value in enumerate(cat_item_dict[key][1]):
                identifier = new_list[index]
                text = cat_item_dict[key][1][index]
                is_sme = cat_item_dict[key][2][index]
                is_mtcr = cat_item_dict[key][3][index]
                parent = new_list[index].replace(cat_item_dict[key][4][index], "")
                store_item(identifier, text, is_sme, is_mtcr, category_id, parent)


def process_categories():
    for extract in bs_data.find_all("div", {"class": "extract"}):
        for h1 in extract.find_all("h1"):
            h1_text = h1.text.replace("Category", "").strip()
            splits = h1_text.split("-")
            identifier = splits[0].strip()
            title = splits[1].strip()
            store_category(identifier, title)
            print(identifier + " -> " + title)
            category_id = dc.get_entity_id("select id from usml_categories where identifier = %s", (identifier,))
            i_index_lst = list()
            i_text_lst = list()
            parent_lst = list()
            sme_lst = list()
            mtcr_lst = list()
            for sibling in h1.find_next_siblings():
                if sibling.name == "p":
                    is_sme = False
                    is_mtcr = False
                    if sibling.text.strip().startswith("*"):
                        is_sme = True
                    if "(MT)" in sibling.text.strip():
                        is_mtcr = True
                    item_text = sibling.text.replace("*", "").replace("(MT)", "").strip()
                    ind = ''
                    if "[Reserved]" in item_text:
                        if ")-(" not in item_text:
                            ind = item_text.replace("[Reserved]", "").strip()
                            i_index_lst.append(item_text.replace("[Reserved]", "").strip())
                            i_text_lst.append("[Reserved]")
                            sme_lst.append(is_sme)
                            mtcr_lst.append(is_mtcr)
                            parent_lst.append(ind)
                        else:
                            clean_range = item_text.replace("[Reserved]", "")
                            reserved_lst = generate_items_from_range(clean_range.replace(";", "").strip())
                            for res in reserved_lst:
                                ind = res
                                i_index_lst.append(res.strip())
                                i_text_lst.append("[Reserved]")
                                sme_lst.append(is_sme)
                                mtcr_lst.append(is_mtcr)
                                parent_lst.append(ind)
                    else:
                        if item_text.startswith("(") and (not item_text.startswith("(See")) and (not item_text.startswith("(MT")):
                            i_index = item_text.split(")")[0] + ")".strip()
                            i_text = item_text.replace(i_index, "")
                            i_index_lst.append(i_index.strip())
                            ind = i_index
                            i_text_lst.append(i_text)
                            sme_lst.append(is_sme)
                            mtcr_lst.append(is_mtcr)
                            parent_lst.append(ind)
                if sibling.name == "div" and sibling.get("class")[0] == "note":
                    note_header = sibling.find("div", {"class": "header"}).text
                    note_text = ""
                    for ps in sibling.find_all("p"):
                        note_text += ps.text
                    note_header = note_header.replace("USML ", "")
                    if "Category" in note_header:
                        note_text = note_text.strip()
                        #store_note(note_text, category_id, None)
                    elif "paragraph" in note_header:
                        item_identifier = note_header.split("to paragraph")[1].replace(":", "").strip()
                        note_text = note_text.strip()
                        print((item_identifier, category_id))
                        #item_id = dc.get_entity_id("SELECT * from usml_items where identifier = %s and usml_category_id = %s", (item_identifier, category_id))
                        #store_note(note_text, category_id, item_id)
                    elif "paragraphs" in note_header:
                        item_identifier_range = note_header.split("to paragraph")[1].replace(":", "").strip()
                        item_range = generate_items_from_range(item_identifier_range.replace(":", "").strip())
                        #for item in item_range:
                            #item_id = dc.get_entity_id(
                            #"SELECT * from usml_items where identifier = %s and usml_category_id = %s",
                            # (item, category_id))
                            #store_note(note_text, category_id, item_id)
                    else:
                        note_text = note_text.strip()
                        #store_note(note_text, category_id, None)
                    print("-----------------------------")
                if sibling.name == "h1":
                    break
            print("=======================================================")
            process_items({identifier: (i_index_lst, i_text_lst, sme_lst, mtcr_lst, parent_lst)})


process_categories()
