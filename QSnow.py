# -*- coding: utf-8 -*-
"""
Created on Wed May 24 18:11:30 2023

@author: kevinhuang
"""
from random import choice, random
#from tkinter import *
from time import sleep


# myInterface = Tk()
# s = Canvas(myInterface, height = 264, width = 264, background = "white")
# s.pack()

# img = PhotoImage(width=264, height=264)
# image = s.create_image((132, 132), image=img, state="normal")

from royData import Qtable
Q = Qtable

# data = __import__("georgeData")
# Q = data.Q()

# Changing global variables
oppSnowballHistory = []
oppMoveHistory = []
myMoveHistory = []
myMovesThisGame = []
trainingMovesSoFar = []
currentState = []
pastNoSnowballMoves = [0, 0, 0]
sequencesSeen = {}
recurringPatterns = {}
latestSequences = []
oppNetAdv = 0
obamaNetAdv = 0
a = 0

# Unchanging global variables
moves = ["THROW", "DUCK", "RELOAD"]
counters = {"THROW":"DUCK", "DUCK":"RELOAD", "RELOAD":"THROW"}
#Q = Qtable

# Net advantage increases for each matchup
# netAdvIncreases[my move][opp move] gives the increase in net advantage
netAdvIncreases = [[0, 0, 0], [1, 1, -1], [0, 2, 0]]

# Q-learning constants
# The higher the learning rate, the faster it changes the reward values (check formula)
learningRate = 0.81
# The higher the discount factor, the more important looking towards the future becomes (in the formula, the maximum reward for the next game state is added with the reward as well)
discountFactor = 0.96
# The higher the epsilon, the more randomly the bot chooses moves, the more scenarios it trains (high epsilon is good in the beginning, but after some training, it should decrease so that the bot will focus more on the better moves)
epsilon = 0.9


# The Q-table (the reward data array) will be a 2D 264x264 array with each element being an array of length 3 containing the reward values for each move given a certain game state
# 264 x 264 is enough to represent every single possible game state (total number of possible combinations = 4 x 11 x 6 x 4 x 11 x 6 = 264 x 264)
# Let's define a new hypothetical number system where the ones digit goes from 0 to 5, the 'tens' digit goes from 0 to 10, and the 'hundreds' digit goes from 0 to 3 (tens, and hundreds put in quotations because they are technically not tens and hundreds since it's not base 10)
# Let's call this hypothetical number system base n
# Increasing the ones digit would increase the number's value in base 10 by 1
# Increasing the 'tens' digit would increase the number's value in base 10 by 6 base n ones digits which is just 6
# Increasing the 'hundreds' digit would increase the number by 11 base n 'tens' digits which is 11 x 6 = 66 base n ones digits which is just 66

def player_to_index(player_info):
  # Finds the index in the 2D Q-table from the player's information (score, snowballs, ducksUsed) (outer index is found using our into, inner index is found using opp's info)
  # Basically just converting the number gotten from combining the player information 'digits' (score, snowballs, ducksUsed) from our hypothetical number system into base 10
  # Examples:
  # [0, 0, 0] --> 0*11*6 + 0*6 + 0 = index 0
  # [0, 0, 2] --> 0*11*6 + 0*6 + 2 = index 2
  # [0, 1, 0] --> 0*11*6 + 1*6 + 0 = index 6
  # [1, 0, 0] --> 1*11*6 + 0*6 + 0 = index 66
  # [2, 6, 4] --> 2*11*6 + 6*6 + 4 = index 172
  # Our info: [0, 1, 0] --> 0*11*6 + 1*6 + 0 = index 6; Opp info: [0, 1, 1] --> 0*11*6 + 1*6 + 1 = index 7; actual position of the length 3 reward array is at Q[6][7]
 
  return (player_info[SCORE_1_POSITION] * (SNOW_BALLS_RANGE * DUCKS_USED_RANGE) +
  player_info[SNOW_BALLS_1_POSITION] * (DUCKS_USED_RANGE) +
  player_info[DUCKS_USED_1_POSITION])

