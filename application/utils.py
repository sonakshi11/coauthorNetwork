import application.trie as trie
import csv
word_list = []

full_name_root = trie.Node()
# middle_name_root = trie.Node()
last_name_root = trie.Node()

with open('application/data/test.csv', 'r') as csvFile:
    reader = csv.reader(csvFile)
    counter=0
    for w in reader:
        full_name = w[0]
        last_name = full_name.split(' ')[-1]
        word_list.append(w[0])
        full_name += w[0].title()
        full_name_root.add_word(full_name, index_in_list=counter)
        last_name_root.add_word(last_name.title(),index_in_list=counter)
        counter+=1


def getName(index):
    # name = ""
    # l = len(word_list[index])
    # for i in range(0,l):
    #     name = name + " " + word_list[index][i]
    # print(word_list[index])
    return word_list[index]
    

def convert_into_list_of_dict(list_of_names):
    result=[]
    count= 0
    for word in list_of_names:
        result.append({"name": word, "id":count})
        count+=1
    return result


def get_from_trie(root, query):
    # print(root)
    index_list = root.auto_complete_word(query.title())
    # print(index_list)
    name_list = [getName(i) for i in index_list]
    name_list= sorted(name_list, key=len)
    
    return name_list


def get_results(query):
    
    full_name_result = get_from_trie(full_name_root, query)
    # middle_name_result = get_from_trie(middle_name_root, query)
    last_name_result = get_from_trie(last_name_root, query)
    # final_result = full_name_result + middle_name_result + last_name_result
    final_result = full_name_result + last_name_result
    return convert_into_list_of_dict(final_result)


def process_term(query):
    # If search term consists of spaces then 
    # name_list = query.split(' ')
    # result = ""
    # for name in name_list:
    #     result = result + name.title()
    return query