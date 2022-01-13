import datetime
import urllib.request
from bs4 import BeautifulSoup as bs
import database_operations as dc
import json
import hashlib
import usml_utilities as u
import lxml

today = str(datetime.date.today()) #- datetime.timedelta(days=1))
curr_timestamp = datetime.datetime.now().replace(microsecond=0)
bs_data = ""

db = dc.connect_db()


def fetch_all_refs_to_parse():
    mycursor = db.cursor()
    mycursor.execute("SELECT * from references_to_parse", ())
    result = mycursor.fetchall()
    return result


def process_subp(subP, div_id):
    data = None
    # ph = subP.find("span", {"class": "paragraph-hierarchy"}).text.strip()
    if subP.find("em") is not None:
        headingTag = subP.find_all("em")[0]
        heading = ""
        if headingTag.has_attr("class") and headingTag.get("class")[0] == "paragraph-heading":
            heading = headingTag.text.strip()
        if subP.find("div") is not None:
            content = subP.find_all("div").first.text.replace(heading, "").replace("\n", "").replace("()", "").strip()
            # content = content.strip()[len(ph)-1:] if content.startswith(ph) else content.strip()
            data = {"heading": heading, "content": "" if content.strip() == "-" else content.strip()}
        else:
            content = subP.text.replace(heading, "").replace("\n", "").replace("()", "").strip()
            # content = content.strip()[len(ph)-1:] if content.startswith(ph) else content.strip()
            data = {"heading": heading, "content": "" if content.strip() == "-" else content.strip()}
    else:
        content = subP.text.replace("\n", "").replace("()", "").strip()
        # content = content.strip()[len(ph)-1:] if content.startswith(ph) else content.strip()
        data = {"content": "" if content.strip() == "-" else content.strip()}
    return data


def get_shortest_index(index_list):
    if len(index_list) > 0:
        min = list(index_list.values())[0]
        for key in index_list:
            if index_list[key] < min:
                min = index_list[key]
        return min
    else:
        return 0


def fetch_references():
    parsed_ref = "INSERT INTO parsed_references(reference_id, parsed_json_data, parsed_hash_data, updated_on, deleted_on) VALUES (%s, %s, %s, %s, %s)"
    parsed_ref_hist = "INSERT INTO parsed_references_history(version_id, reference_id, parsed_references_id, parsed_json_data, parsed_hash_data, created_on) VALUES (%s, %s, %s, %s, %s, %s)"
    select_parsed_ref = "SELECT * from parsed_references where reference_id = %s and parsed_hash_data = %s"
    result = fetch_all_refs_to_parse()
    for res in result:
        ref_id = res[0]
        ref_text = res[1]
        link = res[2].replace("current", today)
        length = len(link.split("/"))
        sectionNo = ref_text
        file = do_file_operations(ref_text + "_" + today, link)
        bs_data = fetch_xml_content(file)
        for div in bs_data.find_all("DIV8"):
            main_text = None
            if div.find("h8") is not None:
                if div.find("h8").find_next_sibling("p") is not None:
                    pTag = div.find("h8").find_next_sibling("p")
                    if pTag.get("class") is None:
                        main_text = div.find("h8").find_next_sibling("p").text.strip()
            numberings = list()
            content_dict = {}
            numbering_dict = {}
            if link.find("#") == -1:
                d_title = sectionNo = sectionNo.replace("section-", "")
                pTags = div.find_all('P')
                for index, p in enumerate(pTags):
                    if index == 0 and (not p.text.strip().startswith("(")):
                        print("Main Text: " + p.text)
                    else:
                        if p.find("I") is not None:
                            for i_tag in p.find_all("I"):
                                print(i_tag)
                                bracket_string = str(p).split(str(i_tag))[0].replace("<P>", "").replace("(", "").replace(")", "").strip()
                                if "-" in bracket_string:
                                    bracket_string = bracket_string.split("-")[1].strip()
                                numberings.append(bracket_string)
                        else:
                            if p.text.strip().startswith("("):
                                i_index = p.text.strip().split(")")[0] + ")".strip()
                                numberings.append(i_index)
                    print("--------------------------------------------------------")
                    # if p.has_attr('data-title'):
                    #     numberings.append(p.get("data-title").replace(d_title, "").replace("<em>", "").replace("</em>", ""))
                print(numberings)
                numberings = u.process_indexes(numberings)
                print(numberings)
                for div1 in div.findAll('div'):
                    if div1.has_attr('id'):
                        if div1.get("id").find("foot") == -1:
                            div_id = div1.get("id").replace("p-", "").replace(sectionNo, "")
                            subP = div1.select_one("p", {"id": div1.get("id")})
                            content_dict[div_id] = process_subp(subP, div_id)
                for n in numberings:
                    numbering_dict[n] = len(n.split(")"))-1
            # else:
            #     txt_remove = sectionNo.split("#")[1].split("(")[0]
            #     d_title = txt_remove.replace("p-", "")
            #     pTags = div.findAll('p')
            #     for p in pTags:
            #         if p.has_attr('data-title'):
            #             if p.get("data-title").startswith(sectionNo.split("#")[1].replace("p-", "")):
            #                 numberings.append(p.get("data-title").replace("<em>", "").replace("</em>", "").replace(d_title, ""))
            #     for div1 in div.findAll('div'):
            #         if div1.has_attr('id'):
            #             if div1.get("id").find("foot") == -1:
            #                 if div1.get("id").startswith(sectionNo.split("#")[1]):
            #                     div_id = div1.get("id").replace(txt_remove, "")
            #                     subP = div1.select_one("p", {"id": div1.get("id")})
            #                     content_dict[div_id] = process_subp(subP, div_id)
            #
            #     for n in numberings:
            #         numbering_dict[n] = len(n.split(")")) - 1
            main_points = list()
            level1 = list()
            level2 = list()
            level3 = list()
            min_val = get_shortest_index(numbering_dict)
            for i in content_dict:
                if numbering_dict[i] == min_val:
                    main_points.append(i)
                if numbering_dict[i] == min_val+1:
                    level1.append(i)
                if numbering_dict[i] == min_val+2:
                    level2.append(i)
                if numbering_dict[i] == min_val+3:
                    level3.append(i)
            json_data = process_content_dict(sectionNo, content_dict, main_points, level1, level2, level3, main_text)
            print(json_data)
            hash_object = hashlib.sha1(json_data.encode())
            print("----------------------------------------------------------------------------------------------")
            hashed_data = hash_object.hexdigest()
            print(hashed_data)

            if not dc.check_for_duplication(select_parsed_ref, (ref_id, hashed_data)):
                dc.execute_query_single(parsed_ref, (ref_id, json_data, hashed_data, curr_timestamp, None))
                parsed_ref_id = dc.get_entity_id(select_parsed_ref, (ref_id, hashed_data))
                dc.execute_query_single(parsed_ref_hist, (None, ref_id, parsed_ref_id, json_data, hashed_data, curr_timestamp))


