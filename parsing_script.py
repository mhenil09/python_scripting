import datetime
import urllib.request
from bs4 import BeautifulSoup as bs
import database_operations as dc
import lxml
import json

curr_timestamp = datetime.datetime.now().replace(microsecond=0)
today = str(datetime.date.today()) # - datetime.timedelta(days=1))
url_part738 = 'https://www.ecfr.gov/api/versioner/v1/full/'+today+'/title-15.xml?chapter=VII&part=738&subchapter=C&subtitle=B'
url_part740 = 'https://www.ecfr.gov/api/versioner/v1/full/'+today+'/title-15.xml?appendix=Supplement+No.+1+to+Part+740&chapter=VII&part=740&subchapter=C&subtitle=B'
url_part743 = 'https://www.ecfr.gov/api/versioner/v1/full/'+today+'/title-15.xml?appendix=Supplement+No.+1+to+Part+743&chapter=VII&part=743&subchapter=C&subtitle=B'
url_part745 = 'https://www.ecfr.gov/api/versioner/v1/full/'+today+'/title-15.xml?appendix=Supplement+No.+2+to+Part+745&chapter=VII&part=745&subchapter=C&subtitle=B'
url_part746_b_2 = 'https://www.ecfr.gov/api/versioner/v1/full/2021-10-06/title-15.xml?chapter=VII&part=746&section=746.1&subchapter=C&subtitle=B'

# call the URL & collect response
def fetch_data_from_url(url):
    file = urllib.request.urlopen(url)
    data = file.read()
    file.close()
    return str(data,"UTF-8")


# store the response into an XML file in string format
def do_file_operations(url, path):
    file_name = "xml_files/" + path + today + ".xml"
    f = open(file_name, "w")
    f.write(fetch_data_from_url(url).replace("\u2318", " "))
    f.close()
    return file_name


file_name1 = do_file_operations(url_part738, "part738/")
file_name2 = do_file_operations(url_part740, "part740/")
file_name3 = do_file_operations(url_part743, "part743/")
file_name4 = do_file_operations(url_part745, "part745/")
file_name5 = do_file_operations(url_part746_b_2, "part746_b_2/")


# reading the XML file that we just stored
def fetch_xml_content(filename):
    with open(filename, 'r') as f:
    #with open("xml_files/part740/2021-10-06.xml", 'r') as f:
        xml_data = f.readlines()
        xml_data = "".join(xml_data)
        bs_data = bs(xml_data, "lxml-xml")
    return bs_data

bs_data = fetch_xml_content(file_name1)
bs_data1 = fetch_xml_content(file_name2)
part743_data = fetch_xml_content(file_name3)
part745_data = fetch_xml_content(file_name4)
part746_data = fetch_xml_content(file_name5)

# supportive method used for fetch_sub_reasons() & fetch_headers()
def fill_sub_headers(ths):
    lst = list()
    for th in ths:
        lst.append(th.text.strip())
    return lst

# method helps in getting list of sub headers
def fetch_sub_reasons():
    sub_headers = list()
    for div9 in bs_data.find_all("DIV9"):
        for index, tr in enumerate(div9.find_all("TR")):
            if index != 0:
                sub_headers.append(fill_sub_headers(tr.find_all("TH")))
    for sub in sub_headers:
        if not sub:
            sub_headers.remove(sub)
    return sub_headers[0]

# method returns dictionary madeup of reasons as keys & their subreasons list as their respective values
def fetch_headers():
    headers = list()
    sub_headers = list()
    colspans = list()
    dictionary = {}
    for div9 in bs_data.find_all("DIV9"):
        for index, tr in enumerate(div9.find_all("TR")):
            # condition to differentiate between reasons & subreasons
            if index == 0:
                for index, value in enumerate(tr.find_all("TH")):
                    if index != 0:
                        if value.has_attr('colspan'):
                            colspans.append(int(value['colspan']))
                        else:
                            colspans.append(1)
                        headers.append(value.text)
            else:
                sub_headers = fill_sub_headers(tr.find_all("TH"))
                for index, value in enumerate(colspans):
                    lst = list(list())
                    for x in range(value):
                        if len(sub_headers)>0:
                            lst.append(sub_headers[0])
                            sub_headers.remove(sub_headers[0])
                    if lst:
                        dictionary[headers[index].strip()] = lst
    return dictionary

# method returns dictionary madeup of countries with & without superscripts fetched from <TD>, by parsing the table
def fetch_countries():
    countries_list_without_sup = list()
    countries_list_with_sup = list()
    for div9 in bs_data.find_all("DIV9"):
        for tr in div9.find_all("TR"):
            for index, value in enumerate(tr.find_all("TD")):
                if index == 0:
                    countries_list_with_sup.append(value.text.strip())
    for country in countries_list_with_sup:
        var = ''
        for token in fetch_superscripts(country):
            country = country.replace(str(token),"")
        countries_list_without_sup.append(country.strip())
    return {'countries_with_sup':countries_list_with_sup, 'countries_without_sup': countries_list_without_sup}

