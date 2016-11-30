
# coding: utf-8

# ## OpenStreetMap Data Case Study: East Bay, California
# 
# ## Project Code
# 
# P3: Wrangle OpenStreetMap Data -- Udacity Data Science Nanodegree
# 
# Megan O'Neil
# 
# 2016-11-30

# This document contains the code used to:
# - Assess and clean the eastbay.osm file
# - Create csv files for ways, ways_nodes, ways_tags, nodes, and nodes_tags
# - Create the eastbay.db and tables for each of the aforementioned csv files
# - Analyze the dataset through mySQL

# In[1]:

import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import pandas as pd
from matplotlib.pyplot import pie, axis, show
import seaborn as sns


# In[2]:

# Use these functions to take systematic sample of elements from original OSM region

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    
    Helper function to take systematic sample of elements
    from origional OSM region.
    
    Args:
        osm_file (.osm file): the Open Street Map data file that is assessed
        tags (list): list of strings
    
    Returns:
        elements from osm_file if tag is listed in tags
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def create_sample(master_osm, sample_file, k):
    """Take systematic sample of elements from origional OSM region
    Args:
        master_osm (.osm file): Open Street Map data file from which sample is taken
        sample_file (.osm file): Name of sample file that will be created
        k (int): divisor for total number of elements; determines size of sample file. 
            Larger k returns smaller file.
    Returns:
        .osm file, sample of master .osm file.
    """
    with open(sample_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')

        # Write every kth top level element
        for i, element in enumerate(get_element(master_osm)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))

        output.write('</osm>')


# In[3]:

# Create samples - larger k = smaller file size, as it is sampling from 'k'th element.

#create_sample("eastbay.osm", "eastbay_samp1.osm", 100)
#create_sample("eastbay.osm", "eastbay_samp2.osm", 1000)
#create_sample("eastbay.osm", "eastbay_samp3.osm", 10000)


# In[4]:

def count_tags(filename):
    """Return dictionary with tag name as key and 
    number of times this tag can be encountered in map
    as value.
    
    Use to process map file and find out what tags there
    are and how many of each.
    
    Args:
        filename (string): name of .osm file that is reviewed
        
    Returns:
        dictionary with tags as keys, number of cases as value
    """

    tags = []
    for event, elem in ET.iterparse(filename):
        if elem.tag:
            tags.append(elem.tag)
    
    tag_dict = {}
    for tag in tags:   
        tag_dict[tag] = tags.count(tag)

    return tag_dict

#count_tags('eastbay_samp3.osm')


# In[5]:

"""Check the "k" value for each "<tag>" and see if there are any potential problems.

Use 3 regular expressions below to check for certain patterns
in the tags. I will change the data model and expand the 
"addr:street" type of keys to a dictionary like this:
{"address": {"street": "Some value"}}
So, I have to see if I have such tags, and if I have any tags with
problematic characters.

Reference: https://discussions.udacity.com/t/quiz-tag-types/170228/2
"""

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    """Return a count of each of four tag categories in a dictionary:
    
    "lower", for tags that contain only lowercase letters and are valid,
    "lower_colon", for otherwise valid tags with a colon in their names,
    "problemchars", for tags with problematic characters, and
    "other", for other tags that do not fall into the other three categories.
      
    Function is only used as helper function within process_map function below.
      
    Args:
        element (string): element from .osm file.
        keys (dictionary): dictionary of keys and number of cases.
          
    Returns:
        keys (dictionary): updated dictionary.
    """
    if element.tag == "tag":
        k =  element.attrib['k']
        #print k
        if re.search(lower, k):
            keys["lower"] += 1
        elif re.search(lower_colon, k):
            keys['lower_colon'] += 1
        elif re.search(problemchars, k):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1      
        pass    
  
    return keys

def process_map(filename):
    """Return a count of each of four tag categories in a dictionary
    for specified osm file.
    
    Args:
        filename (string): name of .osm file that will be parsed
    
    Returns:
        keys (dictionary): dictionary of character types and number of cases in .osm file
    """
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

process_map("eastbay.osm")


# ### Assess Amenities

# In[6]:

"""
Count total number of unique amenities
Create dictionary of amenities and their frequency.
Review to determine if there are problem amenity names to correct.

Reference: https://discussions.udacity.com/t/quiz-tag-types/170228/2
"""