# Finds the previous game state given the current state, and each player's moves
def revertState(state, myMovesSoFar, oppMovesSoFar):
  #Get the most recent moves of each player
  myLastMove = myMovesSoFar[-1]
  oppLastMove = oppMovesSoFar[-1]

  # temp game state array separate from the input array
  # Simply using the input array to find the previous state would mess up the actual array used as input
  tempState = []
  for value in state:
    tempState.append(value)

  # If I threw, then I would have had one more snowball last turn
  if myLastMove == "THROW":
    tempState[SNOW_BALLS_1_POSITION] += 1
    # If I threw and my opponent reloaded (gained a point), my score would have been one lower a turn ago
    if oppLastMove == "RELOAD":
      tempState[SCORE_1_POSITION] -= 1

  # If I ducked, my ducks used would have been one lower last turn
  elif myLastMove == "DUCK":
    tempState[DUCKS_USED_1_POSITION] -= 1

  # If I reloaded, I would have had one less snowball a turn ago
  elif myLastMove == "RELOAD":
    tempState[SNOW_BALLS_1_POSITION] -= 1
    # If I reloaded and my opponent threw (opponent gained a point), my opponent's score would have been one lower last turn
    if oppLastMove == "THROW":
      tempState[SCORE_2_POSITION] -= 1

  # Same as above
  if oppLastMove == "THROW":
    tempState[SNOW_BALLS_2_POSITION] += 1

  elif oppLastMove == "DUCK":
    tempState[DUCKS_USED_2_POSITION] -= 1

  elif oppLastMove == "RELOAD":
    tempState[SNOW_BALLS_2_POSITION] -= 1

  return tempState

# Finds the new game state given the most recent moves and the old state
# Used after revertState()
def updateState(state, trainingMovesSoFar, oppMovesSoFar):
  lastTrainingMove = trainingMovesSoFar[-1]
  oppLastMove = oppMovesSoFar[-1]
 
  tempState = []
  for value in state:
    tempState.append(value)

  # Just reverse of revertState() function
  if lastTrainingMove == "THROW":
    tempState[SNOW_BALLS_1_POSITION] -= 1
    if oppLastMove == "RELOAD":
      tempState[SCORE_1_POSITION] += 1

  elif lastTrainingMove == "DUCK":
    tempState[DUCKS_USED_1_POSITION] += 1

  elif lastTrainingMove == "RELOAD":
    tempState[SNOW_BALLS_1_POSITION] += 1
    if oppLastMove == "THROW":
      tempState[SCORE_2_POSITION] += 1

 
  if oppLastMove == "THROW":
    tempState[SNOW_BALLS_2_POSITION] -= 1

  elif oppLastMove == "DUCK":
    tempState[DUCKS_USED_2_POSITION] += 1

  elif oppLastMove == "RELOAD":
    tempState[SNOW_BALLS_2_POSITION] += 1

  return tempState

# Returns a hex code given an RGB value
def rgb_to_hex(r, g, b):
  return '#{:02x}{:02x}{:02x}'.format(r, g, b)
  
# Maps an array of three values to RGB (range of 0-255) based on the maximum and minimum values
def getRGB(values):
  minimum = min(values)
  maximum = max(values)

  #Avoid dividing by 0
  if minimum == maximum:
    return [0, 0, 0]

  RGB = []

  for value in values:
    # For the middle value, if the maximum is mapped to 255 and the minimum is mapped to 0,
    # Let x represent the RGB value that the middle value is mapped to
    # (mid - min) / (max - min) = (x - 0) / (255 - 0)
    #                           = x/255
    # Multiply both sides by 255
    # x = (mid - min) / (max - min) * 255

    # For the maximum value, (max - min) / (max - min) * 255 = 255
    # For the minimum value, (min - min) / (max - min) * 255 = 0
    RGB.append(int(round((value - minimum) / (maximum - minimum) * 255)))

  return RGB



# Colours in each pixel using .put() instead of drawing a line each individual pixel (using.put() is much faster)
# def draw2():
#   for row in range(264):
#     for column in range(264):
#       # Save the array at the current index into a variable
#       values = Q[row][column]

#       # Get the RGB values and use those to get the hex code
#       RGB = getRGB(values)
#       hex = rgb_to_hex(RGB[0], RGB[1], RGB[2])
#       img.put(hex, (row, column))

#   s.update()


