Imports VbPixelGameEngine

Friend NotInheritable Class Program
    Inherits PixelGameEngine

    Private m_mazeWidth As Integer
    Private m_mazeHeight As Integer
    Private m_maze As Integer()

    Private Const DRAWING_SCALE As Integer = 8
    Private Const AI_MOVE_INTERVAL As Single = 0.25F
    Private ReadOnly Property MazeOffset As New Vi2d(80, 50)
    Private ReadOnly Property MazeColor As Pixel = Presets.Mint

    Private Enum CellPath
        North = &H1
        East = &H2
        South = &H4
        West = &H8
        Visited = &H10
    End Enum

    Private Enum GameState
        Title = 0
        Warmup = 1
        Playing = 2
        Paused = 3
        Result = 4
    End Enum

    ' Game state variables
    Private m_gameState As GameState = GameState.Title
    Private m_visitedCells As Integer
    Private ReadOnly m_stack As New Stack(Of Vi2d)
    Private m_pathWidth As Integer

    ' Player and AI variables
    Private m_player1Pos As Vi2d
    Private m_player2Pos As Vi2d
    Private m_player1Start As Vi2d
    Private m_player2Start As Vi2d
    Private m_player1Target As Vi2d
    Private m_player2Target As Vi2d
    Private m_player1Finished As Boolean
    Private m_player2Finished As Boolean
    Private m_gameTimer As Single
    Private m_warmupTimer As Single
    Private m_aiMoveTimer As Single
    Private m_aiPath As IEnumerable(Of Vi2d)

    ' Game mode
    Private m_twoPlayerMode As Boolean = False

    ' Colors
    Private ReadOnly Player1Color As Pixel = Presets.Cyan
    Private ReadOnly Player2Color As Pixel = Presets.Green
    Private ReadOnly AIColor As Pixel = Presets.Yellow

    Friend Sub New()
        AppName = "VBPGE Amazing Maze Remake"
    End Sub

    Private Sub GenerateMaze()
        ' Initialize maze
        ReDim m_maze(m_mazeWidth * m_mazeHeight)
        m_visitedCells = 0
        m_stack.Clear()

        ' Choose a starting cell
        Dim x = Rand Mod m_mazeWidth
        Dim y = Rand Mod m_mazeHeight
        m_stack.Push(New Vi2d(x, y))
        m_maze(y * m_mazeWidth + x) = CellPath.Visited
        m_visitedCells = 1

        ' Generate maze using depth-first search
        While m_visitedCells < m_mazeWidth * m_mazeHeight
            Dim offset = Function(xo As Integer, yo As Integer)
                             Dim newX = m_stack.Peek.x + xo
                             Dim newY = m_stack.Peek.y + yo
                             If newX < 0 OrElse newX >= m_mazeWidth OrElse newY < 0 OrElse
                                newY >= m_mazeHeight Then Return -1
                             Return newY * m_mazeWidth + newX
                         End Function

            ' Create a set of unvisited neighbours
            Dim neighbours As New List(Of Integer)

            ' Check all four directions
            If m_stack.Peek.y > 0 AndAlso (m_maze(offset(0, -1)) And CellPath.Visited) = 0 Then neighbours.Add(0)
            If m_stack.Peek.x < m_mazeWidth - 1 AndAlso (m_maze(offset(1, 0)) And CellPath.Visited) = 0 Then neighbours.Add(1)
            If m_stack.Peek.y < m_mazeHeight - 1 AndAlso (m_maze(offset(0, 1)) And CellPath.Visited) = 0 Then neighbours.Add(2)
            If m_stack.Peek.x > 0 AndAlso (m_maze(offset(-1, 0)) And CellPath.Visited) = 0 Then neighbours.Add(3)

            If neighbours.Count > 0 Then
                ' Choose random neighbor
                Dim nextDir = neighbours(Rand Mod neighbours.Count)

                Select Case nextDir
                    Case 0 ' North
                        m_maze(offset(0, -1)) = m_maze(offset(0, -1)) Or CellPath.Visited Or CellPath.South
                        m_maze(offset(0, 0)) = m_maze(offset(0, 0)) Or CellPath.North
                        m_stack.Push(New Vi2d(m_stack.Peek.x, m_stack.Peek.y - 1))
                    Case 1 ' East
                        m_maze(offset(1, 0)) = m_maze(offset(1, 0)) Or CellPath.Visited Or CellPath.West
                        m_maze(offset(0, 0)) = m_maze(offset(0, 0)) Or CellPath.East
                        m_stack.Push(New Vi2d(m_stack.Peek.x + 1, m_stack.Peek.y))
                    Case 2 ' South
                        m_maze(offset(0, 1)) = m_maze(offset(0, 1)) Or CellPath.Visited Or CellPath.North
                        m_maze(offset(0, 0)) = m_maze(offset(0, 0)) Or CellPath.South
                        m_stack.Push(New Vi2d(m_stack.Peek.x, m_stack.Peek.y + 1))
                    Case 3 ' West
                        m_maze(offset(-1, 0)) = m_maze(offset(-1, 0)) Or CellPath.Visited Or CellPath.East
                        m_maze(offset(0, 0)) = m_maze(offset(0, 0)) Or CellPath.West
                        m_stack.Push(New Vi2d(m_stack.Peek.x - 1, m_stack.Peek.y))
                End Select

                m_visitedCells += 1
            Else
                m_stack.Pop()
            End If
        End While
    End Sub

    Private Sub SetUpGame()
        ' Set up entrances and player positions
        ' Randomly choose entrance positions on left and right sides
        Dim leftEntranceY = Rand Mod (m_mazeHeight - 2) + 1
        Dim rightEntranceY = Rand Mod (m_mazeHeight - 2) + 1

        ' Create openings at entrances
        m_maze(leftEntranceY * m_mazeWidth) = m_maze(leftEntranceY * m_mazeWidth) Or CellPath.West
        m_maze(rightEntranceY * m_mazeWidth + (m_mazeWidth - 1)) = m_maze(rightEntranceY * m_mazeWidth + (m_mazeWidth - 1)) Or CellPath.East

        ' Set player starting positions
        m_player1Pos = New Vi2d(0, leftEntranceY)
        m_player2Pos = New Vi2d(m_mazeWidth - 1, rightEntranceY)

        m_player1Start = m_player1Pos
        m_player2Start = m_player2Pos

        ' Set targets (opposite sides)
        m_player1Target = New Vi2d(m_mazeWidth - 1, rightEntranceY)
        m_player2Target = New Vi2d(0, leftEntranceY)

        m_player1Finished = False
        m_player2Finished = False
        m_gameTimer = 0.0F
        m_warmupTimer = 0.0F
        m_aiMoveTimer = 0.0F
        m_aiPath = Nothing
    End Sub

    Private Function CanMove(fromPos As Vi2d, direction As Vi2d) As Boolean
        Dim toPos As Vi2d = fromPos + direction
        If toPos.x < 0 OrElse toPos.x >= m_mazeWidth OrElse toPos.y < 0 OrElse
           toPos.y >= m_mazeHeight Then Return False

        Dim cell = m_maze(fromPos.y * m_mazeWidth + fromPos.x)

        ' Check if there's a path in the desired direction
        If direction.x = -1 AndAlso (cell And CellPath.West) <> 0 Then Return True  ' Moving left
        If direction.x = 1 AndAlso (cell And CellPath.East) <> 0 Then Return True   ' Moving right
        If direction.y = -1 AndAlso (cell And CellPath.North) <> 0 Then Return True ' Moving up
        If direction.y = 1 AndAlso (cell And CellPath.South) <> 0 Then Return True  ' Moving down
        Return False
    End Function

    Private Sub MovePlayer(player As Integer, direction As Vi2d)
        Dim currentPos = If(player = 1, m_player1Pos, m_player2Pos)
        If CanMove(currentPos, direction) Then
            Dim newPos = currentPos + direction

            ' Check if player reached target
            If player = 1 AndAlso newPos = m_player1Target Then
                m_player1Finished = True
            ElseIf player = 2 AndAlso newPos = m_player2Target Then
                m_player2Finished = True
            End If

            If player = 1 Then m_player1Pos = newPos Else m_player2Pos = newPos
        End If
    End Sub

    ' Add this class for A* pathfinding
    Private Class PathNode
        Public Position As Vi2d
        Public Parent As PathNode
        Public GCost As Integer ' Distance from start
        Public HCost As Integer ' Distance to target

        Public ReadOnly Property FCost As Integer
            Get
                Return GCost + HCost
            End Get
        End Property

        Public Sub New(pos As Vi2d)
            Position = pos
        End Sub
    End Class

    ' Add this method to find path using A* algorithm
    Private Function FindPath(start As Vi2d, target As Vi2d) As IEnumerable(Of Vi2d)
        Dim GetDistance = Function(posA As Vi2d, posB As Vi2d) As Integer
                              Return Math.Abs(posA.x - posB.x) + Math.Abs(posA.y - posB.y)
                          End Function

        Dim openSet As New List(Of PathNode), closedSet As New HashSet(Of Vi2d)

        Dim startNode As New PathNode(start) With {
            .GCost = 0,
            .HCost = GetDistance(start, target)
        }
        openSet.Add(startNode)

        While openSet.Count > 0
            Dim currentNode = openSet(0)
            For i As Integer = 1 To openSet.Count - 1
                If openSet(i).FCost < currentNode.FCost OrElse
                   (openSet(i).FCost = currentNode.FCost AndAlso
                    openSet(i).HCost < currentNode.HCost) Then currentNode = openSet(i)
            Next i

            openSet.Remove(currentNode)
            closedSet.Add(currentNode.Position)

            ' If we reached the target
            If currentNode.Position = target Then
                Dim path As New List(Of Vi2d)
                Dim node = currentNode

                While node IsNot Nothing AndAlso node IsNot startNode
                    path.Add(node.Position)
                    node = node.Parent
                End While

                path.Reverse()
                Return path
            End If

            ' Check all neighbors
            For Each direction In {New Vi2d(0, -1), New Vi2d(1, 0), New Vi2d(0, 1), New Vi2d(-1, 0)}
                If CanMove(currentNode.Position, direction) Then
                    Dim neighborPos = currentNode.Position + direction

                    If closedSet.Contains(neighborPos) Then Continue For

                    Dim moveCostToNeighbor = currentNode.GCost + GetDistance(currentNode.Position, neighborPos)
                    Dim neighborNode = openSet.Find(Function(n) n.Position = neighborPos)

                    If neighborNode Is Nothing Then
                        neighborNode = New PathNode(neighborPos) With {
                            .GCost = moveCostToNeighbor,
                            .HCost = GetDistance(neighborPos, target),
                            .Parent = currentNode
                        }
                        openSet.Add(neighborNode)
                    ElseIf moveCostToNeighbor < neighborNode.GCost Then
                        neighborNode.GCost = moveCostToNeighbor
                        neighborNode.Parent = currentNode
                    End If
                End If
            Next
        End While

        ' No path found
        Return New List(Of Vi2d)
    End Function

    ' Update the MoveAI method to use the pathfinding
    Private Sub MoveAI()
        ' If we don't have a path or the AI is off the path, recalculate
        If m_aiPath Is Nothing OrElse Not m_aiPath.Contains(m_player2Pos) Then
            m_aiPath = FindPath(m_player2Pos, m_player2Target)
        End If

        ' Convert to list for easier access
        Dim pathList = m_aiPath.ToList()

        If pathList.Count > 0 Then
            ' Find the next position in the path
            Dim currentIndex = pathList.IndexOf(m_player2Pos)
            If currentIndex < pathList.Count - 1 Then
                Dim nextPos = pathList(currentIndex + 1)
                Dim direction = New Vi2d(nextPos.x - m_player2Pos.x, nextPos.y - m_player2Pos.y)

                ' Move towards next position in path
                If CanMove(m_player2Pos, direction) Then
                    m_player2Pos = nextPos

                    ' Check if reached target
                    If m_player2Pos = m_player2Target Then
                        m_player2Finished = True
                        m_aiPath = Nothing ' Clear path when finished
                    End If
                Else
                    ' Path is blocked, recalculate
                    m_aiPath = Nothing
                End If
            End If
        Else
            ' Fallback to old behavior if no path found
            Dim target = m_player2Target
            Dim currentPos = m_player2Pos
            Dim possibleMoves As New List(Of Vi2d)
            Dim towardTargetMoves As New List(Of Vi2d)

            If CanMove(currentPos, New Vi2d(-1, 0)) Then possibleMoves.Add(New Vi2d(-1, 0))
            If CanMove(currentPos, New Vi2d(1, 0)) Then possibleMoves.Add(New Vi2d(1, 0))
            If CanMove(currentPos, New Vi2d(0, -1)) Then possibleMoves.Add(New Vi2d(0, -1))
            If CanMove(currentPos, New Vi2d(0, 1)) Then possibleMoves.Add(New Vi2d(0, 1))

            If possibleMoves.Count = 0 Then Exit Sub

            For Each move As Vi2d In possibleMoves
                Dim newPos = currentPos + move
                Dim distBefore = Math.Abs(currentPos.x - target.x) + Math.Abs(currentPos.y - target.y)
                Dim distAfter = Math.Abs(newPos.x - target.x) + Math.Abs(newPos.y - target.y)

                If distAfter < distBefore Then towardTargetMoves.Add(move)
            Next move

            Dim bestMove As Vi2d
            If towardTargetMoves.Count > 0 Then
                bestMove = towardTargetMoves(Rand Mod towardTargetMoves.Count)
            Else
                bestMove = possibleMoves(Rand Mod possibleMoves.Count)
            End If

            Dim newAIPos = currentPos + bestMove
            If newAIPos = target Then m_player2Finished = True
            m_player2Pos = newAIPos
        End If
    End Sub

    Protected Overrides Function OnUserCreate() As Boolean
        m_mazeWidth = 20
        m_mazeHeight = 15
        m_pathWidth = 3

        GenerateMaze()
        SetUpGame()
        Return True
    End Function

    Protected Overrides Function OnUserUpdate(elapsedTime As Single) As Boolean
        Select Case m_gameState
            Case GameState.Title
                UpdateTitleScreen()
            Case GameState.Playing, GameState.Warmup
                UpdateGame(elapsedTime)
            Case GameState.Paused
                UpdatePausedScreen()
            Case GameState.Result
                UpdateResultScreen()
        End Select

        Return Not GetKey(Key.ESCAPE).Pressed
    End Function

    Private Sub UpdateTitleScreen()
        If GetKey(Key.NP1).Pressed OrElse GetKey(Key.K1).Pressed Then
            m_twoPlayerMode = False
            GenerateMaze()
            SetUpGame()
            m_gameState = GameState.Warmup
        ElseIf GetKey(Key.NP2).Pressed OrElse GetKey(Key.K2).Pressed Then
            m_twoPlayerMode = True
            GenerateMaze()
            SetUpGame()
            m_gameState = GameState.Warmup
        End If

        Clear()
        DrawString(10, 150, "AMAZING MAZE REMAKE", Player1Color, 5)
        DrawString(30, 240, "* PRESS ""1"" FOR SINGLE PLAYER", AIColor, 3)
        DrawString(30, 300, "* PRESS ""2"" FOR TWO PLAYERS", Player2Color, 3)
        DrawString(30, 400, "Player 1 moves with arrow keys", Presets.White, 3)
        DrawString(30, 450, "Player 2 moves with W,A,S,D", Presets.White, 3)
    End Sub

    Private Sub UpdateGame(dt As Single)
        ' Check if still in warm-up phase
        If m_gameState = GameState.Warmup Then
            m_warmupTimer += dt
            If m_warmupTimer >= 3.0F Then
                m_gameState = GameState.Playing
            End If
        Else
            m_gameTimer += dt
            ' Only allow movement if not in warm-up
            ' Player 1 controls (Arrow keys)
            If GetKey(Key.LEFT).Pressed Then MovePlayer(1, New Vi2d(-1, 0))
            If GetKey(Key.RIGHT).Pressed Then MovePlayer(1, New Vi2d(1, 0))
            If GetKey(Key.UP).Pressed Then MovePlayer(1, New Vi2d(0, -1))
            If GetKey(Key.DOWN).Pressed Then MovePlayer(1, New Vi2d(0, 1))

            If m_twoPlayerMode Then
                ' Player 2 controls (WASD)
                If GetKey(Key.A).Pressed Then MovePlayer(2, New Vi2d(-1, 0))
                If GetKey(Key.D).Pressed Then MovePlayer(2, New Vi2d(1, 0))
                If GetKey(Key.W).Pressed Then MovePlayer(2, New Vi2d(0, -1))
                If GetKey(Key.S).Pressed Then MovePlayer(2, New Vi2d(0, 1))
            Else
                ' AI movement (slower than player)
                m_aiMoveTimer += dt
                If m_aiMoveTimer > AI_MOVE_INTERVAL Then
                    MoveAI()
                    m_aiMoveTimer = 0.0F
                End If
            End If

            ' Check for game completion
            If m_player1Finished OrElse m_player2Finished Then m_gameState = GameState.Result

            ' Pause game
            If GetKey(Key.P).Pressed Then m_gameState = GameState.Paused
        End If

        DrawGame()
    End Sub

    Private Sub UpdatePausedScreen()
        If GetKey(Key.P).Pressed Then m_gameState = GameState.Playing

        FillRect(245, 250, 350, 125, Presets.Black)
        DrawString(290, 280, "GAME PAUSED", Presets.Beige, 3)
        DrawString(250, 340, "PRESS ""P"" TO CONTINUE", Presets.White, 2)
    End Sub

    Private Sub UpdateResultScreen()
        If GetKey(Key.ENTER).Pressed Then m_gameState = GameState.Title

        Dim resultText As String, color As Pixel
        If m_player1Finished AndAlso m_player2Finished Then
            resultText = "IT'S A DRAW!"
            color = Presets.Beige
        ElseIf m_player1Finished Then
            resultText = "PLAYER 1 WINS!"
            color = Player1Color
        Else
            resultText = If(m_twoPlayerMode, "PLAYER 2 WINS!", "COMPUTER WINS!")
            color = If(m_twoPlayerMode, Player2Color, AIColor)
        End If

        FillRect(240, 250, 400, 150, Presets.Black)
        DrawString(250, 270, resultText, color, 3)
        DrawString(270, 330, "TIME: " & m_gameTimer.ToString("F1") & "s", Presets.White, 2)
        DrawString(250, 370, "PRESS ENTER TO CONTINUE", Presets.White, 2)
    End Sub

    Private Sub DrawGame()
        Clear()

        ' Draw Maze using FillRect for efficiency
        Dim cellSize = m_pathWidth * DRAWING_SCALE
        Dim maxCellX = MazeOffset.x + m_mazeWidth * (m_pathWidth + 1) * DRAWING_SCALE
        Dim maxCellY = MazeOffset.y + m_mazeHeight * (m_pathWidth + 1) * DRAWING_SCALE
        FillRect(MazeOffset.x - m_pathWidth * 2, MazeOffset.y - m_pathWidth * 2,
                 maxCellX + m_pathWidth - MazeOffset.x,
                 maxCellY + m_pathWidth - MazeOffset.y, MazeColor)

        For x As Integer = 0 To m_mazeWidth - 1
            For y As Integer = 0 To m_mazeHeight - 1
                Dim cellX = MazeOffset.x + x * (m_pathWidth + 1) * DRAWING_SCALE
                Dim cellY = MazeOffset.y + y * (m_pathWidth + 1) * DRAWING_SCALE

                ' Draw cell background using FillRect
                FillRect(cellX, cellY, cellSize, cellSize, Presets.Black)

                ' Draw passageways between cells using FillRect
                If (m_maze(y * m_mazeWidth + x) And CellPath.South) <> 0 Then
                    FillRect(cellX, cellY + cellSize, cellSize, DRAWING_SCALE, Presets.Black)
                End If
                If (m_maze(y * m_mazeWidth + x) And CellPath.East) <> 0 Then
                    FillRect(cellX + cellSize, cellY, DRAWING_SCALE, cellSize, Presets.Black)
                End If
            Next y
        Next x

        FillRect(MazeOffset.x - m_pathWidth * 2,
                 MazeOffset.y + m_player1Start.y * (m_pathWidth + 1) * DRAWING_SCALE,
                 DRAWING_SCALE, cellSize, Presets.Black)
        DrawExitMarkers(m_player1Start, True)
        DrawExitMarkers(m_player2Start, False)

        ' Draw players using FillRect
        DrawPlayer(m_player1Pos, Player1Color, "P1")
        If m_twoPlayerMode Then
            DrawPlayer(m_player2Pos, Player2Color, "P2")
        Else
            DrawPlayer(m_player2Pos, AIColor, "AI")
        End If

        ' Draw UI
        DrawString(30, 10, "TIME: " & m_gameTimer.ToString("F1") & "s", Presets.White, 2)
        DrawString(75, 550, "Player 1: " & If(m_player1Finished, "FINISHED!", "MOVING..."), Player1Color, 2)
        If m_twoPlayerMode Then
            DrawString(425, 550, "Player 2: " & If(m_player2Finished, "FINISHED!", "MOVING..."), Player2Color, 2)
        Else
            DrawString(425, 550, "Computer: " & If(m_player2Finished, "FINISHED!", "MOVING..."), AIColor, 2)
        End If

        ' Draw warm-up countdown if in warm-up phase
        If m_gameState = GameState.Warmup Then
            Dim countdown = Math.Max(0, 3 - CInt(m_warmupTimer))
            Dim countdownText = "GET READY! " & countdown.ToString()
            DrawString(ScreenWidth - 325, 10, countdownText, Presets.Mint, 3)
        ElseIf m_gameState = GameState.Playing Then
            DrawString(ScreenWidth - 300, 10, "Press ""P"" to pause", Presets.White, 2)
        End If
    End Sub

    Private Sub DrawExitMarkers(pos As Vi2d, isLeftSide As Boolean)
        Dim leftColor = If(m_twoPlayerMode, Player2Color, AIColor)
        Dim rightColor = Player1Color
        Dim baseX = MazeOffset.x + pos.x * (m_pathWidth + 1) * DRAWING_SCALE
        Dim baseY = MazeOffset.y + pos.y * (m_pathWidth + 1) * DRAWING_SCALE + (m_pathWidth * DRAWING_SCALE) \ 2

        Const TIP_SIZE As Integer = 10
        If isLeftSide Then
            Dim mkBaseX = baseX - 5 * DRAWING_SCALE
            Dim mkTipX = baseX - 2 * DRAWING_SCALE
            FillTriangle(mkBaseX, baseY, mkTipX, baseY - TIP_SIZE, mkTipX, baseY + TIP_SIZE, leftColor)
        Else
            Dim mkBaseX = baseX + (m_pathWidth + 5) * DRAWING_SCALE
            Dim mkTipX = baseX + (m_pathWidth + 2) * DRAWING_SCALE
            FillTriangle(mkBaseX, baseY, mkTipX, baseY - TIP_SIZE, mkTipX, baseY + TIP_SIZE, rightColor)
        End If
    End Sub

    Private Sub DrawPlayer(pos As Vi2d, color As Pixel, label As String)
        Dim x = MazeOffset.x + (pos.x * (m_pathWidth + 1) + m_pathWidth \ 2) * DRAWING_SCALE
        Dim y = MazeOffset.y + (pos.y * (m_pathWidth + 1) + m_pathWidth \ 2) * DRAWING_SCALE
        Dim radius = (m_pathWidth \ 2) * (DRAWING_SCALE + m_pathWidth)

        ' Draw player as filled circle
        FillCircle(x + m_pathWidth, y + m_pathWidth, radius, color)
        ' Draw player label
        DrawString(x - 5, y, label, Presets.Black, 1)
    End Sub

    Friend Shared Sub Main()
        With New Program
            If .Construct(800, 600, fullScreen:=True) Then .Start()
        End With
    End Sub
End Class