import streamlit as st
import geopandas as gp
import leafmap.foliumap as leafmap
import requests
import matplotlib.pyplot as plt
import os
import shutil
import subprocess
from shapely.geometry import Polygon, LineString, Point
from folium.plugins import Draw
import folium

#add a uploader and set the type to geojson

st.header("Welcome to Our Map Servicley App")

# get the user choice for using the app on a single file or double files

st.subheader("Do You Want To Deal One or Two Files?")

userUsageChoice = st.radio('Please choose between the two choices',('Single File at a Time','Double Files at a Time'))

if userUsageChoice == 'Single File at a Time':
     
    input = st.file_uploader("Please upload a geojson file", type='geojson', accept_multiple_files=False)

    if input:

        # to get the input file name without its extension

        inputStrFormat = input.name.split('.')
        filename =inputStrFormat[0]

        # after user uploads a file - read the file as a geodataframe

        inputasGDF = gp.read_file(input)

        # add two options for the user - convert the file into other formats uploaded and download it - display it on a map and make analysis on it

        # if use chooses to convert the file and download it 

        st.success("Success!!!  You Uploaded a File Successfully, Now Choose The Next Step!")

        convertandDownload = st.checkbox('Convert Uploaded File and Download it')
        displayandAnalyze = st.checkbox('Display Uploaded File on Map and Analyze')

        if convertandDownload:

            # provide the user with a drop-down list that has format options and inside it the download button for those formats 

            option = st.selectbox(
            'Please Pick a Format to Transform the Uploaded File Into:',
            ('Shapefile', 'Geopackage'))
                    
            # for shapefile and for file geodatabase since there are multiple files we have to compress so that the downloaded files are valid and correct
        
            if option == "Shapefile":

                # so lets create a directory for the shapefile
                
                os.mkdir(f"{filename}_as_shpfile")

                # Lets convert the file to shapefile inside that directory

                shp = inputasGDF.to_file(f'{filename}_as_shpfile/{filename}.shp')

                # now lets compress the file using the shutil library

                shutil.make_archive(f'{filename}','zip',f'{filename}_as_shpfile')

                # now lets open the zip file and download the compressed shapefile

                st.success("Converted to ShapeFile Successfully, Click to Download the Converted File!!!")
                with open(f"{filename}.zip", "rb") as shpFile:
                    btn = st.download_button(
                    label="Download ShapeFile",
                    data=shpFile,
                    file_name=f"{filename}_as_shpfile.zip",
                    )

                # now one of the most important steps is to delete the directory and the compressed file

                # so that we don't create folders in vain and to avoid errors if the user upload the same file again
            
                shutil.rmtree(f'{filename}_as_shpfile')
                os.remove(f"{filename}.zip")

            else:        
                inputasGDF.to_file(f"{filename}_as_geopkg.gpkg")
                st.success("Converted to GeoPackage Successfully, Click to Download the Converted File!!!")
                with open(f"{filename}_as_geopkg.gpkg", "rb") as gpkgFile:
                    st.download_button(
                        label = 'Download Geoackage ',
                        file_name = f"{filename}.gpkg",
                        data = gpkgFile
                        )
                
                # let's remove the geopackage so that  we don't have alot of duplicate files

                os.remove(f"{filename}_as_geopkg.gpkg")

        if displayandAnalyze:

            # we add a map to display the user uploaded file on and then we add the user data as a geodataframe

            # now we have 2 cases : 

            # case 1 -- a single layer analysis: if the user wants to get the center of the uploaded features and then find the shortests path between two centers

            st.success("Added Features To The Map Successfully !!! Please Pick Your Desired Analysis!")
            centeriodAndShortestPath = st.checkbox('Get Centeriods and Find The Shortest Path')

            if centeriodAndShortestPath:

            # now we explain to the user what he needs to do to get the shortest path between two centeriods

                st.success("Success!!! You Generated The Centeriods For The Uploaded Features!")
                st.subheader("By Clicking on a Centeriod You Get The Coordinates of The Point")
                st.subheader("Enter The Coordinates in The Resquested Format To Get The Shortest Path Between Any Two Centroids You Picked ")
                st.subheader("Please Don't Choose The same point For Start And Ending")
                startPoint = st.text_input('Please Enter The Coordinates of The Starting Point ', placeholder ="Longtitude First , and Then Lattitude (Without Any Spaces Please)")
                endPoint = st.text_input('Please Enter The Coordinates of The Ending Point ', placeholder ="Longtitude First , and Then Lattitude (Without Any Spaces Please)")
                getRoute = st.button('Get Shortest Route')
                map = leafmap.Map()
                map.add_gdf(inputasGDF)
                inputasGDF['centroid'] = inputasGDF.centroid

                for r in inputasGDF.iterrows():
                    lat = r[1][1].y
                    lon = r[1][1].x
                    folium.Marker(location=[lat, lon],
                        popup=f'Longtitude : {lon}\nLatitude : {lat}').add_to(map)
                if startPoint and endPoint and getRoute:
                    st.write(startPoint)
                    st.write(endPoint)
                    if startPoint == endPoint:
                        st.error("Please Don't Choose The Same Point as Starting and Ending Point ")
                    else:
                        startCoords = startPoint.split(',')
                        endCoords = endPoint.split(',')
                        headers = {
                        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                            }
                        responseRoute = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf624805d0ade13d2545ef97d45b2cc524c062&start={startCoords[0]},{startCoords[1]}&end={endCoords[0]},{endCoords[1]}',headers=headers)
                        responseRouteGDF = gp.read_file(responseRoute.text)
                        routeStyle = {
                            "stroke": True,
                            "color": "#FF0000",
                            "weight": 4,
                            "opacity": 1,
                            }
                        map.add_gdf(responseRouteGDF,style=routeStyle)
                map.to_streamlit(height=600)


                 






        # Now if the user wants to display the input and make analysis on a map(its not one option or the other the user can choose both options)

