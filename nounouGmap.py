# coding=utf-8
import csv,re,sys,codecs, os
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR


TEXT_TOREMOVE_FROMADRESS=[
"Les Bastides du Micocoulier",
"Les Terrasses d'Antibes",
"Residence Le Champagne",
"Les Lavandes",
"Res. Aurelia - villa 27",
"Res. Aurelia",
"villa 27",
"Les Camelias",
"Les Hauts d'Antibes",
"Les Jonquilles",
"Batiment Le Chantarella B",
"Bât 2",
"Les Logis de St Claude - bat. P",
"Les Logis de St Claude",
"bat. P",
"L'Amarante - bat. C",
"Villa Alexandrine",
"Bat 5",
"Villa Le Mistral",
"Les Jardins de Beauvert",
"Res. Elisara - bat. B",
"Villa Mayotte",
"Les Acanthes",
"Domaine de Beauregard - Villa 12",
"Res. Elisara - bat. B",
'"Magda Cottage" Bat E',
"Bat 5",
"- Bat. P",
["126, rue du Bon Air", "1465, ch des Combes"],
["Ensomeille", "Ensoleille"],
"Le Janival",
"La Cesarine",
"la Closeraie - Villa 3",
" A2 ",
"Res Colline Bat L'orangeraie",
"Le Regent - Bloc D",
" Le Corail",
" L'Orchidee",
' "Les Castors"',
"Residence Les Oliviers Bat A"
]

#43.592120, 7.109704 = 965 chemin du puy, 06600 Antibes
#43.5909601,7.1091283 = libanais (+200m)

TEMPLATE_HTML="""
  <tr>
    <td>%s<br/>%s<br/>place:%s<br/>%s<br/>%s</td>
    <td><p style="%s">%s<br/>%s<br/></p>%s<br/>%s</td>
    <td>
        <iframe
          width="600"
          height="450"
          src="https://www.google.com/maps/embed/v1/directions?key="""+KEY+"""&mode=walking&origin=%s&destination=43.592120,7.109704" allowfullscreen>
        </iframe>
    </td>
    <td>
        <!--iframe
          width="600"
          height="450"
          src="https://www.google.com/maps/embed/v1/directions?key="""+KEY+"""&mode=walking&origin=%s&destination=43.5909601,7.1091283" allowfullscreen>
        </iframe-->
    </td>
  </tr>"""



class HistoriqueNounou:
    def __init__(self,name,contact,commentaire, distance):
        self._name=name
        self._contact = contact[0]
        self._commentaire=commentaire
        self._distance=distance
        if contact=="O" :
            self._style = "background-color:powderblue;"
        elif contact=="T" :
            self._style = "background-color:lightgreen;"
        else:
            self._style = "background-color:red;"
            
    def __eq__(self, other):
        return self._name.lower() in other._name.lower() or other._name.lower() in self._name.lower()
        
    def __str__(self):
        return self._name + " contact:" + self._contact + " com:" + self._commentaire


        
#defrault blue.png
DEFAULT_COLOR = "blue"
COLOR_CONTACT = {
 'O' : "red",
 'T' : "purple",
 'X' : "red"
}