# method returns the values X & O from <TD> for a given country name(name with superscripts), by parsing the table
def fetch_values_for_country(country_name):
    permission_string = ''
    for div9 in bs_data.find_all("DIV9"):
        for tr in div9.find_all("TR"):
            length = len(tr.find_all("TD"))
            for index, value in enumerate(tr.find_all("TD")):
                if tr.find_all("TD")[0].text.strip() == country_name:
                    if index != 0:
                        if value.text.strip() == " " or value.text.strip() == "":
                            permission_string += "O "
                        else:
                            permission_string += value.text.strip()+" "
    return permission_string

# method helps in fetching the superscripts from a givan country name(name with superscripts) to be helpful in further processing of country_notes
def fetch_superscripts(country_name_superscript):
    superscripts_list = list()
    splitted_words = country_name_superscript.strip().split(" ")
    if len(splitted_words) == 1:
        for a in country_name_superscript:
            if a.isdigit():
                superscripts_list.append(int(a))
    else:
        for index, splitted_word in enumerate(splitted_words):
            if index != 0:
                if splitted_word.isdigit():
                    superscripts_list.append(int(splitted_word))
    return superscripts_list


def get_header_ids(sql, val):
    mycursor = db.cursor()
    mycursor.execute(sql, val)
    result = mycursor.fetchall()
    return result