def find_amenity(element, amen_list, amen_dic):
    """Create dictionary of amenities and their frequency.
    Used in process_amenities function below.
    
    Args:
        element (string): element in .osm file
        amen_list (list): list of amenities
        amen_dic (dic): dictionary of amenities
    
    Returns:
        amen_dic (dic): updated dictionary of amenities and number of cases
    """
    if element.tag == "tag":
        k =  element.attrib['k']
        if k == 'amenity':
            v = element.attrib['v']
            amen_dic[v] = 0
            amen_list.append(v)
            
    return amen_dic

def process_amenities(filename):
    """Return total number of amenities and 
    dictionary of amenities and their frequency
    
    Args:
        filename (string): name of .osm file
    
    Returns:
        len(amen_list) (int): Number of unique amenities
        amen_dic (dic): Dictionary of amenities and frequency of each
    """
    #amen_count = 0
    amen_list = []
    amen_dic = {}
    for _, element in ET.iterparse(filename):
        amenities = find_amenity(element, amen_list, amen_dic)
        for key in amen_dic:
            amen_dic[key] = amen_list.count(key)
    return len(amen_list), amen_dic

#process_amenities("eastbay_samp1.osm")


# ### Assess and Clean Zip Codes

# In[7]:

"""
Count total number of postal codes/zip codes.
Create dictionary of zip codes and their frequency.
Review to determine if there are problem amenity names to correct.

Reference: https://discussions.udacity.com/t/quiz-tag-types/170228/2

* Both functions edited per review #2 of project to increment zip_dic, exlude zip_list.
"""

def find_zip(element, zip_dic):    
    """Create dictionary of zip codes and their frequency.
  
    Args:
        element (string): element in .osm file
        zip_dic (dic): dictionary of zip codes
    
    Returns:
        zip_dic (dic): updated dictionary of zip codes and number of cases
        """
    if element.tag == "tag":
        k =  element.attrib['k']
        if k == 'addr:postcode':
            v = element.attrib['v']
            if v not in zip_dic:
                zip_dic[v] = 1
            else:
                zip_dic[v] += 1      
    return zip_dic    

def process_zips(filename):
    """Return total number of zip codes and 
    dictionary of zip codes and their frequency
    
    Args:
        filename (string): name of .osm file
    
    Returns:
        sum(zip_dic.values()) (int): Number of total zip codes found
        zip_dic (dic): Dictionary of zip codes and frequency of each
    """
    zip_dic = {}
    for _, element in ET.iterparse(filename):
        zip_dic = find_zip(element, zip_dic)
        
    return sum(zip_dic.values()), zip_dic

#process_zips("eastbay_samp2.osm")


# In[8]:

def clean_zip(zipcode):
    """Clean zip codes: remove extra spaces, 'CA', extra postal code, zip codes less than 5 digits.
    Ref on regular expressions: https://www.tutorialspoint.com/python/python_reg_expressions.htm
    
    Args:
        zipcode (string): entry for zip code.
        
    Returns:
        Cleaned zipcode (string).
    """
    zipcode = zipcode.replace(' ','')
    if 'ca' in zipcode:        
        zipcode = zipcode.replace('ca', '')
        if re.search(r'\d{5}$', zipcode) == False:
            return None
            #pass
    if 'CA' in zipcode:        
        zipcode = zipcode.replace('CA', '')
        if re.search(r'\d{5}$', zipcode) == False:
            return None
            #pass
    if '-' in zipcode:
        zipcode = zipcode.split('-',1)[0]
        if re.search(r'\d{5}$', zipcode) == False:
            return None
            #pass
    if re.search(r'\d{5}$', zipcode) == False:
        return None
        #pass
    else:
        return zipcode
    
clean_zip('946ca')


# In[40]:

def clean_zip1(zipcode):
    """Clean zip codes: remove extra spaces, 'CA', extra postal code, zip codes less than 5 digits.
    Ref on regular expressions: https://www.tutorialspoint.com/python/python_reg_expressions.htm
    
    Args:
        zipcode (string): entry for zip code.
        
    Returns:
        Cleaned zipcode (string).
    """
    zipcode = zipcode.replace(' ','')
    if 'ca' in zipcode:        
        zipcode = zipcode.replace('ca', '')
    if 'CA' in zipcode:        
        zipcode = zipcode.replace('CA', '')
    if '-' in zipcode:
        zipcode = zipcode.split('-',1)[0]
    
    cleanzip = re.match(r'\d{5}$', zipcode)
    if cleanzip:
        return zipcode
    else:
        return None
    
#clean_zip1('94610')


# In[44]:

postcode = '94610'

clean_postcode = re.findall(r'^(\d{5})-\d{4}$', postcode)[0]

clean_postcode