class Nounou:
    def __init__(self, dispo, places, proposition, name, adress,phone, updated):
        self._name = name
        self._adress = self.setAdress(adress)
        self._phone=self.setPhone(phone)
        self._dispo=dispo
        self._places=places
        self._proposition=proposition
        self._updated=updated
        
    def __eq__(self, other):
        return self._name.lower() in other._name.lower() or other._name.lower() in self._name.lower()
        
        
    def toLocation(self, arrayHist):
        depuisRue = "https://www.google.com/maps/dir/?api=1&origin="+self._adress+"&destination=43.592120,7.109704&travelmode=walking"
        depuisLibanais = "https://www.google.com/maps/dir/?api=1&origin="+self._adress+"&destination=43.5909601,7.1091283&travelmode=walking"
        label = "Y"
        
        
        if "sans mercredi" in self._proposition.lower() or "sauf mercredi" in self._proposition.lower() or "sans le mercredi" in self._proposition.lower():
            label = "M"
            
        if "temps plein" in self._proposition.lower() and not "partiel" in self._proposition.lower():
            label = "P"
        
        if self in arrayHist:
            index=arrayHist.index(self)
            histN = arrayHist[index]
            return [self._name, self._adress, self._dispo, self._places, self._proposition, self._updated,self._phone, depuisRue, depuisLibanais, COLOR_CONTACT[histN._contact], label, histN._commentaire]
        else :
            return [self._name, self._adress, self._dispo, self._places, self._proposition, self._updated,self._phone, depuisRue, depuisLibanais, DEFAULT_COLOR, label, "empty"]
        
        
        
    def setPhone(self, phone):
        #look for 06
        mobileRegexp=re.compile("(0[6-7]{1} ?([0-9]{2} ?){4})")
        mobile = mobileRegexp.search(phone)
        if mobile:
            return mobile.group(1)
        else:
            fixeRegexp=re.compile("(0[0-9]{1} ?([0-9]{2} ?){4})")
            fixe = fixeRegexp.search(phone)
            if fixe:
                return fixe.group(1)
            else:
                print 'nounou sans tel', phone
                sys.exit()
                
                
    def setAdress(self, adress):	
        if ( "girardi martine" in self._name.lower() ) :
            #print "SPECIAL ADDRESS FOR GIRARDI Martine"
            return "1485 Chemin de St Claude, 06600 Antibes"

	
        finalAdress=adress.replace('06 600', '06600')
        finalAdress=finalAdress.replace('06 160', '06160')
        finalAdress=finalAdress.replace('06 410', '06410')
        finalAdress=finalAdress.replace('bis ', '')
        finalAdress=finalAdress.replace(' bis', '')
        
        
        for text in TEXT_TOREMOVE_FROMADRESS:
            if len(text)==2:
                finalAdress=finalAdress.replace(text[0], text[1])
            else:
                finalAdress=finalAdress.replace(text, ' ')
        
        street=None
        city=None
        streetRe=re.compile("(\d+)?([ ,]*)(chemin|avenue|ch|av|traverse|boulevard|bld\.|bd|bd\.|ave|rue|cours|allee|impasse|voie|route)[ .](.+)", re.IGNORECASE  )
        
        lookForInfo=finalAdress.split('\n')
        #print "origin", adress, "end"
        for line in lookForInfo:
            streetTest = streetRe.search(line)
            if streetTest and not street:
                if streetTest.group(1) :
                    number = streetTest.group(1)
                else:
                    number = "1 "
                street=number+streetTest.group(2)+streetTest.group(3)+" "+streetTest.group(4)
                #print "Street", line, streetTest.group(3)
            if "06600" in line:
                city="06600" + line.split('06600')[1]
            if "06160" in line:
                city="06160" + line.split('06160')[1]
            if "06410" in line:
                city="06410" + line.split('06410')[1]
                
                
                
        if not street :
            streetRe=re.compile("(\d+)?(.*)(chemin|avenue|ch|av|traverse|boulevard|bld\.|bd|bd\.|ave|rue|cours|allee|impasse|voie|route)(.+)", re.IGNORECASE  | re.DOTALL)
            streetTest = streetRe.search(adress)
            if streetTest:
                if streetTest.group(1) :
                    number = streetTest.group(1)
                else:
                    number = "1 "
                street=number+streetTest.group(2)+streetTest.group(3)+streetTest.group(4)
                print "fail" , adress, "end"
            else:
                print "fail"
                
        if not city:
            city="06600 Antibes"
            
            
        if "06600" in street:
            street=street.split('06600')[0]
        if "06160" in street:
            street=street.split('06160')[0]
        if "06410" in street:
            street=street.split('06410')[0]
            
        if not city or not street:
            print adress
            sys.exit()
        
        finalAdress =     street + ", " + city
                
        #if "avande" in adress:
            #sys.exit()

                
        return finalAdress
        
    
    def toHtml(self, arrayHist):
        if self in arrayHist:
            index=arrayHist.index(self)
            theText =  TEMPLATE_HTML % (self._name, self._dispo,self._places,self._proposition,self._updated, arrayHist[index]._style, "contact:"+arrayHist[index]._contact, "commentaire:"+arrayHist[index]._commentaire, 
                                    self._phone, self._adress, self._adress, self._adress)
            return theText
        else :
            return TEMPLATE_HTML % (self._name, self._dispo,self._places,self._proposition,self._updated, "background-color:yellow;",  "contact:n/a", "commentaire:n/a" ,
                                    self._phone, self._adress, self._adress, self._adress)

    
    def __str__(self):
        return self._name + "\n" + "\tAdress:" + self._adress + "\n\tPhone:" + self._phone + "\n"

        
        
