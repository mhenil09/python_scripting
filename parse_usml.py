import datetime
import urllib.request
from bs4 import BeautifulSoup as bs
import database_operations as dc
import usml_library as u
import constants

curr_timestamp = datetime.datetime.now().replace(microsecond=0)
today = str(datetime.date.today())  # - datetime.timedelta(days=1))
usml_url = 'https://www.ecfr.gov/api/versioner/v1/full/' + today + '/title-22.xml?chapter=I&part=121&section=121.1&subchapter=M&subject_group=ECFR6cf5c989d9a8d36'

# call the URL & collect response
def fetch_data_from_url(url):
    file = urllib.request.urlopen(url)
    data = file.read()
    file.close()
    string = str(data).encode('utf-8')
    return string.decode().lstrip("b'").rstrip("'")


# method to sanitize string & remove unnecessary characters
def clean_string(string):
    return string.replace("\\xce\\x94", 'Δ').replace("\\xce\\xbb", "λ").replace('\\xe2\\x80\\x9c', '"').replace('\\xe2\\x80\\x9d', '"').replace("\\n", "")\
        .replace("\\xc2\\xa7", "§").replace("\\xe2\\x80\\x98", "‘").replace("\\xc3\\x97", "×").replace("\\xc2\\xb5", "µ")\
        .replace("\\xe2\\x80\\x99", "’").replace("\\'", "'").replace("\\xc2\\xb0", "°").replace("\\xc2\\xb1", "±").replace("\\xc2\\xb7", "Â")\
        .replace("\\xe2\\x86\\x91", "").replace("\\xe2\\x86\\x93", "").replace("\\xe2\\x88\\x92", "").replace("\\xe2\\x80\\xb2", "'").replace("\\xcf\\x81", "ρ").strip()


# store the response into an XML file in string format
def do_file_operations():
    file_name = constants.dir_name + "usml/" + today + ".xml"
    f = open(file_name, "w")
    f.write(fetch_data_from_url(usml_url).replace("\\n", ""))
    f.close()
    return file_name


file_name = do_file_operations()


# reading the XML file that we just stored
def fetch_xml_content(file):
    with open(file, 'r') as f:
        xml_data = f.readlines()
        xml_data = "".join(xml_data)
        _bs_data = bs(xml_data.replace("<I>and</I>", "and").replace("<I>or</I>", "or"), "lxml-xml")
    return _bs_data


bs_data = fetch_xml_content(file_name)


def store_category(identifier, title):
    cat_insert = "INSERT INTO usml_categories(identifier, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    cat_history_insert = "INSERT INTO usml_category_histories(identifier, title, created_on, version_id, usml_category_id) VALUES (%s, %s, %s, %s, %s)"
    cat_check_identifier = "SELECT * from usml_categories where identifier = %s"
    cat_check_title = "SELECT * from usml_categories where title = %s"
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

def store_note(note_header, note_text, category_id, item_id):
    note_insert = "INSERT INTO usml_notes(usml_category_id, header, description, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    note_text = clean_string(note_text)
    note_insert_val = (category_id, note_header, note_text, curr_timestamp, None)
    dc.execute_query_single(note_insert, note_insert_val)


def store_item(identifier, text, is_sme, is_mtcr, category_id, parent):
    text = clean_string(text).strip()
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
            parent_id = dc.get_entity_id(get_parent_id, (parent, category_id))
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


def process_items(cat_item_dict):
    for key in cat_item_dict.keys():
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


def delete_usml_notes():
    dc.execute_query_single("DELETE from usml_item_note", ())
    dc.execute_query_single("DELETE from usml_notes ", ())


