import parsing_script as ps
import parsing_references as pr
import parsing_definitions as pd
import hs_codes_parser as hscp
import country_group_rs_identifier as cgri

# ps.process_part738()
# ps.process_part740()
# ps.process_part743()
# ps.process_part745()
ps.process_part746_b_2()

# pr.fetch_references()

# pd.process_term_definitions()

# hscp.read_excel_file()

# print(cgri.determineCountryGroupOrCountry("Canada"))
# print(cgri.determineCountryGroupOrCountry("Country Group B"))
# print(cgri.determineCountryGroupOrCountry("Country Group D:3"))
# print(cgri.determineCountryGroupOrCountry("RS 2"))
#
# print(cgri.getValidCountryIDsAndNames(33, "country", True))
# print(cgri.getValidCountryIDsAndNames(1, "country-group", True))
# print(cgri.getValidCountryIDsAndNames(1, "country-group", False))