# ### Determine Unique Users

# In[45]:

def process_users(filename):
    """Return a set of unique user IDs ("uid").
    
    Find out how many unique users have contributed to the map in this particular area.
    
    Args:
        filename (string): name of .osm file
    
    Returns:
        Set of unique user IDs
    """
    #users = set()
    users = []
    for _, element in ET.iterparse(filename):
        if 'uid' in element.attrib:
            user = element.attrib['uid']
            if user not in users:
                users.append(user)
            #print element.attrib['uid']
        pass
    #return users
    return set(users)

#print len(process_users('eastbay_samp3.osm'))
#print len(process_users('eastbay_samp2.osm'))
#print len(process_users('eastbay_samp1.osm'))
#print len(process_users('eastbay.osm'))


# ### Assess and Clean Street Types

# In[46]:

"""
Audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix 
the unexpected street types to the appropriate ones in the expected list.
You have to add mappings only for the actual problems you find in this OSMFILE,
not a generalized solution, since that may and will depend on the particular area you are auditing.

"""

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Center", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Plaza", "Commons", "Way", "Circle", "Loop"]


def audit_street_type(street_types, street_name):
    """ Update dictionary with problematic street type as key 
    and full street name where found as value.
    
    Used in 'audit' function below
    
    Args: 
        street_types (dic): default dictionary as applied in audit function
        street_name (string): name of specific street 
    
    Returns:
        street_types (dic) updated with street_type not in 'expected' list as key,
            full street name as value
            
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group() # returns the last word.
        if street_type not in expected:
            street_types[street_type] = street_name # MODIFIED FROM EXAMPLE
            #if last word in street name is not in expected list, 
            # add the street type as key in dictionary, with full street name as value

def is_street_name(elem):
    """Confirm that element reviewed is a street name."""
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile):
    """Return dictionary of problematic street types and street names where found for all streets in osm file
    
    Args:
        osmfile (string): name of .osm file
    
    Returns:
        street_types dictionary, updated for all unexpected street types in .osm file 
            (see audit_street_type function)
    """
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                # in the line below, the code is checking if the 'element' complies            
                # with the code 'is_street_name()'            
                # however, the outer conditions specify that
                # 'element.tag' is 'way' or 'node'      
                #  
                # However, it is the children of the 'way' or 'node' elements      
                #  that you are interested in, so code has named the children
                #  tag in the statement  `for tag in element.iter("tag"):`
                if is_street_name(tag):
                    #  the same is true here: element.attrib['v']
                    #  element.attrib['v'] refers to the attributes of 'node' or 'way'
                    #  but 'node' or 'way' elements don't have an attribute 'v'
                    #  So, tag.attrib['v'] refers to the children of 'node' or 'way'
                    #  that have the tagname 'tag'
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

#audit('eastbay.osm')


# In[47]:

"""Create 'mapping' dictionary to fix street types; create 'special_map' dictionary for special cases to fix."""

mapping = { "St": "Street",
            "St.": "Street",
            "street": "Street",
            "st": "Street",
            "Ave": "Avenue",
            "Rd.": "Road",
            "Rd": "Road",
            "AVE": "Avenue",
            "Ave.": "Avenue",
            "Aveenue": "Avenue",
            "Ave.": "Avenue",
            "Avenie": "Avenue",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "blvd": "Boulevard",
            "Ct": "Court",
            "Ctr": "Center",
            "Dr": "Drive",
            "Dr.": "Drive",
            "Ln.": "Lane",
            "square": "Square",
            "Pl": "Plaza"
          }

special_map = { "Washington St 2nd Floor:": "Washington Street, 2nd Floor",
               "Telegraph": "Telegraph Avenue", 
               "San Francisco/Oakland Bridge Toll Pl": "San Francisco/Oakland Bridge Toll Plaza"
               }

def clean_st_name(name, mapping):
    """Take a string with street name as an argument and return the fixed name,
    as stated in mapping dictionary.
    
    Args:
        name (string): name of street
        mapping (dictionary): dictionary of incorrect street types as key, corrected names as value
        
    Returns:
        Corrected street name (string)
    
    """
    name = name.replace('  ', ' ')
    if name in special_map:
        name = special_map[name]
    m = street_type_re.search(name)
    if m.group() in mapping:
        first_part = name.rsplit(' ', 1)[0]
        # cut off last word in sentence 
        #(http://stackoverflow.com/questions/6266727/python-cut-off-the-last-word-of-a-sentence)
        name = first_part + ' ' + mapping[m.group()]
    return name


# ### Assess and Clean City Names

# In[48]:

"""
Audit the OSMFILE and change the variable 'city_mapping' to reflect the changes needed to fix 
the unexpected city names to the appropriate ones in the expected list
"""

city_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ['Berkeley', 'Piedmont', 'Oakland','Richmond','Albany','Alameda', 'El Cerrito', 'San Leandro','Emeryville',
            'Moraga','Lafayette', 'Castro Valley', 'Kensington', 'Orinda', 'Canyon', 'Walnut Creek']

def audit_city(cities, city_name):
    """ Update dictionary, 'cities', with problematic city name as key 
    and full city name where found as value.
    
    Used in 'audit2' function below
    
    Args: 
        cities (dic): default dictionary as applied in audit function
        city_name (string): name of specific street 
    
    Returns:
        cities (dic) updated with city not in 'expected' list as key,
            correct city name as value

    """
    city = city_re.search(city_name)
    if city:
        if city not in expected:
            cities[city] = city_name 

def is_city_name(elem):
    """Confirm element is listed as a city.
    
    Used in 'audit2' function.
    
    Arg:
        elem (string): element in .osm file
        
    Result:
        Boolean (True or False)
    """
    return (elem.attrib['k'] == "addr:city")

def audit2(osmfile):
    """Return dictionary of problematic city names in osm file
    
    Args:
        osmfile (string): name of .osm file
    
    Returns:
        cities dictionary, updated for all unexpected cities in .osm file 
            (see audit_city function)
    """
    osm_file = open(osmfile, "r")
    cities = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_city_name(tag):
                    audit_city(cities, tag.attrib['v'])
    osm_file.close()
    return cities

#audit2('eastbay.osm')


# In[49]:

## Figure out if I can use regex to improve this function
city_mapping = { "Alamda": "Alameda",
            "alameda": "Alameda",
            "Berkeley, CA": "Berkeley",
            "berkeley": "Berkeley",
            "Oakland ": "Oakland",
            "oakland": "Oakland",
            "Oakland CA": "Oakland",
            "Oakland, CA": "Oakland",
            "Oakland, Ca": "Oakland",
            "Okaland": "Oakland",
            "OAKLAND": "Oakland",
            "Emeyville": "Emeryville"
          }

def clean_city_name(name, city_mapping):
    """Take a string with city name as an argument and return the corrected name,
    as stated in mapping dictionary.
    
    Args:
        name (string): name of city
        city_mapping (dictionary): dictionary of incorrect city names as key, corrected names as value
        
    Returns:
        Corrected city name (string)
    """
    #name = name.replace('  ', ' ')
    if name in city_mapping:
        output = city_mapping[name]
    else:
        output = name
    return output

#clean_city_name("Oakland, CA", city_mapping)


# ## Creating SQL Database

# ### Creating CSV files

# In[50]:

""" Imported cerberus & saved schema.py file into working directory: 
Reference: https://discussions.udacity.com/t/final-project-importing-cerberus-and-schema/177231/2
"""
import csv
import codecs
import cerberus
import schema

#OSM_PATH = "example2_osm.xml" #revised to use the right file.

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

## Trying to add cleaning of zips and addresses
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict.
    
    Calls on 'clean_st_name', 'clean_city_name', and 'clean_zip' functions to clean 
    street names, city name, and zip code before including in database.
    
    Args:
        element (string):
        node_attr_fields (list, defaults to NODE_FIELDS): list of fields for 'node' elements
        way_attr_fields (list, defaults to WAY_FIELDS): list of fields for 'way' elements
        problem_chars (re expression, defaults to PROBLEMCHARS): problematic characters, as defined by regex
        default_tag_type (string, defaults to 'regular'): unless specified, tag type is 'regular'
        
    Returns:
        Dictionary 
    """

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node': #https://discussions.udacity.com/t/help-cleaning-data/169833/6
        for node in NODE_FIELDS: 
            try:
                node_attribs[node] = element.attrib[node]
            except:
                #print {'node':node_attribs, 'node_tags':tags}
                node_attribs[node] = "99999999"
                #https://discussions.udacity.com/t/project-problem-cant-get-through-validate-element-el-validator/179544/28
        
        for tag in element.iter("tag"):
            key = tag.attrib['k']
            if re.search(PROBLEMCHARS, key):
                pass            
            else:
                tagdic = {}
                tagdic['id'] = node_attribs['id']
                # If there's a colon, use only text after colon - only applies to first colon
                if ':' in key: 
                    #Split once on a colon, take string after the split; assign before the split to 'type'
                    ## Added this section to clean street name and zip code.
                    if key == "addr:street":
                        tagdic['value'] = clean_st_name(tag.attrib['v'], mapping)
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                    elif key == "addr:city":
                        tagdic['value'] = clean_city_name(tag.attrib['v'], city_mapping)
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                    elif key == "addr:postcode":
                        value = tag.attrib['v'].strip()
                        if clean_zip(value):
                            tagdic['value'] = clean_zip1(value)
                            tagdic['key'] = key.split(':',1)[1]
                            tagdic['type'] = key.split(':',1)[0]
                        else:
                            continue 
                            #https://discussions.udacity.com/t/project-problem-cant-get-through-validate-element-el-validator/179544/43
                    else: # 'key' has a colon but is not "addr:street" or "addr:postcode"
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                        tagdic['value'] = tag.attrib['v']
    
                else:
                    tagdic['key'] = key
                    tagdic['type'] = "regular"
                    tagdic['value'] = tag.attrib['v']
                
                if tagdic: 
                    if tagdic['key']:
                        tags.append(tagdic)
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        for way in WAY_FIELDS:
            try:
                way_attribs[way] = element.attrib[way]
            except:
                #print(way)
                way_attribs[way] = "99999999" 
                #https://discussions.udacity.com/t/project-problem-cant-get-through-validate-element-el-validator/179544/28
        
        for tag in element.iter("tag"):
            key = tag.attrib['k']
            if re.search(PROBLEMCHARS, key):
                pass            
            else:
                tagdic = {}
                tagdic['id'] = way_attribs['id']
                # If there's a colon, use only text after colon - only applies to first colon
                if ':' in key: 
                    #Split once on a colon, take string after the split; assign before the split to 'type'
                    ## Added this section to clean street name and zip code.
                    if key == "addr:street":
                        tagdic['value'] = clean_st_name(tag.attrib['v'], mapping)
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                    elif key == "addr:city":
                        tagdic['value'] = clean_city_name(tag.attrib['v'], city_mapping)
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                    elif key == "addr:postcode":
                        value = tag.attrib['v'].strip()
                        if clean_zip(value):
                            tagdic['value'] = clean_zip(value)
                            tagdic['key'] = key.split(':',1)[1]
                            tagdic['type'] = key.split(':',1)[0]
                        else:
                            continue 

                    else: # 'key' has a colon but is not "addr:street" or "addr:postcode"
                        tagdic['key'] = key.split(':',1)[1]
                        tagdic['type'] = key.split(':',1)[0]
                        tagdic['value'] = tag.attrib['v']
    
                else:
                    tagdic['key'] = key
                    tagdic['type'] = "regular"
                    tagdic['value'] = tag.attrib['v']
                
                if tagdic: 
                    if tagdic['key']:
                        tags.append(tagdic)
        
        tag_num = 0
        for tag in element.iter("nd"):
            nd_dic = {}
            nd_dic['id'] = way_attribs['id']
            nd_dic['node_id'] = tag.attrib['ref']
            nd_dic['position'] = tag_num
            tag_num += 1
            way_nodes.append(nd_dic)
        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    
    Args:
        osm_file (string): name of .osm file
        tags (list, default ('node, 'way', 'relation')): list of tags for element
    """
    
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)
    
    Args:
        file_in (string): name of .osm file to be processed and written to csv files
        validate (Boolean): determines if function is validated throughout processing
    """

    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,          codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS, lineterminator = '\n')
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS, lineterminator = '\n')
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS, lineterminator = '\n')
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS, lineterminator = '\n')
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS, lineterminator = '\n')
        
        ## Added 'lineterminator' to remove spaces between rows in csv file,
        # Ref: http://stackoverflow.com/questions/11652806/csv-write-skipping-lines-when-writing-to-csv

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
    
