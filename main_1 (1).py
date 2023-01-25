import mysql.connector
import requests
import sys
import xml.etree.ElementTree as ET
from requests_html import HTMLSession




def GetIDNext(ID):
    return (ID+1)

def getDB():
    DB=mysql.connector.connect(host="localhost",user="root",database="summer_project_new")
    return DB

def DBSelect(SQL):
    mydb =getDB()
    mycursor = mydb.cursor()
    mycursor.execute(SQL)
    myresult = mycursor.fetchall()
    return myresult

def DBSelectWithValues(SQL,val):
    mydb =getDB()
    mycursor = mydb.cursor()
    mycursor.execute(SQL,val)
    myresult = mycursor.fetchall()
    return myresult

def DBInsert(SQL,Val):
    mydb = getDB()
    mycursor = mydb.cursor()
    mycursor.execute(SQL,Val)
    mydb.commit()
    myresult = mycursor.fetchall()
    return myresult

def GetIRITTeamNames(url):
    s = HTMLSession()
    r = s.get(url)
    team = r.html.find('#tab-3 ul li a')
    members=[]
    for member in team:
        members.append(member.text)
    return members

def SubmitIRITDepartment(sortname,fullname,link,country,subjects):
    DepartmentName=sortname
    DescriptiveName=fullname
    website=link
    Country=country
    Subjects=[]
    for subject in subjects:
        Subjects.append(subject)
    StartID=1000000
    ID=DBSelect("SELECT MAX(RGroupID) FROM researchgroup")
    if(ID[0][0]==None):
        nextID=StartID
    else:
        nextID=GetIDNext(ID[0][0])
    
    Sql="INSERT INTO `researchgroup` (`RGroupID`, `RGroupName`, `RGroupFullName`, `RGroupCountry`) VALUES (%s, %s, %s,%s);"
    Val=(nextID,DepartmentName,DescriptiveName,Country)
    try:
        DBInsert(Sql,Val)
    except:
        print("SubmitIRITDepartment Data Insertion Failed")

def getReaserchTeamID(departmentname):
    val=(departmentname,)
    Sql="SELECT RGroupID FROM `researchgroup` WHERE RGroupName=%s"
    ID=DBSelectWithValues(Sql,val)
    return ID


def SubmitIRITTeam(url,departmentname):
    TeamMembers=[]
    Team=GetIRITTeamNames(url)
    for Member in Team:
        TeamMembers.append(Member)
    GroupID=getReaserchTeamID(departmentname)
    for Author in TeamMembers:
        FullName=str(Author).split()
        if(FullName[0] and FullName[1]):
            AuthorFname=FullName[0]
            AuthorLname=FullName[1]
            StartID=2000000
            ID=DBSelect("SELECT Max(AuthorID) FROM author")
            if(ID[0][0]==None):
                nextID=StartID
            else:
                nextID=GetIDNext(ID[0][0])
            Sql="INSERT INTO `author` (`AuthorID`, `FirstName`, `Surname`) VALUES (%s, %s, %s);"
            val=(nextID,AuthorFname,AuthorLname)
            try:
                DBInsert(Sql,val)
            except:
                print("SubmitIRITTeam Author Data Insertion Failed")
            Sql="INSERT INTO `authorrgroup` (`AuthorID`, `RGroupID`) VALUES (%s, %s);"
            val=(nextID,GroupID[0][0])
            try:
                DBInsert(Sql,val)
            except:
                print("SubmitIRITTeam AuthorGroup Data Insertion Failed")

def GetAuthors():
    Authors=DBSelect("SELECT FirstName,SurName FROM Author")
    return Authors 

def getAuthorPublications():
    Authors=GetAuthors()
    for Author in Authors:
        response = requests.get("https://dblp.org/search/publ/api?q="+Author[0]+"$"+Author[1]+"$"+"&")
        if(response):
            tree = ET.ElementTree(ET.fromstring(response.text))
            root = tree.getroot()
            for hit in root.iter('hits'):
                TotalHits=hit.attrib
                HitCount=int(TotalHits["total"])
            if(HitCount<=1000):
                for hits in root.findall('hits'):
                    for hit in hits.findall('hit'):
                        for info in hit.findall('info'):
                            for authors in info.findall('authors'):
                                for PaperAuthor in authors.findall('author'):
                                    if(str(PaperAuthor.text).lower()==str(Author[0]+" "+Author[1]).lower()):
                                        AuthorFound=True
                        if(AuthorFound==True):                            
                            if(info.find('title')!=None):
                                PaperTitle=info.find('title').text
                                print(info.find('title').text)
                            if(info.find('venue')!=None):
                                PaperVenue=info.find('venue').text
                                print(info.find('venue').text)
                            if(info.find('type')!=None):
                                PaperType=info.find('type').text
                                print(info.find('type').text)
                            if(info.find('year')!=None):
                                PaperYear=info.find('year').text 
                                print(info.find('year').text)
                            print("---------------------------------------------------------")
                            
                        #sys.exit() 
#gives the links of all the irit teams in each department
def get_teams_link(url):
    r = s.get(url)
    links=[]
    department = r.html.find('div.entry-content tr')
    for team in department:
        links.append((team.find('a',first = True).attrs['href']))
    print(links)
    return links
#gives permanent members for a single group
def get_permanent(url):
    s = HTMLSession()
    r = s.get(url)
    team = r.html.find('#tab-3')
    permanent = team[0].find('div.listMemberEq', first = True)
    div = permanent.find('ul li a') 
    #post = permanent.find('ul li') 
    members=[]
    #jobTitle=[]
    for member in div:
        members.append(member.text)
    #for position in post:
    #    jobTitle.append(position.text.strip())
    #return print(members, jobTitle)
    return members

#getting all urls
url= 'https://www.irit.fr/en/research/departments-research-teams/'
urls = get_teams_link(url)

#gives all the permanent members of all teams in irit
def getAll_permanent():
    permanent_names = []
    for url in urls:
        #print(get_members(url))
        permanent_names.append(get_permanent(url))
        
    return permanent_names

#loads all the permanent members into the JobType column in author table
def load_permanent(permanent_members):

    authors= GetAuthors()

    for authors in permanent_members:
        Sql="INSERT INTO `author` (`JobType`) VALUES (%s);"
        Val=('Permanent')
        try:
            DBInsert(Sql,Val)
        except:
            print("SubmitIRITDepartment Data Insertion Failed")
   

permanent_members= getAll_permanent()

load_permanent(permanent_members)













#-------------Research Teams Add----------#
#sub=['AI','CI','PI']
#SubmitIRITDepartment('AI','Artificial Intelligence','https://www.irit.fr/en/departement/dep-artificial-intelligence/adria-team/','France',sub)

#-------------Authors Add----------#
#SubmitIRITTeam('https://www.irit.fr/en/departement/dep-artificial-intelligence/adria-team/','AI')