# # Goes through each index in each row of the Q-table and colours a pixel corresponding to the index of the action reward array
# # The colour depends on the reward values in the array (RGB)
# # Slower than draw2 but slowness can also be useful for visualisation
# def draw():
#   # Iterate through Q-table
#   for row in range(264):
#     for column in range(264):
#       # Save the array at the current index into a variable
#       values = Q[row][column]

#       # Get the RGB values and use those to get the hex code
#       RGB = getRGB(values)
#       hex = rgb_to_hex(RGB[0], RGB[1], RGB[2])
      
#       s.create_rectangle(row, column, row, column, fill=hex, outline = "")
#       s.update()


# Train the Q-table based on the current game state and both players' moves
def train(myScore, mySnowballs, myDucksUsed, trainingMovesSoFar, oppScore, oppSnowballs, oppDucksUsed, oppMovesSoFar, reward, myMovesSoFar):
  global Q
  global currentState
 
  rewards = [
    [0, -1, 1],
    [1, 0, -2],
    [-1, 2, 0],
    ]

  trainingMoveIndex = moves.index(trainingMovesSoFar[-1])
  oppMoveIndex = moves.index(oppMovesSoFar[-1])

  #If the reward has not been determined yet
  if reward == None:
 
    reward = rewards[trainingMoveIndex][oppMoveIndex]

  # Set the current state
  currentState = [myScore, mySnowballs, myDucksUsed, oppScore, oppSnowballs, oppDucksUsed]

  # Determine the state for the previous turn
  prevState = revertState(currentState, myMovesSoFar, oppMovesSoFar)
  # Determine the hypothetical training state (the state that would appear if the training action was actually done)
  # This would be the same as the current state if the training action and actual action were the same
  currentTrainingState = updateState(prevState, trainingMovesSoFar, oppMovesSoFar)
 
  #Q-learning training formula (source: google)
  Q[player_to_index(prevState[0:3])][player_to_index(prevState[3:])][trainingMoveIndex] += learningRate * (reward + discountFactor * max(Q[player_to_index(currentTrainingState[0:3])][player_to_index(currentTrainingState[3:])]) - Q[player_to_index(prevState[0:3])][player_to_index(prevState[3:])][trainingMoveIndex])

  
 

 
# Good way to check if a game has ended
# As soon as the first game starts, firstGame is set to false
# That way, if the length of myMovesSoFar is 0 and firstGame is False, the program would know that a game has just ended
firstGame = True