def process_recursive_content(content_dict):
    keys = list()
    for main_key in content_dict:
        abc = {}
        for sub_key in content_dict:
            if main_key != sub_key and sub_key.startswith(main_key):
                if content_dict[sub_key].get("heading") is None:
                    abc[sub_key] = {"content": content_dict[sub_key]["content"]}
                else:
                    abc[sub_key] = {"heading": content_dict[sub_key]["heading"], "content": content_dict[sub_key]["content"]}
                content_dict[main_key] = {"heading": (
                    "" if content_dict[main_key].get("heading") is None else content_dict[main_key]["heading"]),
                    "content": str(content_dict[main_key]["content"]), "subpoints": abc}
                keys.append(str(sub_key))
    for key in set(keys):
        if content_dict.get(key):
            del content_dict[key]


def process_content_dict(sectionNo, content_dict, root, level1, level2, level3, main_text):
    process_recursive_content(content_dict)
    for r in root:
        if content_dict[r].get("subpoints") is not None:
            process_recursive_content(content_dict[r].get("subpoints"))
        for p in level1:
            if content_dict[r].get("subpoints") is not None:
                if content_dict[r]["subpoints"].get(p) is not None:
                    if content_dict[r]["subpoints"][p].get("subpoints") is not None:
                        process_recursive_content(content_dict[r]["subpoints"][p]["subpoints"])
                    for p1 in level2:
                        if content_dict[r].get("subpoints") is not None:
                            if content_dict[r]["subpoints"].get(p) is not None:
                                if content_dict[r]["subpoints"][p].get("subpoints") is not None:
                                    if content_dict[r]["subpoints"][p]["subpoints"].get(p1) is not None:
                                        if content_dict[r]["subpoints"][p]["subpoints"][p1].get("subpoints") is not None:
                                            process_recursive_content(content_dict[r]["subpoints"][p]["subpoints"][p1]["subpoints"])
                                        for p2 in level3:
                                            if content_dict[r].get("subpoints") is not None:
                                                if content_dict[r]["subpoints"].get(p) is not None:
                                                    if content_dict[r]["subpoints"][p].get("subpoints") is not None:
                                                        if content_dict[r]["subpoints"][p]["subpoints"].get(p1) is not None:
                                                            if content_dict[r]["subpoints"][p]["subpoints"][p1].get("subpoints") is not None:
                                                                if content_dict[r]["subpoints"][p]["subpoints"][p1]["subpoints"].get(p2) is not None:
                                                                    if content_dict[r]["subpoints"][p]["subpoints"][p1]["subpoints"][p2].get("subpoints") is not None:
                                                                        process_recursive_content(content_dict[r]["subpoints"][p]["subpoints"][p1]["subpoints"][p2]["subpoints"])
    if sectionNo.find("#") == -1:
        if main_text is not None:
            return json.dumps({sectionNo: {"content": main_text, "subpoints": content_dict}})
        else:
            return json.dumps({sectionNo: {"subpoints": content_dict}})
    else:
        return json.dumps(content_dict)


def fetch_data_from_url(link):
    file = urllib.request.urlopen(link)
    data = file.read()
    file.close()
    return str(data, "UTF-8")


def do_file_operations(file, link):
    file_name = "xml_files/ref1/" + file + ".xml"
    f = open(file_name, "w")
    f.write(fetch_data_from_url(link))
    f.close()
    return file_name


def fetch_xml_content(file):
    with open(file, 'r') as f:
        xml_data = f.readlines()
        xml_data = "".join(xml_data)
        bs_data = bs(xml_data.replace("\\n", "").replace("<I>and</I>", "and").replace("<I>or</I>", "or"), "lxml-xml")
    return bs_data

fetch_references()
