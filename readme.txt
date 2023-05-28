This program takes in certain information for a snowball game and gives back a certain move using reinforcement learning.

The Q-table is updated based on the following Q-learning reward formula:
----------------------------
Q[player_to_index(prevState[0:3])][player_to_index(prevState[3:])][trainingMoveIndex] += learningRate * (reward + discountFactor * max(Q[player_to_index(currentTrainingState[0:3])][player_to_index(currentTrainingState[3:])]) - Q[player_to_index(prevState[0:3])][player_to_index(prevState[3:])][trainingMoveIndex])
----------------------------