def getMove(myScore, mySnowballs, myDucksUsed, myMovesSoFar, oppScore, oppSnowballs, oppDucksUsed, oppMovesSoFar):
  #print(a)
  global oppSnowballHistory
  global oppMoveHistory
  global oppNetAdv
  global obamaNetAdv
  global epsilon
  global firstGame
  global trainingMovesSoFar
  global currentState

  if len(oppMovesSoFar) > 0:
    firstGame = False

    # Take in and store information each turn
    oppSnowballHistory[-1].append(oppSnowballs)
    oppMoveHistory[-1].append(oppMovesSoFar[-1])
    myMoveHistory[-1].append(myMovesSoFar[-1])
    
    obamaNetAdv += netAdvIncreases[moves.index(myMovesSoFar[-1])][moves.index(oppMovesSoFar[-1])]
    oppNetAdv += netAdvIncreases[moves.index(oppMovesSoFar[-1])][moves.index(myMovesSoFar[-1])]

    # Train the bot using the most recent opponent action, most recent training action chosen, and the current game state
    train(myScore, mySnowballs, myDucksUsed, trainingMovesSoFar, oppScore, oppSnowballs, oppDucksUsed, oppMovesSoFar, None, myMovesSoFar)

    if myMovesSoFar[-1] != trainingMovesSoFar[-1]:
      # Train the bot using the most recent actions and the current game state
      # Only do this if the actual action is different from the training action to prevent extra changes in reward
      train(myScore, mySnowballs, myDucksUsed, myMovesSoFar, oppScore, oppSnowballs, oppDucksUsed, oppMovesSoFar, None, myMovesSoFar)

  # Do this if it's the first move of a game
  else:
    jumpFactor = 100
    # if len(oppMoveHistory) % jumpFactor == 0:
    #   draw2()

    # if len(oppMoveHistory) == 1000:
    #   draw2()
    
    # Do this if a game has just ended
    if len(myMovesSoFar) == 0 and not firstGame:
      
      # If the 30 move threshold was passed, the result might have been a win, loss, or draw (certain situations here are impossible to decipher completely and some assumptions must be made, but luckily, 30+ move games don't happen very often)
      if len(myMovesThisGame) == 30:
        # Our score was higher than opponent's
        if currentState[SCORE_1_POSITION] > currentState[SCORE_2_POSITION]:
          # Big reward for win
          reward = 100
          trainingReward = 100
          
        # Opponent's score was higher than our's
        elif currentState[SCORE_1_POSITION] < currentState[SCORE_2_POSITION]:
          # Big penalty for loss
          reward = -100
          trainingReward = -100

        # Scores were the same
        else:
          # No reward or penalty for draw
          reward = 0
          trainingReward = 0


      # If the game ended in less than 30 moves, the result was either a win or a loss and the ending state can be easily determined using the game state from the turn before the final turn (currentState is still what it was set to the last time our train function was called which is exactly one turn before the end), as well as our bot's final move from the last game
      else:
        if myMovesThisGame[-1] == "THROW" and currentState[SCORE_1_POSITION] == 2:
          reward = 100
          # No trainingReward is set because there is no guarantee that the game would have ended had our bot used the training action instead of what it actually used
          oppMoveHistory[-1].append("RELOAD")
         
        elif myMovesThisGame[-1] == "RELOAD" and currentState[SCORE_2_POSITION] == 2:
          reward = -100
          oppMoveHistory[-1].append("THROW")

        else:
          # In all other cases, the opponent would have lost via cheating which should not give as much reward but should still give some (exploiting the weakness, but not completely relying on it in case it was a fluke)
          reward = 25

        
      # When all is done, reset the current state to match the current game
      currentState = updateState(currentState, myMovesThisGame, oppMoveHistory[-1])

      # Train the bot using the already-determined reward values
      
      train(currentState[SCORE_1_POSITION], currentState[SNOW_BALLS_1_POSITION], currentState[DUCKS_USED_1_POSITION], myMovesThisGame, currentState[SCORE_2_POSITION], currentState[SNOW_BALLS_2_POSITION], currentState[DUCKS_USED_2_POSITION], oppMoveHistory[-1], reward, myMovesThisGame)

      if myMovesThisGame[-1] != trainingMovesSoFar[-1]:
        
        if len(myMovesThisGame) == 30:
          train(currentState[SCORE_1_POSITION], currentState[SNOW_BALLS_1_POSITION], currentState[DUCKS_USED_1_POSITION], trainingMovesSoFar, currentState[SCORE_2_POSITION], currentState[SNOW_BALLS_2_POSITION], currentState[DUCKS_USED_2_POSITION], oppMoveHistory[-1], trainingReward, myMovesThisGame)

        else:
          # If the game did not end because of the amount of turns, we wouldn't know what the reward value for the chosen training action would be so we train it without a predetermined reward value (the procedure figures out the reward itself using its reward value 'look-up table' array)
          train(currentState[SCORE_1_POSITION], currentState[SNOW_BALLS_1_POSITION], currentState[DUCKS_USED_1_POSITION], trainingMovesSoFar, currentState[SCORE_2_POSITION], currentState[SNOW_BALLS_2_POSITION], currentState[DUCKS_USED_2_POSITION], oppMoveHistory[-1], None, myMovesThisGame)

       
         
      # Decrease chance of random training action being chosen over current best action
      epsilon -= 0.001
     
    # Reset variables
    trainingMovesSoFar = []
    currentState = [0, 1, 0, 0, 1, 0]
    oppSnowballHistory.append([])
    oppMoveHistory.append([])
    myMoveHistory.append([])
    oppNetAdv = 0
    obamaNetAdv = 0
    
  updateTrends(latestSequences)

  # Get the training move (this move is for training purposes only, it is (most likely) not actually the move that gets chosen)
  if random() < epsilon:
    trainingMovesSoFar.append(anticheat(choice(moves), mySnowballs, 5 - myDucksUsed))

  else:
    # If it is decided that no randomness will be used for the turn, the action with the current highest reward value is chosen
    trainingMovesSoFar.append(moves[Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])].index(max(Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])]))])

  # This overwrites any other move that may have been played as it is a guaranteed win strategy provided we have a big enough lead
  if obamaNetAdv >= 6:
    if oppScore < 2:
      return anticheat("RELOAD", mySnowballs, 5 - myDucksUsed)
    else:
      return anticheat("THROW", mySnowballs, 5 - myDucksUsed)


  #Record what move opponent uses each time they run out of snowballs
  if len(oppSnowballHistory[-1]) > 1:
    if oppSnowballHistory[-1][-2] == 0:
      pastNoSnowballMoves[moves.index(oppMovesSoFar[-1])] += 1

  #print(pastNoSnowballMoves)

 
  #  Checks past moves when snowballs were 0
  if oppSnowballs == 0:
    if pastNoSnowballMoves[1] > pastNoSnowballMoves[2]:
      #print(["RELOAD"])
      return anticheat("RELOAD", mySnowballs, 5 - myDucksUsed)
    elif pastNoSnowballMoves[2] > pastNoSnowballMoves[1]:
      #print(["THROW"])
      return anticheat("THROW", mySnowballs, 5 - myDucksUsed)
    else:
      return anticheat("RELOAD", mySnowballs, 5 - myDucksUsed)

  else:
    patternLength = checkForPatterns(oppMovesSoFar)
    if patternLength == 0:
      return defaultStrat(myScore, mySnowballs, myDucksUsed, oppScore, oppSnowballs, oppDucksUsed)
    else:
      return counterPatterns(patternLength, oppMovesSoFar, mySnowballs, 5 - myDucksUsed, 3 - oppScore, myScore, oppSnowballs, oppDucksUsed)

