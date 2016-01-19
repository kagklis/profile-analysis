import glob, nltk, time, os, re, subprocess, math, urllib2, socket, itertools
from nltk.corpus import wordnet
from bs4 import BeautifulSoup,SoupStrainer
from operator import itemgetter
from xml.etree.ElementTree import ElementTree
from itertools import groupby

def most_common_func(L):
  return max(groupby(sorted(L)), key=lambda(x, v):(len(list(v)),-L.index(x)))[0]

#folder with txt, pdf & html files - must be located in the same dir with the script
path = os.getcwd()
tkn_path = path + "\\tokenize\\"
tag_path = path + "\\tagged\\"
types = ['*.txt', '*.html', '*.htm']

while(1):
    x = raw_input("Press:\n1. Run profile analysis \
        \n2. Enter index mode\n3. Exit Program\nYour option: ")
    accepted_inputs = ['1','2','3']
    while(x not in accepted_inputs):
        x = raw_input("Invalid input!!! Press:\n1. Run profile analysis \
        \n2. Enter index mode\n3. Exit Program\nYour option: ")

#----------------------------------- READ BOOKMARK FILE -------------------------------------#
    if(x is '1'):
        if not(os.path.exists(path+"\profile")):
          print "\nThere is no profile folder. Create a folder with the name profile and put your files in it. Then re-try...\n"
          continue
        
        inverted_index = {}
        #noun_dictionary -> {noun1:{doc_id1:weight1, doc_id2:weight2, ...}, noun2:... }
        noun_dictionary = {}                    
        t0=time.time()

        try:
          fh = open('bookmarks.html', 'r')
        except:
          print "\nThere is no file named bookmarks.html! Export bookmarks in HTML and re-try...\n"
          continue
        page = fh.read()
        fh.close()


#------------------------- EXTRACT LINKS AND PUT THEM ON A TXT/LIST -------------------------#

        with open('url_links.txt', 'w') as fh:
          for link in BeautifulSoup(page, 'html.parser', parse_only=SoupStrainer('a')):
              if link.has_key('href') and re.match('^http',link['href']):
                  fh.write(link['href']+"\n")
        


#---------------------------- DOWNLOAD WEB PAGES - .HTML FILES ------------------------------#
        
        i=1
        fh = open('url_links.txt', 'r')
        
        for link in fh.readlines():
            request = urllib2.Request(link)
            opener = urllib2.build_opener()
            try:
                filehandle = opener.open(request, timeout=5)
                myFile = open(path+'\\profile\\'+'bookmark%04d.html'%i,'w')
                myFile.write(link)
                myFile.write(filehandle.read())
            except urllib2.URLError:
                filehandle.close()
                continue
            except socket.timeout:
                filehandle.close()
                continue
            except:
                myFile.close()
                filehandle.close()
                continue
            i += 1
            myFile.close()
            filehandle.close()
        
        print ("\nBookmarked web pages have been succesfuly downloaded!\nProceeding...")

        
        try:
            os.mkdir("tokenize")                        
            os.mkdir("tagged")
        except WindowsError:                            
            pass
        tokens_list=[]                                  
        squares = []
        open_class_cat =['JJ','JJR','JJS','NN','NNS','NP','NPS','NNP','NNPS','RB','RBR','RBS','VV','VVD','VVG','VVN','VVP','VVZ','FW']

            
#-------------------------------- START TO LOOP INTO FILES ----------------------------------#

        #dictionary with id - path/url correspondence
        dic = {}                              
        i = 1
        N = 0


        for file_type in types:
            N += len(glob.glob(path+"\\profile\\"+file_type))
            
        for file_type in types:
            for doc in glob.glob(path+"\\profile\\"+file_type):  
                if not(re.match('.+bookmark\d{4}\.html$', doc)):
                    dic[i] = os.path.join(path+"\profile\\",doc)
                else:
                    with open(doc, 'r') as fh:
                      link = fh.readline()
                    
                    dic[i] = re.compile('\n').sub('',link)
                                    
#-------------------------------------- TOKENIZATION ----------------------------------------#

                #exclude files that contain no latin characters
                try:
                    fh = open(doc,'r')                          
                    s = fh.read()                               
                    if not(re.match('((.|\n)*[a-zA-Z]+(.|\n)*)+', s)):   
                        continue                                
                except IOError:
                    pass
                finally:
                    fh.close()                              

                s = BeautifulSoup(s, 'html.parser')
                tokens_list = nltk.word_tokenize(s.get_text())        

                tkn = "tokenized_text_%04d.txt"%i           
                with open(tkn_path+tkn,'w') as fh:
                  for each_token in tokens_list:              
                      if not(re.search('&',each_token)) and not(each_token.isspace()):
                        fh.write(each_token.encode('utf-8'))
                        fh.write("\n")                             
        
