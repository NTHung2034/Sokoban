import psutil
import time
import Modules.File as File
import copy
import Modules.MazeHelper as MazeHelper

class MazeState:
    def __init__(self, mazeMatrix : dict, rockWeights : list) -> None:
        self.rockData = MazeHelper.getRockData(mazeMatrix, rockWeights)
        self.playerPosition = MazeHelper.getPlayerPosition(mazeMatrix)
        self.switchData = MazeHelper.getSwitchData(mazeMatrix)
        self.wallData = MazeHelper.getWallData(mazeMatrix)

class Maze:
    def __init__(self, mazeState : MazeState) -> None:
        self.mazeState = mazeState

    def __eq__(self, other):
        return self.mazeState.rockData == other.mazeState.rockData and self.mazeState.playerPosition == other.mazeState.playerPosition
    
    def __hash__(self) -> int:
        return hash((tuple(self.mazeState.rockData), self.mazeState.playerPosition))
    
    def copy(self):
        return copy.deepcopy(self)
    
    def __availablePosition(self, location):
        return location in availablePosition
    
    def __isEmpty(self, position):
        if not self.__availablePosition(position):
            return False
        return position not in self.mazeState.rockData and position not in self.mazeState.wallData
    
    def __isRock(self, location):
        # find in the rockData
        return location in self.mazeState.rockData
    
    def __doesCreateDeadlock(self, rockPosition, pushDirection):
        newPosition = (rockPosition[0] + pushDirection[0], rockPosition[1] + pushDirection[1])
        
        if newPosition in self.mazeState.switchData:
            return False
        
        return MazeHelper.isOnDeadlockScenario(self.mazeState.wallData,self.mazeState.rockData,newPosition, rockPosition)
    
    def __isPushableRock(self, location, pushDirection):
        if not self.__availablePosition(location):
            return False
        if self.__isRock(location) and self.__isEmpty((location[0] + pushDirection[0], location[1] + pushDirection[1])) and not self.__doesCreateDeadlock(location, pushDirection):
            return True
        return False
    
    def __updateMazeOnPlayerMove(self, moveDirection) -> int: # return the move cost
        hasRockPushed = False
        if moveDirection == 'U':
            nextMovePosition = (self.mazeState.playerPosition[0] - 1, self.mazeState.playerPosition[1])
            if self.__isPushableRock(nextMovePosition, (-1, 0)):
                # update the rock position in the rock data
                nextRockPostion = (self.mazeState.playerPosition[0] - 2, self.mazeState.playerPosition[1])
                hasRockPushed = True
            
        elif moveDirection == 'D':
            nextMovePosition = (self.mazeState.playerPosition[0] + 1, self.mazeState.playerPosition[1])
            if self.__isPushableRock(nextMovePosition, (1, 0)):
                # update the rock position in the rock data
                nextRockPostion = (self.mazeState.playerPosition[0] + 2, self.mazeState.playerPosition[1])
                hasRockPushed = True

        elif moveDirection == 'L':
            nextMovePosition = (self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] - 1)
            if self.__isPushableRock(nextMovePosition, (0, -1)):
                # update the rock position in the rock data
                nextRockPostion = (self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] - 2)
                hasRockPushed = True

        elif moveDirection == 'R':
            nextMovePosition = (self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] + 1)
            if self.__isPushableRock(nextMovePosition, (0, 1)):
                # update the rock position in the rock data
                nextRockPostion = (self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] + 2)
                hasRockPushed = True
        
        self.mazeState.playerPosition = nextMovePosition
        if hasRockPushed:
            self.mazeState.rockData[nextRockPostion] = self.mazeState.rockData.pop(nextMovePosition)
            return self.mazeState.rockData[nextRockPostion]
        return 1

    def isAvailableMove(self, moveDirection) -> tuple: # return a tuple of (a,b) which a is a boolean indicating if the move is available and b is the action to be taken (push or move)
        if moveDirection == 'U':
            if self.__isEmpty((self.mazeState.playerPosition[0] - 1, self.mazeState.playerPosition[1])):
                return (True, 'u')
            elif self.__isPushableRock((self.mazeState.playerPosition[0] - 1, self.mazeState.playerPosition[1]), (-1, 0)):
                return (True, 'U')
            
        elif moveDirection == 'D':
            if self.__isEmpty((self.mazeState.playerPosition[0] + 1, self.mazeState.playerPosition[1])):
                return (True, 'd')
            elif self.__isPushableRock((self.mazeState.playerPosition[0] + 1, self.mazeState.playerPosition[1]), (1, 0)):
                return (True, 'D')
            
        elif moveDirection == 'L':
            if self.__isEmpty((self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] - 1)):
                return (True, 'l')
            elif self.__isPushableRock((self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] - 1), (0, -1)):
                return (True, 'L')
            
        elif moveDirection == 'R':
            if self.__isEmpty((self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] + 1)):
                return (True, 'r')
            elif self.__isPushableRock((self.mazeState.playerPosition[0], self.mazeState.playerPosition[1] + 1), (0, 1)):
                return (True, 'R')
        return (False, None)

    def getPlayerMoves(self) -> list:
        availableMoves = []
        canMoveUp, moveUpAction = self.isAvailableMove('U')
        canMoveDown, moveDownAction = self.isAvailableMove('D')
        canMoveLeft, moveLeftAction = self.isAvailableMove('L')
        canMoveRight, moveRightAction = self.isAvailableMove('R')
        if canMoveUp:
            availableMoves.append(moveUpAction)
        if canMoveDown:
            availableMoves.append(moveDownAction)
        if canMoveLeft:
            availableMoves.append(moveLeftAction)
        if canMoveRight:
            availableMoves.append(moveRightAction)
        return availableMoves

    def onPlayerMove(self, moveDirection) -> int: # return the move cost
        # reformat the move direction
        formattedMoveDirection = moveDirection.upper()
        if formattedMoveDirection == 'U' and self.isAvailableMove('U')[0]:
            moveCost = self.__updateMazeOnPlayerMove('U')
        elif formattedMoveDirection == 'D' and self.isAvailableMove('D')[0]:
            moveCost = self.__updateMazeOnPlayerMove('D')
        elif formattedMoveDirection == 'L' and self.isAvailableMove('L')[0]:
            moveCost = self.__updateMazeOnPlayerMove('L')
        elif formattedMoveDirection == 'R' and self.isAvailableMove('R')[0]:
            moveCost = self.__updateMazeOnPlayerMove('R')
        return moveCost
    
    def isEnded(self) -> bool: # isEnded when all the switches have rocks on them
        for switch in self.mazeState.switchData:
            if switch not in self.mazeState.rockData:
                return False
        return True