SCORE_1_POSITION = 0
SNOW_BALLS_1_POSITION = 1
DUCKS_USED_1_POSITION = 2
SCORE_2_POSITION = 3
SNOW_BALLS_2_POSITION = 4
DUCKS_USED_2_POSITION = 5

SCORES_RANGE = 4
SNOW_BALLS_RANGE = 11
DUCKS_USED_RANGE = 6

 
randomness = 0.05
def defaultStrat(myScore, mySnowballs, myDucksUsed, oppScore, oppSnowballs, oppDucksUsed):
  choices = []

  if oppScore == 0 and len(oppMoveHistory) < 5:
    return anticheat("RELOAD", mySnowballs, 5 - myDucksUsed)
   
  if oppScore == 2 and len(oppMoveHistory) < 10:
    return anticheat("THROW", mySnowballs, 5 - myDucksUsed)
 
  if random() < randomness:

    for throw in range(1 + int(max(0, Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])][0]))):
      choices.append("THROW")
 
    for duck in range(1 + int(max(0, Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])][1]))):
      choices.append("DUCK")
 
    for reload in range(1 + int(max(0, Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])][2]))):
      choices.append("RELOAD")

  if choices == []:
    return anticheat(moves[Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])].index(max(Q[player_to_index([myScore, mySnowballs, myDucksUsed])][player_to_index([oppScore, oppSnowballs, oppDucksUsed])]))], mySnowballs, 5 - myDucksUsed)

  else:
    return anticheat(choice(choices), mySnowballs, 5 - myDucksUsed)
  # if lives == 3:
  #   return anticheat("RELOAD", snowballs, ducks)
     
  # elif lives == 1:
  #   return anticheat("THROW", snowballs, ducks)

  # else:
  #   return anticheat(choice(["RELOAD", "THROW"]), snowballs, ducks)
     
 