process_map("eastbay.osm", validate = False)


# ### Initiating Tables

# In[51]:

""" Uploading csv files to sql from python.
Ref: https://discussions.udacity.com/t/creating-db-file-from-csv-files-with-non-ascii-unicode-characters/174958/7
"""

# Import modules
import sqlite3
import csv
from pprint import pprint

# Create database file in same file as notebook
sqlite_file = 'eastbay.db'

# Connect to the database
conn = sqlite3.connect(sqlite_file)

# Get a cursor object
cur = conn.cursor()


# #### Table: nodes_tags 

# In[52]:

# Get a cursor object
#cur = conn.cursor()

# Check if the table already exists, drop it if it does
# Reference: https://discussions.udacity.com/t/upload-my-csv-files-sqlite/190795/5
cur.execute('''DROP TABLE IF EXISTS nodes_tags;''')
conn.commit()

# Create nodes_tags table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE nodes_tags(id INTEGER, key TEXT, value TEXT,type TEXT)
''')

# Commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('nodes_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'], i['key'],i['value'].decode("utf-8"), i['type']) for i in dr]
    # include the '.decode("utf-8")' if I get long error about 8-bit bytestrings.
    
# Insert the formatted data
cur.executemany("INSERT INTO nodes_tags(id, key, value,type) VALUES (?, ?, ?, ?);", to_db)
# Commit the changes
conn.commit()

# Check that data imported properly
cur.execute('SELECT * FROM nodes_tags')
all_rows = cur.fetchall()
#print('1):')
#pprint(all_rows)

# Close the connection
#conn.close()


# #### Table: ways

# In[53]:

# Check if the table already exists, drop it if it does
cur.execute('''DROP TABLE IF EXISTS ways;''')
conn.commit()

# Create table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE ways(id INTEGER, user TEXT, uid INTEGER, version INTEGER, changeset INTEGER, timestamp TIMESTAMP)
''')
# Commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('ways.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'].decode("utf-8"), i['user'].decode("utf-8"),i['uid'].decode("utf-8"), 
              i['version'].decode("utf-8"), i['changeset'].decode("utf-8"), 
              i['timestamp'].decode("utf-8")) for i in dr]
    # include the '.decode("utf-8")' if I get long error about 8-bit bytestrings.
    