#------------------------------------------ TAGGING -----------------------------------------#
        
                tag = "tagged_output_%04d.txt"%i
                subprocess.call('.\\TreeTagger\\bin\\tree-tagger.exe -token -lemma .\\TreeTagger\\lib\\english.par "'+tkn_path+tkn+'">"'+tag_path+tag+'"',shell=True)

#-------------------------------------- REMOVE STOP WORDS -----------------------------------#
        
                with open(tag_path+tag, 'r') as fh:
                  lemmas = []
                  for line in fh.readlines():
                      op = line.split()
              
                      
                      if ((op[1] in open_class_cat) and (op[2] != '<unknown>') and (op[2] != '@card@')and (op[2] != '@ord@')and (op[2] != '%')):
                          p = re.compile('(^[\w]{1}$)|(^[\w]+[\.]$)|(^[\w]-[0-9]+)|(^[\w]-[\w])|(^[\w]-)|(-[\w]-[\w]-[\w])|([0-9]+-[0-9]+)|(^[0-9]+$)|((^[\w])([\d]$))')
                          op[2] = p.sub('', op[2])
                          #------------------------------- START CREATING THE INVERTED INDEX --------------------------#
                          if (op[2] != ''):
                              if op[2].lower() not in inverted_index:
                                 inverted_index[op[2].lower()] = {}  
                              lemmas.append(op[2].lower())
                              if(op[2].lower() not in noun_dictionary and (op[1] == 'NN' or op[1] == 'NNS') and op[2] != '<unknown>'):    
                                  noun_dictionary[op[2].lower()] = {}                                                                     
                              if ((op[1] == 'NN' or op[1] == 'NNS') and op[2] != '<unknown>'):                
                                  noun_dictionary[op[2].lower()][i] = 0
                                                               
                u_lemmas = list(set(lemmas))

                
#--------------------------------- CALCULATING SUM OF (tf*idf)^2 ----------------------------#
                
                squares.append(0)
                for lemma in u_lemmas:
                    
                    inverted_index[lemma][i] = int(lemmas.count(lemma))  
                    tf = float(lemmas.count(lemma))
                    if lemma in noun_dictionary.keys():
                      noun_dictionary[lemma][i] = tf
                    idf = float(math.log10(N/len(inverted_index[lemma])))
                    squares[i-1] += float(pow(tf*idf,2))
                i += 1
        
#------------------------ CREATING INVERTED INDEX AND SAVING IT IN XML FILE -----------------#
                
        del  u_lemmas, lemmas                
        top20 = []
        
        with open("inverted_index.xml", 'w') as fh_index:
          fh_index.write('<?xml version=\"1.0\" ?>\n')
          fh_index.write('<inverted_index>\n')
          for lemma in inverted_index:     
              fh_index.write("\t<lemma name=\""+lemma+"\">\n")
              for doc_id,term_frequency in inverted_index[lemma].items():
                  tf = float(term_frequency)
                  #idf=log10(total documents/number of documents that contain lemma)
                  idf=float(math.log10(N/ len(inverted_index[lemma])))
                  weight=float(float(tf*idf)/float(math.sqrt(squares[doc_id-1])+1))
                  inverted_index[lemma][doc_id] = weight    
                  fh_index.write("\t\t<document id=\"%d\" weight=\"%f\"/>\n"%(doc_id,weight))
              fh_index.write('\t</lemma>\n')
          fh_index.write('</inverted_index>\n')
          fh_index.write('<doc_index>\n')
          for i in dic:
              fh_index.write('\t<matching id="%d" path="'%i+dic[i]+'"\>\n')
          fh_index.write('</doc_index>\n')
        

#------------------------------- FIND TOP 20 POPULAR NOUNS ----------------------------------#
        noun_list = []
        noun_freq_list = []
        for lemma in noun_dictionary:
            sum_w = 0                       
            for freq in noun_dictionary[lemma].values():
                sum_w += freq
            noun_list.append(lemma)
            noun_freq_list.append(float(sum_w/N))
                
        for j in range(len(noun_list)):
            top20.append((noun_list[j],noun_freq_list[j]))
        top20 = sorted(top20, key=itemgetter(1),reverse=True)
        top20 = top20[:20]
        
#--------------------------------- DESTROY REDUNDANT ITEMS ----------------------------------#
        del tokens_list, noun_dictionary, noun_list, noun_freq_list, squares