MAX_DEPTH = 1e6 # Avoid traversing too long

def dfs(filepath : str) -> None:
    global availablePosition
    fileInfo = File.getInfoFromTestFile(filepath)
    mazeMatrix = fileInfo['mazeMatrix']
    rockWeights = fileInfo['rockWeights']
    availablePosition = MazeHelper.getAvailablePosition(mazeMatrix) # Cache available position to reduce time complexity and space complexity

    depth = 0

    nodesGenerated = 0
    process = psutil.Process()
    startTime = time.time()

    maze = Maze(MazeState(mazeMatrix, rockWeights))
    # print(maze.mazeState.switchData)
    stack = []
    traveled = set()
    path = []

    stack.append((maze, path, 0))
    while stack:
        if depth > MAX_DEPTH:
            endTime = time.time()
            searchTime = endTime - startTime
            memoryUsed = process.memory_info().rss / (1024 ** 2)
            print('Exceed max depth')
            File.exportSolutionToFile(fileInfo['caseIndex'], 'DFS', 0, 'No solution', 0, nodesGenerated, searchTime, memoryUsed)
            return
        else: 
            depth += 1
        currentMaze, path, cost = stack.pop()
        if currentMaze.isEnded():
            endTime = time.time()
            searchTime = endTime - startTime
            memoryUsed = process.memory_info().rss / (1024 ** 2)
            # print(path, cost)
            # MazeHelper.printMaze(currentMaze)
            pathStr = ''.join(path)
            File.exportSolutionToFile(fileInfo['caseIndex'], 'DFS', len(pathStr), pathStr, cost, nodesGenerated, searchTime, memoryUsed)
            return
        traveled.add(currentMaze)
        availableMoves = currentMaze.getPlayerMoves()
        for move in availableMoves:
            newMaze = currentMaze.copy()
            moveCost = newMaze.onPlayerMove(move)
            if newMaze not in traveled:
                stack.append((newMaze, path + [move], cost + moveCost))
                nodesGenerated += 1

def maze_solve():
    for file in File.getAllTestFiles():
        dfs(file)