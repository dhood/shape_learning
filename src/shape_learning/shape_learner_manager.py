#!/usr/bin/env python

"""
Manages a collection of shape_learners, with long-term memory about the 
history of previous collections seen. An example is managing shape_learners
which represent letters, and the collections represent words. 
"""

from shape_modeler import ShapeModeler
from shape_learner import ShapeLearner

import numpy          
from recordtype import recordtype #for mutable namedtuple (dict might also work)
         
boundExpandingAmount = 0.;
usePrevParamsWhenShapeReappears = True;

Shape = recordtype('Shape',[('path', None), ('shapeID', None), ('shapeType', None), ('shapeType_code', None), ('paramsToVary', None), ('paramValues', None)]);

###--------------------------------------------- WORD LEARNING FUNCTIONS
class ShapeLearnerManager:
    def __init__(self, generateSettingsFunction):
        self.generateSettings = generateSettingsFunction;
        self.shapesLearnt = [];
        self.shapeLearners = {};
        self.settings_shapeLearners = {};
        self.shapeLearnersSeenBefore_currentCollection = [];
        self.currentCollection = [];
        self.collectionsLearnt = [];
        self.nextShapeLearnerToBeStarted = 0;
        
        
    def initialiseShapeLearners(self):
        self.shapeLearnersSeenBefore_currentCollection = [];
        for i in range(len(self.currentCollection)):
            shapeType = self.currentCollection[i];
            
            #check if shape has been learnt before
            try:
                shapeType_index = self.shapesLearnt.index(shapeType);
                newShape = False;
            except ValueError: 
                newShape = True;
            self.shapeLearnersSeenBefore_currentCollection.append(not newShape);
            if(newShape):
                settings = self.generateSettings(shapeType); 

                shapeLearner = ShapeLearner(settings);
                self.shapesLearnt.append(shapeType);
                self.shapeLearners[shapeType] = shapeLearner
                self.settings_shapeLearners[shapeType] = settings
                
            else:
                #use the bounds determined last time
                previousBounds = self.shapeLearners[shapeType].getParameterBounds();
                newInitialBounds = previousBounds;
                newInitialBounds[0,0] -= boundExpandingAmount;#USE ONLY FIRST PARAM FOR SELF-LEARNING ALGORITHM ATM
                newInitialBounds[0,1] += boundExpandingAmount;#USE ONLY FIRST PARAM FOR SELF-LEARNING ALGORITHM ATM
                self.shapeLearners[shapeType].setParameterBounds(newInitialBounds);        
                     
    def startNextShapeLearner(self):
        #start learning
        if( self.nextShapeLearnerToBeStarted < len(self.currentCollection) ):
            shapeType = self.currentCollection[self.nextShapeLearnerToBeStarted];
            shapeType_code = self.nextShapeLearnerToBeStarted;
            if(usePrevParamsWhenShapeReappears and 
            self.shapeLearnersSeenBefore_currentCollection[self.nextShapeLearnerToBeStarted]): #shape has been seen before
                [path, paramValues] = self.shapeLearners[shapeType].getLearnedShape();
            else:
                [path, paramValues] = self.shapeLearners[shapeType].startLearning();
            paramsToVary = self.settings_shapeLearners[shapeType].paramsToVary;
            self.nextShapeLearnerToBeStarted += 1;
            shape = Shape(path=path, shapeID=0, shapeType=shapeType, 
                shapeType_code=shapeType_code, paramsToVary=paramsToVary, paramValues=paramValues);
            return shape;
        else:
            print('Don\'t know what shape learner you want me to start...');
            return -1;

    def feedbackManager(self, shape_messageFor, bestShape_index, noNewShape):
        if(shape_messageFor < 0 ):
            print('Ignoring message because not for valid shape type');
            return -1;
        else:
        
            if(noNewShape): #just respond to feedback, don't make new shape 
                self.shapeLearners[shape_messageFor].respondToFeedback(bestShape_index);
                return 1;
            else:               
                [numItersConverged, newPath, newParamValues] = self.shapeLearners[shape_messageFor].generateNewShapeGivenFeedback(bestShape_index);
            paramsToVary = self.settings_shapeLearners[shape_messageFor].paramsToVary;
            shapeType_code = self.indexOfShapeInCurrentCollection(shape_messageFor)
            shape = Shape(path=newPath, shapeID=[], shapeType=shape_messageFor, 
                shapeType_code=shapeType_code, paramsToVary=paramsToVary, paramValues=newParamValues);
            return numItersConverged, shape;
    
    def respondToDemonstration(self, shape_messageFor, shape):
        if(shape_messageFor < 0 ):
            print('Ignoring demonstration because not for valid shape type');
            return -1;
        else:
            [newPath, newParamValues] = self.shapeLearners[shape_messageFor].respondToDemonstration(shape);
            paramsToVary = self.settings_shapeLearners[shape_messageFor].paramsToVary;
            shapeType_code = self.indexOfShapeInCurrentCollection(shape_messageFor)
            shape = Shape(path=newPath, shapeID=[], shapeType=shape_messageFor, 
                shapeType_code=shapeType_code, paramsToVary=paramsToVary, paramValues=newParamValues);
            return shape
    
    def indexOfShapeInCurrentCollection(self, shapeType):
        try:
            shapeType_index = self.currentCollection.index(shapeType);
        except ValueError: #unknown shape
            shapeType_index = -1;
        return shapeType_index;
            
    def shapeAtIndexInCurrentCollection(self, shapeType_index):
        try:
            shapeType = self.currentCollection[shapeType_index];
        except IndexError: #unknown shape
            shapeType = -1;
        return shapeType;
            
    def newCollection(self, collection):
        self.currentCollection = collection;
        self.nextShapeLearnerToBeStarted = 0;
        
        try:
            collection_index = self.collectionsLearnt.index(self.currentCollection);
            collectionSeenBefore = True;
        except ValueError: 
            collectionSeenBefore = False;
            self.collectionsLearnt.append(self.currentCollection);

        self.initialiseShapeLearners(); 
        
        return collectionSeenBefore;

    def getCurrentCollection(self):
        return self.currentCollection

    def getAllCollections(self):
        return collectionsLearnt

    def resetParameterBounds(self, shapeType):
        currentBounds = self.shapeLearners[shapeType].getParameterBounds();
               
        #change bounds back to the initial ones 
        newBounds = self.shapeLearners[shapeType].initialBounds;
        self.shapeLearners[shapeType].setParameterBounds(newBounds);
        print('Changing bounds on shape '+shapeType+' from '+str(currentBounds)+' to '+str(newBounds));
    
    def generateSimulatedFeedback(self, shapeType_index, newShape, newParamValue):
        return self.shapeLearners[shapeType].generateSimulatedFeedback(newShape, newParamValue);
