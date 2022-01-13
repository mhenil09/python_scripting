import re

def isLevel3(string):
    if string == 'c' or string == 'd' or string == 'm':
        return False
    string = string.upper()
    return bool(re.search(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", string))

def isLevel2(string):
    return string.isdigit()
    
def isLevel1(string):
    if string == 'c' or string == 'd' or string == 'm':
        return True
    return string.isalpha() and string.islower() and len(string) == 1

def isLevel4(string):
    return string.isalpha() and string.isupper()

def getCurrentLevel(index, previousIndex, nextIndex):
    if isLevel4(index):
        return 4
    if index == 'i':
        if isLevel1(previousIndex) or isLevel3(previousIndex):
            return 1
        if isLevel2(previousIndex):
            if (isLevel2(nextIndex) and nextIndex == '1') or nextIndex == 'j':
                return 1
            return 3
    if isLevel1(index) or isLevel3(index):
        if isLevel3(index) == False:
            return 1
        else:
            if isLevel3(index) and isLevel1(index) == False:
                return 3
            if isLevel1(index) and isLevel3(index) == False:
                return 1
            else:
                if (isLevel2(previousIndex) or isLevel3(previousIndex)):
                    if (previousIndex == 'c' and index == 'd') == False and (previousIndex == 'l' and index == 'm') == False:
                        if isLevel2(previousIndex) and index != 'i':
                            return 1
                        return 3
                    else:
                        return 1
                else:
                    return 1
    return 2  

def index_in_list(a_list, index):
    return index < len(a_list)

def getParentIndexes(indexes):
    indexesWithParents = []
    previousIndex = ''
    nextIndex = ''
    for i in range(len(indexes)):
        index = indexes[i]
        if index_in_list(indexes, i+1):
            nextIndex = indexes[i+1]
        else:
            nextIndex = ''
        identifier = ''
        currentLevel = getCurrentLevel(index, previousIndex, nextIndex)
        if currentLevel == 1:
            identifier = index
            lastLevel1Parent = identifier
        if currentLevel == 2:
            identifier = lastLevel1Parent + '.' + index
            lastLevel2Parent = identifier
        if currentLevel == 3:
            identifier = lastLevel2Parent + '.' + index
            lastLevel3Parent = identifier
        if currentLevel == 4:
            identifier = lastLevel3Parent + '.' + index
            lastLevel4Parent = identifier
        previousIndex = index
        indexesWithParents.append(identifier)
    return indexesWithParents


def process_indexes(indexes):
    parents = getParentIndexes(indexes)
    parents_with_bracs = list()
    for p in parents:
        parents_with_bracs.append('(' + p.replace('.', ')(') + ')')
    return parents_with_bracs
