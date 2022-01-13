import datetime
import urllib.request
from bs4 import BeautifulSoup as bs
import database_operations as dc
import lxml

curr_timestamp = datetime.datetime.now().replace(microsecond=0)
today = str(datetime.date.today())  # - datetime.timedelta(days=1))
terms_url = 'https://www.ecfr.gov/api/versioner/v1/full/' + today + '/title-15.xml?chapter=VII&part=772&subchapter=C&subtitle=B'

# db = dc.connect_db()


# call the URL & collect response
def fetch_data_from_url(url):
    file = urllib.request.urlopen(url)
    data = file.read()
    file.close()
    #string = str(data).encode('utf-8')
    return str(data, "UTF-8")


# method to sanitize string & remove unnecessary characters
def clean_string(string):
    return string.replace('\\xe2\\x80\\x9c', '"').replace('\\xe2\\x80\\x9d', '"').replace("\\n", "")\
        .replace("\\xc2\\xa7", "§").replace("\\xe2\\x80\\x98", "‘").replace("\\xc3\\x97", "×")\
        .replace("\\xe2\\x80\\x99", "’").replace("\\'", "'").replace("\\xc2\\xb0", "°").replace("\\xc2\\xb1", "±")\
        .replace("\\xe2\\x86\\x91", "").replace("\\xe2\\x86\\x93", "").replace("\\xe2\\x88\\x92", "").strip()


# store the response into an XML file in string format
def do_file_operations(path):
    file_name = constants.dir_name + "definitions/" + today + ".xml"
    # file_name = "xml_files/" + path + today + ".xml"
    f = open(file_name, "w")
    f.write(clean_string(fetch_data_from_url(terms_url)))
    f.close()
    return file_name


file_name = do_file_operations()


# reading the XML file that we just stored
def fetch_xml_content(file):
    with open(file, 'r') as f:
        xml_data = f.readlines()
        xml_data = "".join(xml_data)
        _bs_data = bs(xml_data.replace("\\n", "").replace("<I>and</I>", "and").replace("<I>or</I>", "or"), "lxml-xml")
    return _bs_data


bs_data = fetch_xml_content(file_name)


# method to extract bracket text from the definition text
def process_bracket_text(definition):
    start_ind = definition.find("(Cat")
    if start_ind > -1:
        end_ind = definition.find(")", start_ind)
        return definition[start_ind:end_ind + 1]
    else:
        return ""


# method to store notes against given term_id
def store_term_notes(term_id, notes):
    term_note_sql = "INSERT INTO term_definition_notes(term_id, note_index, note_text, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    term_note_qry = "SELECT * from term_definition_notes where term_id = %s and note_index = %s and note_text = %s"
    for note in notes:
        note_index = note[0]
        note_text = note[1]
        if not dc.check_for_duplication(term_note_qry, (term_id, note_index, note_text)):
            val = (term_id, note_index, note_text, curr_timestamp, None)
            dc.execute_query_single(term_note_sql, val)


# method to store terms & it's definition to the db
def store_term_definition(term, bracket_text, definition, notes):
    term_sql = "INSERT INTO term_definition(term_text, bracket_text, definition, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    term_qry = "SELECT * from term_definition where term_text = %s and bracket_text = %s"
    if not dc.check_for_duplication(term_qry, (term, bracket_text)):
        val = (term, bracket_text, definition, curr_timestamp, None)
        dc.execute_query_single(term_sql, val)
        if len(notes) > 0:
            term_id = dc.get_entity_id(term_qry, (term, bracket_text))
            store_term_notes(term_id, notes)


# process note/s for a <P> tag
def process_note(p_tag):
    notes = []
    if p_tag.find_next_siblings("NOTE") is not None:
        for sib in p_tag.find_next_siblings():
            if sib.name == 'NOTE':
                note_text = ''
                note_index = clean_string(sib.find("HED").text)
                for p in sib.find_all("P"):
                    note_text += p.text.strip() + " "
                notes.append((note_index, note_text.strip()))
            else:
                break
    return notes


# driver method to parse the document
def process_term_definitions():
    for div5 in bs_data.find_all("DIV8"):
        for index, p in enumerate(div5.find_all("P")):
            if index != 0:
                if p.find("I") is not None and p.find_parent().name != "NOTE":
                    span = p.find("I")
                    print("-----------------------------------------------")
                    span_text = span.text.replace("”", "")
                    span_def = clean_string(p.text.strip().replace(span_text, ""))
                    for sibling in p.find_next_siblings("P"):
                        if not sibling.find("I"):
                            if not sibling.text.startswith("“"):
                                span_def += clean_string(sibling.text) + " "
                                sibling.decompose()
                        else:
                            break
                    term = clean_string(span_text).rstrip(".")
                    bracket_text = process_bracket_text(span_def.strip())
                    definition = span_def.replace(bracket_text, "").strip().lstrip("-").lstrip(".")
                    bracket_text = bracket_text.replace(" part ", "P").replace(" Part ", "P").replace(", Part II", "P2").replace("(", "").replace(")", "").replace("Cat", "").replace(", and", ",").replace(" and", ",")
                    definition = definition.strip().replace("“”.", "").replace("“”", "")
                    notes = process_note(p)
                    if definition != "":
                        store_term_definition(term, bracket_text, definition, notes)


process_term_definitions()
