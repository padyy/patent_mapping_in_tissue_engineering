import epo_ops, json, math, time, sys, os
import xml.etree.ElementTree as ET

if(len(sys.argv) < 3):
    sys.argv.append(str(int(sys.argv[1])-1))

for year in range(int(sys.argv[1]),int(sys.argv[2]),-1):
    print('Getting patents for year '+str(year)+'...')
    with open('DataFull/tissue_engineering_patents_'+str(year)+'.json', 'w') as outfile:
        
        #Initialize the file
        outfile.write("[")

        # Instantiate client
        client = epo_ops.Client(key='ezr4YBielRACa3kG9TyTnusaf41E3PVg', secret='m5n69FP6ozAE8QyP')  

        # Result List
        entriesList = []

        #Create the total Results placeholder
        totalResults = 100000

        #Begin count for current page
        begin_count = 1

        #End count for current page
        end_count = 99 + begin_count
        
        response = None

        while(begin_count <= totalResults):
            try:
                print({'Page':math.ceil(begin_count/100),'totalResults':totalResults,'pageBegin':begin_count})
                #Query to site for current page
                response = client.published_data_search(
                    cql='((ti=tissue AND ti=engineering) OR (ab=tissue AND ab=engineering)) AND (pd='+str(year)+')',
                    range_begin=begin_count,
                    range_end=end_count
                )

                #Parse data for page
                pageRoot = ET.XML(response.text)
                
                #Get the total number of results
                totalResults = int(pageRoot.find('{http://ops.epo.org}biblio-search').get('total-result-count'))
                
                #For each doc in the results
                for doc in pageRoot.iter(tag="{http://www.epo.org/exchange}document-id"):
                    try:
                        #Create document summary object
                        docSummary = {}
                        
                        #Fill the country for the document
                        try: docSummary['country'] = doc.findtext('{http://www.epo.org/exchange}country')
                        except: None
                        
                        #Fill the document number for the document
                        try: docSummary['doc-number'] = doc.findtext('{http://www.epo.org/exchange}doc-number')
                        except: None
                        
                        #Fill the kind value for the document
                        try: docSummary['kind'] = doc.findtext('{http://www.epo.org/exchange}kind')
                        except: None
                        
                        #Get more info about the document
                        responseInner = client.published_data(  # Retrieve bibliography data
                          reference_type = 'publication',  # publication, application, priority
                          input = epo_ops.models.Docdb(docSummary['doc-number'], docSummary['country'], docSummary['kind']),  # original, docdb, epodoc
                          endpoint = 'biblio',  # optional, defaults to biblio in case of published_data
                          constituents = []  # optional, list of constituents
                        )
                            
                        #Parse the extra information
                        docRoot = ET.XML(responseInner.text)
                        
                        exDoc = docRoot.find('{http://www.epo.org/exchange}exchange-documents').find('{http://www.epo.org/exchange}exchange-document')
                        bibData = exDoc.find('{http://www.epo.org/exchange}bibliographic-data')
                        
                        #Get date for document
                        try: docSummary['date'] = bibData.find('{http://www.epo.org/exchange}publication-reference').find('{http://www.epo.org/exchange}document-id').findtext('{http://www.epo.org/exchange}date')
                        except: None
                        
                        #Create ipcrList
                        ipcrClasses = []
                        
                        #Iterate over the ipcr classifications
                        try: 
                            for clasific in bibData.find('{http://www.epo.org/exchange}classifications-ipcr').iterfind('{http://www.epo.org/exchange}classification-ipcr'):
                                ipcrClasses.append(''.join(clasific.findtext('{http://www.epo.org/exchange}text').split()))
                            docSummary['ipcr'] = ipcrClasses
                        except: None
                        
                        #Create cpcList
                        cpcClasses = []

                        #Iterate over the CPC classifications
                        try: 
                            for clasific in bibData.find('{http://www.epo.org/exchange}patent-classifications').iterfind('{http://www.epo.org/exchange}patent-classification'):
                                cpcClasses.append(
                                    clasific.findtext('{http://www.epo.org/exchange}section')+
                                    clasific.findtext('{http://www.epo.org/exchange}class')+
                                    clasific.findtext('{http://www.epo.org/exchange}subclass')+
                                    clasific.findtext('{http://www.epo.org/exchange}main-group')+
                                    '/'+clasific.findtext('{http://www.epo.org/exchange}subgroup')
                                )
                            docSummary['cpc'] = cpcClasses
                        except: None
                        
                        #Create cpcList
                        priorityClaims = []

                        #Iterate over the CPC classifications
                        try: 
                            for prior in bibData.find('{http://www.epo.org/exchange}priority-claims').iterfind('{http://www.epo.org/exchange}priority-claim'):
                                priorityClaims.append(prior.find('{http://www.epo.org/exchange}document-id').findtext('{http://www.epo.org/exchange}date'))
                            docSummary['priorityClaims'] = priorityClaims
                        except: None
                        
                        #Iterate over the associated parties
                        try:
                            for party in bibData.iterfind('{http://www.epo.org/exchange}parties'):
                                
                                #Create applicants list
                                applicants = []
                            
                                #Iterate over applicants
                                for applicant in party.find('{http://www.epo.org/exchange}applicants').iterfind('{http://www.epo.org/exchange}applicant'):
                                    applicants.append(applicant.find('{http://www.epo.org/exchange}applicant-name').findtext('{http://www.epo.org/exchange}name'))
                                docSummary['applicants'] = applicants
                                
                                #Create inventors list
                                inventors = []
                            
                                #Iterate over inventors
                                for inventor in party.find('{http://www.epo.org/exchange}inventors').iterfind('{http://www.epo.org/exchange}inventor'):
                                    inventors.append(inventor.find('{http://www.epo.org/exchange}inventor-name').findtext('{http://www.epo.org/exchange}name'))
                                docSummary['inventors'] = inventors
                        except: None
                        
                        #Get title of current document
                        try: docSummary['title'] = bibData.findtext('{http://www.epo.org/exchange}invention-title[@lang=\'en\']')
                        except: None
                        
                        #Get abstract for current document
                        try:
                            for abstract in exDoc.findall('{http://www.epo.org/exchange}abstract[@lang=\'en\']'):
                                docSummary['abstract']=list(abstract.itertext())[1]
                        except: None
                        
                        #Form URL for patent
                        try: docSummary['url']='https://worldwide.espacenet.com/publicationDetails/biblio?FT=D&CC='+docSummary['country']+'&NR='+docSummary['doc-number']+docSummary['kind']
                        except: None
                        
                        #Add document to entries List
                        print(docSummary['doc-number'])
                        outfile.write(json.dumps(docSummary)+',')
                    except Exception as ex: 
                        print({'inner exception':ex})
                        
                #Renew values for next page
                begin_count = end_count + 1
                end_count = 99 + begin_count
                if(totalResults < end_count):
                    end_count = totalResults
            
            except Exception as e: 
                print({'outer exception':e})
                time.sleep( 60 )
                
        
        #Close the file
        outfile.seek(outfile.tell() - 1, os.SEEK_SET)
        outfile.write(']')