# this method processes & stores reasons & sub-reasons
def process_headers():
    print('=================== Processing Headers ===================')
    headers_dict = fetch_headers()
    group_insert = "INSERT INTO group_countries(code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    group_hist_insert = "INSERT INTO group_countries_history(code, title, group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    parent_id_sql = 'SELECT * from group_countries where code = %s and title = %s limit 1'
    sub_parent_id_sql = 'SELECT * from sub_group_countries where code = %s and title = %s and group_id = %s limit 1'
    sub_group_insert = "INSERT INTO sub_group_countries(group_id, code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    sub_group_hist_insert = "INSERT INTO sub_group_countries_history(code, title, group_id, sub_group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s)"
    for key in headers_dict.keys():
        # insertion queries for reasons_for_control & reasons_for_control_histories
        code = headers_dict.get(key)[0].split(" ")[0].strip()
        if not dc.check_for_duplication(parent_id_sql,(code, key)):
            dc.execute_query_single(group_insert, (code, key, curr_timestamp, None))
            group_id = dc.get_entity_id(parent_id_sql, (code, key))
            dc.execute_query_single(group_hist_insert, (code, key, group_id, None, curr_timestamp))
        for value in headers_dict.get(key):
            group_id = dc.get_entity_id(parent_id_sql, (code, key))
            # insertion queries for sub_reasons_for_control & sub_reasons_for_control_histories
            if not dc.check_for_duplication(sub_parent_id_sql,(value, "", group_id)):
                dc.execute_query_single(sub_group_insert, (group_id, value, "", curr_timestamp, None))
                subgroup_id = dc.get_entity_id(sub_parent_id_sql, (value, "", group_id))
                dc.execute_query_single(sub_group_hist_insert, (value, "", group_id, subgroup_id, None, curr_timestamp))
    print('=================== Headers Processed ===================')

# process the countries data & store it into the database
def process_countries():
    print('=================== Processing Countries ===================')
    countries = fetch_countries()['countries_without_sup']
    master_sql = 'INSERT INTO `countries`(`name`, `updated_on`, `deleted_on`) VALUES (%s, %s, %s)'
    history_sql = 'INSERT INTO country_histories(name, version_id, country_id, created_on) VALUES (%s, %s, %s, %s)'
    country_qry = 'SELECT * from countries where name = %s limit 1'
    for country in countries:
        # insertion queries for countries & countries_histories
        if not dc.check_for_duplication('SELECT * from countries where name = %s limit 1', (country,)):
            dc.execute_query_single(master_sql, (country, curr_timestamp, None))
            country_id = get_country_id(country.strip())
            dc.execute_query_single(history_sql, (country, None, country_id, curr_timestamp))
    print('=================== Countries Processed ===================')

def store_note(note_index, note, part):
    note_insert = "INSERT INTO country_group_notes(note_index, note, part, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    note_hist_insert = "INSERT INTO country_group_notes_history(note_id, note_index, note, part, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s)"
    note_check = 'SELECT * from country_group_notes where note_index = %s and note = %s and part = %s limit 1'
    note_check_null = 'SELECT * from country_group_notes where note = %s and part = %s limit 1'
    if note_index is None:
        if not dc.check_for_duplication(note_check_null, (note, part)):
            dc.execute_query_single(note_insert, (note_index, note, part, curr_timestamp, None))
            note_id = dc.get_entity_id(note_check_null, (note, part))
            dc.execute_query_single(note_hist_insert, (note_id, note_index, note, part, None, curr_timestamp))
    else:
        if not dc.check_for_duplication(note_check, (note_index, note, part)):
            dc.execute_query_single(note_insert, (note_index, note, part, curr_timestamp, None))
            note_id = dc.get_entity_id(note_check, (note_index, note, part))
            dc.execute_query_single(note_hist_insert, (note_id, note_index, note, part, None, curr_timestamp))

# this method fetches notes & stores it into the database
def process_notes():
    print('=================== Processing Notes ===================')
    note_insert = "INSERT INTO country_group_notes(note_index, note, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    note_hist_insert = "INSERT INTO country_group_notes_history(note_id, note_index, note, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    note_check = 'SELECT * from country_group_notes where note_index = %s and note = %s limit 1'
    for div9 in bs_data.find_all("DIV9"):
        for div in div9.find_all("DIV", {"class":"table_foot"}):
            for p in div.find_all("P"):
                sup = int(p.find("sup").text)
                p.find("sup").decompose()
                note = p.text.strip()
                store_note(sup, note, '738')
    print('=================== Notes Processed ===================')


def fetch_group_from_subgroup(subgroup_id):
    group_by_subgroup_sql = 'SELECT group_id from sub_group_countries where id = %s limit 1'
    return dc.get_entity_id(group_by_subgroup_sql, (subgroup_id,))


def fetch_note_ids(group_id, subgroup_id, country_id):
    cgc_id_query = "SELECT note_ids from country_group_countries where group_id = %s and sub_group_id = %s and country_id = %s"
    try:
        note_ids = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
        data = json.loads(note_ids)
        return data
    except:
        return []


# this method fetches country_notes & stores into the database
def process_country_notes():
    print('=================== Processing Country Group Countries ===================')
    c_dict = fetch_countries()
    countries = c_dict['countries_without_sup']
    countries_with_sup = c_dict['countries_with_sup']
    cgc_insert = "INSERT INTO country_group_countries(group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cgc_hist_insert = "INSERT INTO country_group_countries_history(group_id, sub_group_id, country_id, cgc_id, is_present, note_ids, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cgc_note_update = "UPDATE country_group_countries SET note_ids = %s where id = %s"
    cgc_id_query = 'SELECT * from country_group_countries where group_id = %s and sub_group_id = %s and country_id = %s limit 1'
    sub_reasons_lst = fetch_sub_reasons()
    for index, value in enumerate(countries_with_sup):
        country = countries[index]
        country_id = get_country_id(country.strip())
        for index1, value1 in enumerate(sub_reasons_lst):
            parsed_note_ids = fetch_superscripts(value)
            subgroup_id = dc.get_entity_id('SELECT * from sub_group_countries where code = %s and title = %s limit 1', (value1, ''))
            group_id = fetch_group_from_subgroup(subgroup_id)
            note_ids = fetch_note_ids(group_id, subgroup_id, country_id)
            if len(note_ids) == 0:
                for id in parsed_note_ids:
                    note_ids.append(id)
            else:
                for id in parsed_note_ids:
                    if id not in note_ids:
                        note_ids.append(id)
            notes_str = str(note_ids)
            print(str(group_id) + " -> " + value1 + " -> " + country + " -> " + notes_str)
            if not dc.check_for_duplication(cgc_id_query, (group_id, subgroup_id, country_id)):
                dc.execute_query_single(cgc_insert, (group_id, subgroup_id, country_id, False, notes_str, curr_timestamp, None))
                cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, False, notes_str, None, curr_timestamp))
            else:
                entity = dc.get_entity(cgc_id_query, (group_id, subgroup_id, country_id))
                if entity[5] != notes_str:
                    cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                    dc.execute_query_single("DELETE FROM country_group_countries where id = %s", (cgc_id,))
                    dc.execute_query_single("INSERT INTO country_group_countries(id, group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (cgc_id, group_id, subgroup_id, country_id, False, str(note_ids), curr_timestamp, None))
                    dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, False, notes_str, None, curr_timestamp))
    print('=================== Country Group Countries Processed ===================')

# method to manage entries of sanctioned countries for e.g. Iran, Syria, Cuba, N. Korea
def get_sum(permission_arr):
    sum=0
    for per in permission_arr:
        if per == 'X':
            sum+=1
    return sum

