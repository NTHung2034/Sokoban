from Modules import MatrixHelper as matrix

def isSwitch(symbol):
    return symbol in ['.','+','*']

def isWall(symbol):
    return symbol in ['#']

def isRock(symbol):
    return symbol in ['$','*']

def isPlayer(symbol):
    return symbol in ['@','+']

def getPlayerPosition(mazeMatrix):
    for row in range(len(mazeMatrix)):
        for col in range(len(mazeMatrix[row])):
            if isPlayer(mazeMatrix[row][col]):
                return (row, col)
    return None

def getAvailablePosition(mazeMatrix : list) -> set:
    position = set()
    traveled = set()
    playerPosition = getPlayerPosition(mazeMatrix)
    queue = [(playerPosition[0], playerPosition[1])]
    while queue:
        row, col = queue.pop(0)
        if (row, col) in traveled:
            continue
        traveled.add((row, col))
        if mazeMatrix[row][col] != '#':
            position.add((row, col))
            queue.append((row - 1, col))
            queue.append((row + 1, col))
            queue.append((row, col - 1))
            queue.append((row, col + 1))
    return position

def getRockData(mazeMatrix : list,rockWeights : list) -> dict:
    index = 0
    rockData = {}
    for row in range(len(mazeMatrix)):
        for col in range(len(mazeMatrix[row])):
            if isRock(mazeMatrix[row][col]):
                rockData[(row, col)] = int(rockWeights[index])
                index += 1
    return rockData

def getSwitchData(mazeMatrix : list) -> set:
    switchData = set()
    for row in range(len(mazeMatrix)):
        for col in range(len(mazeMatrix[row])):
            if isSwitch(mazeMatrix[row][col]):
                switchData.add((row, col))
    return switchData

def getWallData(mazeMatrix : list) -> set:
    wallData = set()
    for row in range(len(mazeMatrix)):
        for col in range(len(mazeMatrix[row])):
            if isWall(mazeMatrix[row][col]):
                wallData.add((row, col))
    return wallData

def getMazeSize(mazeState) -> dict:
    # find the highest row and the longest column in the wall set
    height = -1
    width = -1
    for position in mazeState.wallData:
        height = max(height, position[0])
        width = max(width, position[1])
    return {'height': height + 1, 'width': width + 1}

def constructMazeMatrix(maze) -> list:
    mazeState = maze.mazeState
    mazeSize = getMazeSize(mazeState)
    mazeMatrix = [[' ' for _ in range(mazeSize['width'])] for _ in range(mazeSize['height'])]
    for position in mazeState.wallData:
        mazeMatrix[position[0]][position[1]] = '#'
    for position in mazeState.switchData:
        mazeMatrix[position[0]][position[1]] = '.' if position not in mazeState.rockData else '*'
    for position in mazeState.rockData:
        mazeMatrix[position[0]][position[1]] = '$' if position not in mazeState.switchData else '*'
    mazeMatrix[mazeState.playerPosition[0]][mazeState.playerPosition[1]] = '@' if mazeState.playerPosition not in mazeState.switchData else '+'
    return mazeMatrix


def printMaze(maze) -> None:
    mazeMatrix = constructMazeMatrix(maze)
    for row in mazeMatrix:
        print(''.join(row))
    print('-------------------------')

def isMatchScenario(mazeMatrix : list, scenario : list) -> bool:
    # create a possible scenario
    scenarioMatrix = [scenario]
    for _ in range(3):
        scenarioMatrix.append(matrix.rotateMatrix(scenarioMatrix[-1]))
    for _ in range(4):
        scenarioMatrix.append(matrix.flip_horizontal(scenarioMatrix[-4]))
    # check if the maze matrix matches the scenario
    for scenario in scenarioMatrix:
        matchCount = 0
        for i, row   in enumerate(scenario):
            for j, col in enumerate(row):
                if col == ' ': matchCount += 1
                elif col == '#' and isWall(mazeMatrix[i][j]): matchCount += 1
                elif col == '$' and isRock(mazeMatrix[i][j]): matchCount += 1
        if matchCount == 9: return True
    return False

def isDeadlockScenario(matrix) -> bool:
    # check if the matrix is a deadlock scenario
    """
        | |#| | \ | |$|#| \ | |$|#| \ | |$|$| \ | |$|#|
        |#|$| | \ | |$|#| \ | |$|$| \ | |$|$| \ |#|$| |
        | | | | \ | | | | \ | | | | \ | | | | \ | |$|#|
    """
    scenarios = [
        [[' ','#',' '],['#','$',' '],[' ',' ',' ']],
        [[' ','$','#'],[' ','$','#'],[' ',' ',' ']],
        [[' ','$','#'],[' ','$','$'],[' ',' ',' ']],
        [[' ','$','$'],[' ','$','$'],[' ',' ',' ']],
        [[' ','$','#'],['#','$',' '],[' ','$','#']],
    ]
    for scenario in scenarios:
        if isMatchScenario(matrix, scenario):
            return True
    return False

def isOnDeadlockScenario(wallData, rockData, newRockPosition, oldPosition) -> bool:
    # get the 3x3 matrix around the new rock position
    row, col = newRockPosition
    matrix = []
    elementCount = 0
    for i in range(row - 1, row + 2):
        row = []
        for j in range(col - 1, col + 2):
            if (i, j) in wallData:
                row.append('#')
                elementCount += 1
            elif ((i, j) in rockData and (i,j) != oldPosition) or (i, j) == newRockPosition:
                row.append('$')
                elementCount += 1
            else:
                row.append(' ')
        matrix.append(row)
    if elementCount < 3:
        return False
    # check if the matrix is a deadlock scenario
    return isDeadlockScenario(matrix)