#THIS IS THE MAIN
#print TEMPLATE_HTML
mairieFile=csv.reader(open(sys.argv[1]), delimiter=';')

outfile=open('newCarte.html','w')
outfile.write("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Nounou</title>
</head>

<body>

<table style="width:100%">
    <tr>
        <th>Nom,Dispo,places,Offre,MaJ</th>
        <th>Historique,telephone, adresse</th>
        <th>rue</th>
        <th>portillon(+200m)</th>
    </tr>
""")

outfile2=open('newCarte2.html','w')
outfile2.write("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Nounou2</title>
</head>

<body>

<table style="width:100%">
    <tr>
        <th>Nom,Dispo,places,Offre,MaJ</th>
        <th>Historique,telephone, adresse</th>
        <th>rue</th>
        <th>portillon(+200m)</th>
    </tr>
""")

historyFile=csv.reader(open('historique.csv', 'rU'), delimiter=';')

HistNouou=[]
MairieNounou=[]

for row in historyFile:
    #name,contact,commentaire, distance
    HistNouou.append(HistoriqueNounou(row[0],row[1],row[3], row[2]))


total=0
for row in mairieFile:
    print row
    if len(row) > 4:
        #dispo, places, proposition, name, adress,phone, updated):
        #theNounou=Nounou(row[0],row[3],row[4],row[5],row[6],row[7],row[8])
        theNounou=Nounou(row[0],row[2],row[3],row[4],row[5],row[6],row[7])
        #print row
        if total<50:
            outfile.write(theNounou.toHtml(HistNouou))
        else:
            outfile2.write(theNounou.toHtml(HistNouou))
            
        MairieNounou.append(theNounou)
        print theNounou
        total+=1
        #break
    
    
    
    
outfile.write("""
</table>

</html>
""")
outfile2.write("""
</table>

</html>
""")


print "ALL OK", total


if len(sys.argv) > 2 :
    print "CarteGlobal"

    strTemplate = open('template.html', 'r').read()


    exempleLocations = [
      ['Location A Name', '47 avenue Paul Eluard , 06600 Antibes', 'Location 1 URL', 'Location 1 URL2'],
      ['Location B Name', '741, Ch des Moyennes Breguieres , 06600 Antibes', 'Location 2 URL', 'Location 1 URL2'],
      ['Location C Name', '233, route de Grasse , 06600 Antibes', 'Location 3 URL', 'Location 1 URL2']
    ]

    locations = []

    totalLoc=0
    for aNounou in MairieNounou:
        totalLoc+=1
        if totalLoc < 500 :
            locations.append(aNounou.toLocation(HistNouou))


    filenameGlobal = 'CarteGlobal.html'
    os.chmod(filenameGlobal, S_IWUSR|S_IREAD)
    outfile3=open(filenameGlobal,'w')
    outputGlobal = strTemplate.replace('VARIABLE_FROM_PYTHON_SCRIPT',str(locations)).replace('CARTE_GLOBAL_KEY',CARTE_GLOBAL_KEY)
    outfile3.write(outputGlobal)
    os.chmod(filenameGlobal, S_IREAD|S_IRGRP|S_IROTH)
    #print str(locations)
else:
    print "NO CarteGlobal"

#print strTemplate
#print outputGlobal