# this method fetches permissions & stores into the database
def process_permissions():
    print('=================== Processing Permissions ===================')
    country_qry = 'SELECT * from countries where name = %s'
    country_chart_qry = 'SELECT * from country_chart where sub_reasons_for_control_id = %s and is_allowed = %s and country_id = %s'
    note_master_sql = 'INSERT INTO notes(id, content, updated_on, deleted_on) VALUES (%s, %s, %s, %s)'
    note_history_sql = 'INSERT INTO note_histories(content, note_id, created_on, version_id) VALUES (%s, %s, %s, %s)'
    country_note_master_qry = 'INSERT INTO country_note(country_id, note_id, updated_on, deleted_on) VALUES (%s, %s, %s, %s)'
    country_note_history_qry = 'INSERT INTO country_notes_histories(country_id, note_id, country_note_id, created_on, version_id) VALUES (%s, %s, %s, %s, %s)'
    find_country_note_qry = 'SELECT * from country_note where country_id = %s and note_id = %s'
    find_country_note_history = 'SELECT * from country_notes_histories where country_id = %s and note_id = %s and country_note_id = %s'
    group_by_subgroup_sql = 'SELECT group_id from sub_group_countries where id = %s limit 1'
    sub_parent_id_sql = 'SELECT * from sub_group_countries where code = %s and title = %s limit 1'
    cgc_insert = "INSERT INTO country_group_countries(group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cgc_hist_insert = "INSERT INTO country_group_countries_history(group_id, sub_group_id, country_id, cgc_id, is_present, note_ids, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cgc_id_query = "SELECT * from country_group_countries where group_id = %s and sub_group_id = %s and country_id = %s"
    cgc_update_permission = "UPDATE country_group_countries SET is_present = %s and note_ids = %s where id = %s"
    sub_reasons_lst = fetch_sub_reasons()
    c_dict = fetch_countries()
    countries = c_dict['countries_with_sup']
    countries_without_sup = c_dict['countries_without_sup']
    for index, value in enumerate(countries):
        permission_arr = fetch_values_for_country(value).strip().split(" ")
        if get_sum(permission_arr) > 0:
            for index1, sub_reason in enumerate(sub_reasons_lst):
                subgroup_id = dc.get_entity_id(sub_parent_id_sql, (sub_reason, ""))
                group_id = fetch_group_from_subgroup(subgroup_id)
                is_allowed = permission_arr[index1]=='O'
                country_id = get_country_id(countries_without_sup[index].strip())
                if not dc.check_for_duplication(cgc_id_query, (group_id, subgroup_id, country_id)):
                    dc.execute_query_single(cgc_insert, (group_id, subgroup_id, country_id, is_allowed, '[]', curr_timestamp, None))
                    cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                    dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, is_allowed, '[]', None, curr_timestamp))
                else:
                    note_ids = fetch_note_ids(group_id, subgroup_id, country_id)
                    notes_str = str(note_ids)
                    entity = dc.get_entity(cgc_id_query, (group_id, subgroup_id, country_id))
                    if entity[4] != int(is_allowed) or entity[5] != notes_str:
                        cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                        dc.execute_query_single("DELETE FROM country_group_countries where id = %s", (cgc_id,))
                        dc.execute_query_single("INSERT INTO country_group_countries(id, group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (cgc_id, group_id, subgroup_id, country_id, is_allowed, notes_str, curr_timestamp, None))
                        dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, is_allowed, notes_str, None, curr_timestamp))
        else:
            note = fetch_values_for_country(value).strip()
            store_note(None, note, '738')
            country_id = get_country_id(countries_without_sup[index].strip())
            note_id = dc.get_entity_id('SELECT * from country_group_notes where note = %s and note_index is null limit 1', (note,))
            for index2, sub_reason in enumerate(sub_reasons_lst):
                subgroup_id = dc.get_entity_id(sub_parent_id_sql, (sub_reason, ""))
                group_id = fetch_group_from_subgroup(subgroup_id)
                is_allowed = False
                country_id = get_country_id(countries_without_sup[index].strip())
                # insertion queries for country_chart & country_chart_histories
                note_ids = fetch_note_ids(group_id, subgroup_id, country_id)
                if len(note_ids) == 0:
                    note_ids.append(note_id)
                else:
                    if note_id not in note_ids:
                        note_ids.append(note_id)
                if not dc.check_for_duplication(cgc_id_query, (group_id, subgroup_id, country_id)):
                    dc.execute_query_single(cgc_insert, (group_id, subgroup_id, country_id, is_allowed, str(note_ids), curr_timestamp, None))
                    cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                    dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, is_allowed, str(note_ids), None, curr_timestamp))
                else:
                    notes_str = str(note_ids)
                    entity = dc.get_entity(cgc_id_query, (group_id, subgroup_id, country_id))
                    if entity[4] != int(is_allowed) or entity[5] != notes_str:
                        cgc_id = dc.get_entity_id(cgc_id_query, (group_id, subgroup_id, country_id))
                        dc.execute_query_single("DELETE FROM country_group_countries where id = %s", (cgc_id,))
                        dc.execute_query_single("INSERT INTO country_group_countries(id, group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
                        cgc_id, group_id, subgroup_id, country_id, is_allowed, notes_str, curr_timestamp, None))
                        dc.execute_query_single(cgc_hist_insert, (
                        group_id, subgroup_id, country_id, cgc_id, is_allowed, notes_str, None, curr_timestamp))
    print('=================== Permissions Processed ===================')