# Insert the formatted data
cur.executemany("INSERT INTO ways(id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db)
# Commit the changes
conn.commit()

# Check that data imported properly
cur.execute('SELECT * FROM ways')
all_rows = cur.fetchall()
#print('1):')
#pprint(all_rows)

# Close the connection
#conn.close()


# #### Table: nodes

# In[54]:

## NODES TABLE

# Check if the table already exists, drop it if it does
cur.execute('''DROP TABLE IF EXISTS nodes;''')
conn.commit()

# Create table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE nodes(id INTEGER, lat NUMERIC, lon NUMERIC, user TEXT, uid INTEGER, 
    version TEXT, changeset INTEGER, timestamp TIMESTAMP)
''')
# Commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'], i['lat'], i['lon'], i['user'].decode("utf-8"), i['uid'].decode("utf-8"), 
              i['version'].decode("utf-8"), i['changeset'].decode("utf-8"), 
              i['timestamp'].decode("utf-8")) for i in dr]
    
# Insert the formatted data
cur.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db)
# Commit the changes
conn.commit()

# Check that data imported properly
cur.execute('SELECT * FROM nodes')
all_rows = cur.fetchall()
#print('1):')
#pprint(all_rows)

# Close the connection
#conn.close()


# #### Table: ways_tags

# In[55]:

# Check if the table already exists, drop it if it does
cur.execute('''DROP TABLE IF EXISTS ways_tags;''')
conn.commit()

# Create table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE ways_tags(id INTEGER, key TEXT, value TEXT, type TEXT)
''')
# Commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('ways_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'], i['key'],i['value'].decode("utf-8"), i['type']) for i in dr]
    