#---------------------------------- RUN PROFILE ANALYSIS ------------------------------------#

        step = 4
        const_step = step
        top20=top20+top20[:step]
        WSD = {}
        while(step<=len(top20)):
            #print step
            syns = []
            pointer = []
            if step<=20:
                pointer=range(step-const_step,step)
            else:
                pointer=range(step-const_step,20)
                pointer +=range(0,step-20)
            for j in pointer:
                if(wordnet.synsets(top20[j][0], pos=wordnet.NOUN)):
                    syns.append(wordnet.synsets(top20[j][0], pos=wordnet.NOUN))
                else:
                    syns.append((1,1))
            
            confs = [()]
            for x in syns:
                confs = [i + (y,) for y in x for i in confs]
                
            max_conf=0
            max_sim=0
            for conf in confs:
                combinations = list(itertools.combinations(conf,2))
                sim = 0
                for pair in combinations:
                    if(pair[0] is not 1 and pair[1] is not 1):
                        sim += wordnet.wup_similarity(pair[0], pair[1])

                sim = float(sim)/float(len(combinations))
                if(sim >= max_sim):
                    max_sim = sim
                    max_conf = confs.index(conf)
                    
            j=0  
            for element in confs[max_conf]:
                if pointer[j] not in WSD:
                    WSD[pointer[j]] = []
                WSD[pointer[j]].append(element)
                j += 1
            step += 1

       
        t1 = time.time()
        time = (t1-t0)                                  
        minutes = time/60                               
        sec = time%60
        print ("Profile Analysis completed in %d minutes and %d seconds"%(minutes, sec))
        print ("Your interests are represented from the following nouns and their definitions: \n")
        j=0
        for element in WSD:
            if most_common_func(WSD[j]) is not 1:
                print (most_common_func(WSD[j]).name()+": "+most_common_func(WSD[j]).definition())
            j+=1
        
#------------------------- LOADING INVERTED INDEX FROM XML FILE -----------------------------#
            
    elif(x is '2'):
        flag = 0
        try:
            len(dic)
        except NameError:
            dic = {}
            flag = 1
        else:
            pass
      
        try:
            len(inverted_index)
        except NameError:
            print "No index was created recently! Checking for a saved copy... "
            try:
                with open('inverted_index.xml') as f: pass
            except IOError as e:
                print 'There was no saved index found!\n\n'
            else:
                print "A saved index was found. Loading...!"
                inverted_index = {}
                fh = open("./inverted_index.xml", 'r')
                for line in fh.readlines():
                    if(re.match('(.|\n)*<lemma', line)):
                        lemma = re.search('"(.*)"', line).group(1)
                        inverted_index[lemma] = {}
                    elif(re.match('(.|\n)*<document', line)):
                        op = line.split('"')
                        inverted_index[lemma][int(op[1])] = float(op[3])
                    elif(re.match('(.|\n)*<matching', line) and flag):
                        op = line.split('"')
                        dic[int(op[1])] = op[3]
                    else:
                      continue
            
#------------------------------ SEARCH QUERY IN INVERTED INDEX ------------------------------#

        
          
        try:                        
            len(inverted_index)
        except NameError:           
            print "\nIndex hasn't been created or loaded!\n"
        else:
            while(True):
                import time
                text_ID_list = []
                weight_list = []
                index_result = []

                query = raw_input('Please insert queries or -1 to exit: \n')
                if query == '-1':
                    print "Exiting Index...\n\n"
                    break
                t0 = time.time()
                query_list = query.split()

                for each_query in query_list:   
                    if each_query in inverted_index.keys():  
                        for text_id, weight in inverted_index[each_query].items():
                            if text_id not in text_ID_list:
                                text_ID_list.append(text_id)  
                                weight_list.append(weight)  
                            else:
                                text_pointer = text_ID_list.index(text_id) 

                                                            
                    else:
                        print("\nCouldn't be found in index!!\n")
                        break
                for j in range(len(text_ID_list)):     
                    if weight_list[j] > 0:          
                        index_result.append((text_ID_list[j],weight_list[j]))
                query_xml = sorted(index_result, key=itemgetter(1),reverse=True)

                t1 = time.time()
                time = (t1-t0)
                if len(query_xml)>0:
                    for doc_id,weight in query_xml: 
                        print ("ID: %d Path/URL: "%doc_id+dic[doc_id]+"\nCosine Similarity: %f\n"%weight)
                
                else:
                    print("Query appears in every file or doesn't appear at all")
                print("Respond time = %f\n"%time)
            
#-------------------------------------- EXIT PROGRAM ----------------------------------------#
            
    elif(x is '3'):
        break