if userUsageChoice == 'Double Files at a Time':
        
        # case 2 -- a double layer analysis : if the user wants to make an intersection, union or difference between 2 layers and downloades that data 

        #  first we modulate a function that makes the analysis displays it on the map and prints it and then call it at each analysis

        def make_Show_Download_Analysis(analysisToMake,analysisDF1,analysisDF2,analysisLyrName,lyrAsGeojson,geoAnalysis,mapToDisplay,lyrStyles):

                # we use the overlay method to get the intersect between the two layers (the same method will be used to union and to erase difference)

                analysisLyrName = gp.overlay(analysisDF1,analysisDF2,how=analysisToMake)

                # we convert the analysis layer to geoJSON so that The User Can Download it

                analysisLyrName.to_file(f'{lyrAsGeojson}.geojson')

                st.success('Successfully Converted the Intersection Analysis Layer To Geojson, Click To Download it!')
                with open(f'{lyrAsGeojson}.geojson','rb') as geoAnalysis:
                    st.download_button(label=f'Download your {analysisToMake}',
                        data=geoAnalysis,
                        file_name=f'{lyrAsGeojson}.geojson')
                
                # Remove the Converted File after you closed it (outside the with open)

                os.remove(f'{lyrAsGeojson}.geojson')

                # Add the Layer To the Map and Then Display it

                st.success(f'The {analysisToMake} Between The Two Layers is Displayed With Clear Color On The Map')
                mapToDisplay = leafmap.Map()
                mapToDisplay.add_gdf(analysisDF1,style=lyrStyles[0])
                mapToDisplay.add_gdf(analysisDF2,style=lyrStyles[1])
                mapToDisplay.add_gdf(analysisLyrName, style=lyrStyles[2])
                mapToDisplay.to_streamlit(height=500)

        #  then we get the user choice for analysis 

        userMultipleLyrAnalysisChoice = st.radio('Please Choose Which Analysis You Want To Perform',('intersection-union-difference','Risk Assessment'))
        if userMultipleLyrAnalysisChoice =='intersection-union-difference' :

            # we add a uploader that accepts mutiple file from the user at once

            multipleLayers = st.file_uploader("Please Upload Your Input Files",type="geojson",accept_multiple_files=True)

            # if the user uploads atleast 2 files then we can go on otherwise we tell him to upload more files

            if len(multipleLayers) ==2:

                # we project the layers to the coordinate system that can be displayed in meters on the map

                firstLayerGDF = gp.read_file(multipleLayers[0]).to_crs('EPSG:3857') 
                secondLayerGDF = gp.read_file(multipleLayers[1]).to_crs('EPSG:3857') 

                # now we get the user choice for the analysis performed

                analysisChoice = st.selectbox('Please Choose Which Analysis You Would Like To Perform on The Data',('intersection','difference','union'))
                
                # lets add styles to make the layers and analysis appear on the map better

                regular_analysis_Style = {
                "stroke": True,
                "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                "fill": True,
                "fillColor": "#006600",
                "fillOpacity": 0.5,
                }
                input_layers_Style = {
                "stroke": True,
                "color": "#ff0000",
                "weight": 1,
                "opacity": 1,
                "fill": True,
                "fillColor": "#8d99ae",
                "fillOpacity": 0.5,
                }
                regularAnalysisLyrStyles = [input_layers_Style,input_layers_Style,regular_analysis_Style]
                if analysisChoice == 'intersection':
                    make_Show_Download_Analysis(analysisToMake=analysisChoice,analysisDF1=firstLayerGDF,analysisDF2=secondLayerGDF,analysisLyrName='intersectonLayer',lyrAsGeojson='intersctLyr',geoAnalysis='geoIntersect',mapToDisplay='mIntersct',lyrStyles=regularAnalysisLyrStyles)
                elif analysisChoice == 'difference':
                    make_Show_Download_Analysis(analysisToMake=analysisChoice,analysisDF1=firstLayerGDF,analysisDF2=secondLayerGDF,analysisLyrName='diffLayer',lyrAsGeojson='diffLyr',geoAnalysis='geoDiff',mapToDisplay='mDiff',lyrStyles=regularAnalysisLyrStyles)
                else :
                    make_Show_Download_Analysis(analysisToMake=analysisChoice,analysisDF1=firstLayerGDF,analysisDF2=secondLayerGDF,analysisLyrName='unionLayer',lyrAsGeojson='unionLyr',geoAnalysis='geoUnion',mapToDisplay='mUnion',lyrStyles=regularAnalysisLyrStyles)
            else:
                st.error("Error!!! Please Upload No More and No Less Than 2 Files in Order To Be Able To Perform The Analysis!")
        elif userMultipleLyrAnalysisChoice =='Risk Assessment' :

            # user have choosen a risk assessment analysis so we have to explain the sequence 
              
            st.header("Risk Assessment")
            st.subheader("The First File You Upload is The Source of Danger")
            st.subheader("The Second File You Upload is The Test Area")
            st.subheader("Then you Need to Enter The Raduis of Effect for that Danger Source")
            st.subheader('You Will Get The Intersection Between The Effective Danger Zone And The Test Area')

            # Now The User Has To Upload the 2 files to test

            multiLyrForRskAssess = st.file_uploader("Please Upload Your Assesment Files",type='geojson',accept_multiple_files=True)
            if len(multiLyrForRskAssess) == 2:
                
                # we project the layers to the coordinate system that can be displayed in meters on the map

                dangerSrcGDF = gp.read_file(multiLyrForRskAssess[0]).to_crs('EPSG:3857')
                testAreaGDF = gp.read_file(multiLyrForRskAssess[1]).to_crs('EPSG:3857') 

                # Now We Get The area of effect from the user

                radius = st.number_input("please enter your area's of effect radius in meter")

                if radius:
                     
                      # now we start with making the area of effect -- which will be done using Buffer

                      # now apply the buffer only on the geometry column

                      buffer = dangerSrcGDF["geometry"].buffer(radius) # this is returns a geoseries but we want it as a geodataframe
                      bufferGDF = gp.GeoDataFrame(geometry=buffer) # so we convert it into a geodata frame and tell it that the geomtry column is the buffer

                      # lets make a style so that the ares in risk appear clearly on the map

                      risk_analysis_Style = {
                            "stroke": True,
                            "color": "#ff0000",
                            "weight": 1,
                            "opacity": 1,
                            "fill": True,
                            "fillColor": "#800020",
                            "fillOpacity": 0.6,
                        }
                      danger_Source_Style = {
                            "stroke": True,
                            "color": "#ff0000",
                            "weight": 1,
                            "opacity": 1,
                            "fill": True,
                            "fillColor": "#5D3FD3",
                            "fillOpacity": 0.6,
                        }
                      test_area_Style = {
                            "stroke": True,
                            "color": "#ff0000",
                            "weight": 1,
                            "opacity": 1,
                            "fill": True,
                            "fillColor": "#FF5733",
                            "fillOpacity": 0.4,
                        }
                      riskAnalysisStyles = [danger_Source_Style,test_area_Style,risk_analysis_Style]

                      # now we make the risk assessment

                      make_Show_Download_Analysis(analysisToMake='intersection',analysisDF1=bufferGDF,analysisDF2=testAreaGDF,analysisLyrName='riskEffectLayer',lyrAsGeojson='effectZoneLyr',geoAnalysis='dangerAreaofEffect',mapToDisplay='mEffect',lyrStyles=riskAnalysisStyles)
            else:
                st.error("Error!!! Please Upload No More and No Less Than 2 Files in Order To Be Able To Perform The Analysis!")
             



        