# Insert the formatted data
cur.executemany("INSERT INTO ways_tags(id, key, value,type) VALUES (?, ?, ?, ?);", to_db)
# Commit the changes
conn.commit()

# Check that data imported properly
cur.execute('SELECT * FROM ways_tags')
all_rows = cur.fetchall()
#print('1):')
#pprint(all_rows)

# Close the connection
#conn.close()


# #### Table: ways_nodes

# In[56]:

# Check if the table already exists, drop it if it does
cur.execute('''DROP TABLE IF EXISTS ways_nodes;''')
conn.commit()

# Create table, specifying the column names and data types:
cur.execute('''
    CREATE TABLE ways_nodes(id INTEGER, node_id INTEGER, position INTEGER)
''')
# Commit the changes
conn.commit()

# Read in the csv file as a dictionary, format the
# data as a list of tuples:
with open('ways_nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db = [(i['id'], i['node_id'],i['position']) for i in dr]
    
# Insert the formatted data
cur.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db)
# Commit the changes
conn.commit()

# Check that data imported properly
cur.execute('SELECT * FROM ways_nodes')
all_rows = cur.fetchall()
#print('1):')
#pprint(all_rows)


# In[57]:

# Close the connection
conn.close()


# ### Assessing SQL Database

# In[58]:

