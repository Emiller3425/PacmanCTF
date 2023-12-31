#baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html
from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint
import layout
import time


#################
# Team creation #
#################

#extend layout 

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DefensiveAgent', second = 'OffensiveAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
 
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    if self.index == 1:
      print(values, file=sys.stderr)
      # print(self.getPreviousObservation(), file=sys.stderr)

    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    # if self.index == 1:
    #   print(bestActions, file=sys.stderr)

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2 or gameState.getAgentState(self.index).numCarrying > 5:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)

    if self.index == 1:
      print(str(features) + str(weights), file=sys.stderr)
      # print(gameState.getAgentState(self.index)) # Print out a text representation of the world.

    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}
  
class OffensiveAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  #defined locations for when OffensiveAgent switches to DefensiveAgent
  x = 15
  y = 8
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    #if red team and score >= 3
    if self.red and self.getScore(successor) <=- 3 and isinstance(self, OffensiveAgent):
        self.__class__ = DefensiveReflexAgent
        return features
    #if blue team and score >= 3
    elif self.getScore(successor) >= 3 and isinstance(self, OffensiveAgent):
        self.__class__ = DefensiveReflexAgent
        return features
    # If score is under 3 and you are an offensive agent continue
    elif isinstance(self, OffensiveAgent):
      myState = successor.getAgentState(self.index)
      myPos = myState.getPosition()

      foodList = self.getFood(successor).asList()    
      features['successorScore'] = -len(foodList)#self.getScore(successor)

      # Compute distance to the nearest food
      if len(foodList) > 0: # This should always be True,  but better safe than sorry
        myPos = successor.getAgentState(self.index).getPosition()
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance
      

      # Determine if the enemy is closer to you than they were last time
      # and you are in their territory.
      # Note: This behavior isn't perfect, and can force Pacman to cower 
      # in a corner.  I leave it up to you to improve this behavior.
      #print(gameState.getAgentState(self.index).numCarrying, file=sys.stderr)
      close_dist = 9999.0
      if gameState.getAgentState(self.index).isPacman:
        #return to own side if has 3 food
        if gameState.getAgentState(self.index).numCarrying >= 3:
          features['distanceToFood'] = self.getMazeDistance(myPos, self.start)
        #Identify if a pacman is being chased by an enemy
        opp_fut_state = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        chasers = [p for p in opp_fut_state if p.getPosition() != None and not p.isPacman]
        
        if len(chasers) > 0:
          if gameState.getAgentState(self.index).numCarrying <= 3:
            team_indexes = self.getTeam(gameState)
            team = [gameState.getAgentState(i) for i in team_indexes]
            if self.index == team_indexes[0]:
              teammate = team[0]
            else:
              teammate = team[1]
            close_dist = min([float(self.getMazeDistance(myPos, teammate.getPosition()))])
            if close_dist != 0.0:
              features['fleeEnemy'] = 0/close_dist
          else:
            close_dist = min([float(self.getMazeDistance(myPos, c.getPosition())) for c in chasers])
            if close_dist != 0.0:
              features['fleeEnemy'] = 1.0/close_dist
    else:
      #if you are a defensive agent, switch to offensive agent if score is less than 3 
      return DefensiveAgent.getFeatures(self, gameState, action)

    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1, 'fleeEnemy': -100.0}
  

class DefensiveAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """
  x = 15
  y = 8
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    #if there is an invader in sight calculate distance to that
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    #calculate location for agent to sit at middle of border and wait for invaders
    else:
      error_occurred = True  # Set the flag to True to indicate that an error occurred
      while error_occurred:
        try:
            while self.getMazeDistance(myPos, (self.x, self.y)) is not int:
              error_occurred = False  # Set the flag to False when no error occurs
              break
        except Exception as e:
            if self.red:
              self.x -= 1
              self.y -= 0.50
            else:
              self.x += 1
              self.y += 0.50
              # Handle the error, e.g., print an error message or take appropriate action.
              print(f"An error occurred: {e}")
      #calculate distance to middle of border
      dists = self.getMazeDistance(myPos, (self.x, self.y))
      features['invaderDistance'] = dists

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}
          
class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}