def checkForPatterns(oppMovesSoFar):
  global sequencesSeen
  global recurringPatterns
  global latestSequences
  
  #Length of longest recurring pattern so far
  longestRecurringLength = 0

  latestSequences = []

  #Loop through every length until maxLength is reached
  maxLength = 5
  for length in range(1, min(len(oppMovesSoFar) + 1, maxLength + 1)):
    #Take last however many length is moves in oppMovesSoFar and store it into a checking variable
    checking = '-'.join(oppMovesSoFar[len(oppMovesSoFar) - length : len(oppMovesSoFar)])
    latestSequences.append(checking)
    
    try:
      sequencesSeen[checking][-1] += 1

    except KeyError:
      sequencesSeen[checking] = [[0, 0, 0] for _ in range(31)]
      sequencesSeen[checking].append(1)

    #Times it has appeared in the past
    timesSeen = sequencesSeen[checking][-1]
 
    if timesSeen >= int(2**(-length) + 2.5) + len(oppMovesSoFar)//3.235:
      #Find recurring pattern of greatest length and use that
      longestRecurringLength = max(longestRecurringLength, length)

      try:
        recurringPatterns[checking][-1] += 0

      except KeyError:
        recurringPatterns[checking] = sequencesSeen[checking]

  return longestRecurringLength

def updateTrends(latestSequences):
  global sequencesSeen
  
  for sequence in latestSequences:
    if len(oppMoveHistory[-1]) != 0:
      sequencesSeen[sequence][len(oppMoveHistory[-1])-1][moves.index(oppMoveHistory[-1][-1])] += 1
def counterPatterns(length, oppMovesSoFar, snowballs, ducks, lives, myScore, oppSnowballs, oppDucksUsed):
  global a
  pastFollowUpMoves = [0, 0, 0]
  checking = '-'.join(oppMovesSoFar[len(oppMovesSoFar) - length : len(oppMovesSoFar)])

  for i in range(len(recurringPatterns[checking]) - 1):
    x = abs(len(oppMovesSoFar) - i)
    #importance = 1 / (0.2*(x/10)**2 + 1)
    importance = 1 / (0.2*((x/10)**2 + 1))

    for moveIndex in range(3):
                      
      pastFollowUpMoves[moveIndex] += importance * recurringPatterns[checking][i][moveIndex]

  # for i in range(len(oppMovesSoFar) - length):
  #   if oppMovesSoFar[i:i+length] == checking:
  #     x = abs(len(oppMovesSoFar) - (i + length))
  #     importance = 1# / (0.2*((x/10)**2 + 1))
  #     pastFollowUpMoves[moves.index(oppMovesSoFar[i+length])] += importance
      # if counters[moves[pastFollowUpMoves.index(max(pastFollowUpMoves))]] != counters[moves[pp.index(max(pp))]]:
      #print(pastFollowUpMoves, pp)
      #print('a', [counters[moves[pastFollowUpMoves.index(max(pastFollowUpMoves))]], counters[moves[pp.index(max(pp))]]])

  if length > 1:
    a += 1

  # print(checking)
  #print(pastFollowUpMoves)
  # print([counters[moves[pastFollowUpMoves.index(max(pastFollowUpMoves))]]])
 
  # As more and more games go by, reliance on guessing recurring patterns decreases as the bot learns the opponent's strategy (only recurring patterns with extremely biased follow up values are even considered)
  if middle(pastFollowUpMoves) / max(pastFollowUpMoves) > (0.952 - len(oppMoveHistory) * 0.01):
    return defaultStrat(myScore, snowballs, 5 - ducks, 3 - lives, oppSnowballs, oppDucksUsed)
  else:
    #print(pastFollowUpMoves)
    print([])
    return anticheat(counters[moves[pastFollowUpMoves.index(max(pastFollowUpMoves))]], snowballs, ducks)

def middle(values):
  temp = []
  for value in values:
    temp.append(value)
  temp.pop(values.index(max(values)))
  return max(temp)
 
def anticheat(move, snowballs, ducks):
  if move == "THROW":
    if snowballs == 0:
      myMovesThisGame.append("RELOAD")
      return "RELOAD"
    else:
      myMovesThisGame.append("THROW")
      return "THROW"

  elif move == "DUCK":
    if ducks == 0:
      if snowballs == 0:
        myMovesThisGame.append("RELOAD")
        return "RELOAD"
      else:
        myMovesThisGame.append("THROW")
        return "THROW"
    else:
      myMovesThisGame.append("DUCK")
      return "DUCK"

  else:
    if snowballs == 10:
      myMovesThisGame.append("THROW")
      return "THROW"
    else:
      myMovesThisGame.append("RELOAD")
      return "RELOAD"