# Connect to the database
db = sqlite3.connect('eastbay.db')
c = db.cursor()


# In[59]:

# Get database filesize
# https://discussions.udacity.com/t/size-of-file-database-query/180429
# http://www.sqlite.org/pragma.html#pragma_page_count

QUERY = "PRAGMA PAGE_SIZE;"
c.execute(QUERY)
rows = c.fetchall()
page_size = rows[0][0]


QUERY = "PRAGMA PAGE_COUNT;"
c.execute(QUERY)
rows = c.fetchall()
page_count = rows[0][0]

bytesize = (page_size * page_count)
MBsize = bytesize/1000000
print MBsize


# In[60]:

# Number of nodes

QUERY = '''
SELECT COUNT(*) 
FROM nodes;'''

c.execute(QUERY)

all_rows = c.fetchall()
pprint(all_rows)
nodes = all_rows[0][0]


# In[61]:

# Number of ways

QUERY = '''
SELECT COUNT(*) 
FROM ways;'''

c.execute(QUERY)

all_rows = c.fetchall()
pprint(all_rows)
ways = all_rows[0][0]


# In[62]:

# Total number of ways + nodes
pprint(ways + nodes)
ways_nodes = ways + nodes


# In[63]:

# Number of unique users

QUERY = '''
SELECT COUNT(DISTINCT(e.uid))
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;'''

c.execute(QUERY)

all_rows = c.fetchall()
pprint(all_rows)

## Note - python script returned 880 users. BUT this was before I dropped files with invalid zip codes.

#Reference sample project: https://gist.github.com/carlward/54ec1c91b62a5f911c42#file-sample_project-md
#Not useful reference: http://stackoverflow.com/questions/7731406/sql-query-to-find-distinct-values-in-two-tables


# In[64]:

# Frequency of users, top 5

QUERY = '''
SELECT DISTINCT(e.user), COUNT(*) as count
FROM (SELECT user FROM nodes UNION ALL SELECT uid FROM ways) e
GROUP BY e.user
ORDER BY count DESC
LIMIT 10;
'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)
top10users = all_rows
topuser_entries = float(all_rows[0][1])
print topuser_entries


# In[65]:

# % of entries by top user:
topuser_entries/ways_nodes


# In[66]:

# Number of users with only one post
QUERY = '''
SELECT COUNT(*)
FROM (SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT uid FROM ways) e
GROUP BY e.user
HAVING num=1) u;
'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[67]:

# Number of users with over 100 posts
QUERY = '''
SELECT COUNT(*)
FROM (SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT uid FROM ways) e
GROUP BY e.user
HAVING num > 100) u;
'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[68]:

# Number and frequency of top 5 zip codes.

QUERY = '''
SELECT tags.value, COUNT(*) as count
FROM (SELECT * FROM nodes_tags 
      UNION ALL 
      SELECT * FROM ways_tags) tags
WHERE tags.key = 'postcode'
GROUP BY tags.value
ORDER BY count DESC
LIMIT 5;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[69]:

# Sort 10 most frequent cities by count, descending

QUERY = '''
SELECT tags.value, COUNT(*) as count
FROM (SELECT * FROM nodes_tags 
      UNION ALL 
      SELECT * FROM ways_tags) tags
WHERE tags.key LIKE '%city'
GROUP BY tags.value
ORDER BY count DESC
LIMIT 10;'''

c.execute(QUERY)

all_rows = c.fetchall()
pprint(all_rows)

## City function is working - it's only cleaning the ones I told it to, the other mess stays in there.


# In[70]:

def plot_freq_query(x, y, title):
    """Create bar plot of query that returns value and frequency of each value"""
    data_list = list(all_rows)
    # Reference: http://stackoverflow.com/questions/14835852/convert-sql-result-to-list-python

    df = pd.DataFrame(data_list)
    # Reference: http://stackoverflow.com/questions/20638006/convert-list-of-dictionaries-to-dataframe
    df.columns = [x,y]

    plot = sns.factorplot(x = x, y = y, data = df, kind = 'bar')
    plot.set_xticklabels(rotation = 90) 
    #Reference: http://stackoverflow.com/questions/26540035/rotate-label-text-in-seaborn-factorplot
    plot.fig.suptitle(title)


# In[71]:

# Frequency of top 10 amenities