def process_categories():
    delete_usml_notes()
    for extract in bs_data.find_all("EXTRACT"):
        for h1 in extract.find_all("HD1"):
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
            notes_to_be_stored = []
            for sibling in h1.find_next_siblings():
                if sibling.name == "P":
                    is_sme = False
                    is_mtcr = False
                    if sibling.text.strip().startswith("*"):
                        is_sme = True
                    if "(MT)" in sibling.text.strip():
                        is_mtcr = True
                    item_text_with_tags = str(sibling).replace("*", "").replace("(MT)", "").strip()
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
                            item_text_with_tags = str(item_text_with_tags)
                            i_index = item_text.split(")")[0] + ")".strip()
                            i_text = item_text_with_tags.replace(i_index, "")
                            i_index_lst.append(i_index.strip())
                            ind = i_index
                            i_text_lst.append(i_text)
                            sme_lst.append(is_sme)
                            mtcr_lst.append(is_mtcr)
                            parent_lst.append(ind)
                        elif (not item_text.startswith("(See")) and (not item_text.startswith("(MT")):
                            item_text_with_tags = str(sibling).strip()
                            i_text_lst[-1] += (str(item_text_with_tags))
                if sibling.name == "img":
                    item_text_with_tags = str(sibling).replace(".gif", ".png").strip()
                    i_text_lst[-1] += (str(item_text_with_tags))
                    for nextSibling in sibling.find_next_siblings():
                        if nextSibling.name == "FP" or nextSibling.name == "FP-2":
                            item_text_with_tags = str(sibling.find_next_sibling()).strip()
                            i_text_lst[-1] += (str(item_text_with_tags))
                            sibling.find_next_sibling().decompose()
                        if nextSibling.name == "P":
                            break
                if sibling.name == "NOTE": # and sibling.get("class")[0] == "note":
                    note_content = sibling
                    note_header = sibling.find("HED").text
                    note_text = ""
                    for ps in sibling.find_all("P"):
                        note_text += "<p>"+ps.text+"</p>"
                    notes_to_be_stored.append([note_header, note_text, category_id, {'item_identifiers': []}])
                if sibling.name == "HD1":
                    break
            print("=======================================================")
            process_items({identifier: (i_index_lst, i_text_lst, sme_lst, mtcr_lst, parent_lst)})
            for note in notes_to_be_stored:
                store_note(note[0], note[1], note[2], note[3])


def find_references_for_notes():
    notes = dc.execute_select_query("Select id, usml_category_id, header from usml_notes", ())
    associate_item_with_note = []
    for note in notes:
        note_id = note[0]
        category_id = note[1]
        note_header = note[2]
        note_header = note_header.lower().replace("usml ", "").replace('(g)(3)-(6)', '(g)(3)-(g)(6)').replace('paragraph e)(17)', 'paragraph (e)(17)').replace('paragraphs', '<para>').replace('paragraph', '<para>').replace(' and ', '<and>').replace('-', '<to>').replace(' to ', '<to>').replace(":", "").strip()
        if '<para>' not in note_header:
            continue
        item_identifier = note_header.split("<para>")[1].strip()
        if "<and>" not in item_identifier and "<to>" not in item_identifier:
            item_identifier = note_header.split("<para>")[1].strip()
            query = "select id from usml_items where identifier like '"+item_identifier.strip()+"%' and usml_category_id = " + str(category_id)
            results = dc.execute_select_query(query, ())
            for result in results:
                associate_item_with_note.append("("+str(result[0])+", "+str(note_id)+")")
            continue
        else:
            if "<and>" in item_identifier:
                identifiers = item_identifier.split('<and>')
                query = "select id from usml_items where identifier like '"+identifiers[0].strip()+"%' or identifier like '"+identifiers[1].strip()+"' and usml_category_id = " + str(category_id)
                results = dc.execute_select_query(query, ())
                for result in results:
                    associate_item_with_note.append("("+str(result[0])+", "+str(note_id)+")")
                continue
            if "<to>" in item_identifier:
                range = item_identifier.split('<to>')
                query = "select distinct id from usml_items where ((identifier >= '"+range[0]+"' and identifier <= '"+range[1]+"') or (identifier like '"+range[0]+"%' or identifier like '"+range[1]+"%')) and usml_category_id = " + str(category_id)
                results = dc.execute_select_query(query, ())
                for result in results:
                    associate_item_with_note.append("("+str(result[0])+", "+str(note_id)+")")    
    query = "INSERT into usml_item_note (item_id, note_id) VALUES " + ", ".join(associate_item_with_note)
    dc.execute_query_single(query, ())
    
    
        # elif "paragraphs" in note_header:
        #     item_identifier_range = note_header.split("to paragraph")[1].replace(":", "").strip()
        #     item_range = generate_items_from_range(item_identifier_range.replace(":", "").strip())
        #     notes_to_be_stored.append([note_text, category_id, {'item_identifiers': item_range}])
        # else:
        #     note_text = note_text.strip()
        #     notes_to_be_stored.append([note_text, category_id, {'item_identifiers': []}])
        
# Note 2 to paragraph e)(17):
# Note: Parts, components, accessories, and attachments in paragraphs (h)(3)-(5), (7), (14), (17), or (19) are licensed by the Department of Commerce when incorporated in an aircraft subject to the EAR and classified under ECCN 9A610. Replacement systems, parts, components, accessories and attachments are subject to the controls of the ITAR.

# process_categories()
# find_references_for_notes()
