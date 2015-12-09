#TODO: add in feature to pull most recent map

from qgis.core import *
from PyQt4.QtGui import *
import psycopg2
import os
import csv

#* global vars
#SQL
TABLE_NAME = 'maps.dist_prof_cov_9_21'

#layerz

CSV_LOC = '/Users/ewanog/tmp/dist_prof_out.csv'
ADM3_LOC = '/Users/ewanog/Dropbox (GSC)/2015 Nepal EQ/04 IM/EO_Folder/Ewan Maps/Shape Files/adm3.shp/npl_polbnda_adm3_dis_25k_50k_sdn_wgs84.shp'
ADM4_LOC = '/Users/ewanog/Dropbox (GSC)/2015 Nepal EQ/04 IM/EO_Folder/Ewan Maps/Shape Files/adm4.shp/npl_polbnda_adm4_vdc_25k_50k_sdn_wgs84.shp'

LAY_COV = 'coverage'
LAY_ADM3_SLIM = 'LAY_ADM3_SLIM' 
LAY_ADM3 = 'adm3'
LAY_ADM4 = 'adm4'

#maps
CSV_ADM4_VAL = 'VDC_CODE'
DBK = 'postgresql://shelter:clusterdata@sheltercluster.ci0kkoh87sga.us-east-1.rds.amazonaws.com:5432/shelter'

#QGIS
FILE_LOC = '/Users/ewanog/code/maps/dist_prof_auto.qgs'

def make_file():
    app = QgsApplication([], True)
    app.setPrefixPath('/Applications/QGIS.app/Contents/MacOS', True)
    app.initQgis()

    QgsProject.instance().setFileName(FILE_LOC)

def write_to_csv():
    data, col_names = get_sql_data()
    print 'Writing to CSV'
    with open(CSV_LOC, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(col_names)
        for r in data:
            writer.writerow(r)            
    print 'Written out to %s' % CSV_LOC
    f.close()


def get_sql_data():
    print 'Connecting to DB'
    conn =  psycopg2.connect(DBK)
    cur = conn.cursor()
    print 'Pulling data from %s' % TABLE_NAME
    cur.execute("select * from %s" % TABLE_NAME)
    print 'Data pulled!'
    return cur.fetchall(), get_sql_col_names(cur)

def get_sql_col_names(cur):
    return [desc[0] for desc in cur.description]

def import_layers():
    add = [ (ADM3_LOC, LAY_ADM3, "ogr"),
            (ADM3_LOC, LAY_ADM3_SLIM, "ogr"),
            (ADM4_LOC, LAY_ADM4, "ogr"),
            (CSV_LOC, LAY_COV, "delimitedtext")]

    for v in add:
        layer = QgsVectorLayer(v[0], v[1], v[2])
        print layer.name() + ' name is'    
        try:
            QgsMapLayerRegistry.instance().addMapLayer(layer)
        except Exception, e:
            raise Exception('Invalid Layer for %s!' % str(layer.name()) + str(e))

    print 'len is: ' + str(len(QgsMapLayerRegistry.instance().mapLayers().values()))


def make_dict():
    #make dict
    layer_dict = {}
    for v in QgsMapLayerRegistry.instance().mapLayers().values():
        print 'dict ' +  str(v.name())
        layer_dict[str(v.name())] = v

    return layer_dict


def rm_joins(layer_dict):
    #remove all joins
    for cur_layer in layer_dict.values():
        for j in cur_layer.vectorJoins():
            cur_layer.removeJoin(j.joinLayerId)

    return layer_dict


#update joins
def update(layer_dict):
    for name, cur_layer in layer_dict.iteritems():
      if name not in (LAY_ADM3_SLIM, DIST_SHP):
        cov = layer_dict[VDC_COV]
        cur_layerField='HLCIT_CODE'
        covField = COV_VDC_VAL
        joinObject = QgsVectorJoinInfo()
        joinObject.joinLayerId = cov.id()
        joinObject.joinFieldName = covField
        joinObject.targetFieldName = cur_layerField
        cur_layer.addJoin(joinObject)
        print 'updated %s' % name

    return layer_dict

#do styles
def add_styles(layer_dict):
    for name, cur_layer in layer_dict.iteritems():
      if name not in (LAY_ADM3_SLIM, DIST_SHP):
        myVectorLayer = cur_layer
        good_layer = False
        if '_cgi' in myVectorLayer.name():
            myTargetField = 'vdc_cov_cc'
            good_layer = True
            print 'cgi'
        elif '_tt' in myVectorLayer.name():
            myTargetField = 'vdc_cov_tt'
            good_layer = True
            print 'tt'
        if good_layer:
            myRangeList = []
            myOpacity = 1

            #0 values
            myMin = 0.0
            myMax = 0.0
            myLabel = 'No coverage or data'
            myColour = QColor('#ffffff')
            mySymbol1 = QgsSymbolV2.defaultSymbol(myVectorLayer.geometryType())
            mySymbol1.setColor(myColour)
            mySymbol1.setAlpha(myOpacity)
            myRange1 = QgsRendererRangeV2(myMin, myMax, mySymbol1, myLabel)
            myRangeList.append(myRange1)

            #0-0.5
            myMin = 0.0
            myMax = 0.5
            myLabel = '< 50%'
            myColour = QColor('#aaaaaa')
            mySymbol2 = QgsSymbolV2.defaultSymbol(
                 myVectorLayer.geometryType())
            mySymbol2.setColor(myColour)
            mySymbol2.setAlpha(myOpacity)
            myRange2 = QgsRendererRangeV2(myMin, myMax, mySymbol2, myLabel)
            myRangeList.append(myRange2)

            #0.5-1
            myMin = 0.5
            myMax = 20
            myLabel = '> 50%'
            myColour = QColor('#e33f42')
            mySymbol3 = QgsSymbolV2.defaultSymbol(
            myVectorLayer.geometryType())
            mySymbol3.setColor(myColour)
            mySymbol3.setAlpha(myOpacity)
            myRange3 = QgsRendererRangeV2(myMin, myMax, mySymbol3, myLabel)
            myRangeList.append(myRange3)
            myRenderer = QgsGraduatedSymbolRendererV2('', myRangeList)
            myRenderer.setMode(QgsGraduatedSymbolRendererV2.EqualInterval)
            myRenderer.setClassAttribute(myTargetField)
            myVectorLayer.setRendererV2(myRenderer)
            QgsMapLayerRegistry.instance().addMapLayer(myVectorLayer)

def filter(layer_dict):
    ds = layer_dict['LAY_ADM3_SLIM']
    ds.setSubsetString(u'"DISTRICT" = "Sindhupalchok"')

def rm_cov(layer_dict):
    try:
        QgsMapLayerRegistry.instance().removeMapLayer(layer_dict['coverage'].id())
    except:
        print 'no coverage layer to remove'

def do():
    print 'creating file'
    make_file()

    print 'writing to csv'
#    write_to_csv()

    print 'importing layers'
    import_layers()
    
    print 'make dict'
    d = make_dict()
    
    print 'rm coverage layer'
    rm_cov(d)
    
    print 'make joins'
    d = rm_joins(d)
    
    print 'update'
    d = update(d)
    
    print 'add styles'    
    add_styles(d)

if __name__ == '__main__':
    do()