QUERY = '''
SELECT tags.value, COUNT(*) as count
FROM (SELECT * FROM nodes_tags 
      UNION ALL 
      SELECT * FROM ways_tags) tags
WHERE tags.key='amenity'
GROUP BY tags.value
ORDER BY count DESC
LIMIT 10;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)

plot_freq_query('Amenity', 'Frequency', 'Top 10 Amenities by Frequency')


# In[72]:

# Average capacity of bicycle parking amenities
QUERY = '''
SELECT AVG(CAST(nodes_tags.value as INTEGER))
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='bicycle_parking') i
    ON nodes_tags.id = i.id
    WHERE nodes_tags.key = 'capacity';'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[73]:

# Capacities of top 10 largest bicycle parking amenities
QUERY = '''
SELECT CAST(nodes_tags.value as INTEGER)
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='bicycle_parking') i
    ON nodes_tags.id = i.id
    WHERE nodes_tags.key = 'capacity'
    ORDER BY cast(nodes_tags.value as INTEGER) DESC
    LIMIT 10;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[74]:

# Details on this giant bicycle parking station!
QUERY = '''
SELECT *
FROM nodes_tags
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE key = 'capacity' AND value='268') i
    ON nodes_tags.id = i.id
  ;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[75]:

# Where is this giant bicycle parking, latitude & longitude?
QUERY = '''
SELECT nodes.lat, nodes.lon
FROM nodes_tags JOIN nodes ON nodes_tags.id = nodes.id
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='bicycle_parking') i
    ON nodes_tags.id = i.id
    WHERE nodes_tags.key = 'capacity' AND nodes_tags.value = '268';'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[76]:

# Number of users adding bicycle parking to OSM
QUERY = '''
SELECT COUNT(DISTINCT(uid))
FROM nodes_tags JOIN nodes ON nodes_tags.id = nodes.id
WHERE nodes_tags.key = 'amenity' and nodes_tags.value = 'bicycle_parking' 
;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[77]:

# Users adding bicycle parking and number of entries per user
QUERY = '''
SELECT DISTINCT(nodes.user), COUNT(*) as count
FROM nodes_tags JOIN nodes ON nodes_tags.id = nodes.id
WHERE nodes_tags.key = 'amenity' and nodes_tags.value = 'bicycle_parking'
GROUP BY nodes.user
ORDER BY count DESC
;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[95]:

# Popular shops

QUERY = '''
SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE key='shop') i
    ON nodes_tags.id = i.id
WHERE key = 'shop'
GROUP BY nodes_tags.value
ORDER BY num DESC
LIMIT 10;'''
c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)

plot_freq_query('Shop Type', 'Frequency', 'Top 10 Shop Types by Frequency')


# In[94]:

# Popular cuisines
QUERY = '''
SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
    ON nodes_tags.id = i.id
WHERE nodes_tags.key='cuisine'
GROUP BY nodes_tags.value
ORDER BY num DESC
LIMIT 10;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)

plot_freq_query('Cuisine', 'Frequency', 'Top 10 Restaurant Cuisines by Frequency')


# In[103]:

# Number of korean and ethiopian restaurants
QUERY = '''
SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
    ON nodes_tags.id = i.id
WHERE nodes_tags.key='cuisine'
AND nodes_tags.value = 'korean' 
OR nodes_tags.value = 'ethiopian'
GROUP BY nodes_tags.value
ORDER BY num DESC
LIMIT 10;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[104]:

# How many solar generators?
QUERY = '''
SELECT COUNT(*) as count
FROM nodes_tags
WHERE nodes_tags.key = 'source'
    AND nodes_tags.value = 'solar';'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[105]:

# What information is there about energy nodes?
QUERY = '''
SELECT nodes_tags.value, COUNT(*) as count
FROM nodes_tags 
     
WHERE nodes_tags.key='power'
GROUP BY nodes_tags.value
ORDER BY count DESC;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[106]:

# What type of generators?
QUERY = '''
SELECT DISTINCT(nodes_tags.value)
FROM nodes_tags
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='generator') i
    ON nodes_tags.id = i.id
    WHERE nodes_tags.key = 'source'
    ORDER BY nodes_tags.value;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[107]:

# Where are they?
QUERY = '''
SELECT DISTINCT(nodes_tags.value)
FROM nodes_tags
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='generator') i
    ON nodes_tags.id = i.id
    WHERE nodes_tags.key = 'place'
    ORDER BY nodes_tags.value;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)


# In[108]:

# Details on one of these rooftop solar systems:
QUERY = '''
SELECT *
FROM nodes_tags
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE key = 'source' AND value='solar') i
    ON nodes_tags.id = i.id
    LIMIT 20
  ;'''

c.execute(QUERY)
all_rows = c.fetchall()
pprint(all_rows)

