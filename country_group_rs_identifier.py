import database_operations as dc
import json


db = dc.connect_db()


def get_country_id(country_name):
    country_sql = "select id, name, synonyms from countries"
    mycursor = db.cursor()
    mycursor.execute(country_sql, ())
    result = mycursor.fetchall()
    for country in result:
        if country_name == country[1]:
            return country[0]
        if country[2] is not None:
            data = json.loads(country[2])
            for syno in data:
                if country_name == syno:
                    return country[0]
    return 0


def get_group_id(group_name):
    group_sql = "select id, code from group_countries"
    mycursor = db.cursor()
    mycursor.execute(group_sql, ())
    result = mycursor.fetchall()
    for group in result:
        group_word = group[1].strip()
        if group_name == group_word:
            return group[0]
    return 0


def determineCountryGroupOrCountry(text):
    # Canada
    # returns {country_id: < x_for_canada >, type1}
    if get_country_id(text.strip()) != 0:
        return json.dumps({"country_id": get_country_id(text.strip()), "type": 'country'})
    # Country Group B
    # returns {group_id: < x_for_group_b >, typ2}
    if get_group_id(text.strip()) != 0:
        return json.dumps({"group_id": get_group_id(text.strip()), "type": 'country-group'})
    # Country Group D: 3
    # returns {group_id: < x_for_group_d3 >, type3}
    if get_group_id(text.split(":")[0]) != 0:
        return json.dumps({"group_id": get_group_id(text.split(":")[0]), "type": 'country-group'})
    # RS Column 2
    # returns {group_id: < x_for_group_rs_column >, type3}


def get_country_details(country_id):
    country_sql = "select name from countries where id = %s"
    mycursor = db.cursor()
    mycursor.execute(country_sql, (country_id,))
    result = mycursor.fetchone()
    if result is not None:
        return {"name": result[0], "id": str(country_id)}


def get_country_ids_in_grp(group_id):
    group_country_sql = "select distinct(country_id) from country_group_countries where group_id = %s"
    mycursor = db.cursor()
    country_list = list()
    mycursor.execute(group_country_sql, (group_id,))
    result = mycursor.fetchall()
    if len(result) > 0:
        for country in result:
            country_list.append(country[0])
    # else:
    #     group_country_sql = "select distinct(country_id) from group_permissions where group_id = %s"
    #     mycursor.execute(group_country_sql, (group_id,))
    #     result = mycursor.fetchall()
    #     if len(result) > 0:
    #         for country in result:
    #             country_list.append(country[0])
    return country_list


def get_countries_in_group(group_id):
    group_country_sql = "select distinct(country_id) from country_group_countries where group_id = %s"
    mycursor = db.cursor()
    country_list = list()
    mycursor.execute(group_country_sql, (group_id,))
    result = mycursor.fetchall()
    if len(result) > 0:
        for country in result:
            country_list.append(get_country_details(country[0]))
    # else:
    #     group_country_sql = "select distinct(country_id) from country_group_countries where group_id = %s"
    #     mycursor.execute(group_country_sql, (group_id,))
    #     result = mycursor.fetchall()
    #     if len(result) > 0:
    #         for country in result:
    #             country_list.append(get_country_details(country[0]))
    return country_list


def get_countries_not_in_group(group_id):
    not_in_list = list()
    country_sql = "select id from countries"
    mycursor = db.cursor()
    mycursor.execute(country_sql, ())
    countries = mycursor.fetchall()
    if len(countries) > 0:
        for cid in countries:
            if cid[0] not in get_country_ids_in_grp(group_id):
                not_in_list.append(get_country_details(cid[0]))
    return not_in_list


def getValidCountryIDsAndNames(id, type, presentIn):
    # x_for_canada, 'country', True
        # return [[name: canada, id: x]]
    if type == "country":
        country = json.dumps(get_country_details(id))
        if country is not None:
            return country

    # x_for_group_b, 'country-group', True
        # return [[], [], [] id and name of all countries in group b]
    # x_for_group_b, 'country-group', False
        # return [[], [], [] id and name of all countries not in group b]
    if type == "country-group":
        return json.dumps(get_countries_in_group(id)) if presentIn else json.dumps(get_countries_not_in_group(id))


#print(determineCountryGroupOrCountry("D"))
#print(getValidCountryIDsAndNames(5, "country-group", False))