def fetch_superscripts_for_heading(th):
    superscripts_list = list()
    for sup in th.find_all("sup"):
        superscripts_list.append(int(sup.text.strip()))
    return superscripts_list

def process_country_groups():
    part = '740'
    group_insert = "INSERT INTO group_countries(code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    group_hist_insert = "INSERT INTO group_countries_history(code, title, group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    sub_group_insert = "INSERT INTO sub_group_countries(group_id, code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    sub_group_hist_insert = "INSERT INTO sub_group_countries_history(code, title, group_id, sub_group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s)"
    for maindiv in bs_data1.find_all("DIV9"):
        for hd1 in maindiv.find_all("HD1"):
            if hd1.find_next_sibling("SCOL2") is not None:
                process_cg_country(hd1, hd1.find_next_sibling("SCOL2"))
            else:
                process_cg_country(hd1, None)
        for div in maindiv.find_all("DIV", {"width": "100%"}):
            group = ''
            group_id = ''
            notes_dict = {}
            superscpt = ''
            group_notes = {}
            headers_list = list()
            cg_note = dict()
            for p in div.find_all("P", {"class": "gpotbl_note"}):
                if p != None:
                    if p.find("sup"):
                        superscpt = p.find("sup").text.strip()
                        notes_dict[superscpt] = str(p).replace('<P class="gpotbl_note">',"").replace("</P>","").replace(str(p.find("sup")), "").strip()
                    else:
                        notes_dict[superscpt] += str(p).replace('<P class="gpotbl_note">',"").replace("</P>","").strip()
            process_notes1(notes_dict)
            for div1 in div.find_all("P", {"class": "gpotbl_title"}):
                if div1.text.strip().startswith("Country Group"):
                    group_note = "" if div1.find("sup") is None else div1.find("sup").text.strip()
                    group = div1.text.replace(group_note,"").strip()
                    code = group.replace("Country Group", "").strip()
                    if not dc.check_for_duplication("SELECT * from group_countries where code = %s and title = %s", (code, group)):
                        dc.execute_query_single(group_insert, (code, group, curr_timestamp, None))
                        group_id = dc.get_entity_id("SELECT * from group_countries where code = %s and title = %s", (code, group))
                        dc.execute_query_single(group_hist_insert, (code, group, group_id, None, curr_timestamp))
                    group_id = dc.get_entity_id("SELECT * from group_countries where code = %s and title = %s", (code, group))
                    if div1.find("sup") is not None:
                        cg_note[group_id] = int(div1.find("sup").text.strip())
            group_notes[group] = notes_dict
            print("==============================================================")
            for table in div.find_all("TABLE", {"class": "gpotbl_table"}):
                headers_list = list()
                sub_notes = dict()
                for th in table.find_all("TH"):
                    th_string = th.text.strip()
                    if th_string.lower() != "country":
                        sub_sup = ''
                        if th.find("sup") is not None:
                            sub_sup = th.find("sup").text.strip()
                        th_text = th.text.split("]")
                        th_code = th_text[0].strip() + "]"
                        if ":" in th_code:
                            th_code = th_code.split(":")[0].strip() + ":" + th_code.split(":")[1].strip()
                        th_code = th_code.replace("[", "").replace("]", "").strip()
                        th_desc = th_text[1].replace(sub_sup, "").strip()
                        if not dc.check_for_duplication("SELECT * from sub_group_countries where code = %s and title = %s and group_id = %s", (th_code, th_desc, group_id)):
                            group_id = dc.get_entity_id("SELECT * from group_countries where title = %s", (group,))
                            dc.execute_query_single(sub_group_insert, (group_id, th_code, th_desc, curr_timestamp, None))
                            subgroup_id = dc.get_entity_id("SELECT * from sub_group_countries where code = %s and title = %s", (th_code, th_desc))
                            headers_list.append(subgroup_id)
                            dc.execute_query_single(sub_group_hist_insert, (th_code, th_desc, group_id, subgroup_id, None, curr_timestamp))
                        if th.find("sup") is not None:
                            superscript = th.find("sup").text.strip()
                            heading_id = dc.get_entity_id("SELECT * from sub_group_countries where code = %s and title = %s", (th_code, th_desc))
                            sub_notes[heading_id] = int(superscript)
                for tr in table.find_all("TR"):
                    group_id = dc.get_entity_id("SELECT * from group_countries where title = %s", (group,))
                    td_text = list()
                    if headers_list == []:
                        headers = dc.execute_select_query("SELECT id from sub_group_countries where group_id = %s", (group_id,))
                        for head in headers:
                            headers_list.append(head[0])
                    country = ''
                    for index, td in enumerate(tr.find_all("TD")):
                        if index == 0:
                            country = td.text.strip()
                        else:
                            td_text.append("O" if td.text.strip() == "" else td.text.strip())
                    process_allowance(country, td_text, headers_list, group_id, notes_dict, sub_notes, cg_note)


def get_country_id(country_name):
    country_sql = "select id, name, synonyms from countries"
    result = dc.execute_select_query(country_sql, ())
    for country in result:
        if country_name == country[1]:
            return country[0]
        if country[2] is not None:
            data = json.loads(country[2])
            for syno in data:
                if country_name == syno:
                    return country[0]
    return 0


def write_exceptional_data(data_string):
    file_name = "xml_files/exceptions/exception_entries.txt"
    f = open(file_name, 'a')
    f.write(str(curr_timestamp) + " -> " + data_string + "\n")
    f.close()


def process_cg_country(p, uls):
    group_insert = "INSERT INTO group_countries(code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    group_hist_insert = "INSERT INTO group_countries_history(code, title, group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    cgc_insert = "INSERT INTO country_group_countries(group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cgc_hist_insert = "INSERT INTO country_group_countries_history(group_id, sub_group_id, country_id, cgc_id, is_present, note_ids, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    group = p.text.replace("Countries","").replace("-","").strip()
    code = group.replace("Country Group", "").strip()
    if not dc.check_for_duplication("SELECT * from group_countries where code = %s and title = %s", (code, group)):
        dc.execute_query_single(group_insert, (code, group, curr_timestamp, None))
        group_id = dc.get_entity_id("SELECT * from group_countries where code = %s and title = %s", (code, group))
        dc.execute_query_single(group_hist_insert, (code, group, group_id, None, curr_timestamp))
    group_id = dc.get_entity_id("SELECT * from group_countries where code = %s and title = %s", (code, group))
    if uls is not None:
        li_text = ""
        for li in uls.find_all("LI"):
            if li.find_next_sibling("LI") is not None:
                if li.find_next_sibling("LI").text.startswith(" "):
                    li_text = li.text
                    li_text += li.find_next_sibling("LI").text
                    write_exceptional_data("Country name found divided in two <LI> tags: " + li_text + " in Part-740")
                    li.find_next_sibling("LI").decompose()
                else:
                    li_text = li.text
            else:
                li_text = li.text
            if li_text.strip() != "":
                country_id = get_country_id(li_text.strip())
                if not dc.check_for_duplication("SELECT * from country_group_countries where country_id = %s and group_id = %s", (country_id, group_id)):
                    dc.execute_query_single(cgc_insert, (group_id, None, country_id, True, '[]', curr_timestamp, None))
                    cgc_id = dc.get_entity_id("SELECT * from country_group_countries where country_id = %s and group_id = %s", (country_id, group_id))
                    dc.execute_query_single(cgc_hist_insert, (group_id, None, country_id, cgc_id, True, '[]', None, curr_timestamp))


def process_notes1(notes_dict):
    for key in notes_dict.keys():
        store_note(key, notes_dict.get(key), '740')


def process_country_notes1(country, sup_lst, notes_dict, group_id):
    for sup in sup_lst:
        country = country.replace(str(sup),"")
    country_id = get_country_id(country.strip())
    cn_sql = "INSERT INTO cg_country_note(group_id, country_id, note_id, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    cnh_sql = "INSERT INTO cg_country_note_history(version_id, group_id, country_id, note_id, cg_country_note_id, created_on) VALUES (%s, %s, %s, %s, %s, %s)"
    for sup1 in sup_lst:
        note_id = dc.get_entity_id("SELECT * from notes where content = %s", (notes_dict.get(str(sup1)),))
        if not dc.check_for_duplication("SELECT * from cg_country_note where group_id = %s and country_id = %s and note_id = %s", (cg_id, country_id, note_id)):
            cn_val = (cg_id, country_id, note_id, curr_timestamp, None)
            dc.execute_query_single(cn_sql, cn_val)

            cn_id = dc.get_entity_id("SELECT * from cg_country_note where group_id = %s and country_id = %s and note_id = %s", (cg_id, country_id, note_id))
            cnh_val = (None, cg_id, country_id, note_id, cn_id, curr_timestamp)
            dc.execute_query_single(cnh_sql, cnh_val)


def get_note_text(notes_dict, superscript):
    for item in notes_dict.items():
        if str(item[0]) == str(superscript):
            return item[1]
    return ""

def process_allowance(country, td_text, header_ids, group_id, notes_dict, sub_notes, cg_notes):
    cgc_insert = "INSERT INTO country_group_countries(group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cgc_hist_insert = "INSERT INTO country_group_countries_history(group_id, sub_group_id, country_id, cgc_id, is_present, note_ids, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    fetch_note_query = "SELECT * from country_group_notes where note_index = %s and note = %s"
    cgc_check = "SELECT * from country_group_countries where group_id = %s and country_id = %s and sub_group_id = %s and is_present = %s limit 1"
    sup_list = fetch_superscripts(country.strip())
    sub_ids = list()
    subgroup_note = dict()
    for key in sub_notes: # fetching sub_group ids
        sub_ids.append(key)
    header_lst = list()
    for h in header_ids:
        header_lst.append(h)
    if len(sup_list) > 0:
        for sup in sup_list:
            country = country.replace(str(sup),"")
    for key in sub_notes:
        if key in header_lst:
            superscript = sub_notes[key]
            note_text = get_note_text(notes_dict, superscript)
            if note_text != "":
                note_id = dc.get_entity_id(fetch_note_query, (superscript, note_text))
                subgroup_note[key] = note_id
    store_country_details(country.strip())
    country_id = get_country_id(country.strip())
    for index, td in enumerate(td_text): # iterating for each permission
        temp_notes = list()
        is_allowed = td_text[index]=='O'
        subgroup_id = header_ids[index]
        if is_allowed == True:
            if subgroup_id in subgroup_note.keys():
                note_id = subgroup_note[subgroup_id]
                temp_notes.append(note_id)
        for key in notes_dict.keys():
            if int(key) in sup_list:
                note_id = dc.get_entity_id(fetch_note_query, (key, notes_dict.get(key)))
                temp_notes.append(note_id)
        for key in cg_notes:
            superscript = cg_notes[key]
            note_text = get_note_text(notes_dict, superscript)
            if note_text != "":
                note_id = dc.get_entity_id(fetch_note_query, (superscript, note_text))
                temp_notes.append(note_id)
        print((group_id, country_id, subgroup_id, is_allowed, temp_notes))
        if not dc.check_for_duplication(cgc_check, (group_id, country_id, subgroup_id, is_allowed)):
            note_str = str(list(set(temp_notes)))
            dc.execute_query_single(cgc_insert, (group_id, subgroup_id, country_id, is_allowed, note_str, curr_timestamp, None))
            cgc_id = dc.get_entity_id(cgc_check, (group_id, country_id, subgroup_id, is_allowed))
            dc.execute_query_single(cgc_hist_insert, (group_id, subgroup_id, country_id, cgc_id, is_allowed, note_str, None, curr_timestamp))

def store_supplement_details(supplement_text):
    group_insert = "INSERT INTO group_countries(code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    group_hist_insert = "INSERT INTO group_countries_history(code, title, group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    group_id = 0
    if not dc.check_for_duplication("SELECT * from group_countries where title = %s", (supplement_text,)):
        dc.execute_query_single(group_insert, ("", supplement_text, curr_timestamp, None))
        group_id = dc.get_entity_id("SELECT * from group_countries where title = %s", (supplement_text,))
        dc.execute_query_single(group_hist_insert, ("", supplement_text, group_id, None, curr_timestamp))
    return group_id

def store_group_country_details(group_id, country_id, note_ids):
    cgc_insert = "INSERT INTO country_group_countries(group_id, sub_group_id, country_id, is_present, note_ids, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cgc_hist_insert = "INSERT INTO country_group_countries_history(group_id, sub_group_id, country_id, cgc_id, is_present, note_ids, version_id, created_on) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    if not dc.check_for_duplication("SELECT * from country_group_countries where group_id = %s and country_id = %s", (group_id, country_id)):
        dc.execute_query_single(cgc_insert, (group_id, None, country_id, True, str(note_ids), curr_timestamp, None))
        cgc_id = dc.get_entity_id("SELECT * from country_group_countries where group_id = %s and country_id = %s", (group_id, country_id))
        dc.execute_query_single(cgc_hist_insert, (group_id, None, country_id, cgc_id, True, str(note_ids), None, curr_timestamp))

def store_country_details(country_name):
    country_id = 0
    if country_name.strip() != "" and get_country_id(country_name) == 0:
        c_sql = 'INSERT INTO countries(name, updated_on, deleted_on) VALUES (%s, %s, %s)'
        ch_sql = 'INSERT INTO country_histories(name, version_id, country_id, created_on) VALUES (%s, %s, %s, %s)'
        dc.execute_query_single(c_sql, (country_name, curr_timestamp, None))

        country_id = get_country_id(country_name)
        dc.execute_query_single(ch_sql, (country_name, None, country_id, curr_timestamp))
    return country_id

def process_waps():
    part = "743"
    supplement = part743_data.find("HEAD").text.strip()
    code = supplement.split("Part " + part)[0].replace("-", "").strip() + " Part " + part
    supplement_text = supplement.replace(code, "").replace("-", "").strip()
    id = store_supplement_details(supplement_text)
    sup_id = id if id!=0 else dc.get_entity_id("SELECT * from group_countries where title = %s", (supplement_text,))
    for maindiv in part743_data.find_all("DIV9"): #, {"class": "appendix"}):
        for scol2 in maindiv.find_all("SCOL2"):
            for li in scol2.find_all("LI"):
                if li.find_next_sibling("LI") is not None:
                    if li.find_next_sibling("LI").text.startswith(" "):
                        li_text = li.text
                        li_text += li.find_next_sibling("LI").text
                        write_exceptional_data(
                            "Country name found divided in two <LI> tags: " + li_text + " in Part-" + part)
                        li.find_next_sibling("LI").decompose()
                    else:
                        li_text = li.text
                else:
                    li_text = li.text
                if li_text.strip() != "":
                    country_id = store_country_details(li_text.strip()) if get_country_id(li_text.strip()) == 0 else get_country_id(li_text.strip())
                    store_group_country_details(sup_id, country_id, [])

def process_state_parties():
    part = "745"
    master_qry = 'INSERT INTO country_note(country_id, note_id, updated_on, deleted_on) VALUES (%s, %s, %s, %s)'
    history_qry = 'INSERT INTO country_notes_histories(country_id, note_id, country_note_id, created_on, version_id) VALUES (%s, %s, %s, %s, %s)'
    supplement = part745_data.find("HEAD").text
    code = supplement.split("Part " + part)[0].replace("-", "").strip() + " Part " + part
    supplement_text = supplement.replace(code, "").replace("-", "").strip()
    id = store_supplement_details(supplement_text)
    sup_id = id if id!=0 else dc.get_entity_id("SELECT * from group_countries where title = %s", (supplement_text,))
    note_dict = {}
    for maindiv in part745_data.find_all("DIV9"):
        for p in maindiv.find_all("P"):
            if p.text.strip().startswith("*"):
                note_code = p.text.strip().split(" ")[0]
                store_note(note_code, p.text.replace(note_code, "").strip(), part)
        for p in maindiv.find_all("FP-1"):
            if p.text.strip().endswith("*"):
                length = len(p.text.strip().split(' '))
                note_start = p.text.strip().split(' ')[length-1]
                note_dict[note_start] = ""
                note_ids = list()
                note_id = dc.get_entity_id("SELECT * from country_group_notes where note_index = %s and part = %s", (note_start, part))
                note_ids.append(note_id)
                country_name = p.text.replace("*", "").strip()
                country_id = store_country_details(country_name) if get_country_id(country_name) == 0 else get_country_id(country_name)
                store_group_country_details(sup_id, country_id, note_ids)
            else:
                country_id = store_country_details(p.text.strip()) if get_country_id(p.text.strip()) == 0 else get_country_id(p.text.strip())
                store_group_country_details(sup_id, country_id, [])

def store_UN_Controls_as_group(group):
    part = '746'
    group_insert = "INSERT INTO group_countries(code, title, updated_on, deleted_on) VALUES (%s, %s, %s, %s)"
    group_hist_insert = "INSERT INTO group_countries_history(code, title, group_id, version_id, created_on) VALUES (%s, %s, %s, %s, %s)"
    group_id = 0
    if not dc.check_for_duplication("SELECT * from group_countries where title = %s", (group,)):
        dc.execute_query_single(group_insert, ("", group, curr_timestamp, None))
        group_id = dc.get_entity_id("SELECT * from group_countries where title = %s", (group,))
        dc.execute_query_single(group_hist_insert, ("", group, group_id, None, curr_timestamp))

def process_un_controls_country_group(supplement_text):
    # paragraph_code = url_part746_b_2.split("#")[1].replace("p-", "").strip()
    group_qry = "SELECT * from group_countries where title = %s"
    group_id = dc.get_entity_id(group_qry, (supplement_text,))
    p_text = ''
    for p in part746_data.find_all("P"):
        if p.text.startswith("(b)"):
            if p.find_next_sibling("P").text.startswith("(2)"):
                p_text = p.find_next_sibling("P").text.replace("and", ",").replace(".", "")
    p_text = p_text.split(":")[1]
    for data in p_text.split(","):
        if data.strip() != "":
            country_id = get_country_id(data.strip())
            store_group_country_details(group_id, country_id, [])

def process_part738():
    process_countries()
    process_headers()
    process_notes()
    process_country_notes()
    process_permissions()
    print("Processed Supplement No. 1 to Part 738 - Commerce Country Chart")

def process_part740():
    process_country_groups()
    print("Processed Supplement No. 1 to Part 740 - Country Groups")

def process_part743():
    process_waps()
    print("Processed Supplement No. 1 to Part 743 - Wassenaar Arrangement Participating States")

def process_part745():
    process_state_parties()
    print("Processed Supplement No. 2 to Part 745 - States Parties to the "
          "Convention on the Prohibition of the Development, Production, "
          "Stockpiling, and Use of Chemical Weapons and on Their Destruction")

def process_part746_b_2():
    print("Processing Sanctions on arms embargoes to specific destinations.")
    store_UN_Controls_as_group("UN Controls")
    process_un_controls_country_group("UN Controls")
    print("Processed Sanctions on arms embargoes to specific destinations.")

# process_part738()
process_part740()
# process_part743()
# process_part745()
# process_part746_b_2()