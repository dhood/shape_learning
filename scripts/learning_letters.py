#!/usr/bin/env python
# coding: utf-8

from shape_learning.shape_learner_manager import ShapeLearnerManager
from shape_learning.shape_learner import SettingsStruct
from shape_learning.shape_modeler import ShapeModeler #for normaliseShapeHeight()

import numpy
import matplotlib.pyplot as plt

from kivy.config import Config
Config.set('kivy', 'logger_enable', 0)
Config.write()

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from scipy import interpolate

import argparse
parser = argparse.ArgumentParser(description='Learn a collection of letters in parallel')
parser.add_argument('word', action="store",
                help='The word to be learnt')

numPoints_shapeModeler = 70

shapesLearnt = []
wordsLearnt = []
shapeLearners = []
currentWord = []
settings_shapeLearners = []
userInputCaptures = []

def downsampleShape(shape,numDesiredPoints,xyxyFormat=False):
    numPointsInShape = len(shape)/2
    if(xyxyFormat):
        #make xyxy format
        x_shape = shape[0::2]
        y_shape = shape[1::2]
    else:
        x_shape = shape[0:numPointsInShape]
        y_shape = shape[numPointsInShape:]

    if isinstance(x_shape,numpy.ndarray): #convert arrays to lists for interp1d
        x_shape = (x_shape.T).tolist()[0]
        y_shape = (y_shape.T).tolist()[0]

    #make shape have the same number of points as the shape_modeler
    t_current = numpy.linspace(0, 1, numPointsInShape)
    t_desired = numpy.linspace(0, 1, numDesiredPoints)
    f = interpolate.interp1d(t_current, x_shape, kind='cubic')
    x_shape = f(t_desired)
    f = interpolate.interp1d(t_current, y_shape, kind='cubic')
    y_shape = f(t_desired)

    shape = []
    shape[0:numPoints_shapeModeler] = x_shape
    shape[numPoints_shapeModeler:] = y_shape

    return shape


userShape = []
class MyPaintWidget(Widget):

    def on_touch_down(self, touch):
        with self.canvas:
            Color(1, 1, 0)
            d = 30.
            touch.ud['line'] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        global userShape
        touch.ud['line'].points += [touch.x, touch.y]
        userShape += [touch.x, -touch.y]

    def on_touch_up(self, touch):
        global userShape
        
        wordToLearn = wordManager.getCurrentCollection()
        if len(userShape) < 5:
            
            closeFigures(figuresToClose = range(1,len(wordToLearn)+1))
            wordToLearn = raw_input("Next word:\n")
            newWord(wordToLearn)
            userInputCapture.display_grid(numColumns = len(wordToLearn))

        else:
            userShape = downsampleShape(userShape,numPoints_shapeModeler,xyxyFormat=True)

            shapeCentre = ShapeModeler.getShapeCentre(userShape)
            for i in range(len(wordToLearn)):
                if(shapeCentre[0] > (self.width/len(wordToLearn))*i):
                    shapeIndex_demoFor = i

            shapeType = wordManager.shapeAtIndexInCurrentCollection(shapeIndex_demoFor)
            print('Received demo for letter ' + shapeType)

            userShape = numpy.reshape(userShape, (-1, 1)); #explicitly make it 2D array with only one column
            userShape = ShapeModeler.normaliseShapeHeight(numpy.array(userShape))

            shape = wordManager.respondToDemonstration(shapeType, userShape)

            userShape = []
            self.canvas.remove(touch.ud['line'])
            if shape != -1:
                showShape(shape, shapeIndex_demoFor)

class UserInputCapture(App):

    def build(self):
        self.painter = MyPaintWidget()
        return self.painter

    #def on_start(self):
    #    self.display_grid()

    def display_grid(self, numColumns): #paint vertical lines to separate inputs
        self.painter.canvas.clear()
        with self.painter.canvas:
            Color(1, 1, 0)
            d = 30.
            for i in range(numColumns-1):
                x = (self.painter.width/numColumns)*(i+1)
                Line(points=(x, 0, x, self.painter.height))



###---------------------------------------------- WORD LEARNING SETTINGS
def generateSettings(shapeType):
    #not used while feedback is demonstrations (instead of clicking)
    #but must be specified because of a fault in the design....
    paramsToVary = [1];      
    initialBounds_stdDevMultiples = numpy.array([[-6, 6]]);  
    doGroupwiseComparison = True; 
    initialParamValue = numpy.NaN
    initialBounds = numpy.array([[numpy.NaN, numpy.NaN]])

    import glob
    datasetFiles_shape = glob.glob(datasetDirectory + '/'+shapeType+'*.dat')
    
    if(len(datasetFiles_shape)<1):
        raise Exception("Dataset not available at " + datasetDirectory + " for shape " + shape)
    elif len(datasetFiles_shape)>1: #multiple potential datasets
        datasetFiles_largestCluster = glob.glob(datasetDirectory + '/'+shapeType+'0.dat')
        if len(datasetFiles_largestCluster) > 0:
        	datasetFile = datasetFiles_largestCluster[0] #use largest cluster's dataset
    	else: #largest cluster's dataset not available
    		datasetFile = datasetFiles_shape[0] #just choose one of them
    else: #only one dataset available
        datasetFile = datasetFiles_shape[0]

    settings = SettingsStruct(shape_learning = shapeType,
            paramsToVary = paramsToVary, doGroupwiseComparison = True, 
            datasetFile = datasetFile, initialBounds = initialBounds, 
            initialBounds_stdDevMultiples = initialBounds_stdDevMultiples,
            initialParamValue = initialParamValue, minParamDiff = 0.4)
    return settings

def showShape(shape, shapeIndex):
    plt.figure(shapeIndex+1, figsize=(3,3))
    plt.clf()
    ShapeModeler.normaliseAndShowShape(shape.path)
    plt.draw()

def closeFigures(figuresToClose):
    for i in figuresToClose:
        plt.close(i)

# callback for regular plot updating
def updatePlots(dt):
    plt.draw()
    plt.pause(0.05)

def newWord(wordToLearn):
    wordSeenBefore = wordManager.newCollection(wordToLearn)
    for i in range(len(wordToLearn)):
        shape = wordManager.startNextShapeLearner()
        showShape(shape, i)

if __name__ == "__main__":
    #parse arguments
    args = parser.parse_args()
    wordToLearn = args.word

    import inspect
    fileName = inspect.getsourcefile(ShapeModeler)
    installDirectory = fileName.split('/lib')[0]
    datasetDirectory = installDirectory + '/share/shape_learning/letter_model_datasets/uji_pen_chars2'

    plt.ion()

    wordManager = ShapeLearnerManager(generateSettings)
    newWord(wordToLearn)

    Clock.schedule_interval(updatePlots, 1/2.) #schedule regular update of plots

    #allow user to provide demonstrations in a kivy app with a canvas
    userInputCapture = UserInputCapture()
    userInputCapture.run()
    #draw lines to separate inputs for different letters
    userInputCapture.display_grid(numColumns = len(wordToLearn)) 
